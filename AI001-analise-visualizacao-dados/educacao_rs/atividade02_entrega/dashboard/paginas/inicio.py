"""Página inicial: para quem é o dashboard, as quatro perguntas e como usar os filtros."""

import streamlit as st

import comum

ctx = comum.contexto()

st.title("Escolaridade, renda e produção nos municípios do RS")
st.caption("Censo 2010 · 496 municípios · Atividade 02 da disciplina IA001")

st.markdown(
    "Este dashboard é para **técnicos de planejamento regional** (COREDEs, SEPLAG-RS e "
    "secretarias municipais) que precisam localizar, dentro do seu COREDE, os municípios que mais "
    "se afastam do padrão estadual. Ele dá continuidade às perguntas da Atividade 01: cada uma "
    "tem a sua página, com um mapa interativo, os gráficos da Atividade 01 e a tabela dos "
    "municípios.")

st.subheader("As quatro perguntas")
perguntas = [
    ("paginas/p1_escolaridade_renda.py", ":material/school:", "Escolaridade × renda",
     "Municípios onde mais ocupados têm ensino médio completo pagam melhor?"),
    ("paginas/p2_faixas_de_renda.py", ":material/stacked_bar_chart:", "Faixas de renda",
     "Como muda a distribuição de faixas de renda conforme o nível de escolaridade do município?"),
    ("paginas/p3_capital.py", ":material/location_on:", "Proximidade da capital",
     "A proximidade da capital explica o rendimento, ou há regiões não metropolitanas com "
     "rendimento equivalente ou superior?"),
    ("paginas/p4_renda_producao.py", ":material/factory:", "Renda × produção ✨",
     "Existem municípios cuja renda é incompatível com a produção local, e o que distingue os de "
     "PIB igualmente baixo? *Novidade: não estava na proposta original da Atividade 01.*"),
]
for linha in (perguntas[:2], perguntas[2:]):   # duas linhas de dois cartões, alinhados
    for coluna, (arquivo, icone, titulo, enunciado) in zip(st.columns(2), linha):
        with coluna.container(border=True, height="stretch"):
            st.page_link(arquivo, label=f"**{titulo}**", icon=icone)
            st.markdown(enunciado)

st.subheader("Como usar")
st.markdown(
    "- **Filtros na barra lateral** (Região Funcional e COREDE) valem para todas as páginas e "
    "continuam marcados ao trocar de pergunta.\n"
    "- **Controles próprios** de uma pergunta ficam dentro da página dela, junto do que mudam: "
    "o número de grupos na pergunta 2 e o recorte do tercil inferior de PIB na pergunta 4.\n"
    "- **Os cortes não mudam com o filtro.** Retas, tercis, quartis, quintis e desvios-padrão são "
    "calculados sobre os 496 municípios; o filtro só escolhe o que aparece. Assim um município "
    "fica sempre na mesma classe, qualquer que seja a seleção.")

st.markdown("**Selos:** :blue-badge[Atividade 01] gráfico da Atividade 01 redesenhado com os dados "
            "do dashboard · :green-badge[Atividade 02] criado nesta atividade (mapa, indicadores e "
            "tabela).")

comum.rodape()
