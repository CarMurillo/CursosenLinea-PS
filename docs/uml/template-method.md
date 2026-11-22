# Template Method en las pasarelas de pago

Fuente: `app/modules/payments/domain/adapter.py`. Consumidor: `ProcessPaymentUseCase` en
`app/modules/payments/application/use_cases.py`.

```mermaid
classDiagram
    class PaymentGatewayPort {
        <<abstract>>
        +process_payment(amount, currency, customer_email) PaymentResult*
    }
    class TemplatePaymentAdapter {
        <<abstract>>
        +gateway_name: str
        +process_payment(amount, currency, customer_email) PaymentResult
        #_call_gateway(amount, currency, customer_email) dict*
        #_is_approved(response) bool*
        #_transaction_id(response) str*
        #_prepare_amount(amount) Any
        #_success_message() str
        #_failure_message() str
        #_result(success, tx_id, amount, currency, message) PaymentResult$
    }
    class StripePaymentAdapter {
        +gateway_name = Stripe
        -_sdk: StripeSDK
        #_prepare_amount(amount) int
        #_call_gateway(amount, currency, customer_email) dict
        #_is_approved(response) bool
        #_transaction_id(response) str
        #_failure_message() str
    }
    class WompiPaymentAdapter {
        +gateway_name: str
        -_sdk: WompiSDK
        #_call_gateway(amount, currency, customer_email) dict
        #_is_approved(response) bool
        #_transaction_id(response) str
        #_failure_message() str
    }
    class StripeSDK {
        +create_charge(amount_in_cents, currency_code, email) dict
    }
    class WompiSDK {
        +create_transaction(amount_in_cop, reference, payer_email) dict
    }
    class PaymentResult {
        +success: bool
        +transaction_id: str
        +amount: float
        +currency: str
        +message: str
    }
    class ProcessPaymentUseCase {
        +execute(dto, user_id, customer_email, customer_name) Payment
    }

    PaymentGatewayPort <|-- TemplatePaymentAdapter
    TemplatePaymentAdapter <|-- StripePaymentAdapter
    TemplatePaymentAdapter <|-- WompiPaymentAdapter
    StripePaymentAdapter --> StripeSDK : adapta (simulado)
    WompiPaymentAdapter --> WompiSDK : adapta (simulado)
    TemplatePaymentAdapter ..> PaymentResult : construye
    ProcessPaymentUseCase --> PaymentGatewayPort : gateways por nombre
```

Orden fijo de `process_payment` (método plantilla; ninguna subclase lo sobrescribe):

1. Validar `amount > 0`. Si falla, devuelve un rechazo sin llamar al SDK.
2. Pasar `currency` a mayúsculas.
3. `_prepare_amount(amount)`: gancho. Por defecto devuelve el mismo monto; Stripe lo pasa a centavos con `round`.
4. `_call_gateway(...)`: paso abstracto. Una excepción del SDK se registra con `logging` y se convierte en rechazo.
5. `_is_approved(response)` y `_transaction_id(response)`: pasos abstractos.
6. `_success_message()` o `_failure_message()`: ganchos con mensaje por defecto.
7. `_result(...)`: construye el `PaymentResult`.

`WompiPaymentAdapter.gateway_name` vale `"Wompi (Colombia)"` (se omite en el diagrama porque Mermaid lee los paréntesis como método).

Leyenda: `*` = abstracto, `$` = estático, `#` = protegido por convención (prefijo `_`).
Los SDK son simulados: no hay red ni claves.
