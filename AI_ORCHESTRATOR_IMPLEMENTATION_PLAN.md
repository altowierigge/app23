# AI Orchestrator Implementation Plan for Claude Sonnet

## Executive Summary
Transform the AI Orchestrator from a rigid, web-app-focused system to a truly adaptive AI that can generate ANY type of software project based on user requests.

## Phase 1: Project Analyzer Implementation

### File: `ai_orchestrator/core/project_analyzer.py`

**Purpose**: Intelligently analyze user requests to understand project requirements without assumptions.

**Key Methods**:
1. `analyze(user_request: str, session_id: str) -> ProjectAnalysis`
   - Uses GPT Manager to understand the request
   - Identifies project type, components, tech stack
   - Suggests custom workflow phases

2. `_detect_project_type()` - Pattern matching for project types
3. `_extract_components()` - Identify required components
4. `_extract_tech_stack()` - Determine appropriate technologies
5. `_extract_phases()` - Generate project-specific phases

**Critical Requirements**:
- NO hardcoded assumptions about project structure
- Support for ALL project types (games, CLI, bots, etc.)
- Dynamic phase generation based on actual needs

## Phase 2: Adaptive Workflow Generator

### File: `ai_orchestrator/core/adaptive_workflow.py`

**Purpose**: Generate custom workflows dynamically based on project analysis.

**Key Methods**:
1. `generate_workflow(user_request: str, session_id: str) -> AdaptiveWorkflow`
   - Main entry point for workflow generation
   - Creates phases based on project type
   - Optimizes execution order

2. Phase generators for each project type:
   - `_generate_cli_phases()` - For command-line tools
   - `_generate_webapp_phases()` - For web applications
   - `_generate_game_phases()` - For game development
   - `_generate_api_phases()` - For API services
   - `_generate_bot_phases()` - For chat bots
   - `_generate_generic_phases()` - For unknown types

**Critical Requirements**:
- Phases created on-the-fly, not from templates
- Support parallel execution where appropriate
- Each phase must be self-contained and purposeful

## Phase 3: Agent System Updates

### Update ALL agents with flexible prompts:

1. **GPT Manager Agent** (`gpt_manager_agent.py`):
   ```python
   FLEXIBLE_SYSTEM_PROMPT = """
   You are an AI Project Manager capable of understanding and planning ANY type of software project:
   - Web applications (React, Vue, Django, Rails, etc.)
   - CLI tools (Python, Rust, Go, etc.)
   - Games (Unity, Pygame, JavaScript, etc.)
   - Mobile apps (React Native, Flutter, etc.)
   - APIs and microservices
   - Data processing scripts
   - Machine learning projects
   - Browser extensions
   - Discord/Telegram bots
   - And any other software project
   
   Your role is to:
   1. Understand what the user wants to build
   2. Identify the best approach and tech stack
   3. Plan the project structure
   4. Guide other agents in implementation
   """
   ```

2. **Claude Agent** (`claude_agent.py`):
   ```python
   FLEXIBLE_SYSTEM_PROMPT = """
   You are an AI Software Developer capable of implementing ANY type of software in ANY language:
   - You adapt to the project requirements
   - You write actual, working code (not templates)
   - You follow best practices for the chosen tech stack
   - You create complete, functional applications
   - You don't force unnecessary features (auth, database, etc.)
   """
   ```

### Remove these hardcoded assumptions:
- Every project needs authentication
- Every project needs a database
- Every project is a web application
- Every project needs CRUD operations
- Every project uses React/FastAPI

## Phase 4: Workflow Engine Modification

### File: `ai_orchestrator/core/workflow_engine.py`

**Changes Required**:
1. Create `DynamicWorkflowEngine` class
2. Remove YAML loading logic
3. Add `create_adaptive_workflow()` method
4. Support dynamic phase execution
5. Enable runtime phase generation

**New Methods**:
- `execute_adaptive_workflow(workflow: AdaptiveWorkflow)`
- `_execute_dynamic_phase(phase: DynamicPhase)`
- `_handle_parallel_phases(phases: List[DynamicPhase])`

## Phase 5: Orchestrator Updates

### File: `ai_orchestrator/core/orchestrator.py`

**Changes Required**:
1. Use `AdaptiveWorkflowGenerator` instead of YAML workflows
2. Remove all hardcoded phase logic
3. Support dynamic project creation
4. Integrate with new adaptive system

**Key Changes**:
```python
async def create_project(self, user_request: str, session_id: str):
    # Initialize adaptive generator
    generator = AdaptiveWorkflowGenerator(self.gpt_manager)
    
    # Generate custom workflow
    workflow = await generator.generate_workflow(user_request, session_id)
    
    # Execute adaptive workflow
    result = await self.execute_adaptive_workflow(workflow)
```

## Phase 6: Testing Strategy

### Test Cases (MUST PASS ALL):

1. **CLI Tool Test**:
   - Request: "Build a Python CLI tool to analyze CSV files"
   - Expected: Python project with argparse, CSV handling, NO web components

2. **Game Test**:
   - Request: "Create a 2D platformer game with Pygame"
   - Expected: Pygame project with game loop, sprites, NO authentication

3. **Bot Test**:
   - Request: "Make a Discord bot for moderation"
   - Expected: Discord.py bot with commands, NO web interface

4. **Script Test**:
   - Request: "Create a script to batch rename files"
   - Expected: Simple Python/Bash script, NO database

5. **API Test**:
   - Request: "Build a REST API for weather data"
   - Expected: API with endpoints, appropriate framework, NO frontend

## Phase 7: Cleanup Tasks

1. **Delete These Files**:
   ```bash
   rm -rf ai_orchestrator/core/universal_generator.py
   rm -rf ai_orchestrator/web/templates/universal_generator.html
   rm -rf ai_orchestrator/templates/  # All templates
   rm -rf workflows/*.yaml  # Except for backward compatibility
   ```

2. **Update Web UI**:
   - Remove universal generator routes
   - Update project creation to use adaptive system
   - Show dynamic phase generation in monitor

## Implementation Checklist

- [ ] Create `project_analyzer.py` with full implementation
- [ ] Create `adaptive_workflow.py` with all project type support
- [ ] Update ALL agent prompts to be flexible
- [ ] Modify workflow engine for dynamic execution
- [ ] Update orchestrator to use adaptive system
- [ ] Test with 10+ different project types
- [ ] Remove all template-based code
- [ ] Update documentation
- [ ] Clean up unused imports and files

## Success Metrics

The implementation is successful when:
1. ✅ Can generate ANY project type without templates
2. ✅ No forced features (auth, DB, etc.) on simple projects
3. ✅ Appropriate tech stack for each project type
4. ✅ Clean, working code generation
5. ✅ Proper project structure for each type
6. ✅ All tests pass without web-app bias

## Final Note

Remember: The goal is to create an AI that truly understands software development across all domains, not just web applications. Every decision should support maximum flexibility and intelligence.