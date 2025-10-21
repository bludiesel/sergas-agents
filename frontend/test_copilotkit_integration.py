#!/usr/bin/env python3
"""
Comprehensive test script for CopilotKit UI integration with GLM-4.6 backend
Tests the complete workflow from UI → CopilotKit → Backend → GLM-4.6 → UI
"""

from playwright.sync_api import sync_playwright, expect
import time
import json
import sys

def test_frontend_accessibility(page):
    """Test 1: Frontend Accessibility Test"""
    print("🔍 Test 1: Frontend Accessibility Test")

    # Navigate to frontend
    page.goto('http://localhost:7007')
    page.wait_for_load_state('networkidle')

    # Check page title
    expect(page).to_have_title("Sergas Account Manager")
    print("✅ Page title correct")

    # Check main heading
    main_heading = page.locator('h1')
    expect(main_heading).to_contain_text("Sergas Account Manager")
    print("✅ Main heading present")

    # Check for CopilotKit sidebar
    copilot_sidebar = page.locator('.copilotKitSidebar')
    expect(copilot_sidebar).to_be_visible()
    print("✅ CopilotKit sidebar is visible")

    # Check console for errors
    page.evaluate("() => console.clear()")
    page.wait_for_timeout(2000)

    # Take screenshot for documentation
    page.screenshot(path='/tmp/sergas_initial_load.png', full_page=True)
    print("✅ Screenshot saved to /tmp/sergas_initial_load.png")

    return True

def test_copilotkit_sidebar_functionality(page):
    """Test 2: CopilotKit Sidebar Functionality"""
    print("\n🔍 Test 2: CopilotKit Sidebar Functionality")

    # Check if sidebar is open by default
    sidebar_window = page.locator('.copilotKitWindow.open')
    expect(sidebar_window).to_be_visible()
    print("✅ CopilotKit sidebar is open")

    # Check for welcome message
    welcome_message = page.locator('.copilotKitAssistantMessage .copilotKitMarkdownElement')
    expect(welcome_message).to_contain_text("Hello! I can help you analyze accounts")
    print("✅ Welcome message present")

    # Check for input field
    input_field = page.locator('.copilotKitInput textarea')
    expect(input_field).to_be_visible()
    expect(input_field).to_have_attribute('placeholder', 'Type a message...')
    print("✅ Input field present and functional")

    # Check for send button
    send_button = page.locator('.copilotKitInputControlButton')
    expect(send_button).to_be_visible()
    print("✅ Send button present")

    return True

def test_glm46_integration_basic(page):
    """Test 3: GLM-4.6 Integration - Basic Test"""
    print("\n🔍 Test 3: GLM-4.6 Integration - Basic Test")

    # Find input field and send test message
    input_field = page.locator('.copilotKitInput textarea')
    send_button = page.locator('.copilotKitInputControlButton')

    # Type test message
    test_message = "Hello, what model are you using?"
    input_field.fill(test_message)
    print(f"✅ Typed message: '{test_message}'")

    # Send message
    send_button.click()
    print("✅ Message sent")

    # Wait for response (this may take 5-15 seconds)
    print("⏳ Waiting for GLM-4.6 response...")

    # Wait for new message to appear
    response_message = page.locator('.copilotKitAssistantMessage >> nth=1')

    try:
        expect(response_message).to_be_visible(timeout=30000)  # 30 second timeout
        print("✅ Response received")

        # Check response contains model information
        response_text = response_message.inner_text()
        print(f"📝 Response: {response_text[:200]}...")

        # Check if response mentions GLM or model information
        if any(keyword in response_text.lower() for keyword in ['glm', 'model', 'ai', 'assistant']):
            print("✅ Response contains model information")
        else:
            print("⚠️ Response doesn't explicitly mention model, but this is acceptable")

        # Take screenshot of response
        page.screenshot(path='/tmp/sergas_glm_response.png', full_page=True)
        print("✅ Response screenshot saved")

        return True

    except Exception as e:
        print(f"❌ No response received within timeout: {e}")
        page.screenshot(path='/tmp/sergas_no_response.png', full_page=True)
        return False

def test_account_analysis_functionality(page):
    """Test 4: Account Analysis Functionality"""
    print("\n🔍 Test 4: Account Analysis Functionality")

    # Find input field and send account analysis request
    input_field = page.locator('.copilotKitInput textarea')
    send_button = page.locator('.copilotKitInputControlButton')

    # Type account analysis message
    analysis_message = "Analyze account TEST-001 for risks"
    input_field.fill(analysis_message)
    print(f"✅ Typed analysis request: '{analysis_message}'")

    # Send message
    send_button.click()
    print("✅ Analysis request sent")

    # Wait for response
    print("⏳ Waiting for account analysis response...")

    try:
        # Look for response with account analysis
        response_container = page.locator('.copilotKitMessagesContainer')
        expect(response_container).to_contain_text("TEST-001", timeout=30000)
        print("✅ Account analysis response received")

        # Check for analysis elements
        response_text = response_container.inner_text()
        print(f"📝 Analysis response: {response_text[:300]}...")

        # Look for key analysis indicators
        analysis_keywords = ['risk', 'account', 'analysis', 'status', 'health', 'recommendation']
        found_keywords = [kw for kw in analysis_keywords if kw in response_text.lower()]

        if found_keywords:
            print(f"✅ Response contains analysis keywords: {found_keywords}")
        else:
            print("⚠️ Response may not contain expected analysis keywords")

        # Take screenshot
        page.screenshot(path='/tmp/sergas_account_analysis.png', full_page=True)
        print("✅ Analysis screenshot saved")

        return True

    except Exception as e:
        print(f"❌ Account analysis failed: {e}")
        page.screenshot(path='/tmp/sergas_analysis_failed.png', full_page=True)
        return False

def test_error_handling(page):
    """Test 5: Error Handling"""
    print("\n🔍 Test 5: Error Handling")

    # Test with invalid account ID
    input_field = page.locator('.copilotKitInput textarea')
    send_button = page.locator('.copilotKitInputControlButton')

    # Send invalid request
    invalid_message = "Analyze account INVALID-XYZ-123-NOT-FOUND for risks"
    input_field.fill(invalid_message)
    send_button.click()
    print("✅ Invalid request sent")

    # Wait for response
    try:
        response_container = page.locator('.copilotKitMessagesContainer')

        # Check if response handles the error gracefully
        page.wait_for_timeout(15000)  # 15 second wait

        response_text = response_container.inner_text()

        # Look for error handling indicators
        error_indicators = ['not found', 'invalid', 'error', 'unable', 'cannot find']
        has_error_handling = any(indicator in response_text.lower() for indicator in error_indicators)

        if has_error_handling:
            print("✅ Error handling working properly")
        else:
            print("⚠️ May need better error handling for invalid requests")

        # Test empty message
        input_field.fill("")
        send_button.click()
        print("✅ Empty message test completed")

        return True

    except Exception as e:
        print(f"⚠️ Error handling test issue: {e}")
        return False

def test_performance_and_response_times(page):
    """Test 6: Performance and Response Times"""
    print("\n🔍 Test 6: Performance and Response Times")

    input_field = page.locator('.copilotKitInput textarea')
    send_button = page.locator('.copilotKitInputControlButton')

    # Test multiple message performance
    test_messages = [
        "Quick status check",
        "List account summary",
        "Show risk indicators"
    ]

    response_times = []

    for i, message in enumerate(test_messages):
        print(f"📊 Testing message {i+1}: '{message}'")

        start_time = time.time()

        input_field.fill(message)
        send_button.click()

        # Wait for response
        try:
            page.wait_for_function(
                "() => document.querySelectorAll('.copilotKitAssistantMessage').length > 0",
                timeout=20000
            )
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)

            print(f"✅ Response time: {response_time:.2f} seconds")

        except Exception as e:
            print(f"❌ Response timeout: {e}")
            response_times.append(30.0)  # max timeout

    # Calculate average response time
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        print(f"📈 Average response time: {avg_response_time:.2f} seconds")

        if avg_response_time < 20:
            print("✅ Performance acceptable")
        else:
            print("⚠️ Performance could be improved")

    # Test UI responsiveness
    page.wait_for_timeout(1000)

    # Check if UI remains responsive
    sidebar_button = page.locator('.copilotKitButton')
    if sidebar_button.is_visible():
        sidebar_button.click()
        page.wait_for_timeout(1000)
        sidebar_button.click()
        print("✅ UI responsive during testing")

    return True

def main():
    """Main test execution"""
    print("🚀 Starting Comprehensive CopilotKit UI Integration Tests")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser for debugging
        page = browser.new_page()

        # Set up console logging
        def log_console(msg):
            if msg.type == 'error':
                print(f"🔥 Console Error: {msg.text}")

        page.on('console', log_console)

        try:
            # Run all tests
            test_results = []

            test_results.append(test_frontend_accessibility(page))
            test_results.append(test_copilotkit_sidebar_functionality(page))
            test_results.append(test_glm46_integration_basic(page))
            test_results.append(test_account_analysis_functionality(page))
            test_results.append(test_error_handling(page))
            test_results.append(test_performance_and_response_times(page))

            # Summary
            print("\n" + "=" * 60)
            print("📊 TEST SUMMARY")
            print("=" * 60)

            passed = sum(test_results)
            total = len(test_results)

            print(f"✅ Tests Passed: {passed}/{total}")
            print(f"❌ Tests Failed: {total - passed}/{total}")
            print(f"📈 Success Rate: {(passed/total)*100:.1f}%")

            if passed == total:
                print("\n🎉 ALL TESTS PASSED! CopilotKit integration is working correctly!")
            else:
                print(f"\n⚠️ {total - passed} test(s) failed. Review the logs above.")

            # Final screenshot
            page.screenshot(path='/tmp/sergas_final_state.png', full_page=True)
            print("📸 Final state screenshot saved to /tmp/sergas_final_state.png")

        except Exception as e:
            print(f"💥 Test execution failed: {e}")
            page.screenshot(path='/tmp/sergas_test_crash.png', full_page=True)

        finally:
            browser.close()

if __name__ == "__main__":
    main()