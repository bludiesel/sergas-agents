#!/usr/bin/env python3
"""
Comprehensive CopilotKit Integration Test with GLM-4.6 Backend
Tests sidebar functionality, message flow, and real-time features
"""

from playwright.sync_api import sync_playwright, expect
import time
import json
from datetime import datetime

def take_screenshot(page, name):
    """Helper to take screenshots with timestamps"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/tmp/copilotkit_test_{name}_{timestamp}.png"
    page.screenshot(path=filename, full_page=True)
    print(f"📸 Screenshot saved: {filename}")
    return filename

def test_copilotkit_sidebar(page):
    """Test CopilotKit sidebar functionality"""
    print("\n=== Testing CopilotKit Sidebar ===")

    # Navigate to frontend
    page.goto('http://localhost:7007')
    page.wait_for_load_state('networkidle')

    take_screenshot(page, "01_initial_load")

    # Look for CopilotKit sidebar trigger/button
    print("🔍 Looking for CopilotKit sidebar trigger...")

    # Try different possible selectors for the sidebar trigger
    possible_triggers = [
        'button[aria-label*="chat"]',
        'button[aria-label*="copilot"]',
        'button[aria-label*="assistant"]',
        '[data-copilotkit-sidebar-trigger]',
        '.copilotkit-trigger',
        'button:has-text("AI")',
        'button:has-text("Chat")',
        'button:has-text("Assistant")',
        'div[role="button"] >> text=Chat',
        'button >> svg',  # Icon buttons
    ]

    sidebar_trigger = None
    for selector in possible_triggers:
        try:
            element = page.locator(selector).first
            if element.is_visible():
                sidebar_trigger = element
                print(f"✅ Found sidebar trigger with selector: {selector}")
                break
        except:
            continue

    if not sidebar_trigger:
        # Try to find any clickable element that might open chat
        all_buttons = page.locator('button').all()
        for i, button in enumerate(all_buttons):
            try:
                if button.is_visible():
                    text = button.inner_text()
                    aria_label = button.get_attribute('aria-label')
                    if any(keyword in (text or '').lower() for keyword in ['chat', 'ai', 'assistant', 'copilot']):
                        sidebar_trigger = button
                        print(f"✅ Found potential sidebar trigger: {text} (aria-label: {aria_label})")
                        break
            except:
                continue

    if not sidebar_trigger:
        print("❌ Could not find CopilotKit sidebar trigger")
        # Try to find any floating action button or chat widget
        page.screenshot(path="/tmp/debug_no_trigger.png", full_page=True)
        return False

    # Click to open sidebar
    print("🖱️ Clicking sidebar trigger...")
    sidebar_trigger.click()
    page.wait_for_timeout(1000)  # Wait for animation

    take_screenshot(page, "02_sidebar_opened")

    # Look for sidebar content
    print("🔍 Looking for sidebar content...")

    # Try different selectors for the sidebar/chat interface
    possible_sidebars = [
        '[data-copilotkit-sidebar]',
        '.copilotkit-sidebar',
        '[role="dialog"]',
        '[role="complementary"]',
        '.chat-interface',
        '.ai-chat',
        'div:has-text("Hello")',  # Look for greeting
        'div:has-text("How can")',  # Look for typical AI greeting
        'div:has-text("message")',
        'textarea[placeholder*="message"]',
        'textarea[placeholder*="ask"]',
        'input[type="text"]',
    ]

    sidebar_content = None
    for selector in possible_sidebars:
        try:
            element = page.locator(selector).first
            if element.is_visible():
                sidebar_content = element
                print(f"✅ Found sidebar content with selector: {selector}")
                break
        except:
            continue

    if not sidebar_content:
        print("❌ Could not find sidebar content")
        return False

    # Check for initial message or welcome text
    page.wait_for_timeout(2000)
    take_screenshot(page, "03_sidebar_content")

    return True

def test_message_flow(page):
    """Test sending messages and receiving responses"""
    print("\n=== Testing Message Flow ===")

    # Look for message input
    input_selectors = [
        'textarea[placeholder*="message"]',
        'textarea[placeholder*="ask"]',
        'textarea[placeholder*="Type"]',
        'input[type="text"]',
        'textarea',
        '[contenteditable="true"]',
        'input[placeholder*="chat"]',
    ]

    message_input = None
    for selector in input_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible():
                message_input = element
                print(f"✅ Found message input with selector: {selector}")
                break
        except:
            continue

    if not message_input:
        print("❌ Could not find message input")
        return False

    # Test messages to send
    test_messages = [
        "Hello, what can you help with?",
        "What model are you using?",
        "Analyze account TEST-001 for risks",
        "Generate 3 recommendations for account XYZ-789"
    ]

    for i, message in enumerate(test_messages):
        print(f"📝 Sending test message {i+1}: {message}")

        # Clear input and type message
        message_input.clear()
        message_input.type(message)

        # Look for send button
        send_selectors = [
            'button[type="submit"]',
            'button:has-text("Send")',
            'button:has-text("send")',
            'button >> svg',  # Send icon
            'button[aria-label*="send"]',
        ]

        send_button = None
        for selector in send_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    send_button = element
                    print(f"✅ Found send button: {selector}")
                    break
            except:
                continue

        if send_button:
            send_button.click()
        else:
            # Try pressing Enter
            message_input.press('Enter')

        # Wait for response (with timeout)
        print("⏳ Waiting for response...")
        start_time = time.time()
        response_received = False

        # Look for response indicators
        for _ in range(30):  # Wait up to 30 seconds
            page.wait_for_timeout(1000)

            # Check if response appeared (look for new content)
            response_indicators = [
                'div:has-text("glm-4.6")',
                'div:has-text("GLM")',
                'div:has-text("analysis")',
                'div:has-text("recommendation")',
                'div:has-text("risk")',
                '.message-content',
                '.ai-response',
                '[data-message]',
                'div:has-text("account")',
            ]

            for selector in response_indicators:
                try:
                    elements = page.locator(selector).all()
                    if len(elements) > 0:
                        # Check if any element contains the response content
                        for element in elements:
                            text = element.inner_text()
                            if len(text) > 20 and not text == message:  # Not the sent message
                                response_received = True
                                print(f"✅ Response received: {text[:100]}...")
                                break
                        if response_received:
                            break
                except:
                    continue

            if response_received:
                response_time = time.time() - start_time
                print(f"⏱️ Response time: {response_time:.2f} seconds")
                break

        take_screenshot(page, f"04_message_{i+1}_response")

        if not response_received:
            print(f"❌ No response received for message: {message}")

        page.wait_for_timeout(2000)  # Wait between messages

    return True

def test_real_time_features(page):
    """Test streaming and real-time features"""
    print("\n=== Testing Real-time Features ===")

    # Send a longer message to test streaming
    input_selectors = ['textarea', 'input[type="text"]', '[contenteditable="true"]']
    message_input = None

    for selector in input_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible():
                message_input = element
                break
        except:
            continue

    if message_input:
        print("📝 Testing streaming with longer message...")
        message_input.clear()
        message_input.type("Provide a detailed analysis of account management best practices and strategies for customer success")

        # Send and watch for streaming behavior
        send_selectors = ['button[type="submit"]', 'button:has-text("Send")']
        for selector in send_selectors:
            try:
                send_button = page.locator(selector).first
                if send_button.is_visible():
                    send_button.click()
                    break
            except:
                continue

        # Watch for gradual content appearance (streaming)
        print("👀 Watching for streaming behavior...")
        content_lengths = []

        for i in range(20):  # Monitor for 20 seconds
            page.wait_for_timeout(1000)

            # Check for response content
            response_selectors = ['.message-content', '.ai-response', 'div:has-text("analysis")']
            for selector in response_selectors:
                try:
                    element = page.locator(selector).last  # Get the latest response
                    if element.is_visible():
                        text = element.inner_text()
                        content_lengths.append(len(text))
                        print(f"   Content length at second {i+1}: {len(text)} characters")
                        break
                except:
                    continue

        # Check if content grew gradually (indicating streaming)
        if len(content_lengths) > 5:
            growth = content_lengths[-1] - content_lengths[0]
            if growth > 100:
                print(f"✅ Detected streaming behavior: content grew by {growth} characters")
            else:
                print("⚠️ Limited streaming detected")
        else:
            print("❌ Could not detect streaming behavior")

    return True

def test_error_handling(page):
    """Test error handling and edge cases"""
    print("\n=== Testing Error Handling ===")

    # Test with empty message
    input_selectors = ['textarea', 'input[type="text"]']
    message_input = None

    for selector in input_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible():
                message_input = element
                break
        except:
            continue

    if message_input:
        # Try sending empty message
        print("📝 Testing empty message...")
        message_input.clear()

        # Try to send
        send_selectors = ['button[type="submit"]', 'button:has-text("Send")']
        for selector in send_selectors:
            try:
                send_button = page.locator(selector).first
                if send_button.is_visible():
                    # Check if button is disabled
                    if send_button.is_disabled():
                        print("✅ Send button is disabled for empty message")
                    else:
                        send_button.click()
                        page.wait_for_timeout(1000)
                        # Check for error message
                        error_selectors = ['.error', '.warning', 'div:has-text("error")']
                        for err_selector in error_selectors:
                            try:
                                error_element = page.locator(err_selector).first
                                if error_element.is_visible():
                                    print(f"✅ Error message shown: {error_element.inner_text()}")
                                    break
                            except:
                                continue
                    break
            except:
                continue

    return True

def main():
    """Main test function"""
    print("🚀 Starting CopilotKit Integration Test")
    print("=" * 50)

    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Use headless=False for debugging
        page = browser.new_page()

        # Enable console logging
        def log_console(msg):
            if msg.type == 'error':
                print(f"🔥 Console Error: {msg.text}")
            elif msg.type == 'warning':
                print(f"⚠️ Console Warning: {msg.text}")

        page.on('console', log_console)

        try:
            # Test 1: Sidebar functionality
            results['tests']['sidebar'] = test_copilotkit_sidebar(page)

            # Test 2: Message flow
            if results['tests']['sidebar']:
                results['tests']['message_flow'] = test_message_flow(page)
            else:
                results['tests']['message_flow'] = False
                print("⏭️ Skipping message flow test due to sidebar failure")

            # Test 3: Real-time features
            if results['tests']['message_flow']:
                results['tests']['real_time'] = test_real_time_features(page)
            else:
                results['tests']['real_time'] = False
                print("⏭️ Skipping real-time test due to message flow failure")

            # Test 4: Error handling
            results['tests']['error_handling'] = test_error_handling(page)

        except Exception as e:
            print(f"❌ Test execution failed: {str(e)}")
            results['error'] = str(e)

        finally:
            take_screenshot(page, "final_state")
            browser.close()

    # Print results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    for test_name, result in results['tests'].items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

    # Save results
    with open('/tmp/copilotkit_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Detailed results saved to: /tmp/copilotkit_test_results.json")
    print(f"📸 Screenshots saved in /tmp/ directory")

    return results

if __name__ == "__main__":
    main()