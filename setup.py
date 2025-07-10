"""
Setup configuration for AutoSquad
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="autosquad",
    version="0.1.0",
    author="AutoSquad Team",
    author_email="",
    description="Autonomous Multi-Agent Development Framework built on AutoGen",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/AutoSquad",
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
    ],
    python_requires=">=3.8",
    install_requires=[
        "autogen-agentchat>=0.4.0",
        "autogen-core>=0.4.0", 
        "autogen-ext>=0.4.0",
        "click>=8.1.0",
        "pyyaml>=6.0",
        "rich>=13.0.0",
        "colorama>=0.4.6",
        "typing-extensions>=4.8.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "structlog>=23.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "autosquad=squad_runner.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "squad_runner": ["configs/*.yaml"],
    },
) 