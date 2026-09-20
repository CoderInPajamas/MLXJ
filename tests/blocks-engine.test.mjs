import test from 'node:test';
import assert from 'node:assert/strict';
import {createGame, rotations, legalPlacements, applyPlacement, move, rotate, hardDrop, setBoard, boardMetrics, fits} from '../src/jev_mlx/static/blocks-engine.js';

test('seven-bag is seeded, repeatable, and contains every piece once', () => {
  const a = createGame(42), b = createGame(42), c = createGame(43);
  assert.deepEqual(a, b);
  assert.notDeepEqual([a.current, ...a.queue], [c.current, ...c.queue]);
  assert.equal(new Set([a.current, ...a.queue.slice(0, 6)]).size, 7);
});
test('unique rotations and every vertical hard-drop placement are offered', () => {
  const game = createGame();
  assert.equal(rotations('O').length, 1);
  assert.equal(rotations('I').length, 2);
  assert.equal(rotations('T').length, 4);
  for (const [type, count] of [['O',9], ['I',17], ['T',34]]) {
    game.current = type;
    const choices = legalPlacements(game);
    assert.equal(choices.length, count);
    assert.equal(new Set(choices.map((p) => p.id)).size, count);
    for (const p of choices) {
      assert.ok(fits(game.board, p.matrix, p.x, p.y));
      assert.ok(!fits(game.board, p.matrix, p.x, p.y + 1));
    }
  }
});
test('four-row clear removes rows, awards 800 points, and matches predicted facts', () => {
  const game = createGame();
  const rows = Array(16).fill('..........').concat(Array(4).fill('JJJJ.JJJJJ'));
  setBoard(game, rows, 'I');
  const choice = legalPlacements(game).find((p) => p.rotation === 1 && p.x === 4);
  assert.equal(choice.lines, 4); assert.equal(choice.holes, 0); assert.equal(choice.maxHeight, 0);
  const receipt = applyPlacement(game, choice.id);
  assert.equal(receipt.lines, 4); assert.equal(game.score, 800); assert.equal(game.lines, 4);
  assert.ok(game.board.flat().every((cell) => cell === null));
  assert.equal(game.pieces, 1); assert.equal(receipt.toVersion, receipt.fromVersion + 1);
});
test('bad placements stay available, with factual holes instead of solver filtering', () => {
  const game = createGame();
  setBoard(game, Array(19).fill('..........').concat('....J.....'), 'I');
  const choices = legalPlacements(game);
  assert.equal(choices.length, 17);
  assert.ok(choices.some((p) => p.holes > 0));
  assert.ok(choices.some((p) => p.holes === 0));
  for (const p of choices) {
    const clone = structuredClone(game); applyPlacement(clone, p.id);
    assert.equal(boardMetrics(clone.board).holes, p.holes);
    assert.equal(boardMetrics(clone.board).maxHeight, p.maxHeight);
  }
});
test('manual movement, rotation and hard drop obey walls and collision', () => {
  const game = createGame();
  for (let i = 0; i < 20; i++) move(game, -1);
  assert.equal(game.active.x, 0);
  assert.equal(move(game, -1), false);
  rotate(game);
  const receipt = hardDrop(game);
  assert.equal(receipt.executed, true);
  assert.equal(game.board.flat().filter(Boolean).length, 4);
});
test('invalid choices cannot mutate board and blocked board ends game', () => {
  const game = createGame();
  const before = structuredClone(game);
  assert.equal(applyPlacement(game, 'invented').executed, false);
  assert.deepEqual(game, before);
  setBoard(game, Array(20).fill('JJJJJJJJJJ'), 'T');
  assert.equal(game.gameOver, true); assert.equal(legalPlacements(game).length, 0);
  assert.equal(hardDrop(game).executed, false);
});
