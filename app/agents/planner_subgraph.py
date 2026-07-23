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
    
    # If recovery from a validation failure is needed, increment the replan counter
    if val_result and not val_result.valid:
        replan_count += 1
        
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
        
    # Map new tasks deterministically
    max_existing_id = max(execution_plan.tasks.keys(), default=0)
    new_tasks = {}

    for i, planner_task in enumerate(parsed.tasks):
        g_id = max_existing_id + i + 1

        new_tasks[g_id] = Task(
            id=g_id,
            description=planner_task.description,
            tool_name=planner_task.tool_name,
            arguments=planner_task.arguments,
            depends_on=planner_task.depends_on,
            priority=planner_task.priority,
            status=TaskStatus.PENDING
        )
        
    next_version = 1 if replan_count == 0 else execution_plan.version + 1
    
    val_result = ValidationResult(valid=True)
    
    out_plan = ExecutionPlan(
        tasks=new_tasks,
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
