import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega o arquivo local se ele existir (Modo Desenvolvimento no Computador)
load_dotenv()

def criar_conexao() -> Client:
    """
    Estabelece a conexão com o Supabase de forma híbrida.
    Funciona tanto localmente (.env) quanto na nuvem (st.secrets).
    """
    try:
        # Tenta buscar primeiro nas configurações secretas da nuvem (Streamlit Secrets)
        # Se não encontrar, busca no arquivo local .env
        url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
        chave = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not url or not chave:
            raise ValueError("As credenciais do Supabase não foram encontradas!")
            
        return create_client(url, chave)
    except Exception as e:
        print(f"❌ Erro crítico ao conectar com o Supabase: {e}")
        raise e

