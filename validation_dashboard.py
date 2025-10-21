#!/usr/bin/env python3
"""
📊 SERGAS Agents Validation Dashboard

This script creates a simple monitoring and validation dashboard
to visualize the system status and performance metrics.
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

class ValidationDashboard:
    """Simple validation dashboard for SERGAS Agents"""

    def __init__(self):
        self.components = {
            "Dynamic Workflow Engine": {
                "file": "src/agents/dynamic_workflow_engine.py",
                "description": "Adaptive multi-agent workflow orchestration",
                "status": "unknown",
                "metrics": {}
            },
            "Enhanced GLM Integration": {
                "file": "src/agents/enhanced_glm_integration.py",
                "description": "Intelligent GLM-4.6 model selection and routing",
                "status": "unknown",
                "metrics": {}
            },
            "Self Modification System": {
                "file": "src/agents/self_modification_system.py",
                "description": "Safe agent modification with version control",
                "status": "unknown",
                "metrics": {}
            },
            "Zoho Evolution System": {
                "file": "src/agents/zoho_evolution_system.py",
                "description": "Continuous learning and agent evolution",
                "status": "unknown",
                "metrics": {}
            },
            "Comprehensive Monitoring": {
                "file": "src/monitoring/comprehensive_monitoring.py",
                "description": "Complete testing and monitoring infrastructure",
                "status": "unknown",
                "metrics": {}
            }
        }

    def print_header(self, title):
        """Print formatted header"""
        width = 80
        border = "=" * width
        padding = (width - len(title) - 2) // 2
        print(f"\n{border}")
        print(f"{' ' * padding}{title}{' ' * padding}")
        print(f"{border}")

    def print_component_status(self, name, info):
        """Print component status with visual indicators"""
        status = info["status"]
        if status == "healthy":
            icon = "🟢"
            status_text = "HEALTHY"
        elif status == "warning":
            icon = "🟡"
            status_text = "WARNING"
        elif status == "error":
            icon = "🔴"
            status_text = "ERROR"
        else:
            icon = "⚪"
            status_text = "UNKNOWN"

        print(f"\n{icon} {name}")
        print(f"   Status: {status_text}")
        print(f"   Description: {info['description']}")
        print(f"   File: {info['file']}")

        # Print metrics if available
        if info.get("metrics"):
            print("   Metrics:")
            for key, value in info["metrics"].items():
                print(f"     • {key}: {value}")

    def check_component_health(self, component_name):
        """Check health of a specific component"""
        component_info = self.components[component_name]
        file_path = Path(component_info["file"])

        if not file_path.exists():
            component_info["status"] = "error"
            component_info["metrics"]["error"] = "File not found"
            return

        try:
            # Check file modification time
            stat = file_path.stat()
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            size_kb = stat.st_size / 1024

            component_info["metrics"] = {
                "last_modified": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                "size_kb": round(size_kb, 1),
                "file_exists": True
            }

            # Try to read file content for basic validation
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = len(content.splitlines())

                component_info["metrics"]["lines"] = lines
                component_info["metrics"]["readable"] = True

            # Basic health check
            age_hours = (datetime.now() - mod_time).total_seconds() / 3600

            if lines < 100:
                component_info["status"] = "warning"
                component_info["metrics"]["warning"] = "Component seems incomplete"
            elif age_hours > 24:
                component_info["status"] = "warning"
                component_info["metrics"]["warning"] = f"Component not updated for {age_hours:.1f} hours"
            else:
                component_info["status"] = "healthy"

        except Exception as e:
            component_info["status"] = "error"
            component_info["metrics"]["error"] = str(e)

    def check_system_dependencies(self):
        """Check system dependencies"""
        dependencies = {
            "Python Core": ["ast", "json", "time", "asyncio", "pathlib"],
            "Optional": ["structlog", "prometheus_client", "psutil", "numpy", "sklearn", "httpx", "tenacity"]
        }

        dep_status = {}

        for category, deps in dependencies.items():
            available = []
            missing = []

            for dep in deps:
                try:
                    __import__(dep)
                    available.append(dep)
                except ImportError:
                    missing.append(dep)

            dep_status[category] = {
                "available": len(available),
                "total": len(deps),
                "missing": missing,
                "status": "healthy" if len(available) == len(deps) else "warning"
            }

        return dep_status

    def generate_dashboard(self):
        """Generate the validation dashboard"""
        self.print_header("📊 SERGAS Agents Validation Dashboard")

        # Check all components
        print("🔍 Checking Component Health...")
        for component_name in self.components:
            self.check_component_health(component_name)

        # Print component statuses
        print("\n📋 Component Status:")
        for name, info in self.components.items():
            self.print_component_status(name, info)

        # Check dependencies
        print("\n📦 Dependency Status:")
        dep_status = self.check_system_dependencies()

        for category, status in dep_status.items():
            icon = "🟢" if status["status"] == "healthy" else "🟡"
            print(f"\n{icon} {category}: {status['available']}/{status['total']} dependencies available")

            if status["missing"]:
                print(f"   Missing: {', '.join(status['missing'])}")

        # System summary
        self.print_header("📈 System Summary")

        total_components = len(self.components)
        healthy_components = sum(1 for info in self.components.values() if info["status"] == "healthy")
        warning_components = sum(1 for info in self.components.values() if info["status"] == "warning")
        error_components = sum(1 for info in self.components.values() if info["status"] == "error")

        print(f"📊 Component Status:")
        print(f"   Healthy: {healthy_components} 🟢")
        print(f"   Warning: {warning_components} 🟡")
        print(f"   Error: {error_components} 🔴")
        print(f"   Total: {total_components}")

        # Overall system health
        if error_components > 0:
            overall_status = "CRITICAL"
            icon = "🔴"
        elif warning_components > 0:
            overall_status = "WARNING"
            icon = "🟡"
        else:
            overall_status = "HEALTHY"
            icon = "🟢"

        print(f"\n🎯 Overall System Status: {icon} {overall_status}")

        # Recommendations
        print(f"\n💡 Recommendations:")

        if error_components > 0:
            print("   • Fix components with errors before production use")

        if warning_components > 0:
            print("   • Address warnings in affected components")

        core_deps_available = dep_status["Python Core"]["available"]
        core_deps_total = dep_status["Python Core"]["total"]

        if core_deps_available == core_deps_total:
            print("   • ✅ Core dependencies are satisfied")
        else:
            print("   • ❌ Core dependencies are missing - this should not happen")

        optional_deps_available = dep_status["Optional"]["available"]
        optional_deps_total = dep_status["Optional"]["total"]

        if optional_deps_available == optional_deps_total:
            print("   • ✅ All optional dependencies available - full functionality")
        else:
            print("   • ⚠️  Install optional dependencies for full functionality:")
            missing_count = optional_deps_total - optional_deps_available
            print(f"     pip3 install --user {' '.join(dep_status['Optional']['missing'])}")

        # Quick actions
        print(f"\n🚀 Quick Actions:")
        print("   • Run full validation: python3 dependency_free_test.py")
        print("   • Check integration: python3 final_integration_test.py")
        print("   • View detailed guide: cat TESTING_GUIDE.md")

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "components": self.components,
            "dependencies": dep_status,
            "summary": {
                "total": total_components,
                "healthy": healthy_components,
                "warning": warning_components,
                "error": error_components
            }
        }

    def save_dashboard_data(self, data):
        """Save dashboard data to JSON file"""
        dashboard_file = Path("validation_dashboard_data.json")
        with open(dashboard_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"\n📄 Dashboard data saved to: {dashboard_file}")

def main():
    """Main dashboard runner"""
    dashboard = ValidationDashboard()

    print("🚀 SERGAS Agents Validation Dashboard")
    print("Real-time system health and validation monitoring")

    data = dashboard.generate_dashboard()
    dashboard.save_dashboard_data(data)

    # Exit with appropriate code
    exit_code = 0 if data["overall_status"] in ["HEALTHY", "WARNING"] else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()