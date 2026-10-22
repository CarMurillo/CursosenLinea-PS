from abc import ABC, abstractmethod

from app.modules.courses.domain.content_component import (
    ContentComponent
)


class MediaStorageProvider(ABC):
    """
    Implementador del patrón Bridge.

    Define cómo obtener el recurso multimedia
    independientemente del tipo de lección.
    """

    @abstractmethod
    def get_stream_url(self, media_id: str) -> str:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class VimeoStorageProvider(MediaStorageProvider):

    def get_stream_url(self, media_id: str) -> str:
        return (
            f"https://player.vimeo.com/video/{media_id}"
        )

    def get_provider_name(self) -> str:
        return "Vimeo Pro"


class S3StorageProvider(MediaStorageProvider):

    def get_stream_url(self, media_id: str) -> str:
        return (
            "https://lms-bucket.s3.amazonaws.com/"
            f"courses/videos/{media_id}.mp4"
        )

    def get_provider_name(self) -> str:
        return "AWS S3 Secure Storage"


class LessonContent(ContentComponent, ABC):
    """
    Abstracción del Bridge.

    Una lección puede trabajar con diferentes
    proveedores de almacenamiento.
    """

    def __init__(
        self,
        title: str,
        media_id: str,
        provider: MediaStorageProvider
    ):
        self.title = title
        self.media_id = media_id
        self._provider = provider


class VideoLesson(LessonContent):

    def render_content(self) -> str:

        url = self._provider.get_stream_url(
            self.media_id
        )

        provider_name = (
            self._provider.get_provider_name()
        )

        return (
            f"[Video Player ({provider_name})]: "
            f"Reproduciendo '{self.title}' "
            f"desde {url}"
        )

    def to_dict(self) -> dict:

        return {
            "type": "video",
            "title": self.title,
            "media_id": self.media_id,
            "provider": (
                self._provider.get_provider_name()
            ),
            "url": (
                self._provider.get_stream_url(
                    self.media_id
                )
            ),
            "rendered": self.render_content(),
        }


class InteractiveQuizLesson(LessonContent):

    def render_content(self) -> str:

        url = self._provider.get_stream_url(
            self.media_id
        )

        return (
            "[Quiz Interactivo]: "
            "Cargando recursos multimedia "
            f"desde {url}"
        )

    def to_dict(self) -> dict:

        return {
            "type": "quiz",
            "title": self.title,
            "media_id": self.media_id,
            "provider": (
                self._provider.get_provider_name()
            ),
            "url": (
                self._provider.get_stream_url(
                    self.media_id
                )
            ),
            "rendered": self.render_content(),
        }