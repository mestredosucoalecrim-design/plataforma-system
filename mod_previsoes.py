import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import mod_conexao

def gerenciar_salario_usuario(id_usuario_logado: str, novo_salario: float) -> bool:
    """Insere ou atualiza (UPSERT) o salário fixo do usuário no banco."""
    try:
        supabase = mod_conexao.criar_conexao()
        
        supabase.table("usuario_config").upsert({
            "usuario_id": id_usuario_logado,
            "salario_bruto": float(novo_salario)
        }).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao gerenciar salário: {e}")
        return False

def buscar_salario_usuario(id_usuario_logado: str) -> float:
    """Busca o salário cadastrado do usuário. Se não houver, retorna 0.00."""
    try:
        supabase = mod_conexao.criar_conexao()
        resposta = supabase.table("usuario_config").select("salario_bruto").eq("usuario_id", id_usuario_logado).execute()
        
        if resposta.data and len(resposta.data) > 0:
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

def dar_baixa_parcela_futura(id_parcela: int, id_usuario_logado: str) -> bool:
    """
    Remove a parcela do orçamento previsto e insere automaticamente
    como um lançamento real na tabela public.lancamentos.
    """
    try:
        supabase = mod_conexao.criar_conexao()
        
        # 1. Busca os dados da parcela que vai sofrer a baixa
        resposta = supabase.table("orcamento_previsto")\
            .select("*")\
            .eq("id", id_parcela)\
            .eq("usuario_id", id_usuario_logado)\
            .execute()
            
        if not resposta.data:
            return False
            
        parcela = resposta.data[0]
        
        # 2. Prepara o esqueleto do lançamento real para o passado
        # Formatamos a descrição para indicar o controle da parcela (ex: guarda-roupa (parc 1/10))
        descricao_final = f"{parcela['descricao_item']} (parc {parcela['parcela_atual']}/{parcela['total_parcelas']})"
        
        # Como é uma despesa simulada no orçamento, injetamos como valor negativo
        valor_final = -abs(float(parcela["valor_parcela"]))
        
        dados_lancamento = {
            "created_at": f"{parcela['data_vencimento']}T00:00:00+00:00",
            "banco": "nu bank", # Define um banco padrão para a baixa, o usuário pode alterar no extrato depois
            "categoria": parcela["categoria"].strip().lower(),
            "nome_produto": parcela["descricao_item"].strip().lower(),
            "valor": valor_final,
            "usuario_id": id_usuario_logado
        }
        
        # 3. Dispara a gravação no passado (public.lancamentos)
        supabase.table("lancamentos").insert(dados_lancamento).execute()
        
        # 4. Deleta a parcela do futuro (public.orcamento_previsto) para ela sumir do para-brisa
        supabase.table("orcamento_previsto").delete().eq("id", id_parcela).execute()
        
        return True
    except Exception as e:
        print(f"❌ Erro crítico ao dar baixa na parcela: {e}")
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
