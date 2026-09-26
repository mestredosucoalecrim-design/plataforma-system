import streamlit as st


FAQ_APLICACOES = [
    {
        "pergunta": "1. O que é SELIC?",
        "resposta": """
A SELIC é a taxa básica de juros da economia brasileira.

Ela serve como referência para várias outras taxas de juros. Por isso,
quando a Selic muda, isso pode afetar empréstimos, financiamentos e
também algumas aplicações financeiras.

A taxa Selic é definida pelo Copom — Comitê de Política Monetária do
Banco Central.

Em termos simples: a Selic funciona como uma referência do preço do
dinheiro no Brasil.
""",
        "fonte": "Banco Central do Brasil — Taxa Selic",
        "url": "https://www.bcb.gov.br/controleinflacao/taxaselic",
    },
    {
        "pergunta": "2. O que é CDI?",
        "resposta": """
CDI significa Certificado de Depósito Interbancário.

É uma operação usada pelos bancos para emprestar dinheiro entre si por
períodos muito curtos, geralmente de um dia útil.

A taxa de juros dessas operações é conhecida como Taxa DI. Ela fica
muito próxima da Selic e é uma das principais referências usadas para
calcular o rendimento de várias aplicações financeiras.

É por isso que aparecem ofertas como 100%, 115% ou 140% do CDI.
""",
        "fonte": "Banco Central do Brasil — Glossário de Cidadania Financeira",
        "url": "https://www.bcb.gov.br/content/cidadaniafinanceira/documentos_cidadania/Informacoes_gerais/glossario_cidadania_financeira.pdf",
    },
    {
        "pergunta": "3. Como se calcula o CDI?",
        "resposta": """
Todos os dias úteis são realizadas operações de empréstimos de
curtíssimo prazo entre instituições financeiras.

A partir dessas operações, são apuradas as taxas praticadas e os
respectivos volumes negociados. Dessa apuração resulta a Taxa DI do dia,
que no uso cotidiano do mercado costuma ser chamada de CDI.

Em resumo:

operações entre instituições → apuração das taxas → consideração dos
volumes negociados → Taxa DI do dia.
""",
        "fonte": "B3 — Metodologia da Taxa DI",
        "url": "https://www.b3.com.br/main.jsp?doui_processActionId=setLocaleProcessAction&locale=pt_BR&lumA=1&lumII=2C9FBE63638CFE2501638D36C90D59AE&lumPageId=2C9FBE63638CFE2501638D3464C85778",
    },
    {
        "pergunta": "4. Se o banco oferece 115% do CDI, como encontro a taxa correspondente?",
        "resposta": """
É uma multiplicação simples.

Imagine que o CDI de referência seja 13,65% ao ano:

13,65 × 115 ÷ 100 = 15,6975% ao ano

Portanto:

115% do CDI = aproximadamente 15,70% ao ano.

115% do CDI não significa 115% ao ano.

Você pode fazer essa conta na calculadora, no papel ou no Excel.
""",
        "fonte": "Banco Central do Brasil — Calculadora do Cidadão",
        "url": "https://www3.bcb.gov.br/CALCIDADAO/publico/corrigirPeloCDI.do?aba=5&dataInicial=&method=corrigirPeloCDI",
    },
    {
        "pergunta": "5. Quantos dias úteis são considerados nos cálculos financeiros e por que isso importa?",
        "resposta": """
Um mês não tem uma quantidade fixa de dias úteis. Dependendo do
calendário, pode ter mais ou menos dias úteis.

Para determinados cálculos financeiros, porém, é utilizada uma base de
252 dias úteis por ano.

Isso não significa que todos os anos tenham exatamente 252 dias úteis
no calendário. Trata-se de uma convenção usada em determinados cálculos.

Isso importa porque a forma de transformar uma taxa anual em uma taxa
diária ou mensal depende da convenção e do produto analisado.

Uma taxa de 13,65% ao ano, por exemplo, não deve simplesmente ser
dividida por 12 em todos os tipos de cálculo.

Na nossa simulação usamos uma taxa anual equivalente e períodos
mensais, conforme a metodologia apresentada no próprio sistema.
""",
        "fonte": "Banco Central do Brasil — regulamentação de cálculo de taxas",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/especialnor/Resolu%C3%A7%C3%A3o5171.pdf",
    },
    {
        "pergunta": "6. Eu consigo fazer esse cálculo na calculadora ou no lápis?",
        "resposta": """
Sim.

Você não precisa de um programa especial para entender ou conferir o
cálculo.

A matemática utilizada na simulação pode ser reproduzida com uma
calculadora que tenha a função de potência, com papel e lápis ou no
Excel.

O Banco Central também disponibiliza a Calculadora do Cidadão para
cálculos financeiros.

O S.Y.S.T.E.M. faz a conta para você. Mas você pode conferir o
S.Y.S.T.E.M.
""",
        "fonte": "Banco Central do Brasil — Calculadora do Cidadão",
        "url": "https://www3.bcb.gov.br/CALCIDADAO/publico/exibirFormCalculoValorFuturoCapital.do?method=exibirFormCalculoValorFuturoCapital",
    },
    {
        "pergunta": "7. Qual fórmula é utilizada?",
        "resposta": """
O S.Y.S.T.E.M. utiliza a fórmula de juros compostos:

Valor final = Valor inicial × (1 + taxa mensal)ⁿ

Onde:

• Valor inicial = dinheiro aplicado no começo;
• taxa mensal = taxa utilizada para cada mês;
• n = quantidade de meses.

A cada período, o rendimento passa a fazer parte do valor sobre o qual
será calculado o rendimento seguinte.

Em outras palavras: o dinheiro rende; o rendimento fica junto do
dinheiro; e o próximo rendimento é calculado sobre o novo valor.
""",
        "fonte": "Banco Central do Brasil — Metodologia da Calculadora do Cidadão",
        "url": "https://www3.bcb.gov.br/CALCIDADAO/publico/exibirMetodologiaValorFuturoCapital.do?method=exibirMetodologiaValorFuturoCapital",
    },
    {
        "pergunta": "8. O resultado da simulação é líquido?",
        "resposta": """
Não necessariamente.

O valor mostrado pelo S.Y.S.T.E.M. é uma estimativa do rendimento da
aplicação antes de eventuais impostos ou outros custos.

Dependendo do produto, podem existir regras de Imposto de Renda, IOF,
isenções ou outras condições específicas.

Por isso, o resultado da simulação não deve ser interpretado
automaticamente como o valor líquido que chegará ao bolso do usuário.

Para saber o valor efetivo, é necessário conhecer as regras do produto
específico.
""",
        "fonte": "Receita Federal — Rendimentos do Capital",
        "url": "https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/preenchimento/manual-mir/rendimentos/rendimentos-do-capital",
    },
    {
        "pergunta": "9. O que são IR e IOF?",
        "resposta": """
IR é o Imposto de Renda. Em determinadas aplicações financeiras, os
rendimentos podem estar sujeitos ao imposto, de acordo com o tipo de
investimento e suas condições.

IOF é o Imposto sobre Operações de Crédito, Câmbio e Seguro, ou
relativas a Títulos ou Valores Mobiliários. Ele pode incidir em
determinadas operações, conforme suas regras específicas.

Em resumo:

IR → pode incidir sobre determinados rendimentos.

IOF → pode incidir sobre determinadas operações financeiras.

A simulação básica do S.Y.S.T.E.M. não calcula esses impostos.
""",
        "fonte": "Receita Federal — Rendimentos do Capital",
        "url": "https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/preenchimento/manual-mir/rendimentos/rendimentos-do-capital",
    },
    {
        "pergunta": "10. A taxa oferecida pelo banco pode mudar durante o período?",
        "resposta": """
Depende do tipo de aplicação.

Em uma aplicação prefixada, a taxa é definida no momento da contratação,
de acordo com as condições do produto.

Em uma aplicação pós-fixada, a remuneração acompanha um indicador.
Por exemplo, uma aplicação que remunera 115% do CDI está vinculada ao
comportamento do CDI. Se o indicador mudar, o resultado também poderá
mudar.

Na nossa simulação, o sistema considera que a taxa informada permanece
nas mesmas condições durante todo o período.

Isso é uma premissa matemática da simulação, não uma garantia de
rentabilidade futura.
""",
        "fonte": "Portal do Investidor — Características dos investimentos",
        "url": "https://www.gov.br/investidor/pt-br/investir/antes-de-investir/entenda-as-caracteristicas-dos-investimentos",
    },
    {
        "pergunta": "11. Que produto estamos simulando?",
        "resposta": """
Nesta simulação, usamos como referência uma aplicação de renda fixa
pós-fixada, remunerada por um percentual do CDI.

Um exemplo desse tipo de produto é um CDB pós-fixado que ofereça uma
remuneração vinculada à Taxa DI.

Mas atenção: o S.Y.S.T.E.M. não está simulando um CDB de um banco
específico.

Condições como liquidez, prazo de carência, tributação, garantias e
regras de resgate não fazem parte desta simulação matemática.
""",
        "fonte": "Portal do Investidor — Renda Fixa x Renda Variável",
        "url": "https://www.gov.br/investidor/pt-br/investir/antes-de-investir/entenda-as-caracteristicas-dos-investimentos/renda-fixa-x-renda-variavel",
    },
    {
        "pergunta": "12. Existem outros produtos no mercado financeiro?",
        "resposta": """
Sim. Muitos.

Além dos CDBs, existem, entre outros:

• LCI e LCA;
• títulos públicos;
• debêntures;
• fundos de investimento;
• ações;
• fundos imobiliários;
• ETFs;
• outros produtos do mercado financeiro.

Cada produto possui características próprias de retorno, risco,
liquidez, tributação e funcionamento.

Por isso, não é correto aplicar automaticamente a mesma fórmula a todos
eles.

O S.Y.S.T.E.M. começa por este modelo. Conhecer os outros produtos é
uma próxima etapa de aprendizado.
""",
        "fonte": "Portal do Investidor — Características dos investimentos",
        "url": "https://www.gov.br/investidor/pt-br/investir/antes-de-investir/entenda-as-caracteristicas-dos-investimentos",
    },
    {
        "pergunta": "13. Como a inflação pode influenciar uma aplicação financeira?",
        "resposta": """
A inflação reduz o poder de compra do dinheiro ao longo do tempo.

Por isso, não basta perguntar:

“Quanto meu dinheiro vai render?”

Também é importante perguntar:

“Quanto esse dinheiro poderá comprar no futuro?”

Exemplo: se R$ 10.000,00 se transformarem em R$ 11.000,00, houve um
aumento nominal de R$ 1.000,00. Mas, se os preços também subiram,
o aumento do poder de compra poderá ser menor.

Retorno nominal = quanto o dinheiro aumentou em reais.

Retorno real = quanto o poder de compra aumentou depois de considerar a
inflação.

Uma aplicação pode apresentar rendimento nominal positivo e, ainda
assim, ter ganho real pequeno ou até negativo, dependendo da inflação.
""",
        "fonte": "Banco Central do Brasil — O que é inflação?",
        "url": "https://www.bcb.gov.br/controleinflacao/oqueinflacao",
    },
    {
        "pergunta": "14. Sou obrigado a ter conta corrente no banco onde quero investir?",
        "resposta": """
Não existe uma única regra para todos os investimentos.

Isso depende do produto, da instituição e do canal utilizado para a
aplicação.

Algumas instituições disponibilizam determinados produtos apenas para
seus próprios clientes. Outras oferecem acesso a investimentos por
diferentes plataformas ou canais.

Portanto, não é correto afirmar que todo investimento exige uma conta
corrente no banco onde o investimento foi contratado.

O importante é verificar as condições do produto e da instituição.
""",
        "fonte": "Portal do Investidor — Características dos investimentos",
        "url": "https://www.gov.br/investidor/pt-br/investir/antes-de-investir/entenda-as-caracteristicas-dos-investimentos",
    },
    {
        "pergunta": "15. Posso encerrar a aplicação a qualquer momento?",
        "resposta": """
Depende do produto.

Algumas aplicações permitem resgate antes do vencimento. Outras exigem
que o investidor aguarde o vencimento ou possuem condições específicas
para o resgate.

Essa característica está relacionada à liquidez.

Antes de investir, uma pergunta simples é:

“Eu consigo retirar meu dinheiro quando precisar?”

Mesmo quando existe possibilidade de resgate antecipado, as condições
podem ser diferentes das condições existentes no vencimento.

Na simulação básica do S.Y.S.T.E.M., as regras de resgate não entram no
cálculo.
""",
        "fonte": "Portal do Investidor — Liquidez",
        "url": "https://www.gov.br/investidor/pt-br/investir/antes-de-investir/entenda-as-caracteristicas-dos-investimentos/liquidez",
    },
]


def mostrar_duvidas_frequentes():
    """Exibe a segunda tela educacional de Aplicações Financeiras."""

    st.subheader("❓ Dúvidas Frequentes")

    st.write(
        "Estas perguntas foram organizadas para ajudar você a entender "
        "o que está por trás da simulação."
    )

    st.caption(
        "Resposta direta primeiro. Se quiser aprofundar, consulte a "
        "fonte oficial indicada em cada assunto."
    )

    for item in FAQ_APLICACOES:
        with st.expander(item["pergunta"]):
            st.markdown(item["resposta"])

            st.link_button(
                f"🔎 Consultar fonte oficial",
                item["url"],
                use_container_width=False,
            )
            st.caption(f"Fonte: {item['fonte']}")
