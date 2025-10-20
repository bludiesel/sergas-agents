"""Cross-database compatible types for SQLAlchemy.

Provides type adapters that work with both PostgreSQL and SQLite,
degrading gracefully based on the database backend.
"""

from typing import Any
import json

from sqlalchemy import TypeDecorator, Text, String
from sqlalchemy.dialects import postgresql


class JSONType(TypeDecorator):
    """Cross-database JSON type.

    Uses JSONB for PostgreSQL, TEXT with JSON encoding for SQLite.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.JSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect) -> str:
        """Convert Python value to database value."""
        if value is None:
            return None
        if dialect.name == 'postgresql':
            # PostgreSQL handles JSON natively
            return value
        else:
            # SQLite: encode as JSON string
            return json.dumps(value)

    def process_result_value(self, value: Any, dialect) -> Any:
        """Convert database value to Python value."""
        if value is None:
            return None
        if dialect.name == 'postgresql':
            # PostgreSQL returns dict/list directly
            return value
        else:
            # SQLite: decode JSON string
            return json.loads(value)


class ArrayType(TypeDecorator):
    """Cross-database array type.

    Uses ARRAY for PostgreSQL, TEXT with JSON encoding for SQLite.

    Args:
        item_type: Type of array items (e.g., String, Integer)
    """

    impl = Text
    cache_ok = True

    def __init__(self, item_type=None, *args, **kwargs):
        """Initialize with optional item type."""
        self.item_type = item_type
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the dialect."""
        if dialect.name == 'postgresql':
            if self.item_type:
                return dialect.type_descriptor(
                    postgresql.ARRAY(self.item_type)
                )
            else:
                return dialect.type_descriptor(postgresql.ARRAY(String))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect) -> Any:
        """Convert Python list to database value."""
        if value is None:
            return None
        if dialect.name == 'postgresql':
            # PostgreSQL handles arrays natively
            return value
        else:
            # SQLite: encode as JSON array
            return json.dumps(value)

    def process_result_value(self, value: Any, dialect) -> Any:
        """Convert database value to Python list."""
        if value is None:
            return None
        if dialect.name == 'postgresql':
            # PostgreSQL returns list directly
            return value
        else:
            # SQLite: decode JSON array
            return json.loads(value)
