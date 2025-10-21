"""
Comprehensive tests for the Self-Modification System

Tests cover:
- Safety validation and risk assessment
- Version management and backup/restore
- Rollback capabilities
- Circuit breaker and safety controls
- End-to-end modification workflow
- Edge cases and error handling
"""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.agents.self_modification_system import (
    ModificationType,
    ModificationRisk,
    ModificationStatus,
    ModificationProposal,
    AgentVersion,
    SafetyValidator,
    VersionManager,
    RollbackManager,
    SelfModificationSystem,
)


class TestModificationProposal:
    """Test the ModificationProposal dataclass."""

    def test_proposal_initialization(self):
        """Test basic proposal initialization."""
        proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.CONFIGURATION,
            description="Update configuration",
            reason="Fix configuration issue",
            proposed_state={"setting": "new_value"},
        )

        assert proposal.agent_id == "test_agent"
        assert proposal.modification_type == ModificationType.CONFIGURATION
        assert proposal.status == ModificationStatus.PROPOSED
        assert proposal.risk_level == ModificationRisk.LOW  # Based on type mapping
        assert proposal.proposal_id.startswith("mod_")

    def test_risk_assessment_by_type(self):
        """Test risk assessment based on modification type."""
        risk_mapping = {
            ModificationType.CONFIGURATION: ModificationRisk.LOW,
            ModificationType.SECURITY: ModificationRisk.CRITICAL,
            ModificationType.MODEL: ModificationRisk.HIGH,
            ModificationType.LOGIC: ModificationRisk.MEDIUM,
        }

        for mod_type, expected_risk in risk_mapping.items():
            proposal = ModificationProposal(
                agent_id="test_agent",
                modification_type=mod_type,
                description="Test",
                reason="Test",
                proposed_state={},
            )
            assert proposal.risk_level == expected_risk

    def test_approval_management(self):
        """Test approval addition and checking."""
        proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.HIGH,
            description="Test",
            reason="Test",
            proposed_state={},
        )

        # Set required approvals
        proposal.required_approvals = ["admin", "tech_lead"]

        # Initially not approved
        assert not proposal.is_approved()

        # Add first approval
        assert proposal.add_approval("admin", "Looks good")
        assert "admin" in proposal.received_approvals
        assert not proposal.is_approved()

        # Add duplicate approval (should not be added)
        assert not proposal.add_approval("admin", "Duplicate")
        assert len(proposal.received_approvals) == 1

        # Add second approval
        assert proposal.add_approval("tech_lead", "Approved")
        assert proposal.is_approved()

        # Check approval comments
        assert proposal.approval_comments["admin"] == "Looks good"
        assert proposal.approval_comments["tech_lead"] == "Approved"

    def test_to_dict_serialization(self):
        """Test proposal serialization to dictionary."""
        proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.CONFIGURATION,
            description="Test serialization",
            reason="Testing",
            proposed_state={"key": "value"},
            tags=["test", "serialization"],
        )

        proposal_dict = proposal.to_dict()

        assert proposal_dict["agent_id"] == "test_agent"
        assert proposal_dict["modification_type"] == "configuration"
        assert proposal_dict["status"] == "proposed"
        assert proposal_dict["risk_level"] == "low"
        assert proposal_dict["tags"] == ["test", "serialization"]
        assert "timestamp" in proposal_dict


class TestSafetyValidator:
    """Test the SafetyValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a SafetyValidator instance."""
        return SafetyValidator()

    @pytest.mark.asyncio
    async def test_basic_structure_validation(self, validator):
        """Test basic proposal structure validation."""
        # Valid proposal
        valid_proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.CONFIGURATION,
            description="Valid proposal",
            reason="Testing validation",
            proposed_state={"setting": "value"},
            target_file="src/agents/test.py",
        )

        results = await validator.validate_proposal(valid_proposal)
        assert results["is_valid"] == True
        assert "Basic structure validation passed" in results["validations_passed"]

        # Invalid proposal (missing required fields)
        invalid_proposal = ModificationProposal(
            agent_id="",  # Empty agent_id
            modification_type=ModificationType.CONFIGURATION,
            description="",  # Empty description
            reason="",  # Empty reason
            proposed_state={},  # Empty proposed state
        )

        results = await validator.validate_proposal(invalid_proposal)
        assert results["is_valid"] == False
        assert "Agent ID is required" in results["validations_failed"]

    @pytest.mark.asyncio
    async def test_content_safety_validation(self, validator):
        """Test content safety validation."""
        # Safe content
        safe_proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.CONFIGURATION,
            description="Safe modification",
            reason="Testing",
            proposed_state={"safe_code": "print('hello world')"},
        )

        results = await validator.validate_proposal(safe_proposal)
        assert results["is_valid"] == True

        # Dangerous content
        dangerous_proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.LOGIC,
            description="Dangerous modification",
            reason="Testing",
            proposed_state={"code": "rm -rf / # Dangerous"},
        )

        results = await validator.validate_proposal(dangerous_proposal)
        assert results["is_valid"] == False
        assert dangerous_proposal.risk_level == ModificationRisk.PROHIBITED
        assert any("Prohibited pattern detected" in failure for failure in results["validations_failed"])

    @pytest.mark.asyncio
    async def test_secret_detection(self, validator):
        """Test detection of potential secrets in content."""
        proposal_with_secrets = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.CONFIGURATION,
            description="Config with secrets",
            reason="Testing",
            proposed_state={"api_key": "sk-1234567890abcdef", "password": "secret123"},
        )

        results = await validator.validate_proposal(proposal_with_secrets)
        # Should be valid but with warnings about potential secrets
        assert results["is_valid"] == True
        assert len(results["warnings"]) > 0
        assert any("Potential secret detected" in warning for warning in results["warnings"])

    @pytest.mark.asyncio
    async def test_risk_assessment(self, validator):
        """Test risk assessment based on modification type and content."""
        # Security modification should have high risk
        security_proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.SECURITY,
            description="Security change",
            reason="Testing",
            proposed_state={"auth_method": "oauth2"},
        )

        results = await validator.validate_proposal(security_proposal)
        assert security_proposal.risk_level == ModificationRisk.CRITICAL
        assert "tech_lead" in results["required_approvals"]
        assert "security_officer" in results["required_approvals"]

    @pytest.mark.asyncio
    async def test_approval_requirements_by_risk(self, validator):
        """Test approval requirements based on risk level."""
        test_cases = [
            (ModificationRisk.SAFE, []),
            (ModificationRisk.LOW, ["system_admin"]),
            (ModificationRisk.MEDIUM, ["system_admin", "tech_lead"]),
            (ModificationRisk.HIGH, ["system_admin", "tech_lead", "security_officer"]),
            (ModificationRisk.CRITICAL, ["system_admin", "tech_lead", "security_officer", "product_owner"]),
        ]

        for risk_level, expected_approvers in test_cases:
            proposal = ModificationProposal(
                agent_id="test_agent",
                modification_type=ModificationType.CONFIGURATION,
                description=f"Test {risk_level.value} risk",
                reason="Testing",
                proposed_state={},
            )
            proposal.risk_level = risk_level

            results = await validator.validate_proposal(proposal)
            assert set(results["required_approvals"]) == set(expected_approvers)


class TestVersionManager:
    """Test the VersionManager class."""

    @pytest.fixture
    def temp_backup_dir(self):
        """Create a temporary backup directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def version_manager(self, temp_backup_dir):
        """Create a VersionManager with temporary directory."""
        return VersionManager(backup_directory=temp_backup_dir)

    @pytest.fixture
    def sample_files(self, temp_backup_dir):
        """Create sample files for testing."""
        src_dir = Path(temp_backup_dir) / "src" / "agents"
        src_dir.mkdir(parents=True, exist_ok=True)

        test_file = src_dir / "test_agent.py"
        test_file.write_text("def test_function():\n    return 'test'")

        config_file = Path(temp_backup_dir) / "requirements.txt"
        config_file.write_text("requests==2.28.0\nfastapi==0.85.0")

        return {"test_file": test_file, "config_file": config_file}

    @pytest.mark.asyncio
    async def test_create_backup(self, version_manager, sample_files, temp_backup_dir):
        """Test creating a backup of agent state."""
        proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.CONFIGURATION,
            description="Test backup",
            reason="Testing",
            proposed_state={"config": "new_value"},
        )

        # Change working directory to temp dir for the test
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_backup_dir)

            backup_id = await version_manager.create_backup("test_agent", proposal)

            assert backup_id is not None
            assert backup_id.startswith("v_test_agent_")

            # Check backup directory was created
            backup_path = version_manager.backup_directory / backup_id
            assert backup_path.exists()
            assert backup_path.is_dir()

            # Check metadata file exists
            metadata_file = backup_path / "version_metadata.json"
            assert metadata_file.exists()

            # Check files were backed up
            backed_up_file = backup_path / "src" / "agents" / "test_agent.py"
            assert backed_up_file.exists()

            # Check version was stored
            version = version_manager.get_version(backup_id)
            assert version is not None
            assert version.agent_id == "test_agent"
            assert version.modification_proposal_id == proposal.proposal_id

        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_create_version(self, version_manager):
        """Test creating a version record."""
        proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.CONFIGURATION,
            description="Test version creation",
            reason="Testing",
            proposed_state={"config": "new_value"},
        )

        changes_made = ["Modified configuration", "Updated settings"]

        version = await version_manager.create_version("test_agent", proposal, changes_made)

        assert version is not None
        assert version.agent_id == "test_agent"
        assert version.modification_proposal_id == proposal.proposal_id
        assert version.changes_made == changes_made
        assert version.version_id.startswith("v_test_agent_")

        # Check version is stored
        retrieved_version = version_manager.get_version(version.version_id)
        assert retrieved_version == version

    def test_get_agent_versions(self, version_manager):
        """Test retrieving versions for an agent."""
        # Create some versions
        versions = []
        for i in range(3):
            proposal = ModificationProposal(
                agent_id="test_agent",
                modification_type=ModificationType.CONFIGURATION,
                description=f"Test version {i}",
                reason="Testing",
                proposed_state={"version": i},
            )
            version = AgentVersion(
                version_id=f"v_test_{i}",
                agent_id="test_agent",
                timestamp=datetime.utcnow(),
                description=f"Version {i}",
                file_hashes={},
                config_snapshot={},
                dependencies={},
                modification_proposal_id=proposal.proposal_id,
            )
            version_manager.versions[version.version_id] = version

            if "test_agent" not in version_manager.agent_versions:
                version_manager.agent_versions["test_agent"] = []
            version_manager.agent_versions["test_agent"].append(version.version_id)
            versions.append(version)

        # Test retrieval
        agent_versions = version_manager.get_agent_versions("test_agent")
        assert len(agent_versions) == 3
        assert agent_versions[0].version_id == "v_test_0"
        assert agent_versions[2].version_id == "v_test_2"

        # Test with limit
        limited_versions = version_manager.get_agent_versions("test_agent", limit=2)
        assert len(limited_versions) == 2

    def test_get_latest_version(self, version_manager):
        """Test getting the latest version for an agent."""
        # Create versions
        version_ids = ["v_old", "v_newer", "v_newest"]
        for i, version_id in enumerate(version_ids):
            version = AgentVersion(
                version_id=version_id,
                agent_id="test_agent",
                timestamp=datetime.utcnow() + timedelta(minutes=i),
                description=f"Version {i}",
                file_hashes={},
                config_snapshot={},
                dependencies={},
            )
            version_manager.versions[version_id] = version

        version_manager.agent_versions["test_agent"] = version_ids

        # Test latest version retrieval
        latest = version_manager.get_latest_version("test_agent")
        assert latest is not None
        assert latest.version_id == "v_newest"

        # Test non-existent agent
        assert version_manager.get_latest_version("non_existent") is None


class TestRollbackManager:
    """Test the RollbackManager class."""

    @pytest.fixture
    def version_manager(self):
        """Create a mock VersionManager."""
        mock_vm = Mock(spec=VersionManager)
        mock_vm.backup_directory = Path("/tmp/test_backups")
        mock_vm.versions = {}
        return mock_vm

    @pytest.fixture
    def rollback_manager(self, version_manager):
        """Create a RollbackManager."""
        return RollbackManager(version_manager)

    @pytest.mark.asyncio
    async def test_prepare_rollback_plan(self, rollback_manager):
        """Test preparing a rollback plan."""
        proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.CONFIGURATION,
            description="Test modification",
            reason="Testing",
            proposed_state={"config": "new_value"},
        )
        proposal.backup_location = "/tmp/backup"

        plan = await rollback_manager.prepare_rollback_plan(proposal)

        assert plan["strategy"] == "backup_restore"
        assert plan["agent_id"] == "test_agent"
        assert plan["proposal_id"] == proposal.proposal_id
        assert "rollback_id" in plan
        assert len(plan["steps"]) > 0
        assert len(plan["verification_steps"]) > 0
        assert plan["estimated_time"] > 0

    @pytest.mark.asyncio
    async def test_prepare_rollback_plan_no_backup(self, rollback_manager):
        """Test preparing rollback plan without backup."""
        proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.LOGIC,
            description="Test modification",
            reason="Testing",
            proposed_state={"logic": "new_code"},
        )
        # No backup location set

        plan = await rollback_manager.prepare_rollback_plan(proposal)

        assert plan["strategy"] == "git_revert"

    @pytest.mark.asyncio
    async def test_execute_rollback_success(self, rollback_manager, version_manager):
        """Test successful rollback execution."""
        # Mock version and backup
        version = AgentVersion(
            version_id="test_version",
            agent_id="test_agent",
            timestamp=datetime.utcnow(),
            description="Test version",
            file_hashes={},
            config_snapshot={},
            dependencies={},
        )
        version_manager.versions["test_version"] = version

        # Mock backup directory
        backup_path = Path("/tmp/test_backups/test_version")
        backup_path.mkdir(parents=True, exist_ok=True)

        proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.CONFIGURATION,
            description="Test modification",
            reason="Testing",
            proposed_state={"config": "new_value"},
        )
        proposal.backup_location = str(backup_path)

        # Mock successful restore
        rollback_manager.version_manager.restore_version = AsyncMock(return_value=True)

        success = await rollback_manager.execute_rollback(proposal)

        assert success is True
        assert len(rollback_manager.rollback_history) == 1
        assert rollback_manager.rollback_history[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_rollback_failure(self, rollback_manager, version_manager):
        """Test rollback execution failure."""
        proposal = ModificationProposal(
            agent_id="test_agent",
            modification_type=ModificationType.CONFIGURATION,
            description="Test modification",
            reason="Testing",
            proposed_state={"config": "new_value"},
        )

        # Mock failed restore
        rollback_manager.version_manager.restore_version = AsyncMock(return_value=False)

        success = await rollback_manager.execute_rollback(proposal)

        assert success is False
        assert len(rollback_manager.rollback_history) == 1
        assert rollback_manager.rollback_history[0]["status"] == "failed"


class TestSelfModificationSystem:
    """Test the main SelfModificationSystem class."""

    @pytest.fixture
    def temp_backup_dir(self):
        """Create a temporary backup directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def modification_system(self, temp_backup_dir):
        """Create a SelfModificationSystem instance."""
        return SelfModificationSystem(backup_directory=temp_backup_dir)

    @pytest.mark.asyncio
    async def test_propose_modification(self, modification_system):
        """Test proposing a modification."""
        proposal_data = {
            "agent_id": "test_agent",
            "modification_type": "configuration",
            "description": "Test proposal",
            "reason": "Testing the system",
            "target_file": "src/agents/test_agent.py",
            "proposed_state": {"config_value": "new_value"},
            "priority": "medium",
            "tags": ["test"],
        }

        proposal = await modification_system.propose_modification(proposal_data)

        assert proposal is not None
        assert proposal.agent_id == "test_agent"
        assert proposal.modification_type == ModificationType.CONFIGURATION
        assert proposal.description == "Test proposal"
        assert proposal.proposal_id in modification_system.active_proposals
        assert modification_system.metrics["total_proposals"] == 1

    @pytest.mark.asyncio
    async def test_validate_proposal_success(self, modification_system):
        """Test successful proposal validation."""
        # Create a proposal first
        proposal_data = {
            "agent_id": "test_agent",
            "modification_type": "configuration",
            "description": "Safe configuration change",
            "reason": "Update configuration value",
            "target_file": "src/agents/test_config.py",
            "proposed_state": {"setting": "new_value"},
        }

        proposal = await modification_system.propose_modification(proposal_data)

        # Validate the proposal
        results = await modification_system.validate_proposal(proposal.proposal_id)

        assert results["is_valid"] == True
        assert proposal.status == ModificationStatus.APPROVED  # Low risk proposals are auto-approved
        assert modification_system.metrics["approved_proposals"] == 1

    @pytest.mark.asyncio
    async def test_validate_proposal_rejection(self, modification_system):
        """Test proposal rejection due to safety issues."""
        # Create a dangerous proposal
        proposal_data = {
            "agent_id": "test_agent",
            "modification_type": "logic",
            "description": "Dangerous modification",
            "reason": "Testing rejection",
            "target_file": "src/agents/test_agent.py",
            "proposed_state": {"code": "rm -rf / # Dangerous command"},
        }

        proposal = await modification_system.propose_modification(proposal_data)

        # Validate the proposal
        results = await modification_system.validate_proposal(proposal.proposal_id)

        assert results["is_valid"] == False
        assert proposal.status == ModificationStatus.REJECTED
        assert proposal.risk_level == ModificationRisk.PROHIBITED

    @pytest.mark.asyncio
    async def test_implement_modification_success(self, modification_system, temp_backup_dir):
        """Test successful modification implementation."""
        # Change to temp directory
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_backup_dir)

            # Create source directory and file
            src_dir = Path(temp_backup_dir) / "src" / "agents"
            src_dir.mkdir(parents=True, exist_ok=True)

            test_file = src_dir / "test_agent.py"
            test_file.write_text("# Original content\noriginal_value = True\n")

            # Create and approve proposal
            proposal_data = {
                "agent_id": "test_agent",
                "modification_type": "configuration",
                "description": "Update configuration",
                "reason": "Testing implementation",
                "target_file": "src/agents/test_agent.py",
                "proposed_state": "# Updated content\noriginal_value = False\nnew_value = True\n",
            }

            proposal = await modification_system.propose_modification(proposal_data)
            await modification_system.validate_proposal(proposal.proposal_id)

            # Ensure proposal is approved
            proposal.required_approvals = []
            proposal.received_approvals = []

            # Implement the modification
            with patch('pathlib.Path.exists', return_value=True):
                result = await modification_system.implement_modification(proposal.proposal_id)

            assert result["success"] == True
            assert "version_id" in result
            assert "changes_made" in result
            assert len(result["changes_made"]) > 0
            assert proposal.status == ModificationStatus.COMPLETED
            assert modification_system.metrics["implemented_proposals"] == 1

        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_safety_controls_circuit_breaker(self, modification_system):
        """Test circuit breaker safety control."""
        # Set circuit breaker to triggered state
        modification_system.circuit_breaker_failures = 5
        modification_system.circuit_breaker_reset_time = datetime.utcnow() + timedelta(minutes=5)

        proposal_data = {
            "agent_id": "test_agent",
            "modification_type": "configuration",
            "description": "Test circuit breaker",
            "reason": "Testing",
            "proposed_state": {"config": "value"},
        }

        proposal = await modification_system.propose_modification(proposal_data)
        results = await modification_system.validate_proposal(proposal.proposal_id)

        assert results["is_valid"] == False
        assert "circuit_breaker_active" in results
        assert results["circuit_breaker_active"] == True

    @pytest.mark.asyncio
    async def test_manual_rollback(self, modification_system):
        """Test manual rollback of a modification."""
        proposal_data = {
            "agent_id": "test_agent",
            "modification_type": "configuration",
            "description": "Test rollback",
            "reason": "Testing rollback functionality",
            "proposed_state": {"config": "value"},
        }

        proposal = await modification_system.propose_modification(proposal_data)

        # Mock successful rollback
        modification_system.rollback_manager.execute_rollback = AsyncMock(return_value=True)

        success = await modification_system.rollback_modification(proposal.proposal_id)

        assert success is True
        assert proposal.status == ModificationStatus.ROLLED_BACK
        assert modification_system.metrics["rolled_back_proposals"] == 1

    def test_get_metrics(self, modification_system):
        """Test getting system metrics."""
        metrics = modification_system.get_metrics()

        assert "total_proposals" in metrics
        assert "approved_proposals" in metrics
        assert "implemented_proposals" in metrics
        assert "failed_proposals" in metrics
        assert "rolled_back_proposals" in metrics
        assert "active_proposals" in metrics
        assert "circuit_breaker_failures" in metrics
        assert "total_versions" in metrics

    @pytest.mark.asyncio
    async def test_health_check(self, modification_system):
        """Test system health check."""
        health = await modification_system.health_check()

        assert "status" in health
        assert "checks" in health
        assert "issues" in health
        assert "timestamp" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, modification_system, temp_backup_dir):
        """Test complete end-to-end workflow."""
        # Change to temp directory
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_backup_dir)

            # Setup source structure
            src_dir = Path(temp_backup_dir) / "src" / "agents"
            src_dir.mkdir(parents=True, exist_ok=True)

            # 1. Propose modification
            proposal_data = {
                "agent_id": "test_agent",
                "modification_type": "configuration",
                "description": "End-to-end test modification",
                "reason": "Testing complete workflow",
                "target_file": "src/agents/test_config.py",
                "proposed_state": {"test_setting": "updated_value"},
            }

            proposal = await modification_system.propose_modification(proposal_data)
            proposal_id = proposal.proposal_id

            # 2. Validate proposal
            validation_results = await modification_system.validate_proposal(proposal_id)
            assert validation_results["is_valid"] == True

            # 3. Implement modification
            with patch('pathlib.Path.exists', return_value=True):
                implementation_result = await modification_system.implement_modification(proposal_id)
            assert implementation_result["success"] == True

            # 4. Verify metrics updated
            metrics = modification_system.get_metrics()
            assert metrics["total_proposals"] == 1
            assert metrics["approved_proposals"] == 1
            assert metrics["implemented_proposals"] == 1

            # 5. Check health
            health = await modification_system.health_check()
            assert health["status"] == "healthy"

        finally:
            os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_concurrent_modifications_limit(self, modification_system):
        """Test concurrent modification limit."""
        # Create multiple implementing proposals
        proposals = []
        for i in range(5):
            proposal_data = {
                "agent_id": f"test_agent_{i}",
                "modification_type": "configuration",
                description=f"Test {i}",
                reason="Testing concurrent limit",
                proposed_state={"config": f"value_{i}"},
            }

            proposal = await modification_system.propose_modification(proposal_data)
            proposal.status = ModificationStatus.IMPLEMENTING
            proposals.append(proposal)

        # Try to validate another proposal (should be blocked)
        new_proposal_data = {
            "agent_id": "blocked_agent",
            "modification_type": "configuration",
            description="Should be blocked",
            reason="Testing limit",
            proposed_state={"config": "blocked"},
        }

        new_proposal = await modification_system.propose_modification(new_proposal_data)
        results = await modification_system.validate_proposal(new_proposal.proposal_id)

        assert results["is_valid"] == False

    def test_proposal_serialization_roundtrip(self):
        """Test proposal serialization and deserialization."""
        original_data = {
            "agent_id": "test_agent",
            "modification_type": "configuration",
            "description": "Test serialization",
            "reason": "Testing roundtrip",
            "target_file": "src/agents/test.py",
            "proposed_state": {"key": "value"},
            "priority": "high",
            "tags": ["test", "serialization"],
        }

        proposal = ModificationProposal(
            agent_id=original_data["agent_id"],
            modification_type=ModificationType(original_data["modification_type"]),
            description=original_data["description"],
            reason=original_data["reason"],
            target_file=original_data["target_file"],
            proposed_state=original_data["proposed_state"],
            priority=original_data["priority"],
            tags=original_data["tags"],
        )

        # Serialize to dict
        proposal_dict = proposal.to_dict()

        # Verify all fields are present
        for key, value in original_data.items():
            assert key in proposal_dict
            if key == "modification_type":
                assert proposal_dict[key] == value
            else:
                assert proposal_dict[key] == value

        # Verify additional fields
        assert "proposal_id" in proposal_dict
        assert "timestamp" in proposal_dict
        assert "status" in proposal_dict
        assert "risk_level" in proposal_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])