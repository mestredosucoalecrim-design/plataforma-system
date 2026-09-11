import pandas as pd
import streamlit as st  # Importamos o streamlit para usar o cache
import mod_conexao

@st.cache_data(ttl=3600)  # 🧠 O MÁGICO DO CACHE: Guarda os dados na memória por 1 hora
def buscar_todos_lancamentos_completos(id_usuario_logado: str) -> pd.DataFrame:
    """
    Busca os registros do Supabase filtrando pelo ID do usuário ativo.
    Garante estrutura correta de colunas mesmo para usuários novos com zero dados.
    """
    try:
        supabase = mod_conexao.criar_conexao()
        todos_dados = []
        limite_lote = 1000
        inicio = 0
        
        while True:
            resposta = supabase.table("lancamentos")\
                .select("*")\
                .eq("usuario_id", id_usuario_logado)\
                .range(inicio, inicio + limite_lote - 1)\
                .execute()
                
            registros_trazidos = resposta.data
            todos_dados.extend(registros_trazidos)
            
            if len(registros_trazidos) < limite_lote:
                break
            inicio += limite_lote
            
        df = pd.DataFrame(todos_dados)
        
        # 🛡️ BLINDAGEM MÁXIMA: Se o usuário for novo e o DataFrame estiver vazio, estruturamos as colunas
        if df.empty:
            df = pd.DataFrame(columns=['id', 'created_at', 'banco', 'categoria', 'nome_produto', 'valor', 'usuario_id'])
            df['created_at'] = pd.to_datetime(df['created_at']) # Força o tipo Datetime no Pandas!
            df['valor'] = pd.to_numeric(df['valor'])
            return df
            
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.00)
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
            
        return df
    except Exception as e:
        print(f"❌ Erro ao buscar dados protegidos no mod_calculos: {e}")
        # Retorna estrutura segura em caso de falha crítica
        df_erro = pd.DataFrame(columns=['id', 'created_at', 'banco', 'categoria', 'nome_produto', 'valor', 'usuario_id'])
        df_erro['created_at'] = pd.to_datetime(df_erro['created_at'])
        return df_erro

def calcular_resumo_memoria(df: pd.DataFrame) -> dict:
    """Calcula os totais do topo direto da memória, sem ir na nuvem de novo."""
    if df.empty or 'valor' not in df.columns:
        return {"saldo_total": 0.00, "total_receitas": 0.00, "total_despesas": 0.00}
    total_receitas = df[df['valor'] > 0]['valor'].sum()
    total_despesas = df[df['valor'] < 0]['valor'].sum()
    saldo_total = df['valor'].sum()
    return {"saldo_total": float(saldo_total), "total_receitas": float(total_receitas), "total_despesas": float(total_despesas)}

def filtrar_extrato_memoria(df: pd.DataFrame, mes: int, ano: int, banco: str) -> pd.DataFrame:
    """Filtra o DataFrame direto da memória por mês, ano e banco, tratando tabelas vazias de novos usuários."""
    # 🛡️ TRAVA CIRÚRGICA: Se o usuário não tiver dados cadastrados, retorna vazio sem quebrar!
    if df.empty or 'created_at' not in df.columns:
        return pd.DataFrame()
        
    filtro = (df['created_at'].dt.year == ano) & (df['created_at'].dt.month == mes)
    df_filtrado = df[filtro]
    
    if banco != "-- Selecione um Banco --" and not df_filtrado.empty:
        df_filtrado = df_filtrado[df_filtrado['banco'] == banco]
        
    if not df_filtrado.empty:
        df_filtrado = df_filtrado.sort_values(by='created_at', ascending=False)
        
    return df_filtrado

def calcular_saldo_historico_memoria(df: pd.DataFrame, mes: int, ano: int, banco: str) -> float:
    """Calcula o saldo histórico progressivo do banco direto da memória com trava de segurança para usuários novos."""
    # 🛡️ TRAVA CIRÚRGICA: Se a base estiver vazia, o saldo dele é R$ 0,00 puro
    if df.empty or 'valor' not in df.columns or 'created_at' not in df.columns:
        return 0.00
        
    proximo_mes = mes + 1 if mes < 12 else 1
    proximo_ano = ano if mes < 12 else ano + 1
    data_limite = pd.Timestamp(f"{proximo_ano}-{proximo_mes}-01").tz_localize('UTC')
    
    df_historico = df[df['created_at'] < data_limite]
    
    if banco != "-- Selecione um Banco --" and not df_historico.empty:
        df_historico = df_historico[df_historico['banco'] == banco]
        
    return float(df_historico['valor'].sum())

def obter_despesas_por_categoria_memoria(df_mes: pd.DataFrame) -> pd.DataFrame:
    """Agrupa as despesas do mês por categoria direto da memória."""
    if df_mes.empty or 'valor' not in df_mes.columns:
        return pd.DataFrame()
    df_despesas = df_mes[df_mes['valor'] < 0].copy()
    if df_despesas.empty:
        return pd.DataFrame()
    df_despesas['valor'] = df_despesas['valor'].abs()
    resumo_cat = df_despesas.groupby('categoria')['valor'].sum().reset_index()
    return resumo_cat.sort_values(by='valor', ascending=False)

def atualizar_lancamento_banco(id_lancamento: int, dados_atualizados: dict) -> bool:
    """Atualiza a linha no Supabase e roda o PROCV automático da categoria."""
    try:
        supabase = mod_conexao.criar_conexao()
        if "nome_produto" in dados_atualizados:
            prod_limpo = dados_atualizados["nome_produto"].strip().lower()
            dados_atualizados["nome_produto"] = prod_limpo
            resposta_cat = supabase.table("produtos").select("categoria").eq("nome_produto", prod_limpo).execute()
            if resposta_cat.data:
                dados_atualizados["categoria"] = resposta_cat.data[0]['categoria']
        if "banco" in dados_atualizados:
            dados_atualizados["banco"] = dados_atualizados["banco"].strip().lower()
        supabase.table("lancamentos").update(dados_atualizados).eq("id", id_lancamento).execute()
        st.cache_data.clear() # 🔥 Limpa a memória para o app ler o dado novo editado
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar lançamento: {e}")
        return False

def deletar_lancamento_banco(id_lancamento: int) -> bool:
    """Remove um registro do Supabase usando o ID."""
    try:
        supabase = mod_conexao.criar_conexao()
        supabase.table("lancamentos").delete().eq("id", id_lancamento).execute()
        st.cache_data.clear() # 🔥 Limpa a memória para o app ler o dado novo editado
        return True
    except Exception as e:
        print(f"❌ Erro ao deletar: {e}")
        return False

def registrar_movimentacao_banco(banco: str, nome_produto: str, valor: float, tipo: str, data_lancamento, id_usuario_logado: str) -> bool:
    """Grava o novo lançamento na tabela mãe assinando digitalmente com o ID do usuário logado."""
    try:
        supabase = mod_conexao.criar_conexao()
        prod_limpo = nome_produto.strip().lower()
        
        resposta_prod = supabase.table("produtos").select("categoria_id").eq("nome_produto", prod_limpo).execute()
        
        categoria_nome = "Não Informado"
        if resposta_prod.data and len(resposta_prod.data) > 0:
            id_categoria = resposta_prod.data[0]["categoria_id"]
            resposta_cat = supabase.table("categoria").select("categoria").eq("id", id_categoria).execute()
            if resposta_cat.data and len(resposta_cat.data) > 0:
                categoria_nome = resposta_cat.data[0]["categoria"]
        
        valor_final = -abs(valor) if tipo == "Despesa (Saída)" else abs(valor)
        
        # 🛡️ CARIMBO DIGITAL: Injetamos o id_usuario_logado na coluna usuario_id!
        dados_lancamento = {
            "created_at": str(data_lancamento),
            "banco": banco.strip().lower(),
            "categoria": categoria_nome,
            "nome_produto": prod_limpo,
            "valor": valor_final,
            "usuario_id": id_usuario_logado  # <-- Garante a propriedade da linha
        }
        
        supabase.table("lancamentos").insert(dados_lancamento).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        print(f"❌ Erro ao gravar lançamento relacional: {e}")
        return False


def obter_evolucao_mensal_faturamento(df: pd.DataFrame, banco: str) -> pd.DataFrame:
    """
    Agrupa o histórico de lançamentos por mês/ano, filtrando pelo banco selecionado.
    Garante que o gráfico de barras horizontais obedeça à escolha do usuário.
    """
    if df.empty or 'valor' not in df.columns or 'created_at' not in df.columns:
        return pd.DataFrame()
        
    df_temp = df.copy()
    
    # 🛡️ FILTRO CIRÚRGICO DO BANCO SELECIONADO (Sua observação de ouro!)
    if banco != "-- Selecione um Banco --":
        df_temp = df_temp[df_temp['banco'] == banco]
        
    if df_temp.empty:
        return pd.DataFrame()
    
    # Cria as colunas auxiliares de Ano e Mês
    df_temp['Ano'] = df_temp['created_at'].dt.year
    df_temp['Mês_Num'] = df_temp['created_at'].dt.month
    
    nome_meses_abrev = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    df_temp['Mês'] = df_temp['Mês_Num'].apply(lambda x: nome_meses_abrev[x]) + "/" + df_temp['Ano'].astype(str)
    
    df_temp['Receitas'] = df_temp['valor'].apply(lambda x: x if x > 0 else 0.0)
    df_temp['Despesas'] = df_temp['valor'].apply(lambda x: abs(x) if x < 0 else 0.0)
    
    df_agrupado = df_temp.groupby(['Ano', 'Mês_Num', 'Mês'])[['Receitas', 'Despesas']].sum().reset_index()
    df_agrupado = df_agrupado.sort_values(by=['Ano', 'Mês_Num']).tail(6)
    
    return df_agrupado
def obter_maiores_produtos_mes_memoria(df_mes: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra as despesas do mês e agrupa pelos 5 produtos/itens mais caros,
    preparando os dados para o ranking horizontal.
    """
    if df_mes.empty or 'valor' not in df_mes.columns or 'nome_produto' not in df_mes.columns:
        return pd.DataFrame()
        
    # Filtra apenas o que é despesa (menor que zero)
    df_despesas = df_mes[df_mes['valor'] < 0].copy()
    
    if df_despesas.empty:
        return pd.DataFrame()
        
    # Inverte o sinal para positivo para a barra crescer para a direita de forma natural
    df_despesas['valor'] = df_despesas['valor'].abs()
    
    # Agrupa por produto e soma os totais
    resumo_prod = df_despesas.groupby('nome_produto')['valor'].sum().reset_index()
    
    # Ordena do maior gasto para o menor e pega apenas os 5 "campeões" de custo
    return resumo_prod.sort_values(by='valor', ascending=False).head(5)
def realizar_login_real_supabase(email_usuario: str, senha_usuario: str) -> dict:
    """
    Valida as credenciais do usuário diretamente na nuvem do Supabase.
    Retorna um dicionário indicando o status e o ID único (UUID) se tiver sucesso.
    """
    try:
        supabase = mod_conexao.criar_conexao()
        
        # Comando atômico de autenticação oficial do Supabase
        resposta = supabase.auth.sign_in_with_password({
            "email": email_usuario.strip(),
            "password": senha_usuario
        })
        
        # Se a nuvem autenticou com sucesso, captura o ID único do usuário (UUID)
        if resposta.user:
            return {
                "status": "sucesso",
                "usuario_id": resposta.user.id,
                "email": resposta.user.email
            }
        return {"status": "erro", "mensagem": "Credenciais inválidas."}
        
    except Exception as e:
        # Captura erros comuns como senha errada ou usuário inexistente
        erro_texto = str(e)
        if "Invalid login credentials" in erro_texto:
            return {"status": "erro", "mensagem": "⚠️ E-mail ou Senha incorretos!"}
        return {"status": "erro", "mensagem": f"❌ Falha de comunicação com o servidor: {erro_texto}"}

