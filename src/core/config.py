"""Configuration management for LDAP Health Monitor."""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

from src.core.models import Config


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file. If None, searches for config.yaml
                        in current directory and ~/.config/ldap-monitor/
        """
        self.config_path = self._find_config(config_path)
        self._raw_config: Dict[str, Any] = {}
        self._config: Optional[Config] = None

    def _find_config(self, config_path: Optional[str] = None) -> Optional[Path]:
        """Find configuration file.

        Args:
            config_path: Explicit path to config file

        Returns:
            Path to config file or None if not found
        """
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Search in common locations
        search_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path.home() / ".config" / "ldap-monitor" / "config.yaml",
            Path("/etc/ldap-monitor/config.yaml"),
        ]

        for path in search_paths:
            if path.exists():
                return path

        return None

    def load(self, config_path: Optional[str] = None) -> Config:
        """Load and validate configuration.

        Args:
            config_path: Optional path to configuration file

        Returns:
            Validated configuration object

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        # Load environment variables
        load_dotenv()

        # Update config path if provided
        if config_path:
            self.config_path = self._find_config(config_path)

        if not self.config_path:
            raise FileNotFoundError(
                "No configuration file found. Create config.yaml or use --config option."
            )

        # Load YAML config
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._raw_config = yaml.safe_load(f) or {}

        # Replace environment variables
        self._raw_config = self._replace_env_vars(self._raw_config)

        # Validate and create config object
        try:
            self._config = Config(**self._raw_config)
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}") from e

        return self._config

    def _replace_env_vars(self, data: Any) -> Any:
        """Recursively replace ${VAR} with environment variables.

        Args:
            data: Configuration data (dict, list, or string)

        Returns:
            Data with environment variables replaced
        """
        if isinstance(data, dict):
            return {key: self._replace_env_vars(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._replace_env_vars(item) for item in data]
        elif isinstance(data, str):
            # Replace ${VAR} or $VAR with environment variable
            pattern = r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)"

            def replacer(match: re.Match) -> str:
                var_name = match.group(1) or match.group(2)
                return os.getenv(var_name, match.group(0))

            return re.sub(pattern, replacer, data)
        return data

    @property
    def config(self) -> Optional[Config]:
        """Get loaded configuration."""
        return self._config

    def validate(self) -> bool:
        """Validate current configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if not self._config:
            raise ValueError("Configuration not loaded. Call load() first.")

        # Validate LDAP connection settings
        if not self._config.ldap.server:
            raise ValueError("LDAP server not configured")

        if not self._config.ldap.bind_dn or not self._config.ldap.bind_password:
            raise ValueError("LDAP bind credentials not configured")

        if not self._config.ldap.base_dn:
            raise ValueError("LDAP base DN not configured")

        # Validate directories exist or can be created
        dirs_to_check = [
            self._config.backup.backup_dir,
            self._config.reports.output_dir,
        ]

        for dir_path in dirs_to_check:
            path = Path(dir_path)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise ValueError(f"Cannot create directory {dir_path}: {e}") from e

        return True

    def get_ldap_uri(self) -> str:
        """Get full LDAP URI.

        Returns:
            LDAP URI string
        """
        if not self._config:
            raise ValueError("Configuration not loaded")

        protocol = "ldaps" if self._config.ldap.use_ssl else "ldap"
        return f"{protocol}://{self._config.ldap.server}:{self._config.ldap.port}"

    def init_config(self, output_path: str = "config.yaml") -> None:
        """Create a new configuration file from example.

        Args:
            output_path: Path where to create the config file
        """
        example_path = Path(__file__).parent.parent.parent / "config.example.yaml"
        output = Path(output_path)

        if output.exists():
            raise FileExistsError(f"Configuration file already exists: {output_path}")

        if example_path.exists():
            # Copy example file
            with open(example_path, "r", encoding="utf-8") as f:
                content = f.read()
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Created configuration file: {output_path}")
            print("Please edit the file and configure your LDAP settings.")
        else:
            raise FileNotFoundError("config.example.yaml not found")


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance.

    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Loaded configuration
    """
    manager = get_config_manager()
    return manager.load(config_path)
