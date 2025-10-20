#!/usr/bin/env python3
"""
Test script for database test data creation
This is the extracted and fixed version of Step 7 from setup_sqlite.sh
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import create_engine, text
    from dotenv import load_dotenv

    # Load environment variables with explicit path (required for heredoc)
    load_dotenv('.env')

    # Get database URL, fallback to default if not set
    database_url = os.getenv("DATABASE_URL", "sqlite:///./data/sergas_agent.db")

    print(f"Database URL: {database_url}")

    # Create engine
    engine = create_engine(database_url, echo=False)

    # Use begin() for automatic transaction management
    with engine.begin() as conn:
        # Check if zoho_tokens table exists and has data
        result = conn.execute(text(
            "SELECT COUNT(*) as count FROM zoho_tokens"
        )).fetchone()

        print(f"Current record count: {result[0]}")

        if result[0] == 0:
            # Insert sample Zoho token
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=1)

            conn.execute(text("""
                INSERT INTO zoho_tokens (
                    token_type, access_token, refresh_token, expires_at,
                    created_at, updated_at
                ) VALUES (
                    :token_type, :access_token, :refresh_token, :expires_at,
                    :created_at, :updated_at
                )
            """), {
                "token_type": "Bearer",
                "access_token": "sample_access_token_for_development",
                "refresh_token": "sample_refresh_token_for_development",
                "expires_at": expires_at,
                "created_at": now,
                "updated_at": now
            })
            print("✓ Created sample Zoho token record")
        else:
            print("✓ Zoho tokens table already has data")

    print("✓ Database initialization complete")

    # Verify the data was inserted
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, token_type, access_token, expires_at FROM zoho_tokens LIMIT 1"
        )).fetchone()

        if result:
            print(f"\nVerification:")
            print(f"  ID: {result[0]}")
            print(f"  Token Type: {result[1]}")
            print(f"  Access Token: {result[2][:30]}...")
            print(f"  Expires At: {result[3]}")

except Exception as e:
    import traceback
    print(f"✗ Error creating test data: {e}", file=sys.stderr)
    print("\nFull traceback:", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
