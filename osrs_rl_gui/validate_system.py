#!/usr/bin/env python3
"""Simple validation script to test the improved OSRS RL system."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_task_system():
    """Test the task creation and management system."""
    print("Testing task system...")
    
    try:
        from tasks.task_system import TaskManager, TaskCategory
        
        manager = TaskManager()
        
        # Test various task types
        test_descriptions = [
            "Kill 10 goblins in Lumbridge",
            "Mine 50 iron ore and smelt into bars", 
            "Train woodcutting to level 60",
            "Complete the Cook's Assistant quest",
            "Fight other players in the wilderness",
            "Explore the caves under Lumbridge"
        ]
        
        for desc in test_descriptions:
            task = manager.create_task_from_description(desc)
            print(f"✓ Created task: {task.name} ({task.category.value})")
            
        print(f"✓ Task system working - created {len(manager.tasks)} tasks")
        return True
        
    except Exception as e:
        print(f"✗ Task system failed: {e}")
        return False

def test_environment_factory():
    """Test the environment factory system."""
    print("\nTesting environment factory...")
    
    try:
        from tasks.task_system import TaskManager
        from core.environment_factory import EnvironmentFactory
        
        manager = TaskManager()
        factory = EnvironmentFactory()
        
        # Test creating environments for different task types
        task = manager.create_task_from_description("Kill 5 dragons")
        env_config = factory.create_environment_for_task(task)
        
        print(f"✓ Created environment: {env_config['name']}")
        print(f"✓ Task info included: {'task_info' in env_config}")
        print(f"✓ Observations defined: {len(env_config.get('observations', []))}")
        print(f"✓ Actions defined: {len(env_config.get('actions', []))}")
        
        return True
        
    except Exception as e:
        print(f"✗ Environment factory failed: {e}")
        return False

def test_config_manager():
    """Test the configuration management system."""
    print("\nTesting configuration manager...")
    
    try:
        from core.config_manager import ConfigManager, OSRSRLConfig
        
        manager = ConfigManager()
        
        # Create a test configuration
        config = OSRSRLConfig()
        config.training.experiment_name = "test_experiment"
        config.agent.model_name = "TestAgent"
        
        # Save and load
        manager.create_config("test_config", config)
        loaded_config = manager.get_config("test_config")
        
        assert loaded_config is not None
        assert loaded_config.training.experiment_name == "test_experiment"
        
        print("✓ Configuration manager working")
        return True
        
    except Exception as e:
        print(f"✗ Configuration manager failed: {e}")
        return False

def test_secure_storage():
    """Test the secure credential storage."""
    print("\nTesting secure storage...")
    
    try:
        from core.secure_storage import SecureCredentialStore
        
        store = SecureCredentialStore()
        
        # Test storing and retrieving credentials
        test_user = "test_user"
        test_pass = "test_password_123"
        
        store.store_credentials(test_user, test_pass)
        retrieved = store.retrieve_credentials()
        
        assert retrieved is not None
        assert retrieved[0] == test_user
        assert retrieved[1] == test_pass
        
        # Clean up
        store.clear_credentials()
        
        print("✓ Secure storage working")
        return True
        
    except Exception as e:
        print(f"✗ Secure storage failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=== OSRS RL System Validation ===")
    
    tests = [
        test_task_system,
        test_environment_factory, 
        test_config_manager,
        test_secure_storage
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("✓ All systems working correctly!")
        return 0
    else:
        print("✗ Some systems have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())