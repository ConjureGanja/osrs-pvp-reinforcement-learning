"""Configuration management system for OSRS RL Agent."""
import json
import yaml
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigFormat(Enum):
    """Supported configuration file formats."""
    JSON = "json"
    YAML = "yaml"


@dataclass
class AgentConfig:
    """Configuration for the RL agent."""
    model_name: str = "GeneralizedAgent"
    stack_frames: int = 4
    deterministic: bool = False
    learning_rate: float = 3e-4
    batch_size: int = 32
    buffer_size: int = 100000
    exploration_noise: float = 0.1


@dataclass
class EnvironmentConfig:
    """Configuration for the environment."""
    environment_name: str = "GeneralEnv"
    max_episode_steps: int = 1000
    reward_scaling: float = 1.0
    timeout_penalty: float = -10.0
    success_reward: float = 100.0
    step_penalty: float = -0.1


@dataclass
class TrainingConfig:
    """Configuration for training sessions."""
    experiment_name: str = "experiment"
    total_timesteps: int = 1000000
    eval_frequency: int = 10000
    checkpoint_frequency: int = 50000
    num_eval_episodes: int = 10
    parallel_envs: int = 4
    use_tensorboard: bool = True
    save_best_model: bool = True


@dataclass
class ServerConfig:
    """Configuration for server connections."""
    simulation_host: str = "localhost"
    simulation_port: int = 43594
    api_host: str = "127.0.0.1"
    api_port: int = 9999
    connection_timeout: int = 30


@dataclass
class OSRSRLConfig:
    """Main configuration container for the OSRS RL system."""
    agent: AgentConfig
    environment: EnvironmentConfig
    training: TrainingConfig
    server: ServerConfig
    
    def __init__(
        self,
        agent: Optional[AgentConfig] = None,
        environment: Optional[EnvironmentConfig] = None,
        training: Optional[TrainingConfig] = None,
        server: Optional[ServerConfig] = None
    ):
        self.agent = agent or AgentConfig()
        self.environment = environment or EnvironmentConfig()
        self.training = training or TrainingConfig()
        self.server = server or ServerConfig()


class ConfigManager:
    """Manages configuration files and provides runtime configuration updates."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files (defaults to ~/.osrs_rl/config)
        """
        if config_dir is None:
            self.config_dir = Path.home() / ".osrs_rl" / "config"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._configs: Dict[str, OSRSRLConfig] = {}
    
    def create_config(self, name: str, config: Optional[OSRSRLConfig] = None) -> OSRSRLConfig:
        """Create a new configuration with the given name."""
        if config is None:
            config = OSRSRLConfig()
        
        self._configs[name] = config
        logger.info(f"Created configuration: {name}")
        return config
    
    def load_config(self, name: str, file_format: ConfigFormat = ConfigFormat.YAML) -> OSRSRLConfig:
        """Load configuration from file."""
        file_path = self.config_dir / f"{name}.{file_format.value}"
        
        if not file_path.exists():
            logger.warning(f"Configuration file not found: {file_path}")
            config = OSRSRLConfig()
            self.save_config(name, config, file_format)
            return config
        
        try:
            with open(file_path, 'r') as f:
                if file_format == ConfigFormat.JSON:
                    data = json.load(f)
                else:  # YAML
                    data = yaml.safe_load(f)
            
            config = self._dict_to_config(data)
            self._configs[name] = config
            logger.info(f"Loaded configuration: {name}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration {name}: {e}")
            raise
    
    def save_config(
        self, 
        name: str, 
        config: Optional[OSRSRLConfig] = None, 
        file_format: ConfigFormat = ConfigFormat.YAML
    ) -> None:
        """Save configuration to file."""
        if config is None:
            if name not in self._configs:
                raise ValueError(f"No configuration found with name: {name}")
            config = self._configs[name]
        
        file_path = self.config_dir / f"{name}.{file_format.value}"
        
        try:
            data = self._config_to_dict(config)
            
            with open(file_path, 'w') as f:
                if file_format == ConfigFormat.JSON:
                    json.dump(data, f, indent=2)
                else:  # YAML
                    yaml.dump(data, f, default_flow_style=False, indent=2)
            
            self._configs[name] = config
            logger.info(f"Saved configuration: {name}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration {name}: {e}")
            raise
    
    def get_config(self, name: str) -> Optional[OSRSRLConfig]:
        """Get configuration by name."""
        return self._configs.get(name)
    
    def list_configs(self) -> List[str]:
        """List all available configuration names."""
        configs_from_memory = list(self._configs.keys())
        configs_from_files = []
        
        # Also check for saved configurations
        for file_format in ConfigFormat:
            pattern = f"*.{file_format.value}"
            for file_path in self.config_dir.glob(pattern):
                config_name = file_path.stem
                if config_name not in configs_from_memory:
                    configs_from_files.append(config_name)
        
        return sorted(set(configs_from_memory + configs_from_files))
    
    def delete_config(self, name: str) -> None:
        """Delete a configuration."""
        # Remove from memory
        if name in self._configs:
            del self._configs[name]
        
        # Remove files
        for file_format in ConfigFormat:
            file_path = self.config_dir / f"{name}.{file_format.value}"
            if file_path.exists():
                file_path.unlink()
        
        logger.info(f"Deleted configuration: {name}")
    
    def update_config(self, name: str, updates: Dict[str, Any]) -> OSRSRLConfig:
        """Update specific values in a configuration."""
        config = self.get_config(name)
        if config is None:
            raise ValueError(f"Configuration not found: {name}")
        
        # Apply updates recursively
        config_dict = self._config_to_dict(config)
        self._update_dict_recursive(config_dict, updates)
        updated_config = self._dict_to_config(config_dict)
        
        self._configs[name] = updated_config
        logger.info(f"Updated configuration: {name}")
        return updated_config
    
    def _config_to_dict(self, config: OSRSRLConfig) -> Dict[str, Any]:
        """Convert configuration object to dictionary."""
        return {
            'agent': asdict(config.agent),
            'environment': asdict(config.environment),
            'training': asdict(config.training),
            'server': asdict(config.server)
        }
    
    def _dict_to_config(self, data: Dict[str, Any]) -> OSRSRLConfig:
        """Convert dictionary to configuration object."""
        agent_data = data.get('agent', {})
        env_data = data.get('environment', {})
        training_data = data.get('training', {})
        server_data = data.get('server', {})
        
        return OSRSRLConfig(
            agent=AgentConfig(**agent_data),
            environment=EnvironmentConfig(**env_data),
            training=TrainingConfig(**training_data),
            server=ServerConfig(**server_data)
        )
    
    def _update_dict_recursive(self, original: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """Recursively update dictionary with new values."""
        for key, value in updates.items():
            if isinstance(value, dict) and key in original and isinstance(original[key], dict):
                self._update_dict_recursive(original[key], value)
            else:
                original[key] = value
    
    def create_task_specific_config(self, base_config_name: str, task_name: str, task_config: Dict[str, Any]) -> str:
        """Create a task-specific configuration based on a base config."""
        base_config = self.get_config(base_config_name)
        if base_config is None:
            base_config = OSRSRLConfig()
        
        # Create a copy and apply task-specific settings
        task_config_name = f"{base_config_name}_{task_name.replace(' ', '_')}"
        
        # Update with task-specific values
        updates = {
            'training': {
                'experiment_name': task_config_name
            },
            'environment': {
                'environment_name': f"{task_name}Env"
            }
        }
        
        # Merge with provided task config
        self._update_dict_recursive(updates, task_config)
        
        # Create the new configuration
        new_config = self.update_config(base_config_name, updates)
        self._configs[task_config_name] = new_config
        
        logger.info(f"Created task-specific configuration: {task_config_name}")
        return task_config_name


# Global configuration manager instance
_global_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager