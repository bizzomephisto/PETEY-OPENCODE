import json, os, re, shutil, subprocess, threading, time
from pathlib import Path
from petey.tools.registry import ToolSpec

INTENT=re.compile(r"\bopen\s*code\b",re.I)
START=re.compile(r"(?:\b(?:use|ask|have|start|run)\b.{0,80}\bopen\s*code\b|\bopen\s*code\b.{0,80}\b(?:fix|build|create|edit|change|work|run|start)\b)",re.I|re.S)
STATUS=re.compile(r"(?:\bopen\s*code\b.{0,60}\b(?:status|progress|done|output|result)\b|\b(?:status|progress|done|output|result)\b.{0,60}\bopen\s*code\b)",re.I|re.S)
CODE_STATUS=re.compile(r"(?:\b(?:what(?:'s|\s+is)|check|show|give\s+me)?\s*(?:the\s+)?(?:status|progress)\s+(?:of\s+)?(?:the\s+)?(?:code|coding|project|task|work)\b|\b(?:is|has)\s+(?:the\s+)?(?:code|coding|project|task|work).{0,30}\b(?:done|finished|complete)\b)",re.I|re.S)
FREE_MODELS=("opencode/big-pickle","opencode/ling-3.0-flash-fin-free","opencode/mimo-v2.5-free","opencode/muse-spark-1.2-contributor-free","opencode/muse-spark-1.3-contributor-free","opencode/nemotron-3-ultra-free","opencode/nemotron-3.5-lightning-free")
class BridgeError(Exception): pass

class Run:
    def __init__(self,ident,goal,project,command,label,on_finished=None):
        self.id,self.goal,self.project,self.command,self.label=ident,goal,project,command,label
        self.state,self.output,self.raw_output,self.events="running","","",0; self.returncode=None; self.artifacts=[]
        self.started_at=time.strftime("%Y-%m-%d %H:%M:%S"); self.finished_at=""; self.started=time.monotonic(); self.elapsed_s=None; self.proc=None; self.on_finished=on_finished
    def start(self):
        self.proc=subprocess.Popen(self.command,cwd=self.project,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,start_new_session=True)
        threading.Thread(target=self._collect,daemon=True).start()
    def _collect(self):
        for line in self.proc.stdout:
            self.raw_output=(self.raw_output+line)[-100000:]; self.events+=1
            try:
                event=json.loads(line); part=event.get("part") or {}; kind=event.get("type")
                if kind=="text" and part.get("text"): message=part["text"]
                elif kind=="tool_use":
                    state=part.get("state") or {}; tool=str(part.get("tool") or "tool"); message=f"{tool}: {state.get('title') or state.get('status','running')}"
                    inputs=state.get("input") or {}; metadata=state.get("metadata") or {}
                    candidate=inputs.get("filePath") or inputs.get("path") or inputs.get("file") or metadata.get("filepath")
                    if candidate and re.search(r"(?:write|edit|patch|create)",tool,re.I):
                        root=Path(self.project).resolve(); raw=Path(str(candidate)).expanduser()
                        path=(raw if raw.is_absolute() else root/raw).resolve()
                        if path.is_relative_to(root) and str(path) not in self.artifacts: self.artifacts.append(str(path))
                elif kind=="error": message=str(event.get("error") or "OpenCode error")
                else: message=""
                if message: self.output=(self.output+message+"\n")[-100000:]
            except (ValueError,TypeError): self.output=(self.output+line)[-100000:]
        self.returncode=self.proc.wait()
        if self.state=="running": self.state="done" if self.returncode==0 else "error"
        self.finished_at=time.strftime("%Y-%m-%d %H:%M:%S"); self.elapsed_s=int(time.monotonic()-self.started)
        if self.on_finished: self.on_finished(self)
    def cancel(self):
        if self.state=="running":
            self.state="cancelled"
            try: self.proc.terminate()
            except OSError: pass
    def snapshot(self): return {"id":self.id,"label":self.label,"goal":self.goal,"state":self.state,"project_dir":self.project,"started_at":self.started_at,"finished_at":self.finished_at,"returncode":self.returncode,"elapsed_s":self.elapsed_s if self.elapsed_s is not None else int(time.monotonic()-self.started),"events":self.events,"output":self.output,"artifacts":[{"name":Path(path).name,"path":path,"url":f"/api/addons/petey-opencode/artifacts/{self.id}/{index}"} for index,path in enumerate(self.artifacts)]}

class OpenCodeBridge:
    def __init__(self,data_dir):
        self.data_dir=Path(data_dir); self.data_dir.mkdir(parents=True,exist_ok=True); self.lock=threading.RLock(); self.runs={}; self.history_path=self.data_dir/"runs.json"
        try:
            loaded=json.loads(self.history_path.read_text()); self.history=[x for x in loaded if isinstance(x,dict) and isinstance(x.get("id"),int)][-50:] if isinstance(loaded,list) else []
        except Exception: self.history=[]
        self.next_id=max([int(x["id"]) for x in self.history]+[0])+1
        try: saved=json.loads((self.data_dir/"config.json").read_text())
        except Exception: saved={}
        self.project=str(saved.get("project_dir") or ""); self.model=str(saved.get("model") or FREE_MODELS[0]); self.recent=[str(x) for x in saved.get("recent_project_dirs",[]) if isinstance(x,str)][:8]
        if self.project and self.project not in self.recent: self.recent.insert(0,self.project)
    def binary(self): return next((x for x in (shutil.which("opencode"),str(Path.home()/".opencode/bin/opencode")) if x and Path(x).is_file() and os.access(x,os.X_OK)),None)
    def config(self): return {"project_dir":self.project,"recent_project_dirs":self.recent,"model":self.model,"models":list(FREE_MODELS)}
    def save_config(self,project,model=None):
        project=str(project or "").strip()
        if not Path(project).is_dir(): raise BridgeError("Choose an existing project directory.")
        self.project=project; self.model=str(model or self.model)
        if self.model not in FREE_MODELS: raise BridgeError("Choose an available OpenCode model.")
        self.recent=[project,*(x for x in self.recent if x!=project)][:8]
        tmp=self.data_dir/"config.tmp"; tmp.write_text(json.dumps(self.config(),indent=2)); os.chmod(tmp,0o600); tmp.replace(self.data_dir/"config.json"); return self.config()
    def status(self): return {**self.config(),"installed":bool(self.binary()),"binary":self.binary(),"running":sum(x.state=="running" for x in self.runs.values())}
    def start(self,goal,label="petey chat"):
        goal=str(goal or "").strip()
        if not goal: raise BridgeError("Give OpenCode a task first.")
        if len(goal)>6000: raise BridgeError("The task is too long.")
        binary=self.binary()
        if not binary: raise BridgeError("OpenCode is not installed.")
        if not self.project or not Path(self.project).is_dir(): raise BridgeError("Choose and save a project directory in OpenCode first.")
        with self.lock:
            if sum(x.state=="running" for x in self.runs.values())>=2: raise BridgeError("Two OpenCode runs are already active.")
            ident=self.next_id; self.next_id+=1
            run=Run(ident,goal,self.project,[binary,"run","--format","json","--model",self.model,"--dir",self.project,goal],label or goal[:80],self._archive)
            try: run.start()
            except OSError as exc: raise BridgeError("Could not start OpenCode: "+str(exc)) from exc
            self.runs[ident]=run
        time.sleep(0.5)
        snapshot=run.snapshot()
        if snapshot["state"]=="error": raise BridgeError("OpenCode exited immediately: "+(snapshot["output"] or "unknown error")[-1000:])
        return snapshot
    def _archive(self,run):
        snapshot=run.snapshot()
        with self.lock:
            self.history=[x for x in self.history if x.get("id")!=run.id]+[snapshot]
            self.history=self.history[-50:]
            temporary=self.history_path.with_suffix(".tmp"); temporary.write_text(json.dumps(self.history,indent=2)); os.chmod(temporary,0o600); temporary.replace(self.history_path)
    def recent_runs(self):
        active=[x.snapshot() for x in self.runs.values()]
        active_ids={x["id"] for x in active}
        return sorted([x for x in self.history if x.get("id") not in active_ids]+active,key=lambda x:int(x.get("id",0)),reverse=True)[:8]
    def get(self,ident):
        try:
            number=int(ident)
            if number in self.runs: return self.runs[number].snapshot()
            return next(x for x in reversed(self.history) if x.get("id")==number)
        except (KeyError,StopIteration,TypeError,ValueError): raise BridgeError("OpenCode run not found.") from None
    def cancel(self,ident):
        try: run=self.runs[int(ident)]
        except (KeyError,TypeError,ValueError): raise BridgeError("OpenCode run is not active.") from None
        run.cancel(); return run.snapshot()
    def artifact(self,ident,index):
        try:
            run=self.get(ident); artifact=run["artifacts"][int(index)]; path=Path(artifact["path"]).resolve(); root=Path(run["project_dir"]).resolve()
        except (KeyError,IndexError,TypeError,ValueError): raise BridgeError("Artifact not found.") from None
        if not path.is_relative_to(root) or not path.is_file(): raise BridgeError("Artifact not found.")
        return path
    def tool_specs(self):
        if not self.binary(): return []
        status=lambda text:bool(STATUS.search(text or "") or CODE_STATUS.search(text or ""))
        intent=lambda text:bool(INTENT.search(text or "") or status(text)); start=lambda text:bool(START.search(text or ""))
        def begin(a):
            run=self.start(a.get("goal"),str(a.get("goal") or "OpenCode task")[:80])
            return {"message":f"OpenCode run #{run['id']} is {run['state']} in {run['project_dir']}. Check the OpenCode panel or ask for OpenCode progress.","run":run}
        def check(a):
            run=self.get(a.get("run_id")) if a.get("run_id") else (self.recent_runs()[0] if self.recent_runs() else {"state":"none"})
            links=" ".join(item["url"] for item in run.get("artifacts",[]))
            return {"message":f"OpenCode run is {run.get('state')}. {('Created files: '+links+'. Offer to open the relevant file for the user.') if links else ''}","run":run}
        return [ToolSpec(name="opencode_start_run",description="Start OpenCode on a coding task in the configured project.",parameters={"type":"object","properties":{"goal":{"type":"string"}},"required":["goal"]},handler=begin,available_when=intent,required_when=start,explicit_when=start,control_capability="start_agent_run",control_label="Start coding agents"),ToolSpec(name="opencode_run_status",description="Authoritative status for the latest OpenCode coding run. Always use this instead of guessing whether code is finished. Returns output and links to created files.",parameters={"type":"object","properties":{"run_id":{"type":"integer"}}},handler=check,available_when=intent,required_when=status,explicit_when=status,control_capability="view_agent_runs",control_label="Check agent runs")]
    def close(self):
        for run in list(self.runs.values()): run.cancel()
