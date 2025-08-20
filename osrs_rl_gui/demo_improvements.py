"""Example demonstrating the improved OSRS RL Agent system."""

def demonstrate_task_creation():
    """Show how the new system handles diverse tasks."""
    from tasks.task_system import TaskManager
    from core.environment_factory import EnvironmentFactory
    from core.config_manager import ConfigManager
    from core.task_training_integrator import TaskTrainingIntegrator
    
    print("=== OSRS RL Agent - Task Creation Demo ===\n")
    
    # Initialize components
    task_manager = TaskManager()
    env_factory = EnvironmentFactory()
    config_manager = ConfigManager()
    integrator = TaskTrainingIntegrator(config_manager)
    
    # Examples of diverse tasks the system can now handle
    example_tasks = [
        "Kill 10 goblins in Lumbridge for combat training",
        "Mine 50 iron ore and smelt them into iron bars",
        "Train woodcutting to level 60 by cutting oak trees",
        "Complete the Cook's Assistant quest by gathering ingredients",
        "Explore the Lumbridge castle and map all rooms",
        "Trade with other players to buy 100 cowhides",
        "Fight other players in the wilderness for PvP experience"
    ]
    
    print("Creating tasks from natural language descriptions:\n")
    
    created_tasks = []
    for description in example_tasks:
        print(f"Input: '{description}'")
        
        # Create task from natural language
        task = task_manager.create_task_from_description(description)
        created_tasks.append(task)
        
        print(f"  → Task: {task.name}")
        print(f"  → Category: {task.category.value}")
        print(f"  → Difficulty: {task.difficulty.value}")
        print(f"  → Objectives: {len(task.objectives)}")
        
        # Create environment for this task
        env_config = env_factory.create_environment_for_task(task)
        print(f"  → Environment: {env_config['name']}")
        
        # Prepare training configuration
        training_setup = integrator.prepare_training_for_task(task)
        print(f"  → Training config: {training_setup['training_config']['config_name']}")
        
        print()
    
    print(f"Successfully created {len(created_tasks)} diverse tasks!")
    print("\nTask Categories Created:")
    categories = {}
    for task in created_tasks:
        categories[task.category.value] = categories.get(task.category.value, 0) + 1
    
    for category, count in categories.items():
        print(f"  - {category.title()}: {count} task(s)")
    
    return created_tasks


def demonstrate_flexibility():
    """Show how the system is more flexible than the previous PvP-only approach."""
    print("\n=== Flexibility Improvements ===\n")
    
    improvements = [
        {
            "area": "Task Scope",
            "before": "Limited to PvP combat scenarios only",
            "after": "Supports Combat, Skilling, Questing, Trading, Exploration, and PvP"
        },
        {
            "area": "Natural Language",
            "before": "No natural language processing - manual environment setup",
            "after": "Parses plain English task descriptions automatically"
        },
        {
            "area": "Environment Creation", 
            "before": "Hard-coded JSON contracts for fixed scenarios",
            "after": "Dynamic environment generation based on task requirements"
        },
        {
            "area": "Security",
            "before": "Plain text credential storage (security vulnerability)",
            "after": "Encrypted credential storage with proper key management"
        },
        {
            "area": "Code Architecture",
            "before": "Monolithic 1000+ line GUI class, complex state machines",
            "after": "Modular components, flexible task-based architecture"
        },
        {
            "area": "Configuration",
            "before": "Manual YAML editing for each scenario",
            "after": "Automatic configuration generation based on task type"
        }
    ]
    
    for improvement in improvements:
        print(f"**{improvement['area']}**")
        print(f"  Before: {improvement['before']}")
        print(f"  After:  {improvement['after']}")
        print()


if __name__ == "__main__":
    try:
        demonstrate_task_creation()
        demonstrate_flexibility()
        print("✓ Demo completed successfully!")
    except Exception as e:
        print(f"✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()