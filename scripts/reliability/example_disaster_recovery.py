#!/usr/bin/env python3
"""
Example disaster recovery automation script.

Demonstrates backup creation, restoration, and recovery testing.

Usage:
    # Create backup
    python scripts/reliability/example_disaster_recovery.py create-backup --name=emergency

    # List backups
    python scripts/reliability/example_disaster_recovery.py list-backups

    # Restore backup
    python scripts/reliability/example_disaster_recovery.py restore --backup-id=<id>

    # Test recovery
    python scripts/reliability/example_disaster_recovery.py test-recovery
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.reliability.disaster_recovery import (
    BackupManager,
    BackupType,
    BackupStatus,
    FileSystemBackupStrategy,
    DatabaseBackupStrategy,
    RecoveryTestRunner,
    PointInTimeRecovery,
)


async def create_backup(args):
    """Create a new backup."""
    backup_dir = Path("./backups")
    manager = BackupManager(backup_dir)

    # Register strategies
    fs_strategy = FileSystemBackupStrategy(compress=True)
    manager.register_strategy("filesystem", fs_strategy)

    # Create backup
    print(f"Creating backup: {args.name}")

    metadata = await manager.create_backup(
        name=args.name,
        source=args.source or "./data",
        backup_type=BackupType(args.type) if args.type else BackupType.FULL,
        strategy="filesystem",
        retention_days=args.retention or 30
    )

    if metadata and metadata.status == BackupStatus.COMPLETED:
        print(f"✓ Backup created successfully!")
        print(f"  Backup ID: {metadata.backup_id}")
        print(f"  Size: {metadata.size_bytes / 1024 / 1024:.2f} MB")
        print(f"  Location: {metadata.destination_path}")
        print(f"  Checksum: {metadata.checksum}")
    else:
        print(f"✗ Backup failed!")
        if metadata:
            print(f"  Error: {metadata.error}")
        sys.exit(1)


async def list_backups(args):
    """List all backups."""
    backup_dir = Path("./backups")
    manager = BackupManager(backup_dir)

    # Get backups with filters
    backup_type = BackupType(args.type) if args.type else None
    status = BackupStatus(args.status) if args.status else None

    backups = manager.list_backups(backup_type=backup_type, status=status)

    if not backups:
        print("No backups found.")
        return

    # Print header
    print(f"\n{'Backup ID':<40} {'Type':<15} {'Status':<12} {'Size':<10} {'Date':<20}")
    print("-" * 100)

    # Print backups
    for backup in backups:
        size_mb = backup.size_bytes / 1024 / 1024
        timestamp = backup.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        print(
            f"{backup.backup_id:<40} "
            f"{backup.backup_type.value:<15} "
            f"{backup.status.value:<12} "
            f"{size_mb:>8.2f}MB "
            f"{timestamp:<20}"
        )

    print(f"\nTotal backups: {len(backups)}")


async def restore_backup(args):
    """Restore from backup."""
    backup_dir = Path("./backups")
    manager = BackupManager(backup_dir)

    # Register strategies
    fs_strategy = FileSystemBackupStrategy(compress=True)
    manager.register_strategy("filesystem", fs_strategy)

    print(f"Restoring backup: {args.backup_id}")
    print(f"Destination: {args.destination}")

    # Confirm if not dry-run
    if not args.dry_run:
        response = input("This will overwrite existing data. Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Restore cancelled.")
            return

    success = await manager.restore_backup(
        backup_id=args.backup_id,
        restore_path=args.destination,
        strategy="filesystem"
    )

    if success:
        print(f"✓ Restore completed successfully!")
    else:
        print(f"✗ Restore failed!")
        sys.exit(1)


async def test_recovery(args):
    """Run recovery tests."""
    backup_dir = Path("./backups")
    test_dir = Path("./test_recovery")

    manager = BackupManager(backup_dir)
    test_runner = RecoveryTestRunner(manager, test_dir)

    # Register strategies
    fs_strategy = FileSystemBackupStrategy(compress=True)
    manager.register_strategy("filesystem", fs_strategy)

    print("Running recovery drill...")
    print("-" * 60)

    results = await test_runner.run_recovery_drill()

    # Print results
    print(f"\nRecovery Drill Results:")
    print(f"Start Time: {results['start_time']}")
    print(f"End Time: {results['end_time']}")
    print(f"Tests Passed: {results['passed']}")
    print(f"Tests Failed: {results['failed']}")
    print(f"Overall Success: {'✓ PASS' if results['overall_success'] else '✗ FAIL'}")

    print(f"\nDetailed Results:")
    for test in results['tests']:
        status = "✓ PASS" if test['passed'] else "✗ FAIL"
        print(f"  {status} {test['backup_id']} ({test['backup_type']})")

    # Exit with appropriate code
    sys.exit(0 if results['overall_success'] else 1)


async def cleanup_old_backups(args):
    """Remove old backups past retention period."""
    backup_dir = Path("./backups")
    manager = BackupManager(backup_dir)

    print("Cleaning up old backups...")

    # Get count before cleanup
    before_count = len(manager.list_backups())

    # Run cleanup
    await manager.cleanup_old_backups()

    # Get count after cleanup
    after_count = len(manager.list_backups())

    removed = before_count - after_count

    print(f"✓ Cleanup complete!")
    print(f"  Removed: {removed} backups")
    print(f"  Remaining: {after_count} backups")


async def point_in_time_recovery(args):
    """Perform point-in-time recovery."""
    backup_dir = Path("./backups")
    manager = BackupManager(backup_dir)

    pitr = PointInTimeRecovery(manager)

    target_time = datetime.fromisoformat(args.target_time)

    print(f"Point-in-Time Recovery to: {target_time}")
    print(f"Destination: {args.destination}")

    success = await pitr.recover_to_point(
        target_time=target_time,
        restore_path=args.destination
    )

    if success:
        print(f"✓ PITR completed successfully!")
    else:
        print(f"✗ PITR failed!")
        sys.exit(1)


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Disaster recovery automation"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create backup command
    create_parser = subparsers.add_parser("create-backup", help="Create a new backup")
    create_parser.add_argument("--name", required=True, help="Backup name")
    create_parser.add_argument("--source", help="Source path to backup")
    create_parser.add_argument("--type", choices=["full", "incremental", "differential", "snapshot"], help="Backup type")
    create_parser.add_argument("--retention", type=int, help="Retention period in days")

    # List backups command
    list_parser = subparsers.add_parser("list-backups", help="List all backups")
    list_parser.add_argument("--type", choices=["full", "incremental", "differential", "snapshot"], help="Filter by type")
    list_parser.add_argument("--status", choices=["pending", "in_progress", "completed", "failed", "verified"], help="Filter by status")

    # Restore backup command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("--backup-id", required=True, help="Backup ID to restore")
    restore_parser.add_argument("--destination", required=True, help="Restore destination path")
    restore_parser.add_argument("--dry-run", action="store_true", help="Dry run without actual restoration")

    # Test recovery command
    test_parser = subparsers.add_parser("test-recovery", help="Run recovery tests")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Remove old backups")

    # PITR command
    pitr_parser = subparsers.add_parser("pitr", help="Point-in-time recovery")
    pitr_parser.add_argument("--target-time", required=True, help="Target time (ISO format)")
    pitr_parser.add_argument("--destination", required=True, help="Restore destination path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "create-backup":
        await create_backup(args)
    elif args.command == "list-backups":
        await list_backups(args)
    elif args.command == "restore":
        await restore_backup(args)
    elif args.command == "test-recovery":
        await test_recovery(args)
    elif args.command == "cleanup":
        await cleanup_old_backups(args)
    elif args.command == "pitr":
        await point_in_time_recovery(args)


if __name__ == "__main__":
    asyncio.run(main())
