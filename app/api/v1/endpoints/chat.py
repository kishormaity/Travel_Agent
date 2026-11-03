import json
import asyncio
from uuid import uuid4
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger

from app.agents import CoordinatorAgent
from app.schemas.planner import ProgressEvent
from app.services.trip_extractor import extract_structured_trip_data

router = APIRouter(tags=["Chat"])
coordinator = CoordinatorAgent()


class ChatApiRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User travel planning prompt.")
    conversation_id: str | None = Field(default=None, description="Existing session thread ID.")


class ChatApiResponse(BaseModel):
    conversation_id: str
    response: str
    status: str = "success"
    structured_data: dict | None = None


@router.post("/chat", response_model=ChatApiResponse)
def chat_endpoint(payload: ChatApiRequest):
    """
    Process travel planning request through the StateGraph DAG Travel Agent.
    """
    thread_id = payload.conversation_id or str(uuid4())
    logger.info(f"Processing chat request for session {thread_id}: {payload.message}")

    run_result = coordinator.run_full(user_goal=payload.message, thread_id=thread_id)
    final_response = run_result.get("final_response", "")
    plan = run_result.get("execution_plan")

    structured = extract_structured_trip_data(
        user_goal=payload.message,
        final_response=final_response,
        execution_plan=plan,
        trip_id=thread_id,
    )

    return ChatApiResponse(
        conversation_id=thread_id,
        response=final_response,
        status="success",
        structured_data=structured,
    )


@router.get("/chat/stream")
async def chat_stream_endpoint(
    message: str = Query(..., min_length=1),
    conversation_id: str | None = Query(default=None),
):
    """
    Server-Sent Events (SSE) streaming endpoint emitting real-time agent progress events
    and the final synthesized itinerary with structured data.
    """
    thread_id = conversation_id or str(uuid4())
    event_queue = asyncio.Queue()

    def progress_callback(event: ProgressEvent):
        data = {
            "type": "progress",
            "task_id": event.task_id,
            "description": event.description,
            "status": event.status.value,
            "worker_id": event.worker_id,
            "execution_time": event.execution_time,
            "error": event.error,
        }
        event_queue.put_nowait(data)

    async def event_generator():
        yield f"data: {json.dumps({'type': 'start', 'conversation_id': thread_id})}\n\n"

        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            None,
            lambda: coordinator.run_full(
                user_goal=message,
                on_progress=progress_callback,
                thread_id=thread_id,
            ),
        )

        while not future.done():
            while not event_queue.empty():
                evt = event_queue.get_nowait()
                yield f"data: {json.dumps(evt)}\n\n"
            await asyncio.sleep(0.1)

        # Flush any remaining events
        while not event_queue.empty():
            evt = event_queue.get_nowait()
            yield f"data: {json.dumps(evt)}\n\n"

        try:
            run_result = await future
            final_response = run_result.get("final_response", "")
            plan = run_result.get("execution_plan")
            structured = extract_structured_trip_data(
                user_goal=message,
                final_response=final_response,
                execution_plan=plan,
                trip_id=thread_id,
            )

            yield f"data: {json.dumps({'type': 'final_response', 'content': final_response, 'structured_data': structured})}\n\n"
        except Exception as e:
            logger.error(f"Error in chat_stream_endpoint: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

