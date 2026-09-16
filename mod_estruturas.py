import pandas as pd
import mod_conexao

def buscar_bancos_reais(id_usuario_logado: str) -> list:
    """Busca a lista oficial de bancos cadastrados pertencentes estritamente ao usuário logado."""
    try:
        supabase = mod_conexao.criar_conexao()
        resposta = supabase.table("banco").select("banco").eq("usuario_id", id_usuario_logado).execute()
        if resposta.data:
            df = pd.DataFrame(resposta.data)
            return sorted(df['banco'].str.strip().str.lower().unique().tolist())
        return []
    except Exception:
        return []

if st.button("Gravar Nova Conta", type="primary", key="btn_gravar_novo_banco"):
    if not novo_banco_nome:
        st.warning("⚠️ Digite o nome do banco antes de gravar.")
    else:
        with st.spinner("Conectando com o servidor Supabase..."):
            try:
                # 🔴 LINHA FALTANDO: Chama a função que realmente grava!
                resultado_banco = mod_estruturas.cadastrar_novo_banco_real(novo_banco_nome, st.session_state.usuario_id)
                
                if resultado_banco == "sucesso":
                    st.success(f"🏦 Conta do '{novo_banco_nome}' adicionada com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                elif resultado_banco == "duplicado":
                    st.warning("⚠️ Este banco já está cadastrado.")
                else:
                    st.error(f"❌ Erro ao salvar banco: {resultado_banco}")
            except Exception as e_banco:
                st.error(f"Erro ao salvar banco: {e_banco}")
def buscar_categorias_banco(id_usuario_logado: str) -> pd.DataFrame:
    """Busca as categorias do Supabase filtrando rigorosamente pelo usuário ativo."""
    try:
        supabase = mod_conexao.criar_conexao()
        resposta = supabase.table("categoria").select("id, categoria").eq("usuario_id", id_usuario_logado).execute()
        if resposta.data:
            return pd.DataFrame(resposta.data)
        return pd.DataFrame(columns=["id", "categoria"])
    except Exception as e:
        print(f"Erro ao buscar categorias protegidas: {e}")
        return pd.DataFrame(columns=["id", "categoria"])

def cadastrar_nova_categoria_real(nome_categoria: str, id_usuario_logado: str) -> str:
    """Grava a nova categoria calculando o ID autoincremento via Python."""
    try:
        supabase = mod_conexao.criar_conexao()
        nome_limpo = nome_categoria.strip().lower()
        
        checagem = supabase.table("categoria").select("categoria").eq("categoria", nome_limpo).eq("usuario_id", id_usuario_logado).execute()
        if checagem.data:
            return "duplicado"
            
        todas_linhas = supabase.table("categoria").select("id").execute()
        proximo_id = 1
        if todas_linhas.data:
            maior_id = max([int(linha["id"]) for linha in todas_linhas.data if linha["id"] is not None], default=0)
            proximo_id = maior_id + 1
            
        supabase.table("categoria").insert({
            "id": proximo_id, 
            "categoria": nome_limpo, 
            "usuario_id": id_usuario_logado
        }).execute()
        return "sucesso"
    except Exception as e:
        print(f"Erro ao salvar nova categoria: {e}")
        return "erro"

def buscar_produtos_unicos(id_usuario_logado: str) -> list:
    """Busca a lista de produtos cadastrados pertencentes estritamente ao usuário logado."""
    try:
        supabase = mod_conexao.criar_conexao()
        resposta = supabase.table("produtos").select("nome_produto").eq("usuario_id", id_usuario_logado).execute()
        if resposta.data:
            df = pd.DataFrame(resposta.data)
            return sorted(df['nome_produto'].unique().tolist())
        return []
    except Exception:
        return []

