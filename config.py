# config.py
"""
MÓDULO DE CONFIGURACIÓN GLOBAL - LMS AVANZADO

Patrón de Diseño Utilizado: SINGLETON (Creacional)

Rol en el Proyecto:
-------------------
En una Plataforma de Cursos en Línea (LMS), la configuración global (nombre del sistema,
moneda predeterminada, límites de almacenamiento para grabaciones de videoconferencias y
estado del motor de aprendizaje adaptativo) debe ser única y consistente en todos los módulos.

El patrón Singleton garantiza que exista una única instancia de `LMSConfig` en memoria,
evitando incongruencias donde un módulo cambie la moneda o el nombre de la plataforma y otro
módulo siga consultando datos desactualizados.

Principios SOLID Aplicados:
---------------------------
- SRP (Single Responsibility Principle): La clase `LMSConfig` responde únicamente a la 
  responsabilidad de almacenar y proveer el estado de la configuración del LMS.

- DIP (Dependency Inversion Principle): Se define la interfaz abstracta `IConfigService` 
  para que el resto de componentes (servicios de pago, videoconferencias, cursos) dependan 
  de una abstracción y no directamente de la clase concreta `LMSConfig`.
  
- ISP (Interface Segregation Principle): La interfaz ofrece métodos específicos únicamente 
  relacionados con la lectura y modificación de parámetros de configuración.
"""

from abc import ABC, abstractmethod


class IConfigService(ABC):
    """Interfaz abstracta para el servicio de configuración (Cumple con DIP)"""

    @abstractmethod
    def get_setting(self, key: str):
        pass

    @abstractmethod
    def set_setting(self, key: str, value):
        pass


class LMSConfig(IConfigService):
    """
    Implementación del Patrón Singleton para la Configuración Centralizada del LMS.
    """
    _instance = None  # Variable de clase para guardar la instancia única

    def __new__(cls, *args, **kwargs):
        """Sobrescribimos __new__ para garantizar que solo exista una instancia"""
        if cls._instance is None:
            cls._instance = super(LMSConfig, cls).__new__(cls)
            # Inicialización de variables globales del LMS
            cls._instance._settings = {
                "platform_name": "LMS Avanzado",
                "currency": "USD",
                "max_recording_storage_gb": 50,
                "adaptive_learning_enabled": True
            }
        return cls._instance

    def get_setting(self, key: str):
        return self._settings.get(key)

    def set_setting(self, key: str, value):
        self._settings[key] = value

    def __str__(self):
        return f"Configuración LMS: {self._settings}"