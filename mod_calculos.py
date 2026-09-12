import os
import pandas as pd
import streamlit as st
import mod_conexao

def buscar_todos_lancamentos_completos(id_usuario_logado: str) -> pd.DataFrame:
    """Busca os registros do Supabase filtrando pelo ID do usuário ativo."""
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
        
        if df.empty:
            df = pd.DataFrame(columns=['id', 'created_at', 'banco', 'categoria', 'nome_produto', 'valor', 'usuario_id'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['valor'] = pd.to_numeric(df['valor'])
            return df
            
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.00)
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
            
        return df
    except Exception as e:
        print(f"❌ Erro ao buscar dados protegidos: {e}")
        df_erro = pd.DataFrame(columns=['id', 'created_at', 'banco', 'categoria', 'nome_produto', 'valor', 'usuario_id'])
        df_erro['created_at'] = pd.to_datetime(df_erro['created_at'])
        return df_erro

def filtrar_extrato_memoria(df: pd.DataFrame, mes: int, ano: int, banco: str) -> pd.DataFrame:
    """Filtra o DataFrame direto da memória por mês, ano e banco."""
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
    """Calcula o saldo histórico progressivo do banco direto da memória."""
    if df.empty or 'valor' not in df.columns or 'created_at' not in df.columns:
        return 0.00
        
    proximo_mes = mes + 1 if mes < 12 else 1
    proximo_ano = ano if mes < 12 else ano + 1
    data_limite = pd.Timestamp(f"{proximo_ano}-{proximo_mes}-01").tz_localize('UTC')
    
    df_historico = df[df['created_at'] < data_limite]
    
    if banco != "-- Selecione um Banco --" and not df_historico.empty:
        df_historico = df_historico[df_historico['banco'] == banco]
        
    return float(df_historico['valor'].sum())

def calcular_resumo_memoria(df: pd.DataFrame) -> dict:
    """Calcula os totais de receitas e despesas com base no DataFrame da memória."""
    resumo = {"receitas": 0.00, "despesas": 0.00, "saldo": 0.00}
    if df.empty or 'valor' not in df.columns:
        return resumo
        
    resumo["receitas"] = float(df[df['valor'] > 0]['valor'].sum())
    resumo["despesas"] = float(df[df['valor'] < 0]['valor'].sum())
    resumo["saldo"] = resumo["receitas"] + resumo["despesas"]
    return resumo

def obter_maiores_produtos_mes_memoria(df_mes: pd.DataFrame) -> pd.DataFrame:
    """Agrupa pelos 5 produtos mais caros do mês para o gráfico."""
    if df_mes.empty or 'valor' not in df_mes.columns or 'nome_produto' not in df_mes.columns:
        return pd.DataFrame()
    df_despesas = df_mes[df_mes['valor'] < 0].copy()
    if df_despesas.empty:
        return pd.DataFrame()
    df_despesas['valor'] = df_despesas['valor'].abs()
    resumo_prod = df_despesas.groupby('nome_produto')['valor'].sum().reset_index()
    return resumo_prod.sort_values(by='valor', ascending=False).head(5)

def obter_evolucao_mensal_faturamento(df_global: pd.DataFrame, banco: str) -> pd.DataFrame:
    """Calcula a evolução semestral de receitas e despesas para o gráfico."""
    if df_global.empty or 'created_at' not in df_global.columns:
        return pd.DataFrame()
    df = df_global.copy()
    if banco != "-- Selecione um Banco --" and 'banco' in df.columns:
        df = df[df['banco'] == banco]
    if df.empty:
        return pd.DataFrame()
    df['ano_mes'] = df['created_at'].dt.to_period('M')
    agrupado = df.groupby('ano_mes')['valor'].agg(
        Receitas=lambda x: float(x[x > 0].sum()),
        Despesas=lambda x: float(x[x < 0].sum())
    ).reset_index()
    agrupado['Mês'] = agrupado['ano_mes'].dt.strftime('%b/%Y')
    agrupado['Despesas'] = agrupado['Despesas'].abs()
    return agrupado.tail(6)

def realizar_login_real_supabase(email_usuario: str, senha_usuario: str) -> dict:
    """Valida as credenciais do usuário direto no banco Supabase Auth."""
    try:
        supabase = mod_conexao.criar_conexao()
        resposta = supabase.auth.sign_in_with_password({
            "email": email_usuario.strip(),
            "password": senha_usuario.strip()
        })
        if resposta.user:
            return {"status": "sucesso", "usuario_id": resposta.user.id, "email": resposta.user.email}
        return {"status": "erro", "mensagem": "Credenciais inválidas."}
    except Exception as e:
        if "Invalid login credentials" in str(e):
            return {"status": "erro", "mensagem": "⚠️ E-mail ou Senha incorretos!"}
        return {"status": "erro", "mensagem": f"❌ Falha de comunicação: {e}"}

def cadastrar_novo_produto_real(nome_produto: str, id_categoria: int, id_usuario_logado: str) -> bool:
    """Cadastra um novo produto calculando o ID de forma incremental global e evita duplicidade por usuário."""
    try:
        supabase = mod_conexao.criar_conexao()
        prod_limpo = nome_produto.strip().lower()
        
        # 🛡️ CHECAGEM DE DUPLICIDADE: Evita que o mesmo usuário cadastre o mesmo produto duas vezes
        checagem = supabase.table("produtos").select("id")\
            .eq("nome_produto", prod_limpo).eq("usuario_id", id_usuario_logado).execute()
        if checagem.data and len(checagem.data) > 0:
            return False # Retorna falso porque o item já existe para ele
            
        # 🧠 TRUQUE CONTÁBIL: Busca TODOS os IDs do banco para achar o maior número absoluto existente
        todas_linhas = supabase.table("produtos").select("id").execute()
        proximo_id = 1
        if todas_linhas.data:
            # Captura o maior ID numérico absoluto e soma 1
            maior_id = max([int(linha["id"]) for linha in todas_linhas.data if linha["id"] is not None], default=0)
            proximo_id = maior_id + 1
            
        # Grava na nuvem com o ID sequencial perfeito
        supabase.table("produtos").insert({
            "id": proximo_id,
            "nome_produto": prod_limpo,
            "categoria_id": int(id_categoria),
            "usuario_id": id_usuario_logado
        }).execute()
        return True
    except Exception as e:
        print(f"Erro ao cadastrar produto: {e}")
        return False


def registrar_movimentacao_banco(banco: str, nome_produto: str, valor: float, tipo: str, data_lancamento, id_usuario_logado: str) -> bool:
    """Grava o novo lançamento calculando o ID de movimento automaticamente pelo Python."""
    try:
        supabase = mod_conexao.criar_conexao()
        prod_limpo = nome_produto.strip().lower()
        
        todas_linhas = supabase.table("lancamentos").select("id").execute()
        proximo_id = 1
        if todas_linhas.data:
            maior_id = max([int(linha["id"]) for linha in todas_linhas.data if linha["id"] is not None], default=0)
            proximo_id = maior_id + 1
            
        resposta_prod = supabase.table("produtos").select("categoria_id").eq("nome_produto", prod_limpo).execute()
        categoria_nome = "Não Informado"
        if resposta_prod.data and len(resposta_prod.data) > 0:
            id_categoria = resposta_prod.data["categoria_id"]
            resposta_cat = supabase.table("categoria").select("categoria").eq("id", id_categoria).execute()
            if resposta_cat.data and len(resposta_cat.data) > 0:
                categoria_nome = resposta_cat.data["categoria"]
        
        valor_final = -abs(valor) if tipo == "Despesa" else abs(valor)
        
        dados_lancamento = {
            "id": proximo_id,
            "created_at": str(data_lancamento),
            "banco": banco.strip().lower(),
            "categoria": categoria_nome,
            "nome_produto": prod_limpo,
            "valor": valor_final,
            "usuario_id": id_usuario_logado
        }
        
        supabase.table("lancamentos").insert(dados_lancamento).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        print(f"❌ Erro ao gravar lançamento: {e}")
        return False

