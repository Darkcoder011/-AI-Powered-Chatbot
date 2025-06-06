from transformers import pipeline
from typing import Dict, Tuple
import numpy as np

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = None
        self._initialize_analyzer()

    def _initialize_analyzer(self):
        """Initialize the sentiment analysis model"""
        try:
            # Initialize the sentiment analysis pipeline
            self.analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                return_all_scores=True
            )
        except Exception as e:
            print(f"Error initializing sentiment analyzer: {str(e)}")
            self.analyzer = None

    def analyze(self, text: str) -> str:
        """
        Analyze the sentiment of the given text
        
        Args:
            text: The text to analyze
            
        Returns:
            String indicating the sentiment (positive, negative, or neutral)
        """
        try:
            if not self.analyzer:
                return "neutral"
            
            # Get sentiment scores
            results = self.analyzer(text)[0]
            
            # Get the highest scoring sentiment
            sentiment_scores = {item['label']: item['score'] for item in results}
            
            # Determine sentiment based on scores
            if sentiment_scores.get('POSITIVE', 0) > 0.6:
                return "positive"
            elif sentiment_scores.get('NEGATIVE', 0) > 0.6:
                return "negative"
            else:
                return "neutral"
                
        except Exception as e:
            print(f"Error analyzing sentiment: {str(e)}")
            return "neutral"

    def get_sentiment_scores(self, text: str) -> Dict[str, float]:
        """
        Get detailed sentiment scores for the given text
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing sentiment scores
        """
        try:
            if not self.analyzer:
                return {"positive": 0.5, "negative": 0.5}
            
            results = self.analyzer(text)[0]
            return {item['label'].lower(): item['score'] for item in results}
            
        except Exception as e:
            print(f"Error getting sentiment scores: {str(e)}")
            return {"positive": 0.5, "negative": 0.5}

    def analyze_batch(self, texts: list) -> list:
        """
        Analyze sentiment for multiple texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment results
        """
        try:
            if not self.analyzer:
                return ["neutral"] * len(texts)
            
            results = self.analyzer(texts)
            sentiments = []
            
            for result in results:
                sentiment_scores = {item['label']: item['score'] for item in result}
                
                if sentiment_scores.get('POSITIVE', 0) > 0.6:
                    sentiments.append("positive")
                elif sentiment_scores.get('NEGATIVE', 0) > 0.6:
                    sentiments.append("negative")
                else:
                    sentiments.append("neutral")
                    
            return sentiments
            
        except Exception as e:
            print(f"Error analyzing batch sentiment: {str(e)}")
            return ["neutral"] * len(texts)

    def get_emotion_intensity(self, text: str) -> float:
        """
        Calculate the intensity of the emotion in the text
        
        Args:
            text: The text to analyze
            
        Returns:
            Float between 0 and 1 indicating emotion intensity
        """
        try:
            if not self.analyzer:
                return 0.5
            
            results = self.analyzer(text)[0]
            scores = [item['score'] for item in results]
            
            # Calculate intensity as the maximum score
            intensity = max(scores)
            
            return float(intensity)
            
        except Exception as e:
            print(f"Error calculating emotion intensity: {str(e)}")
            return 0.5 