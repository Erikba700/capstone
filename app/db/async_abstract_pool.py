from abc import ABC, abstractmethod


class AbstractAsyncPool(ABC):
    """Abstract base class for asynchronous connection pools."""

    @abstractmethod
    def get_session(self) -> object:
        """Should return a new async session or connection."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Should close the pool and all connections."""
        pass
