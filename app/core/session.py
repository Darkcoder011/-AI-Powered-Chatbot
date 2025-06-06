import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
from ..services.aws import AWSService

class SessionManager:
    def __init__(self):
        self.aws_service = AWSService()
        self.session_timeout = timedelta(hours=1)

    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new session
        
        Args:
            user_id: Optional user ID to associate with the session
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_active': datetime.utcnow().isoformat(),
            'message_count': 0,
            'context': {},
            'is_active': True
        }
        
        try:
            self.aws_service.sessions_table.put_item(Item=session_data)
            return session_id
        except Exception as e:
            print(f"Error creating session: {str(e)}")
            raise

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            Session data dictionary or None if not found
        """
        try:
            response = self.aws_service.sessions_table.get_item(
                Key={'session_id': session_id}
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting session: {str(e)}")
            return None

    def update_session(self, session_id: str, updates: Dict):
        """
        Update session data
        
        Args:
            session_id: The session ID to update
            updates: Dictionary of updates to apply
        """
        try:
            update_expression = "SET "
            expression_values = {}
            
            for key, value in updates.items():
                update_expression += f"{key} = :{key}, "
                expression_values[f":{key}"] = value
            
            update_expression = update_expression.rstrip(", ")
            
            self.aws_service.sessions_table.update_item(
                Key={'session_id': session_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
        except Exception as e:
            print(f"Error updating session: {str(e)}")

    def end_session(self, session_id: str):
        """
        End a session
        
        Args:
            session_id: The session ID to end
        """
        try:
            self.aws_service.sessions_table.update_item(
                Key={'session_id': session_id},
                UpdateExpression="SET is_active = :active, ended_at = :time",
                ExpressionAttributeValues={
                    ':active': False,
                    ':time': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            print(f"Error ending session: {str(e)}")

    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            # Get all active sessions
            response = self.aws_service.sessions_table.scan(
                FilterExpression="is_active = :active",
                ExpressionAttributeValues={':active': True}
            )
            
            current_time = datetime.utcnow()
            
            for session in response.get('Items', []):
                last_active = datetime.fromisoformat(session['last_active'])
                
                if current_time - last_active > self.session_timeout:
                    self.end_session(session['session_id'])
                    
        except Exception as e:
            print(f"Error cleaning up sessions: {str(e)}")

    def update_session_context(self, session_id: str, context_updates: Dict):
        """
        Update the session context
        
        Args:
            session_id: The session ID to update
            context_updates: Dictionary of context updates
        """
        try:
            # Get current context
            session = self.get_session(session_id)
            if not session:
                return
                
            current_context = session.get('context', {})
            
            # Merge updates
            updated_context = {**current_context, **context_updates}
            
            # Update session
            self.update_session(session_id, {
                'context': updated_context,
                'last_active': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            print(f"Error updating session context: {str(e)}")

    def get_user_sessions(self, user_id: str) -> list:
        """
        Get all sessions for a user
        
        Args:
            user_id: The user ID to get sessions for
            
        Returns:
            List of session data dictionaries
        """
        try:
            response = self.aws_service.sessions_table.query(
                IndexName='user_id-created_at-index',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting user sessions: {str(e)}")
            return []

    def get_active_sessions_count(self) -> int:
        """
        Get the count of active sessions
        
        Returns:
            Number of active sessions
        """
        try:
            response = self.aws_service.sessions_table.scan(
                FilterExpression="is_active = :active",
                ExpressionAttributeValues={':active': True}
            )
            return len(response.get('Items', []))
        except Exception as e:
            print(f"Error getting active sessions count: {str(e)}")
            return 0 