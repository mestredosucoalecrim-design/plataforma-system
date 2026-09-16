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
        

def calcular_radar_sobrevivencia_real(id_usuario_logado: str, data_inicio) -> dict:
    """
    Motor matemático traduzido diretamente do UserForm_Initialize do VBA.
    Garante sincronia perfeita com os filtros e fórmulas do Excel.
    """
    try:
        supabase = mod_conexao.criar_conexao()
        hoje = datetime.now().date()
        
        # Converte a data inicial recebida da tela
        dt_ultimo = datetime.strptime(data_inicio, "%Y-%m-%d").date() if isinstance(data_inicio, str) else data_inicio
        
        # --- PARTE 1: CÁLCULOS DE DATAS (IGUAL AO VBA) ---
        dt_proximo = dt_ultimo + relativedelta(days=30)
        
        dias_passados = (hoje - dt_ultimo).days - 1
        dias_faltam = (dt_proximo - hoje).days + 1
        
        if dias_passados <= 0: 
            dias_passados = 1
            
        # --- PARTE 2: BUSCA E FILTROS DO SUPABASE ---
        # Trazemos os lançamentos do usuário para fazer o SumIfs do Excel usando o Pandas
        resposta = supabase.table("lancamentos").select("valor, created_at, banco").eq("usuario_id", id_usuario_logado).execute()
        
        if not resposta.data:
            return None
            
        df = pd.DataFrame(resposta.data)
        # Limpa e formata as colunas para o filtro
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.date
        df["valor"] = pd.to_numeric(df["valor"])
        df["banco"] = df["banco"].str.strip().str.lower()
        
        # 1. Realidade Hoje (SumIfs do VBA: Conta == 'nu bank' e Data <= Hoje)
        df_realidade = df[(df["banco"] == "nu bank") & (df["created_at"] <= hoje)]
        realidade_hoje = float(df_realidade["valor"].sum())
        
        # 2. Valor Base H24 (Buscamos o recebimento de R$ 580.00 feito no dia inicial)
        df_h24 = df[(df["created_at"] == dt_ultimo) & (df["valor"] > 0)]
        valor_h24 = float(df_h24["valor"].sum()) if not df_h24.empty else 580.00
        if valor_h24 == 0: 
            valor_h24 = 580.00
            
        # 3. Média Necessária (Valor H24 / 30 cravado)
        media_necessaria = valor_h24 / 30
        
        # 4. Total Gastos Período (SumIfs do VBA: Data >= Ultimo+1 e Data <= Hoje e Valor < 0)
        dia_seguinte = dt_ultimo + relativedelta(days=1)
        df_gastos = df[(df["created_at"] >= dia_seguinte) & (df["created_at"] <= hoje) & (df["valor"] < 0)]
        total_gastos_periodo = float(df_gastos["valor"].sum()) # Já virá negativo do banco
        
        # 5. Média Hoje
        media_hoje = total_gastos_periodo / dias_passados
        
        # 6. Perspectiva Hoje
        perspectiva_hoje = valor_h24 - (media_necessaria * dias_passados)
        
        # 7. Vou Gastar = Média Hoje * Dias Faltam
        vou_gastar = media_hoje * dias_faltam
        
        # 8. Gastarei a mais = Realidade Hoje + Vou Gastar (Como vou_gastar é negativo, a soma reduz o saldo)
        gastarei_a_mais = realidade_hoje + vou_gastar
        
        # 9. Posso Até
        posso_ate = realidade_hoje / dias_faltam if dias_faltam > 0 else 0.0
        
        return {
            "posso_ate": round(posso_ate, 2),
            "media_necessaria": round(media_necessaria, 2),
            "media_hoje": round(abs(media_hoje), 2), # Passamos positivo para a tela ficar bonita
            "vou_gastar": round(abs(vou_gastar), 2),
            "gastarei_a_mais": round(gastarei_a_mais, 2),
            "dias_passados": int(dias_passados),
            "dias_faltam": int(dias_faltam),
            "perspectiva_hoje": round(perspectiva_hoje, 2),
            "realidade_hoje": round(realidade_hoje, 2),
            "ultimo_recebimento": dt_ultimo.strftime("%d/%m/%Y"),
            "proximo_recebimento": dt_proximo.strftime("%d/%m/%Y")
        }
    except Exception as e:
        print(f"❌ Erro no motor calibrado VBA: {e}")
        return None