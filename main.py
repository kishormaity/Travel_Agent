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


def main():
    coordinator = CoordinatorAgent()

    print("=" * 60)
    print("🌍 AI Travel Agent (Interactive CLI)")
    print("Type 'exit' to quit.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()

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