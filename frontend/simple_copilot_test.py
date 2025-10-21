#!/usr/bin/env python3
"""
Simple test to debug CopilotKit integration issues
"""

from playwright.sync_api import sync_playwright
import time

def main():
    print("🔍 Debugging CopilotKit Integration")
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

            # Wait a bit for everything to initialize
            page.wait_for_timeout(3000)

            # Check CopilotKit initialization
            copilot_status = page.evaluate("""
                () => {
                    // Check if CopilotKit is properly initialized
                    if (window.copilotKit) {
                        return 'CopilotKit global found';
                    }

                    // Check for React components
                    const messagesContainer = document.querySelector('.copilotKitMessagesContainer');
                    const inputField = document.querySelector('.copilotKitInput textarea');

                    return {
                        messagesContainer: !!messagesContainer,
                        inputField: !!inputField,
                        welcomeMessage: !!document.querySelector('.copilotKitAssistantMessage'),
                        sendButton: !!document.querySelector('.copilotKitInputControlButton')
                    };
                }
            """)

            print(f"📊 CopilotKit Status: {copilot_status}")

            # Try a simple message
            input_field = page.locator('.copilotKitInput textarea')
            if input_field.is_visible():
                print("✅ Input field found, attempting to send message")

                # Type a simple message
                input_field.fill("Test message")
                print("✅ Message typed")

                # Try to send - check if button is enabled
                send_button = page.locator('.copilotKitInputControlButton')
                is_enabled = send_button.is_enabled()
                print(f"📊 Send button enabled: {is_enabled}")

                if is_enabled:
                    send_button.click()
                    print("✅ Message sent")

                    # Wait and check for response
                    page.wait_for_timeout(10000)

                    # Check for any new messages
                    message_count = page.evaluate("""
                        () => document.querySelectorAll('.copilotKitAssistantMessage').length
                    """)
                    print(f"📊 Message count: {message_count}")
                else:
                    print("❌ Send button is disabled")
            else:
                print("❌ Input field not found")

            # Check network requests
            page.wait_for_timeout(5000)

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            page.screenshot(path='/tmp/debug_copilotkit.png', full_page=True)
            print("📸 Debug screenshot saved to /tmp/debug_copilotkit.png")
            browser.close()

if __name__ == "__main__":
    main()