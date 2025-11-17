"""Tests for configuration module."""

import pytest

from src.core.config import ConfigManager
from src.core.models import Config


def test_config_manager_init():
    """Test ConfigManager initialization."""
    manager = ConfigManager()
    assert manager is not None


def test_config_validation(sample_config):
    """Test configuration validation."""
    manager = ConfigManager()
    manager._config = sample_config
    assert manager.validate() is True


def test_config_ldap_uri(sample_config):
    """Test LDAP URI generation."""
    manager = ConfigManager()
    manager._config = sample_config
    uri = manager.get_ldap_uri()
    assert "ldap://" in uri or "ldaps://" in uri
