"""AI work session commit helper.

Reads the latest report's Suggested Commit Message, optionally stages changes,
and creates a commit after user confirmation.
Run from project root: `python scripts/ai_commit.py`
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

GIT_USER_EMAIL = "tjrcksgnl@gmail.com"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKLOG_DIR = PROJECT_ROOT / ".ai-worklog"
SESSIONS_DIR = WORKLOG_DIR / "sessions"
REPORTS_DIR = WORKLOG_DIR / "reports"


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


def is_git_repo() -> bool:
    try:
        code, out, _ = run_git(["rev-parse", "--is-inside-work-tree"])
        return code == 0 and out.strip() == "true"
    except FileNotFoundError:
        return False


def find_latest_session() -> Path | None:
    if not SESSIONS_DIR.exists():
        return None
    candidates = sorted(SESSIONS_DIR.glob("*.json"))
    return candidates[-1] if candidates else None


def extract_suggested_message(report_path: Path) -> str:
    """Parse `## Suggested Commit Message` section from the report file."""
    if not report_path.exists():
        return ""
    text = report_path.read_text(encoding="utf-8")
    match = re.search(
        r"## Suggested Commit Message\s*\n(.+?)(?:\n##|\Z)",
        text,
        flags=re.DOTALL,
    )
    if not match:
        return ""
    return match.group(1).strip()


def prompt_input(message: str) -> str:
    try:
        return input(message)
    except EOFError:
        return ""


def ensure_git_user_email() -> bool:
    """Return True if user.email is set to the expected value (after optional auto-config)."""
    code, current, _ = run_git(["config", "--get", "user.email"])
    current = current.strip()
    if current == GIT_USER_EMAIL:
        return True

    if current:
        print(f"안내: 현재 git user.email은 '{current}' 입니다.")
    else:
        print("안내: git user.email이 설정되어 있지 않습니다.")
    print(f"권장값: {GIT_USER_EMAIL}")
    answer = prompt_input(
        f"이 저장소에만 user.email을 '{GIT_USER_EMAIL}'로 설정할까요? (y/n): "
    ).strip().lower()
    if answer not in ("y", "yes"):
        print("user.email 변경 없이 진행합니다. 필요 시 직접 설정하세요:")
        print(f'  git config --local user.email "{GIT_USER_EMAIL}"')
        return False

    code, _, err = run_git(["config", "--local", "user.email", GIT_USER_EMAIL])
    if code != 0:
        print(f"Error: git config 실행 실패: {err.strip()}")
        return False
    print(f"Done: 현재 저장소의 user.email을 '{GIT_USER_EMAIL}'로 설정했습니다.")
    return True


def show_changed_files() -> list[str]:
    code, out, _ = run_git(["status", "--porcelain"])
    if code != 0 or not out.strip():
        return []
    lines = [line for line in out.splitlines() if line.strip()]
    print("변경된 파일 목록:")
    for line in lines:
        print(f"  {line}")
    return lines


def main() -> int:
    if not is_git_repo():
        print("Error: 이 폴더는 git 저장소가 아닙니다. 먼저 `git init`을 실행하세요.")
        return 1

    session_file = find_latest_session()
    if session_file is None:
        print("Error: 세션 정보를 찾을 수 없습니다. `python scripts/ai_start.py`로 시작하세요.")
        return 1

    metadata = json.loads(session_file.read_text(encoding="utf-8"))
    session_id = metadata["session_id"]
    report_file = REPORTS_DIR / f"{session_id}.md"

    if not report_file.exists():
        print("Error: 리포트 파일이 없습니다. 먼저 `python scripts/ai_finish.py`를 실행하세요.")
        return 1

    print("=" * 60)
    print(f"Session ID : {session_id}")
    print(f"Report file: {report_file}")
    print("=" * 60)

    changes = show_changed_files()
    if not changes:
        print("커밋할 변경사항이 없습니다.")
        return 0

    add_answer = prompt_input("`git add .` 를 실행할까요? (y/n): ").strip().lower()
    if add_answer in ("y", "yes"):
        code, _, err = run_git(["add", "."])
        if code != 0:
            print(f"Error: git add 실패: {err.strip()}")
            return 1
        print("Staged all changes.")
    else:
        print("스테이징을 건너뜁니다. 이미 staged된 변경만 커밋됩니다.")

    suggested = extract_suggested_message(report_file)
    if suggested:
        print()
        print("리포트에서 가져온 Suggested Commit Message:")
        print(f"  {suggested}")
    user_msg = prompt_input("커밋 메시지를 입력하세요 (비워두면 위 메시지 사용): ").strip()
    commit_message = user_msg or suggested
    if not commit_message:
        print("Error: 커밋 메시지가 비어 있습니다. 다시 실행해 주세요.")
        return 1

    if not ensure_git_user_email():
        proceed = prompt_input("그래도 커밋을 진행할까요? (y/n): ").strip().lower()
        if proceed not in ("y", "yes"):
            print("커밋을 취소했습니다.")
            return 1

    confirm = prompt_input(
        f"\n다음 메시지로 커밋합니다:\n  {commit_message}\n진행할까요? (y/n): "
    ).strip().lower()
    if confirm not in ("y", "yes"):
        print("커밋을 취소했습니다.")
        return 1

    # Update status BEFORE committing so the session file is included in the commit
    metadata["status"] = "committed"
    metadata["commit_message"] = commit_message
    session_file.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    run_git(["add", str(session_file.relative_to(PROJECT_ROOT)).replace("\\", "/")])

    code, out, err = run_git(["commit", "-m", commit_message])
    if code != 0:
        metadata["status"] = "finished"
        del metadata["commit_message"]
        session_file.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Error: git commit 실패: {err.strip() or out.strip()}")
        print("초보자 안내: 'nothing to commit'이라면 변경사항이 staged되지 않은 것입니다.")
        return 1

    print(out.strip())
    print("커밋이 완료되었습니다.")
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
