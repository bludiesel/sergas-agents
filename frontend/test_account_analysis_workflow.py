#!/usr/bin/env python3
"""
Comprehensive Account Analysis Workflow Testing Script

Tests the complete Sergas Account Manager UI workflow:
1. Navigate to Account Analysis tab
2. Test CopilotKit integration with GLM-4.6
3. Validate response quality and structure
4. Test UI integration and display
5. Performance testing
6. Error handling validation
"""

import os
import sys
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, expect

# Test configuration
FRONTEND_URL = "http://localhost:7008"
BACKEND_URL = "http://localhost:8008"
TEST_RESULTS_DIR = "/tmp/sergas_account_analysis_test"
SCREENSHOT_DIR = f"{TEST_RESULTS_DIR}/screenshots"
RESPONSES_DIR = f"{TEST_RESULTS_DIR}/responses"

# Test account IDs
TEST_ACCOUNTS = [
    "TEST-001",
    "ACCT-123",
    "ENTERPRISE-456",
    "ACCT-999",
    "NEW-001"
]

# Test queries for CopilotKit
TEST_QUERIES = [
    "Analyze account ACCT-001 for health and risks",
    "What are the top 3 risks for account XYZ-123?",
    "Generate a comprehensive account report for TEST-456",
    "What recommendations would you make for ENTERPRISE-789?",
    "Create an action plan for account ACCT-999"
]

def setup_directories():
    """Create test result directories"""
    os.makedirs(TEST_RESULTS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(RESPONSES_DIR, exist_ok=True)
    print(f"📁 Test results will be saved to: {TEST_RESULTS_DIR}")

def take_screenshot(page, name, description=""):
    """Take a screenshot with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SCREENSHOT_DIR}/{name}_{timestamp}.png"
    page.screenshot(path=filename, full_page=True)
    print(f"📸 Screenshot saved: {filename}")
    if description:
        print(f"   Description: {description}")
    return filename

def wait_for_copilot_response(page, timeout=30000):
    """Wait for CopilotKit response in sidebar"""
    try:
        # Wait for message in copilot sidebar
        page.wait_for_selector('[data-testid="copilot-message"]', timeout=timeout)
        return True
    except:
        # Try alternative selectors
        selectors = [
            '.copilot-message',
            '[class*="message"]',
            '[class*="response"]',
            '.prose',
            '.markdown-content'
        ]

        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=5000)
                return True
            except:
                continue
        return False

def get_copilot_messages(page):
    """Extract messages from CopilotKit sidebar"""
    messages = []

    # Try different selectors for messages
    selectors = [
        '[data-testid="copilot-message"]',
        '.copilot-message',
        '[class*="message"]',
        '.prose p',
        '.markdown-content p'
    ]

    for selector in selectors:
        try:
            elements = page.query_selector_all(selector)
            if elements:
                for element in elements:
                    text = element.text_content()
                    if text and len(text.strip()) > 10:  # Filter out short/empty messages
                        messages.append(text.strip())
                break
        except:
            continue

    return messages

def test_account_analysis_tab_navigation(page):
    """Test Account Analysis tab navigation and component loading"""
    print("\n🧪 Testing Account Analysis Tab Navigation...")

    # Navigate to the application
    page.goto(FRONTEND_URL)
    page.wait_for_load_state('networkidle')

    take_screenshot(page, "01_initial_load", "Initial application load")

    # Check if Account Analysis tab exists and is clickable
    try:
        account_analysis_tab = page.locator('text="Account Analysis"')
        expect(account_analysis_tab).to_be_visible()
        print("✅ Account Analysis tab found")

        # Click on Account Analysis tab
        account_analysis_tab.click()
        page.wait_for_timeout(2000)  # Wait for tab transition

        take_screenshot(page, "02_account_analysis_tab", "Account Analysis tab selected")

        # Verify AccountAnalysisAgent component loads
        # Look for distinctive elements from the component
        component_indicators = [
            'text="Selected Account"',
            'text="Agent Execution Status"',
            'text="Account Snapshot"',
            '[class*="account-analysis"]'
        ]

        component_found = False
        for indicator in component_indicators:
            try:
                element = page.locator(indicator)
                if element.is_visible():
                    component_found = True
                    print(f"✅ AccountAnalysisAgent component loaded (found: {indicator})")
                    break
            except:
                continue

        if not component_found:
            print("⚠️  AccountAnalysisAgent component may not be fully loaded")
            take_screenshot(page, "02a_component_check", "Component loading check")

        return True

    except Exception as e:
        print(f"❌ Account Analysis tab navigation failed: {e}")
        take_screenshot(page, "02_error", "Account Analysis navigation error")
        return False

def test_copilotkit_sidebar(page):
    """Test CopilotKit sidebar functionality"""
    print("\n🧪 Testing CopilotKit Sidebar...")

    try:
        # Look for CopilotKit sidebar
        sidebar_selectors = [
            '[data-testid="copilot-sidebar"]',
            '.copilot-sidebar',
            '[class*="copilot"]',
            'text="Account Analysis Assistant"'
        ]

        sidebar_found = False
        for selector in sidebar_selectors:
            try:
                sidebar = page.locator(selector)
                if sidebar.is_visible():
                    sidebar_found = True
                    print(f"✅ CopilotKit sidebar found (selector: {selector})")
                    break
            except:
                continue

        if not sidebar_found:
            print("⚠️  CopilotKit sidebar not immediately visible, checking if it's closed...")
            # Try to open sidebar if there's a toggle button
            try:
                toggle_button = page.locator('[aria-label*="chat"], [aria-label*="assistant"], button[title*="chat"]')
                if toggle_button.is_visible():
                    toggle_button.click()
                    page.wait_for_timeout(1000)
                    print("✅ Attempted to open sidebar")
            except:
                pass

        take_screenshot(page, "03_copilot_sidebar", "CopilotKit sidebar status")

        # Look for input field
        input_selectors = [
            'textarea[placeholder*="ask"]',
            'textarea[placeholder*="message"]',
            'input[placeholder*="ask"]',
            'input[placeholder*="message"]',
            '.copilot-input textarea',
            '[data-testid="copilot-input"]'
        ]

        input_found = False
        for selector in input_selectors:
            try:
                input_field = page.locator(selector)
                if input_field.is_visible():
                    input_found = True
                    print(f"✅ CopilotKit input field found (selector: {selector})")
                    return input_field
                    break
            except:
                continue

        if not input_found:
            print("⚠️  CopilotKit input field not found")
            take_screenshot(page, "03a_input_check", "Input field check")

        return None

    except Exception as e:
        print(f"❌ CopilotKit sidebar test failed: {e}")
        return None

def test_account_analysis_queries(page, input_field):
    """Test various account analysis queries"""
    print("\n🧪 Testing Account Analysis Queries...")

    results = []

    for i, query in enumerate(TEST_QUERIES):
        print(f"\n📝 Testing query {i+1}: {query}")

        try:
            # Clear any existing text and type new query
            input_field.clear()
            input_field.type(query)

            # Submit the query (look for send button or press Enter)
            send_button_selectors = [
                'button[aria-label*="send"]',
                'button[title*="send"]',
                'button[type="submit"]',
                '.send-button',
                '[data-testid="send-button"]'
            ]

            sent = False
            for selector in send_button_selectors:
                try:
                    send_button = page.locator(selector)
                    if send_button.is_visible():
                        send_button.click()
                        sent = True
                        break
                except:
                    continue

            if not sent:
                # Try pressing Enter
                input_field.press('Enter')

            print("⏳ Waiting for response...")

            # Wait for response
            response_received = wait_for_copilot_response(page)

            if response_received:
                page.wait_for_timeout(3000)  # Additional wait for full response
                take_screenshot(page, f"04_query_{i+1}_response", f"Response for query: {query}")

                # Extract response content
                messages = get_copilot_messages(page)
                if messages:
                    latest_message = messages[-1]  # Get the latest message

                    # Save response to file
                    response_file = f"{RESPONSES_DIR}/query_{i+1}_response.txt"
                    with open(response_file, 'w') as f:
                        f.write(f"Query: {query}\n")
                        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                        f.write(f"Response:\n{latest_message}\n")

                    print(f"✅ Response received and saved to {response_file}")

                    # Basic response quality checks
                    response_length = len(latest_message)
                    has_glM_mentions = "GLM" in latest_message or "model" in latest_message.lower()
                    has_account_context = any(acc_id in latest_message for acc_id in ["ACCT", "TEST", "ENTERPRISE", "XYZ"])

                    results.append({
                        "query": query,
                        "response_length": response_length,
                        "has_model_mention": has_glM_mentions,
                        "has_account_context": has_account_context,
                        "success": True
                    })

                    print(f"   📊 Response length: {response_length} characters")
                    print(f"   🤖 Model mentioned: {has_glM_mentions}")
                    print(f"   📋 Account context: {has_account_context}")

                else:
                    print("⚠️  No clear response content found")
                    results.append({"query": query, "success": False, "error": "No response content"})
            else:
                print("❌ No response received within timeout")
                take_screenshot(page, f"04_query_{i+1}_timeout", f"Timeout for query: {query}")
                results.append({"query": query, "success": False, "error": "Timeout"})

        except Exception as e:
            print(f"❌ Query failed: {e}")
            take_screenshot(page, f"04_query_{i+1}_error", f"Error for query: {query}")
            results.append({"query": query, "success": False, "error": str(e)})

        # Wait between queries
        page.wait_for_timeout(2000)

    return results

def test_ui_integration(page):
    """Test UI integration and response display"""
    print("\n🧪 Testing UI Integration...")

    try:
        # Check if responses appear in main content area
        main_content_selectors = [
            '.account-analysis',
            '[class*="analysis-result"]',
            '[class*="account-snapshot"]',
            '[class*="recommendation"]'
        ]

        ui_updates = []
        for selector in main_content_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    ui_updates.append(selector)
                    print(f"✅ Main content updated: {selector}")
            except:
                continue

        if not ui_updates:
            print("⚠️  No main content updates detected")

        take_screenshot(page, "05_ui_integration", "UI integration state")

        # Test error handling with invalid account ID
        print("\n🧪 Testing Error Handling...")

        # Look for input field again
        input_field = page.locator('textarea, input[type="text"]').first
        if input_field.is_visible():
            input_field.clear()
            input_field.type("Analyze account INVALID-999 which does not exist")

            # Submit
            input_field.press('Enter')

            page.wait_for_timeout(5000)

            # Check for error messages
            error_selectors = [
                '.error-message',
                '[class*="error"]',
                'text="error"',
                'text="failed"',
                'text="not found"'
            ]

            error_found = False
            for selector in error_selectors:
                try:
                    error_element = page.locator(selector)
                    if error_element.is_visible():
                        error_found = True
                        print(f"✅ Error handling working: {selector}")
                        break
                except:
                    continue

            if not error_found:
                print("⚠️  No explicit error messages found")

            take_screenshot(page, "06_error_handling", "Error handling test")

        return True

    except Exception as e:
        print(f"❌ UI integration test failed: {e}")
        return False

def test_performance(page):
    """Test performance metrics"""
    print("\n🧪 Testing Performance...")

    performance_data = {}

    # Test response times
    start_time = time.time()

    # Look for input field
    input_field = page.locator('textarea, input[type="text"]').first
    if input_field.is_visible():
        input_field.clear()
        input_field.type("Quick performance test: analyze account PERF-001")
        input_field.press('Enter')

        # Measure response time
        response_start = time.time()
        response_received = wait_for_copilot_response(page, timeout=15000)
        response_time = time.time() - response_start

        performance_data['response_time'] = response_time
        performance_data['response_received'] = response_received

        print(f"⏱️  Response time: {response_time:.2f} seconds")

        if response_time < 5:
            print("✅ Excellent response time")
        elif response_time < 10:
            print("✅ Good response time")
        elif response_time < 15:
            print("⚠️  Acceptable response time")
        else:
            print("❌ Slow response time")

    total_time = time.time() - start_time
    performance_data['total_test_time'] = total_time

    print(f"⏱️  Total performance test time: {total_time:.2f} seconds")

    return performance_data

def generate_test_report(test_results):
    """Generate comprehensive test report"""
    print("\n📊 Generating Test Report...")

    report = {
        "test_summary": {
            "timestamp": datetime.now().isoformat(),
            "frontend_url": FRONTEND_URL,
            "backend_url": BACKEND_URL,
            "total_tests_run": len(TEST_QUERIES),
        },
        "results": test_results,
        "screenshots_dir": SCREENSHOT_DIR,
        "responses_dir": RESPONSES_DIR
    }

    # Calculate success rate
    successful_tests = sum(1 for result in test_results if result.get("success", False))
    success_rate = (successful_tests / len(test_results)) * 100 if test_results else 0

    report["test_summary"]["successful_tests"] = successful_tests
    report["test_summary"]["success_rate"] = success_rate

    # Save report
    report_file = f"{TEST_RESULTS_DIR}/test_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    # Generate markdown report
    markdown_report = f"""# Sergas Account Analysis Workflow Test Report

## Test Summary
- **Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Frontend URL**: {FRONTEND_URL}
- **Backend URL**: {BACKEND_URL}
- **Total Tests**: {len(TEST_QUERIES)}
- **Successful Tests**: {successful_tests}
- **Success Rate**: {success_rate:.1f}%

## Test Results

"""

    for i, result in enumerate(test_results, 1):
        status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
        markdown_report += f"### Test {i}: {status}\n"
        markdown_report += f"**Query**: {result.get('query', 'N/A')}\n\n"

        if result.get("success", False):
            markdown_report += f"- **Response Length**: {result.get('response_length', 'N/A')} characters\n"
            markdown_report += f"- **Model Mentioned**: {result.get('has_model_mention', 'N/A')}\n"
            markdown_report += f"- **Account Context**: {result.get('has_account_context', 'N/A')}\n"
        else:
            markdown_report += f"- **Error**: {result.get('error', 'Unknown error')}\n"

        markdown_report += "\n"

    markdown_report += f"""
## Files Generated
- **Screenshots**: {SCREENSHOT_DIR}
- **Response Files**: {RESPONSES_DIR}
- **Detailed JSON Report**: {report_file}

## Recommendations

"""

    if success_rate >= 80:
        markdown_report += "✅ **Overall**: Excellent performance! The account analysis workflow is working well.\n"
    elif success_rate >= 60:
        markdown_report += "⚠️ **Overall**: Good performance with some issues that need attention.\n"
    else:
        markdown_report += "❌ **Overall**: Significant issues found that need to be addressed.\n"

    # Save markdown report
    markdown_file = f"{TEST_RESULTS_DIR}/test_report.md"
    with open(markdown_file, 'w') as f:
        f.write(markdown_report)

    print(f"📋 Test report saved to: {markdown_file}")
    print(f"📊 Detailed JSON report saved to: {report_file}")

    return report_file, markdown_file

def main():
    """Main test execution"""
    print("🚀 Starting Sergas Account Analysis Workflow Testing")
    print("=" * 60)

    setup_directories()

    test_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Enable console logging
            page.on('console', lambda msg: print(f"Browser Console: {msg.text}"))

            # Test 1: Account Analysis Tab Navigation
            tab_success = test_account_analysis_tab_navigation(page)

            # Test 2: CopilotKit Sidebar
            input_field = test_copilotkit_sidebar(page)

            if input_field:
                # Test 3: Account Analysis Queries
                query_results = test_account_analysis_queries(page, input_field)
                test_results.extend(query_results)

                # Test 4: UI Integration
                test_ui_integration(page)

                # Test 5: Performance Testing
                performance_data = test_performance(page)
            else:
                print("❌ Cannot proceed with query tests - input field not found")
                test_results.append({
                    "query": "All tests",
                    "success": False,
                    "error": "CopilotKit input field not found"
                })

        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            test_results.append({
                "query": "Test Suite",
                "success": False,
                "error": str(e)
            })

        finally:
            browser.close()

    # Generate final report
    if test_results:
        generate_test_report(test_results)

    print("\n" + "=" * 60)
    print("🏁 Sergas Account Analysis Workflow Testing Complete!")
    print(f"📁 All results saved to: {TEST_RESULTS_DIR}")

    # Print summary
    successful_tests = sum(1 for result in test_results if result.get("success", False))
    success_rate = (successful_tests / len(test_results)) * 100 if test_results else 0
    print(f"📊 Success Rate: {success_rate:.1f}% ({successful_tests}/{len(test_results)})")

if __name__ == "__main__":
    main()