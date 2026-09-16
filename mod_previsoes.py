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
        

def calcular_radar_sobrevivencia_real(id_usuario_logado: str, saldo_atual: float, data_inicio, data_fim) -> dict:
    """
    Motor financeiro dinâmico adaptado para ciclos de recebimentos variáveis (aluguéis/aposentadoria).
    Recebe as datas escolhidas pelo usuário na tela.
    """
    try:
        supabase = mod_conexao.criar_conexao()
        hoje = datetime.now().date()
        
        # Converte as datas recebidas da tela para o formato correto do Python, se necessário
        dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date() if isinstance(data_inicio, str) else data_inicio
        dt_fim = datetime.strptime(data_fim, "%Y-%m-%d").date() if isinstance(data_fim, str) else data_fim
        
        # 1. Cálculos de Ciclo Baseados nas Caixas de Entrada (Sua engenharia)
        total_dias_ciclo = (dt_fim - dt_inicio).days
        dias_passados = (hoje - dt_inicio).days
        
        # Segurança para o motor não calcular dias negativos ou zerados se o usuário mexer na tela
        total_dias_ciclo = max(total_dias_ciclo, 1)
        dias_passados = max(dias_passados, 1)
        dias_restantes = max(total_dias_ciclo - dias_passados, 1)
        
        # 2. Busca no Supabase os gastos do ciclo dinâmico escolhido
        resposta_gastos = supabase.table("lancamentos")\
            .select("valor")\
            .eq("usuario_id", id_usuario_logado)\
            .gte("created_at", dt_inicio.strftime("%Y-%m-%d"))\
            .lte("created_at", hoje.strftime("%Y-%m-%d"))\
            .execute()
            
        # 3. Calcula o total gasto usando a sua lógica matemática
        total_gasto_passado = 0.0
        if resposta_gastos.data:
            total_gasto_passado = sum(abs(float(item["valor"])) for item in resposta_gastos.data if float(item["valor"]) < 0)
            
        # 4. Reconstrói o Saldo do Dia 1 (Quando o ciclo começou na data escolhida)
        saldo_disponivel_dia_um = saldo_atual + total_gasto_passado
        
        # 5. Média Necessária Fixa (Teto inicial permitido por dia)
        media_necessaria = saldo_disponivel_dia_um / total_dias_ciclo
        
        # 6. Média Real (Velocidade de consumo real desde o início do ciclo)
        media_real = total_gasto_passado / dias_passados
        
        # 7. Gasto Futuro Projetado baseado na velocidade real
        gasto_futuro_estimado = media_real * dias_restantes
        
        # 8. Quanto PODE gastar por dia de hoje em diante (Ajuste de Rota do GPS)
        quanto_pode_gastar_hoje = saldo_atual / dias_restantes
        
        # Lógica da Defasagem Financeira (O Rombo)
        rombo_estimado = gasto_futuro_estimado - saldo_atual
        
        return {
            "total_dias_ciclo": total_dias_ciclo,
            "dias_passados": dias_passados,
            "dias_restantes": dias_restantes,
            "media_necessaria": round(media_necessaria, 2),
            "media_real": round(media_real, 2),
            "quanto_pode_gastar_hoje": round(quanto_pode_gastar_hoje, 2),
            "rombo_estimado": round(rombo_estimado, 2) if rombo_estimado > 0 else 0.0,
            "saldo_disponivel_dia_um": round(saldo_disponivel_dia_um, 2)
        }
    except Exception as e:
        print(f"❌ Erro na calibração do motor dinâmico: {e}")
        return None
