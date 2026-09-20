// Original, dependency-free rules for the turn-based MLXJ Blocks demo.
// Coordinates: top-left origin, x increases right, y increases down.
export const WIDTH = 10;
export const HEIGHT = 20;
export const SHAPES = {
  I: [[1, 1, 1, 1]], O: [[1, 1], [1, 1]],
  T: [[0, 1, 0], [1, 1, 1]], S: [[0, 1, 1], [1, 1, 0]],
  Z: [[1, 1, 0], [0, 1, 1]], J: [[1, 0, 0], [1, 1, 1]],
  L: [[0, 0, 1], [1, 1, 1]],
};
const copy = (value) => JSON.parse(JSON.stringify(value));
export function rotations(type) {
  let matrix = SHAPES[type];
  if (!matrix) throw new Error("Unknown piece");
  const result = [];
  const seen = new Set();
  for (let turn = 0; turn < 4; turn++) {
    const key = JSON.stringify(matrix);
    if (!seen.has(key)) { result.push(copy(matrix)); seen.add(key); }
    matrix = matrix[0].map((_, x) => matrix.map((row) => row[x]).reverse());
  }
  return result;
}
function random(game) {
  let x = game.rng | 0;
  x ^= x << 13; x ^= x >>> 17; x ^= x << 5;
  game.rng = x >>> 0;
  return game.rng / 4294967296;
}
function refill(game) {
  while (game.queue.length < 7) {
    const bag = Object.keys(SHAPES);
    for (let i = bag.length - 1; i > 0; i--) {
      const j = Math.floor(random(game) * (i + 1));
      [bag[i], bag[j]] = [bag[j], bag[i]];
    }
    game.queue.push(...bag);
  }
}
export function createGame(seed = 42) {
  const number = Number(seed) >>> 0;
  const game = {seed: number, rng: number || 0x6d2b79f5, board: Array.from({length: HEIGHT}, () => Array(WIDTH).fill(null)), queue: [], current: null, active: null, score: 0, lines: 0, pieces: 0, version: 0, gameOver: false, lastClear: 0};
  spawn(game);
  return game;
}
export function cloneState(game) { return copy(game); }
export function fits(board, matrix, x, y) {
  return matrix.every((row, dy) => row.every((cell, dx) => !cell || (x + dx >= 0 && x + dx < WIDTH && y + dy >= 0 && y + dy < HEIGHT && !board[y + dy][x + dx])));
}
export function dropY(board, matrix, x, start = 0) {
  if (!fits(board, matrix, x, start)) return null;
  let y = start;
  while (fits(board, matrix, x, y + 1)) y++;
  return y;
}
export function boardMetrics(board) {
  const heights = Array(WIDTH).fill(0);
  let holes = 0;
  for (let x = 0; x < WIDTH; x++) {
    let seen = false;
    for (let y = 0; y < HEIGHT; y++) {
      if (board[y][x]) { if (!seen) heights[x] = HEIGHT - y; seen = true; }
      else if (seen) holes++;
    }
  }
  return {holes, maxHeight: Math.max(...heights), aggregateHeight: heights.reduce((a, b) => a + b, 0), roughness: heights.slice(1).reduce((sum, h, i) => sum + Math.abs(h - heights[i]), 0), heights};
}
function lockBoard(board, matrix, x, y, type) {
  const landed = copy(board);
  matrix.forEach((row, dy) => row.forEach((cell, dx) => { if (cell) landed[y + dy][x + dx] = type; }));
  const clearedRows = landed.flatMap((row, rowIndex) => row.every(Boolean) ? [rowIndex] : []);
  const remaining = landed.filter((row) => !row.every(Boolean));
  const nextBoard = [...Array.from({length: clearedRows.length}, () => Array(WIDTH).fill(null)), ...remaining];
  return {board: nextBoard, clearedRows, lines: clearedRows.length};
}
export function legalPlacements(game) {
  if (game.gameOver || !game.current) return [];
  const moves = [];
  rotations(game.current).forEach((matrix, rotation) => {
    for (let x = 0; x <= WIDTH - matrix[0].length; x++) {
      const y = dropY(game.board, matrix, x);
      if (y === null) continue;
      const outcome = lockBoard(game.board, matrix, x, y, game.current);
      moves.push({id: `drop.${game.current}.r${rotation}.x${x}`, type: game.current, rotation, x, y, matrix, lines: outcome.lines, ...boardMetrics(outcome.board)});
    }
  });
  return moves;
}
function spawn(game) {
  refill(game);
  game.current = game.queue.shift();
  const matrix = rotations(game.current)[0];
  game.active = {x: Math.floor((WIDTH - matrix[0].length) / 2), y: 0, rotation: 0};
  const moves = legalPlacements(game);
  if (!moves.length) { game.gameOver = true; game.active = null; return; }
  if (!fits(game.board, matrix, game.active.x, 0)) {
    // Spawn preview only: no placement is executed or selected for the model.
    game.active = {x: moves[0].x, y: 0, rotation: moves[0].rotation};
  }
}
export function applyPlacement(game, id) {
  const move = legalPlacements(game).find((candidate) => candidate.id === id);
  if (!move) return {executed: false, reason: "Placement is no longer legal", stateVersion: game.version};
  return lock(game, move.matrix, move.x, move.y, move.rotation, id);
}
function lock(game, matrix, x, y, rotation, id) {
  const fromVersion = game.version;
  const type = game.current;
  const outcome = lockBoard(game.board, matrix, x, y, type);
  game.board = outcome.board;
  game.lines += outcome.lines;
  game.score += [0, 100, 300, 500, 800][outcome.lines];
  game.pieces++;
  game.lastClear = outcome.lines;
  game.version++;
  spawn(game);
  return {executed: true, id, type, rotation, x, y, fromVersion, toVersion: game.version, clearedRows: outcome.clearedRows, lines: outcome.lines, score: game.score, gameOver: game.gameOver};
}
export function move(game, dx, dy = 0) {
  if (game.gameOver || !game.active) return false;
  const matrix = rotations(game.current)[game.active.rotation];
  if (!fits(game.board, matrix, game.active.x + dx, game.active.y + dy)) return false;
  game.active.x += dx; game.active.y += dy; game.version++;
  return true;
}
export function rotate(game) {
  if (game.gameOver || !game.active) return false;
  const shapes = rotations(game.current);
  const next = (game.active.rotation + 1) % shapes.length;
  for (const offset of [0, -1, 1, -2, 2]) {
    if (fits(game.board, shapes[next], game.active.x + offset, game.active.y)) {
      game.active.rotation = next; game.active.x += offset; game.version++;
      return true;
    }
  }
  return false;
}
export function hardDrop(game) {
  if (game.gameOver || !game.active) return {executed: false, reason: "Game over"};
  const matrix = rotations(game.current)[game.active.rotation];
  const y = dropY(game.board, matrix, game.active.x, game.active.y);
  if (y === null) return {executed: false, reason: "Blocked"};
  return lock(game, matrix, game.active.x, y, game.active.rotation, `manual.${game.current}`);
}
export function setBoard(game, rows, current = game.current) {
  if (!Array.isArray(rows) || rows.length !== HEIGHT || rows.some((row) => row.length !== WIDTH)) throw new Error("Board must be 20 rows of 10 cells");
  if (!SHAPES[current]) throw new Error("Unknown current piece");
  game.board = rows.map((row) => Array.from(row, (cell) => cell === "." || cell === 0 || cell === null ? null : String(cell)));
  game.current = current; game.gameOver = false; game.version++;
  const candidates = legalPlacements(game);
  game.gameOver = candidates.length === 0;
  const first = candidates[0];
  game.active = first ? {x: first.x, y: 0, rotation: first.rotation} : null;
}
