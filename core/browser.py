#!/usr/bin/env python3
"""core/browser.py — Browser abstraction (DIP: scripts depend on THIS interface, not on transport).
Two implementations:
  CtlBrowser  -> TCP bridge to our CloakBrowser server (:9000) — fast-path for known recipes
  McpBrowser  -> cloakbrowser-mcp (Streamable HTTP :3000) — snapshot-driven for unknown sites
Swap per site: browser = CtlBrowser() or browser = McpBrowser()
"""
import json, os, re, socket, time, urllib.request
from core.logger import log

CTL_PORT = 9000
MCP_URL = "http://127.0.0.1:3000/mcp"


class Browser:
    """Interface (ISP: minimal ops every driver needs)."""
    def navigate(self, url): raise NotImplementedError
    def snapshot(self):      raise NotImplementedError
    def eval_js(self, js):   raise NotImplementedError
    def click(self, ref):    raise NotImplementedError
    def type(self, ref, text): raise NotImplementedError
    def close(self):         pass


class CtlBrowser(Browser):
    """TCP bridge to server.py (existing fast path)."""
    def _rpc(self, op, **kw):
        s = socket.create_connection(("127.0.0.1", CTL_PORT), timeout=8)
        try:
            s.sendall((json.dumps({"op": op, **kw}) + "\n").encode())
            data = s.recv(65536).decode()
            return json.loads(data)
        finally:
            s.close()

    def navigate(self, url):
        self._rpc("navigate", url=url); time.sleep(2)
        return self.snapshot() if False else True

    def snapshot(self):
        r = self._rpc("eval", js="() => document.body ? document.body.innerText.slice(0,4000) : ''")
        return {"text": r.get("result", "")}

    def eval_js(self, js):
        r = self._rpc("eval", js=js)
        return r.get("result")

    def click(self, ref): return self.eval_js(f"document.querySelector({json.dumps(ref)}).click()")
    def type(self, ref, text): return self.eval_js(f"() => {{ const e=document.querySelector({json.dumps(ref)}); e.focus(); document.execCommand('insertText', false, {json.dumps(text)}); }}")


class McpBrowser(Browser):
    """cloakbrowser-mcp via Streamable HTTP — accessibility snapshots (fast, no probing)."""
    def __init__(self, url=MCP_URL):
        self.url, self.sid = url, None
        self._sidfile = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "mcp_session.json")
        self._load_sid()

    def _load_sid(self):
        """Reuse the SAME MCP session across script runs (browser stays open + logged in)."""
        try:
            if os.path.exists(self._sidfile):
                self.sid = json.load(open(self._sidfile)).get("sid")
        except Exception:
            self.sid = None

    def _save_sid(self):
        try:
            json.dump({"sid": self.sid}, open(self._sidfile, "w"))
        except Exception:
            pass

    def _rpc(self, method, params, _id=1):
        import urllib.error
        for attempt in range(2):
            try:
                return self._do_rpc(method, params, _id)
            except urllib.error.HTTPError as e:
                if e.code == 400 and attempt == 0:
                    # stale session — re-init fresh, persist new sid
                    self.sid = None
                    self._do_rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "hub", "version": "1"}})
                    self._save_sid()
                    continue
                raise

    def _do_rpc(self, method, params, _id=1):
        body = json.dumps({"jsonrpc": "2.0", "id": _id, "method": method, "params": params}).encode()
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.sid: h["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(self.url, body, h)
        resp = urllib.request.urlopen(req, timeout=120)
        if "Mcp-Session-Id" in resp.headers:
            self.sid = resp.headers["Mcp-Session-Id"]
            self._save_sid()
        raw = resp.read().decode()
        try:
            return json.loads(raw)
        except Exception:
            for line in reversed(raw.splitlines()):
                if line.startswith("data: "):
                    return json.loads(line[6:])
            return {"raw": raw[:200]}

    def eval_js(self, js):
        """Evaluate JS in the reused browser (DOM queries beyond the a11y snapshot)."""
        r = self._call("browser_evaluate", {"function": js})
        content = (r.get("result") or {}).get("content") or []
        txt = "".join(c.get("text", "") for c in content if isinstance(c, dict))
        # strip the '### Error' wrapper when present
        if txt.startswith("### Error"):
            return {"error": txt}
        try:
            return {"result": json.loads(txt)} if txt.startswith(("{", "[", '"')) else {"result": txt}
        except Exception:
            return {"result": txt}

    def _call(self, tool, args):
        return self._rpc("tools/call", {"name": tool, "arguments": args})

    @staticmethod
    def _tool_text(response):
        result = response.get("result") or {}
        content = result.get("content") or []
        return "\n".join(item.get("text", "") for item in content if isinstance(item, dict))

    def list_tabs(self):
        """Return tab identities without changing the active tab."""
        text = self._tool_text(self._call("browser_tabs", {"action": "list"}))
        tabs = []
        for line in text.splitlines():
            match = re.match(r"^- (\d+): (.*?)\[(.*?)\]\((.*)\)$", line.strip())
            if not match:
                continue
            prefix, title, url = match.group(2), match.group(3), match.group(4)
            tabs.append({
                "index": int(match.group(1)),
                "current": "(current)" in prefix,
                "title": title,
                "url": url,
            })
        return tabs

    def select_tab(self, index):
        """Select a tab by index returned from list_tabs()."""
        return self._call("browser_tabs", {"action": "select", "index": int(index)})

    def ensure_gmail_tab(self):
        """Find/reuse Gmail and identify the non-Gmail tab to return to.

        The caller must select the returned Gmail tab before navigating. This
        prevents OTP/confirmation reads from navigating the application form.
        """
        tabs = self.list_tabs()
        gmail = next((tab for tab in tabs if "mail.google.com" in tab["url"]), None)
        if gmail is None:
            self._call("browser_tabs", {
                "action": "new",
                "url": "https://mail.google.com/mail/u/0/#inbox",
            })
            tabs = self.list_tabs()
            gmail = next((tab for tab in tabs if "mail.google.com" in tab["url"]), None)
        if gmail is None:
            raise RuntimeError("Could not create or find the persistent Gmail tab")

        non_gmail = [tab for tab in tabs if "mail.google.com" not in tab["url"]]
        current = next((tab for tab in tabs if tab["current"]), None)
        form = current if current and "mail.google.com" not in current["url"] else (non_gmail[0] if non_gmail else None)
        return {"gmail_index": gmail["index"], "form_index": form["index"] if form else None}

    def navigate(self, url):
        r = self._call("browser_navigate", {"url": url})
        return not (r.get("result") or {}).get("isError", False)

    def snapshot(self):
        r = self._call("browser_snapshot", {})
        res = (r.get("result") or {})
        if "content" in res:
            return {"text": "\n".join(c.get("text", "") for c in res["content"])}
        return {"text": str(res)[:4000]}

    def eval_js(self, js):
        r = self._call("browser_evaluate", {"function": js})
        content = (r.get("result") or {}).get("content") or []
        txt = "".join(c.get("text", "") for c in content if isinstance(c, dict))
        if txt.startswith("### Error"):
            return {"error": txt}
        try:
            return {"result": json.loads(txt)} if txt.startswith(("{", "[", '"')) else {"result": txt}
        except Exception:
            return {"result": txt}

    def click(self, ref):
        r = self._call("browser_click", {"target": ref})
        return not (r.get("result") or {}).get("isError", False)


def pick(kind="auto"):
    """Factory (OCP: add new transports without touching callers)."""
    if kind == "mcp":
        return McpBrowser()
    if kind == "ctl":
        return CtlBrowser()
    # auto: prefer MCP if its health endpoint answers, else ctl
    try:
        urllib.request.urlopen("http://127.0.0.1:3000/healthz", timeout=1)
        return McpBrowser()
    except Exception:
        return CtlBrowser()


if __name__ == "__main__":
    b = pick()
    log.info("picked %s", type(b).__name__)
    ok = b.navigate("https://example.com")
    s = b.snapshot()
    log.info("navigate ok=%s snapshot=%d chars", ok, len(s.get("text", "")))
