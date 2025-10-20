"""
SQLite Database Adapter
Replacement for PostgreSQL for testing and development
"""
import os
import sqlite3
import aiosqlite
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from pathlib import Path


class SQLiteAdapter:
    """SQLite database adapter with async support"""

    def __init__(self, db_path: str = "./data/test_sergas.db"):
        self.db_path = db_path
        self._ensure_directory()
        self._connection: Optional[aiosqlite.Connection] = None

    def _ensure_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    async def connect(self) -> aiosqlite.Connection:
        """Get or create async connection"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            await self._initialize_schema()
        return self._connection

    async def _initialize_schema(self):
        """Initialize database schema"""
        conn = await self.connect()

        # Create sessions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_sessions (
                session_id TEXT PRIMARY KEY,
                orchestrator_id TEXT NOT NULL,
                account_owner_id TEXT,
                account_ids TEXT,  -- JSON array
                status TEXT DEFAULT 'active',
                workflow_state TEXT,  -- JSON object
                subagent_results TEXT,  -- JSON object
                approval_status TEXT DEFAULT 'pending',
                error_log TEXT,  -- JSON array
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)

        # Create audit events table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                session_id TEXT,
                agent_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,  -- JSON object
                severity TEXT DEFAULT 'info',
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES agent_sessions(session_id)
            )
        """)

        # Create token persistence table (for Zoho OAuth)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                token_id TEXT PRIMARY KEY,
                service_name TEXT NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                expires_at TEXT NOT NULL,
                scope TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_status
            ON agent_sessions(status)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_created
            ON agent_sessions(created_at)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_session
            ON audit_events(session_id)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp
            ON audit_events(timestamp)
        """)

        await conn.commit()

    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Execute a query"""
        conn = await self.connect()
        cursor = await conn.execute(query, params)
        await conn.commit()
        return cursor

    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch one row"""
        conn = await self.connect()
        cursor = await conn.execute(query, params)
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        conn = await self.connect()
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def close(self):
        """Close connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None

    # Session Management Methods
    async def create_session(
        self,
        session_id: str,
        orchestrator_id: str,
        account_owner_id: Optional[str] = None,
        account_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new session"""
        now = datetime.utcnow().isoformat()

        await self.execute("""
            INSERT INTO agent_sessions (
                session_id, orchestrator_id, account_owner_id,
                account_ids, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            orchestrator_id,
            account_owner_id,
            json.dumps(account_ids or []),
            now,
            now
        ))

        return await self.get_session(session_id)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        session = await self.fetch_one(
            "SELECT * FROM agent_sessions WHERE session_id = ?",
            (session_id,)
        )

        if session:
            # Parse JSON fields
            session['account_ids'] = json.loads(session.get('account_ids', '[]'))
            if session.get('workflow_state'):
                session['workflow_state'] = json.loads(session['workflow_state'])
            if session.get('subagent_results'):
                session['subagent_results'] = json.loads(session['subagent_results'])
            if session.get('error_log'):
                session['error_log'] = json.loads(session['error_log'])

        return session

    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update session"""
        # Convert complex types to JSON
        for key in ['account_ids', 'workflow_state', 'subagent_results', 'error_log']:
            if key in updates and not isinstance(updates[key], str):
                updates[key] = json.dumps(updates[key])

        updates['updated_at'] = datetime.utcnow().isoformat()

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [session_id]

        await self.execute(
            f"UPDATE agent_sessions SET {set_clause} WHERE session_id = ?",
            tuple(values)
        )

        return await self.get_session(session_id)

    async def log_audit_event(
        self,
        event_id: str,
        session_id: str,
        agent_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        severity: str = "info"
    ):
        """Log an audit event"""
        await self.execute("""
            INSERT INTO audit_events (
                event_id, session_id, agent_id, event_type,
                event_data, severity, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            session_id,
            agent_id,
            event_type,
            json.dumps(event_data),
            severity,
            datetime.utcnow().isoformat()
        ))

    async def get_audit_events(
        self,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit events"""
        if session_id:
            query = """
                SELECT * FROM audit_events
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            events = await self.fetch_all(query, (session_id, limit))
        else:
            query = """
                SELECT * FROM audit_events
                ORDER BY timestamp DESC
                LIMIT ?
            """
            events = await self.fetch_all(query, (limit,))

        # Parse event_data
        for event in events:
            if event.get('event_data'):
                event['event_data'] = json.loads(event['event_data'])

        return events


# Singleton instance
_sqlite_adapter: Optional[SQLiteAdapter] = None


def get_sqlite_adapter(db_path: Optional[str] = None) -> SQLiteAdapter:
    """Get singleton SQLite adapter"""
    global _sqlite_adapter

    if _sqlite_adapter is None:
        from dotenv import load_dotenv
        load_dotenv('.env.test')

        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', './data/test_sergas.db')

        _sqlite_adapter = SQLiteAdapter(db_path)

    return _sqlite_adapter
