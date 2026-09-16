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
        

def buscar_detalhe_compromissos_abertos(id_usuario_logado: str) -> list:
    """Busca cirúrgica na tabela orcamento_previsto para diagnosticar o retorno baleado."""
    try:
        supabase = mod_conexao.criar_conexao()
        
        # Busca direta, sem filtros, para testar a comunicação crua com a tabela
        resposta = supabase.table("orcamento_previsto").select("*").execute()
        
        # Se a resposta contiver dados, retorna a lista
        if hasattr(resposta, 'data') and resposta.data:
            return resposta.data
            
        # Tratamento alternativo caso o objeto venha em formato de dicionário puro
        if isinstance(resposta, dict) and "data" in resposta:
            return resposta["data"]
            
        return []
    except Exception as e:
        # Se o banco rejeitar por qualquer motivo estrutural, o Python vai cuspir o erro aqui
        return [{"ERRO_CRITICO": str(e)}]


def calcular_autonomia_caixa_real(id_usuario_logado: str, data_ultimo_rec, data_proximo_rec, saldo_atual: float) -> dict:
    """
    Calcula a autonomia e o rombo de caixa baseado estritamente na regra de 
    saldo inicial livre do William (Média Necessária fixa vs Média Real diária).
    """
    try:
        from datetime import datetime, timedelta
        supabase = mod_conexao.criar_conexao()
        
        # 1. Alinha as datas do calendário
        dt_ultimo = datetime.strptime(str(data_ultimo_rec), "%Y-%m-%d").date() if isinstance(data_ultimo_rec, str) else data_ultimo_rec
        dt_proximo = datetime.strptime(str(data_proximo_rec), "%Y-%m-%d").date() if isinstance(data_proximo_rec, str) else data_proximo_rec
        dt_hoje = datetime.now().date()
        
        # O ciclo de gastos começa rigorosamente no Dia 1 (um dia após o recebimento)
        dt_dia_um = dt_ultimo + timedelta(days=1)
        
        # 2. Dias do Ciclo
        total_dias_ciclo = (dt_proximo - dt_ultimo).days
        if total_dias_ciclo <= 0: total_dias_ciclo = 30
        
        dias_passados = (dt_hoje - dt_ultimo).days
        if dias_passados <= 0: dias_passados = 1
        
        dias_restantes = (dt_proximo - dt_hoje).days
        if dias_restantes < 0: dias_restantes = 0
        
        # 3. Busca de despesas reais feitas exclusivamente DESDE o Dia 1 (dia seguinte ao recebimento) até hoje
        resposta_gastos = supabase.table("lancamentos")\
            .select("valor, created_at")\
            .eq("usuario_id", id_usuario_logado)\
            .lt("valor", 0)\
            .gte("created_at", dt_dia_um.strftime("%Y-%m-%dT00:00:00+00:00"))\
            .lte("created_at", dt_hoje.strftime("%Y-%m-%dT23:59:59+00:00"))\
            .execute()
            
        total_gasto_passado = 0.0
        if resposta_gastos.data:
            total_gasto_passado = sum(abs(float(item["valor"])) for item in resposta_gastos.data)
            
        # 4. Reconstrói o Saldo do Dia 1 (Saldo que ela tinha na manhã do dia 12)
        saldo_disponivel_dia_um = saldo_atual + total_gasto_passado
        
        # 5. Média Necessária Fixa (Saldo do Dia 1 dividido pelo ciclo total de 30 dias)
        media_necessaria = saldo_disponivel_dia_um / total_dias_ciclo if total_dias_ciclo > 0 else 0.0
        
        # 6. Média Real (Quanto ela vem gastando de verdade por dia desde o dia 12)
        media_real = total_gasto_passado / dias_passados if dias_passados > 0 else 0.0
        
        # 7. Gasto Futuro Projetado baseado na velocidade real
        gasto_futuro_estimado = media_real * dias_restantes
        
        # 8. Quanto ela PODE gastar por dia de hoje em diante para não quebrar (Saldo atual / dias restantes)
        quanto_pode_gastar_hoje = saldo_atual / dias_restantes if dias_restantes > 0 else 0.0
        
        # Lógica do Defasagem Financeira (O Puxão de Orelha)
        # Se o que ela vai gastar no futuro (gasto_futuro) for maior do que ela tem no bolso hoje (saldo_atual)
        rombo_estimado = gasto_futuro_estimado - saldo_atual
        
        return {
            "dias_restantes": dias_restantes,
            "media_necessaria": media_necessaria,
            "media_real": media_real,
            "quanto_pode_gastar_hoje": quanto_pode_gastar_hoje,
            "rombo_estimado": round(rombo_estimado, 2) if rombo_estimado > 0 else 0.0,
            "saldo_disponivel_dia_um": saldo_disponivel_dia_um
        }
    except Exception as e:
        print(f"❌ Erro na calibração do motor: {e}")
        return None
