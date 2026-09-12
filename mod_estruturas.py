import pandas as pd
import streamlit as st
import mod_conexao

def buscar_categorias_banco(id_usuario_logado: str) -> pd.DataFrame:
    """Busca as categorias do Supabase filtrando rigorosamente pelo usuário ativo."""
    try:
        supabase = mod_conexao.criar_conexao()
        # 🛡️ Filtra apenas as categorias que pertencem a este cliente
        resposta = supabase.table("categoria").select("id, categoria").eq("usuario_id", id_usuario_logado).execute()
        if resposta.data:
            return pd.DataFrame(resposta.data)
        return pd.DataFrame(columns=["id", "categoria"])
    except Exception as e:
        print(f"Erro ao buscar categorias protegidas: {e}")
        return pd.DataFrame(columns=["id", "categoria"])

def buscar_produtos_unicos(id_usuario_logado: str) -> list:
    """Busca a lista de produtos cadastrados pertencentes estritamente ao usuário logado."""
    try:
        supabase = mod_conexao.criar_conexao()
        # 🛡️ Filtra apenas os produtos deste cliente
        resposta = supabase.table("produtos").select("nome_produto").eq("usuario_id", id_usuario_logado).execute()
        if resposta.data:
            df = pd.DataFrame(resposta.data)
            return sorted(df['nome_produto'].unique().tolist())
        return []
    except Exception:
        return []

def cadastrar_novo_produto(nome_produto: str, id_categoria: int) -> str:
    """Insere o produto indexado pelo ID da categoria na tabela public.produtos."""
    try:
        supabase = mod_conexao.criar_conexao()
        nome_limpo = nome_produto.strip().lower()
        
        # CORREÇÃO: Mudado de 'produto' para 'produtos' (plural)
        checagem = supabase.table("produtos").select("nome_produto").eq("nome_produto", nome_limpo).execute()
        if checagem.data:
            return "duplicado"
        
        dados = {
            "nome_produto": nome_limpo,
            "categoria_id": int(id_categoria)
        }
        
        supabase.table("produtos").insert(dados).execute()
        return "sucesso"
    except Exception as e:
        print(f"❌ Erro CRÍTICO ao salvar produto no Supabase: {e}")
        return "erro"

def buscar_bancos_reais(id_usuario_logado: str) -> list:
    """Busca a lista oficial de bancos cadastrados pertencentes estritamente ao usuário logado."""
    try:
        supabase = mod_conexao.criar_conexao()
        # 🛡️ Filtra apenas os bancos deste cliente específico
        resposta = supabase.table("banco").select("banco").eq("usuario_id", id_usuario_logado).execute()
        if resposta.data:
            df = pd.DataFrame(resposta.data)
            return sorted(df['banco'].str.strip().str.lower().unique().tolist())
        return []
    except Exception:
        return []

def cadastrar_novo_banco_real(nome_banco: str, id_usuario_logado: str) -> str:
    """Grava o novo banco calculando o ID autoincremento via Python."""
    try:
        supabase = mod_conexao.criar_conexao()
        nome_limpo = nome_banco.strip().lower()
        
        # Checa duplicidade
        checagem = supabase.table("banco").select("banco").eq("banco", nome_limpo).eq("usuario_id", id_usuario_logado).execute()
        if checagem.data:
            return "duplicado"
            
        # 🧠 TRUQUE CONTÁBIL: Busca o maior ID existente para calcular o próximo
        todas_linhas = supabase.table("banco").select("id").execute()
        proximo_id = 1
        if todas_linhas.data:
            maior_id = max([int(linha["id"]) for linha in todas_linhas.data if linha["id"] is not None], default=0)
            proximo_id = maior_id + 1
            
        # Grava enviando o ID calculado manualmente para burlar o erro 23502
        supabase.table("banco").insert({
            "id": proximo_id, 
            "banco": nome_limpo, 
            "usuario_id": id_usuario_logado
        }).execute()
        return "sucesso"
    except Exception as e:
        print(f"Erro ao salvar novo banco protegido: {e}")
        return "erro"

def deletar_banco_real(nome_banco: str) -> bool:
    """Remove uma instituição da tabela public.banco do Supabase."""
    try:
        supabase = mod_conexao.criar_conexao()
        supabase.table("banco").delete().eq("banco", nome_banco.strip().lower()).execute()
        return True
    except Exception as e:
        print(f"Erro ao deletar banco: {e}")
        return False
    
def cadastrar_novo_banco_real(nome_banco: str, id_usuario_logado: str) -> str:
    """Grava o novo banco calculando o ID autoincremento via Python."""
    try:
        supabase = mod_conexao.criar_conexao()
        nome_limpo = nome_banco.strip().lower()
        
        # Checa duplicidade
        checagem = supabase.table("banco").select("banco").eq("banco", nome_limpo).eq("usuario_id", id_usuario_logado).execute()
        if checagem.data:
            return "duplicado"
            
        # 🧠 TRUQUE CONTÁBIL: Busca o maior ID existente para calcular o próximo
        todas_linhas = supabase.table("banco").select("id").execute()
        proximo_id = 1
        if todas_linhas.data:
            maior_id = max([int(linha["id"]) for linha in todas_linhas.data if linha["id"] is not None], default=0)
            proximo_id = maior_id + 1
            
        # Grava enviando o ID calculado manualmente para burlar o erro 23502
        supabase.table("banco").insert({
            "id": proximo_id, 
            "banco": nome_limpo, 
            "usuario_id": id_usuario_logado
        }).execute()
        return "sucesso"
    except Exception as e:
        print(f"Erro ao salvar novo banco protegido: {e}")
        return "erro"
        
def buscar_produtos_por_nome_categoria(nome_categoria: str) -> list:
    """Busca apenas os produtos que pertencem a uma determinada categoria textual."""
    try:
        supabase = mod_conexao.criar_conexao()
        
        # 1. Descobre o ID da categoria pelo nome
        resposta_cat = supabase.table("categoria").select("id").eq("categoria", nome_categoria.strip()).execute()
        
        if resposta_cat.data:
            id_cat = resposta_cat.data[0]["id"]
            
            # 2. Busca os produtos amarrados a esse ID
            resposta_prod = supabase.table("produtos").select("nome_produto").eq("categoria_id", id_cat).execute()
            if resposta_prod.data:
                df = pd.DataFrame(resposta_prod.data)
                return sorted(df['nome_produto'].unique().tolist())
        return []
    except Exception as e:
        print(f"Erro ao filtrar produtos por categoria: {e}")
        return []
def atualizar_categoria_produto_e_retroativos(id_produto: int, nome_produto: str, novo_id_categoria: int, novo_nome_categoria: str) -> bool:
    """
    1. Atualiza o ID da categoria na tabela de apoio 'produtos'.
    2. Roda um comando em lote (UPDATE) alterando o passado inteiro (18k linhas) na tabela 'lancamentos'.
    """
    try:
        supabase = mod_conexao.criar_conexao()
        
        # AÇÃO 1: Atualiza a tabela de apoio 'produtos'
        supabase.table("produtos").update({"categoria_id": int(novo_id_categoria)}).eq("id", id_produto).execute()
        print(f"📦 Tabela de produtos atualizada: {nome_produto} agora é ID {novo_id_categoria}")
        
        # AÇÃO 2: O 'LOCALIZAR E SUBSTITUIR' EM LOTE! 
        # Altera o texto de todas as linhas do passado onde o produto seja igual
        supabase.table("lancamentos").update({"categoria": novo_nome_categoria}).eq("nome_produto", nome_produto.strip().lower()).execute()
        print(f"🔄 Sucesso Retroativo! Todas as linhas de '{nome_produto}' no passado viraram '{novo_nome_categoria}'!")
        
        return True
    except Exception as e:
        print(f"❌ Erro na atualização retroativa: {e}")
        return False
