"""MCP server for PAI A2A Hub — gives Claude Code native tool access to the org network."""
import asyncio
import json
import os
import sys

from mcp_server.client import HubClient


def get_client() -> HubClient:
    return HubClient()


# Tool definitions
TOOLS = [
    {
        "name": "a2a_discover_skills",
        "description": "Search for skills across the organization's PAI instances. Use when you need to find 'who in the org can do X?'",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What capability are you looking for? e.g. 'security analysis', 'research', 'data engineering'",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 10)",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "a2a_send_task",
        "description": "Send a task to another PAI agent in the organization. The receiving user will be notified and can approve/execute it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to_agent_id": {
                    "type": "string",
                    "description": "UUID of the target agent (from discover results)",
                },
                "title": {
                    "type": "string",
                    "description": "Short task title",
                },
                "description": {
                    "type": "string",
                    "description": "Full task description — what you need done",
                },
                "target_skill": {
                    "type": "string",
                    "description": "Specific skill to invoke on the target (optional)",
                },
            },
            "required": ["to_agent_id", "title", "description"],
        },
    },
    {
        "name": "a2a_check_task",
        "description": "Check the status and result of a previously sent task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID of the task to check",
                },
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "a2a_poll_incoming",
        "description": "Check for tasks assigned to this PAI by other org members.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "a2a_respond_task",
        "description": "Submit a response to a received task (complete it, fail it, or request more input).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID of the task to respond to",
                },
                "status": {
                    "type": "string",
                    "enum": ["completed", "failed", "input-required", "working"],
                    "description": "New task status",
                },
                "output_data": {
                    "type": "object",
                    "description": "Result data (for completed tasks)",
                },
                "message": {
                    "type": "string",
                    "description": "Optional message to the sender",
                },
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "a2a_list_agents",
        "description": "List all registered PAI agents in the organization.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


async def handle_tool_call(name: str, arguments: dict) -> str:
    """Execute an MCP tool call and return the result as text."""
    client = get_client()

    if name == "a2a_discover_skills":
        result = await client.discover(
            arguments["query"],
            limit=arguments.get("limit", 10),
        )
        if not result["results"]:
            return "No matching skills found in the organization."
        lines = []
        for r in result["results"]:
            tags = ", ".join(r.get("tags") or [])
            lines.append(
                f"- **{r['skill_name']}** on {r['agent_name']} "
                f"(score: {r['relevance_score']}) — {r['description']}"
                + (f" [{tags}]" if tags else "")
            )
        return f"Found {result['total']} matching skills:\n\n" + "\n".join(lines)

    elif name == "a2a_send_task":
        result = await client.send_task(
            to_agent_id=arguments["to_agent_id"],
            title=arguments["title"],
            description=arguments["description"],
            target_skill=arguments.get("target_skill"),
        )
        return (
            f"Task sent successfully!\n"
            f"- Task ID: {result['id']}\n"
            f"- Status: {result['state']}\n"
            f"- To: {arguments['to_agent_id']}\n"
            f"Use a2a_check_task with this ID to monitor progress."
        )

    elif name == "a2a_check_task":
        result = await client.check_task(arguments["task_id"])
        output = (
            f"Task: {result['title']}\n"
            f"Status: {result['state']}\n"
        )
        if result.get("output_data"):
            output += f"Result: {json.dumps(result['output_data'], indent=2)}\n"
        if result.get("error_message"):
            output += f"Error: {result['error_message']}\n"
        if result.get("messages"):
            output += "\nMessages:\n"
            for msg in result["messages"]:
                output += f"  [{msg['role']}] {msg['content']}\n"
        return output

    elif name == "a2a_poll_incoming":
        result = await client.poll_incoming()
        tasks = result.get("tasks", [])
        if not tasks:
            return "No incoming tasks."
        lines = ["Incoming tasks:\n"]
        for t in tasks:
            lines.append(
                f"- **{t['title']}** (ID: {t['id']})\n"
                f"  From: agent {t['from_agent_id']}\n"
                f"  Skill: {t.get('target_skill', 'any')}\n"
                f"  Description: {t['description'][:200]}"
            )
        return "\n".join(lines)

    elif name == "a2a_respond_task":
        result = await client.respond_task(
            task_id=arguments["task_id"],
            status=arguments["status"],
            output_data=arguments.get("output_data"),
            message=arguments.get("message"),
        )
        return f"Task {arguments['task_id']} updated to: {result['state']}"

    elif name == "a2a_list_agents":
        agents = await client.list_agents()
        if not agents:
            return "No agents registered in the organization."
        lines = ["Registered agents:\n"]
        for a in agents:
            skill_names = [s["skill_name"] for s in a.get("skills", [])]
            lines.append(
                f"- **{a['name']}** (ID: {a['id']})\n"
                f"  User: {a['user_name']}\n"
                f"  Skills: {', '.join(skill_names) or 'none'}"
            )
        return "\n".join(lines)

    return f"Unknown tool: {name}"


async def main():
    """Run the MCP server over stdio using JSON-RPC."""
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    w_transport, w_protocol = await asyncio.get_event_loop().connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, asyncio.get_event_loop())

    async def send_response(response: dict):
        data = json.dumps(response)
        message = f"Content-Length: {len(data)}\r\n\r\n{data}"
        writer.write(message.encode())
        await writer.drain()

    buffer = b""
    while True:
        chunk = await reader.read(4096)
        if not chunk:
            break
        buffer += chunk

        while b"\r\n\r\n" in buffer:
            header_end = buffer.index(b"\r\n\r\n")
            header = buffer[:header_end].decode()
            content_length = 0
            for line in header.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    content_length = int(line.split(":")[1].strip())

            body_start = header_end + 4
            if len(buffer) < body_start + content_length:
                break

            body = buffer[body_start : body_start + content_length].decode()
            buffer = buffer[body_start + content_length :]

            try:
                request = json.loads(body)
            except json.JSONDecodeError:
                continue

            method = request.get("method", "")
            req_id = request.get("id")

            if method == "initialize":
                await send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": {
                            "name": "pai-a2a-hub",
                            "version": "0.1.0",
                        },
                    },
                })
            elif method == "notifications/initialized":
                pass  # No response needed
            elif method == "tools/list":
                await send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS},
                })
            elif method == "tools/call":
                tool_name = request["params"]["name"]
                arguments = request["params"].get("arguments", {})
                try:
                    result_text = await handle_tool_call(tool_name, arguments)
                    await send_response({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": result_text}],
                            "isError": False,
                        },
                    })
                except Exception as e:
                    await send_response({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": f"Error: {e}"}],
                            "isError": True,
                        },
                    })
            elif req_id is not None:
                await send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                })


if __name__ == "__main__":
    asyncio.run(main())
