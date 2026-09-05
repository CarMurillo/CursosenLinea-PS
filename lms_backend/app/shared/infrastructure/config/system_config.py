import os
from datetime import datetime


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
        self.initialization_time = datetime.now()

    def get_info(self) -> dict:
        return {
            "system_name": self.system_name,
            "version": self.version,
            "initialized_at": self.initialization_time.isoformat(),
        }


def get_system_config():
    return SystemConfig()