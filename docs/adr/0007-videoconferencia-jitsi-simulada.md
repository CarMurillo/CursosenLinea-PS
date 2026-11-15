# ADR 0007: Videoconferencia Jitsi simulada (y pagos simulados)

- Estado: aceptado
- Código: `app/modules/live_sessions/domain/ports.py` (`VideoConferencePort`),
  `app/modules/live_sessions/infrastructure/jitsi_adapter.py` (`JitsiAdapter`),
  `app/modules/payments/domain/adapter.py`

## Contexto

El objetivo 3 pide clases en vivo con grabación automática. Integrar un proveedor real exige cuentas,
claves, red y almacenamiento de grabaciones, fuera del alcance de la entrega. Lo mismo aplica a las
pasarelas de pago (objetivo 5).

## Decisión

- Puerto `VideoConferencePort` (`create_room`, `start_meeting`, `end_meeting`, `get_recording_url`).
- `JitsiAdapter` **simulado**: genera `https://meet.jit.si/lms-<slug>-<id>` como sala y
  `https://recordings.lms.local/jitsi/<sala>.mp4` como grabación. No hace llamadas de red ni graba nada.
- Pagos: `StripePaymentAdapter` y `WompiPaymentAdapter` sobre SDK simulados (`StripeSDK`, `WompiSDK`).
- Sin SDK ni claves reales en el repositorio.

## Consecuencias

- Positivas: el flujo completo (State + Observer + notificaciones) se puede demostrar y probar sin
  servicios externos. Cambiar a Zoom/Meet o a una pasarela real es otro adaptador del mismo puerto.
- Negativas: la URL de sala apunta al servicio público de Jitsi, pero la URL de grabación no existe.
  El pago compara el monto contra `price` sin conversión de moneda.
