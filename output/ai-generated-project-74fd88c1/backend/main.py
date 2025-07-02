from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="Social Media API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.auth import router as auth_router
from api.users import router as users_router
from api.posts import router as posts_router
from api.messages import router as messages_router

app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(posts_router, prefix="/api/posts", tags=["posts"])
app.include_router(messages_router, prefix="/api/messages", tags=["messages"])

@app.get("/")
async def root():
    return {"message": "Social Media API v1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "social-media-api"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)