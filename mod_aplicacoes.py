import pandas as pd


# =========================================================
# PLATAFORMA S.Y.S.T.E.M.
# Módulo: mod_aplicacoes
# Objetivo: Motor de Aplicações Financeiras
# =========================================================

def calcular_rendimento_mensal(valor_aplicado, taxa_anual):
    """
    Calcula o rendimento de um mês utilizando
    uma taxa anual convertida para uma taxa mensal equivalente.

    Parâmetros:
        valor_aplicado (float): valor do capital aplicado.
        taxa_anual (float): taxa anual em formato decimal.
                           Ex.: 13,86% = 0.1386

    Retorna:
        float: rendimento do primeiro mês.
    """

    taxa_mensal = (1 + taxa_anual) ** (1 / 12) - 1

    rendimento = valor_aplicado * taxa_mensal

    return rendimento

import pandas as pd


def simular_aplicacao(
    valor_inicial,
    taxa_anual,
    quantidade_meses,
    data_pesquisa
):
    """
    Simula a evolução mensal de uma aplicação.

    A data da pesquisa é considerada a Data 0.
    O primeiro rendimento ocorre um mês após a Data 0.

    Parâmetros:
        valor_inicial (float): capital inicial.
        taxa_anual (float): taxa anual em formato decimal.
        quantidade_meses (int): quantidade de meses da aplicação.
        data_pesquisa: Data 0 da simulação.

    Retorna:
        pandas.DataFrame contendo:
            Data
            Mês
            Capital inicial
            Rendimento
            Saldo
    """

    taxa_mensal = (1 + taxa_anual) ** (1 / 12) - 1

    capital = valor_inicial

    resultados = []

    data_pesquisa = pd.to_datetime(data_pesquisa, dayfirst=True)
    for mes in range(1, quantidade_meses + 1):

        data_periodo = data_pesquisa + pd.DateOffset(months=mes)

        rendimento = capital * taxa_mensal

        saldo = capital + rendimento

        resultados.append({
            "Data": data_periodo,
            "Mês": mes,
            "Capital inicial": capital,
            "Rendimento": rendimento,
            "Saldo": saldo
        })

        capital = saldo

    return pd.DataFrame(resultados)


def criar_aplicacao(
    valor,
    taxa_anual,
    quantidade_meses,
    data_aplicacao
):
    """
    Cria uma aplicação individual.

    Cada aplicação possui:
        - valor próprio
        - data própria
        - taxa própria
        - prazo próprio

    Retorna:
        pandas.DataFrame com a evolução da aplicação.
    """

    return simular_aplicacao(
        valor_inicial=valor,
        taxa_anual=taxa_anual,
        quantidade_meses=quantidade_meses,
        data_pesquisa=data_aplicacao
    )

def gerar_aplicacoes_recorrentes(
    valor_mensal,
    quantidade_meses,
    data_inicial
):
    """
    Gera as aplicações recorrentes de uma carteira.

    A Data 0 pertence à aplicação inicial.
    A primeira aplicação recorrente ocorre um mês depois.

    Parâmetros:
        valor_mensal (float): valor aplicado a cada mês.
        quantidade_meses (int): quantidade de aplicações recorrentes.
        data_inicial: Data 0 da carteira.

    Retorna:
        pandas.DataFrame contendo:
            Data
            Mês
            Valor aplicado
    """

    data_inicial = pd.to_datetime(
        data_inicial,
        dayfirst=True
    )

    resultados = []

    for mes in range(1, quantidade_meses + 1):

        data_aplicacao = (
            data_inicial +
            pd.DateOffset(months=mes)
        )

        resultados.append({
            "Data": data_aplicacao,
            "Mês": mes,
            "Valor aplicado": valor_mensal
        })

    return pd.DataFrame(resultados)  

def simular_aplicacoes_recorrentes(
    valor_mensal,
    quantidade_meses,
    data_inicial,
    taxa_anual
):
    """
    Simula aplicações mensais recorrentes.
    Cada aplicação é tratada como lote independente.

    A aplicação feita na data final da simulação
    entra na carteira, mas ainda não possui rendimento.
    """

    aplicacoes = []

    recorrentes = gerar_aplicacoes_recorrentes(
        valor_mensal,
        quantidade_meses,
        data_inicial
    )

    colunas = [
        "Data",
        "Mês",
        "Capital inicial",
        "Rendimento",
        "Saldo"
    ]

    for _, linha in recorrentes.iterrows():

        mes_aplicacao = int(linha["Mês"])

        meses_restantes = (
            quantidade_meses - mes_aplicacao
        )

        if meses_restantes > 0:

            evolucao = criar_aplicacao(
                valor=linha["Valor aplicado"],
                taxa_anual=taxa_anual,
                quantidade_meses=meses_restantes,
                data_aplicacao=linha["Data"]
            )

        else:

            evolucao = pd.DataFrame(
                columns=colunas
            )

        aplicacoes.append({
            "mes_aplicacao": mes_aplicacao,
            "data_aplicacao": linha["Data"],
            "valor_aplicado": linha["Valor aplicado"],
            "evolucao": evolucao
        })

    return aplicacoes

def consolidar_carteira(aplicacao_inicial, aplicacoes_recorrentes):
    """
    Consolida os saldos de várias aplicações independentes.

    A carteira não recalcula rendimentos.
    Apenas soma os saldos existentes em cada data.

    Parâmetros:
        aplicacao_inicial (dict): aplicação inicial criada
            por criar_aplicacao().

        aplicacoes_recorrentes (list): lista de aplicações
            criada por simular_aplicacoes_recorrentes().

    Retorna:
        pandas.DataFrame contendo:
            Data
            Montante da carteira
    """

    registros = []

    # -----------------------------------------------------
    # APLICAÇÃO INICIAL
    # -----------------------------------------------------

    data_inicial = pd.to_datetime(
        aplicacao_inicial["data_aplicacao"],
        dayfirst=True
    )

    registros.append({
        "Data": data_inicial,
        "Montante": aplicacao_inicial["valor_aplicado"]
    })

    for _, linha in aplicacao_inicial["evolucao"].iterrows():

        registros.append({
            "Data": linha["Data"],
            "Montante": linha["Saldo"]
        })

    # -----------------------------------------------------
    # APLICAÇÕES RECORRENTES
    # -----------------------------------------------------

    for aplicacao in aplicacoes_recorrentes:

        data_aplicacao = pd.to_datetime(
            aplicacao["data_aplicacao"]
        )

        valor_aplicado = aplicacao["valor_aplicado"]

        # No dia da aplicação:
        # o valor já pertence à carteira,
        # mas ainda não possui rendimento.

        registros.append({
            "Data": data_aplicacao,
            "Montante": valor_aplicado
        })

        # Evolução posterior da aplicação
        for _, linha in aplicacao["evolucao"].iterrows():

            registros.append({
                "Data": linha["Data"],
                "Montante": linha["Saldo"]
            })

    df = pd.DataFrame(registros)

    # Somamos os saldos de todas as aplicações
    # existentes na mesma data.
    df = (
        df.groupby("Data", as_index=False)["Montante"]
        .sum()
        .sort_values("Data")
        .reset_index(drop=True)
    )

    return df

def calcular_retirada(valor_retirada, aliquota_ir):
    """
    Calcula o IR e o valor líquido de uma retirada.

    Parâmetros:
        valor_retirada: valor bruto retirado da carteira.
        aliquota_ir: alíquota do IR em formato decimal.

    Retorna:
        valor_retirada: valor que sai da carteira.
        imposto: valor destinado ao IR.
        valor_liquido: valor recebido pelo usuário.
    """

    imposto = valor_retirada * aliquota_ir
    valor_liquido = valor_retirada - imposto

    return valor_retirada, imposto, valor_liquido

def aplicar_retirada_ao_saldo(saldo, valor_retirada):
    """
    Aplica uma retirada ao saldo da carteira.

    A retirada ocorre após o fechamento do período
    de rendimento.

    Retorna o saldo disponível para o próximo período.
    """

    saldo_final = saldo - valor_retirada

    return saldo_final

def calcular_taxa_ofertada(cdi_anual, percentual_cdi):
    taxa_anual = cdi_anual * (percentual_cdi / 100)
    return taxa_anual

def distribuir_aplicacao(
    valor_total,
    limite_taxa,
    percentual_taxa_prometida,
    percentual_taxa_excedente
):
    valor_faixa_promocional = min(
        valor_total,
        limite_taxa
    )

    valor_faixa_excedente = max(
        valor_total - limite_taxa,
        0
    )

    return {
        "faixa_promocional": {
            "valor": valor_faixa_promocional,
            "percentual_cdi": percentual_taxa_prometida
        },
        "faixa_excedente": {
            "valor": valor_faixa_excedente,
            "percentual_cdi": percentual_taxa_excedente
        }
    }

def simular_aplicacao_com_faixas(
    valor_total,
    limite_taxa,
    percentual_taxa_prometida,
    percentual_taxa_excedente,
    cdi_anual,
    quantidade_meses,
    data_aplicacao
):
    faixas = distribuir_aplicacao(
        valor_total=valor_total,
        limite_taxa=limite_taxa,
        percentual_taxa_prometida=percentual_taxa_prometida,
        percentual_taxa_excedente=percentual_taxa_excedente
    )

    taxa_promocional = calcular_taxa_ofertada(
        cdi_anual,
        percentual_taxa_prometida
    )

    taxa_excedente = calcular_taxa_ofertada(
        cdi_anual,
        percentual_taxa_excedente
    )

    simulacao_promocional = criar_aplicacao(
        valor=faixas["faixa_promocional"]["valor"],
        taxa_anual=taxa_promocional / 100,
        quantidade_meses=quantidade_meses,
        data_aplicacao=data_aplicacao
    )

    simulacao_excedente = criar_aplicacao(
        valor=faixas["faixa_excedente"]["valor"],
        taxa_anual=taxa_excedente / 100,
        quantidade_meses=quantidade_meses,
        data_aplicacao=data_aplicacao
    )

    return {
        "faixa_promocional": simulacao_promocional,
        "faixa_excedente": simulacao_excedente
    }

def consolidar_simulacao_faixas(simulacao_faixas):

    promocional = simulacao_faixas["faixa_promocional"]
    excedente = simulacao_faixas["faixa_excedente"]

    consolidado = promocional.copy()

    consolidado["Capital inicial"] = (
        promocional["Capital inicial"]
        + excedente["Capital inicial"]
    )

    consolidado["Rendimento"] = (
        promocional["Rendimento"]
        + excedente["Rendimento"]
    )

    consolidado["Saldo"] = (
        promocional["Saldo"]
        + excedente["Saldo"]
    )

    return consolidado