import pandas as pd
import mod_conexao

def converter_valor_seguro(val):
    """Função cirúrgica para converter a vírgula brasileira em ponto americano"""
    try:
        if pd.isna(val):
            return 0.00
        # Transforma em texto e limpa espaços nas pontas
        txt = str(val).strip()
        # Remove pontos de milhar se o Excel tiver colocado (ex: 1.250,50 -> 1250,50)
        if txt.count('.') > 0 and txt.count(',') > 0:
            txt = txt.replace('.', '')
        # Substitui a vírgula pelo ponto decimal
        txt = txt.replace(',', '.')
        # Converte para número decimal real
        return float(txt)
    except Exception:
        return 0.00

def importar_lancamentos_reais(caminho_csv):
    print("🔄 Lendo o arquivo CSV da Plataforma S.Y.S.T.E.M...")
    
    try:
        # Lendo todas as colunas inicialmente como texto (str) para o Excel não distorcer nada
        df = pd.read_csv(caminho_csv, sep=';', encoding='utf-8', dtype=str)
    except Exception as e:
        print(f"❌ Erro ao tentar ler o arquivo físico: {e}")
        return
    
    df.columns = df.columns.str.strip()
    colunas_reais = ['created_at', 'banco', 'valor', 'categoria', 'nome_produto']
    df = df[colunas_reais]
    df = df.dropna(how='all')
    
    print("🧹 Aplicando limpeza cirúrgica na coluna de valores...")
    # Aplica a função de conversão linha por linha
    df['valor'] = df['valor'].apply(converter_valor_seguro)

    # Limpeza defensiva nas colunas de texto
    for coluna in ['banco', 'categoria', 'nome_produto']:
        df[coluna] = df[coluna].fillna("Não Informado").astype(str).str.strip()
        df[coluna] = df[coluna].replace(['nan', 'NaN', 'None'], 'Não Informado')

    # Conexão com o Supabase
    try:
        supabase = mod_conexao.criar_conexao()
    except Exception as e:
        print(f"❌ Falha ao carregar mod_conexao: {e}")
        return

    dados_para_inserir = df.to_dict(orient='records')
    
    # --- MOSTRAR PREVIEW ANTES DE ENVIAR ---
    print("\n👀 CONFIRMAÇÃO VISUAL - Veja se os primeiros valores estão corretos:")
    for i in range(min(5, len(dados_para_inserir))):
        print(f"Linha {i+1}: Produto: {dados_para_inserir[i]['nome_produto']} | Valor Tratado: {dados_para_inserir[i]['valor']}")
    print("-" * 50)

    print(f"🚀 Enviando {len(df)} lançamentos para o banco de dados...")
    
    try:
        resposta = supabase.table("lancamentos").insert(dados_para_inserir).execute()
        print("🎉 Sucesso!  Dados importados.")
        return resposta
    except Exception as e:
        print(f"❌ Erro ao inserir no Supabase: {e}")

if __name__ == "__main__":
    importar_lancamentos_reais("lancamentos.csv")
