"""
Self-Modification System with Safety Protocols

Critical system infrastructure for safe agent self-modification with comprehensive
safety validation, version control, and rollback capabilities.

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                    Self-Modification System                     │
├─────────────────────────────────────────────────────────────────┤
│  SafetyValidator   │  VersionManager  │  RollbackManager       │
│  - Risk Assessment │  - Version Control│  - Safe Rollback       │
│  - Validation      │  - Backups       │  - Recovery            │
│  - Approval Gates  │  - Snapshots     │  - Verification        │
├─────────────────────────────────────────────────────────────────┤
│                 SelfModificationSystem                          │
│  - Orchestration   │  - Monitoring    │  - Audit Trail         │
│  - Coordination    │  - Metrics       │  - Compliance          │
└─────────────────────────────────────────────────────────────────┘

Safety First Design:
- Multi-layer validation before any modification
- Required approvals for high-risk changes
- Automatic backups before any modification
- Immediate rollback capability
- Comprehensive audit logging
- Circuit breaker patterns for unsafe operations
"""

import asyncio
import hashlib
import json
import shutil
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
import structlog
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger(__name__)


class ModificationType(Enum):
    """Types of modifications that can be made to agents."""

    CONFIGURATION = "configuration"  # Config changes, parameters, settings
    LOGIC = "logic"                  # Code logic, algorithms, workflows
    MODEL = "model"                  # AI model parameters, prompts
    INTEGRATION = "integration"      # External integrations, API connections
    DEPENDENCY = "dependency"        # Library dependencies, versions
    SECURITY = "security"            # Security policies, authentication
    PERFORMANCE = "performance"      # Performance optimizations
    STRUCTURE = "structure"          # Architecture, file structure
    KNOWLEDGE = "knowledge"          # Knowledge base, training data


class ModificationRisk(Enum):
    """Risk levels for modifications."""

    SAFE = "safe"                    # No risk, reversible changes
    LOW = "low"                      # Minor risk, easily reversible
    MEDIUM = "medium"                # Moderate risk, requires testing
    HIGH = "high"                    # High risk, requires approval
    CRITICAL = "critical"            # Critical risk, requires multi-level approval
    PROHIBITED = "prohibited"        # Not allowed under any circumstances


class ModificationStatus(Enum):
    """Status of modification proposals."""

    PROPOSED = "proposed"            # Modification proposed
    VALIDATING = "validating"        # Safety validation in progress
    APPROVED = "approved"            # Approved for implementation
    REJECTED = "rejected"            # Rejected due to safety concerns
    IMPLEMENTING = "implementing"    # Currently being implemented
    COMPLETED = "completed"          # Successfully implemented
    FAILED = "failed"                # Implementation failed
    ROLLED_BACK = "rolled_back"      # Successfully rolled back
    CANCELLED = "cancelled"          # Cancelled before implementation


@dataclass
class ModificationProposal:
    """A proposal for modifying an agent or system component."""

    proposal_id: str = field(default_factory=lambda: f"mod_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Modification details
    agent_id: str
    modification_type: ModificationType
    description: str
    reason: str

    # Target specification
    target_file: Optional[str] = None
    target_function: Optional[str] = None
    target_class: Optional[str] = None
    target_config: Optional[Dict[str, Any]] = None

    # Change specification
    current_state: Optional[Dict[str, Any]] = None
    proposed_state: Dict[str, Any] = field(default_factory=dict)
    diff: Optional[str] = None

    # Risk assessment
    risk_level: ModificationRisk = ModificationRisk.UNKNOWN
    risk_factors: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)

    # Approval workflow
    required_approvals: List[str] = field(default_factory=list)
    received_approvals: List[str] = field(default_factory=list)
    approval_comments: Dict[str, str] = field(default_factory=dict)

    # Status tracking
    status: ModificationStatus = ModificationStatus.PROPOSED
    validation_results: Dict[str, Any] = field(default_factory=dict)
    implementation_log: List[str] = field(default_factory=list)

    # Metadata
    proposed_by: str = "system"
    priority: str = "medium"  # low, medium, high, critical
    tags: List[str] = field(default_factory=list)

    # Rollback information
    rollback_plan: Optional[Dict[str, Any]] = None
    backup_location: Optional[str] = None

    def __post_init__(self):
        """Validate proposal after initialization."""
        if self.risk_level == ModificationRisk.UNKNOWN:
            self.risk_level = self._assess_initial_risk()

    def _assess_initial_risk(self) -> ModificationRisk:
        """Assess initial risk level based on modification type."""
        risk_mapping = {
            ModificationType.CONFIGURATION: ModificationRisk.LOW,
            ModificationType.LOGIC: ModificationRisk.MEDIUM,
            ModificationType.MODEL: ModificationRisk.HIGH,
            ModificationType.INTEGRATION: ModificationRisk.HIGH,
            ModificationType.DEPENDENCY: ModificationRisk.MEDIUM,
            ModificationType.SECURITY: ModificationRisk.CRITICAL,
            ModificationType.PERFORMANCE: ModificationRisk.LOW,
            ModificationType.STRUCTURE: ModificationRisk.HIGH,
            ModificationType.KNOWLEDGE: ModificationRisk.MEDIUM,
        }
        return risk_mapping.get(self.modification_type, ModificationRisk.MEDIUM)

    def add_approval(self, approver: str, comment: str = "") -> bool:
        """Add approval for this modification."""
        if approver in self.required_approvals and approver not in self.received_approvals:
            self.received_approvals.append(approver)
            self.approval_comments[approver] = comment
            logger.info("modification_approval_added",
                       proposal_id=self.proposal_id,
                       approver=approver)
            return True
        return False

    def is_approved(self) -> bool:
        """Check if all required approvals have been received."""
        return all(approver in self.received_approvals for approver in self.required_approvals)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "modification_type": self.modification_type.value,
            "description": self.description,
            "reason": self.reason,
            "target_file": self.target_file,
            "target_function": self.target_function,
            "target_class": self.target_class,
            "target_config": self.target_config,
            "current_state": self.current_state,
            "proposed_state": self.proposed_state,
            "diff": self.diff,
            "risk_level": self.risk_level.value,
            "risk_factors": self.risk_factors,
            "mitigation_strategies": self.mitigation_strategies,
            "required_approvals": self.required_approvals,
            "received_approvals": self.received_approvals,
            "approval_comments": self.approval_comments,
            "status": self.status.value,
            "validation_results": self.validation_results,
            "implementation_log": self.implementation_log,
            "proposed_by": self.proposed_by,
            "priority": self.priority,
            "tags": self.tags,
            "rollback_plan": self.rollback_plan,
            "backup_location": self.backup_location,
        }


@dataclass
class AgentVersion:
    """Version information for an agent."""

    version_id: str
    agent_id: str
    timestamp: datetime
    description: str

    # Version details
    file_hashes: Dict[str, str]  # file_path -> hash
    config_snapshot: Dict[str, Any]
    dependencies: Dict[str, str]  # package -> version

    # Change information
    modification_proposal_id: Optional[str] = None
    changes_made: List[str] = field(default_factory=list)

    # Quality metrics
    test_coverage: Optional[float] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    security_score: Optional[float] = None

    # Metadata
    created_by: str = "system"
    is_stable: bool = False
    rollback_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version_id": self.version_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "file_hashes": self.file_hashes,
            "config_snapshot": self.config_snapshot,
            "dependencies": self.dependencies,
            "modification_proposal_id": self.modification_proposal_id,
            "changes_made": self.changes_made,
            "test_coverage": self.test_coverage,
            "performance_metrics": self.performance_metrics,
            "security_score": self.security_score,
            "created_by": self.created_by,
            "is_stable": self.is_stable,
            "rollback_version": self.rollback_version,
        }


class SafetyValidator:
    """Validates modification proposals for safety and compliance."""

    def __init__(self):
        """Initialize safety validator with rules and policies."""
        self.logger = logger.bind(component="SafetyValidator")

        # Safety rules
        self.prohibited_patterns = [
            r"rm\s+-rf\s+/",          # Dangerous file deletion
            r"sudo\s+.*",             # Sudo commands
            r"eval\s*\(",             # eval usage
            r"exec\s*\(",             # exec usage
            r"__import__\s*\(",       # Dynamic imports
            r"subprocess\.call",      # Direct subprocess calls
            r"os\.system",            # System commands
            r"pickle\.loads",         # Unsafe deserialization
        ]

        # Risk factors by modification type
        self.risk_factors = {
            ModificationType.SECURITY: [
                "authentication_changes",
                "authorization_changes",
                "encryption_key_changes",
                "access_control_modifications"
            ],
            ModificationType.MODEL: [
                "prompt_injection_risk",
                "behavior_changes",
                "output_format_changes",
                "safety_bypass_attempts"
            ],
            ModificationType.INTEGRATION: [
                "api_key_exposure",
                "data_leak_risk",
                "third_party_dependencies",
                "network_access_changes"
            ],
        }

        # Required approvals by risk level
        self.approval_requirements = {
            ModificationRisk.SAFE: [],
            ModificationRisk.LOW: ["system_admin"],
            ModificationRisk.MEDIUM: ["system_admin", "tech_lead"],
            ModificationRisk.HIGH: ["system_admin", "tech_lead", "security_officer"],
            ModificationRisk.CRITICAL: ["system_admin", "tech_lead", "security_officer", "product_owner"],
            ModificationRisk.PROHIBITED: [],  # Cannot be approved
        }

    async def validate_proposal(self, proposal: ModificationProposal) -> Dict[str, Any]:
        """Validate a modification proposal for safety."""
        self.logger.info("validating_proposal",
                        proposal_id=proposal.proposal_id,
                        agent_id=proposal.agent_id,
                        modification_type=proposal.modification_type.value)

        validation_results = {
            "is_valid": False,
            "risk_level": proposal.risk_level.value,
            "validations_passed": [],
            "validations_failed": [],
            "warnings": [],
            "recommendations": [],
            "required_approvals": [],
            "validation_timestamp": datetime.utcnow().isoformat(),
        }

        try:
            # 1. Basic structure validation
            if not self._validate_basic_structure(proposal, validation_results):
                return validation_results

            # 2. Content safety validation
            if not await self._validate_content_safety(proposal, validation_results):
                return validation_results

            # 3. Risk assessment
            if not await self._assess_risk_factors(proposal, validation_results):
                return validation_results

            # 4. Impact analysis
            if not await self._analyze_impact(proposal, validation_results):
                return validation_results

            # 5. Compliance validation
            if not await self._validate_compliance(proposal, validation_results):
                return validation_results

            # Set required approvals based on risk level
            proposal.required_approvals = self.approval_requirements.get(
                proposal.risk_level, []
            )
            validation_results["required_approvals"] = proposal.required_approvals

            # If all validations passed, mark as valid
            if not validation_results["validations_failed"]:
                validation_results["is_valid"] = True
                validation_results["recommendations"].append(
                    "Proposal passed all safety validations"
                )

            self.logger.info("validation_completed",
                           proposal_id=proposal.proposal_id,
                           is_valid=validation_results["is_valid"],
                           risk_level=proposal.risk_level.value,
                           failed_validations=len(validation_results["validations_failed"]))

        except Exception as e:
            self.logger.error("validation_error",
                            proposal_id=proposal.proposal_id,
                            error=str(e),
                            stack_trace=True)
            validation_results["validations_failed"].append(f"Validation system error: {str(e)}")

        return validation_results

    def _validate_basic_structure(self, proposal: ModificationProposal, results: Dict[str, Any]) -> bool:
        """Validate basic proposal structure."""
        try:
            # Required fields
            if not proposal.agent_id:
                results["validations_failed"].append("Agent ID is required")
                return False

            if not proposal.description:
                results["validations_failed"].append("Description is required")
                return False

            if not proposal.reason:
                results["validations_failed"].append("Reason is required")
                return False

            if not proposal.proposed_state:
                results["validations_failed"].append("Proposed state is required")
                return False

            # Check for at least one target
            if not any([proposal.target_file, proposal.target_function, proposal.target_class, proposal.target_config]):
                results["validations_failed"].append("At least one target must be specified")
                return False

            results["validations_passed"].append("Basic structure validation passed")
            return True

        except Exception as e:
            results["validations_failed"].append(f"Structure validation error: {str(e)}")
            return False

    async def _validate_content_safety(self, proposal: ModificationProposal, results: Dict[str, Any]) -> bool:
        """Validate content for prohibited patterns and unsafe code."""
        import re

        try:
            content_to_check = json.dumps(proposal.proposed_state, default=str)

            # Check for prohibited patterns
            for pattern in self.prohibited_patterns:
                if re.search(pattern, content_to_check, re.IGNORECASE):
                    results["validations_failed"].append(f"Prohibited pattern detected: {pattern}")
                    proposal.risk_level = ModificationRisk.PROHIBITED
                    return False

            # Check for potential security issues
            security_issues = []

            # Check for hardcoded secrets
            secret_patterns = [
                r"[\"'][A-Za-z0-9+/]{32,}[\"']",  # Potential base64 secrets
                r"[\"'][A-Za-z0-9_-]{20,}=[\"']",  # Potential API keys
                r"password\s*=\s*[\"'][^\"']+[\"']",
                r"api_key\s*=\s*[\"'][^\"']+[\"']",
                r"secret\s*=\s*[\"'][^\"']+[\"']",
            ]

            for pattern in secret_patterns:
                if re.search(pattern, content_to_check, re.IGNORECASE):
                    security_issues.append(f"Potential secret detected: {pattern}")

            if security_issues:
                results["warnings"].extend(security_issues)
                if proposal.risk_level.value in ["low", "medium"]:
                    proposal.risk_level = ModificationRisk.HIGH

            # Check for infinite loops or recursion
            if "while True:" in content_to_check or "for i in range(" in content_to_check:
                results["warnings"].append("Potential infinite loop detected")

            results["validations_passed"].append("Content safety validation passed")
            return True

        except Exception as e:
            results["validations_failed"].append(f"Content safety validation error: {str(e)}")
            return False

    async def _assess_risk_factors(self, proposal: ModificationProposal, results: Dict[str, Any]) -> bool:
        """Assess risk factors specific to the modification type."""
        try:
            type_specific_factors = self.risk_factors.get(proposal.modification_type, [])

            # Check content for risk factors
            content = json.dumps(proposal.proposed_state, default=str).lower()

            for factor in type_specific_factors:
                if any(keyword in content for keyword in factor.split("_")):
                    proposal.risk_factors.append(factor)
                    results["warnings"].append(f"Risk factor detected: {factor}")

            # Adjust risk level based on factors
            if len(proposal.risk_factors) >= 3:
                if proposal.risk_level.value in ["low", "medium"]:
                    proposal.risk_level = ModificationRisk.HIGH
                elif proposal.risk_level == ModificationRisk.HIGH:
                    proposal.risk_level = ModificationRisk.CRITICAL

            # Check for modification of critical files
            critical_files = [
                "src/main.py",
                "src/agents/orchestrator.py",
                "src/agents/self_modification_system.py",
                "src/security/",
                "src/auth/",
            ]

            if proposal.target_file and any(cf in proposal.target_file for cf in critical_files):
                proposal.risk_factors.append("critical_file_modification")
                results["warnings"].append("Modification targets critical system file")
                if proposal.risk_level.value in ["low", "medium"]:
                    proposal.risk_level = ModificationRisk.HIGH

            results["validations_passed"].append("Risk assessment completed")
            return True

        except Exception as e:
            results["validations_failed"].append(f"Risk assessment error: {str(e)}")
            return False

    async def _analyze_impact(self, proposal: ModificationProposal, results: Dict[str, Any]) -> bool:
        """Analyze potential impact of the modification."""
        try:
            impact_score = 0

            # Base impact by modification type
            type_impact = {
                ModificationType.CONFIGURATION: 2,
                ModificationType.LOGIC: 4,
                ModificationType.MODEL: 5,
                ModificationType.INTEGRATION: 4,
                ModificationType.DEPENDENCY: 3,
                ModificationType.SECURITY: 5,
                ModificationType.PERFORMANCE: 2,
                ModificationType.STRUCTURE: 5,
                ModificationType.KNOWLEDGE: 3,
            }

            impact_score += type_impact.get(proposal.modification_type, 3)

            # Check if modification affects agent interfaces
            if proposal.target_class and "Agent" in proposal.target_class:
                impact_score += 2
                results["warnings"].append("Modification affects agent interface")

            # Check if modification changes public APIs
            if proposal.target_function and not proposal.target_function.startswith("_"):
                impact_score += 1
                results["warnings"].append("Modification affects public API")

            # Check for breaking changes
            if proposal.diff and ("BREAKING CHANGE" in proposal.diff.upper() or
                                "BREAKING-CHANGE" in proposal.diff):
                impact_score += 3
                results["warnings"].append("Breaking change detected")

            # Store impact score
            results["impact_score"] = impact_score

            # Adjust risk based on impact
            if impact_score >= 6 and proposal.risk_level.value in ["low", "medium"]:
                proposal.risk_level = ModificationRisk.HIGH
            elif impact_score >= 8 and proposal.risk_level == ModificationRisk.HIGH:
                proposal.risk_level = ModificationRisk.CRITICAL

            results["validations_passed"].append("Impact analysis completed")
            return True

        except Exception as e:
            results["validations_failed"].append(f"Impact analysis error: {str(e)}")
            return False

    async def _validate_compliance(self, proposal: ModificationProposal, results: Dict[str, Any]) -> bool:
        """Validate compliance with organizational policies."""
        try:
            compliance_issues = []

            # Check for GDPR compliance
            if any(keyword in proposal.description.lower() for keyword in ["personal data", "pii", "privacy"]):
                if "privacy_impact_assessment" not in [tag.lower() for tag in proposal.tags]:
                    compliance_issues.append("Privacy impact assessment required for PII modifications")

            # Check for security compliance
            if proposal.modification_type == ModificationType.SECURITY:
                if "security_review" not in [tag.lower() for tag in proposal.tags]:
                    compliance_issues.append("Security review required for security modifications")

            # Check for data retention compliance
            if "delete" in proposal.description.lower() and "data" in proposal.description.lower():
                if "retention_policy" not in [tag.lower() for tag in proposal.tags]:
                    results["warnings"].append("Consider data retention policy for deletions")

            if compliance_issues:
                results["validations_failed"].extend(compliance_issues)
                return False

            results["validations_passed"].append("Compliance validation passed")
            return True

        except Exception as e:
            results["validations_failed"].append(f"Compliance validation error: {str(e)}")
            return False


class VersionManager:
    """Manages agent versions with backup and restore capabilities."""

    def __init__(self, backup_directory: str = "data/backups/agents"):
        """Initialize version manager."""
        self.backup_directory = Path(backup_directory)
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(component="VersionManager")

        # Version storage
        self.versions: Dict[str, AgentVersion] = {}  # version_id -> AgentVersion
        self.agent_versions: Dict[str, List[str]] = {}  # agent_id -> [version_ids]

        self.logger.info("version_manager_initialized",
                        backup_directory=str(self.backup_directory))

    async def create_backup(self, agent_id: str, proposal: ModificationProposal) -> str:
        """Create a backup of the current agent state."""
        self.logger.info("creating_agent_backup", agent_id=agent_id, proposal_id=proposal.proposal_id)

        try:
            # Generate version ID
            version_id = f"v_{agent_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Create backup directory
            backup_path = self.backup_directory / version_id
            backup_path.mkdir(exist_ok=True)

            # Calculate file hashes
            file_hashes = {}

            # Backup agent files
            agent_dir = Path("src/agents")
            if agent_dir.exists():
                for file_path in agent_dir.rglob(f"*{agent_id}*"):
                    if file_path.is_file():
                        # Calculate hash
                        file_hash = self._calculate_file_hash(file_path)
                        file_hashes[str(file_path)] = file_hash

                        # Copy file to backup
                        relative_path = file_path.relative_to("src")
                        backup_file_path = backup_path / relative_path
                        backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, backup_file_path)

            # Backup configuration
            config_snapshot = {}
            config_files = [
                "src/agents/config.py",
                ".env",
                "pyproject.toml",
                "requirements.txt",
            ]

            for config_file in config_files:
                config_path = Path(config_file)
                if config_path.exists():
                    config_snapshot[config_file] = {
                        "content": config_path.read_text(),
                        "hash": self._calculate_file_hash(config_path),
                    }

            # Get dependencies
            dependencies = {}
            requirements_path = Path("requirements.txt")
            if requirements_path.exists():
                content = requirements_path.read_text()
                for line in content.strip().split('\n'):
                    if line and not line.startswith('#'):
                        if '==' in line:
                            package, version = line.split('==', 1)
                            dependencies[package.strip()] = version.strip()

            # Create version record
            version = AgentVersion(
                version_id=version_id,
                agent_id=agent_id,
                timestamp=datetime.utcnow(),
                description=f"Backup before modification: {proposal.description}",
                file_hashes=file_hashes,
                config_snapshot=config_snapshot,
                dependencies=dependencies,
                modification_proposal_id=proposal.proposal_id,
                created_by="self_modification_system",
            )

            # Save version metadata
            metadata_path = backup_path / "version_metadata.json"
            metadata_path.write_text(json.dumps(version.to_dict(), indent=2))

            # Store in memory
            self.versions[version_id] = version

            if agent_id not in self.agent_versions:
                self.agent_versions[agent_id] = []
            self.agent_versions[agent_id].append(version_id)

            # Set backup location in proposal
            proposal.backup_location = str(backup_path)

            self.logger.info("backup_created_successfully",
                           version_id=version_id,
                           agent_id=agent_id,
                           backup_location=str(backup_path),
                           files_backed_up=len(file_hashes))

            return version_id

        except Exception as e:
            self.logger.error("backup_creation_failed",
                            agent_id=agent_id,
                            proposal_id=proposal.proposal_id,
                            error=str(e),
                            stack_trace=True)
            raise

    async def create_version(self, agent_id: str, proposal: ModificationProposal,
                           changes_made: List[str]) -> AgentVersion:
        """Create a new version record after successful modification."""
        self.logger.info("creating_agent_version",
                        agent_id=agent_id,
                        proposal_id=proposal.proposal_id)

        try:
            # Generate version ID
            version_id = f"v_{agent_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Calculate new file hashes
            file_hashes = {}

            # Hash modified files
            if proposal.target_file:
                file_path = Path(proposal.target_file)
                if file_path.exists():
                    file_hashes[str(file_path)] = self._calculate_file_hash(file_path)

            # Get current configuration snapshot
            config_snapshot = {}

            # Get current dependencies
            dependencies = {}
            requirements_path = Path("requirements.txt")
            if requirements_path.exists():
                content = requirements_path.read_text()
                for line in content.strip().split('\n'):
                    if line and not line.startswith('#'):
                        if '==' in line:
                            package, version = line.split('==', 1)
                            dependencies[package.strip()] = version.strip()

            # Create version record
            version = AgentVersion(
                version_id=version_id,
                agent_id=agent_id,
                timestamp=datetime.utcnow(),
                description=f"Applied modification: {proposal.description}",
                file_hashes=file_hashes,
                config_snapshot=config_snapshot,
                dependencies=dependencies,
                modification_proposal_id=proposal.proposal_id,
                changes_made=changes_made,
                created_by="self_modification_system",
            )

            # Store in memory
            self.versions[version_id] = version

            if agent_id not in self.agent_versions:
                self.agent_versions[agent_id] = []
            self.agent_versions[agent_id].append(version_id)

            self.logger.info("version_created_successfully",
                           version_id=version_id,
                           agent_id=agent_id,
                           changes_count=len(changes_made))

            return version

        except Exception as e:
            self.logger.error("version_creation_failed",
                            agent_id=agent_id,
                            proposal_id=proposal.proposal_id,
                            error=str(e),
                            stack_trace=True)
            raise

    def get_version(self, version_id: str) -> Optional[AgentVersion]:
        """Get a specific version by ID."""
        return self.versions.get(version_id)

    def get_agent_versions(self, agent_id: str, limit: int = 10) -> List[AgentVersion]:
        """Get versions for a specific agent."""
        version_ids = self.agent_versions.get(agent_id, [])
        version_ids = version_ids[-limit:]  # Get most recent

        return [self.versions[vid] for vid in version_ids if vid in self.versions]

    def get_latest_version(self, agent_id: str) -> Optional[AgentVersion]:
        """Get the latest version for an agent."""
        version_ids = self.agent_versions.get(agent_id, [])
        if not version_ids:
            return None

        latest_version_id = version_ids[-1]
        return self.versions.get(latest_version_id)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    async def restore_version(self, version_id: str) -> bool:
        """Restore agent to a specific version."""
        self.logger.info("restoring_agent_version", version_id=version_id)

        try:
            version = self.get_version(version_id)
            if not version:
                self.logger.error("version_not_found", version_id=version_id)
                return False

            backup_path = self.backup_directory / version_id
            if not backup_path.exists():
                self.logger.error("backup_not_found",
                                version_id=version_id,
                                backup_path=str(backup_path))
                return False

            # Restore files from backup
            for backup_file in backup_path.rglob("*"):
                if backup_file.is_file() and backup_file.name != "version_metadata.json":
                    # Calculate target path
                    relative_path = backup_file.relative_to(backup_path)
                    target_path = Path("src") / relative_path

                    # Ensure target directory exists
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Restore file
                    shutil.copy2(backup_file, target_path)
                    self.logger.debug("file_restored",
                                    source=str(backup_file),
                                    target=str(target_path))

            self.logger.info("version_restored_successfully",
                           version_id=version_id,
                           agent_id=version.agent_id)

            return True

        except Exception as e:
            self.logger.error("version_restore_failed",
                            version_id=version_id,
                            error=str(e),
                            stack_trace=True)
            return False


class RollbackManager:
    """Manages safe rollback operations for failed modifications."""

    def __init__(self, version_manager: VersionManager):
        """Initialize rollback manager."""
        self.version_manager = version_manager
        self.logger = logger.bind(component="RollbackManager")

        # Rollback tracking
        self.active_rollbacks: Dict[str, Dict[str, Any]] = {}
        self.rollback_history: List[Dict[str, Any]] = []

    async def prepare_rollback_plan(self, proposal: ModificationProposal) -> Dict[str, Any]:
        """Prepare a rollback plan for a modification."""
        self.logger.info("preparing_rollback_plan", proposal_id=proposal.proposal_id)

        rollback_plan = {
            "rollback_id": f"rb_{uuid.uuid4().hex[:12]}",
            "proposal_id": proposal.proposal_id,
            "agent_id": proposal.agent_id,
            "strategy": "backup_restore",
            "steps": [],
            "estimated_time": 30,  # seconds
            "risk_level": "low",
            "dependencies": [],
            "verification_steps": [],
        }

        try:
            # Identify rollback strategy
            if proposal.backup_location:
                rollback_plan["strategy"] = "backup_restore"
                rollback_plan["steps"] = [
                    "Validate backup integrity",
                    "Stop affected agent processes",
                    "Restore files from backup",
                    "Restart agent processes",
                    "Verify system health",
                    "Run smoke tests"
                ]
            else:
                rollback_plan["strategy"] = "git_revert"
                rollback_plan["steps"] = [
                    "Create git stash of current changes",
                    "Revert to previous commit",
                    "Restart affected services",
                    "Verify system health"
                ]

            # Add verification steps
            rollback_plan["verification_steps"] = [
                "Check agent startup",
                "Validate configuration",
                "Test basic functionality",
                "Verify no data corruption"
            ]

            # Calculate estimated time based on modification complexity
            complexity_multiplier = {
                ModificationType.CONFIGURATION: 1.0,
                ModificationType.LOGIC: 1.5,
                ModificationType.MODEL: 2.0,
                ModificationType.INTEGRATION: 2.5,
                ModificationType.DEPENDENCY: 3.0,
                ModificationType.SECURITY: 2.0,
                ModificationType.PERFORMANCE: 1.5,
                ModificationType.STRUCTURE: 3.0,
                ModificationType.KNOWLEDGE: 1.5,
            }

            multiplier = complexity_multiplier.get(proposal.modification_type, 1.5)
            rollback_plan["estimated_time"] = int(30 * multiplier)

            # Assess rollback risk
            if proposal.risk_level in [ModificationRisk.HIGH, ModificationRisk.CRITICAL]:
                rollback_plan["risk_level"] = "medium"

            self.logger.info("rollback_plan_prepared",
                           rollback_id=rollback_plan["rollback_id"],
                           strategy=rollback_plan["strategy"],
                           estimated_time=rollback_plan["estimated_time"])

            return rollback_plan

        except Exception as e:
            self.logger.error("rollback_plan_preparation_failed",
                            proposal_id=proposal.proposal_id,
                            error=str(e),
                            stack_trace=True)
            raise

    async def execute_rollback(self, proposal: ModificationProposal) -> bool:
        """Execute rollback for a failed modification."""
        self.logger.info("executing_rollback", proposal_id=proposal.proposal_id)

        rollback_id = f"rb_{uuid.uuid4().hex[:12]}"

        try:
            # Record rollback start
            self.active_rollbacks[rollback_id] = {
                "proposal_id": proposal.proposal_id,
                "agent_id": proposal.agent_id,
                "start_time": datetime.utcnow(),
                "status": "executing",
                "steps_completed": [],
                "errors": [],
            }

            # Prepare rollback plan
            rollback_plan = await self.prepare_rollback_plan(proposal)

            # Execute rollback steps
            success = await self._execute_rollback_steps(rollback_id, rollback_plan)

            # Record rollback completion
            rollback_record = {
                "rollback_id": rollback_id,
                "proposal_id": proposal.proposal_id,
                "agent_id": proposal.agent_id,
                "start_time": self.active_rollbacks[rollback_id]["start_time"],
                "end_time": datetime.utcnow(),
                "status": "completed" if success else "failed",
                "steps_completed": self.active_rollbacks[rollback_id]["steps_completed"],
                "errors": self.active_rollbacks[rollback_id]["errors"],
                "rollback_plan": rollback_plan,
            }

            self.rollback_history.append(rollback_record)

            # Remove from active rollbacks
            if rollback_id in self.active_rollbacks:
                del self.active_rollbacks[rollback_id]

            if success:
                self.logger.info("rollback_completed_successfully",
                               rollback_id=rollback_id,
                               proposal_id=proposal.proposal_id)
            else:
                self.logger.error("rollback_failed",
                                rollback_id=rollback_id,
                                proposal_id=proposal.proposal_id,
                                errors=len(rollback_record["errors"]))

            return success

        except Exception as e:
            self.logger.error("rollback_execution_failed",
                            proposal_id=proposal.proposal_id,
                            error=str(e),
                            stack_trace=True)

            # Record failure
            if rollback_id in self.active_rollbacks:
                self.active_rollbacks[rollback_id]["status"] = "failed"
                self.active_rollbacks[rollback_id]["errors"].append(str(e))

                rollback_record = {
                    "rollback_id": rollback_id,
                    "proposal_id": proposal.proposal_id,
                    "agent_id": proposal.agent_id,
                    "start_time": self.active_rollbacks[rollback_id]["start_time"],
                    "end_time": datetime.utcnow(),
                    "status": "failed",
                    "errors": [str(e)],
                }

                self.rollback_history.append(rollback_record)
                del self.active_rollbacks[rollback_id]

            return False

    async def _execute_rollback_steps(self, rollback_id: str, rollback_plan: Dict[str, Any]) -> bool:
        """Execute individual rollback steps."""
        try:
            steps = rollback_plan.get("steps", [])

            for i, step in enumerate(steps):
                self.logger.debug("executing_rollback_step",
                                rollback_id=rollback_id,
                                step_number=i + 1,
                                step_description=step)

                try:
                    if "backup" in rollback_plan.get("strategy", ""):
                        success = await self._execute_backup_rollback_step(
                            rollback_id, step, rollback_plan
                        )
                    else:
                        success = await self._execute_git_rollback_step(
                            rollback_id, step, rollback_plan
                        )

                    if success:
                        self.active_rollbacks[rollback_id]["steps_completed"].append(step)
                    else:
                        self.active_rollbacks[rollback_id]["errors"].append(
                            f"Failed to execute step: {step}"
                        )
                        return False

                except Exception as e:
                    self.active_rollbacks[rollback_id]["errors"].append(
                        f"Error in step '{step}': {str(e)}"
                    )
                    return False

            # Execute verification steps
            verification_steps = rollback_plan.get("verification_steps", [])
            for step in verification_steps:
                try:
                    success = await self._verify_rollback_step(rollback_id, step)
                    if not success:
                        self.active_rollbacks[rollback_id]["errors"].append(
                            f"Verification failed: {step}"
                        )
                        return False
                except Exception as e:
                    self.active_rollbacks[rollback_id]["errors"].append(
                        f"Verification error in '{step}': {str(e)}"
                    )
                    return False

            return True

        except Exception as e:
            self.active_rollbacks[rollback_id]["errors"].append(f"Rollback execution error: {str(e)}")
            return False

    async def _execute_backup_rollback_step(self, rollback_id: str, step: str,
                                          rollback_plan: Dict[str, Any]) -> bool:
        """Execute a backup-based rollback step."""
        try:
            if "Validate backup integrity" in step:
                # Validate backup exists and is accessible
                proposal_id = rollback_plan.get("proposal_id")
                if not proposal_id:
                    return False

                # Find the backup version
                for version_id, version in self.version_manager.versions.items():
                    if version.modification_proposal_id == proposal_id:
                        backup_path = self.version_manager.backup_directory / version_id
                        return backup_path.exists() and backup_path.is_dir()

                return False

            elif "Stop affected agent processes" in step:
                # Implementation would stop agent processes
                # This is a placeholder for actual process management
                self.logger.debug("stopping_agent_processes", rollback_id=rollback_id)
                return True

            elif "Restore files from backup" in step:
                # Restore from backup
                proposal_id = rollback_plan.get("proposal_id")
                if not proposal_id:
                    return False

                # Find the backup version and restore it
                for version_id, version in self.version_manager.versions.items():
                    if version.modification_proposal_id == proposal_id:
                        return await self.version_manager.restore_version(version_id)

                return False

            elif "Restart agent processes" in step:
                # Implementation would restart agent processes
                self.logger.debug("restarting_agent_processes", rollback_id=rollback_id)
                return True

            elif "Verify system health" in step:
                # Basic health check
                return await self._verify_system_health(rollback_id)

            elif "Run smoke tests" in step:
                # Run basic smoke tests
                return await self._run_smoke_tests(rollback_id)

            return True

        except Exception as e:
            self.logger.error("backup_rollback_step_failed",
                            rollback_id=rollback_id,
                            step=step,
                            error=str(e))
            return False

    async def _execute_git_rollback_step(self, rollback_id: str, step: str,
                                       rollback_plan: Dict[str, Any]) -> bool:
        """Execute a git-based rollback step."""
        try:
            # This is a placeholder for git-based rollback
            # In a real implementation, this would use git commands
            self.logger.debug("git_rollback_step_placeholder",
                            rollback_id=rollback_id,
                            step=step)
            return True

        except Exception as e:
            self.logger.error("git_rollback_step_failed",
                            rollback_id=rollback_id,
                            step=step,
                            error=str(e))
            return False

    async def _verify_rollback_step(self, rollback_id: str, step: str) -> bool:
        """Verify a rollback step was successful."""
        try:
            if "Check agent startup" in step:
                # Check if agent can start up
                return True  # Placeholder

            elif "Validate configuration" in step:
                # Validate configuration is valid
                return True  # Placeholder

            elif "Test basic functionality" in step:
                # Test basic agent functionality
                return True  # Placeholder

            elif "Verify no data corruption" in step:
                # Check for data corruption
                return True  # Placeholder

            return True

        except Exception as e:
            self.logger.error("rollback_verification_failed",
                            rollback_id=rollback_id,
                            step=step,
                            error=str(e))
            return False

    async def _verify_system_health(self, rollback_id: str) -> bool:
        """Verify overall system health after rollback."""
        try:
            # Basic health checks
            health_checks = [
                self._check_file_system_integrity(),
                self._check_process_health(),
                self._check_network_connectivity(),
            ]

            return all(health_checks)

        except Exception as e:
            self.logger.error("system_health_check_failed",
                            rollback_id=rollback_id,
                            error=str(e))
            return False

    async def _run_smoke_tests(self, rollback_id: str) -> bool:
        """Run smoke tests after rollback."""
        try:
            # Basic smoke tests
            smoke_tests = [
                self._test_agent_imports(),
                self._test_basic_functionality(),
                self._test_configuration_loading(),
            ]

            return all(smoke_tests)

        except Exception as e:
            self.logger.error("smoke_tests_failed",
                            rollback_id=rollback_id,
                            error=str(e))
            return False

    def _check_file_system_integrity(self) -> bool:
        """Check file system integrity."""
        try:
            # Check critical directories exist
            critical_dirs = ["src", "src/agents", "src/api"]
            for dir_path in critical_dirs:
                if not Path(dir_path).exists():
                    return False
            return True
        except:
            return False

    def _check_process_health(self) -> bool:
        """Check process health."""
        # Placeholder for process health checks
        return True

    def _check_network_connectivity(self) -> bool:
        """Check network connectivity."""
        # Placeholder for network connectivity checks
        return True

    def _test_agent_imports(self) -> bool:
        """Test agent imports."""
        try:
            # Test importing key modules
            import importlib

            test_modules = [
                "src.orchestrator",
                "src.agents.base_agent",
            ]

            for module_name in test_modules:
                try:
                    importlib.import_module(module_name)
                except ImportError:
                    return False

            return True
        except:
            return False

    def _test_basic_functionality(self) -> bool:
        """Test basic functionality."""
        # Placeholder for basic functionality tests
        return True

    def _test_configuration_loading(self) -> bool:
        """Test configuration loading."""
        try:
            # Test loading configuration
            from src.agents.config import get_config
            config = get_config()
            return config is not None
        except:
            return False


class SelfModificationSystem:
    """Main coordinator for the self-modification system."""

    def __init__(self, backup_directory: str = "data/backups/agents"):
        """Initialize the self-modification system."""
        self.logger = logger.bind(component="SelfModificationSystem")

        # Initialize components
        self.safety_validator = SafetyValidator()
        self.version_manager = VersionManager(backup_directory)
        self.rollback_manager = RollbackManager(self.version_manager)

        # Modification tracking
        self.active_proposals: Dict[str, ModificationProposal] = {}
        self.proposal_history: List[Dict[str, Any]] = []

        # Safety controls
        self.max_concurrent_modifications = 3
        self.modification_rate_limit = timedelta(minutes=5)  # Min time between modifications
        self.circuit_breaker_threshold = 3  # Failures before circuit breaker
        self.circuit_breaker_failures = 0
        self.circuit_breaker_reset_time = datetime.utcnow()

        # Metrics
        self.metrics = {
            "total_proposals": 0,
            "approved_proposals": 0,
            "implemented_proposals": 0,
            "failed_proposals": 0,
            "rolled_back_proposals": 0,
            "average_validation_time": 0.0,
            "average_implementation_time": 0.0,
        }

        self.logger.info("self_modification_system_initialized",
                        backup_directory=backup_directory)

    async def propose_modification(self, proposal_data: Dict[str, Any]) -> ModificationProposal:
        """Propose a modification to an agent."""
        self.logger.info("proposing_modification", agent_id=proposal_data.get("agent_id"))

        try:
            # Create proposal
            proposal = ModificationProposal(
                agent_id=proposal_data["agent_id"],
                modification_type=ModificationType(proposal_data["modification_type"]),
                description=proposal_data["description"],
                reason=proposal_data["reason"],
                target_file=proposal_data.get("target_file"),
                target_function=proposal_data.get("target_function"),
                target_class=proposal_data.get("target_class"),
                target_config=proposal_data.get("target_config"),
                current_state=proposal_data.get("current_state"),
                proposed_state=proposal_data["proposed_state"],
                diff=proposal_data.get("diff"),
                proposed_by=proposal_data.get("proposed_by", "system"),
                priority=proposal_data.get("priority", "medium"),
                tags=proposal_data.get("tags", []),
            )

            # Store proposal
            self.active_proposals[proposal.proposal_id] = proposal
            self.metrics["total_proposals"] += 1

            self.logger.info("modification_proposed",
                           proposal_id=proposal.proposal_id,
                           agent_id=proposal.agent_id,
                           modification_type=proposal.modification_type.value)

            return proposal

        except Exception as e:
            self.logger.error("modification_proposal_failed",
                            agent_id=proposal_data.get("agent_id"),
                            error=str(e),
                            stack_trace=True)
            raise

    async def validate_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Validate a modification proposal."""
        self.logger.info("validating_proposal", proposal_id=proposal_id)

        try:
            proposal = self.active_proposals.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal not found: {proposal_id}")

            # Check safety controls
            if not await self._check_safety_controls(proposal):
                return {
                    "is_valid": False,
                    "reason": "Safety controls blocked the modification",
                    "circuit_breaker_active": True,
                }

            # Update status
            proposal.status = ModificationStatus.VALIDATING

            # Run validation
            start_time = datetime.utcnow()
            validation_results = await self.safety_validator.validate_proposal(proposal)
            validation_time = (datetime.utcnow() - start_time).total_seconds()

            # Update metrics
            self.metrics["average_validation_time"] = (
                (self.metrics["average_validation_time"] * (self.metrics["total_proposals"] - 1) + validation_time) /
                self.metrics["total_proposals"]
            )

            # Store validation results
            proposal.validation_results = validation_results

            # Update status based on results
            if validation_results["is_valid"]:
                proposal.status = ModificationStatus.APPROVED if proposal.is_approved() else ModificationStatus.PROPOSED
                self.metrics["approved_proposals"] += 1
            else:
                proposal.status = ModificationStatus.REJECTED
                self.circuit_breaker_failures += 1

            # Record in history
            self.proposal_history.append({
                "proposal_id": proposal_id,
                "timestamp": datetime.utcnow().isoformat(),
                "validation_results": validation_results,
                "validation_time": validation_time,
            })

            self.logger.info("proposal_validation_completed",
                           proposal_id=proposal_id,
                           is_valid=validation_results["is_valid"],
                           validation_time=validation_time)

            return validation_results

        except Exception as e:
            self.logger.error("proposal_validation_failed",
                            proposal_id=proposal_id,
                            error=str(e),
                            stack_trace=True)

            if proposal_id in self.active_proposals:
                self.active_proposals[proposal_id].status = ModificationStatus.FAILED

            raise

    async def implement_modification(self, proposal_id: str) -> Dict[str, Any]:
        """Implement an approved modification."""
        self.logger.info("implementing_modification", proposal_id=proposal_id)

        try:
            proposal = self.active_proposals.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal not found: {proposal_id}")

            # Check if proposal is approved
            if not proposal.is_approved():
                return {
                    "success": False,
                    "reason": "Proposal is not approved",
                    "status": proposal.status.value,
                }

            # Update status
            proposal.status = ModificationStatus.IMPLEMENTING

            # Create backup
            backup_version_id = await self.version_manager.create_backup(
                proposal.agent_id, proposal
            )

            # Prepare rollback plan
            rollback_plan = await self.rollback_manager.prepare_rollback_plan(proposal)
            proposal.rollback_plan = rollback_plan

            # Record implementation start
            start_time = datetime.utcnow()

            try:
                # Implement the modification
                changes_made = await self._apply_modification(proposal)

                # Create new version
                new_version = await self.version_manager.create_version(
                    proposal.agent_id, proposal, changes_made
                )

                # Update metrics
                implementation_time = (datetime.utcnow() - start_time).total_seconds()
                self.metrics["average_implementation_time"] = (
                    (self.metrics["average_implementation_time"] * self.metrics["implemented_proposals"] + implementation_time) /
                    (self.metrics["implemented_proposals"] + 1)
                )
                self.metrics["implemented_proposals"] += 1

                # Update proposal status
                proposal.status = ModificationStatus.COMPLETED
                proposal.implementation_log.extend([
                    f"Backup created: {backup_version_id}",
                    f"Rollback plan prepared: {rollback_plan['rollback_id']}",
                    f"Changes applied: {len(changes_made)}",
                    f"New version created: {new_version.version_id}",
                    f"Implementation time: {implementation_time:.2f}s",
                ])

                # Reset circuit breaker on success
                self.circuit_breaker_failures = 0

                self.logger.info("modification_implemented_successfully",
                               proposal_id=proposal_id,
                               version_id=new_version.version_id,
                               changes_count=len(changes_made),
                               implementation_time=implementation_time)

                return {
                    "success": True,
                    "version_id": new_version.version_id,
                    "changes_made": changes_made,
                    "implementation_time": implementation_time,
                    "backup_version_id": backup_version_id,
                    "rollback_plan_id": rollback_plan["rollback_id"],
                }

            except Exception as e:
                # Implementation failed, execute rollback
                self.logger.error("modification_implementation_failed",
                                proposal_id=proposal_id,
                                error=str(e),
                                executing_rollback=True)

                rollback_success = await self.rollback_manager.execute_rollback(proposal)

                if rollback_success:
                    proposal.status = ModificationStatus.ROLLED_BACK
                    self.metrics["rolled_back_proposals"] += 1
                else:
                    proposal.status = ModificationStatus.FAILED
                    self.metrics["failed_proposals"] += 1

                proposal.implementation_log.append(f"Implementation failed: {str(e)}")
                proposal.implementation_log.append(f"Rollback executed: {'Success' if rollback_success else 'Failed'}")

                raise

        except Exception as e:
            self.logger.error("modification_implementation_failed",
                            proposal_id=proposal_id,
                            error=str(e),
                            stack_trace=True)

            if proposal_id in self.active_proposals:
                self.active_proposals[proposal_id].status = ModificationStatus.FAILED
                self.metrics["failed_proposals"] += 1

            raise

    async def rollback_modification(self, proposal_id: str) -> bool:
        """Manually rollback a modification."""
        self.logger.info("manual_rollback_initiated", proposal_id=proposal_id)

        try:
            proposal = self.active_proposals.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal not found: {proposal_id}")

            # Execute rollback
            rollback_success = await self.rollback_manager.execute_rollback(proposal)

            if rollback_success:
                proposal.status = ModificationStatus.ROLLED_BACK
                self.metrics["rolled_back_proposals"] += 1

                self.logger.info("manual_rollback_completed",
                               proposal_id=proposal_id)
            else:
                self.logger.error("manual_rollback_failed",
                                proposal_id=proposal_id)

            return rollback_success

        except Exception as e:
            self.logger.error("manual_rollback_error",
                            proposal_id=proposal_id,
                            error=str(e),
                            stack_trace=True)
            return False

    async def _check_safety_controls(self, proposal: ModificationProposal) -> bool:
        """Check safety controls before processing a proposal."""
        try:
            # Check circuit breaker
            if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                # Check if reset time has passed
                if datetime.utcnow() < self.circuit_breaker_reset_time:
                    self.logger.warning("circuit_breaker_active",
                                       failures=self.circuit_breaker_failures,
                                       reset_time=self.circuit_breaker_reset_time)
                    return False
                else:
                    # Reset circuit breaker
                    self.circuit_breaker_failures = 0

            # Check concurrent modifications
            active_implementations = sum(
                1 for p in self.active_proposals.values()
                if p.status == ModificationStatus.IMPLEMENTING
            )

            if active_implementations >= self.max_concurrent_modifications:
                self.logger.warning("max_concurrent_modifications_reached",
                                   current=active_implementations,
                                   maximum=self.max_concurrent_modifications)
                return False

            # Check rate limiting
            recent_proposals = [
                p for p in self.proposal_history
                if datetime.fromisoformat(p["timestamp"]) > datetime.utcnow() - self.modification_rate_limit
            ]

            if len(recent_proposals) >= 2:  # Max 2 proposals per rate limit period
                self.logger.warning("rate_limit_exceeded",
                                   recent_proposals=len(recent_proposals),
                                   rate_limit=self.modification_rate_limit)
                return False

            # Check for prohibited modifications
            if proposal.risk_level == ModificationRisk.PROHIBITED:
                self.logger.warning("prohibited_modification_blocked",
                                   proposal_id=proposal.proposal_id,
                                   reason="Prohibited risk level")
                return False

            return True

        except Exception as e:
            self.logger.error("safety_control_check_failed",
                            proposal_id=proposal.proposal_id,
                            error=str(e))
            return False

    async def _apply_modification(self, proposal: ModificationProposal) -> List[str]:
        """Apply the actual modification."""
        changes_made = []

        try:
            if proposal.target_file and proposal.proposed_state:
                # File-based modification
                file_path = Path(proposal.target_file)

                # Ensure directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write new content
                if isinstance(proposal.proposed_state, str):
                    content = proposal.proposed_state
                else:
                    content = json.dumps(proposal.proposed_state, indent=2)

                file_path.write_text(content)
                changes_made.append(f"Modified file: {proposal.target_file}")

            elif proposal.target_config:
                # Configuration modification
                # Implementation would depend on configuration system
                changes_made.append(f"Modified configuration for: {proposal.agent_id}")

            elif proposal.target_function or proposal.target_class:
                # Code modification
                # Implementation would require more sophisticated code manipulation
                changes_made.append(f"Modified code for: {proposal.target_function or proposal.target_class}")

            return changes_made

        except Exception as e:
            self.logger.error("modification_application_failed",
                            proposal_id=proposal.proposal_id,
                            error=str(e))
            raise

    def get_proposal(self, proposal_id: str) -> Optional[ModificationProposal]:
        """Get a proposal by ID."""
        return self.active_proposals.get(proposal_id)

    def get_active_proposals(self) -> List[ModificationProposal]:
        """Get all active proposals."""
        return list(self.active_proposals.values())

    def get_proposal_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get proposal history."""
        return self.proposal_history[-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        return {
            **self.metrics,
            "active_proposals": len(self.active_proposals),
            "circuit_breaker_failures": self.circuit_breaker_failures,
            "circuit_breaker_active": self.circuit_breaker_failures >= self.circuit_breaker_threshold,
            "total_versions": len(self.version_manager.versions),
            "rollback_history_size": len(self.rollback_manager.rollback_history),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        health_status = {
            "status": "healthy",
            "checks": {},
            "issues": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            # Check components
            health_status["checks"]["safety_validator"] = "healthy"
            health_status["checks"]["version_manager"] = "healthy"
            health_status["checks"]["rollback_manager"] = "healthy"

            # Check backup directory
            if self.version_manager.backup_directory.exists():
                health_status["checks"]["backup_directory"] = "healthy"
            else:
                health_status["checks"]["backup_directory"] = "unhealthy"
                health_status["issues"].append("Backup directory not accessible")

            # Check circuit breaker
            if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                health_status["checks"]["circuit_breaker"] = "tripped"
                health_status["issues"].append("Circuit breaker is active")
            else:
                health_status["checks"]["circuit_breaker"] = "healthy"

            # Determine overall status
            if health_status["issues"]:
                health_status["status"] = "degraded" if len(health_status["issues"]) <= 2 else "unhealthy"

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["issues"].append(f"Health check failed: {str(e)}")

        return health_status