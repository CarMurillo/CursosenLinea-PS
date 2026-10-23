
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class ContentMetadata:
    """
    Estado intrínseco compartido entre contenidos.
    Es inmutable para evitar modificaciones accidentales.
    """
    content_type: str
    label: str
    icon: str


class ContentMetadataFactory:
    """
    Flyweight Factory: reutiliza metadatos iguales.
    """

    _items: dict[str, ContentMetadata] = {}
    _lock = Lock()

    @classmethod
    def get_metadata(cls, content_type: str) -> ContentMetadata:
        key = content_type.strip().lower()

        definitions = {
            "video": ContentMetadata(
                content_type="video",
                label="Video",
                icon="play-circle",
            ),
            "quiz": ContentMetadata(
                content_type="quiz",
                label="Cuestionario",
                icon="clipboard-check",
            ),
            "document": ContentMetadata(
                content_type="document",
                label="Documento",
                icon="file-text",
            ),
        }

        if key not in definitions:
            raise ValueError(
                f"Tipo de contenido no soportado: {content_type}"
            )

        with cls._lock:
            if key not in cls._items:
                cls._items[key] = definitions[key]

            return cls._items[key]

    @classmethod
    def cache_size(cls) -> int:
        return len(cls._items)
