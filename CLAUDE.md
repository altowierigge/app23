# CLAUDE.md - Instructions for Claude Sonnet

## Project Overview
You are tasked with fixing the AI Orchestrator to generate ANY type of application dynamically, without templates or rigid workflows. The system should adapt to user requests and create appropriate workflows on-the-fly.

## Critical Rules

### 1. DELETE These Files/Folders First
```bash
# Remove template-based and unnecessary files
rm -rf ai_orchestrator/core/universal_generator.py
rm -rf ai_orchestrator/core/code_generator.py  # If it's template-based
rm -rf ai_orchestrator/web/templates/universal_generator.html
rm -rf ai_orchestrator/web/static/js/universal-generator.js
rm -rf output/incomplete-project-*  # All incomplete test projects
rm -rf ai_orchestrator/templates/  # If exists - remove all templates
```

### 2. Implementation Order (STRICT)
Follow this exact sequence:

1. **Create Project Analyzer** (`ai_orchestrator/core/project_analyzer.py`)
   - Must analyze ANY project type
   - Use GPT Manager for intelligent analysis
   - No hardcoded assumptions

2. **Create Adaptive Workflow Generator** (`ai_orchestrator/core/adaptive_workflow.py`)
   - Dynamic phase generation based on project type
   - No YAML dependencies
   - Support parallel execution

3. **Update ALL Agent Prompts**
   - Remove ALL web-app specific language
   - Make agents truly adaptive
   - Support multiple languages/frameworks

4. **Modify Workflow Engine** (`ai_orchestrator/core/workflow_engine.py`)
   - Support dynamic workflows
   - Remove YAML workflow loading
   - Enable on-the-fly phase execution

5. **Update Orchestrator** (`ai_orchestrator/core/orchestrator.py`)
   - Use new adaptive system
   - Remove all hardcoded logic

## Key Implementation Details

### Project Analyzer Requirements
```python
# Must detect these project types (minimum):
- CLI tools (any language)
- Web applications (any framework)
- Games (console, GUI, web)
- APIs/Microservices
- Mobile apps
- Desktop applications
- Discord/Telegram bots
- Browser extensions
- Data processing scripts
- Machine learning projects
- Libraries/Packages
- DevOps tools
- And ANY other software type
```

### Agent Prompt Updates

#### GPT Manager Agent
- Remove: "You are specialized in web application development"
- Add: "You can understand and plan ANY type of software project"
- Remove: All mentions of authentication, CRUD, databases as defaults
- Add: Dynamic understanding based on project requirements

#### Claude Agent
- Remove: "You implement web backends with FastAPI"
- Add: "You implement ANY software in ANY language/framework"
- Remove: Template-based code generation
- Add: True dynamic code generation

### Workflow Engine Changes
- Remove: `self._load_workflow_definition()` method
- Add: `create_dynamic_workflow()` method
- Remove: YAML parsing logic
- Add: Runtime phase generation

### Testing Requirements
Test with these diverse requests:
1. "Build a Python CLI tool to analyze CSV files"
2. "Create a 2D platformer game with Pygame"
3. "Make a Discord bot for server moderation"
4. "Build a Chrome extension for taking notes"
5. "Create a REST API for a library system using Go"
6. "Make a terminal-based chess game in Rust"
7. "Build a machine learning image classifier"
8. "Create a Jenkins plugin for code analysis"

## Code Quality Standards

### Every Implementation Must:
1. Have comprehensive error handling
2. Include detailed logging
3. Support async operations
4. Be fully typed (type hints)
5. Include docstrings
6. Handle edge cases

### Validation Rules
- NO hardcoded project assumptions
- NO forced authentication/database requirements
- NO template files
- NO rigid phase ordering
- NO language/framework limitations

## File Structure After Fix
```
ai_orchestrator/
├── core/
│   ├── project_analyzer.py      # NEW: Smart project analysis
│   ├── adaptive_workflow.py     # NEW: Dynamic workflow generation
│   ├── workflow_engine.py       # MODIFIED: Dynamic execution
│   ├── orchestrator.py          # MODIFIED: Use adaptive system
│   └── config.py               # Keep as-is
├── agents/
│   ├── base_agent.py           # MODIFIED: Flexible prompts
│   ├── gpt_manager_agent.py    # MODIFIED: Any project type
│   ├── claude_agent.py         # MODIFIED: Any language/framework
│   └── [other agents]          # Update all for flexibility
├── utils/                      # Keep existing utilities
└── web/                        # Update UI for dynamic creation
```

## Integration with Process Monitor
Ensure all new components integrate with existing process monitoring:
```python
self.process_monitor.log_workflow_event(
    session_id=session_id,
    event="adaptive_workflow_created",
    details={
        "project_type": analysis.project_type.value,
        "phase_count": len(phases),
        "tech_stack": analysis.tech_stack
    }
)
```

## Success Criteria Checklist
- [ ] Can generate a CLI tool in any language
- [ ] Can generate a game without web components
- [ ] Can generate a data processing script
- [ ] Can generate a mobile app
- [ ] Can generate a DevOps tool
- [ ] No authentication forced on non-web projects
- [ ] No database forced on simple scripts
- [ ] Appropriate tech stack for each project type
- [ ] Clean, working code generation
- [ ] Proper project structure for each type

## Common Pitfalls to Avoid
1. Don't assume every project needs a database
2. Don't force web frameworks on CLI tools
3. Don't add authentication to simple scripts
4. Don't use React for game development
5. Don't add unnecessary complexity

## Final Cleanup
After implementation:
1. Run comprehensive tests
2. Remove all template references
3. Update documentation
4. Clean up unused imports
5. Remove debug code

## Remember
The goal is to make the AI Orchestrator truly intelligent and adaptive, capable of understanding and building ANY software project the user requests, not just web applications. Every line of code should support this flexibility.

## Command to Run After Implementation
```bash
# Test the new system
python -m ai_orchestrator.cli create "Build a Python script to rename files in bulk"
python -m ai_orchestrator.cli create "Create a terminal-based Tetris game"
python -m ai_orchestrator.cli create "Make a Slack bot for team standup reminders"
```

If any of these create web apps or add unnecessary features, the implementation has failed.