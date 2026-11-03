import io
import sys
from app.agents import CoordinatorAgent
from app.schemas.planner import ProgressEvent

# Ensure UTF-8 output encoding for Rupee symbols on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def on_progress_callback(event: ProgressEvent):
    status_str = event.status.value.upper()
    worker_str = f" [Worker {event.worker_id}]" if event.worker_id else ""
    retry_str = f" (Retry {event.retry_count})" if event.retry_count > 0 else ""
    time_str = (
        f" ({event.execution_time:.2f}s)"
        if event.execution_time is not None
        else ""
    )
    error_str = f" - Error: {event.error}" if event.error else ""
    print(
        f"  [Task {event.task_id}]{worker_str}{retry_str}: "
        f"{event.description} -> {status_str}{time_str}{error_str}",
        flush=True,
    )


def main():
    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Plan a 7-day Kerala trip for 3 adults travelling from Delhi (DEL) to Kochi, Munnar and Alleppey from 10 January 2027 to 17 January 2027, with a total budget of ₹90,000."
    )

    print("=" * 70)
    print("🌍 WAYFARER AI TRAVEL AGENT — TERMINAL EXECUTION")
    print(f"Query: {query}")
    print("=" * 70)

    coordinator = CoordinatorAgent()

    print("\n--- [1] LANGGRAPH DAG TASK ORCHESTRATION ---")
    response = coordinator.run(
        user_goal=query,
        on_progress=on_progress_callback,
    )

    print("\n" + "=" * 70)
    print("📄 FINAL TRAVEL AGENT EXECUTIVE REPORT")
    print("=" * 70)
    print(response)
    print("=" * 70)


if __name__ == "__main__":
    main()

