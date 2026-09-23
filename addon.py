try:
    from .opencode_bridge import OpenCodeBridge, BridgeError
except ImportError:
    from opencode_bridge import OpenCodeBridge, BridgeError
from flask import jsonify, request, send_file

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
        try: return jsonify({"ok":True,**bridge.save_config(data.get("project_dir"),data.get("model"))})
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
        try: return send_file(bridge.artifact(run_id, index), as_attachment=False)
        except BridgeError as exc: return fail(exc,404)
    for suffix, methods, view in (("config",["GET","POST"],config),("status",["GET"],status),("models/refresh",["POST"],refresh_models),("runs",["GET","POST"],runs),("runs/detail",["GET"],detail),("runs/cancel",["POST"],cancel)):
        context.app.add_url_rule("/api/addons/petey-opencode/"+suffix, endpoint="addon_petey_opencode_"+suffix.replace("/","_"), view_func=view, methods=methods)
    context.app.add_url_rule("/api/addons/petey-opencode/artifacts/<int:run_id>/<int:index>", endpoint="addon_petey_opencode_artifact", view_func=artifact, methods=["GET"])
    return Addon(bridge)
