import asyncio, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> int:
    params = StdioServerParameters(command=sys.executable, args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = sorted(t.name for t in tools.tools)
            print("tools:", names)
            assert "get_weather" in names and "save_note" in names, "tools missing"
            res = await session.call_tool("save_note", {"key": "demo", "value": "hello freestack"})
            text = "".join(c.text for c in res.content if c.type == "text")
            print("save_note:", text)
            res = await session.call_tool("get_note", {"key": "demo"})
            text = "".join(c.text for c in res.content if c.type == "text")
            print("get_note:", text)
            assert "hello freestack" in text
            res = await session.call_tool("list_notes", {})
            text = "".join(c.text for c in res.content if c.type == "text")
            print("list_notes:", text)
    print("MCP round-trip OK")
    return 0


sys.exit(asyncio.run(main()))
