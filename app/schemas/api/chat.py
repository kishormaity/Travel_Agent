from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """
    User message sent to the travel agent.
    """
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """
    AI response returned to the user.
    """
    response: str