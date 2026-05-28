"""AI work session finisher.

Captures git diff for the most recent session and generates a review report.
Run from project root: `python scripts/ai_finish.py`
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

GIT_USER_EMAIL = "tjrcksgnl@gmail.com"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKLOG_DIR = PROJECT_ROOT / ".ai-worklog"
PROMPTS_DIR = WORKLOG_DIR / "prompts"
SESSIONS_DIR = WORKLOG_DIR / "sessions"
DIFFS_DIR = WORKLOG_DIR / "diffs"
REPORTS_DIR = WORKLOG_DIR / "reports"

REPORT_TEMPLATE = """# AI Work Report

## Session ID
{session_id}

## Title
{title}

## Git User
{git_user}

## Prompt File
{prompt_file}

## Changed Files
{changed_files_block}

## Git Diff Stat
```text
{diff_stat}
```

## Suggested Commit Message
{commit_message}

## Review Checklist
- [ ] 프롬프트와 실제 변경 내용이 일치하는지 확인
- [ ] 불필요한 파일이 변경되지 않았는지 확인
- [ ] 실행 또는 테스트를 완료했는지 확인
- [ ] 민감정보가 포함되지 않았는지 확인
"""


def is_git_repo() -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except FileNotFoundError:
        return False


def find_latest_session() -> Path | None:
    if not SESSIONS_DIR.exists():
        return None
    candidates = sorted(SESSIONS_DIR.glob("*.json"))
    return candidates[-1] if candidates else None


def run_git(args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout, result.stderr


def collect_changed_files() -> list[str]:
    """Return a sorted unique list of changed file paths (tracked + untracked)."""
    files: set[str] = set()

    # core.quotepath=false: 한글 파일명을 octal 인코딩 없이 UTF-8 그대로 반환
    code, out, _ = run_git(["-c", "core.quotepath=false", "diff", "--name-only"])
    if code == 0:
        files.update(line.strip() for line in out.splitlines() if line.strip())

    code, out, _ = run_git(["-c", "core.quotepath=false", "diff", "--name-only", "--cached"])
    if code == 0:
        files.update(line.strip() for line in out.splitlines() if line.strip())

    code, out, _ = run_git(["-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard"])
    if code == 0:
        files.update(line.strip() for line in out.splitlines() if line.strip())

    return sorted(files)


def build_commit_message(changed: list[str]) -> str:
    if not changed:
        return "[AI] no changes detected"
    names = [Path(p).name for p in changed]
    preview = names[:5]
    suffix = "" if len(names) <= 5 else f" (+{len(names) - 5} more)"
    return f"[AI] modify: {', '.join(preview)}{suffix}"


def main() -> int:
    if not WORKLOG_DIR.exists():
        print("Error: .ai-worklog 폴더가 없습니다. 먼저 `python scripts/ai_start.py`를 실행하세요.")
        return 1

    session_file = find_latest_session()
    if session_file is None:
        print("Error: 진행 중인 세션을 찾을 수 없습니다. `python scripts/ai_start.py`로 새 세션을 시작하세요.")
        return 1

    metadata = json.loads(session_file.read_text(encoding="utf-8"))
    session_id = metadata["session_id"]
    title = metadata.get("title", "")
    prompt_file_rel = metadata.get("prompt_file", "")

    diff_file = DIFFS_DIR / f"{session_id}.diff"
    report_file = REPORTS_DIR / f"{session_id}.md"

    if not is_git_repo():
        print("Warning: 이 폴더는 git 저장소가 아닙니다. 빈 diff/리포트가 생성됩니다.")
        print("초보자 안내: 변경 추적을 사용하려면 `git init`을 먼저 실행하세요.")
        diff_stat = "(not a git repository)"
        diff_text = ""
        changed_files: list[str] = []
    else:
        code, diff_text, err = run_git(["-c", "core.quotepath=false", "diff", "HEAD"])
        if code != 0:
            # 초기 커밋이 아직 없을 때는 HEAD가 없으므로 staged + unstaged 영역만 비교
            code2, diff_text, err2 = run_git(["-c", "core.quotepath=false", "diff"])
            if code2 != 0:
                print(f"Error: git diff 실행 실패: {err.strip() or err2.strip()}")
                return 1

        code, diff_stat, err = run_git(["-c", "core.quotepath=false", "diff", "--stat", "HEAD"])
        if code != 0:
            code2, diff_stat, _ = run_git(["-c", "core.quotepath=false", "diff", "--stat"])
            if code2 != 0:
                diff_stat = "(git diff --stat failed)"

        if not diff_stat.strip():
            diff_stat = "(no tracked changes)"

        changed_files = collect_changed_files()

    diff_file.write_text(diff_text, encoding="utf-8")

    if changed_files:
        changed_files_block = "\n".join(f"- {p}" for p in changed_files)
    else:
        changed_files_block = "- (no changes detected)"

    commit_message = build_commit_message(changed_files)

    report = REPORT_TEMPLATE.format(
        session_id=session_id,
        title=title,
        git_user=GIT_USER_EMAIL,
        prompt_file=prompt_file_rel,
        changed_files_block=changed_files_block,
        diff_stat=diff_stat.strip() or "(empty)",
        commit_message=commit_message,
    )
    report_file.write_text(report, encoding="utf-8")

    metadata["status"] = "finished"
    metadata["finished_at"] = datetime.now().isoformat(timespec="seconds")
    metadata["changed_files"] = changed_files
    metadata["suggested_commit_message"] = commit_message
    session_file.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("AI 작업 세션 리포트가 생성되었습니다.")
    print("=" * 60)
    print(f"Session ID : {session_id}")
    print(f"Diff file  : {diff_file}")
    print(f"Report file: {report_file}")
    print(f"Changed    : {len(changed_files)} file(s)")
    print()
    print("다음 단계: 리포트를 확인한 뒤 `python scripts/ai_commit.py`를 실행하세요.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n사용자가 취소했습니다.")
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"오류가 발생했습니다: {exc}")
        print("초보자 안내: 위 오류 메시지를 그대로 복사해서 검색하거나 도움을 요청하세요.")
        sys.exit(1)
