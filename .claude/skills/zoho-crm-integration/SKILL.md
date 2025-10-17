---
name: zoho-crm-integration
description: Comprehensive Zoho CRM integration toolkit for working with accounts, contacts, deals, notes, and activities. Use this skill when working with Zoho CRM data via MCP tools or REST APIs, including reading account information, creating/updating records, searching contacts, managing deals, and handling OAuth authentication. Essential for building CRM-integrated agents and automating account management workflows.
---

# Zoho CRM Integration

## Overview

This skill provides comprehensive guidance for integrating with Zoho CRM using both MCP (Model Context Protocol) servers and direct REST API access. It covers authentication, data retrieval, record manipulation, and best practices for building CRM-integrated AI agents.

## When to Use This Skill

Use this skill when:
- Retrieving or updating Zoho CRM data (accounts, contacts, deals, notes, activities)
- Working with Zoho CRM MCP tools
- Building agents that need CRM context
- Implementing OAuth authentication for Zoho
- Performing bulk operations on CRM records
- Setting up change notifications and webhooks

## Available Integration Approaches

### 1. MCP-Based Integration (Recommended for Agents)

MCP tools provide a safe, structured interface for CRM operations with built-in permission controls.

#### Available MCP Tools

**zoho-crm-mcp (Python)**
- `get_contact_by_email_tool` - Look up contacts by email
- `create_contact_tool` - Create new contacts
- `update_contact_tool` - Update contact fields
- `get_deal_by_name_tool` - Search deals by name
- `create_deal_tool` - Create new deals
- `list_open_deals_tool` - List all open deals
- `get_user_info_tool` - Get user profile information

**Official Zoho MCP (Remote)**
- Access via: `npx mcp-remote https://zoho-mcp2-900114980.zohomcp.com/...`
- Provides standardized tools across Zoho apps
- OAuth governance built-in
- Production-ready with official support

### 2. Direct REST API Integration

For operations not covered by MCP tools, use the Zoho CRM REST API (v6+).

## Core Workflows

### Authentication Setup

#### OAuth 2.0 Configuration

1. Register OAuth client in Zoho Developer Console
2. Set required scopes:
   - `ZohoCRM.modules.ALL` - Full module access
   - `ZohoCRM.modules.accounts.READ` - Read accounts
   - `ZohoCRM.modules.accounts.WRITE` - Write accounts
   - `ZohoCRM.users.READ` - Read user info

3. Store credentials securely:
```python
# Use environment variables or secrets manager
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_ACCESS_TOKEN = os.getenv("ZOHO_ACCESS_TOKEN")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
```

#### MCP Server Setup

```bash
# Python MCP server
uvx --from zoho-crm-mcp zoho-mcp

# Or use the official remote endpoint
npx mcp-remote https://zoho-mcp2-900114980.zohomcp.com/[your-endpoint]
```

### Reading Account Data

#### Using MCP Tools
```python
# Search contact by email
contact = await get_contact_by_email_tool("john@example.com")

# Get deal information
deal = await get_deal_by_name_tool("Enterprise Contract Q4")

# List open deals
open_deals = await list_open_deals_tool()
```

#### Using REST API
```python
import requests

# Read accounts with filters
url = "https://www.zohoapis.com/crm/v6/Accounts"
headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
params = {
    "fields": "Account_Name,Owner,Modified_Time",
    "per_page": 200
}
response = requests.get(url, headers=headers, params=params)
accounts = response.json()["data"]

# Get specific account
account_id = "123456789"
url = f"https://www.zohoapis.com/crm/v6/Accounts/{account_id}"
account = requests.get(url, headers=headers).json()
```

### Change Detection

Monitor account updates using modified time filters:

```python
# Get accounts modified in last 24 hours
from datetime import datetime, timedelta

yesterday = (datetime.now() - timedelta(days=1)).isoformat()
params = {
    "criteria": f"Modified_Time:greater_than:{yesterday}"
}
response = requests.get(url, headers=headers, params=params)
```

### Creating and Updating Records

#### Using MCP Tools
```python
# Create contact
await create_contact_tool(
    email="jane@example.com",
    first_name="Jane",
    last_name="Smith",
    account_name="Acme Corp"
)

# Update contact field
await update_contact_tool(
    contact_id="123456789",
    field_name="Phone",
    field_value="+1-555-0123"
)

# Create deal
await create_deal_tool(
    deal_name="Q4 Enterprise License",
    stage="Proposal",
    amount=50000,
    contact_email="jane@example.com"
)
```

#### Using REST API
```python
# Create account
url = "https://www.zohoapis.com/crm/v6/Accounts"
data = {
    "data": [{
        "Account_Name": "New Corp",
        "Website": "newcorp.com",
        "Phone": "+1-555-0199"
    }]
}
response = requests.post(url, headers=headers, json=data)

# Update account
url = f"https://www.zohoapis.com/crm/v6/Accounts/{account_id}"
data = {
    "data": [{
        "Account_Status": "Active",
        "Annual_Revenue": 1000000
    }]
}
response = requests.put(url, headers=headers, json=data)
```

### Working with Notes and Activities

```python
# Add note to account
url = f"https://www.zohoapis.com/crm/v6/Accounts/{account_id}/Notes"
data = {
    "data": [{
        "Note_Title": "Follow-up Required",
        "Note_Content": "Customer requested demo of new features"
    }]
}
response = requests.post(url, headers=headers, json=data)

# Get account activities
url = f"https://www.zohoapis.com/crm/v6/Accounts/{account_id}/Activities"
activities = requests.get(url, headers=headers).json()
```

### Bulk Operations

For large-scale operations:

```python
# Bulk read API
url = "https://www.zohoapis.com/crm/bulk/v6/read"
data = {
    "query": {
        "module": {
            "api_name": "Accounts"
        },
        "fields": ["Account_Name", "Owner", "Modified_Time"]
    }
}
response = requests.post(url, headers=headers, json=data)
job_id = response.json()["data"][0]["details"]["id"]

# Check job status
status_url = f"https://www.zohoapis.com/crm/bulk/v6/read/{job_id}"
status = requests.get(status_url, headers=headers).json()
```

## Security Best Practices

1. **Secrets Management**
   - Never hardcode credentials
   - Use environment variables or secrets manager (AWS Secrets Manager, HashiCorp Vault)
   - Separate credentials for staging and production

2. **Least Privilege**
   - Request only required OAuth scopes
   - Use MCP tool allowlists to restrict agent permissions
   - Implement approval gates for write operations

3. **Rate Limiting**
   - Zoho free tier: 200 API calls/day
   - Paid plans: Higher limits
   - Implement caching for static metadata
   - Use webhooks instead of polling when possible

4. **Data Privacy**
   - Mask sensitive fields in logs
   - Comply with data residency requirements
   - Maintain audit trails for all modifications

## Agent Integration Patterns

### Subagent Tool Permissions

```python
# Data Scout agent (read-only)
allowed_tools = [
    "Read",
    "get_contact_by_email_tool",
    "get_deal_by_name_tool",
    "list_open_deals_tool",
    "get_user_info_tool"
]

# Recommendation Author (write with approval)
allowed_tools = [
    "Write",
    "create_contact_tool",  # Requires approval hook
    "update_contact_tool"   # Requires approval hook
]
```

### Approval Hooks

Implement pre-tool hooks to require human approval for mutations:

```python
def pre_tool_use_hook(tool_name, tool_input):
    if tool_name in ["create_contact_tool", "update_contact_tool", "create_deal_tool"]:
        approval = input(f"Approve {tool_name} with {tool_input}? (y/n): ")
        if approval.lower() != 'y':
            raise PermissionError("User rejected tool execution")
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify OAuth scopes match required operations
   - Check token expiration and refresh
   - Ensure redirect URIs match registration

2. **Rate Limit Errors**
   - Implement exponential backoff
   - Cache frequently accessed data
   - Use bulk APIs for large operations

3. **Data Quality Issues**
   - Validate field API names vs. display names
   - Check required fields before creation
   - Handle duplicate detection appropriately

## Resources

See `references/api_reference.md` for:
- Complete endpoint documentation
- Field mappings for all modules
- Error code reference
- Advanced query examples

See `references/zoho_crm_tooling_reference.md` (project root) for:
- Detailed MCP tool inventory
- Comparison of MCP vs REST approaches
- Integration decision matrix
