"""
Setup configuration for AutoSquad
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else "AutoSquad - Autonomous Multi-Agent Development Framework"

setup(
    name="autosquad",
    version="0.1.0",
    author="AutoSquad Team",
    author_email="autosquad@example.com",  # Update with real email
    description="Autonomous Multi-Agent Development Framework built on AutoGen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/AutoSquad",  # Update with real repo
    project_urls={
        "Bug Reports": "https://github.com/yourusername/AutoSquad/issues",
        "Source": "https://github.com/yourusername/AutoSquad",
        "Documentation": "https://github.com/yourusername/AutoSquad#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Environment :: Console",
    ],
    keywords="ai, agents, autogen, development, automation, cli",
    python_requires=">=3.8",
    install_requires=[
        # Core AutoGen dependencies
        "autogen-agentchat>=0.4.0",
        "autogen-core>=0.4.0", 
        "autogen-ext[openai]>=0.4.0",
        
        # CLI and UI dependencies
        "click>=8.1.0",
        "rich>=13.0.0",
        "colorama>=0.4.6",
        
        # Configuration and data handling
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        
        # Core Python utilities
        "typing-extensions>=4.8.0",
        "pathlib; python_version<'3.4'",
        
        # Token counting and optimization
        "tiktoken>=0.5.0",
        
        # OpenAI API client
        "openai>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "structlog>=23.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
        "build": [
            "build>=0.10.0",
            "twine>=4.0.0",
            "wheel>=0.40.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "autosquad=squad_runner.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "squad_runner": [
            "configs/*.yaml",
            "configs/*.yml",
        ],
    },
    zip_safe=False,  # Needed for configs to be accessible
) 