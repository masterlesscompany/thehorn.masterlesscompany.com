import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { buildNameMap, KINDS, parseLine } from "./trace.ts";
import { narrate } from "./narrate.ts";

// 파이썬(backend/tests/test_store_replay.py)과 같은 파일을 읽는다 — 계약이 갈라질 수 없다.
const SAMPLE = new URL("../../docs/trace-samples/one-run.jsonl", import.meta.url);
const lines = readFileSync(SAMPLE, "utf-8").split("\n").filter(Boolean);
const events = lines.map(parseLine);

test("샘플 트레이스의 모든 줄이 알려진 종류다", () => {
  assert.ok(events.length > 100);
  assert.equal(events[0].kind, "run_start");
  assert.equal(events[events.length - 1].kind, "run_end");
  for (const e of events) assert.ok((KINDS as readonly string[]).includes(e.kind));
});

test("seq 는 1부터 빈틈없이 오른다", () => {
  events.forEach((e, i) => assert.equal(e.seq, i + 1));
});

test("이름 맵은 파티와 적을 전부 안다", () => {
  const names = buildNameMap(events);
  assert.equal(names.agnes, "아녜스");
  // 샘플에서는 마르탱이 굴에 끌려가 회수되지 않았다 — 그것이 그 이름을 얻는다
  // (기획서 v3 §8.5). 이름 맵은 mission_start 가 준 **그때의 이름**을 쓴다.
  assert.equal(names.minotaur, "마르탱을 데려간 것");
  assert.ok(Object.keys(names).length >= 4);
});

test("모든 이벤트가 빈 문장이 아닌 서사를 만든다", () => {
  const names = buildNameMap(events);
  for (const e of events) {
    const s = narrate(e, names);
    assert.ok(s.length > 3, `${e.kind}#${e.seq} 의 서사가 비었다`);
    assert.ok(!/undefined|\[object/.test(s), `${e.kind}#${e.seq}: ${s}`);
  }
});

test("서사는 id 가 아니라 이름을 쓴다", () => {
  const names = buildNameMap(events);
  const decisions = events.filter((e) => e.kind === "decision" && e.actor === "agnes");
  assert.ok(decisions.length > 0);
  for (const e of decisions) {
    const s = narrate(e, names);
    assert.ok(s.includes("아녜스"), s);
    assert.ok(!/\bagnes\b/.test(s), s);
  }
});

test("데모 하이라이트 장면이 샘플에 있다", () => {
  const kinds = new Set(events.map((e) => e.kind));
  for (const k of ["abandon", "boss_adapt", "replan_trigger", "flee", "compliance"]) assert.ok(kinds.has(k as never), k);
  const deviate = events.find((e) => e.kind === "compliance" && e.payload.verdict === "deviate");
  assert.ok(deviate, "이탈 장면이 없다");
});

// ─── QA 라운드 2 회귀 ──────────────────────────────────────────────────

test("서사에 조사 병기형이 남지 않는다", () => {
  const names = buildNameMap(events);
  const bad = events
    .map((e) => narrate(e, names))
    .filter((s) => /\(를\)|\(가\)|\(는\)|\(을\)|\(이\)|\(으로\)/.test(s));
  assert.deepEqual(bad, [], `기계 토큰이 남은 문장 ${bad.length}줄: ${bad.slice(0, 3).join(" / ")}`);
});

test("어떤 이벤트의 서사에도 영문 id 가 남지 않는다", () => {
  const names = buildNameMap(events);
  const ids = Object.keys(names);
  const pattern = new RegExp(`\\b(${ids.join("|")})\\b`);
  const bad = events.map((e) => narrate(e, names)).filter((s) => pattern.test(s));
  assert.deepEqual(bad, [], `id 가 남은 문장 ${bad.length}줄: ${bad.slice(0, 3).join(" / ")}`);
});

test("자기에게 거는 기술이 광역기처럼 읽히지 않는다", () => {
  const names = buildNameMap(events);
  const selfCast = events.filter(
    (e) => e.kind === "resolution" && e.payload.target === e.actor && (e.payload.strikes as unknown[]).length === 0,
  );
  assert.ok(selfCast.length > 0, "자기 대상 기술이 샘플에 없다");
  for (const e of selfCast) {
    const s = narrate(e, names);
    assert.ok(!s.includes("전장에 퍼진다"), s);
  }
});

test("변화 없는 적응은 같은 문장을 반복하지 않는다", () => {
  const names = buildNameMap(events);
  const adapts = events.filter((e) => e.kind === "boss_adapt");
  const noChange = adapts.filter((e) => (e.payload.effect as { no_change?: boolean })?.no_change);
  if (noChange.length === 0) return;
  const changed = adapts.filter((e) => !(e.payload.effect as { no_change?: boolean })?.no_change);
  const a = narrate(noChange[0], names);
  assert.ok(changed.every((e) => narrate(e, names) !== a), "변화 있는 적응과 없는 적응이 같은 문장이다");
});

test("지혜 마스킹이 서사에 드러난다", () => {
  const names = buildNameMap(events);
  const ctx = events.filter((e) => e.kind === "context" && (e.payload.masked as string[]).length > 0);
  assert.ok(ctx.length > 0);
  const s = narrate(ctx[0], names);
  assert.ok(/안 보인다/.test(s) && /지혜/.test(s), s);
});
