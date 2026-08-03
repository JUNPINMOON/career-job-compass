# Public candidate inference exposure review — 2026-08-03

INFERENCE_REVIEW

상태: `DONE_PARTIAL`

이 문서는 공개 GitHub Pages 산출물의 추론 노출만 점검한다. 개인 피드백 원문,
프로필, 인증 세션, 토큰, 쿠키, private 엔진 산출물은 읽거나 포함하지 않았다.
완화안은 제안만 하며 이 문서에서 구현하지 않는다.

## 1. 점검 범위와 재현 가능한 근거

점검 대상은 다음 두 산출물이다.

- 로컬 공개 번들: `data/app-data.json`
- Pages 공개 번들: `https://junpinmoon.github.io/career-job-compass/data/app-data.json`

로컬 번들은 87 jobs, 99 programs, 186 funding, 20 sectors를 포함했다. Pages 응답은
HTTP 200이며 같은 87/99/186 수량과 `savedJobs=0`을 반환했다. 로컬과 원격의 바이트
크기는 다르므로 해시 동일성은 주장하지 않는다. 원격 `dataAsOf`는 `2026-08-02`였다.

공개 릴리스 검사(`scripts/check_release.py`)의 금지 키 집합과 별도 구조 검사를
실행했다. 두 번들의 결과는 다음과 같다.

- 토큰·쿠키·사용자 ID·개인 피드백·점수 trace 금지 키 적중: 0
- `preferenceSummary`: `rowCount=0`, `likedCount=0`, `dislikedCount=0`, `digest=null`
- `preferenceDiscovery`: `current=false`, 평가/긍정/발견 후보 모두 0
- `savedJobs`: 빈 목록
- `recommendationSource`: `baseline`
- 원격에서도 동일한 금지 키 검사 결과: 0

따라서 원문 피드백이나 인증값이 공개 번들에 직접 들어간 증거는 없다.

## 2. 확인된 추론 노출 위험

직접적인 개인 필드 노출은 없었지만, 다음 공개 정책 신호는 확인됐다.

- `jobEligibilityOverrides`에 후보 단위 해시 식별자와 정확한 자격 문턱이 공개되어 있다.
- 공개 통계에도 작은 집단의 제외 결과가 그대로 노출되어 있다.

이 조합은 개인의 이름이나 피드백을 노출하지는 않지만, 공개 후보 수·지역·요건과
결합할 때 개인화 게이트의 문턱과 사용자 정책 성향을 외부에서 역추론하게 할 수
있다. 즉 현재 판정은 **직접 개인정보 유출 없음, 소수 집계 기반 정책 추론 위험
있음**이다.

`decisionSupport`에서 한 건의 일반적인 “경력·학력 조건 대조” 문구가 검색됐으나,
개인 연령·전공·지역·자격의 실제 값이나 피드백 원문을 포함하지 않아 개인 조건의
직접 노출로 분류하지 않았다.

## 3. 완화안 (구현하지 않음)

MITIGATION_PROPOSAL_ONLY

1. 정확한 `jobEligibilityOverrides` ID, `minimumExperienceYears`,
   `eligibilityReason`는 공개 번들에서 제거하고 인증된 private 런타임에만 둔다.
2. 공개 통계가 필요하면 소수 억제와 거친 구간화만 사용하고, 작은 집단과 정확한
   문턱값을 동시에 내보내지 않는다.
3. 공개 릴리스 회귀 검사는 override 객체의 정확한 ID/문턱/사유 및 작은 집계를
   금지하고, `recommendationSource=baseline`과 빈 public preference archive를
   계속 요구한다.
4. 개인화된 설명과 정확한 제외 이유는 owner 인증 후 private overlay에서만
   표시한다. 공개 snapshot과 private gate의 성공을 하나의 상태로 합치지 않는다.

## 4. 공통 스키마 설계안 (구현 전)

볼트 `references\\opportunity-records.md`의 태그·상태 의미를 공개/비공개 생산물의
정규 필드로 맞춘다. 한 레코드에 여러 목표가 있으면 `goal`은 배열로 보존하고
`primary_goal`은 파생값으로만 둔다.

| 필드 | 허용 값 | 정합 규칙 |
| --- | --- | --- |
| `source_tier` | `official`, `media`, `agency`, `company_promo`, `self_report`, `estimated` | 볼트 `[공식]`·`[언론]`·`[대행업체]`·`[자사홍보]`·`[자기보고]`·`[추정]`와 일대일 매핑. 근거가 없으면 추정하지 않고 unknown으로 둔다. |
| `status` | `ongoing`, `expired`, `deadline_unknown` | 원문 posted/deadline과 현재성 증거로 결정. 날짜가 없으면 `deadline_unknown`; 새로 수집됐다는 사실만으로 ongoing으로 만들지 않는다. |
| `goal` | `employment`, `income`, `certification`, `people`, `health_pace`, `building` | 볼트 분류와 하는 일의 근거에서 추출. 개인 적합성 판단이 아니다. |
| `requirement_source` | `body`, `attachment`, `unknown` | 요건별로 근거 위치를 보존한다. 본문에 “붙임 참고”만 있으면 `unknown`이며 eligible로 승격하지 않는다. |

모든 요건에는 `source_url`, `retrieved_at`, 가능하면 첨부 파일 식별자/해시를 함께
둔다. 원문이 없으면 `[미확인]`, 접근 실패면 `[검색실패]`를 유지한다. 공개 어댑터는
이 snake_case 필드를 필요한 화면용 camelCase로 변환하되, private 메모·프로필 값은
어댑터 경계를 통과시키지 않는다.

권장 식별자는
`opportunity_id = sha256(canonical_source_url + source_key + normalized_title)`이며,
공개 `public_artifact_id`, private `vault_record_id`, `lineage_digest`를 별도로 둔다.

## 5. 첨부 요건 파서 판단

상태: `DONE_PARTIAL` (근거와 설계 확인 완료, 운영 수집기 연결은 구현/실행 보류)

볼트의 2026-08-03 표본 기록에서 mcee.go.kr 공식 공고 14건은 본문 HTML의 요건
필드가 비어 있고 “세부 응시자격 및 제출서류 등은 붙임 자료를 참고하시기
바랍니다”를 반복했다. 기존 레거시 조사에는 게시판의 `fileId/fileSeq`를
`hg/file/readDownloadFile.do`로 받아 HWPX(zip+xml)와 PDF를 추출하여 13건의 요건을
확보한 파일럿 근거가 이미 있다.

따라서 첨부 파서는 **필요하다**. 다음 운영 설계를 private 수집기에 연결할 때까지
공개 결과를 “자격 확인 완료”로 표시하지 않는다.

1. 게시판 HTML에서 첨부 링크와 `fileId/fileSeq`를 수집한다.
2. HWPX/PDF를 타입 판별·추출하고 원문 URL, 파일 해시, 수집 시각을 저장한다.
3. 학력/경력/연령/어학/기타를 항목별로 파싱하여 `requirement_source=attachment`로
   기록한다.
4. 첨부 접근 실패·파싱 실패는 `unknown`과 `[검색실패]`로 남기고, 본문 반복문구만
   보고 지원 가능 판정을 만들지 않는다.

## 6. 볼트 ↔ 공개 번들 교차참조 설계

현재 파일에서 `## 레코드` 헤딩을 세면 실제 레코드는 50건이다. Claude 인계의
“48건”은 현재 파일과 불일치하므로 그대로 채택하지 않는다. 공개 funding 186건과
볼트 레코드의 정규 URL 겹침은 0, 이름 부분문자열 겹침은 0, 제목 유사도 0.86 이상
후보도 0이었다. 따라서 현재는 자동 중복이라고 볼 근거가 없으며 186건을 50건에
자동 병합하지 않는다.

권장 양방향 구조는 다음과 같다.

- private crosswalk manifest: `public_artifact_id ↔ vault_record_anchor`,
  canonical URL, `source_tier`, `lineage_digest`, `last_seen`, `duplicate_status`를
  저장한다.
- public snapshot: 안정적인 공개 ID·출처·현재성·라인리지 요약만 저장하며 볼트
  경로, private note, 사용자 판단을 저장하지 않는다.
- 인증된 모바일 overlay: crosswalk가 확인된 경우에만 볼트의 공개 허용 필드를
  합친다. 매칭 전에는 공개 baseline을 그대로 사용한다.
- 자동 병합은 exact canonical URL 또는 사람이 승인한 alias만 허용하고, 낮은
  유사도 후보는 `needs_review`로 보류한다.

## 7. 상태 라벨과 게이트 분리

| 산출물 | 상태 | 의미 |
| --- | --- | --- |
| 공개 번들 직접 노출 검사 | `DONE_PARTIAL` | local/Pages 금지 키·archive 경계는 확인. 정책 추론 완화는 제안만 함. |
| 4개 스키마 필드 설계 | `DONE` | 볼트 스키마와 매핑·unknown 규칙을 설계. 구현은 별도 승인 전 보류. |
| 첨부 요건 파서 판단 | `DONE_PARTIAL` | 14건/13건 레거시 근거와 설계 확인. 운영 수집기 연결은 미구현. |
| 볼트 교차참조·중복 점검 | `DONE_PARTIAL` | 현재 50건과 공개 186건의 고신뢰 중복 없음 확인. crosswalk 구현·저신뢰 후보 심사는 보류. |
| GitHub Pages 공개 경계 | `DONE` | 현재 읽기 전용 HTTP 200, 87/99/186, public preference archive 0 확인. |
| iPhone Safari 실기 검증 | `DONE_PARTIAL` | 공개 HTTP/구조만 확인했으며 이번 턴에 실제 기기 탭 검증은 하지 않음. |
| private Career Compass engine/master | `BLOCKED` | 사용자의 “Claude 검토 완료 전 private master push 금지” 지시와 dirty worktree 보존 규칙으로 보류. |

private gate는 공개 Pages 성공과 별도이며, 이 문서 작성만으로 green으로 바꾸지
않는다. marker를 추가해 상태를 조작하지 않았고, private 저장소에는 push·reset·정리
작업을 하지 않았다.

## 8. 재현 명령

```powershell
cd C:\Users\mjb58\career-job-compass
reqgate --root . check
py -B scripts/check_release.py
py -B -c "import json; x=json.load(open('data/app-data.json',encoding='utf-8')); print(len(x['jobs']),len(x['programs']),len(x['funding']),x.get('savedJobs',[]),x['stats'].get('recommendationSource'))"
Invoke-WebRequest -UseBasicParsing 'https://junpinmoon.github.io/career-job-compass/data/app-data.json' | Select-Object StatusCode,Headers
git status --short
```

보안 검사 결과의 핵심은 `scripts/check_release.py`가 공개 번들을 재귀적으로
검사하고, 이 문서의 `SEC-309`가 그 검사 결과와 완화 제안을 장부에 묶는다는 점이다.

NO_PRIVATE_FEEDBACK_FIELDS
DONE_PARTIAL
