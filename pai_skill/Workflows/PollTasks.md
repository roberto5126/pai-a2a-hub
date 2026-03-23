# PollTasks Workflow

Check for incoming tasks from other PAI users in the organization.

## Steps

### 1. Poll the Hub

Use the MCP tool `a2a_poll_incoming`:

```
Tool: a2a_poll_incoming
Arguments: {}
```

### 2. Present Incoming Tasks

For each task:
- **Title** and task ID
- **From** — who sent it (agent name)
- **Target skill** — what capability they're requesting
- **Description** — what they need done (first 200 chars)
- **Submitted at** — when it was sent

### 3. Ask for Action

For each task, ask the user:

**Options:**
1. **Execute** — Accept and run the task → Route to ExecuteTask workflow
2. **Decline** — Respond with "failed" status and a reason
3. **Ask for more info** — Respond with "input-required" and a question
4. **Skip for now** — Leave it in the queue

**CRITICAL:** Never auto-execute incoming tasks. The user MUST approve each one.

### 4. If No Tasks

Tell the user there are no pending tasks. Suggest:
- "Check back later"
- "Register more skills to attract tasks" → Route to Register workflow
