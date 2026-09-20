import {createGame, cloneState, rotations, legalPlacements, applyPlacement, move, rotate, hardDrop, dropY, setBoard, boardMetrics, WIDTH, HEIGHT} from "./blocks-engine.js";

const $ = (id) => document.getElementById(id);
const canvas = $("board");
const ctx = canvas.getContext("2d");
const colors = {I: "#68e1e8", O: "#efd67b", T: "#b697ef", S: "#7edbb0", Z: "#ed8295", J: "#7ea7ed", L: "#f4ad72"};
const params = new URLSearchParams(location.search);
const seed = /^\d+$/.test(params.get("seed") || "") ? Number(params.get("seed")) >>> 0 : 42;
let game = createGame(seed);
let generation = 0;
let inFlight = false;
let auto = false;
let mode = "ready";
let animation = null;
let nextDelay = 0;
let clock = 0;
let flash = null;
let backendReady = false;
let modelIdentity = null;
let lastResult = null;
let placementCache = {game: null, version: -1, value: []};
const transcript = [];
window.blocksTranscript = transcript;
window.blocksSession = {format: "mlxj-blocks-v1", started_at: new Date().toISOString(), initial_seed: seed, rules: "10x20; seven-bag; all legal vertical drops; no gravity timer; 100/300/500/800 line-clear score; no solver", input: "structured board and computed placement outcomes, not screenshots"};

function event(kind, data = {}) { transcript.push({kind, at: new Date().toISOString(), ...data}); }
function boardRows() { return game.board.map((row) => row.map((cell) => cell || ".").join("")); }
function placements() {
  if (placementCache.game !== game || placementCache.version !== game.version) placementCache = {game, version: game.version, value: legalPlacements(game)};
  return placementCache.value;
}
function status(label, type = "") { $("game-status").textContent = label; $("status-dot").className = `status-dot ${type}`; }
function controls() {
  $("step-ai").disabled = inFlight || game.gameOver || !backendReady;
  $("start-ai").disabled = inFlight || auto || game.gameOver || !backendReady;
  $("start-ai").innerHTML = auto ? "<span>●</span> Local AI is playing" : "<span>▶</span> Start local AI";
  $("pause").disabled = !auto && !inFlight;
  $("seed-label").textContent = `SEED ${game.seed}`;
  $("connection-label").textContent = mode === "manual" ? "MANUAL PLAY" : backendReady ? (inFlight || auto ? "LOCAL MODEL · LIVE" : "LOCAL MODEL · CONNECTED") : "LOCAL BACKEND · OFFLINE";
}
function invalidate(reason) {
  generation++; auto = false; nextDelay = 0;
  if (animation) { const pending = animation; animation = null; pending.resolve(false); }
  event("control", {action: reason, state_version: game.version});
}
function reset(newSeed = seed) {
  invalidate("reset"); game = createGame(newSeed); flash = null; mode = "ready";
  $("notice").textContent = inFlight ? "Reset. The pending decision will be recorded and discarded." : "Same seed, fresh board. Earlier decisions remain in the run log.";
  status("Ready to play"); controls(); render();
}
function pause() {
  invalidate("pause"); mode = "paused";
  status("Paused"); $("notice").textContent = inFlight ? "Pending result will not move a piece." : "Continue with Start local AI or One piece.";
  controls(); render();
}
function manual(action) {
  if (game.gameOver) return;
  invalidate("manual"); mode = "manual";
  let receipt;
  if (action === "left") move(game, -1);
  if (action === "right") move(game, 1);
  if (action === "down") move(game, 0, 1);
  if (action === "rotate") rotate(game);
  if (action === "drop") { receipt = hardDrop(game); showClear(receipt); }
  event("manual", {action, receipt, state_version: game.version, board_after: boardRows()});
  $("notice").textContent = "Manual play. Arrow keys move / rotate; space drops.";
  status(game.gameOver ? "Game over" : "You are playing", game.gameOver ? "error" : "");
  controls(); render();
}

function requestFor(moves) {
  return {
    kind: "enum", state_version: game.version,
    question: "Choose a single legal final placement for the current falling block, following the user's goal. Every candidate is executable. Candidate descriptions are exact resulting board facts, calculated by the game rules. The game supplies no recommended placement. A hole is an empty cell below an occupied cell in the same column. Smaller height and roughness mean a lower, flatter stack. Choose only from the supplied placements.",
    utterance: "Drop the current piece into one of the listed legal placements now. Choose the placement you judge best; any equally good placement is acceptable. Prefer clearing rows when possible, then fewer holes and a low, flat stack. It is fine if this turn clears no rows.",
    state: {game: "MLXJ Blocks", width: WIDTH, height: HEIGHT, coordinates: "origin top-left; x right; y down; '.' empty", board_rows: boardRows(), current_piece: game.current, next_pieces: game.queue.slice(0, 3), lines: game.lines, pieces: game.pieces, current_metrics: boardMetrics(game.board), move_rule: "Choose rotation and column before a straight vertical hard drop; no sideways movement after dropping."},
    candidates: moves.map((p) => ({id: p.id, description: `Drop ${p.type}, orientation ${p.rotation}, leftmost column ${p.x + 1}: clears ${p.lines} rows; resulting holes ${p.holes}, max height ${p.maxHeight}, total column heights ${p.aggregateHeight}, surface roughness ${p.roughness}.`, value: {rotation: p.rotation, x: p.x}})),
  };
}
function animatePlacement(placement, epoch, version) {
  return new Promise((resolve) => { animation = {placement, epoch, version, elapsed: 0, duration: 480, resolve}; });
}
function showClear(receipt) {
  if (receipt?.executed) flash = {elapsed: 0, duration: receipt.lines ? 950 : 350, lines: receipt.lines, rows: receipt.clearedRows, x: receipt.x, y: receipt.y};
}
async function stepAI() {
  if (inFlight || game.gameOver || !backendReady) return null;
  const moves = placements();
  if (!moves.length) return null;
  const epoch = generation;
  const version = game.version;
  const request = requestFor(moves);
  const started = performance.now();
  const entry = {kind: "decision", status: "pending", started_at: new Date().toISOString(), request, board_before: boardRows()};
  transcript.push(entry);
  inFlight = true; mode = "ai";
  status("Model is choosing…", "busy"); $("notice").textContent = "";
  controls(); render();
  try {
    const response = await fetch("/v1/decide", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(request)});
    const result = await response.json();
    entry.result = result;
    if (!response.ok) throw new Error(result.message || result.error || `HTTP ${response.status}`);
    lastResult = result; modelIdentity = result.model;
    $("model-name").textContent = result.model?.name || result.model?.path || "Local MLX model";
    $("decision-time").textContent = Number.isFinite(result.timing?.decision_ms) ? `${Math.round(result.timing.decision_ms).toLocaleString()} ms` : "—";
    $("cache-label").textContent = `Cache: ${result.cache?.scope || "unreported"} · ${result.cache?.reused_tokens ?? 0} reused tokens · margin ${Number(result.margin).toFixed(3)} (uncalibrated)`;
    $("result-json").textContent = JSON.stringify(result, null, 2);
    if (epoch !== generation || version !== game.version || result.state_version !== version) {
      auto = false;
      if (epoch === generation) { mode = "paused"; status("Stale result rejected", "error"); }
      entry.receipt = {executed: false, reason: "stale_state", requested_version: version, current_version: game.version};
      $("decision-outcome").textContent = "Discarded";
      $("choice-label").textContent = "Old decision discarded";
      $("choice-detail").textContent = "The board or controls changed while the model was working.";
      return entry;
    }
    const chosen = moves.find((p) => p.id === result.candidate_id);
    if (result.status !== "selected" || !chosen) {
      auto = false; mode = "paused";
      entry.receipt = {executed: false, reason: result.status === "selected" ? "invalid_candidate" : result.status};
      $("choice-label").textContent = result.status === "abstain" ? "Model abstained" : result.status === "no_match" ? "No matching move" : "Invalid model result";
      $("choice-detail").textContent = "Run paused. No fallback move or automatic retry.";
      $("decision-outcome").textContent = "No move";
      status("Model stopped", "error");
      return entry;
    }
    $("choice-label").textContent = `${chosen.type} → column ${chosen.x + 1}`;
    $("choice-detail").textContent = `Orientation ${chosen.rotation} · ${chosen.lines} rows cleared · ${chosen.holes} holes · height ${chosen.maxHeight}`;
    $("decision-outcome").textContent = "Dropping…";
    status("Dropping the chosen piece");
    const completed = await animatePlacement(chosen, epoch, version);
    if (!completed || epoch !== generation || version !== game.version) {
      entry.receipt = {executed: false, reason: "stale_during_animation", requested_version: version, current_version: game.version};
      $("decision-outcome").textContent = "Discarded";
      return entry;
    }
    entry.receipt = applyPlacement(game, chosen.id);
    showClear(entry.receipt);
    $("decision-outcome").textContent = entry.receipt.executed ? (entry.receipt.lines ? `+${entry.receipt.lines} lines` : "Placed") : "Rejected";
    if (game.gameOver) { auto = false; mode = "over"; status("Game over", "error"); }
    else { mode = auto ? "ai" : "paused"; status(auto ? "Local AI is playing" : "One piece complete"); }
    return entry;
  } catch (error) {
    entry.error = String(error.message || error);
    entry.receipt = {executed: false, reason: "request_failed"};
    if (epoch === generation) {
      auto = false; mode = "paused"; status("Request failed", "error");
      $("notice").textContent = `${entry.error}. Run paused; no automatic retry.`;
      $("decision-outcome").textContent = "Error";
    }
    return entry;
  } finally {
    entry.status = "complete"; entry.completed_at = new Date().toISOString();
    entry.elapsed_ms = performance.now() - started; entry.board_after = boardRows();
    entry.game_after = {seed: game.seed, pieces: game.pieces, lines: game.lines, score: game.score, game_over: game.gameOver, state_version: game.version};
    inFlight = false; nextDelay = auto ? 500 : 0;
    controls(); render();
    window.dispatchEvent(new CustomEvent("mlxj-blocks:decision", {detail: entry}));
  }
}
function startAI() {
  if (inFlight || game.gameOver || !backendReady) return;
  auto = true; mode = "ai"; event("control", {action: "start_ai", state_version: game.version});
  void stepAI();
}

function roundRect(x, y, width, height, radius = 6) { ctx.beginPath(); ctx.roundRect(x, y, width, height, radius); }
function text(value, x, y, size = 13, color = "#a3b6ce", weight = 500, align = "left") {
  ctx.fillStyle = color; ctx.font = `${weight} ${size}px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif`; ctx.textAlign = align; ctx.fillText(value, x, y);
}
function block(x, y, size, type, alpha = 1, ghost = false) {
  ctx.save(); ctx.globalAlpha = alpha;
  const color = colors[type] || "#90a3b8";
  roundRect(x + 1.5, y + 1.5, size - 3, size - 3, 3);
  if (ghost) { ctx.strokeStyle = color; ctx.lineWidth = 1.2; ctx.stroke(); ctx.fillStyle = color + "0e"; ctx.fill(); }
  else { ctx.fillStyle = color; ctx.fill(); ctx.fillStyle = "#ffffff33"; ctx.fillRect(x + 5, y + 4, size - 10, 2); ctx.fillStyle = "#00000016"; ctx.fillRect(x + 4, y + size - 6, size - 8, 2); }
  ctx.restore();
}
function drawPiece(matrix, x, y, type, alpha = 1, ghost = false, size = 28) {
  matrix.forEach((row, dy) => row.forEach((cell, dx) => { if (cell) block(x + dx * size, y + dy * size, size, type, alpha, ghost); }));
}
function render() {
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  if (canvas.width !== 640 * ratio || canvas.height !== 700 * ratio) { canvas.width = 640 * ratio; canvas.height = 700 * ratio; }
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, 640, 700);
  const background = ctx.createLinearGradient(0, 0, 640, 700); background.addColorStop(0, "#152335"); background.addColorStop(1, "#0f1726"); ctx.fillStyle = background; ctx.fillRect(0, 0, 640, 700);
  const x0 = 34, y0 = 44, size = 28, boardWidth = WIDTH * size, boardHeight = HEIGHT * size;
  text("THE BOARD", x0, 27, 9, "#728ba7", 700);
  text(`${game.current || "—"} / ${placements().length} legal landings`, x0 + boardWidth, 27, 9, "#728ba7", 500, "right");
  roundRect(x0 - 7, y0 - 7, boardWidth + 14, boardHeight + 14, 9); ctx.fillStyle = "#080f1b"; ctx.fill(); ctx.strokeStyle = "#314256"; ctx.lineWidth = 1; ctx.stroke();
  ctx.strokeStyle = "#192437"; ctx.lineWidth = .6;
  for (let x = 1; x < WIDTH; x++) { ctx.beginPath(); ctx.moveTo(x0 + x * size, y0); ctx.lineTo(x0 + x * size, y0 + boardHeight); ctx.stroke(); }
  for (let y = 1; y < HEIGHT; y++) { ctx.beginPath(); ctx.moveTo(x0, y0 + y * size); ctx.lineTo(x0 + boardWidth, y0 + y * size); ctx.stroke(); }
  game.board.forEach((row, y) => row.forEach((type, x) => { if (type) block(x0 + x * size, y0 + y * size, size, type); }));
  if (game.active && !game.gameOver) {
    const active = animation ? {x: animation.placement.x, y: animation.placement.y * Math.pow(Math.min(1, animation.elapsed / animation.duration), 2), rotation: animation.placement.rotation} : game.active;
    const matrix = rotations(game.current)[active.rotation];
    const ghostY = dropY(game.board, matrix, active.x, Math.floor(active.y));
    if (ghostY !== null) drawPiece(matrix, x0 + active.x * size, y0 + ghostY * size, game.current, .6, true);
    drawPiece(matrix, x0 + active.x * size, y0 + active.y * size, game.current, inFlight && !animation ? .6 + .2 * Math.sin(clock / 250) : 1);
  }
  if (flash?.lines) {
    const opacity = Math.max(0, 1 - flash.elapsed / flash.duration);
    ctx.fillStyle = `rgba(101,228,231,${opacity * .35})`;
    for (const y of flash.rows) ctx.fillRect(x0, y0 + y * size, boardWidth, size);
  }
  const sx = 364;
  text("SCORE", sx, 67, 10, "#7d93ae", 700);
  text(String(game.score).padStart(4, "0"), sx - 2, 121, 54, "#f1f6ff", 650);
  text("LINES", sx, 161, 9, "#7d93ae", 700); text(String(game.lines).padStart(2, "0"), sx, 198, 31, "#65e4e7", 600);
  text("PIECES", sx + 118, 161, 9, "#7d93ae", 700); text(String(game.pieces).padStart(2, "0"), sx + 118, 198, 31, "#c8d6e9", 600);
  ctx.fillStyle = "#2a3a50"; ctx.fillRect(sx, 221, 224, 1);
  text("UP NEXT", sx, 248, 9, "#7d93ae", 700);
  game.queue.slice(0, 3).forEach((piece, index) => {
    const matrix = rotations(piece)[0]; const py = 270 + index * 78;
    text(String(index + 1).padStart(2, "0"), sx, py + 24, 10, "#4e6682", 500);
    drawPiece(matrix, sx + 35, py + (2 - matrix.length) * 12, piece, index === 0 ? 1 : .4, false, 24);
  });
  ctx.fillStyle = "#2a3a50"; ctx.fillRect(sx, 515, 224, 1);
  text(inFlight ? "CHOOSING A LANDING…" : auto ? "LOCAL AI AT THE CONTROLS" : mode === "manual" ? "YOU ARE AT THE CONTROLS" : game.gameOver ? "NO LEGAL LANDINGS LEFT" : "READY WHEN YOU ARE", sx, 549, 9, inFlight ? "#ffbc7c" : "#92afc7", 700);
  text("Each piece = one model choice.", sx, 572, 11, "#617c99");
  text("Rows clear. Mistakes stay.", sx, 591, 11, "#617c99");
  if (flash?.lines) text(`+${flash.lines} ${flash.lines === 1 ? "LINE" : "LINES"}`, x0 + boardWidth / 2, y0 + 258, 32, "#e9ffff", 750, "center");
  if (game.gameOver) {
    ctx.fillStyle = "#080f1bcc"; ctx.fillRect(x0, y0, boardWidth, boardHeight);
    text("GAME OVER", x0 + boardWidth / 2, y0 + 248, 27, "#ffffff", 700, "center");
    text(`${game.lines} lines · ${game.pieces} pieces`, x0 + boardWidth / 2, y0 + 282, 14, "#b6cadf", 500, "center");
    text("Reset to play again", x0 + boardWidth / 2, y0 + 309, 11, "#7f9ab4", 500, "center");
  }
  text("01", 34, 652, 11, "#45617e", 600); text("STATE", 65, 641, 8, "#6a819d", 700); text("board + legal drops", 65, 659, 11, "#a1b4cc");
  text("→", 224, 653, 18, "#436079"); text("02", 264, 652, 11, "#45617e", 600); text("LOCAL MODEL", 295, 641, 8, "#6a819d", 700); text("choose one", 295, 659, 11, "#a1b4cc");
  text("→", 437, 653, 18, "#436079"); text("03", 477, 652, 11, "#45617e", 600); text("GAME", 508, 641, 8, "#6a819d", 700); text("drop it", 508, 659, 11, "#a1b4cc");
}
function update(ms) {
  clock += ms;
  if (flash) { flash.elapsed += ms; if (flash.elapsed > flash.duration) flash = null; }
  if (animation) {
    animation.elapsed += ms;
    if (animation.elapsed >= animation.duration) { const pending = animation; animation = null; pending.resolve(true); }
  }
  if (auto && !inFlight && !game.gameOver) { nextDelay -= ms; if (nextDelay <= 0) void stepAI(); }
}
let lastFrame = performance.now();
function frame(now) { update(Math.min(100, now - lastFrame)); lastFrame = now; render(); requestAnimationFrame(frame); }
window.advanceTime = (ms) => { update(Math.max(0, Number(ms) || 0)); render(); };
window.render_game_to_text = () => JSON.stringify({coordinates: "origin top-left, x right, y down", mode, seed: game.seed, board: boardRows(), current: game.current, active: game.active, next: game.queue.slice(0, 3), score: game.score, lines: game.lines, pieces: game.pieces, state_version: game.version, game_over: game.gameOver, inFlight, animating: Boolean(animation), auto, backendReady, legal_placements: placements().map((p) => ({id: p.id, x: p.x, y: p.y, rotation: p.rotation, lines: p.lines, holes: p.holes})), last_choice: lastResult?.candidate_id || null});
// Explicit test hooks. Every setup is logged; they are not part of AI gameplay.
window.blocksDebug = {state: () => cloneState(game), legalPlacements: () => placements(), request: () => requestFor(placements()), stepAI, reset, manual, setBoard: (rows, current) => { invalidate("test_setup"); setBoard(game, rows, current); event("test_setup", {board: boardRows(), current}); controls(); render(); }};
$("start-ai").addEventListener("click", startAI);
$("step-ai").addEventListener("click", () => { auto = false; void stepAI(); });
$("pause").addEventListener("click", pause);
$("reset").addEventListener("click", () => reset());
$("manual-mode").addEventListener("click", () => manual("enter"));
$("download").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify({session: window.blocksSession, model: modelIdentity, state: JSON.parse(window.render_game_to_text()), events: transcript}, null, 2)], {type: "application/json"});
  const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `mlxj-blocks-seed-${game.seed}.json`; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 1000);
});
document.addEventListener("keydown", (event) => {
  if (["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName) || event.ctrlKey || event.metaKey || event.altKey) return;
  const action = {ArrowLeft: "left", ArrowRight: "right", ArrowDown: "down", ArrowUp: "rotate", " ": "drop"}[event.key];
  if (action) { event.preventDefault(); manual(action); }
  if (event.key.toLowerCase() === "f") { event.preventDefault(); if (document.fullscreenElement) void document.exitFullscreen(); else void $("game-shell").requestFullscreen().catch(() => {}); }
  if (event.key === "Escape" && document.fullscreenElement) void document.exitFullscreen();
});
window.addEventListener("resize", render);
document.addEventListener("fullscreenchange", render);
controls(); render(); requestAnimationFrame(frame);
fetch("/api/demo/state").then((response) => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); }).then((data) => {
  modelIdentity = data.model; backendReady = true;
  $("model-name").textContent = data.model?.name || data.model?.path || "Local MLX model"; controls();
}).catch(() => { status("Local backend unavailable", "error"); $("model-name").textContent = "Start jev-mlx serve to use a local model."; $("notice").textContent = "Manual play is available. AI needs the localhost MLX service."; });
