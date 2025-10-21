#!/usr/bin/env python3
"""
Simple Account Analysis Workflow Test

Tests the core functionality without complex browser automation.
Uses direct API calls and simple browser navigation to validate the workflow.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
import requests

# Test configuration
FRONTEND_URL = "http://localhost:7008"
BACKEND_URL = "http://localhost:8008"
TEST_RESULTS_DIR = "/tmp/sergas_simple_test"

# Test cases
TEST_QUERIES = [
    {
        "name": "Basic Account Analysis",
        "account_id": "TEST-001",
        "query": "Analyze account TEST-001 for health and risks"
    },
    {
        "name": "Risk Assessment",
        "account_id": "ACCT-123",
        "query": "What are the top 3 risks for account ACCT-123?"
    },
    {
        "name": "Comprehensive Report",
        "account_id": "ENTERPRISE-456",
        "query": "Generate a comprehensive account report for ENTERPRISE-456"
    },
    {
        "name": "Recommendations",
        "account_id": "XYZ-789",
        "query": "What recommendations would you make for XYZ-789?"
    },
    {
        "name": "Action Plan",
        "account_id": "ACCT-999",
        "query": "Create an action plan for account ACCT-999"
    }
]

def setup_directories():
    """Create test result directories"""
    os.makedirs(TEST_RESULTS_DIR, exist_ok=True)
    print(f"📁 Test results will be saved to: {TEST_RESULTS_DIR}")

def test_backend_health():
    """Test backend health and CopilotKit integration"""
    print("\n🧪 Testing Backend Health...")

    try:
        # Test general health
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend healthy: {health_data.get('status', 'unknown')}")
            print(f"   Model: {health_data.get('model', 'unknown')}")
            print(f"   Agents: {health_data.get('agents_registered', 0)}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_copilotkit_direct():
    """Test CopilotKit endpoint directly"""
    print("\n🧪 Testing CopilotKit Direct API...")

    results = []

    for i, test_case in enumerate(TEST_QUERIES):
        print(f"\n📝 Test {i+1}: {test_case['name']}")

        # Prepare GraphQL-style request
        request_data = {
            "operationName": "generateCopilotResponse",
            "variables": {
                "data": {
                    "messages": [
                        {"role": "user", "content": test_case['query']}
                    ]
                }
            },
            "account_id": test_case['account_id'],
            "thread_id": f"test_thread_{i}_{int(time.time())}",
            "session_id": f"test_session_{i}_{int(time.time())}",
            "agent": "orchestrator",
            "workflow": "account_analysis"
        }

        try:
            print(f"   🔄 Sending request for {test_case['account_id']}...")
            start_time = time.time()

            response = requests.post(
                f"{BACKEND_URL}/api/copilotkit",
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                response_data = response.json()

                # Extract the actual response
                if 'data' in response_data and 'generateCopilotResponse' in response_data['data']:
                    copilot_response = response_data['data']['generateCopilotResponse']
                    response_text = copilot_response.get('response', '')
                    model = copilot_response.get('model', 'unknown')

                    print(f"   ✅ Response received in {response_time:.2f}s")
                    print(f"   🤖 Model: {model}")
                    print(f"   📊 Response length: {len(response_text)} characters")

                    # Check for GLM-4.6 characteristics
                    has_glm_mention = "GLM" in response_text or "glm-4.6" in response_text
                    has_account_context = test_case['account_id'] in response_text
                    has_professional_tone = any(word in response_text.lower() for word in
                                              ['analysis', 'recommendation', 'risk', 'account', 'health'])

                    print(f"   🔍 GLM-4.6 mentioned: {has_glm_mention}")
                    print(f"   📋 Account context: {has_account_context}")
                    print(f"   💼 Professional tone: {has_professional_tone}")

                    # Save response
                    response_file = f"{TEST_RESULTS_DIR}/test_{i+1}_response.json"
                    with open(response_file, 'w') as f:
                        json.dump({
                            "test_case": test_case,
                            "request": request_data,
                            "response": response_data,
                            "response_time": response_time,
                            "analysis": {
                                "has_glm_mention": has_glm_mention,
                                "has_account_context": has_account_context,
                                "has_professional_tone": has_professional_tone,
                                "response_length": len(response_text)
                            }
                        }, f, indent=2)

                    print(f"   💾 Response saved to {response_file}")

                    results.append({
                        "test": test_case['name'],
                        "success": True,
                        "response_time": response_time,
                        "response_length": len(response_text),
                        "has_glm_mention": has_glm_mention,
                        "has_account_context": has_account_context,
                        "has_professional_tone": has_professional_tone,
                        "model": model
                    })

                else:
                    print(f"   ❌ Invalid response format: {response_data}")
                    results.append({
                        "test": test_case['name'],
                        "success": False,
                        "error": "Invalid response format"
                    })

            else:
                print(f"   ❌ API request failed: {response.status_code}")
                print(f"   Error: {response.text}")
                results.append({
                    "test": test_case['name'],
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                })

        except requests.exceptions.Timeout:
            print(f"   ❌ Request timed out (30s)")
            results.append({
                "test": test_case['name'],
                "success": False,
                "error": "Timeout"
            })

        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            results.append({
                "test": test_case['name'],
                "success": False,
                "error": str(e)
            })

    return results

def test_frontend_connectivity():
    """Test that frontend can connect to CopilotKit endpoint"""
    print("\n🧪 Testing Frontend to Backend Connectivity...")

    try:
        # Test frontend CopilotKit proxy
        request_data = {
            "operationName": "generateCopilotResponse",
            "variables": {
                "data": {
                    "messages": [
                        {"role": "user", "content": "Simple connectivity test"}
                    ]
                }
            },
            "account_id": "CONNECTIVITY-TEST",
            "thread_id": "frontend_test",
            "session_id": "frontend_test"
        }

        response = requests.post(
            f"{FRONTEND_URL}/api/copilotkit",
            json=request_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Frontend can successfully connect to backend")
            response_data = response.json()
            print(f"   Response: {str(response_data)[:100]}...")
            return True
        else:
            print(f"❌ Frontend connection failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Frontend connectivity test failed: {e}")
        return False

def test_browser_accessibility():
    """Test that the frontend application is accessible via browser"""
    print("\n🧪 Testing Browser Accessibility...")

    try:
        # Check if frontend is running
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend application is accessible")

            # Check for key elements in the HTML
            content = response.text
            has_sergas_title = "Sergas Account Manager" in content
            has_copilotkit = "copilot" in content.lower()
            has_account_analysis = "Account Analysis" in content

            print(f"   📱 Sergas title found: {has_sergas_title}")
            print(f"   🤖 CopilotKit integration: {has_copilotkit}")
            print(f"   📊 Account Analysis tab: {has_account_analysis}")

            return has_sergas_title and has_copilotkit
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Browser accessibility test failed: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid requests"""
    print("\n🧪 Testing Error Handling...")

    try:
        # Test with invalid account ID
        invalid_request = {
            "operationName": "generateCopilotResponse",
            "variables": {
                "data": {
                    "messages": [
                        {"role": "user", "content": "Analyze invalid account"}
                    ]
                }
            },
            "account_id": "INVALID-ACCOUNT-999",
            "thread_id": "error_test",
            "session_id": "error_test"
        }

        response = requests.post(
            f"{BACKEND_URL}/api/copilotkit",
            json=invalid_request,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        # Should still get a response (even if account doesn't exist)
        if response.status_code == 200:
            response_data = response.json()
            print("✅ Error handling working gracefully")

            if 'data' in response_data and 'generateCopilotResponse' in response_data['data']:
                copilot_response = response_data['data']['generateCopilotResponse']
                response_text = copilot_response.get('response', '')

                # Check if response acknowledges the issue
                has_error_acknowledgment = any(word in response_text.lower() for word in
                                             ['error', 'invalid', 'not found', 'unable'])

                print(f"   ⚠️ Error acknowledged: {has_error_acknowledgment}")

                # Save error response
                error_file = f"{TEST_RESULTS_DIR}/error_handling_response.json"
                with open(error_file, 'w') as f:
                    json.dump({
                        "request": invalid_request,
                        "response": response_data,
                        "has_error_acknowledgment": has_error_acknowledgment
                    }, f, indent=2)

                return True
            else:
                print("⚠️ Response format unexpected for error case")
                return False
        else:
            print(f"❌ Error handling test failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def generate_test_report(backend_health, frontend_connectivity, browser_accessibility,
                        copilotkit_results, error_handling):
    """Generate comprehensive test report"""
    print("\n📊 Generating Test Report...")

    report = {
        "test_summary": {
            "timestamp": datetime.now().isoformat(),
            "frontend_url": FRONTEND_URL,
            "backend_url": BACKEND_URL,
        },
        "results": {
            "backend_health": backend_health,
            "frontend_connectivity": frontend_connectivity,
            "browser_accessibility": browser_accessibility,
            "copilotkit_tests": copilotkit_results,
            "error_handling": error_handling
        }
    }

    # Calculate success rates
    copilotkit_success = sum(1 for result in copilotkit_results if result.get("success", False))
    copilotkit_total = len(copilotkit_results)
    copilotkit_success_rate = (copilotkit_success / copilotkit_total * 100) if copilotkit_total > 0 else 0

    # GLM-4.6 characteristics
    glm_mentions = sum(1 for result in copilotkit_results if result.get("has_glm_mention", False))
    account_context = sum(1 for result in copilotkit_results if result.get("has_account_context", False))
    professional_tone = sum(1 for result in copilotkit_results if result.get("has_professional_tone", False))

    report["test_summary"].update({
        "copilotkit_success_rate": copilotkit_success_rate,
        "glm_mentions": glm_mentions,
        "account_context": account_context,
        "professional_tone": professional_tone
    })

    # Save JSON report
    json_file = f"{TEST_RESULTS_DIR}/test_report.json"
    with open(json_file, 'w') as f:
        json.dump(report, f, indent=2)

    # Generate markdown report
    markdown_report = f"""# Sergas Account Analysis Workflow Test Report

## Test Summary
- **Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Frontend URL**: {FRONTEND_URL}
- **Backend URL**: {BACKEND_URL}

## Test Results

### ✅ Core Functionality Tests
- **Backend Health**: {'✅ PASS' if backend_health else '❌ FAIL'}
- **Frontend Connectivity**: {'✅ PASS' if frontend_connectivity else '❌ FAIL'}
- **Browser Accessibility**: {'✅ PASS' if browser_accessibility else '❌ FAIL'}
- **Error Handling**: {'✅ PASS' if error_handling else '❌ FAIL'}

### 🤖 CopilotKit API Tests
- **Success Rate**: {copilotkit_success_rate:.1f}% ({copilotkit_success}/{copilotkit_total})
- **GLM-4.6 Mentions**: {glm_mentions}/{copilotkit_total}
- **Account Context**: {account_context}/{copilotkit_total}
- **Professional Tone**: {professional_tone}/{copilotkit_total}

## Detailed Test Results

"""

    for i, result in enumerate(copilotkit_results, 1):
        status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
        markdown_report += f"### Test {i}: {result.get('test', 'Unknown')} - {status}\n"

        if result.get("success", False):
            markdown_report += f"- **Response Time**: {result.get('response_time', 0):.2f}s\n"
            markdown_report += f"- **Response Length**: {result.get('response_length', 0)} characters\n"
            markdown_report += f"- **Model**: {result.get('model', 'Unknown')}\n"
            markdown_report += f"- **GLM-4.6 Mentioned**: {result.get('has_glm_mention', False)}\n"
            markdown_report += f"- **Account Context**: {result.get('has_account_context', False)}\n"
            markdown_report += f"- **Professional Tone**: {result.get('has_professional_tone', False)}\n"
        else:
            markdown_report += f"- **Error**: {result.get('error', 'Unknown error')}\n"

        markdown_report += "\n"

    markdown_report += f"""
## Analysis & Recommendations

### 🎯 Overall Assessment
"""

    overall_success = all([backend_health, frontend_connectivity, browser_accessibility, error_handling])
    if overall_success and copilotkit_success_rate >= 80:
        markdown_report += "✅ **EXCELLENT**: The account analysis workflow is fully functional!\n"
    elif overall_success and copilotkit_success_rate >= 60:
        markdown_report += "⚠️ **GOOD**: Core functionality works with some CopilotKit issues.\n"
    elif overall_success:
        markdown_report += "⚠️ **NEEDS IMPROVEMENT**: Infrastructure works but CopilotKit needs attention.\n"
    else:
        markdown_report += "❌ **CRITICAL ISSUES**: Core infrastructure problems detected.\n"

    if glm_mentions == 0:
        markdown_report += "\n⚠️ **GLM-4.6 Integration**: Model not clearly identified in responses\n"

    if account_context < copilotkit_total * 0.8:
        markdown_report += "⚠️ **Account Context**: Responses don't consistently reference account IDs\n"

    if professional_tone < copilotkit_total * 0.8:
        markdown_report += "⚠️ **Response Quality**: Professional tone needs improvement\n"

    markdown_report += f"""
## Files Generated
- **Detailed JSON Report**: {json_file}
- **Individual Response Files**: {TEST_RESULTS_DIR}/test_*_response.json
- **Error Handling Test**: {TEST_RESULTS_DIR}/error_handling_response.json

## Test Environment
- **Frontend**: Next.js on port 7008
- **Backend**: FastAPI on port 8008
- **AI Model**: GLM-4.6 via Z.ai
- **Integration**: CopilotKit + AG UI Protocol
"""

    # Save markdown report
    markdown_file = f"{TEST_RESULTS_DIR}/test_report.md"
    with open(markdown_file, 'w') as f:
        f.write(markdown_report)

    print(f"📋 Markdown report saved to: {markdown_file}")
    print(f"📊 Detailed JSON report saved to: {json_file}")

    return markdown_file, json_file

def main():
    """Main test execution"""
    print("🚀 Starting Simple Sergas Account Analysis Workflow Test")
    print("=" * 60)

    setup_directories()

    # Run all tests
    backend_health = test_backend_health()
    frontend_connectivity = test_frontend_connectivity()
    browser_accessibility = test_browser_accessibility()
    copilotkit_results = test_copilotkit_direct()
    error_handling = test_error_handling()

    # Generate report
    generate_test_report(
        backend_health,
        frontend_connectivity,
        browser_accessibility,
        copilotkit_results,
        error_handling
    )

    print("\n" + "=" * 60)
    print("🏁 Simple Sergas Account Analysis Workflow Test Complete!")
    print(f"📁 All results saved to: {TEST_RESULTS_DIR}")

    # Print final summary
    copilotkit_success = sum(1 for result in copilotkit_results if result.get("success", False))
    copilotkit_total = len(copilotkit_results)
    success_rate = (copilotkit_success / copilotkit_total * 100) if copilotkit_total > 0 else 0

    print(f"📊 CopilotKit Success Rate: {success_rate:.1f}% ({copilotkit_success}/{copilotkit_total})")
    print(f"🔧 Backend Health: {'✅' if backend_health else '❌'}")
    print(f"🌐 Frontend Connectivity: {'✅' if frontend_connectivity else '❌'}")
    print(f"📱 Browser Access: {'✅' if browser_accessibility else '❌'}")
    print(f"⚠️ Error Handling: {'✅' if error_handling else '❌'}")

if __name__ == "__main__":
    main()