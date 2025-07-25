# 🧠 AutoSquad - Autonomous Multi-Agent Development Framework

> **Turn simple prompts into working software with AI development teams**

AutoSquad is a cutting-edge framework that creates autonomous AI development teams using Microsoft's AutoGen. Give it a project prompt, and watch specialized AI agents collaborate to build complete, working applications.

## 🚀 **New in v0.2: Token Optimization & Live Progress**

✨ **69% Token Reduction** - Intelligent context management dramatically reduces OpenAI API costs  
✨ **Live Progress Display** - Real-time agent activity dashboard with beautiful terminal UI  
✨ **Cost Transparency** - Monitor token usage and costs as development happens  
✨ **Enhanced User Experience** - Watch your agents collaborate in real-time  

## 🎯 What AutoSquad Does

AutoSquad assembles **specialized AI agent teams** that work together to turn your ideas into reality:

- **🎯 PM Agent**: Analyzes requirements, breaks down features, manages scope
- **🧑‍💻 Engineer Agent**: Writes production-ready code, implements features, fixes bugs  
- **🏗️ Architect Agent**: Reviews code quality, suggests improvements, ensures scalability
- **🧪 QA Agent**: Tests functionality, finds edge cases, validates user experience

**Input**: A simple text description of what you want to build  
**Output**: Complete, working software with documentation and tests

## ⚡ Quick Start

### 1. Install AutoSquad

```bash
git clone https://github.com/your-org/autosquad.git
cd autosquad
pip install -r requirements.txt
```

### 2. Set Your OpenAI API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Create Your First Project

```bash
mkdir my-project
echo "Build a Python CLI tool that converts JSON to CSV with error handling" > my-project/prompt.txt
```

### 4. Launch Your AI Development Squad

```bash
# With live progress display (default)
autosquad run --project my-project --rounds 3

# For servers/automation (simple progress bars)
autosquad run --project my-project --rounds 3 --no-live-display
```

### 5. Watch Your Agents Work

Experience the new **live progress display**:

```
╭─ 🧠 AutoSquad - my-project ──────────────────────────────────────╮
│ Round 2/3 | Elapsed: 4m 23s | Files: 7 | Tokens: 12,847 (~$0.38) │
╰──────────────────────────────────────────────────────────────────╯

╭─ 🤖 Agent Status ──────────────────────────╮
│ Agent      │ Status        │ Current Action          │ Progress │
│ Engineer   │ 🟢 Active     │ Writing main.py         │ 3 tasks  │
│ Architect  │ 🟡 Recent     │ Reviewing structure     │ 2 tasks  │  
│ PM         │ ⚪ Waiting    │ Planning next features  │ 4 tasks  │
│ QA         │ ⚪ Waiting    │ Testing functionality   │ 1 tasks  │
╰────────────────────────────────────────────╯

╭─ 💬 Agent Activity ─────────────────────────────────────────────╮
│ 14:23:15 🤖 Engineer started: Writing main.py                   │
│ 14:23:18 📄 Engineer create: src/main.py                        │
│ 14:23:22 💬 Engineer: I've implemented the core CLI structure   │
│ 14:23:25 ✅ Engineer completed: Created main.py                 │
│ 14:23:28 🤖 Architect started: Reviewing structure              │
╰─────────────────────────────────────────────────────────────────╯
```

### 6. Get Your Results

Find your generated code in:
- **`my-project/workspace/`** - Your complete, working application
- **`my-project/logs/`** - Full conversation transcripts and development history

## 💰 Cost-Efficient Development

AutoSquad now includes **intelligent token optimization** that reduces OpenAI API costs by up to **69%**:

### Before vs After Token Usage

```
Traditional Approach:          AutoSquad Optimized:
Round 1: 1,200 tokens         Round 1: 1,200 tokens  
Round 2: 2,800 tokens         Round 2: 1,800 tokens ⬇️ 36% reduction
Round 3: 6,500 tokens         Round 3: 2,200 tokens ⬇️ 66% reduction  
Round 4: 15,000 tokens        Round 4: 2,600 tokens ⬇️ 83% reduction
Total: 25,500 tokens ($0.77)  Total: 7,800 tokens ($0.23) ⬇️ 69% savings
```

**Real-time cost monitoring** keeps you informed:
```bash
╭─ 💰 Cost Summary ───────────────────────────────────────────────╮
│ 💰 Token Usage Summary                                          │
│ Total Tokens: 23,492                                           │
│ API Calls: 31                                                   │
│ Estimated Cost: $0.7048                                        │
│ Avg Tokens/Call: 758                                           │
╰─────────────────────────────────────────────────────────────────╯
```

## 🛠️ Advanced Usage

### Squad Profiles

Choose the right team for your project:

```bash
# MVP Team - Fast prototyping (PM + Engineer + Architect)
autosquad run --squad-profile mvp-team --project my-app

# Full Stack Team - Complete applications (All agents + extended tools)
autosquad run --squad-profile full-stack --project my-app

# Research Team - Experimental projects (PM + Engineer + QA)
autosquad run --squad-profile research-team --project my-app
```

### Model Selection

```bash
# Use different models based on your needs and budget
autosquad run --model gpt-4-turbo --project my-app      # Best quality
autosquad run --model gpt-4 --project my-app            # Balanced
autosquad run --model gpt-3.5-turbo --project my-app    # Most economical
autosquad run --project projects/flowfoundry-marketing-site --model gpt-4o-mini --rounds 3 --squad-profile full-stack
```

### Development Rounds & Reflection

```bash
# Run more rounds for complex projects
autosquad run --project my-app --rounds 5

# Disable reflection for faster development
autosquad run --project my-app --no-reflect

# Enable verbose logging for debugging
autosquad run --project my-app --verbose
```

## 🏗️ Architecture & Technical Features

### Agent Coordination
- **AutoGen Foundation**: Built on Microsoft's proven multi-agent framework
- **Round-Robin Collaboration**: Structured conversation flow ensures all agents contribute
- **Context-Aware Agents**: Each agent maintains project awareness and specialized knowledge
- **Tool Integration**: File operations, code execution, and workspace management

### Token Optimization Engine
- **Intelligent Context Compression**: Keeps recent messages while summarizing older content
- **Smart Message Prioritization**: Maintains conversation flow with minimal token usage
- **Real-Time Usage Tracking**: Monitor costs and usage patterns as development happens
- **Automatic Optimization**: No manual configuration required

### Live Progress System
- **Real-Time Agent Dashboard**: See which agents are active and what they're doing
- **Activity Stream**: Watch file creation, conversations, and progress live
- **Performance Metrics**: Track actions completed, files created, and productivity
- **Professional Terminal UI**: Rich formatting with colors, panels, and layouts

### Project Management
- **Workspace Isolation**: Each project gets its own dedicated workspace
- **Conversation Logging**: Complete transcripts of all agent interactions
- **File Versioning**: Automatic backups and change tracking
- **State Persistence**: Resume projects and maintain context across sessions

## 📊 What Gets Built

AutoSquad agents create **production-ready applications** with:

### Code Quality
- ✅ **Clean, readable code** with proper structure and comments
- ✅ **Error handling** and edge case management
- ✅ **Best practices** for the chosen technology stack
- ✅ **Documentation** and usage instructions

### Project Structure
- ✅ **Organized file hierarchy** with logical folder structures
- ✅ **Configuration files** (requirements.txt, package.json, etc.)
- ✅ **README files** with setup and usage instructions
- ✅ **Basic tests** for core functionality

### Deliverables
- ✅ **Working applications** that solve the specified problem
- ✅ **Installation instructions** and dependency management
- ✅ **Usage examples** and API documentation
- ✅ **Development logs** showing the complete thought process

## 🎯 Example Projects

### CLI Tools
```
"Build a Python CLI that converts between JSON, CSV, and YAML formats"
→ Complete CLI with argparse, error handling, and format validation
```

### Web Applications  
```
"Create a Flask web app for task management with user authentication"
→ Full Flask app with database, auth, REST API, and frontend
```

### Data Processing
```
"Build a data pipeline that processes CSV files and generates reports"
→ Python pipeline with pandas, validation, and HTML report generation
```

### Utilities
```
"Create a file organizer that sorts downloads by file type"
→ Cross-platform utility with configuration and scheduling
```

## 🔧 Configuration

### Environment Setup
```bash
# Required
export OPENAI_API_KEY="your-api-key"

# Optional
export AUTOSQUAD_CONFIG_DIR="~/.autosquad"  # Custom config location
export AUTOSQUAD_LOG_LEVEL="INFO"          # Logging level
```

### Custom Squad Profiles
Create `~/.autosquad/squad_profiles.yaml`:
```yaml
profiles:
  my-custom-team:
    agents:
      - type: pm
        config:
          focus: "user experience"
      - type: engineer  
        config:
          languages: ["python", "typescript"]
          frameworks: ["fastapi", "react"]
      - type: qa
        config:
          focus: ["performance", "security"]
    workflow:
      rounds: 4
      reflection_frequency: 2
```

## 🚀 Performance & Efficiency

### Speed Optimizations
- **Parallel Agent Operations**: Multiple agents can work simultaneously
- **Intelligent Context Management**: Faster API calls through optimized prompts
- **Async Architecture**: Non-blocking operations for better responsiveness
- **Smart Caching**: Reduce redundant API calls and computations

### Cost Management
- **Token Usage Monitoring**: Real-time tracking prevents budget overruns
- **Context Optimization**: 69% average reduction in token usage
- **Model Selection**: Choose the right model for your budget and quality needs
- **Usage Analytics**: Detailed breakdowns help optimize future projects

## 🔮 Roadmap

### Immediate (v0.3)
- [ ] **Code Execution Environment**: Sandboxed testing and validation
- [ ] **Git Integration**: Automatic commits and version control
- [ ] **More Agent Types**: Database, DevOps, and Security specialists
- [ ] **Plugin System**: Custom tools and integrations

### Short Term (v0.4)
- [ ] **Web Interface**: Browser-based project management and monitoring
- [ ] **Team Templates**: Pre-configured squads for common project types
- [ ] **Advanced Analytics**: Performance insights and optimization suggestions
- [ ] **Multi-Language Support**: Beyond Python to Node.js, Go, Rust

### Long Term (v1.0)
- [ ] **Distributed Execution**: Scale to larger, more complex projects
- [ ] **Learning System**: Agents improve based on project feedback
- [ ] **Enterprise Features**: Team management, audit logs, compliance
- [ ] **Marketplace**: Share and discover community squad profiles

## 📚 Documentation

- **[Token Optimization Guide](TOKEN_OPTIMIZATION_GUIDE.md)** - Detailed guide to cost savings
- **[Architecture Overview](ARCHITECTURE.md)** - Technical implementation details
- **[Agent Design](AGENT_DESIGN.md)** - How agents work and interact
- **[Project Status](PROJECT_STATUS.md)** - Current development status
- **[Contributing](CONTRIBUTING.md)** - How to contribute to AutoSquad

## 🤝 Contributing

AutoSquad is open source and welcomes contributions! Whether you're:
- 🐛 **Reporting bugs** or suggesting features
- 📝 **Improving documentation** or examples
- 🔧 **Adding new agent types** or tools
- 🎨 **Enhancing the UI** or user experience

Check out our [Contributing Guide](CONTRIBUTING.md) to get started.

## 📄 License

AutoSquad is released under the MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Microsoft AutoGen** - The powerful multi-agent framework that makes AutoSquad possible
- **OpenAI** - GPT models that power our intelligent agents
- **Rich Library** - Beautiful terminal UI components
- **The Open Source Community** - For tools, libraries, and inspiration

---

**Ready to build something amazing?** 🚀

```bash
autosquad run --project your-next-big-idea --rounds 3
```

*Watch AI agents turn your ideas into reality, efficiently and transparently.*
