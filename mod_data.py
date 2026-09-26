from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


FUSO_HORARIO_SISTEMA = "America/Sao_Paulo"


def data_atual():
    """Retorna a data atual do S.Y.S.T.E.M. no horário de Brasília."""
    return datetime.now(
        ZoneInfo(FUSO_HORARIO_SISTEMA)
    ).date()


def data_atual_menos_dias(dias):
    """Retorna a data atual do S.Y.S.T.E.M. menos a quantidade de dias informada."""
    return data_atual() - timedelta(days=dias)
