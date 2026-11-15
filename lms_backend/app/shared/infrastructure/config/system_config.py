import os
from datetime import datetime

DEFAULT_CORS_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


class SystemConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.app_name = os.getenv("APP_NAME", "LMS Advanced Platform")
        self.system_name = self.app_name
        self.version = "1.0.0"
        self.debug_mode = os.getenv("DEBUG_MODE", "True").lower() == "true"
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
        # CORS: orígenes permitidos separados por comas (no "*" porque se
        # envían credenciales). Por defecto, el frontend de Vite en local.
        self.cors_origins = [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS", ",".join(DEFAULT_CORS_ORIGINS)
            ).split(",")
            if origin.strip()
        ]
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.initialization_time = datetime.now()

    def get_info(self) -> dict:
        return {
            "system_name": self.system_name,
            "version": self.version,
            "initialized_at": self.initialization_time.isoformat(),
        }


def get_system_config():
    return SystemConfig()