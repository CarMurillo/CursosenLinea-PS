
from app.shared.infrastructure.config.system_config import SystemConfig


def test_system_config_singleton():
    # Obtener dos referencias del Singleton
    config1 = SystemConfig()
    config2 = SystemConfig()

    # Comprobar que ambas referencias apuntan exactamente al mismo objeto en memoria
    assert config1 is config2
    assert config1.system_name == config2.system_name
    assert config1.initialization_time == config2.initialization_time


def test_system_config_properties():
    config = SystemConfig()
    info = config.get_info()

    assert info["system_name"] == "LMS Advanced Platform"
    assert info["version"] == "1.0.0"
    assert "initialized_at" in info