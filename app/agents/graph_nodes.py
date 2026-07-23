import time
import json
from datetime import datetime
from loguru import logger
from langchain_core.runnables import RunnableConfig
from app.agents.graph_state import (
    TravelAgentState,
    PlannerContext,
    MemoryContext,
    MetadataContext,
    ValidationResult,
    ValidationErrorType,
    Recoverability,
    TaskStatus,
    SchedulerResult,
    ExecutionPlan,
    TravelPreferences,
    TripConstraints,
)
from app.schemas.planner.task import Task

def extract_preferences_and_constraints(
    summary: str, llm_client, model_name: str
) -> tuple[str | None, TravelPreferences, TripConstraints]:
    """Uses LLM to extract structured destination, preferences, and constraints from the summary text."""
    if not summary:
        return None, TravelPreferences(), TripConstraints(currency="INR")
        
    prompt = (
        "You are a helpful travel assistant. Analyze the conversation summary of the user's travel request. "
        "Extract the destination, travel preferences, and trip constraints.\n\n"
        f"Conversation Summary:\n{summary}\n\n"
        "Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        "  \"destination\": string or null,\n"
        "  \"preferences\": {\n"
        "    \"hotel_rating\": int or null,\n"
        "    \"flight_class\": string or null,\n"
        "    \"dietary_preferences\": list of strings,\n"
        "    \"seat_preference\": string or null,\n"
        "    \"hotel_facilities\": list of strings,\n"
        "    \"preferred_airlines\": list of strings,\n"
        "    \"hotel_brands\": list of strings\n"
        "  },\n"
        "  \"constraints\": {\n"
        "    \"max_budget\": float or null,\n"
        "    \"currency\": \"INR\",\n"
        "    \"max_layovers\": int or null,\n"
        "    \"latest_arrival\": string or null,\n"
        "    \"earliest_departure\": string or null\n"
        "  }\n"
        "}\n"
        "Do NOT include any markdown code blocks, explanations, or extra fields. Return ONLY the raw JSON."
    )
    
    try:
        response = llm_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_completion_tokens=500,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content.strip())
        
        destination = data.get("destination")
        prefs_data = data.get("preferences", {})
        consts_data = data.get("constraints", {})
        
        preferences = TravelPreferences.model_validate(prefs_data)
        constraints = TripConstraints.model_validate(consts_data)
        return destination, preferences, constraints
    except Exception as e:
        logger.warning(f"Failed to extract structured travel preferences: {e}")
        return None, TravelPreferences(), TripConstraints(currency="INR")

def user_request_node(state: TravelAgentState, config: RunnableConfig) -> dict:
    """Ingests and validates the user request at the entry point of the graph."""
    user_request = state.get("user_request", "").strip()
    if not user_request:
        logger.warning("Empty user request received at user_request_node.")
    else:
        logger.info(f"Ingested user request: '{user_request}'")
    return {"user_request": user_request}

def load_memory_node(state: TravelAgentState, config: RunnableConfig) -> dict:
    """Loads conversation summary and history context into the graph state."""
    memory = config["configurable"].get("conversation_memory")
    llm_client = config["configurable"].get("llm_client")
    model_name = config["configurable"].get("model_name")
    
    # Add user request to memory
    user_goal = state["user_request"]
    memory.add_user_message(user_goal)
    
    # Fetch and update conversation summary
    summary = memory.get_conversation_summary(llm_client, model_name)
    
    # Extract structured travel preferences, destination, and constraints
    destination, preferences, constraints = extract_preferences_and_constraints(summary, llm_client, model_name)
    
    # Update planner context
    planner_context = PlannerContext(
        destination=destination,
        preferences=preferences,
        constraints=constraints,
        conversation_summary=summary
    )
    
    # Load running logs/memories
    memory_context = MemoryContext(
        retrieved_memories=[]
    )
    
    return {
        "planner_context": planner_context,
        "memory_context": memory_context,
        "messages": [],
    }

def _detect_dependency_cycles(tasks: dict[int, Task]) -> None:
    adj = {t_id: t.depends_on for t_id, t in tasks.items()}
    visited = {}  # id -> state (0 = visiting, 1 = visited)
    
    def dfs(node_id):
        if node_id in visited:
            if visited[node_id] == 0:
                raise ValueError(f"Dependency cycle detected involving task {node_id}")
            return
        
        visited[node_id] = 0
        for dep in adj.get(node_id, []):
            dfs(dep)
        visited[node_id] = 1
        
    for t_id in tasks:
        dfs(t_id)

def plan_validator_node(state: TravelAgentState, config: RunnableConfig) -> dict:
    """Performs structural and semantic validation on the generated tasks plan."""
    val_result = state.get("validation_result")

    if val_result and not val_result.valid:
        # Planning Pipeline failed. Propagate the error.
        return {
            "validation_result": val_result,
            "final_response": f"Planning Execution Error: {val_result.message}"
        }

    tasks = state["execution_plan"].tasks
    if not tasks:
        return {"validation_result": ValidationResult(valid=True)}

    try:
        # 2. Structural Validation
        try:
            _detect_dependency_cycles(tasks)
        except ValueError as cycle_err:
            err = f"Circular Reference Check Failed: {str(cycle_err)}"
            return {
                "validation_result": ValidationResult(
                    valid=False,
                    recoverable=Recoverability.RECOVERABLE,
                    error_type=ValidationErrorType.CIRCULAR_REFERENCE,
                    message=err
                ),
                "final_response": err
            }

        # Verify dependencies and duplicate checks
        for t_id, task in tasks.items():
            if t_id in task.depends_on:
                err = f"Self-dependency Check Failed: Task {t_id} depends on itself."
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        recoverable=Recoverability.RECOVERABLE,
                        error_type=ValidationErrorType.INVALID_DEPENDENCY,
                        message=err
                    ),
                    "final_response": err
                }

            for dep_id in task.depends_on:
                if dep_id not in tasks:
                    err = f"Dependency Target Check Failed: Task {t_id} depends on Task {dep_id} which does not exist."
                    return {
                        "validation_result": ValidationResult(
                            valid=False,
                            recoverable=Recoverability.RECOVERABLE,
                            error_type=ValidationErrorType.UNKNOWN_DEPENDENCY,
                            message=err
                        ),
                        "final_response": err
                    }

        # 3. Semantic Validation
        from app.registry.tool_registry import AVAILABLE_TOOLS, TOOLS
        required_arguments = {}
        for tool in TOOLS:
            function = tool["function"]
            required_arguments[function["name"]] = function["parameters"].get("required", [])

        for t_id, task in tasks.items():
            if task.tool_name not in AVAILABLE_TOOLS:
                err = f"Unknown Tool Checked: Task {t_id} requests unknown tool '{task.tool_name}'."
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        recoverable=Recoverability.RECOVERABLE,
                        error_type=ValidationErrorType.UNKNOWN_TOOL,
                        message=err
                    ),
                    "final_response": err
                }
                
            required_params = required_arguments.get(task.tool_name, [])
            missing = [p for p in required_params if p not in task.arguments]
            if missing:
                err = f"Arguments Check Failed: Task {t_id} ({task.tool_name}) is missing parameters: {missing}"
                return {
                    "validation_result": ValidationResult(
                        valid=False,
                        recoverable=Recoverability.RECOVERABLE,
                        error_type=ValidationErrorType.INVALID_ARGUMENTS,
                        message=err
                    ),
                    "final_response": err
                }

    except Exception as system_error:
        err = f"Non-recoverable System Validation Error: {str(system_error)}"
        return {
            "validation_result": ValidationResult(
                valid=False,
                recoverable=Recoverability.FATAL,
                error_type=ValidationErrorType.INVALID_ARGUMENTS,
                message=err
            ),
            "final_response": err
        }

    return {"validation_result": ValidationResult(valid=True)}

def _propagate_failure(tasks: dict[int, Task], failed_task_id: int, visited: set[int]) -> dict[int, Task]:
    """Recursively mark downstream tasks depending on the failed task as FAILED."""
    if failed_task_id in visited:
        return {}

    visited.add(failed_task_id)
    
    updates = {}
    
    for t_id, task in tasks.items():
        if task.status in (TaskStatus.PENDING, TaskStatus.READY) and failed_task_id in task.depends_on:
            updated_task = task.model_copy(update={
                "status": TaskStatus.FAILED,
                "error": f"Parent dependency task {failed_task_id} failed."
            })
            updates[t_id] = updated_task
            updates.update(_propagate_failure(tasks, t_id, visited))
    return updates

def scheduler_node(state: TravelAgentState, config: RunnableConfig) -> dict:
    """Pure Scheduler node. Analyzes task statuses, maps completion lists, and propagates failures."""
    tasks = dict(state["execution_plan"].tasks)
    
    # 1. Failure propagation
    failed_task_ids = [t_id for t_id, t in tasks.items() if t.status == TaskStatus.FAILED]

    visited = set()
    updates = {}

    for failed_id in failed_task_ids:
        updates.update(_propagate_failure(tasks, failed_id, visited))
        
    for t_id, updated_task in updates.items():
        tasks[t_id] = updated_task
        
    # 2. Bucket classification
    completed = []
    failed = []
    ready = []
    waiting = []
    blocked = []
    
    def has_failed_ancestor(task_id: int, visited_chk: set[int]) -> bool:
        if task_id in visited_chk:
            return False
        visited_chk.add(task_id)
        task = tasks.get(task_id)
        if not task:
            return False
        for dep_id in task.depends_on:
            dep_task = tasks.get(dep_id)
            if dep_task and (dep_task.status == TaskStatus.FAILED or has_failed_ancestor(dep_id, visited_chk)):
                return True
        return False

    for t_id, task in tasks.items():
        if task.status == TaskStatus.COMPLETED:
            completed.append(t_id)
        elif task.status == TaskStatus.FAILED:
            failed.append(t_id)
        elif task.status in (TaskStatus.PENDING, TaskStatus.READY):
            parents = [tasks[dep_id] for dep_id in task.depends_on if dep_id in tasks]
            if all(p.status == TaskStatus.COMPLETED for p in parents):
                ready.append(t_id)
                if task.status == TaskStatus.PENDING:
                    tasks[t_id] = task.model_copy(update={"status": TaskStatus.READY})
            elif has_failed_ancestor(t_id, set()):
                blocked.append(t_id)
            else:
                waiting.append(t_id)
        elif task.status == TaskStatus.RUNNING:
            waiting.append(t_id)
            
    scheduler_result = SchedulerResult(
        has_ready_tasks=len(ready) > 0,
        ready_tasks=ready,
        waiting_tasks=waiting,
        blocked_tasks=blocked,
        failed_tasks=failed,
        completed_tasks=completed
    )
    
    return {
        "execution_plan": ExecutionPlan(tasks=tasks),
        "scheduler_result": scheduler_result
    }

def responder_node(state: TravelAgentState, config: RunnableConfig) -> dict:
    """Formulates the final natural language response using the state values."""
    responder = config["configurable"].get("response_agent")
    user_goal = state["user_request"]
    execution_plan = state["execution_plan"]
    
    response = responder.generate_response(user_goal, execution_plan)
    return {"final_response": response}

def update_memory_node(state: TravelAgentState, config: RunnableConfig) -> dict:
    """Appends assistant response back to conversation memory."""
    memory = config["configurable"].get("conversation_memory")
    response = state["final_response"]
    
    memory.add_assistant_message(response)
    return {}
