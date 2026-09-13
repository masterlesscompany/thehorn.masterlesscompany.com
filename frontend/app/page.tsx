import Link from "next/link";

// 투표 사용자 진입 화면(기획서 §11.2). 30초 안에 "뭐가 신기한지" — 한 문장 + 3장면 + 한 판 돌리기.
// 백엔드를 부르지 않는다. 꺼져 있어도 이 화면은 열린다.

const SCENES = [
  {
    kicker: "장면 1 · 이탈",
    title: "약탈병이 먼저 물러섰다",
    body: "두 살 딸이 집에 있는 아녜스는 HP 가 무너지면 단장의 방침을 버린다. 왜? 클릭하면 열린다 — 이탈 확률, 위험 성향 -40, 희생 수용도 -50 이 항목별로 남는다.",
    tag: "판정 인스펙터",
  },
  {
    kicker: "장면 2 · 포기",
    title: "단장이 철수를 명령했다",
    body: "어떻게 이기는가보다 먼저, 싸울 가치가 있는가. 승산이 임계 아래로 무너지면 단장은 작전을 다시 짜고, 안 되면 사람을 데리고 나온다.",
    tag: "재계획 → 포기",
  },
  {
    kicker: "장면 3 · 읽힘",
    title: "굴에 두고 온 사람에게서 배운다",
    body: "그것에게는 이름이 없다. 처음 데려간 사람의 이름으로 불리고, 회수하지 않은 대원에게서 배운 것이 다음 보스전에 카드로 펼쳐진다 — 출처 인물과 관측 수치가 함께.",
    tag: "학습 카드",
  },
];

export default function Home() {
  return (
    <main className="page page-narrow stack" style={{ gap: 28 }}>
      <section className="stack" style={{ gap: 12, paddingTop: 12 }}>
        <span className="tag tag-accent" style={{ alignSelf: "flex-start" }}>
          Wanted AI Championship 2026
        </span>
        <h1>캐릭터를 조종하는 게임이 아니라, 고용하는 게임.</h1>
        <p className="muted" style={{ fontSize: 16 }}>
          1360년대, 휴전으로 실직한 병사들이 자유중대를 짰다. 당신은 그중 가장 작은 중대의 <b>서기</b>다.
          칼을 들지 않고 장부를 든다 — 다섯 중 셋을 골라 보내고, 그다음부터 손을 뗀다. 전장에서는
          단장 AI 가 작전을 짜고 단원 AI 가 매 턴 판단한다. 그리고 <b>왜 그랬는지</b> 전부 숫자로 남는다.
        </p>
        <div className="row" style={{ marginTop: 4 }}>
          <Link href="/roster" className="btn btn-primary">
            한 판 돌리기 →
          </Link>
          <Link href="/experiments" className="btn">
            실험 결과 보기
          </Link>
        </div>
      </section>

      <section className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
        {SCENES.map((s) => (
          <div key={s.kicker} className="card" style={{ gap: 8 }}>
            <div className="card-kicker">{s.kicker}</div>
            <div className="card-title">{s.title}</div>
            <p className="small muted">{s.body}</p>
            <span className="tag tag-steel" style={{ alignSelf: "flex-start" }}>
              {s.tag}
            </span>
          </div>
        ))}
      </section>

      <section className="card" style={{ gap: 10 }}>
        <div className="card-kicker">이건 게임이 아니라 관찰 도구다</div>
        <p className="small muted">
          겉은 중세 용병단, 속은 &ldquo;AI 에이전트가 제약 속에서 얼마나 잘 판단하는가&rdquo;를 재는 장치다.
          그래픽은 없다. 대사와 흐름과 판정값만 있다. 왼쪽에서 일어나는 모든 일은 가운데에서 설명된다 —
          결정론적 가중치 → 수치 → 판단 축 → 모델의 사유.
        </p>
        <div className="row small faint">
          <span>지혜가 낮은 단원은 아군 상태를 못 본다</span>
          <span>·</span>
          <span>행운은 주사위에만 걸리고 판단엔 개입하지 않는다</span>
          <span>·</span>
          <span>같은 시드는 같은 판을 만든다</span>
        </div>
      </section>
    </main>
  );
}
