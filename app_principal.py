import streamlit as st
import datetime
import plotly.express as px
import mod_calculos
import mod_estruturas

# 1. Configuração de Layout da Página
st.set_page_config(
    page_title="Plataforma S.Y.S.T.E.M",
    page_icon="📊",
    layout="centered"
)

# 2. Inicialização da Memória de Sessão
if "logado" not in st.session_state:
    st.session_state.logado = False
if "ano_atual" not in st.session_state:
    st.session_state.ano_atual = datetime.date.today().year
if "mes_atual" not in st.session_state:
    st.session_state.mes_atual = datetime.date.today().month

NOME_MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# =========================================================================
# TELA 1: INTERFACE DE LOGIN / CADASTRO (AUTENTICAÇÃO REAL CONECTADA)
# =========================================================================
if not st.session_state.logado:
    st.title("Plataforma S.Y.S.T.E.M")
    st.subheader("Acesso Restrito")
    
    aba_login, aba_cadastro = st.tabs(["🔒 Entrar no Sistema", "📝 Criar Nova Conta"])
    
    with aba_login:
        email_input = st.text_input("E-mail de Acesso:", placeholder="exemplo@sistema.com", key="txt_login_email")
        senha_input = st.text_input("Senha Securitária:", type="password", key="txt_login_senha")
        
        if st.button("Acessar Plataforma", type="primary", use_container_width=True):
            if email_input and senha_input:
                with st.spinner("Autenticando credenciais na nuvem..."):
                    # Dispara a validação real no Supabase
                    resultado_login = mod_calculos.realizar_login_real_supabase(email_input, senha_input)
                
                if resultado_login["status"] == "sucesso":
                    # 🔥 GUARDA NA MEMÓRIA DA SESSÃO: Transforma o app em privado para este ID único!
                    st.session_state.logado = True
                    st.session_state.usuario_id = resultado_login["usuario_id"]
                    st.session_state.usuario_email = resultado_login["email"]
                    
                    st.toast(f"Bem-vindo de volta, {resultado_login['email']}!", icon="🔑")
                    st.rerun()
                else:
                    st.error(resultado_login["mensagem"])
            else:
                st.warning("⚠️ Campo obrigatório: Preencha o e-mail e a senha para acessar.")
                
    with aba_cadastro:
        st.write("### Formulário de Cadastro")
        st.info("Para esta fase de homologação, os novos usuários devem ser cadastrados via convite ou diretamente pelo Administrador no painel do Supabase.")


# =========================================================================
# TELA 2: MENU PRINCIPAL E NAVEGAÇÃO
# =========================================================================
else:
    st.sidebar.title("S.Y.S.T.E.M v2.0")
    st.sidebar.write("👤 Usuário: **Administrador Teste**")
    
    opcao_menu = st.sidebar.radio(
        "Selecione uma Tela:",
        ["📈 Painel e Extratos", "📥 Novo Lançamento", "⚙️ Cadastros Básicos"],
        key="menu_principal"
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state.logado = False
        st.rerun()

        # --- TELA 1: PAINEL E EXTRATOS ---
    if opcao_menu == "📈 Painel e Extratos":
        st.title("Painel Financeiro")
        
                # 🚀 VELOCIDADE E SEGURANÇA: Passa o ID único do usuário ativo para o filtro
        with st.spinner("Sincronizando base histórica com a nuvem..."):
            # CORREÇÃO: Enviamos o st.session_state.usuario_id para o motor!
            df_global = mod_calculos.buscar_todos_lancamentos_completos(st.session_state.usuario_id)
            resumo = mod_calculos.calcular_resumo_memoria(df_global)

        
        # Painel fixo do topo
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Saldo Geral Consolidado", value=f"R$ {resumo['saldo']:,.2f}")
        col2.metric(label="Total de Receitas", value=f"R$ {resumo['receitas']:,.2f}")
        col3.metric(label="Total de Despesas", value=f"R$ {resumo['despesas']:,.2f}")
        
        st.markdown("---")
        st.subheader("Consulte seu Extrato")
        
        col_banco, col_setas = st.columns([0.6, 0.4])
        with col_banco:
            lista_bancos = ["-- Selecione um Banco --"] + mod_estruturas.buscar_bancos_reais(st.session_state.usuario_id)
            banco_selecionado = st.selectbox("Escolha a conta bancária para conciliação:", lista_bancos)
            
        with col_setas:
            st.write("Navegar por Período:")
            c_esq, c_dir = st.columns(2)
            if c_esq.button("◀"):
                st.session_state.mes_atual -= 1
                if st.session_state.mes_atual == 0:
                    st.session_state.mes_atual = 12
                    st.session_state.ano_atual -= 1
                st.rerun()
                
            if c_dir.button("▶"):
                st.session_state.mes_atual += 1
                if st.session_state.mes_atual == 13:
                    st.session_state.mes_atual = 1
                    st.session_state.ano_atual += 1
                st.rerun()
                
        st.info(f"📅 Período de Análise Selecionado: **{NOME_MESES[st.session_state.mes_atual]} / {st.session_state.ano_atual}**")
        
        if banco_selecionado == "-- Selecione um Banco --":
            st.write("")
            st.info("💡 **Aguardando Ação:** Por favor, selecione uma conta bancária acima para visualizar o extrato detalhado e o saldo real acumulado.")
        else:
            # ⚡ Filtros executados estritamente quando o banco está ativo na tela
            df_extrato = mod_calculos.filtrar_extrato_memoria(df_global, st.session_state.mes_atual, st.session_state.ano_atual, banco_selecionado)
            saldo_real_banco = mod_calculos.calcular_saldo_historico_memoria(df_global, st.session_state.mes_atual, st.session_state.ano_atual, banco_selecionado)
            df_grafico = mod_calculos.obter_despesas_por_categoria_memoria(df_extrato)
            
            st.markdown(f"### Resumo da Conta: {banco_selecionado.upper()}")
            
            col_real, col_mensal = st.columns(2)
            with col_real:
                st.metric(label=f"Saldo Real em Conta ({banco_selecionado.upper()})", value=f"R$ {saldo_real_banco:,.2f}")
            with col_mensal:
                soma_mes = df_extrato['valor'].sum() if not df_extrato.empty else 0.00
                st.metric(label="Movimentação Líquida do Mês", value=f"R$ {soma_mes:,.2f}")

            # ⚡ Busca o terceiro conjunto de dados (Maiores Produtos do Mês)
            df_produtos_top = mod_calculos.obter_maiores_produtos_mes_memoria(df_extrato)

            st.markdown("### 📊 Indicadores Visuais de Desempenho")
            
            # 🎮 A MÁGICA DA HORIZONTAL: Divide a tela em 3 colunas iguais!
            col_graf1, col_graf2, col_graf3 = st.columns(3)
            
            # --- COLUNA 1: MAIORES CUSTOS POR CATEGORIA ---
            with col_graf1:
                st.markdown("##### 🎯 Custos por Categoria")
                if df_grafico.empty:
                    st.info("Sem despesas no período.")
                else:
                    try:
                        figura_categoria = px.bar(
                            df_grafico, x='valor', y='categoria', orientation='h',
                            labels={'valor': 'R$', 'categoria': ''}, color='categoria',
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        figura_categoria.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=220, showlegend=False)
                        figura_categoria.update_yaxes(categoryorder='total ascending')
                        st.plotly_chart(figura_categoria, use_container_width=True)
                    except Exception as e:
                        st.error(f"Erro G1: {e}")

            # --- COLUNA 2: HISTÓRICO SEMESTRAL (ENTRADAS E SAÍDAS) ---
            with col_graf2:
                st.markdown("##### 📈 Histórico Semestral")
                df_evolucao = mod_calculos.obter_evolucao_mensal_faturamento(df_global, banco_selecionado)
                if df_evolucao.empty:
                    st.info("Dados insuficientes.")
                else:
                    try:
                        df_melted = df_evolucao.melt(id_vars=['Mês'], value_vars=['Receitas', 'Despesas'], 
                                                     var_name='Fluxo', value_name='Total')
                        figura_barras = px.bar(
                            df_melted, x='Total', y='Mês', color='Fluxo', orientation='h', barmode='group',
                            labels={'Total': 'R$', 'Mês': ''},
                            color_discrete_map={'Receitas': '#2ECC71', 'Despesas': '#E74C3C'}
                        )
                        figura_barras.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=220, showlegend=False)
                        st.plotly_chart(figura_barras, use_container_width=True)
                    except Exception as e:
                        st.error(f"Erro G2: {e}")

            # --- COLUNA 3: NOVO GRÁFICO - TOP 5 PRODUTOS MAIS GASTOS ---
            with col_graf3:
                st.markdown("##### 📦 Top 5 Itens (Maiores Gastos)")
                if df_produtos_top.empty:
                    st.info("Sem despesas no período para listar produtos.")
                else:
                    try:
                        figura_produtos = px.bar(
                            df_produtos_top,
                            x='valor',
                            y='nome_produto',
                            orientation='h',
                            labels={'valor': 'R$', 'nome_produto': ''},
                            color='nome_produto',                          
                            color_discrete_sequence=px.colors.qualitative.Pastel
                         )
                        figura_produtos.update_layout(margin=dict(t=5, b=5, l=5, r=5), height=220, showlegend=False)
                        figura_produtos.update_yaxes(categoryorder='total ascending')
                        st.plotly_chart(figura_produtos, use_container_width=True)
                    except Exception as e:
                        st.error(f"Erro G3: {e}")

            st.markdown("---")
            st.write("📝 **Extrato Dinâmico (Altere a célula e aperte Enter para atualizar):**")


            if df_extrato.empty:
                st.warning(f"⚠️ Nenhum lançamento efetuado no banco '{banco_selecionado.upper()}' neste período.")
            else:
                df_editor = df_extrato[['id', 'created_at', 'banco', 'categoria', 'nome_produto', 'valor']].copy()
                df_editor['created_at'] = df_editor['created_at'].dt.strftime('%Y-%m-%d')
                df_editor['Selecionar para Exclusão'] = False
                
                tabela_viva = st.data_editor(
                    df_editor,
                    width='stretch',
                    hide_index=True,
                    disabled=["id", "categoria"],
                    key="extrato_vico_system",
                    column_config={
                        "id": None, 
                        "created_at": st.column_config.TextColumn("Data (AAAA-MM-DD)"),
                        "banco": st.column_config.TextColumn("Banco/Conta"), 
                        "categoria": st.column_config.TextColumn("Categoria (Automática)"),
                        "nome_produto": st.column_config.TextColumn("Produto/Item"),
                        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                        "Selecionar para Exclusão": st.column_config.CheckboxColumn("🗑️ Deletar?", default=False)
                    }
                )
                
                # Exclusão por botão
                linhas_para_deletar = tabela_viva[tabela_viva['Selecionar para Exclusão'] == True]
                if not linhas_para_deletar.empty:
                    st.write("")
                    if st.button("🗑️ Excluir Registros Selecionados", type="secondary"):
                        sucesso_del = True
                        for _, linha in linhas_para_deletar.iterrows():
                            id_real = int(linha['id'])
                            if not mod_calculos.deletar_lancamento_banco(id_real):
                                sucesso_del = False
                        if sucesso_del:
                            st.toast("⚡ Registros eliminados!", icon="🗑️")
                            st.rerun()
                
                # Edição instantânea
                mudancas = st.session_state.get("extrato_vico_system")
                if mudancas and mudancas.get("edited_rows"):
                    sucesso_global = True
                    houve_edicao = False
                    for idx_linha, campos_alterados in mudancas["edited_rows"].items():
                        if "Selecionar para Exclusão" in campos_alterados:
                            continue
                        houve_edicao = True
                        id_real = int(df_editor.iloc[idx_linha]['id'])
                        if "valor" in campos_alterados:
                            campos_alterados["valor"] = float(campos_alterados["valor"])
                        if not mod_calculos.atualizar_lancamento_banco(id_real, campos_alterados):
                            sucesso_global = False
                    if houve_edicao and sucesso_global:
                        st.toast("⚡ Banco atualizado!", icon="💾")
                        st.rerun()

    # --- TELA 2: NOVO LANÇAMENTO ---
    elif opcao_menu == "📥 Novo Lançamento":
        # Criamos colunas invisíveis para "espremer" o formulário no centro, simulando um UserForm do VBA!
        col_margem_esq, col_formulario_central, col_margem_dir = st.columns([0.1, 0.8, 0.1])
        
        with col_formulario_central:
            st.title("📥 Registrar Movimentação Financeira")
            st.write("Insira os dados abaixo para registrar uma despesa ou receita em tempo real.")
            
            # Buscas dinâmicas do Supabase
            bancos_disponiveis = mod_estruturas.buscar_bancos_reais(st.session_state.usuario_id)
            produtos_disponiveis = mod_estruturas.buscar_produtos_unicos(st.session_state.usuario_id)
            
            # 🛡️ BLINDAGEM: Adicionamos a opção neutra no topo para abrir totalmente vazio!
            lista_bancos_form = ["-- Escolha o Banco --"] + bancos_disponiveis
            lista_produtos_form = ["-- Selecione o Produto --"] + produtos_disponiveis
            
            col_b, col_p = st.columns(2)
            with col_b:
                banco_mov = st.selectbox("1. Escolha a Conta/Banco:", mod_estruturas.buscar_bancos_reais(st.session_state.usuario_id))
            with col_p:
                if not produtos_disponiveis:
                    st.warning("⚠️ Nenhum produto cadastrado no sistema. Vá em Configurações primeiro.")
                    st.stop()
                produto_mov = st.selectbox("2. Produto / Item Comprado:", lista_produtos_form, index=0)
                
            col_t, col_v, col_d = st.columns(3)
            with col_t:
                tipo_mov = st.selectbox("3. Tipo de Operação:", ["-- Selecione --", "Despesa (Saída)", "Receita (Entrada)"], index=0)
            with col_v:
                # Inicializa em 0.00 para forçar a BIOS a digitar o valor real
                valor_mov = st.number_input("4. Valor do Lançamento (R$):", min_value=0.00, step=1.00, format="%.2f", value=0.00)
            with col_d:
                data_mov = st.date_input("5. Data do Gasto:", datetime.date.today())
                
            st.markdown("---")
            
            if st.button("🚀 Confirmar e Salvar Lançamento", type="primary"):
                # 🕵️‍♂️ VALIDAÇÃO CIRÚRGICA: Se o atendente esqueceu de preencher algo, o sistema barra!
                if banco_mov == "-- Escolha o Banco --":
                    st.error("⚠️ Erro Operacional: Você precisa selecionar um **Banco/Conta** válido!")
                elif produto_mov == "-- Selecione o Produto --":
                    st.error("⚠️ Erro Operacional: Você precisa selecionar um **Produto**!")
                elif tipo_mov == "-- Selecione --":
                    st.error("⚠️ Erro Operacional: Você precisa definir se é uma **Despesa** ou **Receita**!")
                elif valor_mov <= 0.00:
                    st.error("⚠️ Erro Operacional: O **Valor** do lançamento deve ser maior que R$ 0,00!")
                else:
                    # Se passou em todas as travas, grava com segurança no Supabase
                    with st.spinner("Gravando movimentação na nuvem..."):
                       # Como deve ficar a linha do botão de salvar dentro do app_principal.py:
                       sucesso_lanc = mod_calculos.registrar_movimentacao_banco(
                       banco_mov, produto_mov, valor_mov, tipo_mov, data_mov, st.session_state.usuario_id
)

                    if sucesso_lanc:
                        st.success(f"🎉 Sucesso! O lançamento de '{produto_mov}' foi gravado no banco '{banco_mov.upper()}'!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Falha técnica ao salvar o lançamento no servidor.")


    # --- TELA 3: CADASTROS BÁSICOS ---
    elif opcao_menu == "⚙️ Cadastros Básicos":
        st.title("⚙️ Configurações de Estrutura")
        st.write("Gerencie os parâmetros operacionais da sua plataforma de forma simples.")
        
        tab_produtos, tab_bancos = st.tabs(["📦 Cadastro de Produtos e Categorias", "🏦 Bancos e Contas Ativas"])
        
        # 1. ABA DE PRODUTOS E CATEGORIAS
        with tab_produtos:
            # ➕ NOVO BLOCO: Cadastrar Nova Categoria Contábil
            st.subheader("📁 Cadastrar Nova Categoria")
            nova_cat_nome = st.text_input("Digite o nome da nova categoria (ex: transporte, lazer):", key="txt_nova_cat")
            
            if st.button("Gravar Nova Categoria", type="secondary"):
                if nova_cat_nome:
                    with st.spinner("Gravando categoria na nuvem..."):
                        # Envia o comando de inserção para o Supabase
                        resultado_cat = mod_estruturas.cadastrar_nova_categoria_real(nova_cat_nome)
                    if resultado_cat == "sucesso":
                        st.success(f"🎉 Categoria '{nova_cat_nome}' cadastrada com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                    elif resultado_cat == "duplicado":
                        st.warning("⚠️ Esta categoria já está cadastrada.")
                    else:
                        st.error("❌ Erro ao salvar categoria no banco.")
                else:
                    st.warning("⚠️ Digite o nome da categoria.")

            st.markdown("---")
            st.subheader("📦 Vincular Novo Produto a uma Categoria")
            st.write("Insira o nome do item e selecione a qual grupo de despesa ele pertence.")
            
            df_categorias = mod_estruturas.buscar_categorias_banco(st.session_state.usuario_id)
            
            if df_categorias.empty:
                st.warning("⚠️ Nenhuma categoria encontrada na tabela 'categoria' do Supabase. Cadastre uma categoria acima primeiro.")
            else:
                lista_nomes_cat = df_categorias['categoria'].tolist()
                cat_escolhida_nome = st.selectbox("1º Passo: Escolha a Categoria Contábil:", lista_nomes_cat)
                
                id_cat_selecionado = int(df_categorias[df_categorias['categoria'] == cat_escolhida_nome]['id'].values[0])
                novo_prod = st.text_input("2º Passo: Digite o nome do Produto (ex: uber, energia solar):")
                
                if st.button("Confirmar e Gravar Registro", type="primary"):
                    if novo_prod:
                        with st.spinner("Gravando no Supabase..."):
                            resultado = mod_estruturas.cadastrar_novo_produto(novo_prod, id_cat_selecionado)
                        
                        if resultado == "sucesso":
                            st.success(f"🎉 Sucesso! O produto '{novo_prod.lower()}' foi indexado na categoria '{cat_escolhida_nome}' (ID: {id_cat_selecionado}).")
                        elif resultado == "duplicado":
                            st.warning(f"⚠️ Operação Recusada: O produto '{novo_prod.lower()}' já existe no sistema.")
                        else:
                            st.error("❌ O banco rejeitou a gravação.")
                    else:
                        st.warning("⚠️ Campo obrigatório: Digite o nome do produto antes de gravar.")

            # 🛠️ O Painel de Alterações Focado (Estilo UserForm)
            st.markdown("---")
            st.subheader("🔄 Correção e Reclassificação Histórica")
            st.write("Mude a categoria de qualquer item existente. O sistema corrigirá o cadastro e todo o passado automaticamente.")
            
            if not df_categorias.empty:
                # 1ª Combobox: Escolha da categoria antiga
                cat_filtro_origem = st.selectbox(
                    "1º Passo: Selecione a Categoria ATUAL do item:", 
                    ["-- Escolha --"] + lista_nomes_cat, 
                    key="sb_cat_origem"
                )
                
                if cat_filtro_origem != "-- Escolha --":
                    # O Python vai no banco e traz APENAS os produtos dessa categoria!
                    produtos_filtrados = mod_estruturas.buscar_produtos_por_nome_categoria(cat_filtro_origem)
                    
                    if not produtos_filtrados:
                        st.info(f"Nenhum produto cadastrado atualmente na categoria '{cat_filtro_origem}'.")
                    else:
                        # 2ª Combobox: Escolha do produto específico
                        produto_para_corrigir = st.selectbox(
                            "2º Passo: Selecione o Produto que deseja alterar:", 
                            ["-- Selecione o Produto --"] + produtos_filtrados,
                            key="sb_prod_corrigir"
                        )
                        
                        if produto_para_corrigir != "-- Selecione o Produto --":
                            # 3ª Combobox: Escolha da nova categoria destino
                            cat_destino_nome = st.selectbox(
                                f"3º Passo: Mova '{produto_para_corrigir.upper()}' para a NOVA Categoria:", 
                                ["-- Selecione a Nova Categoria --"] + lista_nomes_cat,
                                key="sb_cat_destino"
                            )
                            
                            if cat_destino_nome != "-- Selecione a Nova Categoria --":
                                # Trava de segurança: impede escolher a mesma categoria
                                if cat_filtro_origem == cat_destino_nome:
                                    st.warning("⚠️ Operação Inválida: A nova categoria deve ser diferente da atual!")
                                else:
                                    st.write("") # Espaçador visual
                                if st.button(f"🚀 Executar Atualização em Lote de '{produto_para_corrigir.upper()}'", type="primary"):
                                        # 1. Descobre o ID da nova categoria selecionada
                                        id_nova_cat = int(df_categorias[df_categorias['categoria'] == cat_destino_nome]['id'].values[0])
                                        
                                        # 2. Busca o ID real do produto direto no Supabase de forma rápida
                                        import mod_conexao
                                        supabase_busca = mod_conexao.criar_conexao()
                                        res_prod = supabase_busca.table("produtos").select("id").eq("nome_produto", produto_para_corrigir.strip().lower()).execute()
                                        
                                        if res_prod.data:
                                            id_real_prod = int(res_prod.data[0]["id"])
                                            
                                            # 3. Dispara o gatilho atômico que reclassifica e varre o passado de 18k linhas!
                                            with st.spinner(f"Varrendo histórico... Reclassificando de '{cat_filtro_origem}' para '{cat_destino_nome}'..."):
                                                if mod_estruturas.atualizar_categoria_produto_e_retroativos(id_real_prod, produto_para_corrigir, id_nova_cat, cat_destino_nome):
                                                    st.success(f"🎉 Sucesso Absoluto! '{produto_para_corrigir.upper()}' foi reclassificado para '{cat_destino_nome}' em todo o histórico!")
                                                    st.balloons()
                                                    st.cache_data.clear() # Limpa a memória para os saldos e gráficos atualizarem na hora
                                                    st.rerun()
                                                else:
                                                    st.error("Erro técnico ao tentar varrer o histórico no Supabase.")
                        
        # 2. ABA DE BANCOS (Sincronizada direto com a tabela public.banco!)
        with tab_bancos:
            st.subheader("Gerenciar Instituições e Fluxos de Caixa")
            st.write("Adicione novas contas ou remova as antigas. As alterações impactam todo o sistema instantaneamente.")
            
            with st.expander("➕ Adicionar Nova Conta / Banco"):
                novo_banco_nome = st.text_input("Nome da nova conta (ex: itau, inter, bradesco):")
                if st.button("Gravar Nova Conta", type="primary"):
                    if novo_banco_nome:
                        with st.spinner("Conectando com o servidor Supabase..."):
                            # Executa o INSERT real na tabela 'banco'
                            resultado_banco = mod_estruturas.cadastrar_novo_banco_real(novo_banco_nome, st.session_state.usuario_id)
                        
                        if resultado_banco == "sucesso":
                            st.success(f"🎉 Sucesso! A conta '{novo_banco_nome.upper()}' foi registrada no banco de dados!")
                            # Limpa o cache para que o app inteiro passe a exibir o novo banco nas comboboxes
                            st.cache_data.clear()
                            st.rerun()
                        elif resultado_banco == "duplicado":
                            st.warning(f"⚠️ Operação Recusada: A conta '{novo_banco_nome.upper()}' já existe no sistema.")
                        else:
                            st.error("❌ O servidor rejeitou a gravação. Verifique a conexão.")
                    else:
                        st.warning("⚠️ Campo obrigatório: Digite o nome da conta antes de gravar.")
            
            st.markdown("---")
            st.write("📋 **Contas Operacionais Ativas na Nuvem:**")
            
            # Busca a lista atualizada direto do Supabase
            lista_bancos_reais = mod_estruturas.buscar_bancos_reais(st.session_state.usuario_id)
            
            if not lista_bancos_reais:
                st.info("Nenhum banco cadastrado na tabela física do Supabase.")
            else:
                for b in lista_bancos_reais:
                    col_texto, col_btn = st.columns([0.8, 0.2])
                    with col_texto:
                        if b.lower() == "caixa":
                            st.markdown(f"💵 • **{b.upper()}** *(Dinheiro Físico / Gaveta)*")
                        else:
                            st.markdown(f"🏛️ • **{b.upper()}** *(Conta Corrente / Investimento)*")
                    with col_btn:
                        # Criamos chaves exclusivas para o Streamlit não duplicar os botões de lixeira
                        if st.button("🗑️", key=f"btn_deletar_banco_{b}", help=f"Excluir definitivamente a conta {b.upper()}"):
                            with st.spinner("Removendo do Supabase..."):
                                if mod_estruturas.deletar_banco_real(b):
                                    st.toast(f"⚡ Conta {b.upper()} eliminada com sucesso!", icon="🗑️")
                                    # Limpa o cache para atualizar as telas imediatamente
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Erro técnico ao tentar deletar o banco.")
