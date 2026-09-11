import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega as variáveis do arquivo oculto .env
load_dotenv()

URL_SUPABASE = os.getenv("SUPABASE_URL")
CHAVE_SUPABASE = os.getenv("SUPABASE_KEY")

def criar_conexao() -> Client:
    """Estabelece e retorna a conexão oficial com o cliente Supabase."""
    try:
        if not URL_SUPABASE or not CHAVE_SUPABASE:
            raise ValueError("As credenciais do Supabase não foram encontradas no arquivo .env!")
        return create_client(URL_SUPABASE, CHAVE_SUPABASE)
    except Exception as e:
        print(f"❌ Erro crítico ao conectar com o Supabase: {e}")
        raise e
