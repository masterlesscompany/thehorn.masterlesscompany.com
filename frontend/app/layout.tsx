import "./_ds/parchment.css";
import Link from "next/link";

export const metadata = {
  title: "에르덴 용병단 — 자율 캐릭터 자동대전",
  description: "캐릭터를 조종하는 게임이 아니라 고용하는 게임. AI 에이전트의 판단을 관찰하는 도구.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <header
          style={{
            borderBottom: "1px solid var(--color-divider)",
            background: "var(--color-surface)",
          }}
        >
          <div
            className="row"
            style={{ maxWidth: 1180, margin: "0 auto", padding: "10px 20px", justifyContent: "space-between" }}
          >
            <Link href="/" style={{ color: "var(--color-text)", fontWeight: 700, fontFamily: "var(--font-heading)" }}>
              에르덴 용병단
            </Link>
            <nav className="row small">
              <Link href="/roster">로스터</Link>
              <Link href="/experiments">실험</Link>
              <a href="https://github.com/whoareryu" target="_blank" rel="noreferrer" className="faint">
                코드
              </a>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
