# 🤝 Contributing to AutoSquad

Thank you for your interest in contributing to AutoSquad! This guide will help you get started with development and understand how to contribute effectively to this AI-powered autonomous development framework.

## 🌟 What is AutoSquad?

AutoSquad is a production-ready framework that creates autonomous AI development teams using Microsoft's AutoGen. Our latest v0.2 release features:

- **69% Token Cost Reduction** through intelligent context optimization
- **Real-Time Progress Display** with beautiful terminal UI
- **Professional Tooling** for AI-powered software development
- **Extensible Architecture** built on AutoGen foundation

## 🚀 Quick Start for Contributors

### 1. Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-org/autosquad.git
cd autosquad

# Create virtual environment (recommended)
python -m venv autosquad-dev
source autosquad-dev/bin/activate  # On Windows: autosquad-dev\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black flake8 mypy

# Verify installation
python test_install.py
```

### 2. Set Up Environment Variables

```bash
# Required for testing with real AI agents
export OPENAI_API_KEY="your-openai-api-key"

# Optional: Custom config directory
export AUTOSQUAD_CONFIG_DIR="~/.autosquad-dev"
```

### 3. Run Tests

```bash
# Run the test suite
pytest

# Run with coverage
pytest --cov=squad_runner

# Run specific test categories
pytest -m "not integration"  # Skip integration tests
pytest -m "token_optimization"  # Only token optimization tests
```

### 4. Try AutoSquad

```bash
# Test with the example project
python -m squad_runner.cli run --project projects/example-cli-tool --rounds 2 --verbose

# Or create your own test project
mkdir test-project
echo "Build a simple Python calculator" > test-project/prompt.txt
python -m squad_runner.cli run --project test-project --rounds 2
```

## 🏗️ Project Structure & Architecture

### Core Components

```
squad_runner/
├── __init__.py              # Main package
├── cli.py                   # Command-line interface (Click + Rich)
├── orchestrator.py          # Main orchestration with token optimization
├── token_optimization.py    # Context compression & cost management
├── progress_display.py      # Real-time terminal UI
├── project_manager.py       # Workspace & logging management
├── config.py               # YAML configuration system
├── tools.py                # Function calling tools for agents
└── agents/
    ├── __init__.py          # Agent factory
    ├── base.py              # BaseSquadAgent with progress tracking
    ├── engineer.py          # Code implementation specialist
    ├── architect.py         # Code review & architecture specialist
    ├── pm.py                # Requirements & project management
    └── qa.py                # Quality assurance & testing
```

### Key Technologies

- **AutoGen**: Microsoft's multi-agent framework (our foundation)
- **Rich**: Beautiful terminal UI components
- **tiktoken**: Accurate token counting for OpenAI models
- **Click**: Command-line interface framework
- **PyYAML**: Configuration management
- **asyncio**: Asynchronous operations

## 🎯 Ways to Contribute

### 🐛 Bug Reports & Issues

**Before reporting a bug:**
1. Check existing issues to avoid duplicates
2. Test with the latest version
3. Gather relevant logs and error messages

**Good bug reports include:**
- Clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs from `project/logs/` directory
- Token usage information if applicable

### 💡 Feature Requests

**Feature request guidelines:**
- Search existing issues first
- Describe the problem you're trying to solve
- Explain how this would benefit AutoSquad users
- Consider implementation complexity and scope
- Provide mockups or examples if applicable

**Current priority areas:**
- Code execution environment (v0.3)
- Git integration and version control
- New agent types (DevOps, Security, etc.)
- Performance optimizations
- Integration improvements

### 🔧 Code Contributions

#### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/autosquad.git
   cd autosquad
   git remote add upstream https://github.com/original-org/autosquad.git
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

3. **Make Changes**
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed
   - Test thoroughly

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add token optimization dashboard panel"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Use clear, descriptive title
   - Reference related issues
   - Include testing instructions
   - Add screenshots for UI changes

#### Coding Standards

**Python Style:**
```bash
# Format code with Black
black squad_runner/

# Check style with flake8
flake8 squad_runner/

# Type checking with mypy
mypy squad_runner/
```

**Code Guidelines:**
- Use type hints for all function parameters and return values
- Write descriptive docstrings for classes and methods
- Follow PEP 8 style guidelines
- Keep functions focused and single-purpose
- Add comprehensive error handling
- Include logging for debugging

**Example of good code style:**
```python
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TokenOptimizer:
    """Optimizes conversation context to reduce token usage."""
    
    def __init__(self, model: str, max_context_tokens: int = 6000):
        """Initialize the token optimizer.
        
        Args:
            model: OpenAI model name for token counting
            max_context_tokens: Maximum tokens to include in context
        """
        self.model = model
        self.max_context_tokens = max_context_tokens
        logger.info(f"Initialized TokenOptimizer for {model}")
    
    def optimize_context(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Optimize conversation context by removing older messages.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Optimized list of messages within token limits
            
        Raises:
            ValueError: If messages list is empty
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
            
        # Implementation here...
```

## 🧪 Testing Guidelines

### Test Categories

**Unit Tests**: Test individual components in isolation
```python
# tests/test_token_optimization.py
def test_token_counting():
    optimizer = TokenOptimizer("gpt-4")
    text = "Hello, world!"
    token_count = optimizer.count_tokens(text)
    assert token_count > 0
    assert isinstance(token_count, int)
```

**Integration Tests**: Test component interactions
```python
# tests/test_orchestrator_integration.py
async def test_orchestrator_with_progress_display():
    orchestrator = SquadOrchestrator(
        project_manager=mock_pm,
        config=test_config,
        squad_profile=test_profile,
        model="gpt-4",
        show_live_progress=True
    )
    
    progress_display = orchestrator.get_progress_display()
    assert progress_display is not None
    assert len(orchestrator.agents) > 0
```

**End-to-End Tests**: Test complete workflows
```python
# tests/test_e2e.py
async def test_complete_development_cycle():
    # Test full project creation, agent collaboration, and file generation
    result = await run_autosquad_test_project()
    assert result.success
    assert len(result.files_created) > 0
    assert result.token_usage.total_tokens < expected_limit
```

### Test Naming & Organization

```
tests/
├── unit/
│   ├── test_token_optimization.py
│   ├── test_progress_display.py
│   └── test_agents/
│       ├── test_base_agent.py
│       └── test_engineer_agent.py
├── integration/
│   ├── test_orchestrator_integration.py
│   └── test_autogen_integration.py
└── e2e/
    ├── test_complete_workflows.py
    └── test_cli_interface.py
```

## 📚 Documentation Contributions

### Types of Documentation

1. **Code Documentation**: Docstrings, type hints, inline comments
2. **API Documentation**: Function and class reference docs
3. **User Guides**: How-to guides and tutorials
4. **Architecture Documentation**: Design decisions and system overview

### Documentation Standards

**Docstring Format:**
```python
def create_agent(agent_type: str, config: Dict[str, Any]) -> BaseSquadAgent:
    """Create a specialized agent based on type and configuration.
    
    This factory function creates agents with role-specific prompts,
    tools, and capabilities based on the provided agent type.
    
    Args:
        agent_type: Type of agent to create ('engineer', 'architect', 'pm', 'qa')
        config: Configuration dictionary with agent settings
        
    Returns:
        Initialized agent instance ready for use in squad
        
    Raises:
        ValueError: If agent_type is not supported
        ConfigurationError: If config is invalid for agent type
        
    Example:
        >>> config = {"languages": ["python"], "focus": "web_development"}
        >>> engineer = create_agent("engineer", config)
        >>> engineer.name
        'Engineer'
    """
```

**README Updates:**
- Keep examples current and working
- Update feature lists when adding capabilities
- Include performance metrics and benchmarks
- Add troubleshooting information

## 🔄 Release Process

### Version Numbers

We follow semantic versioning (SemVer):
- **Major** (1.0.0): Breaking changes
- **Minor** (0.2.0): New features, backward compatible
- **Patch** (0.2.1): Bug fixes, backward compatible

### Release Checklist

**Pre-Release:**
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Performance benchmarks run
- [ ] Breaking changes documented
- [ ] Migration guide created (if needed)

**Release:**
- [ ] Update version numbers
- [ ] Create release notes
- [ ] Tag release in git
- [ ] Build and test distribution
- [ ] Update main documentation

## 🚀 Development Roadmap

### Current Priorities (v0.3)

1. **Code Execution Environment**
   - Docker-based sandboxed execution
   - Real-time output in progress display
   - Security controls and resource limits

2. **Git Integration**
   - Automatic repository initialization
   - Commit generation from agent activity
   - Branch management for features

3. **Enhanced Agents**
   - DevOps agent for deployment
   - Security agent for vulnerability scanning
   - Database agent for data modeling

### Future Opportunities

- **Web Interface**: Browser-based project management
- **Plugin System**: Community-contributed extensions
- **Enterprise Features**: Team collaboration and management
- **Performance Optimization**: Distributed execution and scaling

## 🤝 Community Guidelines

### Code of Conduct

- **Be respectful**: Treat all contributors with respect and kindness
- **Be inclusive**: Welcome contributors from all backgrounds and skill levels
- **Be constructive**: Provide helpful feedback and suggestions
- **Be collaborative**: Work together to improve AutoSquad

### Communication

- **GitHub Issues**: Bug reports, feature requests, technical discussions
- **Pull Requests**: Code contributions and reviews
- **Discussions**: General questions, ideas, and community feedback

### Recognition

We value all contributions! Contributors will be:
- Listed in project contributors
- Mentioned in release notes for significant contributions
- Invited to join the core contributor team for ongoing contributions

## 🆘 Getting Help

### Resources

- **Documentation**: Start with README.md and architecture docs
- **Examples**: Check `projects/example-cli-tool/` for working examples
- **Tests**: Look at test files for usage examples
- **Logs**: Check `project/logs/` for debugging information

### Common Issues

**Installation Problems:**
```bash
# Clear pip cache and reinstall
pip cache purge
pip install -r requirements.txt --force-reinstall
```

**Token Optimization Not Working:**
- Verify tiktoken installation: `pip show tiktoken`
- Check model name matches tiktoken supported models
- Enable verbose logging: `--verbose` flag

**Progress Display Issues:**
- Test terminal compatibility: `python -c "from rich.console import Console; Console().print('Test')"`
- Use headless mode if needed: `--no-live-display`
- Check terminal size: Rich requires minimum dimensions

**AutoGen Integration Issues:**
- Verify AutoGen version compatibility
- Check API key environment variable
- Test with simple conversation first

### Support Channels

1. **Search existing issues first**
2. **Create detailed bug report** with logs and reproduction steps
3. **Join community discussions** for questions and ideas
4. **Read documentation thoroughly** - many questions are answered there

---

## 🎉 Thank You!

Every contribution makes AutoSquad better! Whether you're fixing typos, adding features, or helping other users, your participation helps create better AI development tools for everyone.

**Ready to contribute?** Start by exploring the codebase, running the tests, and checking out our current issues. We look forward to your contributions! 🚀

---

*Last Updated: December 2024*  
*AutoSquad v0.2 - Token Optimization & Live Progress Display* 