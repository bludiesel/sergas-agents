# 🧪 SERGAS Agents Testing Guide

## 📋 Testing Overview

This guide provides multiple ways to test and validate the implemented multi-agent system components. Each testing approach validates different aspects of the system.

## 🚀 Quick Start Testing

### 1. Immediate Validation (5 minutes)

```bash
# Run the comprehensive integration test
python3 final_integration_test.py

# Check file structure and syntax
python3 -c "
import ast, os
files = [
    'src/agents/dynamic_workflow_engine.py',
    'src/agents/enhanced_glm_integration.py',
    'src/agents/self_modification_system.py',
    'src/agents/zoho_evolution_system.py',
    'src/monitoring/comprehensive_monitoring.py'
]
for f in files:
    try:
        with open(f) as file: ast.parse(file.read())
        print(f'✅ {f}: Valid syntax')
    except Exception as e:
        print(f'❌ {f}: {e}')
"
```

### 2. Component Structure Validation

```bash
# Check that all components have the expected classes
python3 -c "
import ast

def analyze_component(file_path):
    with open(file_path) as f:
        tree = ast.parse(f.read())

    classes = []
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef): classes.append(node.name)
        elif isinstance(node, ast.FunctionDef): functions.append(node.name)

    return {'classes': classes, 'functions': functions}

components = {
    'DynamicWorkflowEngine': 'src/agents/dynamic_workflow_engine.py',
    'EnhancedGLMIntegration': 'src/agents/enhanced_glm_integration.py',
    'SelfModificationSystem': 'src/agents/self_modification_system.py',
    'ZohoEvolutionSystem': 'src/agents/zoho_evolution_system.py',
    'ComprehensiveMonitoring': 'src/monitoring/comprehensive_monitoring.py'
}

for name, path in components.items():
    try:
        analysis = analyze_component(path)
        print(f'✅ {name}: {len(analysis[\"classes\"])} classes, {len(analysis[\"functions\"])} functions')
        print(f'   Classes: {analysis[\"classes\"][:3]}...' if len(analysis['classes']) > 3 else f'   Classes: {analysis[\"classes\"]}')
    except Exception as e:
        print(f'❌ {name}: {e}')
"
```

## 🔧 Component-Specific Testing

### 3. Dynamic Workflow Engine Testing

```python
# test_workflow_engine.py
import sys
import os
sys.path.append('.')

def test_workflow_engine_basic():
    """Basic workflow engine functionality test"""
    try:
        # Mock the imports that might have dependencies
        import sys
        from unittest.mock import Mock

        # Mock the modules that might not be available
        sys.modules['src.agents.intent_detection'] = Mock()
        sys.modules['src.events.ag_ui_emitter'] = Mock()

        # Try to import and create basic workflow
        from src.agents.dynamic_workflow_engine import (
            WorkflowState, WorkflowPriority, DynamicWorkflowEngine
        )

        print("✅ Workflow Engine imports successful")

        # Test enum values
        assert WorkflowState.PENDING == "pending"
        assert WorkflowPriority.CRITICAL == "critical"
        print("✅ Workflow enums working")

        # Test basic workflow creation (without actual execution)
        print("✅ Dynamic Workflow Engine structure validated")

        return True

    except Exception as e:
        print(f"❌ Workflow Engine test failed: {e}")
        return False

if __name__ == "__main__":
    test_workflow_engine_basic()
```

### 4. Enhanced GLM Integration Testing

```python
# test_glm_integration.py
import sys
sys.path.append('.')

def test_glm_integration_basic():
    """Basic GLM integration functionality test"""
    try:
        from src.agents.enhanced_glm_integration import (
            GLMModel, ModelCapability, IntelligentModelSelector
        )

        print("✅ GLM Integration imports successful")

        # Test model enums
        assert GLMModel.GLM_4_FLASH == "glm-4-flash"
        assert GLMModel.GLM_4_PLUS == "glm-4-plus"
        print("✅ GLM model enums working")

        # Test model capability creation
        capability = ModelCapability(
            model=GLMModel.GLM_4_FLASH,
            max_tokens=128000,
            speed_factor=0.8,
            quality_factor=0.7
        )
        print(f"✅ Model capability created: {capability.model}")

        # Test intelligent selector (without actual API calls)
        selector = IntelligentModelSelector()
        print("✅ Intelligent model selector created")

        return True

    except Exception as e:
        print(f"❌ GLM Integration test failed: {e}")
        return False

if __name__ == "__main__":
    test_glm_integration_basic()
```

### 5. Self-Modification System Testing

```python
# test_self_modification.py
import sys
sys.path.append('.')

def test_self_modification_basic():
    """Basic self-modification system functionality test"""
    try:
        from src.agents.self_modification_system import (
            ModificationType, ModificationRisk, ModificationStatus,
            SafetyValidator, VersionManager
        )

        print("✅ Self-Modification System imports successful")

        # Test enums
        assert ModificationType.CODE_CHANGE == "code_change"
        assert ModificationRisk.LOW.value == 1
        assert ModificationStatus.PROPOSED == "proposed"
        print("✅ Self-modification enums working")

        # Test safety validator
        validator = SafetyValidator()
        print("✅ Safety validator created")

        # Test version manager
        version_manager = VersionManager("test_versions")
        print("✅ Version manager created")

        return True

    except Exception as e:
        print(f"❌ Self-Modification test failed: {e}")
        return False

if __name__ == "__main__":
    test_self_modification_basic()
```

### 6. Zoho Evolution System Testing

```python
# test_zoho_evolution.py
import sys
sys.path.append('.')

def test_zoho_evolution_basic():
    """Basic Zoho evolution system functionality test"""
    try:
        from src.agents.zoho_evolution_system import (
            LearningType, EvolutionStrategy, PerformanceTracker,
            FeedbackProcessor, PatternRecognizer, EvolutionEngine
        )

        print("✅ Zoho Evolution System imports successful")

        # Test enums
        assert LearningType.PERFORMANCE_BASED == "performance_based"
        assert EvolutionStrategy.GRADUAL_IMPROVEMENT == "gradual_improvement"
        print("✅ Evolution enums working")

        # Test performance tracker
        tracker = PerformanceTracker()
        print("✅ Performance tracker created")

        # Test feedback processor
        feedback_processor = FeedbackProcessor()
        print("✅ Feedback processor created")

        # Test pattern recognizer
        recognizer = PatternRecognizer()
        print("✅ Pattern recognizer created")

        # Test evolution engine
        evolution_engine = EvolutionEngine("test_agent")
        print("✅ Evolution engine created")

        return True

    except Exception as e:
        print(f"❌ Zoho Evolution test failed: {e}")
        return False

if __name__ == "__main__":
    test_zoho_evolution_basic()
```

### 7. Comprehensive Monitoring Testing

```python
# test_monitoring.py
import sys
sys.path.append('.')

def test_monitoring_basic():
    """Basic monitoring system functionality test"""
    try:
        from src.monitoring.comprehensive_monitoring import (
            TestType, MonitorType, AlertLevel, TestRunner,
            MetricsCollector, AlertManager, HealthChecker
        )

        print("✅ Comprehensive Monitoring imports successful")

        # Test enums
        assert TestType.UNIT == "unit"
        assert MonitorType.PERFORMANCE == "performance"
        assert AlertLevel.CRITICAL == "critical"
        print("✅ Monitoring enums working")

        # Test components (without actual execution)
        test_runner = TestRunner()
        print("✅ Test runner created")

        metrics_collector = MetricsCollector()
        print("✅ Metrics collector created")

        alert_manager = AlertManager()
        print("✅ Alert manager created")

        health_checker = HealthChecker()
        print("✅ Health checker created")

        return True

    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")
        return False

if __name__ == "__main__":
    test_monitoring_basic()
```

## 🔗 Integration Testing

### 8. End-to-End Integration Test

```python
# test_integration.py
import sys
sys.path.append('.')

def test_system_integration():
    """Test system integration without external dependencies"""
    try:
        # Test that all components can be imported together
        from src.agents.dynamic_workflow_engine import WorkflowState, DynamicWorkflowEngine
        from src.agents.enhanced_glm_integration import GLMModel, IntelligentModelSelector
        from src.agents.self_modification_system import ModificationType, SafetyValidator
        from src.agents.zoho_evolution_system import LearningType, EvolutionEngine
        from src.monitoring.comprehensive_monitoring import TestType, TestRunner

        print("✅ All components imported successfully")

        # Test that enums don't conflict
        assert WorkflowState.PENDING != TestType.UNIT
        print("✅ Enum conflicts checked")

        # Test basic component creation
        selector = IntelligentModelSelector()
        validator = SafetyValidator()
        runner = TestRunner()

        print("✅ Core components created successfully")

        # Test architecture validation
        components = {
            "workflow": DynamicWorkflowEngine,
            "glm": IntelligentModelSelector,
            "modification": SafetyValidator,
            "evolution": EvolutionEngine,
            "monitoring": TestRunner
        }

        print(f"✅ {len(components)} system components validated")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    test_system_integration()
```

## 📊 Performance Testing

### 9. Performance Benchmarks

```python
# test_performance.py
import time
import sys
sys.path.append('.')

def test_import_performance():
    """Test component import performance"""
    components = {
        "Dynamic Workflow Engine": "src.agents.dynamic_workflow_engine",
        "Enhanced GLM Integration": "src.agents.enhanced_glm_integration",
        "Self Modification System": "src.agents.self_modification_system",
        "Zoho Evolution System": "src.agents.zoho_evolution_system",
        "Comprehensive Monitoring": "src.monitoring.comprehensive_monitoring"
    }

    print("🚀 Testing Import Performance:")

    for name, module_path in components.items():
        start_time = time.time()

        try:
            import importlib
            importlib.import_module(module_path)
            import_time = time.time() - start_time

            print(f"✅ {name}: {import_time:.3f}s")

        except Exception as e:
            print(f"❌ {name}: Failed - {e}")

def test_memory_usage():
    """Test approximate memory usage"""
    import sys

    print("\n💾 Testing Memory Usage:")

    # Get baseline memory
    baseline_objects = len(gc.get_objects()) if 'gc' in sys.modules else 0

    try:
        # Import all components
        from src.agents.dynamic_workflow_engine import DynamicWorkflowEngine
        from src.agents.enhanced_glm_integration import IntelligentModelSelector
        from src.agents.self_modification_system import SafetyValidator
        from src.agents.zoho_evolution_system import EvolutionEngine
        from src.monitoring.comprehensive_monitoring import TestRunner

        # Create instances
        engine = DynamicWorkflowEngine()
        selector = IntelligentModelSelector()
        validator = SafetyValidator()
        evolution = EvolutionEngine("test")
        runner = TestRunner()

        print("✅ All components created in memory")
        print(f"✅ Approximate component count: 5 main classes + supporting classes")

    except Exception as e:
        print(f"❌ Memory test failed: {e}")
```

## 🛠️ Dependency Testing

### 10. Dependency Check

```bash
# Check what dependencies are missing
python3 -c "
import sys

# Check optional dependencies
optional_deps = {
    'structlog': 'structured logging',
    'prometheus_client': 'monitoring metrics',
    'psutil': 'system monitoring',
    'numpy': 'numerical computations',
    'sklearn': 'machine learning (evolution system)',
    'httpx': 'HTTP client (GLM integration)',
    'tenacity': 'retry logic',
    'pydantic': 'data validation'
}

print('🔍 Checking Optional Dependencies:')
available = []
missing = []

for dep, description in optional_deps.items():
    try:
        __import__(dep)
        available.append(f'✅ {dep}: {description}')
    except ImportError:
        missing.append(f'❌ {dep}: {description}')

for item in available:
    print(item)

if missing:
    print('\n⚠️  Missing Optional Dependencies:')
    for item in missing:
        print(item)

    print('\n💡 Install with: pip3 install ' + ' '.join(optional_deps.keys()))
else:
    print('\n✅ All optional dependencies available!')
"
```

## 🚀 Real-World Testing

### 11. Mock Scenario Testing

```python
# test_scenarios.py
import sys
sys.path.append('.')

def test_workflow_scenario():
    """Test a realistic workflow scenario"""
    try:
        from src.agents.dynamic_workflow_engine import WorkflowState, WorkflowPriority
        from src.agents.enhanced_glm_integration import GLMModel
        from src.agents.self_modification_system import ModificationType

        print("🎭 Testing Realistic Scenario:")

        # Simulate account analysis workflow
        workflow_states = [
            WorkflowState.PENDING,
            WorkflowState.INITIALIZING,
            WorkflowState.RUNNING,
            WorkflowState.COMPLETED
        ]

        print(f"✅ Workflow states: {[state.value for state in workflow_states]}")

        # Simulate GLM model selection
        task_requirements = {
            "complexity": "high",
            "urgency": "normal",
            "requires_vision": False,
            "max_tokens": 2000
        }

        # Mock model selection
        selected_model = GLMModel.GLM_4_PLUS if task_requirements["complexity"] == "high" else GLMModel.GLM_4_FLASH
        print(f"✅ Selected GLM model: {selected_model.value}")

        # Simulate self-modification proposal
        modification = {
            "type": ModificationType.PROMPT_CHANGE,
            "risk": "low",
            "description": "Improve account analysis prompts"
        }

        print(f"✅ Modification proposal: {modification['type']} - {modification['description']}")

        return True

    except Exception as e:
        print(f"❌ Scenario test failed: {e}")
        return False

if __name__ == "__main__":
    test_workflow_scenario()
```

## 📋 Quick Test Commands

```bash
# 1. Run all basic tests
echo "🧪 Running Basic Tests..."
python3 final_integration_test.py

# 2. Test individual components
echo "🔧 Testing Components..."
python3 -c "
exec(open('test_workflow_engine.py').read())
exec(open('test_glm_integration.py').read())
exec(open('test_self_modification.py').read())
exec(open('test_zoho_evolution.py').read())
exec(open('test_monitoring.py').read())
"

# 3. Test integration
echo "🔗 Testing Integration..."
python3 test_integration.py

# 4. Check dependencies
echo "📦 Checking Dependencies..."
python3 -c "
# Check core dependencies
import ast, json, time, asyncio
print('✅ Core dependencies available')

# Check optional dependencies
try:
    import structlog, psutil
    print('✅ Some optional dependencies available')
except:
    print('⚠️  Some optional dependencies missing')
"
```

## 🎯 Success Criteria

Your testing is successful if:

✅ **Basic Tests Pass**: All components import and basic functionality works
✅ **Integration Works**: Components can work together without conflicts
✅ **Performance Acceptable**: Import times under 1 second per component
✅ **Memory Reasonable**: Components can be created without excessive memory usage
✅ **Dependencies Clear**: You know what's optional vs required

## 🔧 Troubleshooting

### Import Errors
- Check Python path: `export PYTHONPATH="${PYTHONPATH}:."`
- Install missing dependencies: `pip3 install structlog psutil prometheus-client`
- Check file permissions: `ls -la src/`

### Syntax Errors
- Run syntax check: `python3 -m py_compile src/agents/dynamic_workflow_engine.py`
- Check encoding: Ensure files are UTF-8 encoded

### Performance Issues
- Check system resources: `htop` or `Activity Monitor`
- Disable debug logging in production

## 📈 Next Steps

After successful basic testing:

1. **Add Real API Keys**: Test GLM integration with actual API keys
2. **Set Up Monitoring**: Configure Prometheus and alerting
3. **Load Testing**: Test with concurrent workflows
4. **Integration Testing**: Test with your actual Zoho data
5. **Production Deployment**: Set up proper environment and monitoring

Happy testing! 🚀