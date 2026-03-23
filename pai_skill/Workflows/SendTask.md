# SendTask Workflow

Send a task to another PAI agent in the organization.

## Steps

### 1. Identify Target

The user specifies who to send the task to. This can be:
- A specific agent name → look up ID via `a2a_list_agents`
- An agent ID (from a previous discover result)
- A capability → first run Discover, then select the best agent

If ambiguous, use `a2a_list_agents` to show options and ask the user to pick.

### 2. Compose the Task

Extract from the user's request:
- **title** — Short summary (under 100 chars)
- **description** — Full task description with all context the receiver needs
- **target_skill** — Specific skill to invoke (optional, from discover results)

If the description is vague, ask the user for more details. The receiving PAI needs enough context to execute without back-and-forth.

### 3. Send the Task

Use the MCP tool `a2a_send_task`:

```
Tool: a2a_send_task
Arguments: {
  "to_agent_id": "<uuid>",
  "title": "<short title>",
  "description": "<full description>",
  "target_skill": "<optional skill name>"
}
```

### 4. Report and Track

Show the user:
- Task ID (for tracking)
- Target agent name
- Status (should be "submitted")

Offer: "Check on this task later with: check task [task_id]"

### 5. Important Notes

- The receiving user must **approve** the task before it executes
- Tasks expire after 1 hour by default
- The sender can cancel with `a2a_check_task` → cancel flow
