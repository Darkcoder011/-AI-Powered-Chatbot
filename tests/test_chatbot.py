import unittest
from app.core.chatbot import Chatbot
from app.core.sentiment import SentimentAnalyzer
from app.core.session import SessionManager
from app.services.aws import AWSService

class TestChatbot(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.chatbot = Chatbot()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.session_manager = SessionManager()
        self.aws_service = AWSService()

    def test_message_processing(self):
        """Test message processing functionality"""
        # Test basic message processing
        message = "Hello, how are you?"
        session_id = self.session_manager.create_session()
        
        response, confidence = self.chatbot.process_message(message, session_id)
        
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        self.assertIsInstance(confidence, float)
        self.assertTrue(0 <= confidence <= 1)

    def test_sentiment_analysis(self):
        """Test sentiment analysis functionality"""
        # Test positive sentiment
        positive_message = "I'm really happy with the service!"
        positive_sentiment = self.sentiment_analyzer.analyze(positive_message)
        self.assertIn(positive_sentiment, ["positive", "neutral"])

        # Test negative sentiment
        negative_message = "I'm very disappointed with the service."
        negative_sentiment = self.sentiment_analyzer.analyze(negative_message)
        self.assertIn(negative_sentiment, ["negative", "neutral"])

        # Test neutral sentiment
        neutral_message = "What is the status of my order?"
        neutral_sentiment = self.sentiment_analyzer.analyze(neutral_message)
        self.assertEqual(neutral_sentiment, "neutral")

    def test_session_management(self):
        """Test session management functionality"""
        # Test session creation
        session_id = self.session_manager.create_session()
        self.assertIsNotNone(session_id)
        
        # Test session retrieval
        session = self.session_manager.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session['session_id'], session_id)
        
        # Test session update
        updates = {'message_count': 1}
        self.session_manager.update_session(session_id, updates)
        updated_session = self.session_manager.get_session(session_id)
        self.assertEqual(updated_session['message_count'], 1)
        
        # Test session ending
        self.session_manager.end_session(session_id)
        ended_session = self.session_manager.get_session(session_id)
        self.assertFalse(ended_session['is_active'])

    def test_aws_service(self):
        """Test AWS service functionality"""
        # Test user creation
        user_data = {
            'user_id': 'test_user',
            'email': 'test@example.com',
            'preferences': {'language': 'en'}
        }
        user = self.aws_service.create_user(user_data)
        self.assertEqual(user['user_id'], 'test_user')
        
        # Test user context
        session_id = self.session_manager.create_session('test_user')
        context = self.aws_service.get_user_context(session_id)
        self.assertIsNotNone(context)
        
        # Test interaction logging
        self.aws_service.log_interaction(
            session_id=session_id,
            user_id='test_user',
            message="Test message",
            response="Test response",
            sentiment="neutral",
            confidence=0.8,
            intent="test"
        )
        
        # Test user history
        history = self.aws_service.get_user_history('test_user')
        self.assertIsInstance(history, list)

    def test_error_handling(self):
        """Test error handling"""
        # Test invalid session
        response, confidence = self.chatbot.process_message(
            "Test message",
            "invalid_session_id"
        )
        self.assertIsNotNone(response)
        self.assertIsInstance(confidence, float)
        
        # Test invalid sentiment analysis
        sentiment = self.sentiment_analyzer.analyze("")
        self.assertEqual(sentiment, "neutral")
        
        # Test invalid session management
        session = self.session_manager.get_session("invalid_session_id")
        self.assertIsNone(session)

if __name__ == '__main__':
    unittest.main() 