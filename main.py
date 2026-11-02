import io
import sys
from app.agents import CoordinatorAgent
from app.schemas.planner import ProgressEvent

# Force UTF-8 stdout encoding to support Rupee symbols on Windows cmd/powershell
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def on_progress_callback(event: ProgressEvent):
    status_str = event.status.value.upper()
    worker_str = f" [Worker Thread {event.worker_id}]" if event.worker_id else ""
    retry_str = f" (Retry {event.retry_count})" if event.retry_count > 0 else ""
    time_str = (
        f" (execution time: {event.execution_time:.2f}s)"
        if event.execution_time is not None
        else ""
    )
    error_str = f" - Error: {event.error}" if event.error else ""

    print(
        f"[ProgressEvent] Task {event.task_id}{worker_str}{retry_str}: "
        f"\"{event.description}\" -> {status_str}{time_str}{error_str}",
        flush=True,
    )


def get_user_input() -> str:
    """
    Reads user input, supporting both standard single-line typing and
    multi-line pasted queries (or triple-quoted multiline input).
    """
    print("\nYou: ", end="", flush=True)
    first_line = sys.stdin.readline()
    if not first_line:
        return ""

    first_clean = first_line.rstrip("\r\n")

    # 1. Multi-line block mode if user begins with triple quotes """
    if first_clean.strip().startswith('"""'):
        lines = [first_clean.strip()[3:]]
        print("(Multi-line mode: type \"\"\" on a new line and press Enter to finish)")
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            if '"""' in line:
                lines.append(line.split('"""')[0].rstrip("\r\n"))
                break
            lines.append(line.rstrip("\r\n"))
        return "\n".join(lines).strip()

    lines = [first_clean]

    # 2. Check if more lines are immediately buffered in OS stream (e.g. pasted text)
    try:
        import msvcrt
        import time
        time.sleep(0.04)  # Small grace window for OS clipboard buffer stream
        while msvcrt.kbhit():
            more = sys.stdin.readline()
            if more:
                lines.append(more.rstrip("\r\n"))
            else:
                break
    except (ImportError, Exception):
        pass

    full_query = "\n".join(lines).strip()
    if len(lines) > 1:
        word_count = len(full_query.split())
        print(f"  [Received full query: {len(lines)} lines, {word_count} words]")
    return full_query


def main():
    coordinator = CoordinatorAgent()

    print("=" * 60)
    print("🌍 AI Travel Agent (Interactive CLI)")
    print("Tip: You can paste long multi-paragraph queries directly.")
    print("Type 'exit' to quit.")
    print("=" * 60)

    while True:
        try:
            user_input = get_user_input()

            if user_input.lower() in {"exit", "quit", "bye"}:
                print("\n👋 Goodbye!")
                break

            if not user_input:
                continue

            print("\n--- Planner/Executor Progress ---")
            response = coordinator.run(
                user_goal=user_input,
                on_progress=on_progress_callback,
            )
            print("\n--- Final Response ---")
            print(response)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

        except Exception as error:
            print(f"\n❌ Error: {error}")


if __name__ == "__main__":
    main()