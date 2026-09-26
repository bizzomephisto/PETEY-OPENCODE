(function () {
    "use strict";
    const B = "/api/addons/petey-opencode";
    let e = {};
    let polling = false;
    let statesReady = false;
    let chatActivityEnabled = true;
    let activeRunCount = 0;
    let currentWorkHost = null;
    const knownStates = new Map();

    function placeChatActivity() {
        const button = document.getElementById("oc-chat-activity");
        if (!button) return;
        const dock = document.getElementById("chat-utility-dock");
        const badgeAllowed = window.PETEY_ADDON_INTERFACE?.["petey-opencode"]?.badges !== false;
        if (dock && button.parentElement !== dock) dock.append(button);
        button.hidden = !chatActivityEnabled || !badgeAllowed || activeRunCount === 0;
    }

    function ensureChatActivity() {
        let button = document.getElementById("oc-chat-activity");
        if (button) return button;
        button = document.createElement("button");
        button.id = "oc-chat-activity";
        button.className = "oc-chat-activity";
        button.type = "button";
        button.innerHTML = '<span class="oc-chat-activity-icon" aria-hidden="true"></span><span class="oc-chat-activity-count">0</span>';
        button.addEventListener("click", () => {
            document.querySelector('.nav-button[data-view="addon-petey-opencode"]')?.click();
        });
        document.getElementById("chat-utility-dock")?.append(button);
        return button;
    }

    function syncChatActivitySurface() {
        const button = ensureChatActivity();
        if (!button) return;
        placeChatActivity();
    }

    function updateChatActivity(items) {
        const button = ensureChatActivity();
        if (!button) return;
        const count = items.filter(run => run.state === "running").length;
        activeRunCount = count;
        const noun = count === 1 ? "job" : "jobs";
        button.querySelector(".oc-chat-activity-count").textContent = String(count);
        button.classList.toggle("is-running", count > 0);
        button.title = `OpenCode: ${count} ${noun} running`;
        button.setAttribute("aria-label", `${button.title}. Open OpenCode.`);
        placeChatActivity();
    }

    function renderCurrentWork(items) {
        if (!currentWorkHost) return;
        const running = items.filter(run => run.state === "running");
        currentWorkHost.replaceChildren();
        if (!running.length) {
            const idle = document.createElement("p");
            idle.className = "oc-current-idle";
            idle.textContent = "No OpenCode job is running.";
            currentWorkHost.append(idle);
            return;
        }
        running.slice(0, 2).forEach(run => {
            const job = document.createElement("article");
            job.className = "oc-current-work";
            const heading = document.createElement("strong");
            heading.textContent = `#${run.id} ${run.label}`;
            const project = document.createElement("small");
            project.textContent = run.project_dir || "Project unavailable";
            const output = document.createElement("pre");
            output.className = "oc-current-output";
            output.textContent = (run.output || "Waiting for OpenCode output…").slice(-1400);
            job.append(heading, project, output);
            currentWorkHost.append(job);
        });
        const open = document.createElement("button");
        open.type = "button";
        open.className = "oc-current-open";
        open.textContent = "Open OpenCode";
        open.addEventListener("click", () => {
            document.querySelector('.nav-button[data-view="addon-petey-opencode"]')?.click();
        });
        currentWorkHost.append(open);
    }

    function api(path, options) {
        return fetch(B + path, options).then(async response => {
            const data = await response.json();
            if (!response.ok) throw Error(data.error || "Request failed");
            return data;
        });
    }

    function folders(data) {
        e.project.textContent = "";
        e.project.append(new Option("Choose a project…", ""));
        (data.recent_project_dirs || []).forEach(path => e.project.add(new Option(path, path)));
        e.project.value = data.project_dir || "";
        e.model.textContent = "";
        (data.models || []).forEach(model => e.model.add(new Option(model, model)));
        e.model.value = data.model || "";
        e.allowRepeatedTools.checked = data.allow_repeated_tools !== false;
        chatActivityEnabled = data.show_chat_activity !== false;
        e.showChatActivity.checked = chatActivityEnabled;
        syncChatActivitySurface();
        const refreshed = data.models_refreshed_at ? ` · ${data.models_refreshed_at}` : "";
        e.modelStatus.textContent = `${data.models_source || "bundled fallback"}${refreshed}`;
    }

    function announceFinished(run) {
        const files = (run.artifacts || []).map(item => `${item.name}: ${item.url}`);
        let message = `OpenCode run #${run.id} ${run.state === "done" ? "finished" : run.state}.`;
        if (files.length) message += `\nCreated files:\n${files.join("\n")}`;
        else if (run.state === "done") message += " No created files were reported.";
        window.dispatchEvent(new CustomEvent("petey:addon-notification", {
            detail: {addon: "petey-opencode", message},
        }));
    }

    function trackTransitions(items) {
        for (const run of items) {
            const previous = knownStates.get(run.id);
            if (statesReady && run.state !== "running"
                    && (previous === "running" || previous === undefined)) announceFinished(run);
            knownStates.set(run.id, run.state);
        }
        statesReady = true;
    }

    function renderRuns(items) {
        const host = e.runs;
        const view = host.closest(".app-view");
        const viewTop = view ? view.scrollTop : 0;
        const outputTops = new Map([...host.querySelectorAll(".oc-run")].map(node => [
            node.dataset.runId, node.querySelector(".oc-output")?.scrollTop || 0,
        ]));
        host.textContent = "";
        if (!items.length) {
            host.textContent = "No runs yet.";
            return;
        }
        items.forEach(run => {
            const row = document.createElement("div");
            row.className = "oc-run";
            row.dataset.runId = String(run.id);
            const heading = document.createElement("b");
            heading.textContent = `#${run.id} ${run.label} · ${run.state}`;
            const summary = document.createElement("small");
            summary.textContent = `\n${run.project_dir} · ${run.elapsed_s}s · ${run.events} events`;
            const output = document.createElement("div");
            output.className = "oc-output";
            output.textContent = (run.output || "Waiting for output…").slice(-4000);
            row.append(heading, summary, output);
            (run.artifacts || []).forEach(artifact => {
                const link = document.createElement("a");
                link.href = artifact.url;
                link.textContent = `Open ${artifact.name}`;
                link.target = "_blank";
                link.rel = "noopener";
                link.addEventListener("click", event => {
                    if (!window.peteyOpenArtifactPreview) return;
                    event.preventDefault();
                    window.peteyOpenArtifactPreview(artifact.url, artifact.name);
                });
                row.append(link, document.createTextNode(" "));
            });
            if (run.state === "running") {
                const cancel = document.createElement("button");
                cancel.textContent = "Cancel";
                cancel.onclick = () => api("/runs/cancel", {
                    method: "POST", headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({id: run.id}),
                }).then(() => loadRuns(true));
                row.append(cancel);
            }
            host.append(row);
            output.scrollTop = outputTops.get(String(run.id)) || 0;
        });
        if (view) view.scrollTop = viewTop;
    }

    async function loadRuns(render) {
        const data = await api("/runs");
        const runs = data.runs || [];
        trackTransitions(runs);
        updateChatActivity(runs);
        renderCurrentWork(runs);
        if (render) renderRuns(runs);
    }

    async function poll() {
        if (polling) return;
        polling = true;
        try {
            const active = document.getElementById("view-addon-petey-opencode")?.classList.contains("active-view");
            await loadRuns(Boolean(active));
        } catch (error) {
            e.message.textContent = error.message;
        } finally {
            polling = false;
        }
    }

    async function refresh() {
        try {
            const data = await api("/status");
            folders(data);
            e.state.textContent = data.installed ? `OpenCode ready · ${data.running} running` : "OpenCode not installed";
            e.start.disabled = !data.installed;
            await loadRuns(true);
        } catch (error) {
            e.state.textContent = error.message;
        }
    }

    async function browse() {
        let path = "";
        if (window.pywebview?.api?.choose_workspace_folder) path = await window.pywebview.api.choose_workspace_folder();
        else path = prompt("Full project path:") || "";
        if (path) {
            e.project.add(new Option(path, path));
            e.project.value = path;
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        ensureChatActivity();
        window.peteyInterface?.registerPanel({
            addonId: "petey-opencode",
            id: "petey-opencode-current-work",
            title: "OpenCode current work",
            icon: "▮",
            render(container) {
                currentWorkHost = container;
                renderCurrentWork([]);
                return () => { currentWorkHost = null; };
            },
        });
        window.addEventListener("petey:addon-interface", placeChatActivity);
        syncChatActivitySurface();
        e = {
            state: document.getElementById("petey-opencode-state"),
            project: document.getElementById("oc-project"),
            model: document.getElementById("oc-model"),
            modelStatus: document.getElementById("oc-model-status"),
            refreshModels: document.getElementById("oc-refresh-models"),
            allowRepeatedTools: document.getElementById("oc-allow-repeated-tools"),
            showChatActivity: document.getElementById("oc-show-chat-activity"),
            start: document.getElementById("oc-start"),
            runs: document.getElementById("oc-runs"),
            goal: document.getElementById("oc-goal"),
            message: document.getElementById("oc-message"),
        };
        document.getElementById("oc-browse").onclick = browse;
        e.refreshModels.onclick = async () => {
            e.refreshModels.disabled = true;
            e.message.textContent = "Refreshing OpenCode models…";
            try {
                const data = await api("/models/refresh", {method: "POST"});
                folders(data);
                e.message.textContent = `Found ${(data.models || []).length} OpenCode models.`;
            } catch (error) {
                e.message.textContent = error.message;
            } finally {
                e.refreshModels.disabled = false;
            }
        };
        document.getElementById("oc-save").onclick = () => api("/config", {
            method: "POST", headers: {"Content-Type": "application/json"},
            body: JSON.stringify({project_dir: e.project.value, model: e.model.value, allow_repeated_tools: e.allowRepeatedTools.checked, show_chat_activity: e.showChatActivity.checked}),
        }).then(data => {
            folders(data);
            e.message.textContent = "Setup saved.";
        }).catch(error => { e.message.textContent = error.message; });
        e.start.onclick = () => api("/runs", {
            method: "POST", headers: {"Content-Type": "application/json"},
            body: JSON.stringify({goal: e.goal.value}),
        }).then(() => {
            e.goal.value = "";
            return loadRuns(true);
        }).catch(error => { e.message.textContent = error.message; });
        window.addEventListener("petey:view", event => {
            if (event.detail.view === "addon-petey-opencode") refresh();
        });
        refresh();
        window.setInterval(poll, 2000);
    });
})();
