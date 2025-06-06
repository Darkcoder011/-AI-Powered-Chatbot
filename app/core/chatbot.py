import tensorflow as tf
from transformers import BertTokenizer, TFBertForSequenceClassification
import numpy as np
from typing import Tuple, Dict, List
import json
import os
from ..services.aws import AWSService

class Chatbot:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.knowledge_base = {}
        self.aws_service = AWSService()
        self._initialize_model()
        self._load_knowledge_base()

    def _initialize_model(self):
        """Initialize the BERT model and tokenizer"""
        try:
            # Load pre-trained BERT model and tokenizer
            self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            self.model = TFBertForSequenceClassification.from_pretrained(
                'bert-base-uncased',
                num_labels=2  # Binary classification for intent matching
            )
        except Exception as e:
            print(f"Error initializing model: {str(e)}")
            # Fallback to a simpler model if BERT fails
            self._initialize_fallback_model()

    def _initialize_fallback_model(self):
        """Initialize a simpler fallback model"""
        # Implement a simpler model as fallback
        pass

    def _load_knowledge_base(self):
        """Load the knowledge base from S3"""
        try:
            self.knowledge_base = self.aws_service.get_knowledge_base()
        except Exception as e:
            print(f"Error loading knowledge base: {str(e)}")
            self.knowledge_base = {}

    def process_message(self, message: str, session_id: str) -> Tuple[str, float]:
        """
        Process the incoming message and generate a response
        
        Args:
            message: The user's message
            session_id: The current session ID
            
        Returns:
            Tuple containing the response and confidence score
        """
        try:
            # Get user context
            user_context = self.aws_service.get_user_context(session_id)
            
            # Preprocess the message
            processed_message = self._preprocess_message(message)
            
            # Get intent and entities
            intent, entities = self._extract_intent_and_entities(processed_message)
            
            # Generate response
            response, confidence = self._generate_response(
                intent=intent,
                entities=entities,
                context=user_context
            )
            
            # Update user context
            self._update_user_context(session_id, message, response, intent)
            
            return response, confidence
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now.", 0.0

    def _preprocess_message(self, message: str) -> str:
        """Preprocess the message for model input"""
        # Convert to lowercase
        message = message.lower()
        
        # Remove special characters
        message = ''.join(c for c in message if c.isalnum() or c.isspace())
        
        return message

    def _extract_intent_and_entities(self, message: str) -> Tuple[str, Dict]:
        """Extract intent and entities from the message"""
        # Tokenize the message
        inputs = self.tokenizer(
            message,
            return_tensors="tf",
            padding=True,
            truncation=True,
            max_length=512
        )
        
        # Get model predictions
        outputs = self.model(inputs)
        predictions = tf.nn.softmax(outputs.logits, axis=-1)
        
        # Get the predicted intent
        intent = "general_query" if predictions[0][1] > 0.5 else "specific_query"
        
        # Extract entities (simplified version)
        entities = self._extract_entities(message)
        
        return intent, entities

    def _extract_entities(self, message: str) -> Dict:
        """Extract named entities from the message"""
        # Implement entity extraction logic
        # This is a simplified version
        entities = {
            "keywords": [],
            "topics": []
        }
        
        # Add basic keyword extraction
        words = message.split()
        for word in words:
            if len(word) > 3:  # Simple filter for meaningful words
                entities["keywords"].append(word)
        
        return entities

    def _generate_response(
        self,
        intent: str,
        entities: Dict,
        context: Dict
    ) -> Tuple[str, float]:
        """Generate a response based on intent, entities, and context"""
        try:
            # Search knowledge base
            relevant_info = self._search_knowledge_base(intent, entities)
            
            if relevant_info:
                response = self._format_response(relevant_info, context)
                confidence = 0.8  # High confidence for knowledge base matches
            else:
                # Fallback to general response
                response = self._generate_fallback_response(intent, context)
                confidence = 0.5  # Lower confidence for fallback responses
            
            return response, confidence
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I'm not sure how to respond to that.", 0.0

    def _search_knowledge_base(self, intent: str, entities: Dict) -> Dict:
        """Search the knowledge base for relevant information"""
        # Implement knowledge base search logic
        # This is a simplified version
        return self.knowledge_base.get(intent, {})

    def _format_response(self, info: Dict, context: Dict) -> str:
        """Format the response based on the information and context"""
        # Implement response formatting logic
        return str(info.get("response", "I don't have enough information to answer that."))

    def _generate_fallback_response(self, intent: str, context: Dict) -> str:
        """Generate a fallback response when no specific answer is found"""
        fallback_responses = {
            "general_query": "Could you please provide more specific information?",
            "specific_query": "I'm not sure I understand. Could you rephrase that?",
            "default": "I'm still learning and don't have an answer for that yet."
        }
        return fallback_responses.get(intent, fallback_responses["default"])

    def _update_user_context(self, session_id: str, message: str, response: str, intent: str):
        """Update the user's context with the latest interaction"""
        try:
            self.aws_service.update_user_context(
                session_id=session_id,
                message=message,
                response=response,
                intent=intent
            )
        except Exception as e:
            print(f"Error updating user context: {str(e)}") 