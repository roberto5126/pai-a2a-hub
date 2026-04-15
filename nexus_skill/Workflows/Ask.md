# Ask Workflow

Answer a free-form natural-language question about the Argos business ontology by calling `POST /ontology/ask` on the nexus-v2 Railway service. The endpoint runs a Claude tool-use loop against HermesClient methods and returns a rendered markdown answer grounded in live data.

## Trigger phrases

- `/nexus <question>`
- "ask argos <question>"
- "query argos"
- "ask the ontology"
- "what does argos know about <entity>"
- "what's the latest with <client>"
- "tell me about <client>"
- "who hasn't replied in <timeframe>"
- "which active clients <condition>"
- "any new opportunities <context>"

## Inputs

- **question** (string): the user's natural-language question. For slash-style invocations (`/nexus <text>`), everything after the slash command is the question. For natural invocations, extract the question from the user's message. If the question is ambiguous, prefer passing it through verbatim — the endpoint's system prompt handles clarification.

## Steps

### 1. Voice notification

```bash
curl -s -X POST http://localhost:8888/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "Running the Ask workflow in the Nexus skill to query the Argos ontology"}' \
  > /dev/null 2>&1 &
```

And output: `Running the **Ask** workflow in the **Nexus** skill to query the Argos ontology...`

### 2. Load environment

Read `ARGOS_API_URL` and `ARGOS_API_KEY` from `~/.claude/.env` or the shell environment. If either is missing, output:

> ⚠ Nexus is not configured. Add `ARGOS_API_URL` and `ARGOS_API_KEY` to `~/.claude/.env`. Ask Roberto for the key if you don't have it.

And stop.

### 3. Call the /ontology/ask endpoint

```bash
RESPONSE=$(curl -s -X POST "${ARGOS_API_URL}/ontology/ask" \
  -H "Authorization: Bearer ${ARGOS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg q "${QUESTION}" '{question: $q}')" \
  --max-time 120)
```

The endpoint typically responds in 10–40 seconds depending on how many tool calls Claude decides to make (up to 5 turns). Timeout is 120 seconds — if you hit it, the question is likely too broad; retry with something more focused.

### 4. Parse the response

The response shape is:
```json
{
  "answer": "<markdown string — the actual answer>",
  "question": "<echo of the original question>",
  "tools_used": ["get_client_by_canonical", "get_recent_communications", ...],
  "turns": 3
}
```

Extract `.answer` and display it as the primary output.

### 5. Display the answer

Render the markdown answer directly — no reformatting, no editorializing. The backend system prompt already instructs Claude to produce clean, scoped markdown.

After the answer, add a subtle footer showing what tools were used (so the user can trust the grounding):

```
---
*Queried via Nexus (`nexus_ask` • N turns • tools: tool1, tool2, ...)*
```

### 6. Offer a follow-up

After the answer, suggest one logical next question based on what the answer contained. Examples:

- If the answer listed multiple engagements → "Want more detail on one of these engagements? `/nexus tell me about <engagement name>`"
- If the answer surfaced a churn risk → "Want to see the full comm history? `/nexus show me every comm with <client> in the last 60 days`"
- If the answer showed multiple silent clients → "Want to draft check-in emails for them? Let me know which client."

Keep the follow-up to ONE suggestion — don't spam options.

## Error handling

- **HTTP 401**: `ARGOS_API_KEY` is wrong or expired. Show: "Auth failed — double-check ARGOS_API_KEY in ~/.claude/.env matches the current Railway WORKER_API_KEY."
- **HTTP 500 / 502 / 503**: Backend error. Show: "Argos backend returned an error. Check nexus-v2 Railway logs: `railway logs --service nexus-v2 --tail 50`."
- **HTTP 200 but empty answer**: Claude hit the turn limit without synthesizing. Show the scoped message from the backend AND suggest: "The question might be too broad. Try focusing on one client or one time window."
- **Timeout**: Same as above — suggest a more focused question.
- **Connection refused / DNS failure**: Railway service might be down. Show: `curl -s "${ARGOS_API_URL}/health"` output for diagnosis.

## Invocation as A2A incoming task

When this workflow is triggered by an incoming A2A task (dispatched from ExecuteTask.md with `target_skill=Nexus`):

1. The `question` input comes from `task.description` instead of the user's direct message
2. Voice notification still fires (to announce the cross-PAI request)
3. After step 4 (parse response), the answer is returned to A2AHub's ExecuteTask, which posts it via `a2a_respond_task` as `output_data.answer`
4. The follow-up suggestion in step 6 is SKIPPED for A2A invocations (the sender will decide their own follow-up)

## Example execution

```
User: /nexus what's the latest with DHG

→ [voice] "Running the Ask workflow..."
→ [text]  Running the **Ask** workflow in the **Nexus** skill to query the Argos ontology...
→ [curl]  POST /ontology/ask {"question": "what's the latest with DHG"}
→ [wait]  ~15 seconds
→ [display]

# DHG Hotel Group

## Overview
**DHG Hotel Group** is an **active** client in hospitality...
[rest of markdown answer]

---
*Queried via Nexus (`nexus_ask` • 4 turns • tools: get_client_by_canonical, get_client_contacts, get_engagements_for_client, get_recent_communications, get_opportunities_for_client, get_person_by_id, get_revenue_for_client)*

Want more detail on one of these engagements? `/nexus tell me about DHG-Alfred`
```
