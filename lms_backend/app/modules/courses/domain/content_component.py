
from abc import ABC, abstractmethod


class ContentComponent(ABC):
    """
    Componente común utilizado por el patrón Composite.
    """

    @abstractmethod
    def render_content(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

