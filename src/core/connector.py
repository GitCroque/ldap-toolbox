"""LDAP connection management."""

import time
from typing import Any, Dict, List, Optional, Tuple

from ldap3 import ALL, ALL_ATTRIBUTES, Connection, Server, Tls
from ldap3.core.exceptions import LDAPException

from src.core.models import LDAPConfig


class LDAPConnector:
    """Manages LDAP server connections."""

    def __init__(self, config: LDAPConfig) -> None:
        """Initialize LDAP connector.

        Args:
            config: LDAP configuration
        """
        self.config = config
        self._server: Optional[Server] = None
        self._connection: Optional[Connection] = None

    def connect(self) -> Connection:
        """Establish connection to LDAP server.

        Returns:
            LDAP connection object

        Raises:
            LDAPException: If connection fails
        """
        if self._connection and self._connection.bound:
            return self._connection

        # Create server object
        tls_config = None
        if self.config.use_tls:
            tls_config = Tls(validate=0)  # For production, configure proper TLS validation

        protocol = "ldaps" if self.config.use_ssl else "ldap"
        server_uri = f"{protocol}://{self.config.server}"

        self._server = Server(
            host=self.config.server,
            port=self.config.port,
            use_ssl=self.config.use_ssl,
            tls=tls_config,
            get_info=ALL,
            connect_timeout=self.config.timeout,
        )

        # Create connection with retry logic
        last_exception = None
        for attempt in range(self.config.retry_max):
            try:
                self._connection = Connection(
                    self._server,
                    user=self.config.bind_dn,
                    password=self.config.bind_password,
                    auto_bind=True,
                    raise_exceptions=True,
                )
                return self._connection
            except LDAPException as e:
                last_exception = e
                if attempt < self.config.retry_max - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))

        raise LDAPException(
            f"Failed to connect after {self.config.retry_max} attempts: {last_exception}"
        )

    def disconnect(self) -> None:
        """Close LDAP connection."""
        if self._connection:
            self._connection.unbind()
            self._connection = None

    def search(
        self,
        search_base: Optional[str] = None,
        search_filter: str = "(objectClass=*)",
        attributes: Optional[List[str]] = None,
        paged: bool = True,
    ) -> List[Dict[str, Any]]:
        """Search LDAP directory.

        Args:
            search_base: Base DN for search (defaults to config base_dn)
            search_filter: LDAP search filter
            attributes: List of attributes to retrieve (None for all)
            paged: Use paged search for large results

        Returns:
            List of entries with their attributes

        Raises:
            LDAPException: If search fails
        """
        conn = self.connect()
        base = search_base or self.config.base_dn

        if attributes is None:
            attributes = ALL_ATTRIBUTES

        results = []

        try:
            if paged:
                conn.search(
                    search_base=base,
                    search_filter=search_filter,
                    attributes=attributes,
                    paged_size=self.config.page_size,
                )

                # Collect all paged results
                while True:
                    results.extend(conn.entries)
                    cookie = conn.result["controls"]["1.2.840.113556.1.4.319"]["value"][
                        "cookie"
                    ]
                    if not cookie:
                        break
                    conn.search(
                        search_base=base,
                        search_filter=search_filter,
                        attributes=attributes,
                        paged_size=self.config.page_size,
                        paged_cookie=cookie,
                    )
            else:
                conn.search(
                    search_base=base, search_filter=search_filter, attributes=attributes
                )
                results = conn.entries

        except LDAPException as e:
            raise LDAPException(f"Search failed: {e}") from e

        # Convert entries to dictionaries
        return [self._entry_to_dict(entry) for entry in results]

    def get_entry(self, dn: str, attributes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get a single entry by DN.

        Args:
            dn: Distinguished Name of the entry
            attributes: List of attributes to retrieve

        Returns:
            Entry dictionary or None if not found
        """
        conn = self.connect()

        if attributes is None:
            attributes = ALL_ATTRIBUTES

        try:
            conn.search(
                search_base=dn,
                search_filter="(objectClass=*)",
                search_scope="BASE",
                attributes=attributes,
            )

            if conn.entries:
                return self._entry_to_dict(conn.entries[0])
            return None

        except LDAPException:
            return None

    def add_entry(self, dn: str, object_class: List[str], attributes: Dict[str, Any]) -> bool:
        """Add new LDAP entry.

        Args:
            dn: Distinguished Name for new entry
            object_class: List of object classes
            attributes: Entry attributes

        Returns:
            True if successful

        Raises:
            LDAPException: If add operation fails
        """
        conn = self.connect()

        try:
            conn.add(dn, object_class, attributes)
            return conn.result["result"] == 0
        except LDAPException as e:
            raise LDAPException(f"Failed to add entry {dn}: {e}") from e

    def modify_entry(self, dn: str, changes: Dict[str, Any]) -> bool:
        """Modify LDAP entry.

        Args:
            dn: Distinguished Name of entry to modify
            changes: Dictionary of attribute changes

        Returns:
            True if successful

        Raises:
            LDAPException: If modify operation fails
        """
        conn = self.connect()

        try:
            conn.modify(dn, changes)
            return conn.result["result"] == 0
        except LDAPException as e:
            raise LDAPException(f"Failed to modify entry {dn}: {e}") from e

    def delete_entry(self, dn: str) -> bool:
        """Delete LDAP entry.

        Args:
            dn: Distinguished Name of entry to delete

        Returns:
            True if successful

        Raises:
            LDAPException: If delete operation fails
        """
        conn = self.connect()

        try:
            conn.delete(dn)
            return conn.result["result"] == 0
        except LDAPException as e:
            raise LDAPException(f"Failed to delete entry {dn}: {e}") from e

    def test_connection(self) -> Tuple[bool, float, Optional[str]]:
        """Test LDAP connection.

        Returns:
            Tuple of (success, response_time_ms, error_message)
        """
        start_time = time.time()

        try:
            conn = self.connect()
            # Try a simple search to verify connection works
            conn.search(
                search_base=self.config.base_dn,
                search_filter="(objectClass=*)",
                search_scope="BASE",
                attributes=["objectClass"],
            )
            response_time = (time.time() - start_time) * 1000
            return True, response_time, None
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, str(e)

    def get_server_info(self) -> Dict[str, Any]:
        """Get LDAP server information.

        Returns:
            Dictionary with server information
        """
        conn = self.connect()

        if not self._server:
            return {}

        info = {
            "host": self._server.host,
            "port": self._server.port,
            "ssl": self._server.ssl,
            "schema": {},
        }

        # Get server schema information if available
        if self._server.info:
            info["schema"] = {
                "naming_contexts": self._server.info.naming_contexts,
                "supported_ldap_versions": self._server.info.supported_ldap_versions,
                "vendor": self._server.info.vendor_name if hasattr(self._server.info, 'vendor_name') else None,
            }

        return info

    def _entry_to_dict(self, entry: Any) -> Dict[str, Any]:
        """Convert LDAP entry to dictionary.

        Args:
            entry: LDAP entry object

        Returns:
            Dictionary representation of entry
        """
        result = {"dn": entry.entry_dn, "attributes": {}}

        for attr in entry.entry_attributes:
            value = entry[attr].value
            # Convert single-item lists to single values
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            result["attributes"][attr] = value

        return result

    def __enter__(self) -> "LDAPConnector":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.disconnect()
