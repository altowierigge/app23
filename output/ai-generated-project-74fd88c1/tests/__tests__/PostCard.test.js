import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import PostCard from '../components/Feed/PostCard';
import authSlice from '../store/authSlice';

const mockStore = configureStore({
  reducer: {
    auth: authSlice
  },
  preloadedState: {
    auth: {
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' }
    }
  }
});

const mockPost = {
  id: 1,
  content: 'This is a test post',
  author: {
    name: 'Test User',
    username: 'testuser',
    avatar: '/test-avatar.jpg'
  },
  likeCount: 5,
  commentCount: 2,
  isLiked: false,
  createdAt: '2024-01-01T00:00:00Z'
};

describe('PostCard Component', () => {
  test('renders post content correctly', () => {
    render(
      <Provider store={mockStore}>
        <PostCard post={mockPost} />
      </Provider>
    );
    
    expect(screen.getByText('This is a test post')).toBeInTheDocument();
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('@testuser')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument(); // Like count
  });
  
  test('handles like button click', async () => {
    render(
      <Provider store={mockStore}>
        <PostCard post={mockPost} />
      </Provider>
    );
    
    const likeButton = screen.getByRole('button', { name: /heart/i });
    fireEvent.click(likeButton);
    
    await waitFor(() => {
      expect(screen.getByText('6')).toBeInTheDocument(); // Like count increased
    });
  });
});