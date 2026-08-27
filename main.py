# main.py
from config import LMSConfig, IConfigService

# Demostración del Principio de Inversión de Dependencias (DIP):
# La función recibe una abstracción (IConfigService) en lugar de depender directamente de la clase concreta.
def mostrar_configuracion(config_service: IConfigService):
    print(f"Nombre de la plataforma: {config_service.get_setting('platform_name')}")
    print(f"Moneda activa: {config_service.get_setting('currency')}")

def main():
    config1 = LMSConfig()
    config2 = LMSConfig()

    print("--- Demostración Singleton + SOLID ---")
    print(f"¿Es la misma instancia en memoria? {config1 is config2}")  # Imprime True

    print("\n[DIP] Consultando a través de la interfaz abstracta:")
    mostrar_configuracion(config1)

    # Modificamos la configuración desde una referencia
    config1.set_setting("platform_name", "LMS Avanzado - Universidad")

    print("\nDespués de modificar la configuración:")
    print(f"Reflejado en config2: {config2.get_setting('platform_name')}")

if __name__ == "__main__":
    main()