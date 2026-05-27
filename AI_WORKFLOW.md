# AI Prompt to Code Tracking Workflow

이 프로젝트는 Claude CLI로 작성한 코드와 그것을 만든 프롬프트를 1:1로 연결해 기록합니다.
하나의 "AI 작업 = 하나의 세션"으로 끊으면, 나중에 "이 코드가 왜 생겼는지"를 추적할 수 있습니다.

---

## 0. 명령어 형태로 사용하기 (권장)

프로젝트 루트에 다음 4개의 `.cmd` 래퍼가 들어 있습니다.

- `ai_start.cmd`
- `ai_finish.cmd`
- `ai_commit.cmd`
- `ai_record.cmd`

각 래퍼는 자동으로 `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8` / `chcp 65001` 을 설정하므로
**한글 입출력이 깨지지 않습니다.**

### A. 프로젝트 루트에서만 사용

PowerShell에서:
```powershell
.\ai_start
.\ai_finish
.\ai_commit
```
cmd에서:
```
ai_start
ai_finish
ai_commit
```

### B. 어디서든 사용 (PATH 등록, 1회 설치)

프로젝트 루트에서 다음 중 **하나** 를 실행:

```powershell
.\install_ai_path             # 권장 (PowerShell 실행 정책 영향 없음)
```
또는
```
install_ai_path               # cmd에서도 동일
```

> `install_ai_path.cmd` 는 PowerShell을 `-ExecutionPolicy Bypass` 로 한 번만 띄워서 설치 스크립트를 실행합니다. 사용자 시스템의 실행 정책을 영구적으로 바꾸지 않습니다.

이후 **새 터미널** 을 열면 어느 폴더에서나 다음 명령이 동작합니다.
```powershell
ai_start
ai_finish
ai_commit
ai_record --help
```
되돌리려면:
```powershell
.\install_ai_path -Remove
```

> 사용자(User) PATH에만 추가되며 시스템(System) PATH에는 손대지 않습니다. 관리자 권한 불필요.

#### 만약 실행 정책 오류가 떴다면

이미 `install_ai_path.cmd` 가 정책 우회를 처리하므로 그걸 쓰면 됩니다. 굳이 정책 자체를 바꾸고 싶다면 한 번만:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
(현재 사용자만 적용, 시스템 전체엔 영향 없음. 일반적으로 권장되는 설정값)

---

## 1. 작업 시작

```powershell
ai_start
```
(혹은 직접 호출: `python scripts/ai_start.py`)

- 작업 제목을 입력하면 `YYYYMMDD_HHMMSS_slug` 형식의 세션 ID가 생성됩니다.
- 다음 두 파일이 만들어집니다.
  - `.ai-worklog/prompts/{세션ID}.md` (프롬프트 템플릿)
  - `.ai-worklog/sessions/{세션ID}.json` (메타데이터)
- 커밋되지 않은 변경사항이 있으면 경고가 표시됩니다.

## 2. 생성된 프롬프트 파일 작성

`.ai-worklog/prompts/세션ID.md` 파일을 열어 Claude에게 보낼 프롬프트를 붙여넣습니다.
"Goal", "Expected Files", "Notes" 섹션을 함께 채워두면 나중에 보기 좋습니다.

## 3. Claude CLI로 코드 작업 수행

Claude CLI에서 위 프롬프트로 실제 코드 수정을 진행합니다.

## 4. 작업 종료 및 변경 이력 저장

```powershell
ai_finish
```
(직접 호출: `python scripts/ai_finish.py`)

- 가장 최근 세션을 자동으로 찾습니다.
- `git diff` 결과를 `.ai-worklog/diffs/{세션ID}.diff`로 저장합니다.
- 변경 파일 목록, `git diff --stat`, Suggested Commit Message를 모은
  `.ai-worklog/reports/{세션ID}.md` 리포트를 생성합니다.

## 5. 리포트 확인

`.ai-worklog/reports/세션ID.md`를 열어 다음을 점검하세요.

- 프롬프트와 실제 변경 내용이 일치하는가
- 의도하지 않은 파일이 변경되지 않았는가
- 실행/테스트를 마쳤는가
- 민감정보가 들어가지 않았는가

## 5-α. (자동) Claude 채팅에서 [목표]/[프롬프트] 포맷 사용하기

매번 prompt.md를 직접 열어 채우기가 번거롭다면, Claude 채팅창에 아래 형식으로 한 번에 보내면 됩니다.

```text
[목표]
짧게 한 줄~여러 줄로 목표 작성

[프롬프트]
Claude에게 실제로 시킬 작업 본문 작성
```

Claude는 이 형식을 인식하면 다음을 자동 실행합니다.

1. 가장 최근 세션의 `.ai-worklog/prompts/{세션ID}.md`의 `## Goal`, `## Prompt` 섹션에 본문을 기록
2. 프롬프트에 요청된 코드 작업 수행
3. `python scripts/ai_finish.py`를 실행해 diff/리포트 생성

수동 호출이 필요할 때는 헬퍼 명령(또는 스크립트)을 직접 써도 됩니다.

```powershell
# stdin으로 입력하기
ai_record --from-stdin

# 또는 인자로
ai_record --goal "..." --prompt "..."

# 또는 파일로
ai_record --goal-file goal.txt --prompt-file prompt.txt
```

옵션: `--session 세션ID` 로 특정 세션 지정, `--append` 로 덮어쓰지 않고 이어쓰기.

## 6. 커밋

```powershell
ai_commit
```
(직접 호출: `python scripts/ai_commit.py`)

- 변경 파일 목록을 보여줍니다.
- `git add .` 여부, 커밋 메시지를 묻습니다(비워두면 리포트의 Suggested Commit Message 사용).
- `user.email`이 `tjrcksgnl@gmail.com`이 아니면 `git config --local`로 설정할지 묻습니다.

---

## 왜 이 방식이 좋은가

- **프롬프트와 코드 변경 이력을 직접 연결**할 수 있습니다.
- 시간이 지난 뒤에도 **특정 코드가 어떤 의도로 생겼는지 추적**할 수 있습니다.
- AI가 만든 코드와 사람이 만든 코드를 **commit 단위로 구분**하기 쉽습니다.
- **자기소개서/포트폴리오**에서 "AI 개발 프로세스를 직접 설계해 관리했다"는 사례로 활용 가능합니다.
