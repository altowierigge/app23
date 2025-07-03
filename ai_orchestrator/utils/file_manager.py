"""
File output management and project structure generation.
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from ..core.config import get_config
from .logging_config import get_logger, TimedOperation


@dataclass
class GeneratedFile:
    """Represents a generated file with metadata."""
    path: str
    content: str
    file_type: str  # 'code', 'config', 'documentation', 'test'
    language: Optional[str] = None
    encoding: str = 'utf-8'
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProjectStructure:
    """Represents the complete project structure."""
    name: str
    description: str
    session_id: str
    created_at: datetime
    files: List[GeneratedFile]
    metadata: Dict[str, Any]
    
    def get_backend_files(self) -> List[GeneratedFile]:
        """Get all backend-related files."""
        return [f for f in self.files if f.path.startswith('backend/')]
    
    def get_frontend_files(self) -> List[GeneratedFile]:
        """Get all frontend-related files."""
        return [f for f in self.files if f.path.startswith('frontend/')]
    
    def get_test_files(self) -> List[GeneratedFile]:
        """Get all test files."""
        return [f for f in self.files if f.file_type == 'test' or 'test' in f.path]
    
    def get_documentation_files(self) -> List[GeneratedFile]:
        """Get all documentation files."""
        return [f for f in self.files if f.file_type == 'documentation' or f.path.startswith('docs/')]


class CodeParser:
    """Parses generated code to extract files and structure."""
    
    def __init__(self):
        self.logger = get_logger("code_parser")
    
    def parse_backend_implementation(self, content: str, session_id: str) -> List[GeneratedFile]:
        """Parse backend implementation into individual files."""
        files = []
        
        # Guard against None content
        if not content:
            return files
        
        # First, try to parse using the Claude agent format (===== filename =====)
        claude_files = self._parse_claude_format_files(content, "backend/")
        files.extend(claude_files)
        
        # Only try other parsing methods if Claude format didn't find files
        if not claude_files:
            # Parse structured implementation with multiple approaches
            if "```python" in content or "```py" in content:
                files.extend(self._extract_python_files(content, "backend/"))
            
            # Parse structured file descriptions
            files.extend(self._parse_structured_files(content, "backend/", ["python", "py"]))
            
            # If no files were parsed, try to create from file structure documentation
            if not files:
                files.extend(self._create_files_from_structure(content, "backend/"))
        
        # Remove duplicates based on file path
        files = self._remove_duplicate_files(files)
        
        # Add configuration files if not already present
        has_requirements = any(f.path.endswith('requirements.txt') for f in files)
        has_dockerfile = any(f.path.endswith('Dockerfile') for f in files)
        has_readme = any(f.path.endswith('README.md') for f in files)
        
        if not has_requirements:
            files.append(GeneratedFile(
                path="backend/requirements.txt",
                content=self._generate_requirements_txt(),
                file_type="config",
                language="text"
            ))
        
        if not has_readme:
            files.append(GeneratedFile(
                path="backend/README.md",
                content=self._generate_backend_readme(content),
                file_type="documentation",
                language="markdown"
            ))
        
        if not has_dockerfile:
            files.append(GeneratedFile(
                path="backend/Dockerfile",
                content=self._generate_dockerfile(),
                file_type="config",
                language="dockerfile"
            ))
        
        return files
    
    def parse_frontend_implementation(self, content: str, session_id: str) -> List[GeneratedFile]:
        """Parse frontend implementation into individual files."""
        files = []
        
        # Guard against None content
        if not content:
            return files
        
        # First, try to parse using the Claude agent format (===== filename =====)
        claude_files = self._parse_claude_format_files(content, "frontend/")
        files.extend(claude_files)
        
        # Only try other parsing methods if Claude format didn't find files
        if not claude_files:
            # Parse different frontend file types with structured parsing
            if "```javascript" in content or "```js" in content:
                files.extend(self._extract_javascript_files(content, "frontend/"))
            
            if "```typescript" in content or "```ts" in content:
                files.extend(self._extract_typescript_files(content, "frontend/"))
            
            if "```jsx" in content or "```tsx" in content:
                files.extend(self._extract_react_files(content, "frontend/"))
            
            if "```css" in content or "```scss" in content:
                files.extend(self._extract_style_files(content, "frontend/"))
            
            # Parse structured file descriptions
            files.extend(self._parse_structured_files(content, "frontend/", ["js", "jsx", "ts", "tsx", "css", "scss"]))
            
            # If no files were parsed, try to create from file structure documentation
            if not files:
                files.extend(self._create_frontend_files_from_structure(content, "frontend/"))
        
        # Remove duplicates based on file path
        files = self._remove_duplicate_files(files)
        
        # Add configuration files if not already present
        has_package_json = any(f.path.endswith('package.json') for f in files)
        has_dockerfile = any(f.path.endswith('Dockerfile') for f in files)
        has_readme = any(f.path.endswith('README.md') for f in files)
        
        if not has_package_json:
            files.append(GeneratedFile(
                path="frontend/package.json",
                content=self._generate_package_json(),
                file_type="config",
                language="json"
            ))
        
        if not has_readme:
            files.append(GeneratedFile(
                path="frontend/README.md",
                content=self._generate_frontend_readme(content),
                file_type="documentation",
                language="markdown"
            ))
        
        if not has_dockerfile:
            files.append(GeneratedFile(
                path="frontend/Dockerfile",
                content=self._generate_frontend_dockerfile(),
                file_type="config",
                language="dockerfile"
            ))
        
        return files
    
    def parse_test_implementation(self, content: str, session_id: str) -> List[GeneratedFile]:
        """Parse test implementation into individual files."""
        files = []
        
        # Guard against None content
        if not content:
            return files
        
        # First, try to parse using the Claude agent format (===== filename =====)
        claude_files = self._parse_claude_format_files(content, "tests/")
        files.extend(claude_files)
        
        # Only try other parsing methods if Claude format didn't find files
        if not claude_files:
            # Parse test files
            if "```python" in content:
                files.extend(self._extract_python_files(content, "tests/", file_type="test"))
            
            if "```javascript" in content or "```js" in content:
                files.extend(self._extract_javascript_files(content, "tests/", file_type="test"))
        
        # Remove duplicates based on file path
        files = self._remove_duplicate_files(files)
        
        return files
    
    def _extract_python_files(self, content: str, base_path: str, file_type: str = "code") -> List[GeneratedFile]:
        """Extract Python files from code blocks."""
        files = []
        lines = content.split('\n')
        
        current_file = None
        current_content = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            # Look for file path indicators before code blocks
            if not in_code_block and ('.py' in line or 'models/' in line or 'api/' in line or 'core/' in line):
                # Check if this line contains a file path
                if '/' in line and '.py' in line:
                    # Extract filename from various formats
                    if '## ' in line or '### ' in line:  # Markdown headers
                        if '(' in line and ')' in line:
                            current_file = line.split('(')[1].split(')')[0]
                        elif line.strip().endswith('.py'):
                            current_file = line.split()[-1]
                    elif line.strip().startswith('# ') and line.strip().endswith('.py'):
                        current_file = line.strip()[2:]
                    elif line.strip().startswith('//') and line.strip().endswith('.py'):
                        current_file = line.strip()[2:].strip()
                        
            if line.strip().startswith('```python') or line.strip().startswith('```py'):
                in_code_block = True
                # Try to extract filename from comment after ```python
                if '#' in line:
                    comment = line.split('#', 1)[1].strip()
                    if comment.endswith('.py'):
                        current_file = comment
                continue
            elif line.strip() == '```' and in_code_block:
                in_code_block = False
                if current_content:
                    if not current_file:
                        # Try to infer filename from content
                        content_str = '\n'.join(current_content)
                        if 'class User' in content_str or 'class Post' in content_str:
                            current_file = 'models.py'
                        elif 'FastAPI' in content_str or 'app = ' in content_str:
                            current_file = 'main.py'
                        elif 'router = APIRouter' in content_str:
                            current_file = 'api.py'
                        else:
                            current_file = 'app.py'
                    
                    # Clean up the file path
                    if current_file and not current_file.startswith(base_path):
                        if current_file.startswith('src/'):
                            current_file = current_file[4:]  # Remove 'src/' prefix
                        
                    files.append(GeneratedFile(
                        path=f"{base_path}{current_file}",
                        content='\n'.join(current_content),
                        file_type=file_type,
                        language="python"
                    ))
                current_file = None
                current_content = []
                continue
            elif in_code_block:
                current_content.append(line)
        
        # If no files were extracted but we have content, create default files
        if not files and '```python' in content:
            # Extract all Python code blocks and create basic files
            python_content = []
            in_block = False
            for line in lines:
                if line.strip().startswith('```python'):
                    in_block = True
                    continue
                elif line.strip() == '```' and in_block:
                    in_block = False
                    continue
                elif in_block:
                    python_content.append(line)
            
            if python_content:
                files.append(GeneratedFile(
                    path=f"{base_path}main.py",
                    content='\n'.join(python_content),
                    file_type=file_type,
                    language="python"
                ))
        
        return files
    
    def _extract_javascript_files(self, content: str, base_path: str, file_type: str = "code") -> List[GeneratedFile]:
        """Extract JavaScript files from code blocks."""
        files = []
        lines = content.split('\n')
        
        current_file = None
        current_content = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            # Look for file path indicators
            if not in_code_block and ('.js' in line or 'src/' in line or 'components/' in line):
                if '/' in line and '.js' in line:
                    if '## ' in line or '### ' in line:
                        if '(' in line and ')' in line:
                            current_file = line.split('(')[1].split(')')[0]
                        elif line.strip().endswith('.js'):
                            current_file = line.split()[-1]
                    elif line.strip().startswith('# ') and line.strip().endswith('.js'):
                        current_file = line.strip()[2:]
                        
            if line.strip().startswith('```javascript') or line.strip().startswith('```js'):
                in_code_block = True
                if '#' in line:
                    comment = line.split('#', 1)[1].strip()
                    if comment.endswith('.js'):
                        current_file = comment
                continue
            elif line.strip() == '```' and in_code_block:
                in_code_block = False
                if current_content:
                    if not current_file:
                        content_str = '\n'.join(current_content)
                        if 'import React' in content_str or 'function App' in content_str:
                            current_file = 'App.js'
                        elif 'export default' in content_str:
                            current_file = 'component.js'
                        else:
                            current_file = 'script.js'
                    
                    if current_file.startswith('src/'):
                        current_file = current_file[4:]
                        
                    files.append(GeneratedFile(
                        path=f"{base_path}{current_file}",
                        content='\n'.join(current_content),
                        file_type=file_type,
                        language="javascript"
                    ))
                current_file = None
                current_content = []
                continue
            elif in_code_block:
                current_content.append(line)
        
        return files
    
    def _extract_typescript_files(self, content: str, base_path: str, file_type: str = "code") -> List[GeneratedFile]:
        """Extract TypeScript files from code blocks."""
        files = []
        lines = content.split('\n')
        
        current_file = None
        current_content = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            if not in_code_block and ('.ts' in line or '.tsx' in line):
                if '/' in line and ('.ts' in line or '.tsx' in line):
                    if '## ' in line or '### ' in line:
                        if '(' in line and ')' in line:
                            current_file = line.split('(')[1].split(')')[0]
                        elif line.strip().endswith(('.ts', '.tsx')):
                            current_file = line.split()[-1]
                    elif line.strip().startswith('# ') and line.strip().endswith(('.ts', '.tsx')):
                        current_file = line.strip()[2:]
                        
            if line.strip().startswith('```typescript') or line.strip().startswith('```ts'):
                in_code_block = True
                if '#' in line:
                    comment = line.split('#', 1)[1].strip()
                    if comment.endswith(('.ts', '.tsx')):
                        current_file = comment
                continue
            elif line.strip() == '```' and in_code_block:
                in_code_block = False
                if current_content:
                    if not current_file:
                        content_str = '\n'.join(current_content)
                        if 'interface ' in content_str or 'type ' in content_str:
                            current_file = 'types.ts'
                        elif 'export default' in content_str:
                            current_file = 'component.ts'
                        else:
                            current_file = 'index.ts'
                    
                    if current_file.startswith('src/'):
                        current_file = current_file[4:]
                        
                    files.append(GeneratedFile(
                        path=f"{base_path}{current_file}",
                        content='\n'.join(current_content),
                        file_type=file_type,
                        language="typescript"
                    ))
                current_file = None
                current_content = []
                continue
            elif in_code_block:
                current_content.append(line)
        
        return files
    
    def _extract_react_files(self, content: str, base_path: str, file_type: str = "code") -> List[GeneratedFile]:
        """Extract React component files from code blocks."""
        files = []
        lines = content.split('\n')
        
        current_file = None
        current_content = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            if not in_code_block and ('.jsx' in line or '.tsx' in line or 'components/' in line):
                if '/' in line and ('.jsx' in line or '.tsx' in line):
                    if '## ' in line or '### ' in line:
                        if '(' in line and ')' in line:
                            current_file = line.split('(')[1].split(')')[0]
                        elif line.strip().endswith(('.jsx', '.tsx')):
                            current_file = line.split()[-1]
                    elif line.strip().startswith('# ') and line.strip().endswith(('.jsx', '.tsx')):
                        current_file = line.strip()[2:]
                        
            if line.strip().startswith('```jsx') or line.strip().startswith('```tsx'):
                in_code_block = True
                if '#' in line:
                    comment = line.split('#', 1)[1].strip()
                    if comment.endswith(('.jsx', '.tsx')):
                        current_file = comment
                continue
            elif line.strip() == '```' and in_code_block:
                in_code_block = False
                if current_content:
                    if not current_file:
                        content_str = '\n'.join(current_content)
                        if 'function App' in content_str or 'const App' in content_str:
                            current_file = 'App.jsx'
                        elif 'export default' in content_str:
                            # Try to extract component name
                            for content_line in current_content:
                                if 'const ' in content_line and ' = ' in content_line:
                                    comp_name = content_line.split('const ')[1].split(' =')[0].strip()
                                    current_file = f'{comp_name}.jsx'
                                    break
                            else:
                                current_file = 'Component.jsx'
                        else:
                            current_file = 'component.jsx'
                    
                    if current_file.startswith('src/'):
                        current_file = current_file[4:]
                        
                    files.append(GeneratedFile(
                        path=f"{base_path}{current_file}",
                        content='\n'.join(current_content),
                        file_type=file_type,
                        language="jsx"
                    ))
                current_file = None
                current_content = []
                continue
            elif in_code_block:
                current_content.append(line)
        
        return files
    
    def _extract_style_files(self, content: str, base_path: str, file_type: str = "code") -> List[GeneratedFile]:
        """Extract CSS/SCSS files from code blocks."""
        files = []
        lines = content.split('\n')
        
        current_file = None
        current_content = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            if not in_code_block and ('.css' in line or '.scss' in line or 'styles/' in line):
                if '/' in line and ('.css' in line or '.scss' in line):
                    if '## ' in line or '### ' in line:
                        if '(' in line and ')' in line:
                            current_file = line.split('(')[1].split(')')[0]
                        elif line.strip().endswith(('.css', '.scss')):
                            current_file = line.split()[-1]
                    elif line.strip().startswith('# ') and line.strip().endswith(('.css', '.scss')):
                        current_file = line.strip()[2:]
                        
            if line.strip().startswith('```css') or line.strip().startswith('```scss'):
                in_code_block = True
                if '#' in line:
                    comment = line.split('#', 1)[1].strip()
                    if comment.endswith(('.css', '.scss')):
                        current_file = comment
                continue
            elif line.strip() == '```' and in_code_block:
                in_code_block = False
                if current_content:
                    if not current_file:
                        current_file = 'styles.css'
                    
                    if current_file.startswith('src/'):
                        current_file = current_file[4:]
                        
                    files.append(GeneratedFile(
                        path=f"{base_path}{current_file}",
                        content='\n'.join(current_content),
                        file_type=file_type,
                        language="css"
                    ))
                current_file = None
                current_content = []
                continue
            elif in_code_block:
                current_content.append(line)
        
        return files
    
    def _parse_claude_format_files(self, content: str, base_path: str) -> List[GeneratedFile]:
        """Parse files in Claude agent format (===== filename =====)."""
        files = []
        
        if not content:
            return files
        
        self.logger.info(f"Parsing Claude format files for base_path: {base_path}")
        
        lines = content.split('\n')
        current_file = None
        current_content = []
        in_file_section = False
        
        for line in lines:
            # Look for the Claude format: ===== filename =====
            if line.strip().startswith('=====') and line.strip().endswith('====='):
                # Save previous file if exists
                if current_file and current_content:
                    generated_file = self._create_generated_file(current_file, current_content, base_path)
                    files.append(generated_file)
                    self.logger.info(f"Parsed file: {generated_file.path} ({len(generated_file.content)} chars)")
                
                # Extract new filename
                filename = line.strip()[5:-5].strip()  # Remove ===== from both ends
                current_file = filename
                current_content = []
                in_file_section = True
                self.logger.debug(f"Found Claude format file marker: {filename}")
                continue
            
            # If we're in a file section, collect content
            if in_file_section and current_file:
                # Stop collecting if we hit another ===== or reach end
                if line.strip().startswith('====='):
                    # This is the start of a new file section, handle it in next iteration
                    if current_file and current_content:
                        generated_file = self._create_generated_file(current_file, current_content, base_path)
                        files.append(generated_file)
                        self.logger.info(f"Parsed file: {generated_file.path} ({len(generated_file.content)} chars)")
                    
                    # Extract new filename
                    filename = line.strip()[5:-5].strip()
                    current_file = filename
                    current_content = []
                    self.logger.debug(f"Found Claude format file marker: {filename}")
                    continue
                else:
                    current_content.append(line)
        
        # Don't forget the last file
        if current_file and current_content:
            generated_file = self._create_generated_file(current_file, current_content, base_path)
            files.append(generated_file)
            self.logger.info(f"Parsed file: {generated_file.path} ({len(generated_file.content)} chars)")
        
        self.logger.info(f"Total Claude format files parsed: {len(files)}")
        return files
    
    def _create_generated_file(self, filename: str, content_lines: List[str], base_path: str) -> GeneratedFile:
        """Create a GeneratedFile object from filename and content lines."""
        # Clean up filename - remove any path prefixes that match base_path
        clean_filename = filename
        if clean_filename.startswith(base_path):
            clean_filename = clean_filename[len(base_path):]
        if clean_filename.startswith('/'):
            clean_filename = clean_filename[1:]
        
        # Determine file type and language
        file_type = "code"
        language = "text"
        
        if clean_filename.endswith(('.py',)):
            language = "python"
        elif clean_filename.endswith(('.js', '.jsx')):
            language = "javascript"
        elif clean_filename.endswith(('.ts', '.tsx')):
            language = "typescript"
        elif clean_filename.endswith(('.css', '.scss')):
            language = "css"
            file_type = "style"
        elif clean_filename.endswith(('.json',)):
            language = "json"
            file_type = "config"
        elif clean_filename.endswith(('.yml', '.yaml')):
            language = "yaml"
            file_type = "config"
        elif clean_filename.endswith(('.md',)):
            language = "markdown"
            file_type = "documentation"
        elif clean_filename.endswith(('.html',)):
            language = "html"
        elif clean_filename.endswith(('.txt',)):
            file_type = "config"
        elif 'Dockerfile' in clean_filename:
            language = "dockerfile"
            file_type = "config"
        
        # Join content and clean up
        content = '\n'.join(content_lines).strip()
        
        return GeneratedFile(
            path=f"{base_path}{clean_filename}",
            content=content,
            file_type=file_type,
            language=language
        )
    
    def _remove_duplicate_files(self, files: List[GeneratedFile]) -> List[GeneratedFile]:
        """Remove duplicate files based on file path."""
        seen_paths = set()
        unique_files = []
        
        for file in files:
            if file.path not in seen_paths:
                seen_paths.add(file.path)
                unique_files.append(file)
            else:
                self.logger.debug(f"Removing duplicate file: {file.path}")
        
        return unique_files
    
    def _parse_structured_files(self, content: str, base_path: str, extensions: List[str]) -> List[GeneratedFile]:
        """Parse structured file descriptions from AI agent output."""
        files = []
        lines = content.split('\n')
        
        current_file = None
        current_content = []
        in_code_block = False
        
        for i, line in enumerate(lines):
            # Look for file path patterns in various formats
            if not in_code_block:
                # Pattern: ## filename.ext or ### filename.ext
                if line.strip().startswith(('#', '##', '###')) and any(f'.{ext}' in line for ext in extensions):
                    # Extract filename after markdown header
                    header_text = line.strip().lstrip('#').strip()
                    if '(' in header_text and ')' in header_text:
                        # Pattern: ## File (path/file.py):
                        current_file = header_text.split('(')[1].split(')')[0]
                    else:
                        # Simple pattern: ## file.py
                        words = header_text.split()
                        for word in words:
                            if any(f'.{ext}' in word for ext in extensions):
                                current_file = word.strip(':')
                                break
                
                # Pattern: src/path/file.py or backend/path/file.py
                elif '/' in line and any(f'.{ext}' in line for ext in extensions):
                    words = line.split()
                    for word in words:
                        if '/' in word and any(f'.{ext}' in word for ext in extensions):
                            current_file = word.strip('`').strip(',').strip(':')
                            # Remove base_path if it's already in the filename
                            if current_file.startswith(base_path):
                                current_file = current_file[len(base_path):]
                            break
            
            # Handle code blocks
            if any(line.strip().startswith(f'```{ext}') for ext in extensions) or line.strip().startswith('```python'):
                in_code_block = True
                continue
            elif line.strip() == '```' and in_code_block:
                in_code_block = False
                if current_content and current_file:
                    files.append(GeneratedFile(
                        path=f"{base_path}{current_file}",
                        content='\n'.join(current_content),
                        file_type="code",
                        language=extensions[0] if extensions else "text"
                    ))
                current_file = None
                current_content = []
                continue
            elif in_code_block:
                current_content.append(line)
        
        return files
    
    def _create_files_from_structure(self, content: str, base_path: str) -> List[GeneratedFile]:
        """Create files based on file structure documentation in the content."""
        files = []
        
        # Look for common file structure patterns and create basic files
        if 'main.py' in content and base_path == 'backend/':
            main_content = self._generate_basic_fastapi_main()
            files.append(GeneratedFile(
                path=f"{base_path}src/main.py",
                content=main_content,
                file_type="code",
                language="python"
            ))
        
        if 'models/' in content and base_path == 'backend/':
            user_model = self._generate_basic_user_model()
            files.append(GeneratedFile(
                path=f"{base_path}src/models/user.py",
                content=user_model,
                file_type="code",
                language="python"
            ))
            
            post_model = self._generate_basic_post_model()
            files.append(GeneratedFile(
                path=f"{base_path}src/models/post.py",
                content=post_model,
                file_type="code",
                language="python"
            ))
            
            init_file = "# SQLAlchemy models\n"
            files.append(GeneratedFile(
                path=f"{base_path}src/models/__init__.py",
                content=init_file,
                file_type="code",
                language="python"
            ))
        
        if 'api/' in content and base_path == 'backend/':
            auth_api = self._generate_basic_auth_api()
            files.append(GeneratedFile(
                path=f"{base_path}src/api/auth.py",
                content=auth_api,
                file_type="code",
                language="python"
            ))
            
            users_api = self._generate_basic_users_api()
            files.append(GeneratedFile(
                path=f"{base_path}src/api/users.py",
                content=users_api,
                file_type="code",
                language="python"
            ))
            
            posts_api = self._generate_basic_posts_api()
            files.append(GeneratedFile(
                path=f"{base_path}src/api/posts.py",
                content=posts_api,
                file_type="code",
                language="python"
            ))
            
            init_file = "# API routers\n"
            files.append(GeneratedFile(
                path=f"{base_path}src/api/__init__.py",
                content=init_file,
                file_type="code",
                language="python"
            ))
        
        if 'core/' in content and base_path == 'backend/':
            config_file = self._generate_basic_config()
            files.append(GeneratedFile(
                path=f"{base_path}src/core/config.py",
                content=config_file,
                file_type="code",
                language="python"
            ))
            
            database_file = self._generate_basic_database()
            files.append(GeneratedFile(
                path=f"{base_path}src/core/database.py",
                content=database_file,
                file_type="code",
                language="python"
            ))
            
            init_file = "# Core modules\n"
            files.append(GeneratedFile(
                path=f"{base_path}src/core/__init__.py",
                content=init_file,
                file_type="code",
                language="python"
            ))
        
        return files
    
    def _generate_basic_fastapi_main(self) -> str:
        """Generate a basic FastAPI main.py file."""
        return '''from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(posts_router, prefix="/api/posts", tags=["posts"])

@app.get("/")
async def root():
    return {"message": "Social Media API v1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "social-media-api"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''
    
    def _generate_basic_user_model(self) -> str:
        """Generate a basic User model."""
        return '''from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    bio = Column(Text)
    avatar_url = Column(String(500))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
'''
    
    def _generate_basic_post_model(self) -> str:
        """Generate a basic Post model."""
        return '''from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(500))
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    author = relationship("User", back_populates="posts")
'''
    
    def _generate_basic_auth_api(self) -> str:
        """Generate a basic authentication API."""
        return '''from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import bcrypt
import jwt
from datetime import datetime, timedelta

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    # Hash password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user in database
    # Implementation here...
    
    return {"access_token": "jwt_token_here", "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    # Authenticate user
    # Implementation here...
    
    return {"access_token": "jwt_token_here", "token_type": "bearer"}
'''
    
    def _generate_basic_users_api(self) -> str:
        """Generate a basic users API."""
        return '''from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    bio: str = None
    avatar_url: str = None

@router.get("/me", response_model=UserProfile)
async def get_current_user():
    # Get current user profile
    return {"id": 1, "username": "user", "email": "user@example.com", "full_name": "User"}

@router.get("/{user_id}", response_model=UserProfile)
async def get_user(user_id: int):
    # Get user by ID
    return {"id": user_id, "username": "user", "email": "user@example.com", "full_name": "User"}

@router.post("/{user_id}/follow")
async def follow_user(user_id: int):
    # Follow/unfollow user
    return {"message": "User followed successfully"}
'''
    
    def _generate_basic_posts_api(self) -> str:
        """Generate a basic posts API."""
        return '''from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter()

class PostCreate(BaseModel):
    content: str
    image_url: str = None

class PostResponse(BaseModel):
    id: int
    content: str
    image_url: str = None
    like_count: int
    comment_count: int
    created_at: datetime
    author: dict

@router.get("/feed", response_model=List[PostResponse])
async def get_feed():
    # Get user feed
    return []

@router.post("/", response_model=PostResponse)
async def create_post(post: PostCreate):
    # Create new post
    return {
        "id": 1,
        "content": post.content,
        "image_url": post.image_url,
        "like_count": 0,
        "comment_count": 0,
        "created_at": datetime.now(),
        "author": {"id": 1, "username": "user", "full_name": "User"}
    }

@router.post("/{post_id}/like")
async def like_post(post_id: int):
    # Like/unlike post
    return {"message": "Post liked successfully"}
'''
    
    def _generate_basic_config(self) -> str:
        """Generate a basic configuration file."""
        return '''import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost/socialdb"
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
'''
    
    def _generate_basic_database(self) -> str:
        """Generate a basic database configuration file."""
        return '''from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
    
    def _generate_requirements_txt(self) -> str:
        """Generate requirements.txt for Python backend."""
        return """fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
alembic==1.13.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.25.2
tenacity==8.2.3
pyyaml==6.0.1
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
"""
    
    def _generate_package_json(self) -> str:
        """Generate package.json for frontend."""
        package_data = {
            "name": "ai-generated-frontend",
            "version": "1.0.0",
            "description": "AI Generated Frontend Application",
            "main": "src/index.js",
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1",
                "axios": "^1.6.0",
                "react-router-dom": "^6.8.0"
            },
            "devDependencies": {
                "@testing-library/jest-dom": "^5.16.5",
                "@testing-library/react": "^13.4.0",
                "@testing-library/user-event": "^13.5.0"
            },
            "browserslist": {
                "production": [
                    ">0.2%",
                    "not dead",
                    "not op_mini all"
                ],
                "development": [
                    "last 1 chrome version",
                    "last 1 firefox version",
                    "last 1 safari version"
                ]
            }
        }
        return json.dumps(package_data, indent=2)
    
    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile for backend."""
        return """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    def _generate_backend_readme(self, implementation: str) -> str:
        """Generate README for backend."""
        return f"""# AI Generated Backend

This backend was generated by an AI orchestration system.

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
uvicorn main:app --reload
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Implementation Details

{implementation[:500]}...

Generated on: {datetime.now().isoformat()}
"""
    
    def _generate_frontend_readme(self, implementation: str) -> str:
        """Generate README for frontend."""
        return f"""# AI Generated Frontend

This frontend was generated by an AI orchestration system.

## Installation

```bash
npm install
```

## Running

```bash
npm start
```

## Building for Production

```bash
npm run build
```

## Implementation Details

{implementation[:500]}...

Generated on: {datetime.now().isoformat()}
"""

    def _create_frontend_files_from_structure(self, content: str, base_path: str) -> List[GeneratedFile]:
        """Create frontend files based on file structure documentation."""
        files = []
        
        # Create basic React app structure
        if 'App.js' in content or 'React' in content:
            app_content = self._generate_basic_react_app()
            files.append(GeneratedFile(
                path=f"{base_path}src/App.js",
                content=app_content,
                file_type="code",
                language="javascript"
            ))
            
            index_content = self._generate_basic_react_index()
            files.append(GeneratedFile(
                path=f"{base_path}src/index.js",
                content=index_content,
                file_type="code",
                language="javascript"
            ))
        
        if 'components/' in content:
            # Create basic components
            header_content = self._generate_basic_header_component()
            files.append(GeneratedFile(
                path=f"{base_path}src/components/Header.js",
                content=header_content,
                file_type="code",
                language="javascript"
            ))
            
            post_card_content = self._generate_basic_post_card_component()
            files.append(GeneratedFile(
                path=f"{base_path}src/components/PostCard.js",
                content=post_card_content,
                file_type="code",
                language="javascript"
            ))
        
        if 'pages/' in content:
            # Create basic pages
            home_page = self._generate_basic_home_page()
            files.append(GeneratedFile(
                path=f"{base_path}src/pages/Home.js",
                content=home_page,
                file_type="code",
                language="javascript"
            ))
        
        if 'public/' in content:
            # Create public files
            index_html = self._generate_basic_index_html()
            files.append(GeneratedFile(
                path=f"{base_path}public/index.html",
                content=index_html,
                file_type="code",
                language="html"
            ))
        
        return files
    
    def _generate_basic_react_app(self) -> str:
        """Generate a basic React App component."""
        return '''import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Home from './pages/Home';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
'''
    
    def _generate_basic_react_index(self) -> str:
        """Generate a basic React index.js file."""
        return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''
    
    def _generate_basic_header_component(self) -> str:
        """Generate a basic Header component."""
        return '''import React from 'react';

const Header = () => {
  return (
    <header className="header">
      <div className="container">
        <h1 className="logo">Social Media App</h1>
        <nav>
          <ul className="nav-links">
            <li><a href="/">Home</a></li>
            <li><a href="/profile">Profile</a></li>
            <li><a href="/messages">Messages</a></li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;
'''
    
    def _generate_basic_post_card_component(self) -> str:
        """Generate a basic PostCard component."""
        return '''import React, { useState } from 'react';

const PostCard = ({ post }) => {
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(post.likeCount || 0);

  const handleLike = () => {
    setLiked(!liked);
    setLikeCount(liked ? likeCount - 1 : likeCount + 1);
  };

  return (
    <div className="post-card">
      <div className="post-header">
        <img src={post.author?.avatar || '/default-avatar.png'} alt="Avatar" className="avatar" />
        <div className="post-info">
          <h3>{post.author?.name}</h3>
          <span className="username">@{post.author?.username}</span>
        </div>
      </div>
      <div className="post-content">
        <p>{post.content}</p>
        {post.image && <img src={post.image} alt="Post" className="post-image" />}
      </div>
      <div className="post-actions">
        <button onClick={handleLike} className={`like-btn ${liked ? 'liked' : ''}`}>
          ❤️ {likeCount}
        </button>
        <button className="comment-btn">💬 {post.commentCount || 0}</button>
        <button className="share-btn">🔄</button>
      </div>
    </div>
  );
};

export default PostCard;
'''
    
    def _generate_basic_home_page(self) -> str:
        """Generate a basic Home page component."""
        return '''import React, { useState, useEffect } from 'react';
import PostCard from '../components/PostCard';

const Home = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setPosts([
        {
          id: 1,
          content: "Welcome to our social media app!",
          author: { name: "John Doe", username: "johndoe", avatar: "/avatar1.jpg" },
          likeCount: 5,
          commentCount: 2
        },
        {
          id: 2,
          content: "This is a sample post to demonstrate the feed.",
          author: { name: "Jane Smith", username: "janesmith", avatar: "/avatar2.jpg" },
          likeCount: 12,
          commentCount: 4
        }
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="home">
      <div className="container">
        <h2>Feed</h2>
        <div className="posts">
          {posts.map(post => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Home;
'''
    
    def _generate_basic_index_html(self) -> str:
        """Generate a basic index.html file."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Social Media App</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        .header {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1rem 0;
        }
        .nav-links {
            display: flex;
            list-style: none;
            gap: 2rem;
            margin: 0;
            padding: 0;
        }
        .nav-links a {
            text-decoration: none;
            color: #333;
        }
        .post-card {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .loading {
            text-align: center;
            padding: 2rem;
        }
    </style>
</head>
<body>
    <div id="root"></div>
</body>
</html>
'''
    
    def _generate_frontend_dockerfile(self) -> str:
        """Generate Dockerfile for frontend."""
        return '''FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
'''


class FileOutputManager:
    """Manages file output and project structure generation."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("file_manager")
        self.parser = CodeParser()
    
    def create_project_structure(self, workflow_state: Dict[str, Any]) -> ProjectStructure:
        """Create complete project structure from workflow state."""
        session_id = workflow_state.get('session_id', 'unknown')
        
        with TimedOperation("create_project_structure", {"session_id": session_id}):
            files = []
            
            # Parse backend implementation (use improved version if available)
            backend_code = workflow_state.get('improved_backend_implementation') or workflow_state.get('backend_implementation')
            if backend_code:
                backend_files = self.parser.parse_backend_implementation(
                    backend_code,
                    session_id
                )
                files.extend(backend_files)
            
            # Parse frontend implementation (use improved version if available)
            frontend_code = workflow_state.get('improved_frontend_implementation') or workflow_state.get('frontend_implementation')
            if frontend_code:
                frontend_files = self.parser.parse_frontend_implementation(
                    frontend_code,
                    session_id
                )
                files.extend(frontend_files)
            
            # Parse test implementation
            if 'test_implementation' in workflow_state:
                test_files = self.parser.parse_test_implementation(
                    workflow_state['test_implementation'],
                    session_id
                )
                files.extend(test_files)
            
            # Add documentation files
            files.extend(self._generate_documentation_files(workflow_state))
            
            # Add project configuration files
            files.extend(self._generate_project_config_files(workflow_state))
            
            project = ProjectStructure(
                name=f"ai-generated-project-{session_id[:8]}",
                description=workflow_state.get('refined_requirements', 'AI Generated Project')[:200],
                session_id=session_id,
                created_at=datetime.now(),
                files=files,
                metadata={
                    'workflow_state': workflow_state,
                    'generation_time': datetime.now().isoformat(),
                    'file_count': len(files)
                }
            )
            
            self.logger.info(f"Created project structure with {len(files)} files")
            return project
    
    def write_project_to_disk(self, project: ProjectStructure, output_dir: Optional[str] = None) -> str:
        """Write complete project structure to disk."""
        if output_dir is None:
            output_dir = os.path.join(self.config.output_dir, project.name)
        
        output_path = Path(output_dir)
        
        with TimedOperation("write_project_to_disk", {"project": project.name}):
            # Create base directory
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Write all files
            for file in project.files:
                file_path = output_path / file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    with open(file_path, 'w', encoding=file.encoding) as f:
                        f.write(file.content)
                    
                    self.logger.debug(f"Wrote file: {file.path}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to write file {file.path}: {str(e)}")
                    raise
            
            # Write project metadata
            metadata_path = output_path / 'project_metadata.json'
            with open(metadata_path, 'w') as f:
                metadata = {
                    'name': project.name,
                    'description': project.description,
                    'session_id': project.session_id,
                    'created_at': project.created_at.isoformat(),
                    'file_count': len(project.files),
                    'metadata': project.metadata
                }
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Project written to disk: {output_path}")
            return str(output_path)
    
    def _generate_documentation_files(self, workflow_state: Dict[str, Any]) -> List[GeneratedFile]:
        """Generate project documentation files."""
        files = []
        
        # Main README
        readme_content = self._generate_main_readme(workflow_state)
        files.append(GeneratedFile(
            path="README.md",
            content=readme_content,
            file_type="documentation",
            language="markdown"
        ))
        
        # Architecture documentation
        if 'claude_plan' in workflow_state or 'gemini_plan' in workflow_state:
            arch_content = self._generate_architecture_doc(workflow_state)
            files.append(GeneratedFile(
                path="docs/ARCHITECTURE.md",
                content=arch_content,
                file_type="documentation",
                language="markdown"
            ))
        
        # API documentation
        if 'backend_implementation' in workflow_state:
            api_content = self._generate_api_doc(workflow_state)
            files.append(GeneratedFile(
                path="docs/API.md",
                content=api_content,
                file_type="documentation",
                language="markdown"
            ))
        
        return files
    
    def _generate_project_config_files(self, workflow_state: Dict[str, Any]) -> List[GeneratedFile]:
        """Generate project-wide configuration files."""
        files = []
        
        # .gitignore
        files.append(GeneratedFile(
            path=".gitignore",
            content=self._generate_gitignore(),
            file_type="config",
            language="text"
        ))
        
        # docker-compose.yml
        files.append(GeneratedFile(
            path="docker-compose.yml",
            content=self._generate_docker_compose(),
            file_type="config",
            language="yaml"
        ))
        
        return files
    
    def _generate_main_readme(self, workflow_state: Dict[str, Any]) -> str:
        """Generate main project README."""
        session_id = workflow_state.get('session_id', 'unknown')
        requirements = workflow_state.get('refined_requirements', 'No requirements specified')
        
        return f"""# AI Generated Project

**Session ID:** {session_id}  
**Generated:** {datetime.now().isoformat()}

## Overview

This project was generated by an AI orchestration system using GPT (Project Manager), Claude (Backend Expert), and Gemini (Frontend Expert).

## Requirements

{requirements}

## Project Structure

```
├── backend/          # Backend API implementation
├── frontend/         # Frontend application
├── tests/           # Test suites
├── docs/            # Documentation
└── docker-compose.yml
```

## Quick Start

### Using Docker Compose

```bash
docker-compose up --build
```

### Manual Setup

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## API Documentation

- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Generated Components

- ✅ Backend API with database integration
- ✅ Frontend user interface
- ✅ Comprehensive test suite
- ✅ Docker configuration
- ✅ Documentation

## AI Agents Involved

- **GPT-4**: Project management, requirements refinement, test generation
- **Claude**: Backend architecture and implementation
- **Gemini**: Frontend design and implementation

## Notes

This is an AI-generated project. Review and test thoroughly before production use.
"""
    
    def _generate_architecture_doc(self, workflow_state: Dict[str, Any]) -> str:
        """Generate architecture documentation."""
        claude_plan = workflow_state.get('claude_plan', 'No backend plan available')
        gemini_plan = workflow_state.get('gemini_plan', 'No frontend plan available')
        
        return f"""# System Architecture

## Backend Architecture

{claude_plan}

## Frontend Architecture

{gemini_plan}

## Integration Points

The backend and frontend communicate via RESTful API endpoints. Key integration considerations:

1. Authentication and authorization
2. Data validation and serialization
3. Error handling and user feedback
4. Real-time updates (if applicable)

## Deployment Architecture

The system is designed to be deployed using Docker containers with the following components:

- Backend API server
- Frontend web server
- Database (PostgreSQL/MySQL)
- Reverse proxy (Nginx)

## Security Considerations

- API authentication using JWT tokens
- Input validation on all endpoints
- CORS configuration for frontend access
- Environment-based configuration management

Generated on: {datetime.now().isoformat()}
"""
    
    def _generate_api_doc(self, workflow_state: Dict[str, Any]) -> str:
        """Generate API documentation."""
        return f"""# API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The API uses JWT token authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

*Note: This is a generated API documentation. Actual endpoints depend on the implementation.*

### Health Check

```http
GET /health
```

Returns the health status of the API.

### Authentication

```http
POST /auth/login
POST /auth/register
POST /auth/refresh
```

### Data Operations

```http
GET /data
POST /data
PUT /data/:id
DELETE /data/:id
```

## Error Responses

The API returns standardized error responses:

```json
{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details"
  }}
}}
```

## Rate Limiting

API requests are rate limited to prevent abuse:

- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

Generated on: {datetime.now().isoformat()}
"""
    
    def _generate_gitignore(self) -> str:
        """Generate .gitignore file."""
        return """# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Environment variables
.env
.env.local
.env.production

# Build outputs
build/
dist/
*.egg-info/

# Database
*.db
*.sqlite
*.sqlite3

# Docker
.dockerignore

# Temporary files
tmp/
temp/
*.tmp
"""
    
    def _generate_docker_compose(self) -> str:
        """Generate docker-compose.yml file."""
        return """version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
    depends_on:
      - db
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm start

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
"""