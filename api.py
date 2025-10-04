from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
from backend import InstagramBackend
import json

# Load environment variables
load_dotenv()

app = FastAPI(title="Instagram Scraper API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://your-frontend-domain.vercel.app",
        "https://*.vercel.app"  # Vercel subdomain'leri için
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize backend
backend = InstagramBackend()

# Pydantic models
class ScrapeRequest(BaseModel):
    username: str
    max_posts: Optional[int] = 10
    include_stories: Optional[bool] = False

class MessageRequest(BaseModel):
    username: str
    message: str
    delay_seconds: Optional[int] = 2

class UserData(BaseModel):
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    posts_count: Optional[int] = None

class PostData(BaseModel):
    id: str
    caption: Optional[str] = None
    likes_count: Optional[int] = None
    comments_count: Optional[int] = None
    timestamp: Optional[str] = None
    media_urls: List[str] = []

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Instagram Scraper API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "backend_available": True}

@app.post("/scrape/profile")
async def scrape_profile(request: ScrapeRequest):
    """Scrape Instagram profile data"""
    try:
        result = backend.scrape_instagram_profile(
            username=request.username,
            max_posts=request.max_posts,
            include_stories=request.include_stories
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape/posts")
async def scrape_posts(request: ScrapeRequest):
    """Scrape Instagram posts"""
    try:
        result = backend.scrape_instagram_posts(
            username=request.username,
            max_posts=request.max_posts
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send/message")
async def send_message(request: MessageRequest):
    """Send Instagram message"""
    try:
        result = backend.send_instagram_message(
            username=request.username,
            message=request.message,
            delay_seconds=request.delay_seconds
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users")
async def get_users():
    """Get all users from database"""
    try:
        users = backend.get_all_users()
        return {"success": True, "data": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{username}")
async def get_user(username: str):
    """Get specific user data"""
    try:
        user = backend.get_user_data(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "data": user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/{username}")
async def get_analytics(username: str):
    """Get analytics data for a user"""
    try:
        analytics = backend.get_user_analytics(username)
        return {"success": True, "data": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = backend.get_dashboard_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{username}")
async def delete_user(username: str):
    """Delete user data"""
    try:
        result = backend.delete_user_data(username)
        return {"success": True, "message": f"User {username} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
