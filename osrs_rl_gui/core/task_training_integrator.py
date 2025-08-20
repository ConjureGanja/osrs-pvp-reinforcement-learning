"""Integration layer for connecting task system with training pipeline."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile

from .config_manager import ConfigManager, OSRSRLConfig

# Import task system components - adjust path as needed
try:
    from ..tasks.task_system import Task, TaskCategory
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tasks.task_system import Task, TaskCategory

logger = logging.getLogger(__name__)


class TaskTrainingIntegrator:
    """Integrates the task system with the ML training pipeline."""
    
    def __init__(self, config_manager: ConfigManager, contracts_dir: Optional[Path] = None):
        self.config_manager = config_manager
        if contracts_dir is None:
            # Default to the main contracts directory
            self.contracts_dir = Path(__file__).parent.parent.parent.parent / "contracts" / "environments"
        else:
            self.contracts_dir = contracts_dir
    
    def prepare_training_for_task(self, task: Task, base_config_name: str = "default") -> Dict[str, Any]:
        """Prepare training configuration and environment for a specific task."""
        
        # Create environment contract for the task
        env_contract = self._create_environment_contract(task)
        
        # Save environment contract to temporary location
        contract_path = self._save_temp_contract(env_contract)
        
        # Create training configuration
        training_config = self._create_training_config(task, base_config_name)
        
        return {
            "environment_contract_path": str(contract_path),
            "training_config": training_config,
            "task_name": task.name,
            "task_category": task.category.value
        }
    
    def _create_environment_contract(self, task: Task) -> Dict[str, Any]:
        """Create an environment contract tailored for the specific task."""
        
        # Base contract structure
        contract = {
            "name": f"{task.name.replace(' ', '')}Env",
            "description": f"Environment for task: {task.description}",
            "category": task.category.value,
            "difficulty": task.difficulty.value,
            "observations": [],
            "actions": [],
            "reward_structure": {},
            "task_metadata": {
                "objectives": [
                    {
                        "description": obj.description,
                        "target": obj.target,
                        "quantity": obj.quantity
                    }
                    for obj in task.objectives
                ],
                "requirements": {
                    "skill_levels": task.requirements.skill_levels,
                    "items": task.requirements.items,
                    "quests_completed": task.requirements.quests_completed
                }
            }
        }
        
        # Add category-specific components
        if task.category == TaskCategory.COMBAT or task.category == TaskCategory.PVP:
            contract.update(self._get_combat_contract_components())
        elif task.category == TaskCategory.SKILLING:
            contract.update(self._get_skilling_contract_components())
        elif task.category == TaskCategory.EXPLORATION:
            contract.update(self._get_exploration_contract_components())
        else:
            # Generic contract
            contract.update(self._get_generic_contract_components())
        
        return contract
    
    def _get_combat_contract_components(self) -> Dict[str, Any]:
        """Get contract components for combat tasks."""
        return {
            "observations": [
                {"name": "hitpoints", "type": "discrete", "min": 0, "max": 99},
                {"name": "prayer_points", "type": "discrete", "min": 0, "max": 99},
                {"name": "enemy_hitpoints", "type": "discrete", "min": 0, "max": 99},
                {"name": "combat_stance", "type": "discrete", "min": 0, "max": 4},
                {"name": "weapon_equipped", "type": "discrete", "min": 0, "max": 1000}
            ],
            "actions": [
                {
                    "name": "combat_actions",
                    "description": "Combat-related actions",
                    "actions": [
                        {"name": "attack", "description": "Attack target"},
                        {"name": "cast_spell", "description": "Cast magic spell"},
                        {"name": "use_special", "description": "Use special attack"},
                        {"name": "change_stance", "description": "Change combat stance"},
                        {"name": "eat_food", "description": "Consume food"},
                        {"name": "drink_potion", "description": "Drink potion"}
                    ]
                }
            ],
            "reward_structure": {
                "damage_dealt": 1.0,
                "damage_taken": -0.5,
                "kill_enemy": 100.0,
                "death": -100.0
            }
        }
    
    def _get_skilling_contract_components(self) -> Dict[str, Any]:
        """Get contract components for skilling tasks."""
        return {
            "observations": [
                {"name": "skill_xp", "type": "continuous", "min": 0, "max": 200000000},
                {"name": "skill_level", "type": "discrete", "min": 1, "max": 99},
                {"name": "inventory_space", "type": "discrete", "min": 0, "max": 28},
                {"name": "resource_available", "type": "discrete", "min": 0, "max": 1},
                {"name": "fatigue", "type": "continuous", "min": 0, "max": 100}
            ],
            "actions": [
                {
                    "name": "skilling_actions",
                    "description": "Skilling-related actions",
                    "actions": [
                        {"name": "gather_resource", "description": "Gather natural resource"},
                        {"name": "process_material", "description": "Process gathered materials"},
                        {"name": "bank_items", "description": "Store items in bank"},
                        {"name": "withdraw_items", "description": "Withdraw items from bank"},
                        {"name": "drop_item", "description": "Drop unwanted item"},
                        {"name": "use_tool", "description": "Use skilling tool"}
                    ]
                }
            ],
            "reward_structure": {
                "xp_gained": 1.0,
                "level_up": 50.0,
                "inventory_full": -5.0,
                "objective_progress": 10.0
            }
        }
    
    def _get_exploration_contract_components(self) -> Dict[str, Any]:
        """Get contract components for exploration tasks."""
        return {
            "observations": [
                {"name": "position_x", "type": "discrete", "min": 0, "max": 4096},
                {"name": "position_y", "type": "discrete", "min": 0, "max": 4096},
                {"name": "region_id", "type": "discrete", "min": 0, "max": 65535},
                {"name": "destination_distance", "type": "continuous", "min": 0, "max": 100},
                {"name": "path_blocked", "type": "discrete", "min": 0, "max": 1}
            ],
            "actions": [
                {
                    "name": "movement_actions",
                    "description": "Movement and exploration actions",
                    "actions": [
                        {"name": "move_north", "description": "Move north"},
                        {"name": "move_south", "description": "Move south"},
                        {"name": "move_east", "description": "Move east"},
                        {"name": "move_west", "description": "Move west"},
                        {"name": "run_toggle", "description": "Toggle running"},
                        {"name": "use_teleport", "description": "Use teleportation method"}
                    ]
                }
            ],
            "reward_structure": {
                "distance_reduced": 1.0,
                "reached_destination": 100.0,
                "got_lost": -10.0,
                "efficient_path": 5.0
            }
        }
    
    def _get_generic_contract_components(self) -> Dict[str, Any]:
        """Get generic contract components for unknown task types."""
        return {
            "observations": [
                {"name": "game_state", "type": "discrete", "min": 0, "max": 1000},
                {"name": "progress", "type": "continuous", "min": 0, "max": 1}
            ],
            "actions": [
                {
                    "name": "basic_actions",
                    "description": "Basic game actions",
                    "actions": [
                        {"name": "wait", "description": "Do nothing"},
                        {"name": "interact", "description": "Interact with object"},
                        {"name": "move", "description": "Move character"},
                        {"name": "use_item", "description": "Use an item"}
                    ]
                }
            ],
            "reward_structure": {
                "progress_made": 1.0,
                "objective_completed": 50.0,
                "time_penalty": -0.1
            }
        }
    
    def _save_temp_contract(self, contract: Dict[str, Any]) -> Path:
        """Save environment contract to a temporary file."""
        # Create temporary file in contracts directory
        contracts_dir = self.contracts_dir
        contracts_dir.mkdir(parents=True, exist_ok=True)
        
        temp_file = contracts_dir / f"temp_{contract['name']}.json"
        
        with open(temp_file, 'w') as f:
            json.dump(contract, f, indent=2)
        
        logger.info(f"Saved temporary environment contract: {temp_file}")
        return temp_file
    
    def _create_training_config(self, task: Task, base_config_name: str) -> Dict[str, Any]:
        """Create training configuration for the task."""
        
        # Load or create base configuration
        try:
            base_config = self.config_manager.load_config(base_config_name)
        except:
            logger.warning(f"Failed to load base config {base_config_name}, using default")
            base_config = OSRSRLConfig()
        
        # Customize for this task
        task_config_updates = {
            "training": {
                "experiment_name": f"{task.name.replace(' ', '_')}_training",
            },
            "environment": {
                "environment_name": f"{task.name.replace(' ', '')}Env",
                "max_episode_steps": self._estimate_episode_steps(task),
            },
            "agent": {
                "model_name": f"{task.category.value.title()}Agent"
            }
        }
        
        # Apply task-specific adjustments
        if task.category == TaskCategory.SKILLING:
            task_config_updates["training"]["total_timesteps"] = 2000000  # Longer for skilling
            task_config_updates["environment"]["step_penalty"] = -0.05  # Less penalty for patience
        elif task.category == TaskCategory.EXPLORATION:
            task_config_updates["agent"]["exploration_noise"] = 0.2  # More exploration
            
        updated_config = self.config_manager.update_config(base_config_name, task_config_updates)
        
        return {
            "config_name": f"{base_config_name}_{task.name.replace(' ', '_')}",
            "config_data": updated_config
        }
    
    def _estimate_episode_steps(self, task: Task) -> int:
        """Estimate the number of steps needed for a task."""
        base_steps = 1000
        
        # Adjust based on task complexity
        complexity_multiplier = len(task.objectives)
        
        # Adjust based on category
        category_multipliers = {
            TaskCategory.COMBAT: 1.0,
            TaskCategory.PVP: 1.2,
            TaskCategory.SKILLING: 2.0,  # Skilling tasks take longer
            TaskCategory.EXPLORATION: 1.5,
            TaskCategory.QUESTING: 3.0,  # Quests are complex
            TaskCategory.TRADING: 0.8
        }
        
        multiplier = category_multipliers.get(task.category, 1.0)
        
        return int(base_steps * complexity_multiplier * multiplier)