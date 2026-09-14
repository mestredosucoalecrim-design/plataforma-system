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

