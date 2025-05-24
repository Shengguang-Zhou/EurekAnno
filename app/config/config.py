import os
import yaml
from typing import Dict, Any, Optional

class Config:
    """
    Configuration loader for the application.
    
    Loads configuration from app/config/config.yaml and provides
    easy access to configuration values.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Optional path to configuration file.
                         Defaults to app/config/config.yaml.
        """
        if config_path is None:
            # Get the directory of the current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "config.yaml")
        
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as config_file:
                self.config = yaml.safe_load(config_file)
        except FileNotFoundError:
            print(f"Warning: Configuration file not found at {self.config_path}")
            self.config = {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML configuration: {e}")
            self.config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Uses dot notation for nested keys (e.g., "models.yoloe.yoloe-seg").
        
        Args:
            key: Configuration key in dot notation.
            default: Default value if key is not found.
            
        Returns:
            Configuration value if found, default otherwise.
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_models_config(self) -> Dict[str, Any]:
        """
        Get models configuration section.
        
        Returns:
            Models configuration dictionary.
        """
        return self.get("models", {})
    
    def get_yoloe_model_paths(self) -> Dict[str, str]:
        """
        Get YOLOE model paths configuration.
        
        Returns:
            Dictionary with YOLOE model paths.
        """
        return self.get("models.yoloe", {})
    
    def get_yoloe_seg_path(self) -> str:
        """
        Get path to YOLOE-SEG model.
        
        Returns:
            Path to YOLOE-SEG model or an empty string if not configured.
        """
        return self.get("models.yoloe.yoloe-seg", "")
    
    def get_yoloe_seg_pf_path(self) -> str:
        """
        Get path to YOLOE-SEG-PF model.
        
        Returns:
            Path to YOLOE-SEG-PF model or an empty string if not configured.
        """
        return self.get("models.yoloe.yoloe-seg-pf", "")
    
    def get_moondream_model_path(self) -> str:
        """
        Get path to Moondream model.
        
        Returns:
            Path to Moondream model or an empty string if not configured.
        """
        return self.get("models.moondream.model", "")


# Create global configuration instance
config = Config() 