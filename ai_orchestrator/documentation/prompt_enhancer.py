"""
Prompt Enhancement System for Plan-Driven Development.
Enhances AI prompts with structured plan files and phase documentation.
"""

import json
import logging
from typing import Dict, List, Optional, Any
import yaml

from .phase_documenter import PhaseDocumenter, ArchitecturePlan, PhaseDocumentation


class PromptEnhancer:
    """
    Enhances AI prompts with structured plan files and documentation.
    
    Provides context-aware prompts that reference previous phases,
    follow architecture plans, and maintain consistency across phases.
    """
    
    def __init__(self, phase_documenter: PhaseDocumenter):
        """Initialize prompt enhancer."""
        self.phase_documenter = phase_documenter
        self.logger = logging.getLogger("prompt_enhancer")
    
    async def enhance_architecture_prompt(self, base_prompt: str, session_id: str,
                                        unified_features: str) -> str:
        """Enhance architecture design prompt with brainstorming context."""
        
        enhanced_prompt = f"""
{base_prompt}

## CONTEXT FROM PREVIOUS PHASES

### Brainstorming Results
{unified_features}

## ARCHITECTURE DESIGN REQUIREMENTS

Create a comprehensive architecture plan that includes:

### 1. SYSTEM OVERVIEW
- High-level system description
- Core architectural principles
- Technology stack justification

### 2. TECHNOLOGY STACK
Specify exact technologies for:
- Backend framework and language
- Frontend framework and language  
- Database system and type
- Deployment and infrastructure
- Authentication and security
- Testing frameworks
- Monitoring and logging

### 3. COMPONENT ARCHITECTURE
Define each major component:
- Component name and purpose
- Responsibilities and boundaries
- Interface definitions
- Data flow and communication patterns

### 4. DATA MODELS
For each entity:
- Model name and description
- Field definitions with types
- Relationships and constraints
- Validation rules

### 5. API DESIGN
For each endpoint:
- HTTP method and path
- Request/response schemas
- Authentication requirements
- Error handling

### 6. PROJECT STRUCTURE
Detailed file organization:
- Directory structure
- File naming conventions
- Module organization
- Configuration locations

### 7. IMPLEMENTATION PLAN
Break down into phases:
- Phase name and description
- Implementation order and dependencies
- Estimated timeline
- Key deliverables

### 8. CODING STANDARDS
Specify standards for:
- Code formatting and style
- Documentation requirements
- Error handling patterns
- Testing requirements

### 9. QUALITY REQUIREMENTS
Define requirements for:
- Performance benchmarks
- Security standards
- Scalability targets
- Accessibility compliance

## OUTPUT FORMAT
Structure your response to be parseable for creating detailed implementation plans.
Use clear sections and structured data where possible.
"""
        
        return enhanced_prompt
    
    async def enhance_micro_phase_planning_prompt(self, base_prompt: str, session_id: str,
                                                 approved_architecture: str) -> str:
        """Enhance micro-phase planning with architecture plan."""
        
        # Get architecture plan file
        arch_plan = await self.phase_documenter.get_architecture_plan(session_id)
        
        enhanced_prompt = f"""
{base_prompt}

## CONTEXT FROM PREVIOUS PHASES

### Approved Architecture
{approved_architecture}

### Architecture Plan Details
"""
        
        if arch_plan:
            enhanced_prompt += f"""
**Technology Stack:**
{yaml.dump(arch_plan.technology_stack, default_flow_style=False)}

**Components:**
{yaml.dump(arch_plan.components, default_flow_style=False)}

**Project Structure:**
{yaml.dump(arch_plan.project_structure, default_flow_style=False)}

**Development Phases:**
{yaml.dump(arch_plan.development_phases, default_flow_style=False)}
"""
        
        enhanced_prompt += """

## MICRO-PHASE BREAKDOWN REQUIREMENTS

Create detailed micro-phases following these guidelines:

### 1. PHASE GRANULARITY
- Each phase should be completable in 1-3 days
- Clear, testable deliverables
- Minimal dependencies between phases
- Independent deployment if possible

### 2. PHASE STRUCTURE
For each micro-phase, define:
- **Name**: Clear, descriptive name
- **Description**: Detailed purpose and scope
- **Phase Type**: (foundation, feature, integration, testing)
- **Dependencies**: Which phases must complete first
- **Acceptance Criteria**: Specific, testable requirements
- **Implementation Approach**: High-level strategy
- **Files to Create**: Specific file list
- **Tests to Write**: Testing requirements
- **Integration Points**: How it connects to other phases

### 3. IMPLEMENTATION ORDER
- Start with foundation (data models, core APIs)
- Build features incrementally
- Include testing phases
- End with integration and deployment

### 4. QUALITY GATES
Each phase must include:
- Unit test requirements
- Integration test requirements
- Code review criteria
- Documentation updates

## OUTPUT FORMAT
Provide structured micro-phase definitions that can be used to create detailed implementation guides.
"""
        
        return enhanced_prompt
    
    async def enhance_implementation_prompt(self, base_prompt: str, session_id: str,
                                          micro_phase: Dict[str, Any], 
                                          implementation_guide: Dict[str, Any]) -> str:
        """Enhance implementation prompt with plan file and previous phase context."""
        
        # Get architecture plan
        arch_plan = await self.phase_documenter.get_architecture_plan(session_id)
        
        # Get previous phase documentation
        previous_docs = await self.phase_documenter.get_phase_documentation(session_id)
        
        enhanced_prompt = f"""
{base_prompt}

## CURRENT MICRO-PHASE DETAILS

### Phase Information
- **Name**: {micro_phase.get('name', 'Unknown')}
- **Description**: {micro_phase.get('description', 'No description')}
- **Type**: {micro_phase.get('phase_type', 'feature')}
- **Dependencies**: {', '.join(micro_phase.get('dependencies', []))}

### Acceptance Criteria
"""
        
        for i, criteria in enumerate(micro_phase.get('acceptance_criteria', []), 1):
            enhanced_prompt += f"{i}. {criteria}\n"
        
        enhanced_prompt += f"""

### Implementation Approach
{micro_phase.get('implementation_approach', 'Follow architecture plan')}

## ARCHITECTURE PLAN CONTEXT
"""
        
        if arch_plan:
            enhanced_prompt += f"""
### Technology Stack
{yaml.dump(arch_plan.technology_stack, default_flow_style=False)}

### Coding Standards
{yaml.dump(arch_plan.coding_standards, default_flow_style=False)}

### Project Structure
{yaml.dump(arch_plan.project_structure, default_flow_style=False)}

### Testing Strategy
{yaml.dump(arch_plan.testing_strategy, default_flow_style=False)}
"""
        
        enhanced_prompt += """

## IMPLEMENTATION GUIDE FROM PLAN FILE
"""
        
        if implementation_guide:
            enhanced_prompt += f"""
### Files to Create
{yaml.dump(implementation_guide.get('files_to_create', []), default_flow_style=False)}

### Tests to Write
{yaml.dump(implementation_guide.get('tests_to_write', []), default_flow_style=False)}

### Integration Points
{yaml.dump(implementation_guide.get('integration_points', []), default_flow_style=False)}

### Estimated Duration
{implementation_guide.get('estimated_duration', 'Not specified')}
"""
        
        enhanced_prompt += """

## PREVIOUS PHASE CONTEXT
"""
        
        # Add context from completed phases
        completed_phases = [doc for doc in previous_docs if doc.status == 'completed']
        for doc in completed_phases[-3:]:  # Last 3 completed phases
            enhanced_prompt += f"""
### {doc.phase_name}
- **Status**: {doc.status}
- **Files Generated**: {', '.join(doc.generated_files.keys()) if doc.generated_files else 'None'}
- **Key Deliverables**: {', '.join(doc.deliverables)}
"""
        
        enhanced_prompt += """

## IMPLEMENTATION REQUIREMENTS

### 1. CODE QUALITY
- Follow the coding standards defined in the architecture plan
- Include comprehensive error handling
- Add logging for debugging and monitoring
- Write clean, maintainable, well-documented code

### 2. TESTING
- Create unit tests for all new functions/methods
- Write integration tests for API endpoints
- Include edge case testing
- Ensure tests are runnable and pass

### 3. DOCUMENTATION
- Add docstrings to all functions and classes
- Include inline comments for complex logic
- Update README if needed
- Document any configuration changes

### 4. INTEGRATION
- Ensure compatibility with previous phases
- Follow established patterns and conventions
- Test integration points thoroughly
- Consider backwards compatibility

### 5. VALIDATION
- Verify all acceptance criteria are met
- Test error scenarios and edge cases
- Validate input/output formats
- Ensure security best practices

## OUTPUT REQUIREMENTS

Provide complete, working code that:
1. Fulfills all acceptance criteria
2. Follows the architecture plan
3. Integrates properly with previous phases
4. Includes comprehensive tests
5. Is production-ready

Structure your response with:
- Main implementation files
- Test files
- Configuration updates
- Documentation updates
"""
        
        return enhanced_prompt
    
    async def enhance_validation_prompt(self, base_prompt: str, session_id: str,
                                       micro_phase: Dict[str, Any],
                                       generated_files: Dict[str, str]) -> str:
        """Enhance validation prompt with acceptance criteria and architecture standards."""
        
        # Get architecture plan for validation standards
        arch_plan = await self.phase_documenter.get_architecture_plan(session_id)
        
        enhanced_prompt = f"""
{base_prompt}

## VALIDATION CONTEXT

### Micro-Phase Details
- **Name**: {micro_phase.get('name', 'Unknown')}
- **Type**: {micro_phase.get('phase_type', 'feature')}
- **Description**: {micro_phase.get('description', 'No description')}

### Acceptance Criteria to Validate
"""
        
        for i, criteria in enumerate(micro_phase.get('acceptance_criteria', []), 1):
            enhanced_prompt += f"{i}. {criteria}\n"
        
        enhanced_prompt += f"""

### Generated Files to Validate
"""
        
        for filename, content in generated_files.items():
            enhanced_prompt += f"- **{filename}** ({len(content)} characters)\n"
        
        enhanced_prompt += """

## VALIDATION STANDARDS FROM ARCHITECTURE PLAN
"""
        
        if arch_plan:
            enhanced_prompt += f"""
### Coding Standards
{yaml.dump(arch_plan.coding_standards, default_flow_style=False)}

### Quality Requirements
**Performance**: {', '.join(arch_plan.performance_requirements)}
**Security**: {', '.join(arch_plan.security_requirements)}
**Scalability**: {', '.join(arch_plan.scalability_considerations)}

### Testing Strategy
{yaml.dump(arch_plan.testing_strategy, default_flow_style=False)}
"""
        
        enhanced_prompt += """

## COMPREHENSIVE VALIDATION CHECKLIST

### 1. FUNCTIONAL VALIDATION
- [ ] All acceptance criteria are met
- [ ] Core functionality works as specified
- [ ] Edge cases are handled properly
- [ ] Error scenarios are managed correctly
- [ ] Integration points function correctly

### 2. CODE QUALITY VALIDATION
- [ ] Code follows established coding standards
- [ ] Functions and classes have proper docstrings
- [ ] Variable names are descriptive and consistent
- [ ] Code is properly structured and organized
- [ ] No code duplication or redundancy

### 3. TESTING VALIDATION
- [ ] Unit tests are present and comprehensive
- [ ] Integration tests cover key workflows
- [ ] Tests are properly named and documented
- [ ] Test coverage is adequate (>80%)
- [ ] All tests pass successfully

### 4. SECURITY VALIDATION
- [ ] Input validation is implemented
- [ ] Authentication/authorization is proper
- [ ] No sensitive data exposure
- [ ] SQL injection prevention (if applicable)
- [ ] XSS prevention (if applicable)

### 5. PERFORMANCE VALIDATION
- [ ] Code is optimized for performance
- [ ] Database queries are efficient
- [ ] No memory leaks or resource issues
- [ ] Scalability considerations are addressed
- [ ] Caching is implemented where appropriate

### 6. INTEGRATION VALIDATION
- [ ] Compatible with existing codebase
- [ ] Follows established patterns
- [ ] API contracts are maintained
- [ ] Database schema is consistent
- [ ] Configuration is properly managed

### 7. DOCUMENTATION VALIDATION
- [ ] Code is well-documented
- [ ] API documentation is updated
- [ ] README changes are included
- [ ] Configuration changes are documented
- [ ] Deployment notes are provided

## VALIDATION OUTPUT FORMAT

Provide a structured validation report with:

### VALIDATION SUMMARY
- Overall status: PASS/FAIL
- Critical issues count
- Warning issues count
- Suggestions count

### DETAILED FINDINGS
For each validation category:
- Status (Pass/Fail/Warning)
- Specific findings
- Recommendations for improvement

### ACCEPTANCE CRITERIA VERIFICATION
For each acceptance criteria:
- Criteria text
- Verification status
- Evidence/reasoning

### RECOMMENDATIONS
- Priority fixes required
- Suggested improvements
- Future considerations
"""
        
        return enhanced_prompt
    
    async def enhance_integration_prompt(self, base_prompt: str, session_id: str,
                                       completed_phases: List[str]) -> str:
        """Enhance integration prompt with comprehensive phase context."""
        
        # Get all phase documentation
        all_docs = await self.phase_documenter.get_phase_documentation(session_id)
        arch_plan = await self.phase_documenter.get_architecture_plan(session_id)
        
        enhanced_prompt = f"""
{base_prompt}

## INTEGRATION CONTEXT

### Project Overview
- **Session ID**: {session_id}
- **Completed Phases**: {len(completed_phases)}
- **Total Development Time**: {sum(doc.duration_seconds for doc in all_docs):.1f} seconds

## ARCHITECTURE PLAN REFERENCE
"""
        
        if arch_plan:
            enhanced_prompt += f"""
### System Overview
{arch_plan.system_overview}

### Technology Stack
{yaml.dump(arch_plan.technology_stack, default_flow_style=False)}

### Deployment Plan
{yaml.dump(arch_plan.deployment_plan, default_flow_style=False)}
"""
        
        enhanced_prompt += """

## COMPLETED PHASES SUMMARY
"""
        
        for doc in all_docs:
            if doc.status == 'completed':
                enhanced_prompt += f"""
### {doc.phase_name}
- **Status**: {doc.status}
- **Duration**: {doc.duration_seconds:.1f}s
- **Agent**: {doc.agent_used}
- **Deliverables**: {', '.join(doc.deliverables)}
- **Generated Files**: {', '.join(doc.generated_files.keys()) if doc.generated_files else 'None'}
"""
        
        enhanced_prompt += """

## INTEGRATION REQUIREMENTS

### 1. SYSTEM INTEGRATION
- Merge all micro-phase outputs
- Resolve any integration conflicts
- Ensure proper service communication
- Validate end-to-end workflows

### 2. TESTING INTEGRATION
- Run comprehensive integration tests
- Perform end-to-end testing
- Validate system performance
- Test error handling and recovery

### 3. DEPLOYMENT PREPARATION
- Create deployment package
- Configure production settings
- Set up monitoring and logging
- Prepare rollback procedures

### 4. DOCUMENTATION INTEGRATION
- Combine all phase documentation
- Create comprehensive user guide
- Generate API documentation
- Prepare deployment guide

### 5. QUALITY ASSURANCE
- Final code review
- Security assessment
- Performance validation
- Accessibility testing

## INTEGRATION DELIVERABLES

Provide:
1. **Integrated Application**: Complete, deployable application
2. **Integration Report**: Summary of integration activities
3. **Test Results**: Comprehensive testing outcomes
4. **Deployment Guide**: Step-by-step deployment instructions
5. **Project Documentation**: Complete project overview
6. **Maintenance Guide**: Ongoing maintenance procedures
"""
        
        return enhanced_prompt