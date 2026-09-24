try:
    from .opencode_bridge import OpenCodeBridge, BridgeError
except ImportError:
    from opencode_bridge import OpenCodeBridge, BridgeError
from flask import jsonify, request, send_file

PREVIEW_STORAGE_SHIM = """<script>
(() => {
  function memoryStorage() {
    const values = new Map();
    return {
      get length() { return values.size; },
      key(index) { return Array.from(values.keys())[Number(index)] ?? null; },
      getItem(key) { key = String(key); return values.has(key) ? values.get(key) : null; },
      setItem(key, value) { values.set(String(key), String(value)); },
      removeItem(key) { values.delete(String(key)); },
      clear() { values.clear(); }
    };
  }
  for (const name of ["localStorage", "sessionStorage"]) {
    try { void window[name].length; }
    catch (_error) {
      try { Object.defineProperty(window, name, {value: memoryStorage(), configurable: true}); }
      catch (_ignored) {}
    }
  }
})();
</script>"""
MAX_PREVIEW_HTML_BYTES = 5 * 1024 * 1024


def preview_html(path):
    """Add volatile Web Storage to an opaque-origin sandbox without weakening it."""
    source = path.read_bytes()[:MAX_PREVIEW_HTML_BYTES].decode("utf-8", errors="replace")
    lower = source.lower()
    head = lower.find("<head")
    if head >= 0:
        close = source.find(">", head)
        if close >= 0:
            return source[: close + 1] + PREVIEW_STORAGE_SHIM + source[close + 1 :]
    return PREVIEW_STORAGE_SHIM + source

class Addon:
    def __init__(self, bridge): self.bridge = bridge
    def tool_specs(self): return self.bridge.tool_specs()
    def close(self): self.bridge.close()

def setup(context):
    bridge = OpenCodeBridge(context.data_dir)
    def body():
        value = request.get_json(silent=True)
        return value if isinstance(value, dict) else {}
    def fail(exc, status=400): return jsonify({"ok":False,"error":str(exc)}), status
    def config():
        if request.method == "GET": return jsonify({"ok":True,**bridge.config()})
        data=body()
        try: return jsonify({"ok":True,**bridge.save_config(data.get("project_dir"),data.get("model"),data.get("allow_repeated_tools"),data.get("show_chat_activity"))})
        except BridgeError as exc: return fail(exc)
    def status(): return jsonify({"ok":True,**bridge.status()})
    def refresh_models():
        try: return jsonify({"ok":True,**bridge.refresh_models(force=True)})
        except BridgeError as exc: return fail(exc)
    def runs():
        if request.method == "GET": return jsonify({"ok":True,"runs":bridge.recent_runs()})
        try: return jsonify({"ok":True,"run":bridge.start(body().get("goal"),"panel")})
        except BridgeError as exc: return fail(exc)
    def detail():
        try: return jsonify({"ok":True,"run":bridge.get(request.args.get("id"))})
        except BridgeError as exc: return fail(exc,404)
    def cancel():
        try: return jsonify({"ok":True,"run":bridge.cancel(body().get("id"))})
        except BridgeError as exc: return fail(exc)
    def artifact(run_id, index):
        try:
            path = bridge.artifact(run_id, index)
            if (request.args.get("petey_preview") == "1"
                    and path.suffix.lower() in {".html", ".htm"}
                    and path.stat().st_size <= MAX_PREVIEW_HTML_BYTES):
                return context.app.response_class(
                    preview_html(path), mimetype="text/html", headers={"Cache-Control": "no-store"}
                )
            return send_file(path, as_attachment=False)
        except BridgeError as exc: return fail(exc,404)
    for suffix, methods, view in (("config",["GET","POST"],config),("status",["GET"],status),("models/refresh",["POST"],refresh_models),("runs",["GET","POST"],runs),("runs/detail",["GET"],detail),("runs/cancel",["POST"],cancel)):
        context.app.add_url_rule("/api/addons/petey-opencode/"+suffix, endpoint="addon_petey_opencode_"+suffix.replace("/","_"), view_func=view, methods=methods)
    context.app.add_url_rule("/api/addons/petey-opencode/artifacts/<int:run_id>/<int:index>", endpoint="addon_petey_opencode_artifact", view_func=artifact, methods=["GET"])
    return Addon(bridge)
