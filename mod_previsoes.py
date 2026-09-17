import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import mod_conexao

def gerenciar_salario_usuario(id_usuario_logado: str, novo_salario: float) -> bool:
    """Insere ou atualiza (UPSERT) o salário fixo do usuário no banco."""
    try:
        supabase = mod_conexao.criar_conexao()
        
        # Forçamos a limpeza e conversão dos dados para evitar rejeição do banco
        dados = {
            "usuario_id": str(id_usuario_logado).strip(),
            "salario_bruto": float(novo_salario)
        }
        
        # Executa o upsert explícito baseado na chave única usuario_id
        supabase.table("usuario_config").upsert(dados, on_conflict="usuario_id").execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao gerenciar salário: {e}")
        return False

def buscar_salario_usuario(id_usuario_logado: str) -> float:
    """Busca o salário cadastrado do usuário. Se não houver, retorna 0.00."""
    try:
        supabase = mod_conexao.criar_conexao()
        resposta = supabase.table("usuario_config").select("salario_bruto").eq("usuario_id", str(id_usuario_logado).strip()).execute()
        
        if resposta.data and len(resposta.data) > 0:
            # Retorna o valor puro extraído do primeiro registro da lista
            return float(resposta.data[0]["salario_bruto"])
        return 0.00
    except Exception as e:
        print(f"❌ Erro ao buscar salário: {e}")
        return 0.00


def gerar_lancamentos_futuros_parcelados(
    descricao: str, 
    categoria: str, 
    valor_parcela: float, 
    total_parcelas: int, 
    data_primeiro_vencimento, 
    id_usuario_logado: str
) -> bool:
    """
    Roda um loop 'For' estilo VBA, calcula as datas futuras mês a mês
    e insere os registros automáticos na tabela public.orcamento_previsto.
    """
    try:
        supabase = mod_conexao.criar_conexao()
        lista_insercao = []
        
        if isinstance(data_primeiro_vencimento, str):
            data_atual = datetime.strptime(data_primeiro_vencimento, "%Y-%m-%d").date()
        else:
            data_atual = data_primeiro_vencimento

        for parcela in range(1, total_parcelas + 1):
            dados_linha = {
                "usuario_id": id_usuario_logado,
                "descricao_item": descricao.strip().lower(),
                "categoria": categoria.strip().lower(),
                "valor_parcela": float(valor_parcela),
                "parcela_atual": int(parcela),
                "total_parcelas": int(total_parcelas),
                "data_vencimento": data_atual.strftime("%Y-%m-%d"),
                "status": "em aberto"
            }
            lista_insercao.append(dados_linha)
            data_atual = data_atual + relativedelta(months=1)
        
        supabase.table("orcamento_previsto").insert(lista_insercao).execute()
        return True
    except Exception as e:
        print(f"❌ Erro crítico ao gerar parcelamento futuro: {e}")
        return False

def calcular_comprometimento_mensal_futuro(id_usuario_logado: str) -> pd.DataFrame:
    """Busca todas as parcelas 'em aberto' e agrupa os totais por mês/ano."""
    try:
        supabase = mod_conexao.criar_conexao()
        
        # Busca apenas os lançamentos que ainda estão planejados e não foram pagos
        resposta = supabase.table("orcamento_previsto")\
            .select("valor_parcela, data_vencimento")\
            .eq("usuario_id", id_usuario_logado)\
            .eq("status", "em aberto")\
            .execute()
            
        if not resposta.data:
            return pd.DataFrame(columns=["Ano_Mes", "Mês/Ano", "Comprometido"])
            
        df = pd.DataFrame(resposta.data)
        
        # Converte a coluna de data para conseguir extrair o mês e o ano
        df["data_vencimento"] = pd.to_datetime(df["data_vencimento"])
        df["valor_parcela"] = pd.to_numeric(df["valor_parcela"])
        
        # Cria uma coluna formatada para exibição (Ex: 09/2026) e outra para ordenação
        df["Ano_Mes"] = df["data_vencimento"].dt.to_period("M")
        df["Mês/Ano"] = df["data_vencimento"].dt.strftime("%m/%Y")
        
        # Agrupa e soma os valores de todas as parcelas daquele mês
        resumo = df.groupby(["Ano_Mes", "Mês/Ano"])["valor_parcela"].sum().reset_index()
        resumo.columns = ["Ano_Mes", "Mês/Ano", "Comprometido"]
        
        # Ordena cronologicamente para o futuro fazer sentido na tela
        return resumo.sort_values(by="Ano_Mes")
    except Exception as e:
        print(f"❌ Erro ao calcular comprometimento futuro: {e}")
        return pd.DataFrame(columns=["Ano_Mes", "Mês/Ano", "Comprometido"])

def dar_baixa_parcela_futura(id_parcela: int, id_usuario_logado: str, banco_escolhido: str) -> bool:
    """Remove a parcela do orçamento previsto e insere com a data de HOJE no passado."""
    try:
        supabase = mod_conexao.criar_conexao()
        
        # 1. Busca os dados da parcela para saber valor, categoria e descrição
        resposta = supabase.table("orcamento_previsto").select("*").eq("id", id_parcela).eq("usuario_id", id_usuario_logado).execute()
        if not resposta.data:
            return False
            
        parcela = resposta.data[0] # Captura a primeira linha retornada
        descricao_final = f"{parcela['descricao_item']} (parc {parcela['parcela_atual']}/{parcela['total_parcelas']})"
        valor_final = -abs(float(parcela["valor_parcela"]))
        
        # 🟢 A MÁGICA DO CAIXA REAL: Captura a data exata de HOJE (dia do pagamento)
        data_hoje_formatada = datetime.now().strftime("%Y-%m-%d")
        
        dados_lancamento = {
            "created_at": f"{data_hoje_formatada}T00:00:00+00:00", # Carimba com o dia atual do clique
            "banco": banco_escolhido.strip().lower(),
            "categoria": parcela["categoria"].strip().lower(),
            "nome_produto": descricao_final.strip().lower(), # Salva a descrição detalhada com a parcela
            "valor": valor_final,
            "usuario_id": id_usuario_logado
        }
        
        # 2. Grava no passado e deleta do futuro simulado
        supabase.table("lancamentos").insert(dados_lancamento).execute()
        supabase.table("orcamento_previsto").delete().eq("id", id_parcela).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao dar baixa: {e}")
        return False


def excluir_parcela_futura_definitivo(id_parcela: int, id_usuario_logado: str) -> bool:
    """Deleta permanentemente uma projeção do para-brisa sem gerar lançamento real."""
    try:
        supabase = mod_conexao.criar_conexao()
        supabase.table("orcamento_previsto")\
            .delete()\
            .eq("id", id_parcela)\
            .eq("usuario_id", id_usuario_logado)\
            .execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao excluir parcela futura: {e}")
        return False
        



def buscar_detalhe_compromissos_abertos(
    id_usuario_logado: str
) -> list:
    """
    Retorna as projeções futuras em aberto do usuário.

    RESPONSABILIDADE:
        Centralizar a leitura detalhada de orcamento_previsto.
        A interface apenas apresenta os dados.
    """
    try:
        supabase = mod_conexao.criar_conexao()

        resposta = (
            supabase.table("orcamento_previsto")
            .select(
                "id, descricao_item, categoria, valor_parcela, "
                "parcela_atual, total_parcelas, data_vencimento, status"
            )
            .eq("usuario_id", str(id_usuario_logado).strip())
            .eq("status", "em aberto")
            .order("data_vencimento")
            .order("id")
            .execute()
        )

        return resposta.data or []

    except Exception as e:
        print(f"❌ Erro ao buscar compromissos futuros: {e}")
        return []

def calcular_radar_sobrevivencia_real(
    id_usuario_logado: str,
    data_inicio,
    saldo_real_tela: float,
    df_lancamentos: pd.DataFrame
) -> dict:
    """
    Motor do Radar de Sobrevivência.

    RESPONSABILIDADE:
        Interpretar o saldo real e os lançamentos já carregados pelo
        módulo de cálculos. Este módulo NÃO consulta o Supabase para
        recalcular o saldo.

    PRINCÍPIO ARQUITETURAL:
        mod_calculos = fonte dos dados e cálculos básicos.
        mod_previsoes = inteligência preditiva.
        Menu Principal = apresentação.

    COMPATIBILIDADE:
        O parâmetro saldo_real_tela permanece na assinatura porque o
        chamador atual do sistema já trabalha com esse valor. Ele é a
        fonte oficial do saldo atual utilizado pelo Radar.

    REGRAS:
        - valor > 0  : entrada
        - valor < 0  : despesa
        - ciclo       : 30 dias inclusivos
        - dia seguinte ao recebimento inicia a medição do gasto corrente
        - entradas posteriores aumentam o saldo real
        - despesas posteriores reduzem o saldo real
    """

    try:
        if df_lancamentos is None:
            raise ValueError("O DataFrame de lançamentos não foi informado.")

        # ---------------------------------------------------------
        # 1. NORMALIZAÇÃO DA DATA DE INÍCIO
        # ---------------------------------------------------------
        if isinstance(data_inicio, str):
            data_inicio = data_inicio.strip()

            formatos = ("%Y-%m-%d", "%d/%m/%Y")

            dt_recebimento = None
            for formato in formatos:
                try:
                    dt_recebimento = datetime.strptime(
                        data_inicio, formato
                    ).date()
                    break
                except ValueError:
                    continue

            if dt_recebimento is None:
                raise ValueError(
                    "Data de início inválida. Use DD/MM/AAAA ou AAAA-MM-DD."
                )

        elif isinstance(data_inicio, datetime):
            dt_recebimento = data_inicio.date()
        elif hasattr(data_inicio, "year") and hasattr(data_inicio, "month") and hasattr(data_inicio, "day"):
            # Compatível com datetime.date e objetos equivalentes.
            dt_recebimento = data_inicio
        else:
            raise ValueError("Data de início inválida.")

        hoje = datetime.now().date()

        # ---------------------------------------------------------
        # 2. CÓPIA E NORMALIZAÇÃO DOS DADOS
        # ---------------------------------------------------------
        df = df_lancamentos.copy()

        if df.empty:
            df = pd.DataFrame(
                columns=["created_at", "valor", "banco"]
            )

        if "created_at" not in df.columns:
            raise ValueError("O DataFrame não possui a coluna 'created_at'.")

        if "valor" not in df.columns:
            raise ValueError("O DataFrame não possui a coluna 'valor'.")

        df["created_at"] = pd.to_datetime(
            df["created_at"],
            errors="coerce"
        )

        df["valor"] = pd.to_numeric(
            df["valor"],
            errors="coerce"
        ).fillna(0.0)

        df = df.dropna(subset=["created_at"])

        # Trabalhamos com a data civil do lançamento.
        df["data_lancamento"] = df["created_at"].dt.date

        # ---------------------------------------------------------
        # 3. SALDO RECEBIDO DO MOD_CÁLCULOS
        # ---------------------------------------------------------
        saldo_atual_real = float(saldo_real_tela or 0.0)

        # ---------------------------------------------------------
        # 4. CICLO DE 30 DIAS
        #    Ex.: 11/09/2026 -> 10/10/2026
        # ---------------------------------------------------------
        dt_dia_anterior = dt_recebimento - relativedelta(days=1)
        dt_fim_ciclo = dt_recebimento + relativedelta(days=29)
        dt_proximo_recebimento = dt_recebimento + relativedelta(days=30)

        # ---------------------------------------------------------
        # DIAS DO CICLO — REGRA OFICIAL DO RADAR
        #
        # Dia do recebimento = Dia 0.
        # O dia seguinte ao recebimento = Dia 1.
        # O último dia antes do próximo recebimento = Dia 30.
        #
        # Exemplo:
        # Recebimento: 10/09
        # 11/09 = Dia 1
        # 09/10 = Dia 30
        # 10/10 = novo recebimento / novo Dia 0
        # ---------------------------------------------------------
        if hoje < dt_recebimento:
            dias_decorridos_ciclo = 0
        elif hoje <= dt_fim_ciclo:
            dias_decorridos_ciclo = (hoje - dt_recebimento).days
        else:
            dias_decorridos_ciclo = 30

        dias_restantes_ciclo = max(
            30 - dias_decorridos_ciclo,
            0
        )

        # ---------------------------------------------------------
        # 5. BANCO DO RADAR
        #
        # O saldo atual já veio do mod_calculos. Aqui usamos o banco
        # somente para analisar os lançamentos que compõem o ciclo,
        # preservando a lógica específica do Radar.
        # ---------------------------------------------------------
        if "banco" in df.columns:
            df["banco_limpo"] = (
                df["banco"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            # Normalização sem espaços: "nu bank" -> "nubank".
            df["banco_chave"] = (
                df["banco_limpo"]
                .str.replace(" ", "", regex=False)
            )

            df_radar = df[df["banco_chave"] == "nubank"].copy()
        else:
            # Se o DataFrame não trouxer banco, não inventamos filtro.
            # Isso permite que o chamador forneça previamente somente
            # os lançamentos do banco desejado.
            df_radar = df.copy()

        # ---------------------------------------------------------
        # 6. HISTÓRICO ANTERIOR AO RECEBIMENTO
        # ---------------------------------------------------------
        df_historico = df_radar[
            df_radar["data_lancamento"] <= dt_dia_anterior
        ]

        saldo_anterior_dia_um = float(
            df_historico["valor"].sum()
        )

        # ---------------------------------------------------------
        # 7. MOVIMENTAÇÕES NO DIA DO RECEBIMENTO
        # ---------------------------------------------------------
        df_dia_recebimento = df_radar[
            df_radar["data_lancamento"] == dt_recebimento
        ]

        creditos_dia_recebimento = float(
            df_dia_recebimento[
                df_dia_recebimento["valor"] > 0
            ]["valor"].sum()
        )

        debitos_dia_recebimento = float(
            df_dia_recebimento[
                df_dia_recebimento["valor"] < 0
            ]["valor"].sum()
        )

        movimento_dia_recebimento = (
            creditos_dia_recebimento
            + debitos_dia_recebimento
        )

        # Saldo disponível no início do ciclo após os movimentos do
        # próprio dia do recebimento.
        saldo_para_passar_mes = (
            saldo_anterior_dia_um
            + movimento_dia_recebimento
        )

        media_necessaria_original = (
            saldo_para_passar_mes / 30
            if saldo_para_passar_mes > 0
            else 0.0
        )

        # ---------------------------------------------------------
        # 8. MOVIMENTAÇÕES POSTERIORES AO RECEBIMENTO
        # ---------------------------------------------------------
        dia_seguinte = dt_recebimento + relativedelta(days=1)

        if hoje >= dia_seguinte:
            df_periodo = df_radar[
                (df_radar["data_lancamento"] >= dia_seguinte)
                & (df_radar["data_lancamento"] <= hoje)
            ].copy()

            dias_gastos_periodo = (
                hoje - dia_seguinte
            ).days + 1
        else:
            df_periodo = df_radar.iloc[0:0].copy()
            dias_gastos_periodo = 0

        total_gastos_periodo = float(
            df_periodo[
                df_periodo["valor"] < 0
            ]["valor"].sum()
        )

        total_entradas_extras = float(
            df_periodo[
                df_periodo["valor"] > 0
            ]["valor"].sum()
        )

        # ---------------------------------------------------------
        # 9. MÉDIA REAL DE GASTOS
        # ---------------------------------------------------------
        media_real_hoje = (
            abs(total_gastos_periodo) / dias_gastos_periodo
            if dias_gastos_periodo > 0
            else 0.0
        )

        # ---------------------------------------------------------
        # 10. MARGEM DINÂMICA A PARTIR DE HOJE
        # ---------------------------------------------------------
        if dias_restantes_ciclo > 0:
            quanto_pode_gastar_hoje = (
                max(saldo_atual_real, 0.0)
                / dias_restantes_ciclo
            )
        else:
            quanto_pode_gastar_hoje = 0.0

        reducao_necessaria = max(
            media_real_hoje - quanto_pode_gastar_hoje,
            0.0
        )

        excesso_diario = max(
            media_real_hoje - media_necessaria_original,
            0.0
        )

        # ---------------------------------------------------------
        # 11. PROJEÇÃO ATÉ O FIM DO CICLO
        # ---------------------------------------------------------
        gasto_futuro_projetado = (
            media_real_hoje * dias_restantes_ciclo
        )

        rombo_estimado = max(
            gasto_futuro_projetado - max(saldo_atual_real, 0.0),
            0.0
        )

        # ---------------------------------------------------------
        # 12. PROJEÇÃO DE ESGOTAMENTO
        # ---------------------------------------------------------
        if saldo_atual_real <= 0:
            dias_ate_esgotamento = 0.0
            data_esgotamento = hoje

        elif media_real_hoje <= 0:
            dias_ate_esgotamento = None
            data_esgotamento = None

        else:
            dias_ate_esgotamento = (
                saldo_atual_real / media_real_hoje
            )

            # O dinheiro pode ser consumido durante o dia de
            # esgotamento; por isso arredondamos para cima.
            dias_calendario = int(
                dias_ate_esgotamento
            )

            if dias_ate_esgotamento > dias_calendario:
                dias_calendario += 1

            data_esgotamento = (
                hoje + relativedelta(days=dias_calendario)
            )

        # ---------------------------------------------------------
        # 13. SITUAÇÃO DO RADAR
        # ---------------------------------------------------------
        if media_real_hoje > media_necessaria_original:
            situacao = (
                "ATENÇÃO: sua média de gasto extrapolou sua margem."
            )
        elif media_real_hoje == media_necessaria_original:
            situacao = (
                "ATENÇÃO: sua média de gasto atingiu o limite diário."
            )
        else:
            situacao = (
                "Dentro da margem: sua média de gasto está sob controle."
            )

        if dias_restantes_ciclo <= 0:
            situacao_futura = "Ciclo encerrado."

        elif saldo_atual_real <= 0:
            situacao_futura = (
                "ATENÇÃO: o saldo atual está zerado ou negativo."
            )

        elif rombo_estimado > 0:
            situacao_futura = (
                "ATENÇÃO: mantendo a média atual, o saldo "
                "não cobre o restante do ciclo."
            )

        else:
            situacao_futura = (
                "O saldo atual cobre o restante do ciclo "
                "na média de gasto observada."
            )

        # ---------------------------------------------------------
        # 14. RETORNO PADRONIZADO
        # ---------------------------------------------------------
        return {
            # Saldos
            "saldo_anterior_dia_um": round(
                saldo_anterior_dia_um, 2
            ),
            "saldo_para_passar_mes": round(
                saldo_para_passar_mes, 2
            ),
            "saldo_atual_real": round(
                saldo_atual_real, 2
            ),
            "realidade_hoje": round(
                saldo_atual_real, 2
            ),

            # Movimentação do recebimento
            "creditos_dia_recebimento": round(
                creditos_dia_recebimento, 2
            ),
            "debitos_dia_recebimento": round(
                abs(debitos_dia_recebimento), 2
            ),
            "movimento_dia_recebimento": round(
                movimento_dia_recebimento, 2
            ),

            # Movimentação posterior
            "total_gastos": round(
                abs(total_gastos_periodo), 2
            ),
            "entradas_extras": round(
                total_entradas_extras, 2
            ),
            "debitos_periodo": round(
                abs(total_gastos_periodo), 2
            ),
            "creditos_periodo": round(
                total_entradas_extras, 2
            ),

            # Margens
            "media_necessaria": round(
                media_necessaria_original, 2
            ),
            "media_real": round(
                media_real_hoje, 2
            ),
            "quanto_pode_gastar_hoje": round(
                quanto_pode_gastar_hoje, 2
            ),
            "media_necessaria_hoje": round(
                quanto_pode_gastar_hoje, 2
            ),
            "reducao_necessaria": round(
                reducao_necessaria, 2
            ),
            "excesso_diario": round(
                excesso_diario, 2
            ),

            # Tempo
            "dias_decorridos_ciclo": int(
                dias_decorridos_ciclo
            ),
            "dias_passados": int(
                dias_gastos_periodo
            ),
            "dias_gastos_periodo": int(
                dias_gastos_periodo
            ),
            "dias_restantes": int(
                dias_restantes_ciclo
            ),

            # Projeções
            "gasto_futuro_projetado": round(
                gasto_futuro_projetado, 2
            ),
            "rombo_estimado": round(
                rombo_estimado, 2
            ),
            "dias_ate_esgotamento": (
                round(dias_ate_esgotamento, 2)
                if dias_ate_esgotamento is not None
                else None
            ),
            "data_esgotamento": (
                data_esgotamento.strftime("%d/%m/%Y")
                if data_esgotamento is not None
                else None
            ),

            # Datas
            "ultimo_recebimento": dt_recebimento.strftime(
                "%d/%m/%Y"
            ),
            "proximo_recebimento": dt_proximo_recebimento.strftime(
                "%d/%m/%Y"
            ),
            "data_fim_ciclo": dt_fim_ciclo.strftime(
                "%d/%m/%Y"
            ),
            "data_hoje": hoje.strftime(
                "%d/%m/%Y"
            ),

            # Situação
            "situacao": situacao,
            "situacao_futura": situacao_futura,
        }

    except Exception as e:
        print(f"❌ Erro no Radar de Sobrevivência: {e}")
        return None
