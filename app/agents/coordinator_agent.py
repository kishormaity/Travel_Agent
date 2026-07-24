from typing import Callable
from loguru import logger

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send

from app.agents.response_agent import ResponseAgent
from app.core import get_llm
from app.memory import ConversationMemory
from app.schemas.planner import ProgressEvent, ExecutionPolicy

from app.config import MODEL_NAME
from app.agents.graph_state import (
    TravelAgentState,
    PlannerContext,
    MemoryContext,
    MetadataContext,
    ExecutionPlan,
    ValidationResult,
    SchedulerResult,
    Recoverability,
    RetryPolicy,
)
from app.agents.checkpoint_provider import MemoryCheckpointProvider
from app.agents.graph_nodes import (
    user_request_node,
    load_memory_node,
    plan_validator_node,
    scheduler_node,
    responder_node,
    update_memory_node,
)
from app.agents.planner_subgraph import planner_subgraph
from app.agents.execution_subgraph import execute_task_subgraph
from app.agents.executor_router import ExecutorRouter

def route_after_validator(state: TravelAgentState):
    """Router gate evaluating validation status after PlanValidator node."""
    val_result = state.get("validation_result")
    replan_count = state.get("replan_count", 0)
    max_replan_attempts = state.get("max_replan_attempts", 3)
    
    if val_result and not val_result.valid:
        if val_result.recoverable == Recoverability.RECOVERABLE and replan_count < max_replan_attempts:
            logger.warning(f"Plan validation failed with recoverable error: {val_result.message}. Returning to planner.")
            return "planner"
        else:
            logger.error(f"Plan validation failed with fatal error or max replans reached: {val_result.message}. Aborting.")
            return "responder"
    
    return "scheduler"

def route_after_scheduler(state: TravelAgentState):
    """Routing edge evaluating execution outcomes from Scheduler node."""
    scheduler_result = state.get("scheduler_result")
    replan_count = state.get("replan_count", 0)
    max_replan_attempts = state.get("max_replan_attempts", 3)
    policy = state.get("execution_policy") or "best_effort"
    tasks = state["execution_plan"].tasks
    
    # 1. Check if all tasks are completed
    if len(scheduler_result.completed_tasks) == len(tasks):
        logger.info("Execution plan completed successfully with all tasks completed.")
        return "responder"
        
    # 2. Dynamic Parallel Task Scheduler (concurrency resolution)
    if scheduler_result.has_ready_tasks:
        logger.info(f"Scheduling {len(scheduler_result.ready_tasks)} parallel execution task(s): {scheduler_result.ready_tasks}")
        return [Send("execute_task", {"task_id": t_id, "task": tasks[t_id]}) for t_id in scheduler_result.ready_tasks]
        
    # 3. Evaluate failures when no ready tasks remain
    if scheduler_result.failed_tasks:
        if policy == "fail_fast":
            logger.warning("Fail-fast policy triggered by task failure. Aborting execution loop.")
            return "responder"
            
        if replan_count >= max_replan_attempts:
            logger.warning("Maximum replanning attempts reached. Ending execution.")
            return "responder"
            
        logger.info(f"Replanning attempt {replan_count + 1}/{max_replan_attempts} triggered by task failure.")
        return "planner"
        
    # 4. Deadlock / Finish fallback
    if scheduler_result.waiting_tasks or scheduler_result.blocked_tasks:
        logger.warning(f"No ready tasks available. Waiting tasks: {scheduler_result.waiting_tasks}. Blocked tasks: {scheduler_result.blocked_tasks}.")
        return "responder"
        
    return "responder"

class CoordinatorAgent:
    def __init__(self):
        self.llm_client = get_llm()
        self.responder = ResponseAgent()
        self.memory = ConversationMemory()
        self.executor_router = ExecutorRouter()
        self.retry_policy = RetryPolicy()
        
        # Build base coordinator graph
        builder = StateGraph(TravelAgentState)
        
        # Define nodes
        builder.add_node("user_request", user_request_node)
        builder.add_node("load_memory", load_memory_node)
        builder.add_node("planner", planner_subgraph)
        builder.add_node("plan_validator", plan_validator_node)
        builder.add_node("scheduler", scheduler_node)
        builder.add_node("execute_task", execute_task_subgraph)
        builder.add_node("responder", responder_node)
        builder.add_node("update_memory", update_memory_node)
        
        # Define edges
        builder.add_edge(START, "user_request")
        builder.add_edge("user_request", "load_memory")
        builder.add_edge("load_memory", "planner")
        builder.add_edge("planner", "plan_validator")
        
        # Validation router
        builder.add_conditional_edges(
            "plan_validator",
            route_after_validator,
            {
                "planner": "planner",
                "responder": "responder",
                "scheduler": "scheduler",
            }
        )
        
        # Scheduler router
        builder.add_conditional_edges(
            "scheduler",
            route_after_scheduler,
            {
                "execute_task": "execute_task",
                "planner": "planner",
                "responder": "responder",
            }
        )
        
        # Loopback execute task output into scheduler node
        builder.add_edge("execute_task", "scheduler")
        
        builder.add_edge("responder", "update_memory")
        builder.add_edge("update_memory", END)
        
        # Compile
        self.checkpoint_provider = MemoryCheckpointProvider()
        self.graph = builder.compile(checkpointer=self.checkpoint_provider.get_checkpointer())

    def run(
        self,
        user_goal: str,
        on_progress: Callable[[ProgressEvent], None] = None,
        policy: ExecutionPolicy = ExecutionPolicy.BEST_EFFORT,
    ) -> str:
        """Run the travel agent workflow via compiled LangGraph."""
        logger.info(f"Invoking Travel Agent graph for query: '{user_goal}'")
        
        initial_state = {
            "user_request": user_goal,
            "messages": [],
            "execution_plan": ExecutionPlan(tasks={}),
            "replan_count": 0,
            "max_replan_attempts": 3,
            "execution_policy": policy.value if hasattr(policy, "value") else policy,
            "interrupt": None,
            "planner_context": PlannerContext(),
            "memory_context": MemoryContext(),
            "metadata_context": MetadataContext(),
            "final_response": "",
            "validation_result": ValidationResult(valid=True),
            "scheduler_result": SchedulerResult(),
        }
        
        config = {
            "configurable": {
                "thread_id": "session-default",
                "conversation_memory": self.memory,
                "llm_client": self.llm_client,
                "model_name": MODEL_NAME,
                "response_agent": self.responder,
                "executor_router": self.executor_router,
                "retry_policy": self.retry_policy,
                "on_progress": on_progress,
                "user_request": user_goal,
            }
        }
        
        final_state = self.graph.invoke(initial_state, config)
        return final_state["final_response"]