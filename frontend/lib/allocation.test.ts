import assert from "node:assert/strict";
import { test } from "node:test";
import { bump, compact, remaining, total, validate } from "./allocation.ts";

test("총량과 남은 포인트", () => {
  assert.equal(total({ str_: 6, con: 8, wis: 4 }), 18);
  assert.equal(remaining({ str_: 6 }, 18), 12);
});

test("한 능력치 몰빵은 8+12=20 까지 된다", () => {
  let a = {};
  for (let i = 0; i < 12; i++) a = bump(a, "str_", 1, 8, 18);
  assert.equal(total(a), 12);
  assert.equal(bump(a, "str_", 1, 8, 18), a); // 상한 20
});

test("총량을 넘는 bump 는 무시된다", () => {
  const a = { str_: 10, agi: 8 };
  assert.equal(bump(a, "con", 1, 8, 18), a);
});

test("음수로 내려가지 않는다", () => {
  assert.deepEqual(bump({}, "agi", -1, 8, 18), {});
});

test("검증 메시지", () => {
  assert.equal(validate({ str_: 6, con: 8, wis: 4 }, 8, 18), null);
  assert.match(validate({ str_: 19 }, 8, 18)!, /상한/);
  assert.match(validate({ str_: 10, agi: 9 }, 8, 18)!, /총량/);
});

test("compact 는 0 을 뺀다", () => {
  assert.deepEqual(compact({ str_: 3, agi: 0, wis: 2 }), { str_: 3, wis: 2 });
});
