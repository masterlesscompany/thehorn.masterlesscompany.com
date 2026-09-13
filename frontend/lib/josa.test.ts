import assert from "node:assert/strict";
import { test } from "node:test";
import { hasFinal, josa, withJosa } from "./josa.ts";

test("받침을 보고 조사를 고른다", () => {
  assert.equal(josa("가렛 발렌", "은"), "은");
  assert.equal(josa("일레인 모어", "은"), "는");
  assert.equal(josa("바르가스", "을"), "를");
  assert.equal(josa("카일 브란트", "이"), "가");
});

test("받침 판정", () => {
  assert.equal(hasFinal("칼"), true);
  assert.equal(hasFinal("나"), false);
  assert.equal(hasFinal("kyle"), null);
  assert.equal(hasFinal(""), null);
});

test("한글이 아니면 병기한다", () => {
  assert.equal(josa("kyle", "은"), "은(는)");
  assert.equal(withJosa("vargas", "을"), "vargas을(를)");
});

test("ㄹ 받침은 로", () => {
  assert.equal(josa("서울", "으로"), "로");
  assert.equal(josa("강타", "으로"), "로");
  assert.equal(josa("손", "으로"), "으로");
});

test("붙여서 돌려준다", () => {
  assert.equal(withJosa("가렛 발렌", "은"), "가렛 발렌은");
  assert.equal(withJosa("일레인 모어", "가"), "일레인 모어가");
});
