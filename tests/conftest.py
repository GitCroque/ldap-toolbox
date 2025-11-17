"""Pytest configuration and fixtures."""

import pytest

from src.core.models import Config, LDAPConfig


@pytest.fixture
def sample_config() -> Config:
    """Sample configuration for testing."""
    ldap_config = LDAPConfig(
        server="ldap://test.example.com",
        port=389,
        bind_dn="cn=admin,dc=test,dc=com",
        bind_password="password",
        base_dn="dc=test,dc=com",
        users_ou="ou=users,dc=test,dc=com",
        groups_ou="ou=groups,dc=test,dc=com",
    )

    return Config(ldap=ldap_config)


@pytest.fixture
def mock_ldap_connector(mocker):
    """Mock LDAP connector."""
    from src.core.connector import LDAPConnector

    mock = mocker.Mock(spec=LDAPConnector)
    mock.test_connection.return_value = (True, 100.0, None)
    return mock
