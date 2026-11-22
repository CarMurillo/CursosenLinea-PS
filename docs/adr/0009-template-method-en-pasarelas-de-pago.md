# ADR 0009: Template Method en las pasarelas de pago

- Estado: aceptado
- Código: `app/modules/payments/domain/adapter.py` (`TemplatePaymentAdapter`, `StripePaymentAdapter`,
  `WompiPaymentAdapter`)
- Pruebas: `tests/test_template_method.py` (Template Method), `tests/test_payments.py` (Adapter)

## Contexto

`StripePaymentAdapter` y `WompiPaymentAdapter` duplicaban el mismo flujo de cobro. Solo cambiaban la
llamada al SDK y la lectura de la respuesta. Una tercera pasarela iba a copiar el flujo otra vez.
Además, no había validación común del monto ni manejo de errores del SDK: una excepción del SDK
terminaba en HTTP 500 en `POST /payments/process`.

## Decisión

- Clase abstracta `TemplatePaymentAdapter(PaymentGatewayPort)` con el método plantilla `process_payment`.
- Pasos fijos: validar el monto (> 0, si falla rechaza sin llamar al SDK); moneda en mayúsculas;
  gancho `_prepare_amount`; paso abstracto `_call_gateway` (una excepción se registra con `logging` y
  se convierte en rechazo); pasos abstractos `_is_approved` y `_transaction_id`; ganchos
  `_success_message` y `_failure_message`; construcción del `PaymentResult`.
- `StripePaymentAdapter` sobrescribe `_prepare_amount` (centavos con `round`) y `_failure_message`.
  `WompiPaymentAdapter` arma la referencia `REF-LMS-<usuario>` en `_call_gateway`. Ninguna subclase
  sobrescribe `process_payment`.
- Los adaptadores siguen siendo Adapters de `StripeSDK` y `WompiSDK` (simulados). El puerto
  `PaymentGatewayPort` y `ProcessPaymentUseCase` no cambian.

## Consecuencias

- Positivas: el esqueleto de cobro vive en un solo lugar. Validación, moneda y manejo de errores se
  aplican a todas las pasarelas. Agregar una pasarela = implementar 3 pasos (`_call_gateway`,
  `_is_approved`, `_transaction_id`). Un fallo del SDK llega al caso de uso como rechazo
  (`PaymentRejectedError` → HTTP 400), no como HTTP 500.
- Negativas: herencia en lugar de composición; una pasarela con un flujo muy distinto (por ejemplo,
  redirección y webhook asíncrono) no encajaría en este esqueleto y necesitaría otro adaptador del
  puerto. La validación de monto se repite con la del DTO (`Field(gt=0)`), a propósito: el DTO protege
  la API y el método plantilla protege a cualquier cliente del puerto.

## Alternativas descartadas

- Mantener el flujo duplicado en cada adaptador: cada pasarela nueva repetiría validación y manejo de errores.
- Template Method en los observadores (`AutoEnrollOnPaymentObserver`, `CertificateIssuerObserver`,
  `RecommendationProfileObserver`), que repiten la guarda del tipo de evento y la validación de
  `user_id`/`course_id`: la duplicación es de 2 o 3 líneas por clase, cada observador ya tiene una sola
  responsabilidad y una jerarquía base añadiría acoplamiento sin beneficio claro. Queda como posible mejora.
