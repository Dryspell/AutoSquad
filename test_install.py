#!/usr/bin/env python3
"""
Simple test script to verify AutoSquad installation
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all main modules can be imported."""
    print("Testing imports...")
    
    try:
        import squad_runner
        print("✅ squad_runner imported successfully")
        
        from squad_runner.cli import main
        print("✅ CLI module imported successfully")
        
        from squad_runner.config import load_config, load_squad_profile
        print("✅ Config module imported successfully")
        
        from squad_runner.project_manager import ProjectManager
        print("✅ ProjectManager imported successfully")
        
        from squad_runner.orchestrator import SquadOrchestrator
        print("✅ SquadOrchestrator imported successfully")
        
        from squad_runner.agents import create_agent
        print("✅ Agents module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from squad_runner.config import load_config, load_squad_profile
        
        # Test loading default config
        config = load_config()
        print("✅ Default config loaded successfully")
        
        # Test loading squad profiles
        profile = load_squad_profile("mvp-team")
        print("✅ MVP team profile loaded successfully")
        
        profile = load_squad_profile("full-stack")
        print("✅ Full-stack team profile loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def test_project_structure():
    """Test project structure creation."""
    print("\nTesting project structure...")
    
    try:
        from squad_runner.project_manager import ProjectManager
        
        # Test project path validation
        test_project = Path("projects/example-cli-tool")
        if test_project.exists():
            print("✅ Example project exists")
            
            # Test ProjectManager initialization
            pm = ProjectManager(test_project)
            print("✅ ProjectManager created successfully")
            
            return True
        else:
            print("⚠️  Example project not found, but this is not critical")
            return True
            
    except Exception as e:
        print(f"❌ Project structure test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧠 AutoSquad Installation Test\n")
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_config),
        ("Project Structure Test", test_project_structure),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AutoSquad is ready to use.")
        print("\nNext steps:")
        print("1. Set your OpenAI API key: export OPENAI_API_KEY=sk-...")
        print("2. Create a project: autosquad create --name my-project")
        print("3. Run a squad: autosquad run --project projects/my-project")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 