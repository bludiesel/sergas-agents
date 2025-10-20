#!/usr/bin/env python3
"""
Direct LiteLLM test with Z.ai GLM-4.6
Based on LITELLM-GLM46-INTEGRATION-GUIDE.md
"""
import os
from litellm import completion

# Set Z.ai credentials
os.environ["ZAI_API_KEY"] = "6845ef1767204ea98a67faaecb3afe08.fyZ4DweXVe3SvCXS"

print("=" * 80)
print("DIRECT LITELLM + Z.AI GLM-4.6 TEST")
print("=" * 80)
print()

print("Configuration:")
print(f"  Model: anthropic/glm-4.6 (ACTUAL MODEL: GLM-4.6, NOT Claude!)")
print(f"  Endpoint: https://api.z.ai/api/anthropic")
print(f"  API Key: {os.getenv('ZAI_API_KEY')[:15]}...")
print()

print("Testing connection...")
try:
    response = completion(
        model="anthropic/glm-4.6",  # Anthropic format (GLM-4.6 runs!)
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What model are you? Answer in one sentence."}
        ],
        api_base="https://api.z.ai/api/anthropic",
        api_key=os.getenv("ZAI_API_KEY"),
        temperature=0.7,
        max_tokens=100
    )

    print("✅ SUCCESS!")
    print()
    print("Response from GLM-4.6:")
    print(f"  {response.choices[0].message.content}")
    print()
    print("Model info:")
    print(f"  Model used: {response.model}")
    print(f"  Tokens: {response.usage.total_tokens}")
    print()
    print("✅ Z.ai GLM-4.6 is working perfectly with LiteLLM!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
