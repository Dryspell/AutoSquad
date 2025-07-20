# AutoSquad Installation Guide

AutoSquad can be installed in several ways depending on your preferences and use case.

## 🐍 **Option 1: Install from PyPI (Recommended)**

**For most users, this is the easiest option:**

```bash
# Install AutoSquad
pip install autosquad

# Verify installation
autosquad --version

# Set up your API key
autosquad init
```

**Requirements:**
- Python 3.8 or higher
- pip (Python package manager)

---

## 🔧 **Option 2: Install from Source (Developers)**

**For developers who want the latest features or to contribute:**

```bash
# Clone the repository
git clone https://github.com/yourusername/AutoSquad.git
cd AutoSquad

# Create virtual environment (recommended)
python -m venv autosquad-env
source autosquad-env/bin/activate  # On Windows: autosquad-env\Scripts\activate

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"

# Verify installation
autosquad --version
```

---

## 📦 **Option 3: Standalone Executable (Coming Soon)**

**For users who don't want to install Python:**

### Windows
```bash
# Download the latest release
curl -L -o autosquad.exe https://github.com/yourusername/AutoSquad/releases/latest/download/autosquad-windows.exe

# Run it directly
./autosquad.exe --version
```

### macOS
```bash
# Download the latest release
curl -L -o autosquad https://github.com/yourusername/AutoSquad/releases/latest/download/autosquad-macos

# Make it executable
chmod +x autosquad

# Run it
./autosquad --version
```

### Linux
```bash
# Download the latest release
curl -L -o autosquad https://github.com/yourusername/AutoSquad/releases/latest/download/autosquad-linux

# Make it executable
chmod +x autosquad

# Move to PATH (optional)
sudo mv autosquad /usr/local/bin/

# Run it
autosquad --version
```

---

## 🍺 **Option 4: Package Managers (Coming Soon)**

### Homebrew (macOS/Linux)
```bash
brew install autosquad
```

### Chocolatey (Windows)
```bash
choco install autosquad
```

### Snap (Linux)
```bash
sudo snap install autosquad
```

---

## 🐳 **Option 5: Docker Container**

**For containerized environments:**

```bash
# Pull the image
docker pull autosquad/autosquad:latest

# Run AutoSquad in a container
docker run -it --rm \
  -v $(pwd)/projects:/app/projects \
  -e OPENAI_API_KEY=your_api_key_here \
  autosquad/autosquad:latest autosquad --help

# Create an alias for easier use
echo 'alias autosquad="docker run -it --rm -v $(pwd)/projects:/app/projects -e OPENAI_API_KEY=$OPENAI_API_KEY autosquad/autosquad:latest autosquad"' >> ~/.bashrc
source ~/.bashrc
```

---

## ⚙️ **Post-Installation Setup**

After installing AutoSquad, you'll need to configure it:

### 1. **API Key Setup**
```bash
# Interactive setup wizard (recommended for first-time users)
autosquad init

# Or manually set environment variable
export OPENAI_API_KEY="your-api-key-here"

# Or use the configuration command
autosquad config setup
```

### 2. **Verify Everything Works**
```bash
# Check configuration
autosquad config validate

# Test API connection
autosquad config check-api

# View current settings
autosquad config show
```

### 3. **Create Your First Project**
```bash
# Create a new project
autosquad project create --name my-first-app --prompt "Create a simple calculator CLI"

# List all projects
autosquad project list

# Run your first squad
autosquad run --project projects/my-first-app --squad-profile mvp-team
```

---

## 🚀 **Installation for Different Use Cases**

### **For End Users (Just Want to Use It)**
→ **Use Option 1 (PyPI)** or **Option 3 (Standalone)**

### **For Developers (Want to Contribute)**
→ **Use Option 2 (Source)**

### **For CI/CD Pipelines**
→ **Use Option 5 (Docker)**

### **For Enterprise/Managed Environments**
→ **Use Option 4 (Package Managers)** when available

---

## 🔧 **Building Your Own Distribution**

### **Build Python Package**
```bash
# Install build dependencies
pip install build twine

# Build the package
python -m build

# Test locally
pip install dist/*.whl
```

### **Build Standalone Executable**
```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --name autosquad squad_runner/cli.py

# Find executable in dist/
```

### **Build Docker Image**
```bash
# Build the image
docker build -t autosquad:local .

# Test it
docker run --rm autosquad:local autosquad --version
```

---

## 📋 **System Requirements**

### **Minimum Requirements**
- **Python:** 3.8 or higher
- **Memory:** 2GB RAM
- **Storage:** 500MB free space
- **Network:** Internet connection for API calls

### **Recommended Requirements**
- **Python:** 3.10 or higher
- **Memory:** 4GB RAM
- **Storage:** 2GB free space
- **OS:** Linux, macOS, or Windows 10+

---

## 🆘 **Troubleshooting**

### **Common Issues**

#### **"Command not found: autosquad"**
```bash
# Check if it's installed
pip list | grep autosquad

# Check PATH
echo $PATH

# Reinstall if needed
pip uninstall autosquad
pip install autosquad
```

#### **"API key not found"**
```bash
# Set environment variable
export OPENAI_API_KEY="your-key-here"

# Or run setup
autosquad config setup
```

#### **"Permission denied"**
```bash
# On Unix systems, make sure the executable is in your PATH
which autosquad

# If installing globally, use sudo (not recommended)
sudo pip install autosquad

# Better: use user install
pip install --user autosquad
```

### **Getting Help**
```bash
# CLI help
autosquad --help
autosquad config --help
autosquad project --help

# Check version and dependencies
autosquad config show

# Test your setup
autosquad config validate
```

---

## 🔄 **Updating AutoSquad**

### **PyPI Installation**
```bash
pip install --upgrade autosquad
```

### **Source Installation**
```bash
cd AutoSquad
git pull origin main
pip install -e .
```

### **Docker**
```bash
docker pull autosquad/autosquad:latest
```

---

Need help? [Open an issue](https://github.com/yourusername/AutoSquad/issues) or check our [documentation](https://github.com/yourusername/AutoSquad#readme). 