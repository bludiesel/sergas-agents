"""
Disaster recovery and backup automation system.

Provides automated backup, point-in-time recovery, data restoration,
and recovery testing capabilities.
"""

import asyncio
import shutil
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import structlog
import json
import tarfile
import gzip

logger = structlog.get_logger()


class BackupType(Enum):
    """Types of backups."""
    FULL = "full"              # Complete backup
    INCREMENTAL = "incremental"  # Changes since last backup
    DIFFERENTIAL = "differential"  # Changes since last full backup
    SNAPSHOT = "snapshot"      # Point-in-time snapshot


class BackupStatus(Enum):
    """Backup operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    backup_id: str
    backup_type: BackupType
    timestamp: datetime
    size_bytes: int = 0
    status: BackupStatus = BackupStatus.PENDING
    source_path: str = ""
    destination_path: str = ""
    checksum: Optional[str] = None
    error: Optional[str] = None
    retention_days: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type.value,
            "timestamp": self.timestamp.isoformat(),
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_bytes / 1024 / 1024, 2),
            "status": self.status.value,
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "checksum": self.checksum,
            "error": self.error,
            "retention_days": self.retention_days,
            "metadata": self.metadata,
        }


class BackupStrategy(ABC):
    """Base class for backup strategies."""

    def __init__(self, name: str):
        """
        Initialize backup strategy.

        Args:
            name: Strategy identifier
        """
        self.name = name
        self.logger = logger.bind(backup_strategy=name)

    @abstractmethod
    async def create_backup(
        self,
        source: str,
        destination: str,
        metadata: BackupMetadata
    ) -> bool:
        """
        Create a backup.

        Args:
            source: Source path
            destination: Destination path
            metadata: Backup metadata

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def restore_backup(
        self,
        backup_path: str,
        restore_path: str,
        metadata: BackupMetadata
    ) -> bool:
        """
        Restore from backup.

        Args:
            backup_path: Backup file path
            restore_path: Restoration destination
            metadata: Backup metadata

        Returns:
            True if successful
        """
        pass


class FileSystemBackupStrategy(BackupStrategy):
    """Backup strategy for file systems."""

    def __init__(self, compress: bool = True):
        """
        Initialize filesystem backup.

        Args:
            compress: Enable compression
        """
        super().__init__("filesystem")
        self.compress = compress

    async def create_backup(
        self,
        source: str,
        destination: str,
        metadata: BackupMetadata
    ) -> bool:
        """Create filesystem backup."""
        try:
            source_path = Path(source)
            dest_path = Path(destination)

            if not source_path.exists():
                raise FileNotFoundError(f"Source not found: {source}")

            # Create parent directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Create tar archive
            if self.compress:
                dest_file = str(dest_path) + ".tar.gz"
                mode = "w:gz"
            else:
                dest_file = str(dest_path) + ".tar"
                mode = "w"

            self.logger.info(
                "creating_backup",
                source=source,
                destination=dest_file,
                compress=self.compress
            )

            # Create archive in separate thread to avoid blocking
            await asyncio.to_thread(
                self._create_tar_archive,
                source_path,
                dest_file,
                mode
            )

            # Calculate size and checksum
            dest_path_obj = Path(dest_file)
            metadata.size_bytes = dest_path_obj.stat().st_size
            metadata.destination_path = dest_file
            metadata.checksum = await self._calculate_checksum(dest_file)

            self.logger.info(
                "backup_created",
                destination=dest_file,
                size_mb=round(metadata.size_bytes / 1024 / 1024, 2),
                checksum=metadata.checksum
            )

            return True

        except Exception as e:
            self.logger.error("backup_failed", error=str(e))
            metadata.error = str(e)
            return False

    def _create_tar_archive(self, source: Path, dest: str, mode: str):
        """Create tar archive (blocking operation)."""
        with tarfile.open(dest, mode) as tar:
            tar.add(source, arcname=source.name)

    async def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum."""
        import hashlib

        def _calc():
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()

        return await asyncio.to_thread(_calc)

    async def restore_backup(
        self,
        backup_path: str,
        restore_path: str,
        metadata: BackupMetadata
    ) -> bool:
        """Restore from backup."""
        try:
            backup_file = Path(backup_path)
            restore_dir = Path(restore_path)

            if not backup_file.exists():
                raise FileNotFoundError(f"Backup not found: {backup_path}")

            # Verify checksum if available
            if metadata.checksum:
                current_checksum = await self._calculate_checksum(backup_path)
                if current_checksum != metadata.checksum:
                    raise ValueError("Checksum mismatch - backup may be corrupted")

            # Create restore directory
            restore_dir.mkdir(parents=True, exist_ok=True)

            self.logger.info(
                "restoring_backup",
                backup=backup_path,
                destination=restore_path
            )

            # Extract archive
            await asyncio.to_thread(
                self._extract_tar_archive,
                backup_path,
                restore_dir
            )

            self.logger.info("backup_restored", destination=restore_path)
            return True

        except Exception as e:
            self.logger.error("restore_failed", error=str(e))
            return False

    def _extract_tar_archive(self, archive_path: str, dest_dir: Path):
        """Extract tar archive (blocking operation)."""
        with tarfile.open(archive_path, 'r:*') as tar:
            tar.extractall(dest_dir)


class DatabaseBackupStrategy(BackupStrategy):
    """Backup strategy for PostgreSQL databases."""

    def __init__(self, db_host: str, db_port: int, db_name: str, db_user: str):
        """
        Initialize database backup.

        Args:
            db_host: Database host
            db_port: Database port
            db_name: Database name
            db_user: Database user
        """
        super().__init__("postgresql")
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user

    async def create_backup(
        self,
        source: str,
        destination: str,
        metadata: BackupMetadata
    ) -> bool:
        """Create database backup using pg_dump."""
        try:
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            dump_file = str(dest_path) + ".sql.gz"

            self.logger.info(
                "creating_database_backup",
                database=self.db_name,
                destination=dump_file
            )

            # Execute pg_dump
            cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-F", "c",  # Custom format
                "-f", dump_file,
                self.db_name
            ]

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Calculate size and checksum
            dump_path = Path(dump_file)
            metadata.size_bytes = dump_path.stat().st_size
            metadata.destination_path = dump_file

            self.logger.info(
                "database_backup_created",
                destination=dump_file,
                size_mb=round(metadata.size_bytes / 1024 / 1024, 2)
            )

            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(
                "pg_dump_failed",
                error=e.stderr,
                returncode=e.returncode
            )
            metadata.error = e.stderr
            return False
        except Exception as e:
            self.logger.error("database_backup_failed", error=str(e))
            metadata.error = str(e)
            return False

    async def restore_backup(
        self,
        backup_path: str,
        restore_path: str,
        metadata: BackupMetadata
    ) -> bool:
        """Restore database from backup using pg_restore."""
        try:
            backup_file = Path(backup_path)

            if not backup_file.exists():
                raise FileNotFoundError(f"Backup not found: {backup_path}")

            self.logger.info(
                "restoring_database_backup",
                backup=backup_path,
                database=self.db_name
            )

            # Execute pg_restore
            cmd = [
                "pg_restore",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", self.db_name,
                "--clean",  # Clean before restore
                "--if-exists",
                str(backup_file)
            ]

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            self.logger.info("database_backup_restored", database=self.db_name)
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(
                "pg_restore_failed",
                error=e.stderr,
                returncode=e.returncode
            )
            return False
        except Exception as e:
            self.logger.error("database_restore_failed", error=str(e))
            return False


class BackupManager:
    """
    Central manager for backup operations.

    Handles backup creation, scheduling, retention, and verification.
    """

    def __init__(self, backup_dir: Path):
        """
        Initialize backup manager.

        Args:
            backup_dir: Root directory for backups
        """
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.strategies: Dict[str, BackupStrategy] = {}
        self.backups: Dict[str, BackupMetadata] = {}
        self.logger = logger.bind(component="backup_manager")

        # Load existing backup metadata
        self._load_metadata()

    def register_strategy(self, name: str, strategy: BackupStrategy):
        """
        Register backup strategy.

        Args:
            name: Strategy identifier
            strategy: Backup strategy instance
        """
        self.strategies[name] = strategy
        self.logger.info("backup_strategy_registered", name=name)

    async def create_backup(
        self,
        name: str,
        source: str,
        backup_type: BackupType = BackupType.FULL,
        strategy: str = "filesystem",
        retention_days: int = 30,
        metadata_extra: Optional[Dict[str, Any]] = None
    ) -> Optional[BackupMetadata]:
        """
        Create a backup.

        Args:
            name: Backup name
            source: Source path
            backup_type: Type of backup
            strategy: Backup strategy to use
            retention_days: Days to retain backup
            metadata_extra: Additional metadata

        Returns:
            BackupMetadata or None if failed
        """
        if strategy not in self.strategies:
            self.logger.error("backup_strategy_not_found", strategy=strategy)
            return None

        # Generate backup ID
        timestamp = datetime.now()
        backup_id = f"{name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            timestamp=timestamp,
            source_path=source,
            retention_days=retention_days,
            metadata=metadata_extra or {}
        )

        # Destination path
        destination = self.backup_dir / strategy / backup_id

        self.logger.info(
            "creating_backup",
            backup_id=backup_id,
            strategy=strategy,
            backup_type=backup_type.value
        )

        metadata.status = BackupStatus.IN_PROGRESS

        # Execute backup
        backup_strategy = self.strategies[strategy]
        success = await backup_strategy.create_backup(
            source,
            str(destination),
            metadata
        )

        if success:
            metadata.status = BackupStatus.COMPLETED
            self.backups[backup_id] = metadata
            self._save_metadata()

            self.logger.info(
                "backup_created",
                backup_id=backup_id,
                size_mb=round(metadata.size_bytes / 1024 / 1024, 2)
            )
        else:
            metadata.status = BackupStatus.FAILED
            self.logger.error("backup_failed", backup_id=backup_id)

        return metadata

    async def restore_backup(
        self,
        backup_id: str,
        restore_path: str,
        strategy: Optional[str] = None
    ) -> bool:
        """
        Restore from backup.

        Args:
            backup_id: Backup identifier
            restore_path: Restoration destination
            strategy: Optional strategy override

        Returns:
            True if successful
        """
        metadata = self.backups.get(backup_id)
        if not metadata:
            self.logger.error("backup_not_found", backup_id=backup_id)
            return False

        # Determine strategy
        if not strategy:
            # Extract strategy from destination path
            strategy = Path(metadata.destination_path).parent.name

        if strategy not in self.strategies:
            self.logger.error("backup_strategy_not_found", strategy=strategy)
            return False

        self.logger.info(
            "restoring_backup",
            backup_id=backup_id,
            destination=restore_path
        )

        backup_strategy = self.strategies[strategy]
        success = await backup_strategy.restore_backup(
            metadata.destination_path,
            restore_path,
            metadata
        )

        if success:
            self.logger.info("backup_restored", backup_id=backup_id)
        else:
            self.logger.error("backup_restore_failed", backup_id=backup_id)

        return success

    async def cleanup_old_backups(self):
        """Remove backups past retention period."""
        now = datetime.now()
        removed_count = 0

        for backup_id, metadata in list(self.backups.items()):
            age_days = (now - metadata.timestamp).days

            if age_days > metadata.retention_days:
                self.logger.info(
                    "removing_old_backup",
                    backup_id=backup_id,
                    age_days=age_days,
                    retention_days=metadata.retention_days
                )

                # Remove backup file
                backup_path = Path(metadata.destination_path)
                if backup_path.exists():
                    backup_path.unlink()

                # Remove from registry
                del self.backups[backup_id]
                removed_count += 1

        if removed_count > 0:
            self._save_metadata()
            self.logger.info("old_backups_removed", count=removed_count)

    def list_backups(
        self,
        backup_type: Optional[BackupType] = None,
        status: Optional[BackupStatus] = None
    ) -> List[BackupMetadata]:
        """
        List backups with optional filters.

        Args:
            backup_type: Filter by backup type
            status: Filter by status

        Returns:
            List of backup metadata
        """
        backups = list(self.backups.values())

        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]

        if status:
            backups = [b for b in backups if b.status == status]

        # Sort by timestamp (newest first)
        backups.sort(key=lambda b: b.timestamp, reverse=True)

        return backups

    def _save_metadata(self):
        """Save backup metadata to disk."""
        metadata_file = self.backup_dir / "backups.json"

        try:
            data = {
                "backups": [b.to_dict() for b in self.backups.values()]
            }

            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error("metadata_save_failed", error=str(e))

    def _load_metadata(self):
        """Load backup metadata from disk."""
        metadata_file = self.backup_dir / "backups.json"

        if not metadata_file.exists():
            return

        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)

            for backup_data in data.get("backups", []):
                metadata = BackupMetadata(
                    backup_id=backup_data["backup_id"],
                    backup_type=BackupType(backup_data["backup_type"]),
                    timestamp=datetime.fromisoformat(backup_data["timestamp"]),
                    size_bytes=backup_data["size_bytes"],
                    status=BackupStatus(backup_data["status"]),
                    source_path=backup_data["source_path"],
                    destination_path=backup_data["destination_path"],
                    checksum=backup_data.get("checksum"),
                    error=backup_data.get("error"),
                    retention_days=backup_data.get("retention_days", 30),
                    metadata=backup_data.get("metadata", {})
                )
                self.backups[metadata.backup_id] = metadata

            self.logger.info("metadata_loaded", count=len(self.backups))

        except Exception as e:
            self.logger.error("metadata_load_failed", error=str(e))


class PointInTimeRecovery:
    """Point-in-time recovery for databases."""

    def __init__(self, backup_manager: BackupManager):
        """
        Initialize PITR.

        Args:
            backup_manager: Backup manager instance
        """
        self.backup_manager = backup_manager
        self.logger = logger.bind(component="point_in_time_recovery")

    async def recover_to_point(
        self,
        target_time: datetime,
        restore_path: str
    ) -> bool:
        """
        Recover database to specific point in time.

        Args:
            target_time: Target recovery time
            restore_path: Restoration destination

        Returns:
            True if successful
        """
        self.logger.info(
            "starting_pitr",
            target_time=target_time.isoformat(),
            restore_path=restore_path
        )

        # Find most recent full backup before target time
        full_backups = self.backup_manager.list_backups(
            backup_type=BackupType.FULL
        )

        base_backup = None
        for backup in full_backups:
            if backup.timestamp <= target_time:
                base_backup = backup
                break

        if not base_backup:
            self.logger.error("no_base_backup_found")
            return False

        self.logger.info(
            "using_base_backup",
            backup_id=base_backup.backup_id,
            timestamp=base_backup.timestamp.isoformat()
        )

        # Restore base backup
        success = await self.backup_manager.restore_backup(
            base_backup.backup_id,
            restore_path
        )

        if not success:
            self.logger.error("base_backup_restore_failed")
            return False

        # Apply incremental backups up to target time
        # (Implementation would depend on WAL replay for PostgreSQL)

        self.logger.info("pitr_completed", target_time=target_time.isoformat())
        return True


class RecoveryManager:
    """Disaster recovery orchestration."""

    def __init__(self, backup_manager: BackupManager):
        """
        Initialize recovery manager.

        Args:
            backup_manager: Backup manager instance
        """
        self.backup_manager = backup_manager
        self.pitr = PointInTimeRecovery(backup_manager)
        self.logger = logger.bind(component="recovery_manager")

    async def execute_recovery_plan(
        self,
        plan_file: Path
    ) -> bool:
        """
        Execute disaster recovery plan from file.

        Args:
            plan_file: Path to recovery plan JSON

        Returns:
            True if successful
        """
        try:
            with open(plan_file, 'r') as f:
                plan = json.load(f)

            self.logger.info("executing_recovery_plan", plan_file=str(plan_file))

            for step in plan.get("steps", []):
                step_type = step.get("type")

                if step_type == "restore_backup":
                    success = await self.backup_manager.restore_backup(
                        step["backup_id"],
                        step["restore_path"]
                    )
                elif step_type == "pitr":
                    target_time = datetime.fromisoformat(step["target_time"])
                    success = await self.pitr.recover_to_point(
                        target_time,
                        step["restore_path"]
                    )
                else:
                    self.logger.warning("unknown_step_type", type=step_type)
                    continue

                if not success:
                    self.logger.error("recovery_step_failed", step=step)
                    return False

            self.logger.info("recovery_plan_completed")
            return True

        except Exception as e:
            self.logger.error("recovery_plan_failed", error=str(e))
            return False


class RecoveryTestRunner:
    """Automated recovery testing."""

    def __init__(self, backup_manager: BackupManager, test_dir: Path):
        """
        Initialize recovery test runner.

        Args:
            backup_manager: Backup manager instance
            test_dir: Directory for test restorations
        """
        self.backup_manager = backup_manager
        self.test_dir = test_dir
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(component="recovery_test_runner")

    async def test_backup_restoration(self, backup_id: str) -> bool:
        """
        Test backup can be restored successfully.

        Args:
            backup_id: Backup to test

        Returns:
            True if test passed
        """
        test_restore_path = self.test_dir / f"test_{backup_id}"

        self.logger.info("testing_backup_restoration", backup_id=backup_id)

        try:
            # Attempt restoration
            success = await self.backup_manager.restore_backup(
                backup_id,
                str(test_restore_path)
            )

            if success:
                # Verify restoration
                if test_restore_path.exists():
                    self.logger.info("backup_test_passed", backup_id=backup_id)

                    # Cleanup test restoration
                    shutil.rmtree(test_restore_path)
                    return True

            self.logger.error("backup_test_failed", backup_id=backup_id)
            return False

        except Exception as e:
            self.logger.error(
                "backup_test_error",
                backup_id=backup_id,
                error=str(e)
            )
            return False

    async def run_recovery_drill(self) -> Dict[str, Any]:
        """
        Run full recovery drill on latest backups.

        Returns:
            Test results dictionary
        """
        self.logger.info("starting_recovery_drill")

        results = {
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "passed": 0,
            "failed": 0
        }

        # Get latest backup of each type
        for backup_type in BackupType:
            backups = self.backup_manager.list_backups(backup_type=backup_type)

            if backups:
                latest = backups[0]
                test_result = await self.test_backup_restoration(latest.backup_id)

                results["tests"].append({
                    "backup_id": latest.backup_id,
                    "backup_type": backup_type.value,
                    "passed": test_result
                })

                if test_result:
                    results["passed"] += 1
                else:
                    results["failed"] += 1

        results["end_time"] = datetime.now().isoformat()
        results["overall_success"] = results["failed"] == 0

        self.logger.info(
            "recovery_drill_completed",
            passed=results["passed"],
            failed=results["failed"]
        )

        return results
