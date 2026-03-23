---
name: A2AHub
description: Organizational PAI networking via A2A protocol — register skills, discover coworkers' capabilities, send cross-user tasks, and poll for incoming work. USE WHEN ask the org, send task to another PAI, check incoming tasks, register with hub, discover skills across organization, who can help with, delegate to coworker, cross-team task, org-wide search, poll tasks, a2a hub, connect PAIs.
---

# A2AHub

Connect PAI instances across an organization. Discover skills, delegate tasks, and collaborate with coworkers' PAIs through a centralized A2A hub.

## Customization

**Before executing, check for user customizations at:**
`~/.claude/PAI/USER/SKILLCUSTOMIZATIONS/A2AHub/`

If this directory exists, load and apply any PREFERENCES.md or configuration found there. These override default behavior. If the directory does not exist, proceed with skill defaults.

## Voice Notification

**When executing a workflow, do BOTH:**

1. **Send voice notification**:
   ```bash
   curl -s -X POST http://localhost:8888/notify \
     -H "Content-Type: application/json" \
     -d '{"message": "Running the WORKFLOWNAME workflow in the A2AHub skill to ACTION"}' \
     > /dev/null 2>&1 &
   ```

2. **Output text notification**:
   ```
   Running the **WorkflowName** workflow in the **A2AHub** skill to ACTION...
   ```

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **Register** | "register with hub", "update my agent card", "connect to hub" | `Workflows/Register.md` |
| **Discover** | "who can do X", "ask the org", "find skills", "discover capabilities" | `Workflows/Discover.md` |
| **SendTask** | "send task to", "delegate to", "ask [name]'s PAI to" | `Workflows/SendTask.md` |
| **PollTasks** | "check incoming tasks", "any tasks for me", "poll tasks" | `Workflows/PollTasks.md` |
| **ExecuteTask** | "execute incoming task", "run task [id]" | `Workflows/ExecuteTask.md` |

## Examples

**Example 1: Discover who can help**
```
User: "Who in the org can do security analysis?"
→ Invokes Discover workflow
→ Searches hub for skills matching "security analysis"
→ Returns list of agents and their relevant skills
```

**Example 2: Delegate a task**
```
User: "Send a research task to Sarah's PAI about AI agent frameworks"
→ Invokes SendTask workflow
→ Sends task to Sarah's registered agent
→ Returns task ID for tracking
```

**Example 3: Check for work**
```
User: "Any incoming tasks for me?"
→ Invokes PollTasks workflow
→ Polls hub for submitted tasks
→ Lists pending tasks with descriptions
```

## Configuration

The A2AHub skill requires two environment variables:
- `A2A_HUB_URL` — URL of the centralized hub (e.g., `https://pai-hub.railway.app`)
- `A2A_API_KEY` — Your PAI's API key for the hub

Set these in `~/.claude/.env` or as system environment variables.

## Quick Reference

| Action | MCP Tool | CLI Command |
|--------|----------|-------------|
| Search skills | `a2a_discover_skills` | `bun A2AClient.ts discover --query "..."` |
| Send task | `a2a_send_task` | `bun A2AClient.ts send --to <id> ...` |
| Check task | `a2a_check_task` | `bun A2AClient.ts check --task-id <id>` |
| Poll incoming | `a2a_poll_incoming` | `bun A2AClient.ts poll` |
| Respond to task | `a2a_respond_task` | `bun A2AClient.ts respond --task-id <id> ...` |
| List agents | `a2a_list_agents` | `bun A2AClient.ts agents` |
