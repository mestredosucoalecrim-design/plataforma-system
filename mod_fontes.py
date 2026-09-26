import pandas as pd
from bcb import sgs


def buscar_cdi_anual():

    df_cdi = sgs.get(
        {"CDI": 4389},
        start="2026-01-01"
    )

    ultimo_registro = df_cdi.iloc[-1]

    cdi_anual = ultimo_registro["CDI"]
    data_referencia = df_cdi.index[-1]

    return {
        "cdi_anual": cdi_anual,
        "data_referencia": data_referencia
    }