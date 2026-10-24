
from dataclasses import dataclass
from threading import Lock
from types import MappingProxyType


@dataclass(frozen=True)
class ContentMetadata:
    """
    Flyweight: estado INTRÍNSECO compartido (inmutable).
    El estado extrínseco (título, media_id, proveedor) vive en cada lección.
    """
    content_type: str
    label: str
    icon: str


# Definiciones (datos puros). Se crean UNA sola vez; los objetos
# ContentMetadata se instancian de forma perezosa en la fábrica.
_DEFINITIONS = MappingProxyType({
    "video": ("Video", "play-circle"),
    "quiz": ("Cuestionario", "clipboard-check"),
    "document": ("Documento", "file-text"),
})


class ContentMetadataFactory:
    """Flyweight Factory: devuelve siempre la misma instancia por tipo."""

    _items: dict[str, ContentMetadata] = {}
    _lock = Lock()

    @classmethod
    def get_metadata(cls, content_type: str) -> ContentMetadata:
        key = content_type.strip().lower()

        if key not in _DEFINITIONS:
            raise ValueError(
                f"Tipo de contenido no soportado: {content_type}"
            )

        with cls._lock:
            metadata = cls._items.get(key)
            if metadata is None:
                label, icon = _DEFINITIONS[key]
                metadata = ContentMetadata(key, label, icon)
                cls._items[key] = metadata
            return metadata

    @classmethod
    def cache_size(cls) -> int:
        return len(cls._items)
