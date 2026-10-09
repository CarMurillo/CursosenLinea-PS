from app.shared.system_config import get_system_config

class PaymentService:
    def __init__(self):
        # Inyectamos la configuración compartida
        self.config = get_system_config()

    def process_payment(self, amount: float):
        currency = self.config.get("currency", "USD")
        print(f"Procesando pago de {amount} {currency} en {self.config.get('app_name')}")