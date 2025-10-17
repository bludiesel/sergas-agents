# Zoho CRM Tooling Reference for Agent Integrations

## 1. Purpose
Summarize the concrete tools/endpoints available for two integration approaches:
- **MCP-based connectors**, where Claude invokes predefined tools that wrap Zoho APIs.
- **Direct REST/SDK access**, where we call Zoho CRM endpoints (v6/v7/v8) to read or modify data.

## 2. MCP Tool Inventories

### 2.1 `zoho-crm-mcp` (Python, SkanderBS2024)
| Tool | Description | Typical Scope |
| --- | --- | --- |
| `get_contact_by_email_tool` | Look up a contact via email, returning metadata (ID, owner, account). | `ZohoCRM.modules.contacts.READ` |
| `create_contact_tool` | Create a contact with basic fields. | `ZohoCRM.modules.contacts.CREATE` |
| `update_contact_tool` | Update a single field on a contact. | `ZohoCRM.modules.contacts.UPDATE` |
| `get_deal_by_name_tool` | Search for a deal by deal name. | `ZohoCRM.modules.deals.READ` |
| `create_deal_tool` | Create deals tied to contacts with stage/amount. | `ZohoCRM.modules.deals.CREATE` |
| `list_open_deals_tool` | Return open deals (stage not closed). | `ZohoCRM.modules.deals.READ` |
| `get_user_info_tool` | Fetch authenticated user profile (owner metadata). | `ZohoCRM.users.READ` |
- Extensible: add modules (Accounts, Notes, Tasks) by defining new handlers in `zoho_mcp/zoho_tools.py` and exposing via `@mcp.tool()`.

### 2.2 `zohocrm-mcpserver` (Node.js/Docker, whiteside-daniel)
| Tool | Description |
| --- | --- |
| `authorize-zoho` | Generates OAuth URL and manages refresh token capture. |
| `list-zoho-modules` | Enumerates modules and API names. |
| `zoho-module-list-fields` | Returns field metadata for a module (labels, API names). |
| `simple-search-zoho-records` | Keyword search within a module (Accounts, Contacts, etc.). |
| `get-zoho-record` | Fetches record by ID in a module. |
- Customize Docker image to add write actions (`create-record`, `update-record`) if needed.

### 2.3 Hosted MCP Integrations
- **Composio Zoho MCP**: exposes high-level tools such as `create_record`, `update_record`, `convert_lead`, `update_related_records`, `get_records`, `create_tag`. Good for quick prototyping; Composio handles auth.
- **Zapier MCP for Zoho CRM**: provides access to Zapier actions (create/update records, add attachments, convert leads). Supports write operations but comes with task quotas.
- **Knit MCP Server**: curated tool catalog with live schema search; supports read/write and can mix APIs from multiple systems.
- **CData Zoho MCP** (beta): read-only server using JDBC driver; paid beta offers CRUD.
- **Zoho MCP (official, early access)**: currently accessible via the provided remote endpoint; offers standardized tools across Zoho apps with OAuth governance and is the recommended starting point.

## 3. Direct REST/SDK Endpoint Catalog (Zoho CRM v6–v8)

### 3.1 Core Records Modules
| Module | Read Endpoints | Write Endpoints | Notes |
| --- | --- | --- | --- |
| Accounts | `GET /crm/v{n}/Accounts`, `GET /Accounts/{id}` | `POST /Accounts`, `PUT /Accounts/{id}`, `DELETE /Accounts/{id}` | Supports filters (`lastModifiedTime`), COQL, bulk ops. |
| Contacts | `GET /Contacts`, `GET /Contacts/{id}` | `POST /Contacts`, `PUT /Contacts/{id}`, `DELETE /Contacts/{id}` | Map contacts to accounts via `Account_Name`. |
| Deals | `GET /Deals`, `GET /Deals/{id}` | `POST /Deals`, `PUT /Deals/{id}`, `DELETE /Deals/{id}` | Includes stages, pipeline support. |
| Leads | `GET /Leads` | `POST /Leads`, `PUT /Leads/{id}`, `POST /Leads/{id}/actions/convert` | Convert to Accounts/Contacts/Deals. |
| Tasks/Events/Calls | `GET /Tasks`, etc. | `POST /Tasks`, `PUT /Tasks/{id}` | Manage activities assigned to owners. |

### 3.2 Related Lists & Notes
| Function | Endpoint |
| --- | --- |
| List related records | `GET /{module}/{record_id}/{related_list}` (e.g., notes, activities) |
| Add related record | `POST /{module}/{record_id}/{related_list}` |
| Notes CRUD | `GET /Notes`, `POST /Notes`, `POST /{module}/{record_id}/Notes`, `PUT /Notes/{id}`, `DELETE /Notes/{id}` |
| Attachments | `GET /{module}/{id}/Attachments`, `POST /{module}/{id}/Attachments`, `DELETE /{module}/{id}/Attachments/{attachment_id}` |

### 3.3 Search & Query
- **Search API**: `GET /crm/v{n}/search?module=Accounts&criteria=(Account_Name:equals:Acme)`; supports partial search, `email`, `phone`, etc.
- **COQL (SQL-like)**: `POST /crm/v{n}/coql` with `select` statements for complex filters.
- **API Discovery**: `GET /crm/v{n}/__apis` to list available endpoints with filters.

### 3.4 Bulk & Composite
- **Bulk Read**: `POST /bulk/v{n}/read` to export large datasets; `GET /bulk/v{n}/read/{job_id}` to monitor.
- **Bulk Write**: `POST /bulk/v{n}/write` for batch inserts/updates.
- **Composite API**: `POST /crm/v{n}/composite` to combine up to five sub-requests with dependencies.

### 3.5 Automation Hooks
- **Notification API**: `POST /crm/v{n}/actions/watch` to subscribe to module changes; agent receives callbacks when records change.
- **Functions (Deluge)**: create serverless functions invoked via `POST /crm/v{n}/functions/{function_name}/actions/execute`.
- **Schedules/Webhooks**: configure within Zoho to trigger outbound calls for sync jobs.

### 3.6 SDKs & OpenAPI
- Official SDKs (Python, Java, Node, PHP, .NET) wrap the endpoints with token handling and model classes.
- OpenAPI specs (`zohocorp-pvt-ltd/crm-oas`) enable auto-generation for custom clients.

## 4. Choosing Between MCP Tools and REST Endpoints
| Consideration | MCP Tooling | REST/SDK |
| --- | --- | --- |
| Setup Speed | Fast (tools pre-defined) | More setup (build service) |
| Coverage | Limited to exposed tools (extendable) | Full API surface (Accounts, custom modules, bulk) |
| Permissions | Fine-grained per tool (allowed/disallowed) | Must enforce in code |
| Maintenance | Need to host MCP server & update tools | Need to manage API client, token refresh, retries |
| Agent Safety | Built-in allowlists, easier approval gating | Requires custom guards |

## 5. Next Steps for Sergas
1. Select base MCP server (Python or Node) and extend tools for Accounts, Deals, Notes, Tasks (read/write).
2. Document mapping between MCP tool inputs and underlying REST endpoints for auditing.
3. For operations not covered by MCP (bulk sync, advanced analytics), implement REST/SDK service with shared OAuth credentials and queueing.
4. Maintain scopes registry to ensure least-privilege access for both the MCP and direct API clients.

---
This reference will evolve as MCP offerings expand and as we extend custom tooling for Sergas agents.
