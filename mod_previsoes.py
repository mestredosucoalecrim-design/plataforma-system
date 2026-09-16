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
    Calcula a autonomia real do William baseado no saldo atualizado 
    e no ritmo de despesas diárias desde o dia seguinte ao último recebimento.
    """
    try:
        from datetime import datetime, timedelta
        supabase = mod_conexao.criar_conexao()
        
        # 1. Alinha as datas do calendário
        dt_ultimo = datetime.strptime(str(data_ultimo_rec), "%Y-%m-%d").date() if isinstance(data_ultimo_rec, str) else data_ultimo_rec
        dt_proximo = datetime.strptime(str(data_proximo_rec), "%Y-%m-%d").date() if isinstance(data_proximo_rec, str) else data_proximo_rec
        dt_hoje = datetime.now().date()
        
        # O gasto real começa um dia APÓS o recebimento (Dia 12/09)
        dt_inicio_gasto = dt_ultimo + timedelta(days=1)
        
        # 2. Janela do Ciclo Total e Dias Passados/Restantes
        total_dias_ciclo = (dt_proximo - dt_ultimo).days
        if total_dias_ciclo <= 0: total_dias_ciclo = 30
        
        dias_passados = (dt_hoje - dt_ultimo).days
        if dias_passados <= 0: dias_passados = 1
        
        dias_restantes = (dt_proximo - dt_hoje).days
        if dias_restantes < 0: dias_restantes = 0
        
        # 3. Média Necessária (Saldo histórico do dia do recebimento / total de dias do ciclo)
        # Para descobrir o saldo que você tinha no dia do recebimento, somamos o saldo atual + o que foi gasto depois
        resposta_gastos = supabase.table("lancamentos")\
            .select("valor, created_at")\
            .eq("usuario_id", id_usuario_logado)\
            .lt("valor", 0)\
            .execute()
            
        total_gasto_desde_dia_seguinte = 0.0
        if resposta_gastos.data:
            for item in resposta_gastos.data:
                data_lancado_curta = item["created_at"][:10]
                # Soma tudo o que saiu a partir do dia seguinte (12/09) até hoje
                if dt_inicio_gasto.strftime("%Y-%m-%d") <= data_lancado_curta <= dt_hoje.strftime("%Y-%m-%d"):
                    total_gasto_desde_dia_seguinte += abs(float(item["valor"]))
                    
        saldo_no_dia_recebimento = saldo_atual + total_gasto_desde_dia_seguinte
        media_necessaria = saldo_no_dia_recebimento / total_dias_ciclo
        
        # 4. Média Real (Quanto gastou de verdade por dia desde o dia seguinte)
        media_real = total_gasto_desde_dia_seguinte / dias_passados if dias_passados > 0 else 0.0
        
        # 5. Quanto PODE gastar por dia a partir de hoje
        quanto_pode_gastar_hoje = saldo_atual / dias_restantes if dias_restantes > 0 else 0.0
        
        # 6. Cálculo exato de quantos dias o dinheiro vai durar se continuar na média real
        if media_real > 0:
            dias_duracao_estimada = saldo_atual / media_real
            dias_deficit = dias_restantes - dias_duracao_estimada
        else:
            dias_duracao_estimada = dias_restantes
            dias_deficit = 0.0
            
        return {
            "dias_passados": dias_passados,
            "dias_restantes": dias_restantes,
            "media_necessaria": media_necessaria,
            "media_real": media_real,
            "quanto_pode_gastar_hoje": quanto_pode_gastar_hoje,
            "dias_deficit": round(dias_deficit, 1) if dias_deficit > 0 else 0
        }
    except Exception as e:
        print(f"❌ Erro na calibração do motor: {e}")
        return None
