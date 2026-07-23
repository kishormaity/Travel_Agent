from abc import ABC, abstractmethod
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

class BaseCheckpointProvider(ABC):
    @abstractmethod
    def get_checkpointer(self) -> BaseCheckpointSaver:
        """Return the checkpointer instance."""
        pass

class MemoryCheckpointProvider(BaseCheckpointProvider):
    def __init__(self):
        self._saver = MemorySaver()

    def get_checkpointer(self) -> BaseCheckpointSaver:
        return self._saver
