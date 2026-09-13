// 한국어 조사 선택 — 받침을 보고 고른다. backend/core/agents/josa.py 의 쌍둥이.
//
// 이름이 화면에 그대로 나가므로 "가렛 발렌은(는)" 같은 문장을 두지 않는다.
// 한글이 아닌 글자로 끝나면 병기형으로 물러선다 — 로마자·숫자의 받침 여부는
// 읽는 사람마다 다르고, 틀리게 붙이는 것보다 병기가 낫다.

const PAIRS: Record<string, [string, string]> = {
  은: ["은", "는"],
  는: ["은", "는"],
  이: ["이", "가"],
  가: ["이", "가"],
  을: ["을", "를"],
  를: ["을", "를"],
  과: ["과", "와"],
  와: ["과", "와"],
  으로: ["으로", "로"],
  로: ["으로", "로"],
  에게: ["에게", "에게"],
};

const HANGUL_START = 0xac00;
const HANGUL_END = 0xd7a3;

/** 마지막 글자에 받침이 있는가. 한글이 아니면 null. */
export function hasFinal(word: string): boolean | null {
  if (!word) return null;
  const code = word.charCodeAt(word.length - 1);
  if (code < HANGUL_START || code > HANGUL_END) return null;
  return (code - HANGUL_START) % 28 !== 0;
}

export function josa(word: string, kind: keyof typeof PAIRS | string): string {
  const pair = PAIRS[kind];
  if (!pair) return "";
  const [withFinal, without] = pair;
  const final = hasFinal(word);
  if (final === null) return withFinal === without ? withFinal : `${withFinal}(${without})`;
  // ㄹ 받침은 '로' 를 쓴다 — "서울로", "칼로".
  if ((kind === "으로" || kind === "로") && final) {
    const code = word.charCodeAt(word.length - 1);
    if ((code - HANGUL_START) % 28 === 8) return "로";
  }
  return final ? withFinal : without;
}

/** 단어에 조사를 붙여 돌려준다. */
export function withJosa(word: string, kind: string): string {
  return `${word}${josa(word, kind)}`;
}
