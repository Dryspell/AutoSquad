#!/usr/bin/env python3
"""
Build script for AutoSquad package distribution.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return None


def main():
    """Main build process."""
    print("🚀 AutoSquad Package Builder")
    print("=" * 40)
    
    # Ensure we're in the project root
    if not Path("setup.py").exists():
        print("❌ Error: Run this script from the project root directory")
        sys.exit(1)
    
    # Clean previous builds
    print("\n📂 Cleaning previous builds...")
    for dir_name in ["build", "dist", "*.egg-info"]:
        run_command(f"rm -rf {dir_name}", f"Removing {dir_name}")
    
    # Install build dependencies
    print("\n📦 Installing build dependencies...")
    if not run_command("pip install build twine wheel", "Installing build tools"):
        sys.exit(1)
    
    # Build the package
    print("\n🔨 Building package...")
    if not run_command("python -m build", "Building wheel and source distribution"):
        sys.exit(1)
    
    # List built files
    dist_dir = Path("dist")
    if dist_dir.exists():
        print(f"\n📋 Built packages:")
        for file in dist_dir.glob("*"):
            print(f"   📄 {file.name}")
    
    # Verify the package
    print("\n🔍 Verifying package...")
    wheel_files = list(dist_dir.glob("*.whl"))
    if wheel_files:
        wheel_file = wheel_files[0]
        if run_command(f"twine check {wheel_file}", "Checking package validity"):
            print("✅ Package verification passed!")
        else:
            print("❌ Package verification failed!")
            sys.exit(1)
    
    print("\n🎉 Build completed successfully!")
    print("\nNext steps:")
    print("1. Test installation: pip install dist/*.whl")
    print("2. Upload to TestPyPI: twine upload --repository testpypi dist/*")
    print("3. Upload to PyPI: twine upload dist/*")


if __name__ == "__main__":
    main() 