# Discover Workflow

Search for skills across all PAI instances in the organization.

## Steps

### 1. Get Search Query

The user's request contains the search intent. Extract the capability they're looking for.

Examples:
- "Who can do security analysis?" → query: "security analysis"
- "Find someone who can help with data engineering" → query: "data engineering"
- "Ask the org about research capabilities" → query: "research"

### 2. Search the Hub

Use the MCP tool `a2a_discover_skills` with the extracted query:

```
Tool: a2a_discover_skills
Arguments: { "query": "<extracted query>", "limit": 10 }
```

### 3. Present Results

Format the results for the user:

For each match:
- Agent name (who has this skill)
- Skill name
- Description
- Relevance score
- Tags

If no results found, suggest:
- Broadening the search query
- Checking `/discover/capabilities` for available tags
- Asking if the capability exists in the org

### 4. Offer Next Steps

After showing results, offer:
- "Send a task to [agent name]?" → Route to SendTask workflow
- "See all capabilities?" → Call `a2a_discover_skills` with broader query
