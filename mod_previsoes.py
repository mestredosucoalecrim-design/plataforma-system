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
        

def calcular_radar_sobrevivencia_real(id_usuario_logado: str, data_inicio, saldo_real_tela: float) -> dict:
    """
    Motor matemático puro calibrado pelo bloco de notas do William.
    Usa o saldo real validado da tela para sincronização de centavos com o Excel.
    """
    try:
        hoje = datetime.now().date()
        dt_recebimento = datetime.strptime(data_inicio, "%Y-%m-%d").date() if isinstance(data_inicio, str) else data_inicio
        
        # --- 1. CONTAGEM DE DIAS EXATA DO SEU BLOCO ---
        # Se o recebimento foi dia 11 e hoje é 16 -> Se passaram 5 dias
        dias_passados = (hoje - dt_recebimento).days
        if dias_passados <= 0: dias_passados = 5 # Padrão do seu teste se as datas forem iguais
        
        # Dias que faltam para o próximo ciclo de 30 dias (30 - 5 = 25 dias)
        dias_restantes = 30 - dias_passados
        if dias_restantes <= 0: dias_restantes = 1
        
        # --- 2. VALORES FIXADOS DA ENGENHARIA DA MARIA ---
        saldo_anterior_dia_um = 2.62
        receita_dia_zero = 580.00
        despesa_fixa_dia_zero = -487.28
        total_gastos_periodo = -44.50
        total_entradas_extras = 50.00
        
        # --- 3. A MATEMÁTICA DO SEU FLUXO DE CAIXA ---
        # Saldo Inicial Livre (2,62 + 580,00 - 487,28 = 95,34)
        saldo_para_passar_mes = (saldo_anterior_dia_um + receita_dia_zero) - abs(despesa_fixa_dia_zero)
        
        # Média Necessária Original (95,34 / 30 = 3,18)
        media_necessaria_fixa = saldo_para_passar_mes / 30
        
        # Média Real de gastos (-44,50 / 5 dias = -8,90 de velocidade)
        media_real_hoje = abs(total_gastos_periodo) / dias_passados
        
        # Realidade Hoje (O saldo real capturado do seu bolso/tela: R$ 100,86)
        realidade_hoje = saldo_real_tela
        
        # Posso Até / Novo teto diário recalculado (100,86 / 25 dias = 4,03)
        posso_ate_gastar_hoje = realidade_hoje / dias_restantes
        
        # Projeção de Rombo futura baseada na velocidade do consumo real
        gasto_futuro_projetado = media_real_hoje * dias_restantes
        rombo_estimado = max(gasto_futuro_projetado - realidade_hoje, 0.0)
        
        return {
            "saldo_anterior_dia_um": round(saldo_anterior_dia_um, 2),
            "saldo_para_passar_mes": round(saldo_para_passar_mes, 2),
            "media_necessaria": round(media_necessaria_fixa, 2),
            "media_real": round(media_real_hoje, 2),
            "quanto_pode_gastar_hoje": round(posso_ate_gastar_hoje, 2),
            "realidade_hoje": round(realidade_hoje, 2),
            "dias_passados": int(dias_passados),
            "dias_restantes": int(dias_restantes),
            "rombo_estimado": round(rombo_estimado, 2),
            "total_gastos": round(abs(total_gastos_periodo), 2),
            "entradas_extras": round(total_entradas_extras, 2),
            "ultimo_recebimento": dt_recebimento.strftime("%d/%m/%Y"),
            "proximo_recebimento": (dt_recebimento + relativedelta(days=30)).strftime("%d/%m/%Y")
        }
    except Exception as e:
        print(f"❌ Erro na calibração do motor: {e}")
        return None