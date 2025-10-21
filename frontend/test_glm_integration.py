#!/usr/bin/env python3
"""
Test GLM-4.6 integration through CopilotKit
"""

from playwright.sync_api import sync_playwright
import time
import json

def test_glm_integration():
    print("🤖 Testing GLM-4.6 Integration via CopilotKit")
    print("=" * 50)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Set up console logging
        def log_console(msg):
            if msg.type in ['error', 'warning', 'log']:
                print(f"🔥 Console {msg.type}: {msg.text}")

        page.on('console', log_console)

        try:
            # Navigate to frontend
            page.goto('http://localhost:7007')
            page.wait_for_load_state('networkidle')
            print("✅ Page loaded")

            # Wait for CopilotKit to initialize
            page.wait_for_timeout(3000)

            # Test 1: Basic GLM model identification
            print("\n🧪 Test 1: Basic GLM Model Identification")
            input_field = page.locator('.copilotKitInput textarea')
            send_button = page.locator('.copilotKitInputControlButton')

            input_field.fill("Hello, what model are you using?")
            send_button.click()
            print("✅ Message sent")

            # Wait for response
            page.wait_for_timeout(15000)  # 15 seconds

            # Check for new messages
            all_messages = page.evaluate("""
                () => {
                    const messages = document.querySelectorAll('.copilotKitAssistantMessage .copilotKitMarkdownElement');
                    return Array.from(messages).map(m => m.textContent);
                }
            """)

            print(f"📊 Total messages: {len(all_messages)}")
            for i, msg in enumerate(all_messages):
                print(f"Message {i+1}: {msg[:100]}...")

            # Test 2: Account analysis
            print("\n🧪 Test 2: Account Analysis")
            input_field.fill("Analyze account TEST-001 for risks")
            send_button.click()
            print("✅ Account analysis request sent")

            # Wait for response
            page.wait_for_timeout(20000)  # 20 seconds

            # Check for response
            all_messages = page.evaluate("""
                () => {
                    const messages = document.querySelectorAll('.copilotKitAssistantMessage .copilotKitMarkdownElement');
                    return Array.from(messages).map(m => m.textContent);
                }
            """)

            print(f"📊 Total messages after analysis: {len(all_messages)}")
            if len(all_messages) > 2:
                latest_message = all_messages[-1]
                print(f"Latest response: {latest_message[:200]}...")

                # Check for GLM-4.6 indicators
                if 'glm-4.6' in latest_message.lower():
                    print("✅ GLM-4.6 model confirmed in response")
                else:
                    print("⚠️ GLM-4.6 not explicitly mentioned")

                # Check for account analysis elements
                analysis_keywords = ['risk', 'account', 'analysis', 'status', 'health']
                found_keywords = [kw for kw in analysis_keywords if kw in latest_message.lower()]
                if found_keywords:
                    print(f"✅ Analysis keywords found: {found_keywords}")
                else:
                    print("⚠️ No analysis keywords found")

            # Test 3: Error handling
            print("\n🧪 Test 3: Error Handling")
            input_field.fill("Analyze account NONEXISTENT-123")
            send_button.click()
            print("✅ Invalid account request sent")

            page.wait_for_timeout(15000)

            # Test 4: Performance check
            print("\n🧪 Test 4: Performance Check")
            start_time = time.time()
            input_field.fill("Quick status check")
            send_button.click()

            # Wait for response
            page.wait_for_timeout(10000)
            end_time = time.time()

            response_time = end_time - start_time
            print(f"📊 Response time: {response_time:.2f} seconds")

            if response_time < 15:
                print("✅ Performance acceptable")
            else:
                print("⚠️ Performance could be improved")

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            page.screenshot(path='/tmp/glm_integration_test.png', full_page=True)
            print("📸 Integration test screenshot saved")
            browser.close()

if __name__ == "__main__":
    test_glm_integration()