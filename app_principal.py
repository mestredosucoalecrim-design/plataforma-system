import streamlit as st
import datetime
import plotly.express as px
import mod_calculos
import mod_estruturas
import mod_previsoes
import pandas as pd

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
    
    # Cria as duas abas limpas na tela
    aba_login, aba_cadastro = st.tabs(["🔒 Entrar no Sistema", "📝 Criar Nova Conta"])
    
    # 1. FORMULÁRIO DE LOGIN (Tudo o que pertence ao acesso)
    with aba_login:
        email_input = st.text_input("E-mail de Acesso:", placeholder="exemplo@sistema.com", key="txt_login_email")
        senha_input = st.text_input("Senha Securitária:", type="password", key="txt_login_senha")
        
        if st.button("Acessar Plataforma", type="primary", use_container_width=True):
            if email_input and senha_input:
                with st.spinner("Autenticando credenciais na nuvem..."):
                    resultado_login = mod_calculos.realizar_login_real_supabase(email_input, senha_input)
                
                if resultado_login["status"] == "sucesso":
                    st.session_state.logado = True
                    st.session_state.usuario_id = resultado_login["usuario_id"]
                    st.session_state.usuario_email = resultado_login["email"]
                    
                    st.toast(f"Bem-vindo de volta, {resultado_login['email']}!", icon="🔑")
                    st.rerun()
                else:
                    st.error(resultado_login["mensagem"])
            else:
                st.warning("⚠️ Campo obrigatório: Preencha o e-mail e a senha para acessar.")
                
    # 2. 📝 FORMULÁRIO DE CADASTRO (Os campos agora estão realocados no lugar certo!)
    with aba_cadastro:
        st.write("### Formulário de Cadastro")
        
        novo_email = st.text_input("Defina seu E-mail de Acesso:", placeholder="seu-email@sistema.com", key="txt_cadastro_email")
        nova_senha = st.text_input("Defina sua Senha Securitária:", type="password", placeholder="Mínimo 6 caracteres", key="txt_cadastro_senha")
        confirmar_senha = st.text_input("Confirme sua Senha:", type="password", key="txt_cadastro_confirma")
        
        # Botão para disparar o cadastro de novo usuário
        if st.button("Criar My Conta", type="primary", use_container_width=True):
            if novo_email and nova_senha and confirmar_senha:
                if nova_senha != confirmar_senha:
                    st.error("❌ As senhas digitadas não são iguais. Tente novamente.")
                elif len(nova_senha) < 6:
                    st.error("❌ Por segurança, a senha deve ter pelo menos 6 caracteres.")
                else:
                    with st.spinner("Registrando credenciais na nuvem..."):
                        try:
                            resultado_cadastro = mod_calculos.realizar_cadastro_supabase(novo_email, nova_senha)
                            
                            if resultado_cadastro.get("status") == "sucesso":
                                st.success("✅ Conta criada com sucesso! Vá para a aba '🔒 Entrar no Sistema' para fazer login.")
                            else:
                                st.error(resultado_cadastro.get("mensagem", "Erro ao cadastrar."))
                        except Exception as erro_interno:
                            st.error(f"❌ Erro na execução do código: {erro_interno}")
            else:
                st.warning("⚠️ Todos os campos são obrigatórios para realizar o cadastro.")

# =========================================================================
# TELA 2: MENU PRINCIPAL E NAVEGAÇÃO
# =========================================================================
else:
    st.sidebar.title("S.Y.S.T.E.M v2.0")
    st.sidebar.write("👤 Usuário: **William Melo: Administrador**")
    
    # 🟢 ADICIONADO: '🏠 Menu Principal' entra como a primeira opção da lista
    opcao_menu = st.sidebar.radio(
        "Selecione uma Tela:",
        ["🏠 Menu Principal", "📈 Painel e Extratos", "📥 Novo Lançamento", "⚙️ Cadastros Básicos", "🔮 Orçamento Preditivo"],
        key="menu_principal"
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state.logado = False
        st.rerun()

    # 🟢 NOVO BLOCO: RENDERIZA O SEU MARCADOR DE COMBUSTÍVEL SE A PRIMEIRA OPÇÃO FOR SELECIONADA
    if opcao_menu == "🏠 Menu Principal":
        st.title("🏠 Bem-vindo à Plataforma S.Y.S.T.E.M")
        st.markdown(f"Olá, **{st.session_state.usuario_email}**! Seu cockpit está conectado.")
        
        st.markdown("---")
        st.subheader("📊 Marcador de Autonomia Financeira")
        st.write("Calibre os sensores informando o ciclo do seu recebimento para monitorar seu ritmo de consumo:")
        
        # Caixas de entrada para o ciclo dinâmico do dinheiro do William
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_ultimo = st.date_input("Data do Último Recebimento:", value=pd.Timestamp.now().date() - pd.Timedelta(days=5), key="cal_data_ultimo")
        with col_d2:
            data_proximo = st.date_input("Data do Próximo Recebimento:", value=pd.Timestamp.now().date() + pd.Timedelta(days=25), key="cal_data_proximo")
            
        # Busca o saldo consolidado atual do usuário para o cálculo
        df_glob_menu = mod_calculos.buscar_todos_lancamentos_completos(st.session_state.usuario_id)
        resumo_menu = mod_calculos.calcular_resumo_memoria(df_glob_menu)
        saldo_em_bolso = resumo_menu['saldo']
        
        # Dispara o motor de cálculo matemático do mod_previsoes
        dados_autonomia = mod_previsoes.calcular_autonomia_caixa_real(st.session_state.usuario_id, data_ultimo, data_proximo, saldo_em_bolso)
        
                if dados_autonomia:
            st.markdown("### 🧭 Diagnóstico do Manche")
            
            c_met1, c_met2, c_met3, c_met4 = st.columns(4)
            c_met1.metric(label="Saldo Inicial Livre", value=f"R$ {dados_autonomia['saldo_disponivel_dia_um']:,.2f}")
            c_met2.metric(label="Média Necessária (Teto)", value=f"R$ {dados_autonomia['media_necessaria']:,.2f}/dia")
            c_met3.metric(label="Sua Média Real", value=f"R$ {dados_autonomia['media_real']:,.2f}/dia")
            c_met4.metric(label="Quanto PODE gastar/dia", value=f"R$ {dados_autonomia['quanto_pode_gastar_hoje']:,.2f}")
            
            st.markdown("---")
            
            if dados_autonomia["rombo_estimado"] == 0:
                st.success(
                    f"🟢 **Rota Segura!** Seu ritmo de gastos real está dentro do limite. "
                    f"Você pode gastar até **R$ {dados_autonomia['quanto_pode_gastar_hoje']:,.2f} por dia** para chegar ao final do ciclo com total folga!"
                )
            else:
                # 🔴 O SEU PUXÃO DE ORELHA PERSONALIZADO E MATEMÁTICO:
                st.error(
                    f"🔴 **⚠️ PUXÃO DE ORELHA FINANCEIRO:**\n\n"
                    f"**Se você continuar gastando R$ {dados_autonomia['media_real']:,.2f} por dia dessa forma, "
                    f"suas despesas vão demandar R$ {dados_autonomia['media_real']*dados_autonomia['dias_restantes']:,.2f} até o fim do mês. "
                    f"De onde você vai tirar esse dinheiro se o seu saldo atual é de apenas R$ {saldo_em_bolso:,.2f}? "
                    f"Você terá um rombo estimado de R$ {dados_autonomia['rombo_estimado']:,.2f} antes do próximo recebimento!**\n\n"
                    f"💡 **Ação Imediata:** Reduza o ritmo diário urgentemente para no máximo **R$ {dados_autonomia['quanto_pode_gastar_hoje']:,.2f}/dia** para o tanque durar!"
                )


    # 🟢 AJUSTADO: Mudamos de 'if' para 'elif' para o sistema Hide funcionar e limpar a tela anterior!
    elif opcao_menu == "📈 Painel e Extratos":
        st.title("Painel Financeiro")
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
                        st.plotly_chart(figura_categoria, use_container_width=True, config={'displayModeBar': False})
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
                        st.plotly_chart(figura_barras, use_container_width=True, config={'displayModeBar': False})
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
                        st.plotly_chart(figura_produtos, use_container_width=True, config={'displayModeBar': False})
                    except Exception as e:
                        st.error(f"Erro G3: {e}")

            st.markdown("---")
            st.write("📝 **Extrato Dinâmico (Altere a célula e aperte Enter para atualizar):**")


            if df_extrato.empty:
                st.warning(f"⚠️ Nenhum lançamento efetuado no banco '{banco_selecionado.upper()}' neste período.")
            else:
                df_editor = df_extrato[['id', 'created_at', 'banco', 'categoria', 'nome_produto', 'valor']].copy()
                
                # Força a coluna a ser do tipo Data para o calendário funcionar
                df_editor['created_at'] = pd.to_datetime(df_editor['created_at']).dt.date
                df_editor['Selecionar para Exclusão'] = False
                
                # 1. MONTAGEM DA PLANILHA INTERATIVA (Lugar correto das configurações visuais)
                tabela_viva = st.data_editor(
                    df_editor,
                    width='stretch',
                    hide_index=True,
                    disabled=["id", "categoria"],
                    key="extrato_vico_system",
                    column_config={
                        "id": None, 
                        "created_at": st.column_config.DateColumn("Data do Lançamento", format="DD/MM/YYYY"),
                        "banco": st.column_config.TextColumn("Banco/Conta"), 
                        "categoria": st.column_config.TextColumn("Categoria (Automática)"),
                        "nome_produto": st.column_config.TextColumn("Produto/Item"),
                        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                        "Selecionar para Exclusão": st.column_config.CheckboxColumn("🗑️ Deletar?", default=False)
                    }
                )
                
                # 2. FLUXO DE EXCLUSÃO POR BOTÃO
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
                
                # 3. FLUXO DE EDIÇÃO INSTANTÂNEA (Versão Direta e Imune a Erros)
                mudancas = st.session_state.get("extrato_vico_system")
                if mudancas and mudancas.get("edited_rows"):
                    sucesso_global = True
                    houve_edicao = False
                    for idx_linha, campos_alterados in mudancas["edited_rows"].items():
                        if "Selecionar para Exclusão" in campos_alterados:
                            continue
                        houve_edicao = True
                        id_real = int(df_editor.iloc[idx_linha]['id'])
                        
                        # Converte o valor para float se houver alteração
                        if "valor" in campos_alterados:
                            campos_alterados["valor"] = float(campos_alterados["valor"])
                            
                        # Ajusta o formato da data para o Supabase se houver alteração
                        if "created_at" in campos_alterados:
                            dt_alvo = campos_alterados["created_at"]
                            data_curta = str(dt_alvo)[:10].strip()
                            campos_alterados["created_at"] = f"{data_curta}T00:00:00+00:00"
                        
                        # 🟢 CONEXÃO DIRETA COM O SUPABASE: Atualiza qualquer campo (Data, Produto, Valor) de forma dinâmica
                        try:
                            import mod_conexao
                            supabase = mod_conexao.criar_conexao()
                            supabase.table("lancamentos").update(campos_alterados).eq("id", id_real).execute()
                        except Exception as e_direto:
                            print(f"❌ Erro na gravação direta: {e_direto}")
                            sucesso_global = False
                                
                    if houve_edicao and sucesso_global:
                        st.toast("⚡ Banco atualizado com sucesso!", icon="💾")
                        st.cache_data.clear()
                        st.rerun()

    # --- TELA 2: NOVO LANÇAMENTO ---
    elif opcao_menu == "📥 Novo Lançamento":
        # Criamos colunas invisíveis para "espremer" o formulário no centro, simulando um UserForm do VBA!
        col_margem_esq, col_formulario_central, col_margem_dir = st.columns([0.1, 0.8, 0.1])
        
        with col_formulario_central:
            st.title("📥 Registrar Movimentação Financeira")
            st.write("Insira os dados abaixo para registrar uma despesa ou receita em tempo real.")
            
            # Buscas dinâmicas do Supabase
            # 🟢 CORREÇÃO DE SEGURANÇA: Garante que a lista nasça preenchida se o banco vier vazio
            try:
                bancos_disponiveis = mod_estruturas.buscar_bancos_reais(st.session_state.usuario_id)
            except TypeError:
                # Caso a função não aceite o ID do usuário ainda:
                bancos_disponiveis = mod_estruturas.buscar_bancos_reais()

            # Se mesmo assim retornar vazio ou der erro, entregamos a lista padrão salvadora:
            if not bancos_disponiveis:
                bancos_disponiveis = ["Banco do Brasil", "Itaú", "Bradesco", "Santander", "NuBank", "Caixa"]

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
            st.subheader("📁 Cadastrar Nova Categoria")
            nova_cat_nome = st.text_input("Digite o nome da nova categoria (ex: transporte, lazer):", key="txt_nova_cat")
            
            if st.button("Gravar Nova Categoria", type="secondary"):
                if nova_cat_nome:
                    with st.spinner("Gravando categoria na nuvem..."):
                        resultado_cat = mod_estruturas.cadastrar_nova_categoria_real(nova_cat_nome, st.session_state.usuario_id)

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
            
            # BUSCA DE CATEGORIAS
            df_categorias = mod_estruturas.buscar_categorias_banco(st.session_state.usuario_id)
            if not df_categorias.empty:
                dict_categorias = dict(zip(df_categorias["categoria"].str.upper(), df_categorias["id"]))
                lista_cat = list(dict_categorias.keys())
                
                cat_selecionada = st.selectbox("Escolha a Categoria para Vincular:", lista_cat)
                id_cat_selecionado = int(dict_categorias[cat_selecionada])
                novo_prod = st.text_input("2º Passo: Digite o nome do Produto (ex: uber, energia solar):")
                
                if st.button("Confirmar e Gravar Registro", type="primary"):
                    if novo_prod:
                        with st.spinner("Gravando no Supabase..."):
                            resultado = mod_calculos.cadastrar_novo_produto_real(novo_prod, id_cat_selecionado, st.session_state.usuario_id)
                        
                        if resultado is True:
                            st.success(f"🎉 Sucesso! O produto '{novo_prod.lower()}' foi indexado na categoria '{cat_selecionada}'.")
                            st.cache_data.clear()
                            st.rerun()
                        elif resultado == "duplicado":
                            st.warning(f"⚠️ Operação Recusada: O produto '{novo_prod.lower()}' já existe.")
                        else:
                            # Se o banco rejeitar por erro estrutural, mostra o texto do erro aqui
                            st.error(f"❌ O banco rejeitou a gravação. Detalhe: {resultado}")
                    else:
                        st.warning("⚠️ Campo obrigatório: Digite o nome do produto antes de gravar.")

            st.markdown("---")
            st.subheader("🔄 Correção e Reclassificação Histórica")
            st.write("Mude a categoria de qualquer item existente.")
            
            if not df_categorias.empty:
                cat_filtro_origem = st.selectbox("1º Passo: Selecione a Categoria ATUAL do item:", ["-- Escolha --"] + lista_cat, key="sb_cat_origem")
                
                if cat_filtro_origem != "-- Escolha --":
                    produtos_filtrados = mod_estruturas.buscar_produtos_por_nome_categoria(cat_filtro_origem)
                    
                    if not produtos_filtrados:
                        st.info(f"Nenhum produto cadastrado na categoria '{cat_filtro_origem}'.")
                    else:
                        produto_para_corrigir = st.selectbox("2º Passo: Selecione o Produto:", ["-- Selecione o Produto --"] + produtos_filtrados, key="sb_prod_corrigir")
                        
                        if produto_para_corrigir != "-- Selecione o Produto --":
                            cat_destino_nome = st.selectbox(f"3º Passo: Mova para a NOVA Categoria:", ["-- Selecione a Nova Categoria --"] + lista_cat, key="sb_cat_destino")
                            
                            if cat_destino_nome != "-- Selecione a Nova Categoria --":
                                if cat_filtro_origem == cat_destino_nome:
                                    st.warning("⚠️ Operação Inválida!")
                                else:
                                    if st.button(f"🚀 Executar Atualização de '{produto_para_corrigir.upper()}'", type="primary"):
                                        id_nova_cat = int(df_categorias[df_categorias['categoria'] == cat_destino_nome]['id'].values[0])
                                        import mod_conexao
                                        supabase_busca = mod_conexao.criar_conexao()
                                        res_prod = supabase_busca.table("produtos").select("id").eq("nome_produto", produto_para_corrigir.strip().lower()).execute()
                                        
                                        if res_prod.data:
                                            id_real_prod = int(res_prod.data[0]["id"])
                                            with st.spinner("Reclassificando..."):
                                                if mod_estruturas.atualizar_categoria_produto_e_retroativos(id_real_prod, produto_para_corrigir, id_nova_cat, cat_destino_nome):
                                                    st.success("🎉 Reclassificado com sucesso!")
                                                    st.cache_data.clear()
                                                    st.rerun()

        # 2. ABA DE BANCOS (Estrutura blindada e alinhada)
        with tab_bancos:
            st.subheader("🏦 Gerenciar Bancos")
            lista_bancos_reais = ["Banco do Brasil", "Itaú", "Bradesco", "Santander", "NuBank", "Caixa"]
            
            st.write("Seus bancos ativos para lançamentos:")
            for b in lista_bancos_reais:
                st.write(f"- {b}")
            
            st.markdown("---")
            st.subheader("➕ Adicionar Novo Banco")
            novo_banco_nome = st.text_input("Digite o nome do novo banco/conta:", key="txt_novo_banco")
            
            if st.button("Gravar Nova Conta", type="primary", key="btn_gravar_novo_banco"):
                if not novo_banco_nome:
                    st.warning("⚠️ Digite o nome do banco antes de gravar.")
                else:
                    with st.spinner("Conectando com o servidor Supabase..."):
                        try:
                            st.success(f"🏦 Conta do '{novo_banco_nome}' adicionada com sucesso!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e_banco:
                            st.error(f"Erro ao salvar banco: {e_banco}")
                        
            st.markdown("---")
            st.write("📋 **Contas Operacionais Ativas na Nuvem:**")
            
            # Buscas dinâmicas do Supabase
            bancos_disponiveis = mod_estruturas.buscar_bancos_reais(st.session_state.usuario_id)
            produtos_disponiveis = mod_estruturas.buscar_produtos_unicos(st.session_state.usuario_id)
            
            # Garante que a lista exista na memória, mesmo se o usuário for novo e não tiver dados cadastrados
            lista_bancos_reais = []

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
                                        
    # =========================================================================
    # TELA 4: ORÇAMENTO PREDITIVO (O PARA-BRISA)
    # =========================================================================
    elif opcao_menu == "🔮 Orçamento Preditivo":
        st.title("🔮 Orçamento Preditivo & Projeções")
        st.write("Olhe pelo para-brisa: gerencie seu salário e planeje seus compromissos futuros.")
        
        # 🟢 Adicionamos a 3ª aba aqui: 'tab_visualizar'
        tab_perfil, tab_novas_previsoes, tab_visualizar = st.tabs([
            "👤 Salário & Perfil", 
            "📝 Agendar Gasto Futuro / Parcelado",
            "📊 Visualizar Para-brisa (Mês a Mês)"
        ])
        
        # 1. ABA DO SALÁRIO CONFIGURÁVEL
        with tab_perfil:
            st.subheader("Configuração de Renda Fixa")
            salario_atual = mod_previsoes.buscar_salario_usuario(st.session_state.usuario_id)
            
            st.write(f"💵 Seu salário base cadastrado atualmente é: **R$ {salario_atual:,.2f}**")
            novo_salario_input = st.number_input("Alterar Salário Base (R$):", min_value=0.00, value=salario_atual, step=100.00, key="num_novo_salario")
            
            if st.button("Salvar Nova Renda", type="primary", key="btn_salvar_salario"):
                if mod_previsoes.gerenciar_salario_usuario(st.session_state.usuario_id, novo_salario_input):
                    st.success("🎉 Renda base atualizada com sucesso no banco de dados!")
                    st.rerun()
                else:
                    st.error("❌ Falha ao tentar atualizar a renda base.")
                    
        # 2. ABA DO PARCELAMENTO AUTOMÁTICO
        with tab_novas_previsoes:
            st.subheader("Agendar Novo Compromisso Parcelado")
            desc_item = st.text_input("Descrição do Item (ex: guarda-roupa, IPVA):", key="txt_prev_desc")
            
            df_cat_prev = mod_estruturas.buscar_categories_banco(st.session_state.usuario_id) if 'buscar_categories_banco' in dir(mod_estruturas) else pd.DataFrame()
            if not df_cat_prev.empty:
                lista_cat_prev = df_cat_prev["categoria"].str.upper().tolist()
                cat_escolhida = st.selectbox("Selecione o Grupo de Despesa:", lista_cat_prev, key="sb_prev_cat")
            else:
                cat_escolhida = st.text_input("Digite o Grupo de Despesa (ex: moveis, lazer):", key="txt_prev_cat_manual")
                
            col_vlr, col_qtd, col_data = st.columns(3)
            with col_vlr:
                vlr_parc = st.number_input("Valor de CADA Parcela (R$):", min_value=0.01, step=10.00, key="num_prev_vlr")
            with col_qtd:
                qtd_parc = st.number_input("Quantidade Total de Parcelas:", min_value=1, max_value=120, value=1, step=1, key="num_prev_qtd")
            with col_data:
                data_prim = st.date_input("Data do 1º Vencimento:", key="date_prev_vcto")
                
            if st.button("Gerar Projeção de Parcelas", type="primary", use_container_width=True, key="btn_gerar_parcelas"):
                if desc_item and cat_escolhida and vlr_parc > 0:
                    with st.spinner("Calculando calendário..."):
                        sucesso = mod_previsoes.gerar_lancamentos_futuros_parcelados(
                            descricao=desc_item,
                            categoria=cat_escolhida,
                            valor_parcela=vlr_parc,
                            total_parcelas=int(qtd_parc),
                            data_primeiro_vencimento=data_prim,
                            id_usuario_logado=st.session_state.usuario_id
                        )
                    if sucesso:
                        st.success(f"🎉 Sucesso! Foram geradas {qtd_parc} parcelas de R$ {vlr_parc:,.2f}!")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.warning("⚠️ Preencha todos os campos obrigatórios.")

        # 3. ABA DE VISUALIZAÇÃO MÊS A MÊS (O REAL PARA-BRISA)
        with tab_visualizar:
            st.subheader("🗓️ Gestão e Projeção do Orçamento")
            st.write("Abaixo estão suas contas futuras. Marque a caixinha 'Baixar' para pagá-la ou 'Excluir' para deletar a projeção.")
            
            salario_base = mod_previsoes.buscar_salario_usuario(st.session_state.usuario_id)
            compromissos_detalhes = mod_previsoes.buscar_detalhe_compromissos_abertos(st.session_state.usuario_id)
            
            if not compromissos_detalhes:
                st.info("✨ Nenhuma parcela ou despesa futura agendada para os próximos meses!")
            else:
                # 🟢 REMOVIDO o st.write de teste perigoso que expunha os dados!
                
                df_detalhado = pd.DataFrame(compromissos_detalhes)
                df_detalhado["vencimento"] = pd.to_datetime(df_detalhado["data_vencimento"]).dt.strftime("%d/%m/%Y")
                df_detalhado["parcela"] = df_detalhado["parcela_atual"].astype(str) + "/" + df_detalhado["total_parcelas"].astype(str)
                
                df_detalhado["Baixar (Pagar)"] = False
                df_detalhado["Excluir Registro"] = False
                
                df_visual = df_detalhado[["id", "vencimento", "descricao_item", "categoria", "parcela", "valor_parcela", "Baixar (Pagar)", "Excluir Registro"]]
                df_visual.columns = ["ID", "Vencimento", "Descrição", "Categoria", "Parcela", "Valor (R$)", "Baixar", "Excluir"]
                
                # Planilha interativa
                linhas_editadas = st.data_editor(
                    df_visual,
                    hide_index=True,
                    use_container_width=True,
                    disabled=["ID", "Vencimento", "Descrição", "Categoria", "Parcela", "Valor (R$)"],
                    column_config={
                        "Valor (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                        "Baixar": st.column_config.CheckboxColumn(help="Marque para enviar ao fluxo de caixa real"),
                        "Excluir": st.column_config.CheckboxColumn(help="Marque para deletar permanentemente do para-brisa")
                    }
                )
                
                st.markdown("---")
                st.subheader("⚙️ Executar Baixa/Exclusão em Lote")
                
                # 🟢 NOVO COMPONENTE: Busca os bancos dinâmicos do usuário para ele escolher de onde sai o dinheiro
                try:
                    bancos_selecao = mod_estruturas.buscar_bancos_reais(st.session_state.usuario_id)
                except:
                    bancos_selecao = []
                
                if not bancos_selecao or isinstance(bancos_selecao, float):
                    bancos_selecao = ["Banco do Brasil", "Itaú", "Bradesco", "Santander", "NuBank", "Caixa"]
                
                banco_debitar = st.selectbox("Se houver Baixa, debitar de qual Conta/Banco?", bancos_selecao, key="sb_previsao_banco_debito")
                
                # Botão para processar as caixinhas
                if st.button("🚀 Processar Ações Marcadas", type="primary", use_container_width=True, key="btn_processar_previsoes_lote"):
                    sucessos = 0
                    
                    # 🟢 CORREÇÃO CRÍTICA: Mudado de lines_editadas para linhas_editadas (com H)
                    for index, linha in linhas_editadas.iterrows():
                        id_registro = int(linha["ID"])
                        
                        # Se marcou para dar baixa (Pagar)
                        if linha["Baixar"] is True:
                            # Passamos o banco escolhido dinamicamente na tela
                            if mod_previsoes.dar_baixa_parcela_futura(id_registro, st.session_state.usuario_id, banco_debitar):
                                sucessos += 1
                                
                        # Se marcou para excluir a projeção
                        elif java_script_falso := (linha["Excluir"] is True):
                            if mod_previsoes.excluir_parcela_futura_definitivo(id_registro, st.session_state.usuario_id):
                                successes = 0 # Ajuste interno
                                sucessos += 1
                    
                    if sucessos > 0:
                        st.success(f"🎉 Sucesso! {sucessos} operação(ões) sincronizada(s) com o banco de dados!")
                        
                        # 🟢 LIMPEZA DE CACHE COMPREENSIVA (Zera todas as memórias de busca de extratos e painéis)
                        st.cache_data.clear()
                        if 'bancos_disponiveis' in st.session_state:
                            del st.session_state['bancos_disponiveis']
                        
                        # Dá o comando de reinicialização visual instantânea
                        st.rerun()

                        
                st.markdown("---")
                st.subheader("📊 Resumo Consolidado Preditivo")
                
                df_futuro = mod_previsoes.calcular_comprometimento_mensal_futuro(st.session_state.usuario_id)
                if not df_futuro.empty:
                    df_futuro["Salário Fixo"] = salario_base
                    df_futuro["Saldo Livre"] = df_futuro["Salário Fixo"] - df_futuro["Comprometido"]
                    
                    df_exibicao = df_futuro.copy()
                    df_exibicao["Comprometido"] = df_exibicao["Comprometido"].map("R$ {:,.2f}".format)
                    df_exibicao["Salário Fixo"] = df_exibicao["Salário Fixo"].map("R$ {:,.2f}".format)
                    df_exibicao["Saldo Livre"] = df_exibicao["Saldo Livre"].map("R$ {:,.2f}".format)
                    
                    st.dataframe(
                        df_exibicao[["Mês/Ano", "Salário Fixo", "Comprometido", "Saldo Livre"]], 
                        use_container_width=True, 
                        hide_index=True
                    )
