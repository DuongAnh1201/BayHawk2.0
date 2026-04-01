from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """Execute the agent's core logic and return its typed result."""

    async def __call__(self, **kwargs) -> Any:
        return await self.run(**kwargs)
