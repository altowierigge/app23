import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'react-redux';
import FeedContainer from '../components/Feed/FeedContainer';
import { store } from '../store';

// Mock API
jest.mock('../services/api', () => ({
  fetchPosts: jest.fn(() => Promise.resolve([
    {
      id: 1,
      content: 'Test post 1',
      author: { name: 'User 1', username: 'user1' },
      likeCount: 10,
      commentCount: 3,
      isLiked: false,
      createdAt: '2024-01-01T00:00:00Z'
    },
    {
      id: 2,
      content: 'Test post 2',
      author: { name: 'User 2', username: 'user2' },
      likeCount: 5,
      commentCount: 1,
      isLiked: true,
      createdAt: '2024-01-02T00:00:00Z'
    }
  ]))
}));

describe('Feed Integration', () => {
  test('loads and displays posts from API', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    
    render(
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          <FeedContainer />
        </QueryClientProvider>
      </Provider>
    );
    
    // Should show loading initially
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for posts to load
    await waitFor(() => {
      expect(screen.getByText('Test post 1')).toBeInTheDocument();
      expect(screen.getByText('Test post 2')).toBeInTheDocument();
    });
  });
});