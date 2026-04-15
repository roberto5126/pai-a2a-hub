# ExecuteTask Workflow

Execute an incoming task that the user has approved.

## Prerequisites

- User has reviewed the task (via PollTasks workflow) and approved execution
- Task ID is known

## Steps

### 1. Acknowledge the Task

First, mark the task as "working":

```
Tool: a2a_respond_task
Arguments: { "task_id": "<uuid>", "status": "working", "message": "Task accepted, working on it" }
```

### 2. Execute the Work

Based on the task's `target_skill`:
- If a specific skill is requested, invoke that skill with the task description as context
- If no skill specified, determine the best approach from the task description

**Execute the task using normal PAI capabilities** — use the appropriate skill, tools, and workflows.

#### Dispatch rules for named skills

| `target_skill` | Handler | How |
|---|---|---|
| `Nexus` | **Nexus** skill → `Workflows/Ask.md` | Treat `task.description` as the natural-language question input. Run the Ask workflow to the point where it has a rendered markdown answer, but SKIP the voice notification (it's a background A2A task, not a local interactive request) and SKIP the follow-up suggestion step (the sender decides their own follow-up). Use the returned markdown as `output_data.answer` in the final `a2a_respond_task` call. |

(Add new rows to this table as more skills become A2A-exposable.)

### 3. Capture the Result

Collect the output from the execution:
- Summary of what was done
- Any generated artifacts (text, data, analysis)
- Key findings or deliverables

### 4. Respond with Results

Use the MCP tool `a2a_respond_task`:

**On success (generic):**
```
Tool: a2a_respond_task
Arguments: {
  "task_id": "<uuid>",
  "status": "completed",
  "output_data": { "summary": "...", "result": "..." },
  "message": "Task completed successfully"
}
```

**On success (Nexus):** populate `output_data.answer` with the rendered markdown from Nexus/Ask, plus a short summary:
```
Tool: a2a_respond_task
Arguments: {
  "task_id": "<uuid>",
  "status": "completed",
  "output_data": {
    "answer": "<markdown answer from Nexus/Ask>",
    "tools_used": ["..."],
    "turns": N
  },
  "message": "Nexus answered the question — see output_data.answer"
}
```

**On failure:**
```
Tool: a2a_respond_task
Arguments: {
  "task_id": "<uuid>",
  "status": "failed",
  "message": "Reason for failure"
}
```

**If more info needed:**
```
Tool: a2a_respond_task
Arguments: {
  "task_id": "<uuid>",
  "status": "input-required",
  "message": "Question for the sender"
}
```

### 5. Report to User

Show the user:
- Task status update
- Summary of what was executed
- Confirmation that the sender will be notified
