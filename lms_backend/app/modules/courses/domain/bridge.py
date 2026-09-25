"""
Módulo: Courses - Capa de Dominio
Patrón de Diseño: Bridge (Estructural)
Principios SOLID: SRP, OCP, DIP
"""

from abc import ABC, abstractmethod


# --- IMPLEMENTADOR (Bridge Implementation Interface) ---
class MediaStorageProvider(ABC):
    """
    Interfaz del Implementador. Define las operaciones de infraestructura de medios.
    """
    @abstractmethod
    def get_stream_url(self, media_id: str) -> str:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


# Implementadores Concretos
class VimeoStorageProvider(MediaStorageProvider):
    def get_stream_url(self, media_id: str) -> str:
        return f"https://player.vimeo.com/video/{media_id}"

    def get_provider_name(self) -> str:
        return "Vimeo Pro"


class S3StorageProvider(MediaStorageProvider):
    def get_stream_url(self, media_id: str) -> str:
        return f"https://lms-bucket.s3.amazonaws.com/courses/videos/{media_id}.mp4"

    def get_provider_name(self) -> str:
        return "AWS S3 Secure Storage"


# --- ABSTRACCIÓN (Bridge Abstraction) ---
class LessonContent(ABC):
    """
    Abstracción principal. Mantiene una referencia al implementador (Bridge).
    """
    def __init__(self, title: str, media_id: str, provider: MediaStorageProvider):
        self.title = title
        self.media_id = media_id
        self._provider = provider  # El "Puente" (Bridge) hacia la infraestructura

    @abstractmethod
    def render_content(self) -> str:
        pass


# Abstracciones Refinadas
class VideoLesson(LessonContent):
    def render_content(self) -> str:
        url = self._provider.get_stream_url(self.media_id)
        provider_name = self._provider.get_provider_name()
        return f"[Video Player ({provider_name})]: Reproduciendo '{self.title}' desde {url}"


class InteractiveQuizLesson(LessonContent):
    def render_content(self) -> str:
        url = self._provider.get_stream_url(self.media_id)
        return f"[Quiz Interactivo]: Cargando recursos multimedia del examen desde {url}"