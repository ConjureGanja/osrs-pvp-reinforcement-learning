"""Environment factory system for creating dynamic OSRS RL environments."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
import json
import logging
from pathlib import Path

# Import task system components - adjust path as needed
try:
    from ..tasks.task_system import Task, TaskCategory, TaskObjective
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tasks.task_system import Task, TaskCategory, TaskObjective

logger = logging.getLogger(__name__)


class EnvironmentFactory:
    """Factory for creating dynamic environments based on tasks."""
    
    def __init__(self, contracts_dir: Optional[Path] = None):
        """Initialize the environment factory.
        
        Args:
            contracts_dir: Directory containing environment contracts (defaults to ../contracts/environments)
        """
        if contracts_dir is None:
            # Default to the contracts directory in the repo
            self.contracts_dir = Path(__file__).parent.parent.parent.parent / "contracts" / "environments"
        else:
            self.contracts_dir = contracts_dir
        
        self._base_contracts = {}
        self._load_base_contracts()
    
    def _load_base_contracts(self):
        """Load base environment contracts from disk."""
        if not self.contracts_dir.exists():
            logger.warning(f"Contracts directory not found: {self.contracts_dir}")
            return
        
        for contract_file in self.contracts_dir.glob("*.json"):
            try:
                with open(contract_file, 'r') as f:
                    contract_data = json.load(f)
                    self._base_contracts[contract_file.stem] = contract_data
                    logger.info(f"Loaded contract: {contract_file.stem}")
            except Exception as e:
                logger.error(f"Failed to load contract {contract_file}: {e}")
    
    def create_environment_for_task(self, task: Task) -> Dict[str, Any]:
        """Create an environment configuration for a specific task."""
        # Select base contract based on task category
        base_contract_name = self._select_base_contract(task.category)
        
        if base_contract_name not in self._base_contracts:
            logger.warning(f"No suitable base contract found for category {task.category}")
            # Fall back to a generic environment
            return self._create_generic_environment(task)
        
        base_contract = self._base_contracts[base_contract_name].copy()
        
        # Customize the contract for this specific task
        customized_contract = self._customize_contract_for_task(base_contract, task)
        
        logger.info(f"Created environment contract for task: {task.name}")
        return customized_contract
    
    def _select_base_contract(self, category: TaskCategory) -> str:
        """Select the most appropriate base contract for a task category."""
        category_mapping = {
            TaskCategory.COMBAT: "NhEnv",  # Use NH environment for combat
            TaskCategory.PVP: "NhEnv",
            TaskCategory.SKILLING: "SkillingEnv",  # Would need to be created
            TaskCategory.TRADING: "TradingEnv",   # Would need to be created
            TaskCategory.QUESTING: "QuestEnv",    # Would need to be created
            TaskCategory.EXPLORATION: "ExplorationEnv",  # Would need to be created
        }
        
        return category_mapping.get(category, "NhEnv")  # Default to NH for now
    
    def _customize_contract_for_task(self, base_contract: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """Customize a base contract for a specific task."""
        contract = base_contract.copy()
        
        # Update contract metadata
        contract["name"] = f"{task.name}Env"
        contract["description"] = f"Environment for task: {task.description}"
        
        # Add task-specific observations if needed
        if "observations" in contract:
            task_observations = self._generate_task_observations(task)
            contract["observations"].extend(task_observations)
        
        # Add task-specific actions if needed
        if "actions" in contract:
            task_actions = self._generate_task_actions(task)
            for action_group in task_actions:
                contract["actions"].append(action_group)
        
        # Add task metadata
        contract["task_info"] = {
            "name": task.name,
            "category": task.category.value,
            "difficulty": task.difficulty.value,
            "objectives": [
                {
                    "description": obj.description,
                    "target": obj.target,
                    "quantity": obj.quantity,
                    "completed": obj.completed
                }
                for obj in task.objectives
            ]
        }
        
        return contract
    
    def _generate_task_observations(self, task: Task) -> List[Dict[str, Any]]:
        """Generate task-specific observations."""
        observations = []
        
        # Add objective progress observations
        for i, objective in enumerate(task.objectives):
            observations.append({
                "name": f"objective_{i}_progress",
                "description": f"Progress towards: {objective.description}",
                "type": "discrete",
                "min": 0,
                "max": objective.quantity
            })
        
        # Add category-specific observations
        if task.category == TaskCategory.SKILLING:
            observations.extend([
                {
                    "name": "xp_gained",
                    "description": "Experience gained this episode",
                    "type": "continuous",
                    "min": 0,
                    "max": 10000
                },
                {
                    "name": "skill_level_progress",
                    "description": "Progress towards next skill level",
                    "type": "continuous", 
                    "min": 0,
                    "max": 1
                }
            ])
        
        return observations
    
    def _generate_task_actions(self, task: Task) -> List[Dict[str, Any]]:
        """Generate task-specific actions."""
        actions = []
        
        # Add category-specific actions
        if task.category == TaskCategory.SKILLING:
            actions.append({
                "name": "skilling_actions",
                "description": "Actions for skilling tasks",
                "actions": [
                    {"name": "mine", "description": "Mine a resource"},
                    {"name": "cut_tree", "description": "Cut down a tree"},
                    {"name": "fish", "description": "Catch fish"},
                    {"name": "cook", "description": "Cook food"},
                    {"name": "craft_item", "description": "Craft an item"}
                ]
            })
        elif task.category == TaskCategory.EXPLORATION:
            actions.append({
                "name": "movement_actions",
                "description": "Actions for exploration tasks",
                "actions": [
                    {"name": "move_north", "description": "Move north"},
                    {"name": "move_south", "description": "Move south"},
                    {"name": "move_east", "description": "Move east"},
                    {"name": "move_west", "description": "Move west"},
                    {"name": "interact_object", "description": "Interact with object"},
                    {"name": "use_teleport", "description": "Use teleportation"}
                ]
            })
        
        return actions
    
    def _create_generic_environment(self, task: Task) -> Dict[str, Any]:
        """Create a generic environment contract when no specific one is available."""
        return {
            "name": f"{task.name}Env",
            "description": f"Generic environment for task: {task.description}",
            "task_info": {
                "name": task.name,
                "category": task.category.value,
                "difficulty": task.difficulty.value,
                "objectives": [
                    {
                        "description": obj.description,
                        "target": obj.target,
                        "quantity": obj.quantity,
                        "completed": obj.completed
                    }
                    for obj in task.objectives
                ]
            },
            "observations": [
                {
                    "name": "player_position",
                    "description": "Player's position in the game world",
                    "type": "discrete",
                    "min": 0,
                    "max": 4096
                },
                {
                    "name": "task_progress",
                    "description": "Overall task completion progress",
                    "type": "continuous",
                    "min": 0,
                    "max": 1
                }
            ],
            "actions": [
                {
                    "name": "basic_actions",
                    "description": "Basic game actions",
                    "actions": [
                        {"name": "wait", "description": "Do nothing"},
                        {"name": "move", "description": "Move player"},
                        {"name": "interact", "description": "Interact with object"},
                        {"name": "use_item", "description": "Use an item"}
                    ]
                }
            ]
        }
    
    def save_environment_contract(self, contract: Dict[str, Any], filename: str) -> None:
        """Save an environment contract to disk."""
        output_path = self.contracts_dir / f"{filename}.json"
        try:
            with open(output_path, 'w') as f:
                json.dump(contract, f, indent=2)
            logger.info(f"Saved environment contract: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save contract {output_path}: {e}")
    
    def list_available_contracts(self) -> List[str]:
        """List all available base contracts."""
        return list(self._base_contracts.keys())
    
    def get_contract(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific contract by name."""
        return self._base_contracts.get(name)