---
name: Nexus
description: On-demand natural-language query layer for the Argos business ontology — ask about Hermes clients, engagements, communications, opportunities, revenue, or agent runs and get a rendered answer pulled live from the knowledge graph. USE WHEN /nexus, ask argos, query argos, what does argos know, what's the latest with, tell me about client, who hasn't replied, gone quiet, top opportunities, client 360, hermes business question, ontology query, argos question.
---

# Nexus

On-demand pull-based interface to the Argos ontology. The push surfaces (daily brief, monthly innovation brief) tell you what Argos thinks is important; Nexus lets you *ask* Argos anything and get a live answer. One endpoint, one Claude tool-use loop, one rendered markdown response.

## Customization

**Before executing, check for user customizations at:**
`~/.claude/PAI/USER/SKILLCUSTOMIZATIONS/Nexus/`

If this directory exists, load and apply any PREFERENCES.md or configuration found there. These override default behavior. If the directory does not exist, proceed with skill defaults.

## Voice Notification

**When executing a workflow, do BOTH:**

1. **Send voice notification**:
   ```bash
   curl -s -X POST http://localhost:8888/notify \
     -H "Content-Type: application/json" \
     -d '{"message": "Running the WORKFLOWNAME workflow in the Nexus skill to ACTION"}' \
     > /dev/null 2>&1 &
   ```

2. **Output text notification**:
   ```
   Running the **WorkflowName** workflow in the **Nexus** skill to ACTION...
   ```

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **Ask** | `/nexus`, "ask argos", "query argos", "ask the ontology", "what does argos know", "what's the latest with", "tell me about [client]", "who hasn't replied", "which clients are [x]", "any new opportunities", "hermes business question" | `Workflows/Ask.md` |

## Examples

**Example 1: Full client picture**
```
User: "/nexus what's the latest with DHG"
→ Invokes Ask workflow
→ POSTs /ontology/ask with the question
→ Returns a markdown answer with DHG's engagements, recent comms, opportunities, revenue
```

**Example 2: Cross-client signal**
```
User: "Ask argos which active clients have gone quiet in the last 30 days"
→ Invokes Ask workflow
→ /ontology/ask chains list_clients + count_communications per client
→ Returns a ranked list with outreach recommendations
```

**Example 3: Opportunity scan**
```
User: "what are the top 5 BUILD NOW opportunities right now"
→ Invokes Ask workflow
→ /ontology/ask calls get_top_opportunities(tier=1, limit=5)
→ Returns tier-1 ideas with scores + rationale
```

## Configuration

The Nexus skill requires two environment variables:
- `ARGOS_API_URL` — Base URL of the nexus-v2 Railway service hosting /ontology/ask (e.g., `https://nexus-v2-production-981b.up.railway.app`)
- `ARGOS_API_KEY` — Bearer token (same value as `WORKER_API_KEY` on the Argos Railway services)

Set these in `~/.claude/.env` or as system environment variables.

## A2A Hub Registration

This skill is intended to be discoverable + callable across PAIs via the A2A Hub. Register with:

**Skill name:** `Nexus`
**Description:** `Query the Argos business ontology in natural language — clients, engagements, communications, opportunities, revenue, agent runs. Returns rendered markdown answers grounded in live data.`
**Visibility:** `org`

When another PAI sends an incoming task with `target_skill=Nexus`, the receiving PAI's ExecuteTask workflow routes to `Workflows/Ask.md` using `task.description` as the question input, then responds via `a2a_respond_task` with the returned markdown as `output_data.answer`.

## Quick Reference

| Action | Endpoint | How |
|--------|----------|-----|
| Ask a question | `POST /ontology/ask` | `curl -X POST "$ARGOS_API_URL/ontology/ask" -H "Authorization: Bearer $ARGOS_API_KEY" -d '{"question": "..."}'` |
| Check endpoint health | `GET /health` | `curl "$ARGOS_API_URL/health"` |

## What Argos knows about (scope of /ask)

- **Clients** — name, status, industry, contact cadence, timezone
- **Persons + contacts** — who works where, roles, emails
- **Engagements** — project/retainer/advisory, budget, lifecycle phase timestamps, Asana + GitHub refs
- **Deliverables** — type, status, owner, deploy state
- **Communications** — emails, meetings, chats, docs with sentiment + action items
- **Opportunities** — identified leads with tier + confidence score, INVENT NEXT ideas
- **Revenue** — invoices, payments, expenses, outstanding balances
- **Decisions** — business decisions with rationale + outcome
- **Agent runs + outcomes** — what SOLVE NOW / INVENT NEXT / other agents did and what acted-on rate

## What Argos does NOT know

Current events, weather, general world knowledge, people outside Hermes contacts, anything outside the ontology schema. Out-of-scope questions return a scoped rejection.
