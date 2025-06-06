from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import boto3
import json
import os
from datetime import datetime

from ..core.chatbot import Chatbot
from ..core.session import SessionManager
from ..core.sentiment import SentimentAnalyzer
from ..models.user import User, UserCreate
from ..services.aws import AWSService

app = FastAPI(title="AI Chatbot API", version="1.0.0")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
chatbot = Chatbot()
session_manager = SessionManager()
sentiment_analyzer = SentimentAnalyzer()
aws_service = AWSService()

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sentiment: str
    confidence: float

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        # Get or create session
        session_id = message.session_id or session_manager.create_session(message.user_id)
        
        # Process message and get response
        response, confidence = chatbot.process_message(message.message, session_id)
        
        # Analyze sentiment
        sentiment = sentiment_analyzer.analyze(message.message)
        
        # Log interaction
        aws_service.log_interaction(
            session_id=session_id,
            user_id=message.user_id,
            message=message.message,
            response=response,
            sentiment=sentiment,
            confidence=confidence
        )
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            sentiment=sentiment,
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    try:
        return aws_service.create_user(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/history")
async def get_user_history(user_id: str):
    try:
        return aws_service.get_user_history(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 