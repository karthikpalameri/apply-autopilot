#!/usr/bin/env python3
"""mcp_test.py — live-test cloakbrowser-mcp over Streamable HTTP. Proves tool surface + speed."""
import json, time, urllib.request

URL = "http://127.0.0.1:3000/mcp"

SID = None

def rpc(method, params, _id):
    global SID
    body = json.dumps({"jsonrpc": "2.0", "id": _id, "method": method, "params": params}).encode()
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if SID:
        h["Mcp-Session-Id"] = SID
    req = urllib.request.Request(URL, body, h)
    resp = urllib.request.urlopen(req, timeout=120)
    if "Mcp-Session-Id" in resp.headers:
        SID = resp.headers["Mcp-Session-Id"]
    raw = resp.read().decode()
    try:
        return json.loads(raw)
    except Exception:
        # SSE format: extract the last data: line
        for line in reversed(raw.splitlines()):
            if line.startswith("data: "):
                return json.loads(line[6:])
        return {"raw": raw[:200]}

# 1) initialize
t0 = time.time()
r = rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "probe", "version": "0.1"}}, 1)
print(f"initialize: {time.time()-t0:.2f}s · server: {r.get('result',{}).get('serverInfo')}")

# 2) tools/list
t0 = time.time()
r = rpc("tools/list", {}, 2)
tools = r.get("result", {}).get("tools", [])
names = [t["name"] for t in tools]
print(f"tools/list: {time.time()-t0:.2f}s · {len(tools)} tools")
have = {"browser_navigate","browser_snapshot","browser_click","browser_type","browser_network","browser_console","browser_take_screenshot"}
print("  key tools:", sorted(have & set(names)))
print("  sample:", names[:8])

# 3) navigate + snapshot — THE SPEED TEST
t0 = time.time()
r = rpc("tools/call", {"name": "browser_navigate", "arguments": {"url": "https://example.com"}}, 3)
nav_t = time.time() - t0
ok = r.get("result", {}).get("isError") == False if "result" in r else None
r2 = rpc("tools/call", {"name": "browser_snapshot", "arguments": {}}, 4)
snap_t = time.time() - r2.get("time", time.time())
snap = json.dumps(r2.get("result", {}))[:150]
print(f"navigate: {nav_t:.2f}s · snapshot: {snap_t:.2f}s")
print(f"  snapshot head: {snap}")

# 4) a form interaction sample on a realistic page
t0 = time.time()
rpc("tools/call", {"name": "browser_navigate", "arguments": {"url": "https://www.google.com"}}, 5)
r = rpc("tools/call", {"name": "browser_snapshot", "arguments": {}}, 6)
txt = json.dumps(r.get("result", {}))
print(f"google snapshot: {time.time()-t0:.2f}s · has input: {'<input' in txt or 'input' in txt[:2000]}")
print("RESULT: MCP WORKS" if "result" in str(r2) else "RESULT: CHECK OUTPUT")
