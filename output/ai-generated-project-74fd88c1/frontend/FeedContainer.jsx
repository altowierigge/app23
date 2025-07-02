import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import PostCard from './PostCard';
import CreatePost from './CreatePost';
import { fetchPosts } from '../../services/api';

const FeedContainer = () => {
  const [posts, setPosts] = useState([]);
  
  const { data: feedPosts, isLoading, error } = useQuery({
    queryKey: ['posts'],
    queryFn: fetchPosts
  });
  
  useEffect(() => {
    if (feedPosts) {
      setPosts(feedPosts);
    }
  }, [feedPosts]);
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="text-center text-red-500 p-4">
        Error loading posts. Please try again.
      </div>
    );
  }
  
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <CreatePost onPostCreated={(newPost) => setPosts([newPost, ...posts])} />
      
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
      
      {posts.length === 0 && (
        <div className="text-center text-gray-500 p-8">
          No posts yet. Be the first to share something!
        </div>
      )}
    </div>
  );
};

export default FeedContainer;