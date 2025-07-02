# REST API Reference

Complete API documentation for the AI Orchestration System.

## 🌐 Base URL

```
http://localhost:8000/api
```

## 🔐 Authentication

Currently, the API does not require authentication for local development. In production environments, implement appropriate authentication mechanisms.

## 📊 Response Format

All API responses follow a consistent JSON format:

```json
{
  "data": {},
  "status": "success|error",
  "message": "Human readable message",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🚀 Projects API

### Create New Project

**POST** `/api/projects`

Create a new AI-generated project workflow.

**Request Body:**
```json
{
  "description": "Create a todo application with user authentication",
  "output_directory": "/path/to/output",
  "enable_git": true,
  "enable_github": false
}
```

**Response:**
```json
{
  "session_id": "abc123-def456-ghi789",
  "status": "started",
  "message": "Project workflow started successfully"
}
```

**Status Codes:**
- `200` - Project created successfully
- `400` - Invalid request parameters
- `500` - Internal server error

### Get Project Status

**GET** `/api/projects/{session_id}/status`

Get the current status of a specific project workflow.

**Response:**
```json
{
  "session_id": "abc123-def456-ghi789",
  "current_phase": "technical_planning",
  "progress": 45.2,
  "execution_time": 127.5,
  "error_count": 0,
  "created_at": 1704110400.0
}
```

**Workflow Phases:**
- `initialization` - Setting up workflow
- `requirements_refinement` - GPT refining requirements
- `technical_planning` - Claude & Gemini creating plans
- `plan_comparison` - Comparing technical approaches
- `conflict_resolution` - Resolving disagreements
- `voting` - Democratic decision making
- `implementation` - Code generation
- `testing` - Test creation
- `finalization` - Project completion
- `completed` - Workflow finished
- `failed` - Workflow failed

### List All Projects

**GET** `/api/projects`

List all active and recent projects.

**Query Parameters:**
- `limit` (optional) - Maximum number of projects to return (default: 50)
- `status` (optional) - Filter by workflow status
- `since` (optional) - ISO timestamp to filter recent projects

**Response:**
```json
{
  "projects": [
    {
      "session_id": "abc123-def456-ghi789",
      "user_request": "Create a todo application...",
      "current_phase": "completed",
      "progress": 100.0,
      "created_at": 1704110400.0
    }
  ],
  "total_count": 1,
  "has_more": false
}
```

### Download Project Files

**GET** `/api/projects/{session_id}/download`

Download the generated project files as a ZIP archive.

**Response:**
- Content-Type: `application/zip`
- Content-Disposition: `attachment; filename="ai-project-{session_id}.zip"`

**Status Codes:**
- `200` - File download ready
- `404` - Project not found or not completed
- `500` - Error generating download

### Delete Project

**DELETE** `/api/projects/{session_id}`

Delete a project and its associated files.

**Response:**
```json
{
  "message": "Project deleted successfully"
}
```

## 🏥 Health & Monitoring API

### System Health Check

**GET** `/api/health`

Get comprehensive system health status.

**Response:**
```json
{
  "overall_status": "healthy",
  "checks": {
    "api_keys": {
      "openai": true,
      "anthropic": true,
      "google": false
    },
    "configuration": {
      "valid": true,
      "errors": []
    },
    "dependencies": {
      "all_available": true,
      "missing": []
    },
    "file_system": {
      "writable": true,
      "output_dir_exists": true
    }
  },
  "errors": [],
  "warnings": ["Google API key not configured"]
}
```

**Health Status Values:**
- `healthy` - All systems operational
- `warning` - Some non-critical issues
- `unhealthy` - Critical issues detected

### System Metrics

**GET** `/api/metrics`

Get system performance metrics and statistics.

**Response:**
```json
{
  "metrics": {
    "total_runtime": 3600.5,
    "total_metrics": 1247,
    "aggregated_metrics": {
      "api_calls_total": {
        "count": 156,
        "total": 156.0,
        "average": 1.0,
        "min": 1.0,
        "max": 1.0
      },
      "workflow_execution_time": {
        "count": 12,
        "total": 1456.7,
        "average": 121.4,
        "min": 45.2,
        "max": 287.1
      }
    }
  },
  "health": {
    "status": "healthy",
    "recent_alerts": 0,
    "critical_alerts": 0
  }
}
```

### Validate API Keys

**POST** `/api/validate-keys`

Validate all configured API keys by making test requests.

**Response:**
```json
{
  "results": {
    "openai": true,
    "anthropic": true,
    "google": false
  },
  "all_valid": false,
  "total_keys": 3,
  "valid_keys": 2
}
```

## ⚙️ Configuration API

### Get Configuration

**GET** `/api/config`

Get current system configuration (sanitized, no API keys).

**Response:**
```json
{
  "config": {
    "environment": "development",
    "debug": true,
    "log_level": "INFO",
    "output_dir": "./output",
    "enable_voting": true,
    "require_consensus": true,
    "allow_tie_breaking": true,
    "max_concurrent_agents": 3,
    "git_enabled": true,
    "git_auto_commit": true,
    "git_auto_push": false
  }
}
```

### Update Configuration

**PUT** `/api/config`

Update system configuration (non-sensitive settings only).

**Request Body:**
```json
{
  "enable_voting": false,
  "max_concurrent_agents": 5,
  "git_auto_push": true
}
```

**Response:**
```json
{
  "message": "Configuration updated successfully",
  "updated_fields": ["enable_voting", "max_concurrent_agents", "git_auto_push"]
}
```

## 🤖 Agents API

### List Available Agents

**GET** `/api/agents`

Get information about available AI agents and their capabilities.

**Response:**
```json
{
  "agents": [
    {
      "name": "gpt",
      "role": "project_manager",
      "model": "gpt-4",
      "capabilities": [
        "requirements_refinement",
        "plan_comparison", 
        "voting",
        "testing"
      ],
      "status": "healthy",
      "last_used": "2024-01-01T12:00:00Z"
    },
    {
      "name": "claude",
      "role": "backend_expert",
      "model": "claude-3-sonnet",
      "capabilities": [
        "technical_planning",
        "implementation",
        "justification",
        "voting"
      ],
      "status": "healthy",
      "last_used": "2024-01-01T11:45:00Z"
    }
  ]
}
```

### Agent Performance

**GET** `/api/agents/{agent_name}/performance`

Get performance metrics for a specific agent.

**Response:**
```json
{
  "agent": "gpt",
  "metrics": {
    "total_requests": 45,
    "successful_requests": 43,
    "failed_requests": 2,
    "average_response_time": 2.3,
    "success_rate": 95.6
  },
  "recent_activity": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "task_type": "requirements_refinement",
      "execution_time": 1.8,
      "success": true
    }
  ]
}
```

## 🔄 Workflows API

### List Workflow Definitions

**GET** `/api/workflows`

Get available workflow definitions.

**Response:**
```json
{
  "workflows": [
    {
      "name": "AI Multi-Agent Orchestration",
      "version": "1.0.0",
      "description": "Complete workflow for GPT, Claude, and Gemini collaboration",
      "phases": 9,
      "estimated_duration": "5-15 minutes"
    }
  ]
}
```

### Get Workflow Definition

**GET** `/api/workflows/{workflow_name}`

Get detailed workflow definition.

**Response:**
```json
{
  "name": "AI Multi-Agent Orchestration",
  "version": "1.0.0",
  "phases": [
    {
      "name": "requirements_refinement",
      "agent": "gpt",
      "task_type": "requirements_refinement",
      "parallel": false,
      "required": true,
      "timeout": 300
    }
  ],
  "settings": {
    "max_execution_time": 3600,
    "enable_parallel_execution": true
  }
}
```

## 📁 Files API

### List Generated Files

**GET** `/api/projects/{session_id}/files`

List all files generated for a project.

**Response:**
```json
{
  "files": [
    {
      "path": "backend/src/main.py",
      "type": "code",
      "language": "python",
      "size": 1024,
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "path": "frontend/src/App.js",
      "type": "code", 
      "language": "javascript",
      "size": 512,
      "created_at": "2024-01-01T12:05:00Z"
    }
  ],
  "total_files": 15,
  "total_size": 45678
}
```

### Get File Content

**GET** `/api/projects/{session_id}/files/{file_path}`

Get the content of a specific generated file.

**Response:**
```json
{
  "path": "backend/src/main.py",
  "content": "#!/usr/bin/env python3\n# Generated backend code...",
  "language": "python",
  "size": 1024,
  "encoding": "utf-8"
}
```

## 🚨 Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid project description",
    "details": {
      "field": "description",
      "constraint": "minimum length 10 characters"
    }
  },
  "status": "error",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `SESSION_NOT_FOUND` | Project session not found | 404 |
| `WORKFLOW_FAILED` | Workflow execution failed | 500 |
| `API_KEY_INVALID` | AI service API key invalid | 401 |
| `RATE_LIMITED` | Too many requests | 429 |
| `SERVICE_UNAVAILABLE` | AI service unavailable | 503 |

## 📝 Rate Limiting

API requests are rate limited to prevent abuse:

- **General endpoints**: 100 requests per minute
- **Project creation**: 10 requests per minute
- **File downloads**: 50 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704110460
```

## 🔍 Pagination

List endpoints support pagination:

**Query Parameters:**
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20, max: 100)

**Response Headers:**
```
X-Total-Count: 150
X-Page-Count: 8
Link: <http://localhost:8000/api/projects?page=2>; rel="next"
```

This API provides comprehensive access to all AI Orchestration System functionality through RESTful endpoints with consistent response formats and proper error handling.