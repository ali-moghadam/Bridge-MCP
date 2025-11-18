# Bridge-MCP - Tool Reference

This document describes all the available tools in Bridge-MCP.

## Authentication
Bridge-MCP uses token-based authentication for all integrations:
- **Jira**: Personal Access Token (PAT) — Set `JIRA_PERSONAL_ACCESS_TOKEN` in your environment
- **GitLab**: Personal Access Token — Set `GITLAB_PERSONAL_ACCESS_TOKEN` (requires `api`, `read_api`, and `read_repository` scopes)
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

## Tool: get_issue_media

Download and display images and videos attached to a Jira issue.

### Parameters

- `issue_key` (string, required): The Jira issue key (e.g., "BAL-7437")
- `max_files` (number, optional): Maximum number of media files to return (default: 10)

### Example Usage

```
Show me the images from issue BAL-7437
```

### Returns

Inline image content for all image and video attachments on the issue. Supported formats include PNG, JPEG, GIF, MP4, and WebM.

---

## GitLab Tools

## Tool: get_gitlab_project

Get detailed information about a GitLab project by its ID or path.

### Parameters

- `project_id` (string, required): The project ID (numeric) or path (e.g., 'group/project', 'username/repo')

### Example Usage

```
Get details for GitLab project mygroup/myproject
```

### Returns

A formatted response with:
- Project ID, name, and path
- Description
- Web URL
- Default branch
- Visibility (public/private/internal)
- Creation and last activity dates
- Star and fork counts

### Example Output

```
# Project: awesome-project

**ID:** 12345
**Path:** mygroup/awesome-project
**Description:** An awesome project for building amazing things

**Details:**
- **URL:** https://gitlab.com/mygroup/awesome-project
- **Default Branch:** main
- **Visibility:** private
- **Created:** 2024-01-15T10:30:00.000Z
- **Last Activity:** 2025-11-18T09:45:00.000Z
- **Stars:** 42
- **Forks:** 7
```

---

## Tool: list_gitlab_projects

List GitLab projects accessible to the authenticated user.

### Parameters

- `owned` (boolean, optional): List only owned projects (default: false)
- `search` (string, optional): Search projects by name
- `max_results` (number, optional): Maximum number of projects to return (default: 20)

### Example Usage

```
List my GitLab projects
Show all projects containing "backend" in the name
```

### Returns

A list of projects with basic information including ID, name, path, description, and URL.

---

## Tool: get_merge_request

Get detailed information about a specific merge request.

### Parameters

- `project_id` (string, required): The project ID or path
- `mr_iid` (number, required): The merge request IID (internal ID shown in GitLab UI)

### Example Usage

```
Show me details for merge request !123 in project mygroup/myproject
```

### Returns

A formatted response with:
- MR title and description
- State (opened, merged, closed)
- Author and assignees
- Source and target branches
- Web URL
- Creation and update timestamps
- Merge status and pipeline status
- Labels and milestone

### Example Output

```
# MR !123: Add user authentication feature

**State:** opened
**Author:** Jane Smith
**Assignees:** John Doe, Alice Johnson

**Branches:**
- **Source:** feature/user-auth
- **Target:** main

**Status:**
- **Mergeable:** Yes
- **Pipeline:** passed

**URL:** https://gitlab.com/mygroup/myproject/-/merge_requests/123

**Created:** 2025-11-15T10:30:00.000Z
**Updated:** 2025-11-18T14:20:00.000Z

## Description
This MR implements user authentication using JWT tokens...

**Labels:** authentication, security, backend
**Milestone:** v2.0
```

---

## Tool: list_merge_requests

List merge requests for a project.

### Parameters

- `project_id` (string, required): The project ID or path
- `state` (string, optional): Filter by state: 'opened', 'closed', 'merged', or 'all' (default: 'opened')
- `max_results` (number, optional): Maximum number of MRs to return (default: 20)

### Example Usage

```
Show all open merge requests for mygroup/myproject
List recently merged MRs in project 12345
```

### Returns

A list of merge requests with key information including IID, title, state, author, and URL.

---

## Tool: list_pipelines

List CI/CD pipelines for a project.

### Parameters

- `project_id` (string, required): The project ID or path
- `ref` (string, optional): Filter by git ref (branch/tag name)
- `status` (string, optional): Filter by status: 'running', 'pending', 'success', 'failed', 'canceled'
- `max_results` (number, optional): Maximum number of pipelines to return (default: 20)

### Example Usage

```
Show failed pipelines for mygroup/myproject
List all pipelines running on the main branch
```

### Returns

A list of pipelines with ID, status, ref (branch/tag), web URL, and creation timestamp.

### Example Output

```
# Pipelines for mygroup/myproject (10 results)

## Pipeline #54321
- **Status:** success
- **Ref:** main
- **Created:** 2025-11-18T09:30:00.000Z
- **URL:** https://gitlab.com/mygroup/myproject/-/pipelines/54321

## Pipeline #54320
- **Status:** failed
- **Ref:** feature/new-api
- **Created:** 2025-11-17T16:45:00.000Z
- **URL:** https://gitlab.com/mygroup/myproject/-/pipelines/54320
```

---

## Tool: get_pipeline

Get detailed information about a specific pipeline including all jobs.

### Parameters

- `project_id` (string, required): The project ID or path
- `pipeline_id` (number, required): The pipeline ID

### Example Usage

```
Show details for pipeline 54321 in project mygroup/myproject
```

### Returns

Detailed pipeline information including:
- Pipeline ID, status, and ref
- Web URL
- Creation and update timestamps
- All jobs in the pipeline with their statuses

### Example Output

```
# Pipeline #54321

**Status:** success
**Ref:** main
**URL:** https://gitlab.com/mygroup/myproject/-/pipelines/54321

**Created:** 2025-11-18T09:30:00.000Z
**Updated:** 2025-11-18T09:45:00.000Z

## Jobs:
1. **build** - success
2. **test** - success
3. **lint** - success
4. **deploy** - success
```

---

## Tool: list_gitlab_issues

List issues for a GitLab project.

### Parameters

- `project_id` (string, required): The project ID or path
- `state` (string, optional): Filter by state: 'opened' or 'closed' (default: 'opened')
- `max_results` (number, optional): Maximum number of issues to return (default: 20)

### Example Usage

```
Show open issues in mygroup/myproject
List closed issues for project 12345
```

### Returns

A list of issues with IID, title, state, author, assignees, and URL.

---

## Tool: get_gitlab_issue

Get detailed information about a specific GitLab issue.

### Parameters

- `project_id` (string, required): The project ID or path
- `issue_iid` (number, required): The issue IID (internal ID shown in GitLab UI)

### Example Usage

```
Show details for issue #456 in project mygroup/myproject
```

### Returns

Detailed issue information including:
- Issue title and description
- State (opened/closed)
- Author and assignees
- Labels and milestone
- Web URL
- Creation and update timestamps
- Due date (if set)

### Example Output

```
# Issue #456: Fix login bug

**State:** opened
**Author:** John Doe
**Assignees:** Jane Smith

**Labels:** bug, high-priority
**Milestone:** v2.1

**URL:** https://gitlab.com/mygroup/myproject/-/issues/456

**Created:** 2025-11-16T10:00:00.000Z
**Updated:** 2025-11-18T15:30:00.000Z
**Due Date:** 2025-11-20

## Description
Users are unable to log in when using special characters in their password...
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

### 6. Code Review Preparation

```
Show me all open merge requests for mygroup/backend-service
Get details for MR !123 in mygroup/backend-service
```

### 7. Pipeline Monitoring

```
Show me failed pipelines for mygroup/frontend
Check the status of pipeline 54321
```

### 8. Release Planning

```
List all merged MRs for project mygroup/api since last week
Show me closed issues in mygroup/mobile-app
```

### 9. CI/CD Investigation

```
Show me all pipelines running on the main branch
Get details for the latest pipeline in mygroup/service
```

### 10. Project Overview

```
Get details for GitLab project mygroup/awesome-app
List all my GitLab projects
```

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

### 6. GitLab Project Paths

For GitLab, you can use either numeric IDs or project paths:
- Numeric ID: `12345`
- Project path: `mygroup/myproject` or `username/repo`

Paths are usually easier to remember and use.

### 7. MR and Issue IDs

GitLab uses IIDs (internal IDs) for merge requests and issues:
- When you see `!123` in GitLab UI, use `123` as the `mr_iid`
- When you see `#456` in GitLab UI, use `456` as the `issue_iid`

### 8. Pipeline Filtering

When monitoring pipelines, use status filters to focus on what matters:
- `failed` - Quickly identify broken builds
- `running` - See what's currently in progress
- `success` - Verify successful deployments

---

## Limitations

### Current Limitations

1. **Read-Only**: This server only reads data, it cannot:
   - Create or update Jira issues
   - Create or merge GitLab merge requests
   - Add comments or approve MRs
   - Trigger pipelines or jobs
   - Change issue/MR status or assignments

2. **VPN Required**: You must be connected to your VPN (e.g., FortiClient) to access your private instances (Jira, GitLab, Confluence)

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
