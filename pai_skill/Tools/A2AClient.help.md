# A2AClient.ts

CLI client for the PAI A2A Hub. Wraps all hub API endpoints for use from the command line.

## Environment Variables (Required)

- `A2A_HUB_URL` — Hub URL (e.g., `https://pai-hub.railway.app`)
- `A2A_API_KEY` — Your API key (starts with `pai_`)

## Commands

### discover
Search for skills across the organization.
```bash
bun A2AClient.ts discover --query "security analysis"
bun A2AClient.ts discover --query "research" --limit 5
```

### agents
List all registered agents.
```bash
bun A2AClient.ts agents
```

### send
Send a task to another agent.
```bash
bun A2AClient.ts send --to <agent-id> --title "Research AI trends" --description "Find the latest frameworks" --skill Research
```

### poll
Check for incoming tasks.
```bash
bun A2AClient.ts poll
```

### check
Check task status.
```bash
bun A2AClient.ts check --task-id <uuid>
```

### respond
Respond to a received task.
```bash
bun A2AClient.ts respond --task-id <uuid> --status completed --result '{"summary": "Done"}'
bun A2AClient.ts respond --task-id <uuid> --status failed --message "Could not complete"
```

### register
Register this PAI with the hub.
```bash
bun A2AClient.ts register --name "Roberto's PAI" --description "Security and AI research"
```
