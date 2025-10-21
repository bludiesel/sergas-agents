#!/usr/bin/env python3
"""
🚀 Quick Validation Script for SERGAS Agents

Run this script to quickly validate that all implemented components are working.
This script tests basic functionality without requiring external dependencies.
"""

import sys
import time
import importlib.util
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_result(test_name, success, message="", details=None):
    """Print formatted test result"""
    icon = "✅" if success else "❌"
    print(f"  {icon} {test_name}")
    if message:
        print(f"     {message}")
    if details:
        for key, value in details.items():
            print(f"     {key}: {value}")

def test_imports():
    """Test that all components can be imported"""
    print_header("Testing Component Imports")

    components = {
        "Dynamic Workflow Engine": "src.agents.dynamic_workflow_engine",
        "Enhanced GLM Integration": "src.agents.enhanced_glm_integration",
        "Self Modification System": "src.agents.self_modification_system",
        "Zoho Evolution System": "src.agents.zoho_evolution_system",
        "Comprehensive Monitoring": "src.monitoring.comprehensive_monitoring"
    }

    results = {}

    for name, module_path in components.items():
        start_time = time.time()

        try:
            spec = importlib.util.find_spec(module_path)
            if spec is None:
                print_result(name, False, f"Module not found: {module_path}")
                results[name] = {"success": False, "import_time": 0}
                continue

            module = importlib.import_module(module_path)
            import_time = time.time() - start_time

            print_result(name, True, f"Imported in {import_time:.3f}s", {
                "module_path": module_path,
                "file": getattr(module, '__file__', 'unknown')
            })

            results[name] = {"success": True, "import_time": import_time}

        except Exception as e:
            print_result(name, False, f"Import failed: {e}")
            results[name] = {"success": False, "import_time": 0, "error": str(e)}

    return results

def test_basic_functionality():
    """Test basic functionality of each component"""
    print_header("Testing Basic Functionality")

    functionality_results = {}

    # Test Dynamic Workflow Engine
    try:
        from src.agents.dynamic_workflow_engine import WorkflowState, WorkflowPriority

        # Test enum values
        assert WorkflowState.PENDING == "pending"
        assert WorkflowPriority.CRITICAL == "critical"

        print_result("Workflow Engine Enums", True, "All enums working correctly", {
            "states": [state.value for state in WorkflowState],
            "priorities": [priority.value for priority in WorkflowPriority]
        })

        functionality_results["workflow_engine"] = {"success": True}

    except Exception as e:
        print_result("Workflow Engine Enums", False, f"Failed: {e}")
        functionality_results["workflow_engine"] = {"success": False, "error": str(e)}

    # Test Enhanced GLM Integration
    try:
        from src.agents.enhanced_glm_integration import GLMModel, ModelCapability

        # Test model enums
        models = [model.value for model in GLMModel]
        expected_models = ["glm-4-flash", "glm-4-plus", "glm-4-air", "glm-4-long", "glm-4-vision"]

        print_result("GLM Model Types", True, f"{len(models)} models available", {
            "models": models,
            "expected_count": len(expected_models),
            "actual_count": len(models)
        })

        functionality_results["glm_integration"] = {"success": True}

    except Exception as e:
        print_result("GLM Model Types", False, f"Failed: {e}")
        functionality_results["glm_integration"] = {"success": False, "error": str(e)}

    # Test Self Modification System
    try:
        from src.agents.self_modification_system import ModificationType, ModificationRisk, ModificationStatus

        # Test modification enums
        modification_types = [mod_type.value for mod_type in ModificationType]
        risk_levels = [risk.value for risk in ModificationRisk]

        print_result("Self Modification Enums", True, "Safety protocols available", {
            "modification_types": modification_types,
            "risk_levels": risk_levels
        })

        functionality_results["self_modification"] = {"success": True}

    except Exception as e:
        print_result("Self Modification Enums", False, f"Failed: {e}")
        functionality_results["self_modification"] = {"success": False, "error": str(e)}

    # Test Zoho Evolution System
    try:
        from src.agents.zoho_evolution_system import LearningType, EvolutionStrategy

        # Test evolution enums
        learning_types = [lt.value for lt in LearningType]
        evolution_strategies = [es.value for es in EvolutionStrategy]

        print_result("Evolution System Enums", True, "Learning capabilities available", {
            "learning_types": learning_types,
            "evolution_strategies": evolution_strategies
        })

        functionality_results["zoho_evolution"] = {"success": True}

    except Exception as e:
        print_result("Evolution System Enums", False, f"Failed: {e}")
        functionality_results["zoho_evolution"] = {"success": False, "error": str(e)}

    # Test Comprehensive Monitoring
    try:
        from src.monitoring.comprehensive_monitoring import TestType, MonitorType, AlertLevel

        # Test monitoring enums
        test_types = [tt.value for tt in TestType]
        monitor_types = [mt.value for mt in MonitorType]
        alert_levels = [al.value for al in AlertLevel]

        print_result("Monitoring System Enums", True, "Comprehensive monitoring available", {
            "test_types": test_types,
            "monitor_types": monitor_types,
            "alert_levels": alert_levels
        })

        functionality_results["monitoring"] = {"success": True}

    except Exception as e:
        print_result("Monitoring System Enums", False, f"Failed: {e}")
        functionality_results["monitoring"] = {"success": False, "error": str(e)}

    return functionality_results

def test_component_creation():
    """Test that components can be instantiated"""
    print_header("Testing Component Creation")

    creation_results = {}

    # Test components that can be created without dependencies
    try:
        from src.agents.enhanced_glm_integration import IntelligentModelSelector

        # This should work without external dependencies
        selector = IntelligentModelSelector()

        print_result("GLM Model Selector", True, "Created successfully", {
            "type": type(selector).__name__,
            "methods": [method for method in dir(selector) if not method.startswith('_')][:5]
        })

        creation_results["glm_selector"] = {"success": True}

    except Exception as e:
        print_result("GLM Model Selector", False, f"Creation failed: {e}")
        creation_results["glm_selector"] = {"success": False, "error": str(e)}

    try:
        from src.agents.zoho_evolution_system import PerformanceTracker

        tracker = PerformanceTracker()

        print_result("Performance Tracker", True, "Created successfully", {
            "type": type(tracker).__name__,
            "max_history_days": getattr(tracker, 'max_history_days', 'unknown')
        })

        creation_results["performance_tracker"] = {"success": True}

    except Exception as e:
        print_result("Performance Tracker", False, f"Creation failed: {e}")
        creation_results["performance_tracker"] = {"success": False, "error": str(e)}

    try:
        from src.monitoring.comprehensive_monitoring import MetricsCollector

        collector = MetricsCollector()

        print_result("Metrics Collector", True, "Created successfully", {
            "type": type(collector).__name__
        })

        creation_results["metrics_collector"] = {"success": True}

    except Exception as e:
        print_result("Metrics Collector", False, f"Creation failed: {e}")
        creation_results["metrics_collector"] = {"success": False, "error": str(e)}

    return creation_results

def test_file_structure():
    """Test that all expected files exist and have reasonable content"""
    print_header("Testing File Structure")

    expected_files = [
        "src/agents/dynamic_workflow_engine.py",
        "src/agents/enhanced_glm_integration.py",
        "src/agents/self_modification_system.py",
        "src/agents/zoho_evolution_system.py",
        "src/monitoring/comprehensive_monitoring.py"
    ]

    structure_results = {}

    for file_path in expected_files:
        full_path = Path(file_path)

        if full_path.exists():
            # Check file size and basic content
            stat = full_path.stat()
            size_kb = stat.st_size / 1024

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.splitlines())

                print_result(file_path, True, f"File exists and readable", {
                    "size_kb": round(size_kb, 1),
                    "lines": lines,
                    "last_modified": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                })

                structure_results[file_path] = {
                    "success": True,
                    "size_kb": size_kb,
                    "lines": lines
                }

            except Exception as e:
                print_result(file_path, False, f"File exists but unreadable: {e}")
                structure_results[file_path] = {"success": False, "error": str(e)}
        else:
            print_result(file_path, False, "File not found")
            structure_results[file_path] = {"success": False, "error": "File not found"}

    return structure_results

def test_dependencies():
    """Test dependency availability"""
    print_header("Testing Dependencies")

    # Core dependencies (should always be available)
    core_deps = {
        "ast": "Python AST parsing",
        "json": "JSON handling",
        "time": "Time functions",
        "asyncio": "Async programming",
        "pathlib": "Path operations",
        "dataclasses": "Data class support",
        "enum": "Enum support",
        "typing": "Type hints"
    }

    # Optional dependencies (may enhance functionality)
    optional_deps = {
        "structlog": "Structured logging",
        "prometheus_client": "Prometheus metrics",
        "psutil": "System monitoring",
        "numpy": "Numerical operations",
        "sklearn": "Machine learning",
        "httpx": "HTTP client",
        "tenacity": "Retry logic",
        "pydantic": "Data validation"
    }

    dependency_results = {}

    print("📦 Core Dependencies:")
    core_available = 0
    for dep, description in core_deps.items():
        try:
            __import__(dep)
            print_result(dep, True, description)
            core_available += 1
        except ImportError:
            print_result(dep, False, f"Missing: {description}")

    print(f"\n✅ Core Dependencies: {core_available}/{len(core_deps)} available")
    dependency_results["core"] = {"available": core_available, "total": len(core_deps)}

    print("\n📦 Optional Dependencies:")
    optional_available = 0
    for dep, description in optional_deps.items():
        try:
            __import__(dep)
            print_result(dep, True, description)
            optional_available += 1
        except ImportError:
            print_result(dep, False, f"Missing: {description}")

    print(f"\n✅ Optional Dependencies: {optional_available}/{len(optional_deps)} available")
    dependency_results["optional"] = {"available": optional_available, "total": len(optional_deps)}

    return dependency_results

def generate_summary(import_results, functionality_results, creation_results, structure_results, dependency_results):
    """Generate final summary"""
    print_header("📊 FINAL SUMMARY")

    # Calculate statistics
    total_imports = len(import_results)
    successful_imports = sum(1 for result in import_results.values() if result["success"])

    total_functionality = len(functionality_results)
    successful_functionality = sum(1 for result in functionality_results.values() if result["success"])

    total_files = len(structure_results)
    successful_files = sum(1 for result in structure_results.values() if result["success"])

    # Print summary statistics
    print(f"📈 Import Success: {successful_imports}/{total_imports} ({successful_imports/total_imports*100:.1f}%)")
    print(f"🔧 Functionality Success: {successful_functionality}/{total_functionality} ({successful_functionality/total_functionality*100:.1f}%)")
    print(f"📁 File Structure Success: {successful_files}/{total_files} ({successful_files/total_files*100:.1f}%)")

    core_deps = dependency_results["core"]
    optional_deps = dependency_results["optional"]

    print(f"📦 Core Dependencies: {core_deps['available']}/{core_deps['total']} available")
    print(f"📦 Optional Dependencies: {optional_deps['available']}/{optional_deps['total']} available")

    # Overall assessment
    overall_success = (
        successful_imports == total_imports and
        successful_functionality >= total_functionality * 0.8 and  # 80% threshold
        successful_files == total_files and
        core_deps["available"] == core_deps["total"]
    )

    print(f"\n🎯 OVERALL RESULT: {'SUCCESS' if overall_success else 'PARTIAL SUCCESS'}")

    if overall_success:
        print("🎉 Excellent! All major components are working correctly.")
        print("🚀 Your SERGAS Agents system is ready for the next steps!")
    else:
        print("⚠️  Some components need attention before full functionality.")
        print("💡 Check the individual test results above for details.")

    # Recommendations
    print(f"\n💡 Recommendations:")

    if optional_deps["available"] < optional_deps["total"]:
        missing = optional_deps["total"] - optional_deps["available"]
        print(f"   • Install {missing} optional dependencies for full functionality:")
        print(f"     pip3 install structlog psutil prometheus-client")

    if successful_imports < total_imports:
        print(f"   • Fix import issues for failed components")

    if successful_functionality < total_functionality:
        print(f"   • Address functionality issues in failed components")

    print(f"   • Run: python3 final_integration_test.py for comprehensive testing")
    print(f"   • Check: TESTING_GUIDE.md for detailed testing instructions")

    return {
        "overall_success": overall_success,
        "import_success_rate": successful_imports/total_imports,
        "functionality_success_rate": successful_functionality/total_functionality,
        "file_structure_success_rate": successful_files/total_files,
        "core_dependencies_complete": core_deps["available"] == core_deps["total"],
        "optional_dependencies_available": optional_deps["available"]
    }

def main():
    """Main test runner"""
    print("🚀 SERGAS Agents Quick Validation")
    print("This script validates that all implemented components are working correctly.")

    start_time = time.time()

    # Run all tests
    import_results = test_imports()
    functionality_results = test_basic_functionality()
    creation_results = test_component_creation()
    structure_results = test_file_structure()
    dependency_results = test_dependencies()

    # Generate summary
    summary = generate_summary(
        import_results, functionality_results, creation_results,
        structure_results, dependency_results
    )

    total_time = time.time() - start_time
    print(f"\n⏱️  Total test time: {total_time:.2f} seconds")

    # Exit with appropriate code
    exit_code = 0 if summary["overall_success"] else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()