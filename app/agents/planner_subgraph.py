import json
from datetime import datetime
from typing import TypedDict, Any
from loguru import logger
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END

from app.agents.graph_state import (
    ValidationResult,
    ExecutionPlan,
    PlannerContext,
    ValidationErrorType,
    Recoverability,
    PlanStatus,
)
from app.schemas.planner.task import Task, TaskStatus
from app.config import PLANNER_TEMPERATURE, MAX_TOKENS

class PlanningPipelineState(TypedDict):
    # Inputs from Parent state
    user_request: str
    messages: list[AnyMessage]
    replan_count: int
    planner_context: PlannerContext
    execution_plan: ExecutionPlan
    
    # Internal Pipeline State (ephemeral, deleted upon exit)
    prompt_messages: list[dict]
    llm_response: str | None
    
    # Outputs returned to Parent state
    validation_result: ValidationResult
    replan_count: int  # Propagate updated count back

def build_prompt_node(state: PlanningPipelineState) -> dict:
    """Prepares prompt templates and system variables for the planner LLM."""
    replan_count = state.get("replan_count", 0)
    val_result = state.get("validation_result")
    execution_plan = state.get("execution_plan")
    
    # If recovery from validation failure or existing plan execution failure, increment replan counter
    has_existing_tasks = bool(execution_plan and execution_plan.tasks and len(execution_plan.tasks) > 0)
    if val_result and not val_result.valid:
        replan_count += 1
    elif has_existing_tasks and replan_count == 0:
        replan_count = 1
        
    user_request = state["user_request"]
    planner_context = state.get("planner_context")
    
    # Generate system prompt based on planning mode
    if replan_count > 0:
        execution_plan = state.get("execution_plan")
        tasks = execution_plan.tasks if execution_plan else {}
        
        # Build execution history of finished tasks
        from app.utils import serialize_task_to_dict

        execution_history = []
        sorted_tasks = sorted(tasks.values(), key=lambda t: t.id)
        
        for task in sorted_tasks:
            execution_history.append(serialize_task_to_dict(task, full_context=True))
            
        from app.registry.tool_registry import get_planner_tools_description
        from app.prompts import REPLANNER_SYSTEM_PROMPT
        
        max_existing_id = max(tasks.keys(), default=0)
        start_id = max_existing_id + 1
        
        execution_history_str = json.dumps(execution_history, indent=2, default=str)
        
        system_prompt = REPLANNER_SYSTEM_PROMPT.replace(
            "{execution_history}", execution_history_str
        ).replace(
            "{available_tools}", get_planner_tools_description()
        ).replace(
            "{start_id}", str(start_id)
        )
    else:
        from app.registry.tool_registry import get_planner_tools_description
        from app.prompts import PLANNER_SYSTEM_PROMPT
        
        system_prompt = PLANNER_SYSTEM_PROMPT.replace(
            "{available_tools}", get_planner_tools_description()
        )
        max_existing_id = 0
        
    # Inject Pydantic Schema and current date/time context
    from app.schemas.planner.planner_response import PlannerResponse
    json_schema_str = json.dumps(PlannerResponse.model_json_schema(), indent=2)
    schema_instruction = f"\n\nOUTPUT FORMAT SCHEMA:\nYour output MUST strictly conform to the following Pydantic JSON Schema:\n{json_schema_str}"

    current_time_context = f"\n\nCurrent Local Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    from langchain_core.messages import SystemMessage, HumanMessage
    prompt_messages = [
        SystemMessage(content=system_prompt + schema_instruction + current_time_context)
    ]
    
    # Injects running summary of conversation history
    summary = planner_context.conversation_summary if planner_context else ""
    if summary:
        prompt_messages.append(SystemMessage(content=f"Historical Conversation Summary:\n{summary}"))
        
    prompt_messages.append(HumanMessage(content=user_request))
        
    return {"prompt_messages": prompt_messages, "replan_count": replan_count}

def query_llm_node(state: PlanningPipelineState, config: RunnableConfig) -> dict:
    """Submits messages statelessly to ChatGroq client."""
    llm_client = config["configurable"].get("llm_client")
    prompt_messages = state["prompt_messages"]
    
    replan_count = state.get("replan_count", 0)
    prompt_type = "replanner" if replan_count > 0 else "planner"
    logger.info(f"Planner attempt {replan_count + 1} ({prompt_type}) via LangGraph Planning Pipeline Subgraph")
    
    response = llm_client.invoke(prompt_messages)
    return {"llm_response": response.content}

def _is_task_equivalent(tool1: str, args1: dict, tool2: str, args2: dict) -> bool:
    """Evaluates whether two tasks perform the identical logical operation."""
    if tool1 != tool2:
        return False
    args1 = args1 or {}
    args2 = args2 or {}

    from app.services.request_normalizer import resolve_airport_code, normalize_city_name
    from app.tools.weather import normalize_weather_city

    if tool1 == "search_flights":
        o1 = resolve_airport_code(str(args1.get("departure_iata") or args1.get("origin") or ""))
        o2 = resolve_airport_code(str(args2.get("departure_iata") or args2.get("origin") or ""))
        d1 = resolve_airport_code(str(args1.get("arrival_iata") or args1.get("destination") or ""))
        d2 = resolve_airport_code(str(args2.get("arrival_iata") or args2.get("destination") or ""))
        date1 = str(args1.get("flight_date") or args1.get("departure_date") or "")
        date2 = str(args2.get("flight_date") or args2.get("departure_date") or "")
        ret1 = str(args1.get("return_date") or "")
        ret2 = str(args2.get("return_date") or "")
        return o1 == o2 and d1 == d2 and date1 == date2 and ret1 == ret2

    if tool1 in ("search_hotels", "search_places"):
        c1 = normalize_city_name(str(args1.get("city") or "")).lower()
        c2 = normalize_city_name(str(args2.get("city") or "")).lower()
        return c1 == c2 and bool(c1)

    if tool1 == "get_current_weather":
        c1 = normalize_weather_city(str(args1.get("city") or "")).lower()
        c2 = normalize_weather_city(str(args2.get("city") or "")).lower()
        return c1 == c2 and bool(c1)

    if tool1 == "convert_currency":
        return (
            args1.get("from_currency") == args2.get("from_currency")
            and args1.get("to_currency") == args2.get("to_currency")
        )

    if tool1 == "get_route":
        return (
            args1.get("origin") == args2.get("origin")
            and args1.get("destination") == args2.get("destination")
        )

    return args1 == args2


def parse_and_map_node(state: PlanningPipelineState, config: RunnableConfig) -> dict:
    """Extracts JSON, runs Pydantic validations, and maps task IDs sequentially in code."""
    llm_response = state["llm_response"]
    replan_count = state.get("replan_count", 0)
    execution_plan = state["execution_plan"]
    model_name = config["configurable"].get("model_name")
    
    from app.schemas.planner.planner_response import PlannerResponse
    try:
        # Strip markdown wrapper blocks
        cleaned = llm_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        data = json.loads(cleaned)
        parsed = PlannerResponse.model_validate(data)
    except Exception as e:
        logger.warning(f"Planner response JSON validation failed: {e}. Raw: {llm_response}")
        # Return invalid validation result directly back to parent
        val_result = ValidationResult(
            valid=False,
            recoverable=Recoverability.RECOVERABLE,
            error_type=ValidationErrorType.INVALID_ARGUMENTS,
            message=f"JSON Parsing Error: {str(e)}"
        )
        return {
            "validation_result": val_result,
            "execution_plan": ExecutionPlan(
                tasks={},
                version=execution_plan.version,
                parent_version=execution_plan.parent_version,
                plan_status=PlanStatus.FAILED
            )
        }
        
    # Map new tasks deterministically, preventing duplicate re-execution of COMPLETED tasks
    max_existing_id = max(execution_plan.tasks.keys(), default=0) if execution_plan and execution_plan.tasks else 0
    new_tasks = {}
    completed_existing = (
        {t_id: t for t_id, t in execution_plan.tasks.items() if t.status == TaskStatus.COMPLETED and t.result is not None}
        if (replan_count > 0 and execution_plan and execution_plan.tasks)
        else {}
    )

    id_remap: dict[int, int] = {}  # newly generated 1-based index -> existing completed id or new id

    for i, planner_task in enumerate(parsed.tasks):
        temp_id = i + 1

        # Check if identical task already completed in execution plan
        matched_completed = None
        for c_id, c_task in completed_existing.items():
            if _is_task_equivalent(c_task.tool_name, c_task.arguments, planner_task.tool_name, planner_task.arguments):
                matched_completed = c_task
                break

        if matched_completed is not None:
            logger.info(
                f"[PlannerDeduplication] Task '{planner_task.description}' ({planner_task.tool_name}) "
                f"matches already COMPLETED Task {matched_completed.id}. Preserving successful output without re-executing."
            )
            id_remap[temp_id] = matched_completed.id
            continue

        g_id = max_existing_id + len(new_tasks) + 1
        id_remap[temp_id] = g_id

        # Remap dependencies to point to existing completed IDs or new IDs
        remapped_deps = []
        for dep in planner_task.depends_on:
            # 1. Never allow self-dependency
            if dep == g_id:
                continue

            # 2. If dep explicitly references an existing task in execution_plan, preserve that historical task ID
            if execution_plan and dep in execution_plan.tasks:
                remapped_deps.append(dep)
            # 3. If dep references a task within the newly generated batch by relative 1-based index
            elif dep in id_remap:
                target_dep = id_remap[dep]
                if target_dep != g_id:
                    remapped_deps.append(target_dep)
            # 4. If dep references an already-created new task in new_tasks
            elif dep in new_tasks:
                remapped_deps.append(dep)
            else:
                remapped_deps.append(dep)

        new_tasks[g_id] = Task(
            id=g_id,
            description=planner_task.description,
            tool_name=planner_task.tool_name,
            arguments=planner_task.arguments,
            depends_on=remapped_deps,
            priority=planner_task.priority,
            status=TaskStatus.PENDING,
        )
        
    # In replanning, merge existing tasks with new tasks so historical results and dependency lineage are preserved
    if replan_count > 0 and execution_plan and execution_plan.tasks:
        merged_tasks = {**execution_plan.tasks, **new_tasks}
    else:
        merged_tasks = new_tasks
        
    next_version = 1 if replan_count == 0 else execution_plan.version + 1
    
    val_result = ValidationResult(valid=True)
    
    out_plan = ExecutionPlan(
        tasks=merged_tasks,
        version=next_version,
        parent_version=execution_plan.version if replan_count > 0 else None,
        planning_rationale="Initial plan generated" if replan_count == 0 else f"Replanned next steps (Replan {replan_count})",
        planner_model=model_name,
        plan_status=PlanStatus.ACTIVE
    )
    
    return {
        "execution_plan": out_plan,
        "validation_result": val_result
    }

# Build Subgraph
builder = StateGraph(PlanningPipelineState)
builder.add_node("build_prompt", build_prompt_node)
builder.add_node("query_llm", query_llm_node)
builder.add_node("parse_and_map", parse_and_map_node)

builder.add_edge(START, "build_prompt")
builder.add_edge("build_prompt", "query_llm")
builder.add_edge("query_llm", "parse_and_map")
builder.add_edge("parse_and_map", END)

planner_subgraph = builder.compile()
