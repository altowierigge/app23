import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_post():
    """Test creating a new post."""
    # First login to get token
    login_response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    post_data = {
        "content": "This is a test post!",
        "image_url": None
    }
    
    response = client.post(
        "/api/posts",
        json=post_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == post_data["content"]
    assert "id" in data
    assert "created_at" in data

def test_get_feed():
    """Test retrieving user feed."""
    response = client.get("/api/posts/feed")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data["posts"], list)
    assert "total" in data

def test_like_post():
    """Test liking a post."""
    # Create a post first
    post_response = client.post("/api/posts", json={
        "content": "Test post for liking"
    })
    post_id = post_response.json()["id"]
    
    # Like the post
    response = client.post(f"/api/posts/{post_id}/like")
    assert response.status_code == 200
    
    data = response.json()
    assert data["liked"] == True