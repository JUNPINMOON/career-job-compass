# ⚠ 볼트 우선 계약 — 모든 에이전트 공통 (Claude / Codex / Gemini / agy)

**이 레포에서 작업을 시작하기 전에 반드시 읽는다:**

1. `C:\Users\mjb58\connect-ai-vault\00_MOC\Current Truth.md` — 프로젝트 라우팅 표(이 레포 = **4행 Career Compass PWA**)·안전선·핀 결정 대기. 이 표에 없는 맥락으로 작업 방향을 정하지 않는다.
2. 표의 이 프로젝트 행 → 정본 → 최신 handoff, 3 hop. 30K자 넘는 문서는 표에 적힌 섹션만 읽는다.
3. 과거 판단·기준·이력이 필요하면 `vault-recall "<질문>"` — 큐레이션·원본 두 층을 한 번에 검색한다.

**철칙:**

- **기존 산출물을 재생성·덮어쓰기 전에 기존 파일을 먼저 연다.** 크기가 10배 이상 다르거나 내용 계열이 다르면 덮어쓰지 말고 멈추고 보고한다. (2026-07-27 실사고: us-execution에서 1.1MB 대시보드가 1.6KB 차단 페이지로 반복 덮어써졌다)
- 완료 주장은 증거(diff·테스트·exit code·산출물)와 함께. 안 됐으면 `DONE_PARTIAL` / `CLAIMED_NOT_VERIFIED`로 정직하게 보고한다.
- `requirements/ledger.yaml`이 이 레포에 있으면 `py C:\Users\mjb58\Scripts\reqgate\reqgate.py --root . check` 통과가 완료 조건이다. **원장 행 삭제 금지 — 지우면 게이트가 잡는다.**
- 이 프로젝트를 실제로 진척시켰으면 끝내기 전에 Current Truth의 해당 행과 `확인` 날짜를 갱신한다.

---

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
