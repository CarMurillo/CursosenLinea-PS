import sys
from pathlib import Path

# Inclusión dinámica del directorio raíz del backend
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.modules.payments.domain.adapter import (
    StripePaymentAdapter,
    WompiPaymentAdapter,
    PaymentGatewayPort
)
from app.modules.courses.domain.bridge import (
    VimeoStorageProvider,
    S3StorageProvider,
    VideoLesson,
    InteractiveQuizLesson
)


def run_tests():
    print("=" * 60)
    print("DEMOSTRACIÓN SEMANA 7: PATRONES ADAPTER & BRIDGE (SOLID)")
    print("=" * 60)

    # 1. PRUEBA PATRÓN ADAPTER
    print("\n--- 1. Probrando Patrón Adapter (Pasarelas de Pago) ---")
    
    # Inyección de dependencias usando la misma abstracción PaymentGatewayPort
    adapters: list[PaymentGatewayPort] = [
        StripePaymentAdapter(),
        WompiPaymentAdapter()  # Adaptador para pasarela colombiana
    ]

    for adapter in adapters:
        result = adapter.process_payment(
            amount=150000.0,
            currency="COP",
            customer_email="estudiante@universidad.edu.co"
        )
        print(f"-> Pasarela: {adapter.__class__.__name__}")
        print(f"   Estado: {'Éxito' if result.success else 'Fallo'} | TX ID: {result.transaction_id}")
        print(f"   Mensaje: {result.message}\n")

    # 2. PRUEBA PATRÓN BRIDGE
    print("--- 2. Probando Patrón Bridge (Gestión de Lecciones y Almacenamiento) ---")
    
    # Proveedores de almacenamiento (Implementadores)
    vimeo = VimeoStorageProvider()
    s3 = S3StorageProvider()

    # Lecciones (Abstracciones) combinadas dinámicamente con los proveedores
    lesson_1 = VideoLesson("Introducción a SOLID", "vimeo_987654", vimeo)
    lesson_2 = VideoLesson("Implementación de Bridge", "video_aws_001", s3)
    quiz = InteractiveQuizLesson("Evaluación Módulo 3", "assets_quiz_10", s3)

    print(f"-> {lesson_1.render_content()}")
    print(f"-> {lesson_2.render_content()}")
    print(f"-> {quiz.render_content()}")

    print("\n✅ ¡Todos los patrones estructurales ejecutados correctamente!")


if __name__ == "__main__":
    run_tests()