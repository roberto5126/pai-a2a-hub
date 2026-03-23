# Register Workflow

Register this PAI's System skills with the A2A Hub, making them discoverable and callable by other org members.

## Prerequisites

- `A2A_HUB_URL` and `A2A_API_KEY` must be set (check `~/.claude/.env` or environment)
- The hub must be running and accessible

## Steps

### 1. Gather Configuration

Read `A2A_HUB_URL` and `A2A_API_KEY` from the environment.

If not set, ask the user with AskUserQuestion:
- Hub URL (e.g., `https://pai-hub.railway.app`)
- API key (provided by the org admin, starts with `pai_`)

### 2. Scan System Skills

Scan `~/.claude/skills/` for System skills (TitleCase directories only):
- **Include:** TitleCase directories with a valid `SKILL.md`
- **Exclude:** `_ALLCAPS` directories (Personal skills — NEVER register these)
- **Exclude:** Skills with `visibility: private` in any customization

For each skill, extract from the YAML frontmatter:
- `name` — The skill name
- `description` — The full description (used for discovery matching)

Parse tags from the `USE WHEN` section of the description.

### 3. Build Registration Payload

```json
{
  "name": "{user_name}'s PAI",
  "description": "PAI instance with [N] shareable skills",
  "user_name": "{user_name}",
  "user_email": "{optional}",
  "skills": [
    {
      "skill_name": "Research",
      "description": "Comprehensive research with multi-agent parallel research...",
      "tags": ["research", "analysis", "content-extraction"],
      "visibility": "org"
    }
  ]
}
```

Get `user_name` from `~/.claude/PAI/USER/README.md` or ask the user.

### 4. Register with Hub

Use the MCP tool `a2a_discover_skills` is not needed here — instead use the HTTP client directly:

```bash
curl -s -X POST "${A2A_HUB_URL}/agents/register" \
  -H "Authorization: Bearer ${A2A_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '${PAYLOAD}'
```

Or use the MCP server if configured.

### 5. Store Agent ID

Save the returned `agent_id` for future reference:
- Store in `~/.claude/PAI/USER/A2AHub/agent_id.txt`

### 6. Report Results

Show the user:
- Number of skills registered
- Agent ID
- Hub URL
- Confirmation message
