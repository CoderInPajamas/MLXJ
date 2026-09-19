"use strict";

let current = null;
let pendingOperation = null;
let decisionBusy = false;
let loadingTimer = null;
let lastLoadingVersion = -1;
const byId = (id) => document.getElementById(id);
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));

async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data)});
  const payload = await response.json();
  if (!response.ok) {
    if (payload.state) render(payload);
    const error = new Error(payload.message || payload.error || "Local request failed");
    error.payload = payload;
    throw error;
  }
  return payload;
}

function actionButton(id, label, classes = "", extra = "") {
  return `<button type="button" class="${classes}" data-action="${escapeHTML(id)}" ${extra}>${label}</button>`;
}

function closeButton(id) { return actionButton(id, "×", "close-button", 'aria-label="Close current window"'); }

function render(snapshot) {
  if (!snapshot.state || (current && snapshot.state_version < current.state_version)) return;
  const changed = !current || snapshot.state_version !== current.state_version;
  current = snapshot;
  byId("state-version").textContent = `STATE ${current.state_version}`;
  byId("view-label").textContent = ({desktop:"Desktop",library:"Course library",notes:"Field notes",player:"Course player"})[current.state.view];
  byId("state-json").textContent = JSON.stringify(current.state, null, 2);
  byId("candidate-count").textContent = current.candidates.length;
  byId("candidate-list").innerHTML = current.candidates.map((c) => `<span class="candidate" title="${escapeHTML(c.description)}">${escapeHTML(c.id)}</span>`).join("");
  const model = current.model;
  byId("model-name").textContent = typeof model === "object" && model ? (model.name || model.path || JSON.stringify(model)) : String(model || "Local MLX model");
  if (!changed) return;
  const state = current.state;
  const view = state.view;
  if (view === "desktop") {
    byId("stage").innerHTML = `<div class="desktop-home"><span class="desktop-overline">A LITTLE SPACE FOR CURIOSITY</span><h2>What will you explore today?</h2><p>Your next small discovery starts here.</p><div class="app-grid">${actionButton("open.library",'<span class="app-icon">▷</span><strong>Course library</strong><small>6 little worlds to explore</small>',"app-tile")}${actionButton("open.notes",'<span class="app-icon">▤</span><strong>Field notes</strong><small>A place for your ideas</small>',"app-tile notes")}</div><p class="desktop-hint">A fictional desktop. Real local model decisions.</p></div>`;
  } else if (view === "library") {
    const filters = ["All","Design","Science","Music"].map((category) => category === state.library.filter ? `<button class="filter-button active" type="button" disabled>${category}</button>` : actionButton(`filter.${category.toLowerCase()}`,category,"filter-button")).join("");
    const sorts = [["featured","Featured"],["az","A–Z"],["za","Z–A"]].map(([id,label]) => id === state.library.sort ? `<button class="sort-button active" type="button" disabled>${label}</button>` : actionButton(`sort.${id}`,label,"sort-button")).join("");
    const cards = current.courses.map((course,i) => actionButton(`play.${course.id}`,`<div class="course-art ${escapeHTML(course.color)}"><span class="course-index">0${i+1}</span>${escapeHTML(course.symbol)}</div><div class="course-copy"><strong>${escapeHTML(course.title)}</strong><span>${escapeHTML(course.category)}<i>${course.minutes} min ↗</i></span></div>`,"course-card")).join("");
    byId("stage").innerHTML = `<div class="library"><div class="page-heading"><div><h2>The course library</h2><p>Follow your curiosity, one small lesson at a time.</p></div>${closeButton("close.library")}</div><div class="library-controls"><div class="filter-group">${filters}</div><div class="sort-group">${sorts}</div></div><div class="course-grid">${cards}</div></div>`;
  } else if (view === "notes") {
    byId("stage").innerHTML = `<div class="notes-page"><div class="page-heading"><div><h2>Field notes</h2><p>A few things worth remembering.</p></div>${closeButton("close.notes")}</div><div class="notes-body"><strong>Make room for small discoveries.</strong><br>Notice a new color.<br>Listen for a different rhythm.<br>Leave a little space to wonder.<br><span>Fictional notes, written for this public demo.</span></div></div>`;
  } else {
    const player = state.player;
    const loading = player.status === "loading";
    const playing = player.status === "playing";
    const controls = loading ? '<span class="player-position">Controls appear when the player is ready.</span>' : `${actionButton(playing ? "player.pause" : "player.resume",playing ? "Ⅱ Pause" : "▷ Resume","control-button")}${actionButton("player.rewind","↶ 10 sec","control-button")}<div class="progress-track"><div class="progress-fill"></div></div><span class="player-position">${Math.floor(player.position_seconds / 60)}:${String(player.position_seconds % 60).padStart(2,"0")}</span>`;
    byId("stage").innerHTML = `<div class="player"><div class="page-heading"><div><h2>${escapeHTML(player.course)}</h2><p>Your own little moment of discovery.</p></div>${closeButton("close.player")}</div><div class="player-screen"><span class="player-status-label">${escapeHTML(player.status)} · simulated video</span>${loading ? '<div class="spinner"></div>' : `<span class="player-art">${playing ? "◒" : "Ⅱ"}</span>`}<span class="player-caption">${loading ? "GETTING YOUR LESSON READY" : "A FICTIONAL COURSE. A REAL CONTROL."}</span></div><div class="player-controls">${controls}</div></div>`;
    if (loading && lastLoadingVersion !== current.state_version) {
      clearTimeout(loadingTimer);
      lastLoadingVersion = current.state_version;
      const version = current.state_version;
      loadingTimer = setTimeout(() => api("/api/demo/player-ready",{state_version:version}).then(render).catch(() => {}), 1600);
    }
  }
  document.querySelectorAll("[data-action]").forEach((element) => element.addEventListener("click", () => handleAction(element)));
  const examples = ({desktop:["Open the course library","Open my notes","Close it"],library:["First one","Only design courses","Close it"],notes:["Close it","Did you just close it?"],player:state.player?.status === "loading" ? ["Close it","Pause it"] : ["Pause it","Go back ten seconds","Close it"]})[view];
  byId("suggestions").innerHTML = examples.map((text) => `<button class="suggestion" type="button">${escapeHTML(text)}</button>`).join("");
  byId("suggestions").querySelectorAll("button").forEach((button) => button.addEventListener("click", () => {byId("utterance").value = button.textContent; byId("utterance").focus();}));
}

async function handleAction(element) {
  const actionId = element.dataset.action;
  const ticket = element.dataset.decisionTicket;
  delete element.dataset.decisionTicket;
  element.disabled = true;
  try {
    const response = ticket ? await api("/api/demo/execute",{ticket,action_id:actionId}) : await api("/api/demo/action",{action_id:actionId,state_version:current.state_version});
    render(response);
    const receipt = {...response.receipt, browser_event:"DOM button click", element:`[data-action="${actionId}"]`, observed_view:current.state.view, observed_state_version:current.state_version};
    showReceipt(receipt);
    byId("notice").textContent = "";
    document.dispatchEvent(new CustomEvent("jevkit:receipt",{detail:receipt}));
  } catch (error) {
    byId("notice").textContent = error.message;
    if (ticket) showReceipt({executed:false,action_id:actionId,reason:error.message});
    element.disabled = false;
  }
}

function showReceipt(receipt) {
  byId("receipt-status").textContent = receipt.executed ? "EXECUTED" : "REJECTED";
  byId("receipt-status").className = `tag ${receipt.executed ? "success" : "rejected"}`;
  byId("receipt").className = "receipt-details";
  byId("receipt").innerHTML = receipt.executed ? `<code>${escapeHTML(receipt.action_id)}</code><br>${receipt.source === "model" ? "Model-selected" : "Manual"} DOM button click<br>State ${receipt.from_version} → ${receipt.to_version} · ${escapeHTML(receipt.observed_view || current.state.view)}` : `No action applied.<br>${escapeHTML(receipt.reason || "The decision did not select an action.")}`;
}

function showResult(result) {
  const title = result.candidate_id || ({no_match:"No matching action",abstain:"Needs clarification",stale:"State changed — discarded"})[result.status] || result.status;
  byId("chosen-action").innerHTML = `${escapeHTML(title)}<span>${escapeHTML(result.status)} · state ${result.state_version} · raw choice ${escapeHTML(result.raw_selected_id || "—")}</span>`;
  const timing = result.timing || {};
  const latency = timing.decision_ms ?? timing.total_ms ?? timing.inference_ms ?? timing.model_ms ?? timing.elapsed_ms;
  byId("latency").innerHTML = `${Number.isFinite(latency) ? latency.toFixed(1) : "—"}<small> ms</small>`;
  byId("margin").textContent = Number.isFinite(result.margin) ? result.margin.toFixed(3) : "—";
  const cache = result.cache || {};
  byId("cache-info").textContent = Object.entries(cache).map(([key,value]) => `${key}: ${typeof value === "object" ? JSON.stringify(value) : value}`).join(" · ") || "No cache details supplied";
  byId("result-json").textContent = JSON.stringify(result,null,2);
  const scores = Object.entries(result.scores || {}).sort((a,b) => b[1]-a[1]).slice(0,5);
  byId("score-list").innerHTML = scores.map(([id,score]) => `<div class="score-item"><span>${escapeHTML(id)}</span><b>${score.toFixed(3)}</b><progress class="score-bar" value="${Math.max(0,Math.min(1,score))}" max="1"></progress></div>`).join("");
}

function executeBrowserOperation(operation) {
  if (!operation || operation.type !== "click") return;
  pendingOperation = null;
  byId("execute-pending").hidden = true;
  const target = [...document.querySelectorAll("[data-action]")].find((element) => element.dataset.action === operation.action_id);
  if (!target || current.state_version !== operation.state_version) {
    showReceipt({executed:false,reason:"The browser state changed before the selected button could be clicked."});
    byId("notice").textContent = "Stale browser operation rejected. Ask again with the current page.";
    return;
  }
  // The model selects an allowlisted action, not executable source. Invoke the
  // same real DOM control a person uses; the server validates its issued ticket.
  target.dataset.decisionTicket = operation.ticket;
  target.classList.add("model-target");
  target.click();
}

byId("command-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (decisionBusy || !current) return;
  const utterance = byId("utterance").value.trim();
  if (!utterance) return;
  decisionBusy = true;
  pendingOperation = null;
  byId("execute-pending").hidden = true;
  byId("decide-button").disabled = true;
  byId("decision-status").textContent = "Thinking locally…";
  byId("notice").textContent = "You can still change the page while inference runs. Old decisions will be rejected.";
  const started = performance.now();
  try {
    const response = await api("/api/demo/decide",{utterance});
    render(response);
    showResult(response.result);
    byId("decision-status").textContent = `${((performance.now()-started)/1000).toFixed(2)}s round trip`;
    byId("notice").textContent = "";
    if (response.browser_operation) {
      if (byId("auto-execute").checked) executeBrowserOperation(response.browser_operation);
      else {pendingOperation = response.browser_operation; byId("execute-pending").hidden = false; showReceipt({executed:false,reason:"Decision ready; click execution is waiting for you."});}
    } else showReceipt({executed:false,reason:response.result.status === "stale" ? "The page changed during inference. The old result cannot execute." : "The model declined to select a browser action."});
  } catch (error) {
    byId("notice").textContent = error.message;
    byId("decision-status").textContent = "Decision failed";
  } finally {
    decisionBusy = false;
    byId("decide-button").disabled = false;
  }
});
byId("execute-pending").addEventListener("click",() => executeBrowserOperation(pendingOperation));
api("/api/demo/state").then(render).catch((error) => {byId("notice").textContent = error.message;});
setInterval(() => api("/api/demo/state").then(render).catch(() => {}),1500);
