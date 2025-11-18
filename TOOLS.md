# Bridge-MCP - Tool Reference

This document describes all the available tools in Bridge-MCP.

## Authentication
Bridge-MCP uses token-based authentication for all integrations:
- **Jira**: Personal Access Token (PAT) — Set `JIRA_PERSONAL_ACCESS_TOKEN` in your environment
- **GitLab** (coming soon): Personal Access Token — Set `GITLAB_PERSONAL_ACCESS_TOKEN`
- **Confluence** (coming soon): API Token — Set `CONFLUENCE_API_TOKEN`

Username/password authentication is not used for security reasons.

## Jira Tools

## Tool: get_jira_issue

Get detailed information about a specific Jira issue by its key.

### Parameters

- `issue_key` (string, required): The Jira issue key (e.g., "BAL-7437", "PROJ-123")

### Example Usage

```
Get details for issue BAL-7437
```

### Returns

A formatted text response with:
- Issue key and summary
- Status, priority, and type
- URL to the issue
- Full description
- Created and updated timestamps
- Reporter and assignee information
- Project details
- Components (if any)
- Labels (if any)
- Fix versions (if any)
- Resolution (if resolved)
- Due date (if set)

### Example Output

```
# BAL-7437: Implement user authentication

**Status:** In Progress
**Priority:** High
**Type:** Story

**URL:** https://your-jira-instance.com/browse/BAL-7437

## Description
As a user, I want to be able to log in to the system...

## Details
- **Created:** 2025-11-01T10:30:00.000+0330
- **Updated:** 2025-11-15T14:20:00.000+0330
- **Reporter:** John Doe
- **Assignee:** Jane Smith
- **Project:** Balance (BAL)

**Components:** Backend, Authentication
**Labels:** security, mvp
```

---

## Tool: search_jira_issues

Search for Jira issues using JQL (Jira Query Language).

### Parameters

- `jql` (string, required): JQL query string
- `max_results` (number, optional): Maximum number of results to return (default: 50)

### Example Usage

```
Search for all open issues in project BAL assigned to me
```

This translates to JQL: `project = BAL AND status = Open AND assignee = currentUser()`

### JQL Examples

Common JQL patterns you can use:

```jql
# All issues in a project
project = BAL

# Open issues
project = BAL AND status = Open

# High priority bugs
project = BAL AND priority = High AND type = Bug

# Recently created issues
project = BAL AND created >= -7d

# Issues assigned to a specific user
assignee = "john.doe"

# Issues updated in the last week
updated >= -1w

# Issues with specific labels
labels = "urgent"

# Multiple conditions
project = BAL AND status IN (Open, "In Progress") AND priority = High
```

### Returns

A list of matching issues with:
- Issue key and summary
- Status
- Priority
- Assignee
- URL to each issue

### Example Output

```
# Search Results (15 issues)

**Query:** project = BAL AND status = Open

## BAL-7437: Implement user authentication
- **Status:** Open
- **Priority:** High
- **Assignee:** Jane Smith
- **URL:** https://your-jira-instance.com/browse/BAL-7437

## BAL-7438: Fix login bug
- **Status:** Open
- **Priority:** Medium
- **Assignee:** Unassigned
- **URL:** https://your-jira-instance.com/browse/BAL-7438

...
```

---

## Tool: get_issue_comments

Get all comments for a specific Jira issue.

### Parameters

- `issue_key` (string, required): The Jira issue key (e.g., "BAL-7437")

### Example Usage

```
Show me all comments on BAL-7437
```

### Returns

A list of all comments with:
- Comment number
- Author name
- Created timestamp
- Updated timestamp
- Comment body text

### Example Output

```
# Comments for BAL-7437 (3 comments)

## Comment 1
**Author:** John Doe
**Created:** 2025-11-01T11:00:00.000+0330
**Updated:** 2025-11-01T11:00:00.000+0330

This looks good. We should also consider adding two-factor authentication.

---

## Comment 2
**Author:** Jane Smith
**Created:** 2025-11-02T09:30:00.000+0330
**Updated:** 2025-11-02T09:30:00.000+0330

Good idea. I'll add that to the scope.

---

## Comment 3
**Author:** Admin User
**Created:** 2025-11-10T14:00:00.000+0330
**Updated:** 2025-11-10T14:00:00.000+0330

Status update: Development is 70% complete.

---
```

---

## Tool: get_issue_attachments

Get all attachments for a specific Jira issue.

### Parameters

- `issue_key` (string, required): The Jira issue key (e.g., "BAL-7437")

### Example Usage

```
List all attachments for BAL-7437
```

### Returns

A list of all attachments with:
- Filename
- File size in bytes
- MIME type
- Author who uploaded it
- Upload timestamp
- Download URL

### Example Output

```
# Attachments for BAL-7437 (2 files)

## authentication-flow.png
- **Size:** 524288 bytes
- **Type:** image/png
- **Author:** Jane Smith
- **Created:** 2025-11-01T12:00:00.000+0330
- **URL:** https://your-jira-instance.com/secure/attachment/12345/authentication-flow.png

## requirements.pdf
- **Size:** 1048576 bytes
- **Type:** application/pdf
- **Author:** John Doe
- **Created:** 2025-11-02T10:00:00.000+0330
- **URL:** https://your-jira-instance.com/secure/attachment/12346/requirements.pdf
```

---

## Common Use Cases

### 1. Daily Standup Preparation

```
Show me all issues assigned to me that were updated in the last 24 hours
```

Claude will construct a JQL query and fetch the results.

### 2. Sprint Review

```
Find all completed issues in the BAL project from the last 2 weeks
```

### 3. Bug Triage

```
Show me all unassigned high-priority bugs in project BAL
```

### 4. Issue Investigation

```
Get full details for BAL-7437 including comments and attachments
```

Claude can chain multiple tool calls to gather all information.

### 5. Team Workload

```
How many open issues does each person have in project BAL?
```

Claude can search and analyze the results.

---

## Tips and Best Practices

### 1. Natural Language

You don't need to know JQL syntax. Just ask in natural language:
- "Show me open bugs"
- "Find issues I created last week"
- "What issues are in review?"

Claude will translate to appropriate JQL queries.

### 2. Combining Information

You can ask for multiple pieces of information:
```
Get details for BAL-7437 and show me all its comments
```

Claude will make multiple tool calls automatically.

### 3. Filtering Results

If you get too many results, ask for refinement:
```
Show me only the high-priority ones
```

### 4. Time-Based Queries

Use relative time expressions:
- "last week"
- "yesterday"
- "this month"
- "in the last 3 days"

### 5. Project Context

Once you mention a project, Claude remembers it:
```
Show me open issues in BAL
Now show me the closed ones
And the ones updated today
```

---

## Limitations

### Current Limitations

1. **Read-Only**: This server only reads data, it cannot:
   - Create issues
   - Update issues
   - Add comments
   - Change status
   - Assign issues

2. **VPN Required**: You must be connected to your VPN (e.g., FortiClient) to access your private Jira instance

3. **Authentication**: Uses Personal Access Token (PAT), not OAuth

4. **Rate Limiting**: Respects Jira's rate limits (usually not an issue for read operations)

### Future Enhancements

Potential features for future versions:
- Write operations (create, update issues)
- Bulk operations
- Custom field support
- Board and sprint information
- Agile metrics
- Caching for better performance
- Webhook support for real-time updates

---

## Troubleshooting

### "Error: Jira client not initialized"

The server couldn't connect to Jira. Check:
1. VPN connection is active
2. PAT is correct in configuration
3. Jira server is accessible

### "Error fetching issue"

The specific issue couldn't be retrieved. Possible reasons:
1. Issue doesn't exist
2. You don't have permission to view it
3. Issue key is misspelled
4. Network connectivity issues

### "No issues found matching query"

Your search returned no results. Try:
1. Simplifying the JQL query
2. Checking if the project key is correct
3. Verifying the status values exist
4. Removing some filters

### SSL Certificate Errors

If you see SSL/certificate errors:
1. Verify VPN is connected
2. Check if the Jira URL is correct
3. You may need to disable SSL verification (see QUICKSTART.md)

---

## Advanced JQL Reference

### Operators

- `=` : equals
- `!=` : not equals
- `>`, `<`, `>=`, `<=` : comparison
- `IN` : in list
- `NOT IN` : not in list
- `~` : contains text
- `IS EMPTY` : field is empty
- `IS NOT EMPTY` : field has value

### Functions

- `currentUser()` : the logged-in user
- `now()` : current date/time
- `-1w`, `-7d`, `-1h` : relative time

### Fields

Common fields you can use:
- `project`
- `status`
- `priority`
- `assignee`
- `reporter`
- `created`
- `updated`
- `resolved`
- `type` (or `issuetype`)
- `labels`
- `component`
- `fixVersion`
- `description`
- `summary`

### Examples

```jql
# Complex query
project = BAL 
  AND status IN (Open, "In Progress") 
  AND priority IN (High, Highest) 
  AND assignee = currentUser() 
  AND created >= -30d
  ORDER BY priority DESC, created DESC

# Issues without assignee
project = BAL AND assignee IS EMPTY

# Issues with specific text
project = BAL AND summary ~ "authentication"

# Recently resolved issues
project = BAL AND resolved >= -7d

# Overdue issues
project = BAL AND duedate < now() AND status != Done
```

---

## API Reference

If you want to use the server programmatically or understand its internals, here's the technical reference:

### MCP Protocol

The server implements the Model Context Protocol (MCP) standard:
- Communicates via stdio
- Uses JSON-RPC 2.0
- Supports async operations

### Tool Definitions

Each tool is defined with:
- `name`: Unique identifier
- `description`: What the tool does
- `inputSchema`: JSON Schema for parameters

### Return Format

All tools return a sequence of `TextContent` objects with markdown-formatted text.

### Error Handling

Errors are returned as text content with descriptive messages, not as exceptions to the MCP client.
