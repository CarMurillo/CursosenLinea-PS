"""Base común de los DTO de entrada (capa de aplicación).

`StrictDTO` rechaza `Infinity`/`NaN` en todos los campos float
(`allow_inf_nan=False`): sin esto, un JSON como `{"price": 1e999}` se
convertía en `inf`, se guardaba y rompía después la serialización (500).
Con la base, Pydantic responde 422 antes de llegar al caso de uso.
"""

from pydantic import BaseModel, ConfigDict

# Tope razonable para montos (precio de curso, monto de pago).
MAX_MONEY_AMOUNT = 1_000_000_000


class StrictDTO(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
