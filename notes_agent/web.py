"""Web UI for NoteVault — stdlib only, localhost only.

A judge cannot click a CLI, so this is the demo surface. It adds no
new intelligence: every answer still goes through NotesAgent, with
the same local search, the same grounded-refusal rule, and the same
routing + budget panel. The UI is the thing that *shows* Otari
routing; it does not invent it.

Run:  python3 run.py serve            (http://127.0.0.1:8767/)
      python3 run.py serve --port 8000

Binds 127.0.0.1 by default. Never pass --host 0.0.0.0 for a demo
unless you understand that your notes folder becomes reachable
on the local network. No token, key, or note body is ever logged.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .agent import NotesAgent

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NoteVault — Ask your notes, routed smart</title>
<style>
body{font-family:system-ui,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#1a1a1a;background:#fafaf7}
h1{font-size:1.6em;margin-bottom:0}.tag{color:#555}
.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-weight:700;font-size:.85em}
.mock{background:#ffe8c2;color:#7a3e00}.real{background:#d2f4d2;color:#145214}
.grid{display:grid;grid-template-columns:1fr 1.6fr 1fr;gap:16px;margin-top:16px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
.card{border:1px solid #ddd;border-radius:12px;padding:14px;background:#fff}
button{padding:8px 14px;border-radius:8px;border:1px solid #333;background:#222;color:#fff;cursor:pointer}
input,select{width:100%;padding:9px;border:1px solid #bbb;border-radius:8px;box-sizing:border-box}
.meter{height:14px;background:#eee;border-radius:999px;overflow:hidden}.meter>div{height:100%;background:#d98200}
.chip{display:inline-block;background:#eef;border-radius:999px;padding:2px 9px;margin:2px;font-size:.85em}
.refusal{border:2px solid #b00020;background:#fff0f0;padding:10px;border-radius:8px}
pre{white-space:pre-wrap;word-wrap:break-word;background:#f4f4f4;padding:10px;border-radius:8px}
.note-item{cursor:pointer;padding:6px;border-radius:6px}.note-item:hover{background:#eef}
small{color:#555}
</style></head><body>
<h1>NoteVault</h1>
<p class="tag"><b>Ask your notes, routed smart.</b> One Otari gateway, many providers.
The panel on the right shows, for every answer, which provider/model was chosen and why,
what the fallback is, and how much of the local budget is left. Grounded answers only:
if your notes do not match, it refuses instead of guessing.</p>
<div id="modebar"><span id="modebadge" class="badge mock">[mock]</span> <span id="modeline"></span></div>
<div class="grid">
<div class="card"><h3>Your notes</h3><div id="notes">Loading…</div><h3>Note preview</h3><pre id="preview">Click a note.</pre></div>
<div class="card"><h3>Ask</h3>
<label>Question <input id="q" placeholder="What is Abhiverse for?"></label><br><br>
<label>Model (provider:model or vendor/model, routed by Otari)
<select id="model">
<option value="">Default (from configuration)</option>
<option value="openai:gpt-4o-mini">openai:gpt-4o-mini — documented example</option>
<option value="mistralai/mistral-small-latest">mistralai/mistral-small-latest — Otari dashboard ID</option>
</select></label>
<label>…or a custom model string <input id="customModel" placeholder="provider:model or vendor/model"></label><br><br>
<button onclick="ask()">Ask</button>
<button onclick="askPreset('What is Abhiverse for?')">Try: Abhiverse</button>
<button onclick="askPreset('quantum bananas')">Try: refusal</button>
<div id="answer" style="margin-top:14px"></div>
<h3>Organise plan <small>(plan only — no files are changed)</small></h3>
<button onclick="organise()">Show plan</button><pre id="plan"></pre></div>
<div class="card"><h3>Routing — via Otari</h3><div id="routing">Ask a question to see the route.</div>
<h3>Budget</h3><div id="budget"></div>
<p><small>Gateway-side budget/usage lives in the otari.ai account dashboard and is
not visible from this app. The meter above is the local session budget only.</small></p>
<button onclick="resetBudget()">Reset demo budget</button>
<p><small>Notes never leave this machine except the few excerpts sent to Otari, and only when you ask.</small></p></div>
</div>
<script>
async function api(path, body){
  const r = await fetch(path, {method: body ? 'POST' : 'GET',
    headers:{'Content-Type':'application/json'}, body: body ? JSON.stringify(body) : undefined});
  const j = await r.json(); if(!r.ok) throw new Error(j.error || ('HTTP '+r.status)); return j;
}
async function load(){
  const s = await api('/api/status');
  document.getElementById('modebadge').textContent = s.mode_label;
  document.getElementById('modebadge').className = 'badge ' + (s.mode === 'mock' ? 'mock' : 'real');
  document.getElementById('modeline').textContent =
    'Gateway: ' + s.gateway + ' · Default model: ' + s.model + (s.fallback_model ? ' · Fallback: ' + s.fallback_model : ' · No fallback configured');
  document.getElementById('notes').innerHTML = s.notes.map(n =>
    '<div class="note-item" onclick="showNote(\\'' + n.rel_path.replace(/'/g, '') + '\\')">📄 ' + n.title +
    ' <small>(' + n.word_count + ' words' + (n.tags.length ? ', #' + n.tags.join(' #') : '') + ')</small></div>').join('') || 'No notes found.';
  renderBudget(s.budget);
}
function renderBudget(b){
  document.getElementById('budget').innerHTML =
    '<div class="meter"><div style="width:' + b.percent_used + '%"></div></div>' +
    '<p><b>' + b.used + ' / ' + b.limit + ' calls used</b> · ' + b.remaining + ' remaining' +
    (b.exhausted ? ' · <b>Budget exhausted</b>' : '') + '</p>';
}
function renderRouting(r){
  if(r.refused_before_routing) return '<p><b>No LLM call made.</b><br>Refused before routing — no matching notes, so no provider was called and no budget was used.</p>';
  const c = r.chosen;
  return '<p><b>Gateway:</b> ' + r.gateway + '<br><b>Mode:</b> ' + r.mode_label +
    '<br><b>Chosen:</b> ' + (c ? c.provider + ' / ' + c.model : '—') + '<br><b>Why:</b> ' + (c ? c.reason : '—') +
    '<br><b>Fallback chain:</b> ' + (r.fallback_chain.length ? r.fallback_chain.map(f => f.provider + ' / ' + f.model).join(', ') : 'none configured') +
    '<br><b>Attempted:</b> ' + (r.attempted.length ? r.attempted.join(' → ') : 'none') +
    (r.fallback_used ? '<br><b>⚠ Fallback was used</b> (primary failed)' : '') + '</p>';
}
async function askPreset(t){ document.getElementById('q').value = t; await ask(); }
async function ask(){
  const q = document.getElementById('q').value.trim();
  const model = document.getElementById('customModel').value.trim() || document.getElementById('model').value || null;
  if(!q){ alert('Type a question first.'); return; }
  document.getElementById('answer').innerHTML = 'Asking…';
  try{
    const r = await api('/api/ask', {question: q, model: model});
    const ans = document.getElementById('answer');
    ans.innerHTML = (r.refused ? '<div class="refusal"><b>Refused — no guess.</b></div>' : '') +
      '<pre>' + r.answer.replace(/</g, '&lt;') + '</pre>' +
      '<div>' + r.sources.map(s => '<span class="chip">📄 ' + s.title + '</span>').join('') + '</div>' +
      '<p><span class="badge ' + (r.mode === 'mock' ? 'mock' : 'real') + '">' + (r.mode === 'mock' ? '[mock] offline stand-in' : 'real Otari') + '</span></p>';
    document.getElementById('routing').innerHTML = renderRouting(r.routing);
    renderBudget(r.budget);
  }catch(e){ document.getElementById('answer').innerHTML = '<div class="refusal">Error: ' + e.message.replace(/</g, '&lt;') + '</div>'; }
}
async function organise(){ document.getElementById('plan').textContent = (await api('/api/organise', {})).plan; }
async function showNote(p){ const n = await api('/api/note?path=' + encodeURIComponent(p)); document.getElementById('preview').textContent = n.title + String.fromCharCode(10, 10) + n.body; }
async function resetBudget(){ await api('/api/reset-budget', {}); await load(); }
load();
</script></body></html>
"""


def _json(handler: BaseHTTPRequestHandler, obj: dict, status: int = 200) -> None:
    data = json.dumps(obj).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class NoteVaultHandler(BaseHTTPRequestHandler):
    agent: NotesAgent  # set on the server instance

    def log_message(self, *args) -> None:  # never log bodies / tokens
        pass

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > 64_000:
            raise ValueError("Request too large")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8")) if raw.strip() else {}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        agent = self.server.agent  # type: ignore[attr-defined]
        if parsed.path == "/":
            data = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if parsed.path == "/api/status":
            _json(self, agent.status_dict())
            return
        if parsed.path == "/api/note":
            rel = parse_qs(parsed.query).get("path", [""])[0]
            try:
                note = agent.get_note(rel)
            except (FileNotFoundError, ValueError) as exc:
                _json(self, {"error": str(exc)}, status=404)
                return
            _json(self, {"title": note.title, "rel_path": note.rel_path, "tags": note.tags, "body": note.body[:8000]})
            return
        _json(self, {"error": "Not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        agent = self.server.agent  # type: ignore[attr-defined]
        try:
            body = self._read_json()
        except (ValueError, json.JSONDecodeError) as exc:
            _json(self, {"error": str(exc)}, status=400)
            return
        try:
            if parsed.path == "/api/ask":
                question = str(body.get("question") or "").strip()
                if not question:
                    _json(self, {"error": "question is required"}, status=400)
                    return
                model = body.get("model") or None
                result = agent.ask_detailed(question, model=model)
                _json(self, result.to_dict())
                return
            if parsed.path == "/api/organise":
                _json(self, {"plan": agent.organise_plan()})
                return
            if parsed.path == "/api/reset-budget":
                agent.reset_budget()
                _json(self, {"budget": agent.budget.to_dict()})
                return
        except (ValueError, RuntimeError) as exc:
            # ValueError: bad model string / path. RuntimeError: budget, provider failure.
            # Never include token values: these messages come from our own code, not env.
            _json(self, {"error": str(exc)}, status=400)
            return
        _json(self, {"error": "Not found"}, status=404)


def make_server(agent: NotesAgent, host: str = "127.0.0.1", port: int = 8767) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), NoteVaultHandler)
    server.agent = agent  # type: ignore[attr-defined]
    return server


def serve(agent: NotesAgent, host: str = "127.0.0.1", port: int = 8767) -> int:
    server = make_server(agent, host=host, port=port)
    print(f"NoteVault web UI: http://{host}:{port}/  (localhost only unless --host is changed)")
    print("Mode:", agent.mode, "| gateway:", agent.config.gateway_label, "| model:", agent.config.model)
    print("Press Ctrl-C to stop. Notes are read locally; excerpts go to Otari only when you ask.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0
