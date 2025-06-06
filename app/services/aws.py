import boto3
import json
from typing import Dict, List, Optional
from datetime import datetime
import os
from botocore.exceptions import ClientError

class AWSService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.s3 = boto3.client('s3')
        self.lambda_client = boto3.client('lambda')
        
        # Initialize tables
        self.users_table = self.dynamodb.Table(os.getenv('USERS_TABLE', 'chatbot-users'))
        self.sessions_table = self.dynamodb.Table(os.getenv('SESSIONS_TABLE', 'chatbot-sessions'))
        self.interactions_table = self.dynamodb.Table(os.getenv('INTERACTIONS_TABLE', 'chatbot-interactions'))
        
        # S3 bucket names
        self.knowledge_base_bucket = os.getenv('KNOWLEDGE_BASE_BUCKET', 'chatbot-knowledge-base')
        self.models_bucket = os.getenv('MODELS_BUCKET', 'chatbot-models')

    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user in DynamoDB"""
        try:
            user_item = {
                'user_id': user_data['user_id'],
                'email': user_data['email'],
                'created_at': datetime.utcnow().isoformat(),
                'last_active': datetime.utcnow().isoformat(),
                'preferences': user_data.get('preferences', {}),
                'interaction_count': 0
            }
            
            self.users_table.put_item(Item=user_item)
            return user_item
            
        except ClientError as e:
            print(f"Error creating user: {str(e)}")
            raise

    def get_user_context(self, session_id: str) -> Dict:
        """Get user context from DynamoDB"""
        try:
            response = self.sessions_table.get_item(Key={'session_id': session_id})
            return response.get('Item', {})
        except ClientError as e:
            print(f"Error getting user context: {str(e)}")
            return {}

    def update_user_context(
        self,
        session_id: str,
        message: str,
        response: str,
        intent: str
    ):
        """Update user context in DynamoDB"""
        try:
            self.sessions_table.update_item(
                Key={'session_id': session_id},
                UpdateExpression="SET last_interaction = :time, message_count = message_count + :inc",
                ExpressionAttributeValues={
                    ':time': datetime.utcnow().isoformat(),
                    ':inc': 1
                }
            )
            
            # Log interaction
            self.log_interaction(
                session_id=session_id,
                message=message,
                response=response,
                intent=intent
            )
            
        except ClientError as e:
            print(f"Error updating user context: {str(e)}")

    def log_interaction(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        message: str = "",
        response: str = "",
        sentiment: str = "",
        confidence: float = 0.0,
        intent: str = ""
    ):
        """Log interaction in DynamoDB"""
        try:
            interaction_item = {
                'interaction_id': f"{session_id}_{datetime.utcnow().timestamp()}",
                'session_id': session_id,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'message': message,
                'response': response,
                'sentiment': sentiment,
                'confidence': confidence,
                'intent': intent
            }
            
            self.interactions_table.put_item(Item=interaction_item)
            
        except ClientError as e:
            print(f"Error logging interaction: {str(e)}")

    def get_knowledge_base(self) -> Dict:
        """Get knowledge base from S3"""
        try:
            response = self.s3.get_object(
                Bucket=self.knowledge_base_bucket,
                Key='knowledge_base.json'
            )
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            print(f"Error getting knowledge base: {str(e)}")
            return {}

    def get_user_history(self, user_id: str) -> List[Dict]:
        """Get user interaction history"""
        try:
            response = self.interactions_table.query(
                IndexName='user_id-timestamp-index',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={
                    ':uid': user_id
                },
                Limit=100  # Limit to last 100 interactions
            )
            return response.get('Items', [])
        except ClientError as e:
            print(f"Error getting user history: {str(e)}")
            return []

    def update_knowledge_base(self, knowledge_base: Dict):
        """Update knowledge base in S3"""
        try:
            self.s3.put_object(
                Bucket=self.knowledge_base_bucket,
                Key='knowledge_base.json',
                Body=json.dumps(knowledge_base),
                ContentType='application/json'
            )
        except ClientError as e:
            print(f"Error updating knowledge base: {str(e)}")

    def invoke_lambda(self, function_name: str, payload: Dict) -> Dict:
        """Invoke AWS Lambda function"""
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            return json.loads(response['Payload'].read().decode('utf-8'))
        except ClientError as e:
            print(f"Error invoking Lambda: {str(e)}")
            return {}

    def get_model_from_s3(self, model_name: str) -> bytes:
        """Get model file from S3"""
        try:
            response = self.s3.get_object(
                Bucket=self.models_bucket,
                Key=f'models/{model_name}'
            )
            return response['Body'].read()
        except ClientError as e:
            print(f"Error getting model from S3: {str(e)}")
            return b'' 