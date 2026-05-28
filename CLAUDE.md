# AI Worklog 자동화 지침

## 트리거
사용자 메시지에 `[목적]` 태그가 포함되면 코딩 전/후에 아래를 자동 실행한다.

---

## 코딩 시작 전 (첫 번째 코드 수정 전에 먼저 실행)

1. Bash로 타임스탬프 획득:
   ```
   python -c "from datetime import datetime; print(datetime.now().strftime('%Y%m%d_%H%M%S'))"
   ```
2. `[목적]` 내용을 한글 포함 kebab-case slug로 변환 → `session_id = {타임스탬프}_{slug}`
3. `.ai-worklog/sessions/{session_id}.json` 생성 (status: "started")
4. `.ai-worklog/prompts/{session_id}.md` 생성 (사용자 메시지 내용 정리)

---

## 코딩 완료 후

5. `.ai-worklog/reports/{session_id}.md` 생성 (변경 내용 요약)
6. `.ai-worklog/sessions/{session_id}.json` status를 "finished"로 업데이트, `changed_files` 목록 추가

---

## 파일 형식

### sessions/{session_id}.json
```json
{
  "session_id": "...",
  "title": "[목적] 내용",
  "git_user_email": "tjrcksgnl@gmail.com",
  "created_at": "ISO 시각",
  "prompt_file": ".ai-worklog/prompts/{session_id}.md",
  "diff_file": ".ai-worklog/diffs/{session_id}.diff",
  "report_file": ".ai-worklog/reports/{session_id}.md",
  "status": "started"
}
```

### prompts/{session_id}.md
```
# AI Work Session
## Session ID
## Title
## Git User
## Goal          ← [목적] 내용
## Prompt        ← [프롬프트] 내용 정리
## Expected Files
## Notes         ← [추가요청사항] 내용
```

### reports/{session_id}.md
```
# AI Work Report
## Session ID / Title / Git User / Prompt File
## Changed Files   ← 실제 수정된 파일 목록
## 작업 내용       ← 변경 사항 간결히 요약
## Suggested Commit Message
## Review Checklist
```

---

## 규칙
- 워크로그 파일 생성/수정은 조용히 실행 (사용자에게 별도 알림 없음)
- 레포트는 실제 변경된 내용만 간결하게 기록
- 커밋은 사용자가 PowerShell에서 수동으로 실행
- `.ai-worklog/` 디렉토리가 없으면 자동 생성
