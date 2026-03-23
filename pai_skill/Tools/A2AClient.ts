#!/usr/bin/env bun
/**
 * A2AClient.ts — CLI client for the PAI A2A Hub
 *
 * Usage:
 *   bun A2AClient.ts discover --query "security analysis"
 *   bun A2AClient.ts agents
 *   bun A2AClient.ts send --to <agent-id> --title "..." --description "..."
 *   bun A2AClient.ts poll
 *   bun A2AClient.ts check --task-id <uuid>
 *   bun A2AClient.ts respond --task-id <uuid> --status completed --result '{"key":"val"}'
 *   bun A2AClient.ts register --name "My PAI" --description "..." --skills '[...]'
 */

const HUB_URL = (process.env.A2A_HUB_URL || "").replace(/\/$/, "");
const API_KEY = process.env.A2A_API_KEY || "";

if (!HUB_URL || !API_KEY) {
  console.error("Error: A2A_HUB_URL and A2A_API_KEY environment variables are required.");
  process.exit(1);
}

const headers = {
  Authorization: `Bearer ${API_KEY}`,
  "Content-Type": "application/json",
};

async function request(method: string, path: string, body?: unknown): Promise<unknown> {
  const resp = await fetch(`${HUB_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const text = await resp.text();
    console.error(`Error ${resp.status}: ${text}`);
    process.exit(1);
  }
  return resp.json();
}

function parseArgs(args: string[]): Record<string, string> {
  const result: Record<string, string> = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith("--")) {
      const key = args[i].slice(2);
      const val = args[i + 1] && !args[i + 1].startsWith("--") ? args[++i] : "true";
      result[key] = val;
    }
  }
  return result;
}

const [command, ...rest] = process.argv.slice(2);
const args = parseArgs(rest);

switch (command) {
  case "discover": {
    if (!args.query) {
      console.error("Usage: bun A2AClient.ts discover --query <search terms>");
      process.exit(1);
    }
    const data = (await request("GET", `/discover?q=${encodeURIComponent(args.query)}&limit=${args.limit || 10}`)) as any;
    console.log(JSON.stringify(data, null, 2));
    break;
  }

  case "agents": {
    const data = await request("GET", "/agents");
    console.log(JSON.stringify(data, null, 2));
    break;
  }

  case "send": {
    if (!args.to || !args.title || !args.description) {
      console.error("Usage: bun A2AClient.ts send --to <agent-id> --title <title> --description <desc> [--skill <name>]");
      process.exit(1);
    }
    const payload: Record<string, unknown> = {
      to_agent_id: args.to,
      title: args.title,
      description: args.description,
    };
    if (args.skill) payload.target_skill = args.skill;
    const data = await request("POST", "/tasks/send", payload);
    console.log(JSON.stringify(data, null, 2));
    break;
  }

  case "poll": {
    const data = await request("GET", "/tasks/poll");
    console.log(JSON.stringify(data, null, 2));
    break;
  }

  case "check": {
    if (!args["task-id"]) {
      console.error("Usage: bun A2AClient.ts check --task-id <uuid>");
      process.exit(1);
    }
    const data = await request("GET", `/tasks/${args["task-id"]}`);
    console.log(JSON.stringify(data, null, 2));
    break;
  }

  case "respond": {
    if (!args["task-id"] || !args.status) {
      console.error("Usage: bun A2AClient.ts respond --task-id <uuid> --status <completed|failed|working> [--result '{...}'] [--message '...']");
      process.exit(1);
    }
    const payload: Record<string, unknown> = { status: args.status };
    if (args.result) payload.output_data = JSON.parse(args.result);
    if (args.message) payload.message = args.message;
    const data = await request("POST", `/tasks/${args["task-id"]}/respond`, payload);
    console.log(JSON.stringify(data, null, 2));
    break;
  }

  case "register": {
    if (!args.name) {
      console.error("Usage: bun A2AClient.ts register --name <name> --description <desc> [--skills '<json array>']");
      process.exit(1);
    }
    const payload: Record<string, unknown> = {
      name: args.name,
      description: args.description || "",
      user_name: args.name,
    };
    if (args.skills) payload.skills = JSON.parse(args.skills);
    const data = await request("POST", "/agents/register", payload);
    console.log(JSON.stringify(data, null, 2));
    break;
  }

  default:
    console.log(`PAI A2A Hub Client

Commands:
  discover  --query <text>              Search skills across the org
  agents                                List all registered agents
  send      --to <id> --title <t> --description <d> [--skill <name>]
  poll                                  Check for incoming tasks
  check     --task-id <uuid>            Get task status
  respond   --task-id <uuid> --status <s> [--result '{...}'] [--message '...']
  register  --name <n> --description <d> [--skills '<json>']

Environment:
  A2A_HUB_URL   Hub URL (required)
  A2A_API_KEY   API key (required)`);
}
