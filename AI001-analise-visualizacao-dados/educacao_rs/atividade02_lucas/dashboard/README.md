# Escolaridade, renda e produção nos municípios do RS — dashboard

Atividade 02 da disciplina IA001: dashboard em Streamlit que dá continuidade à
Atividade 01 (`notebook/atividade01_dados_pib_2010.ipynb`) e permite investigar
as suas quatro perguntas nos 496 municípios gaúchos, com dados do Censo 2010.

**Público:** técnicos de planejamento regional (COREDEs, SEPLAG-RS e secretarias
municipais) que precisam localizar, dentro do seu COREDE, os municípios que mais se
afastam do padrão estadual.

## Perguntas e origem de cada visualização

A página de cada pergunta é uma coluna única, de cima para baixo: indicadores da
seleção, mapa interativo, gráficos da Atividade 01 e tabela. Cada bloco traz um selo
com a sua origem:

- **Atividade 01** (azul) — o mesmo gráfico de `notebook/atividade01_dados_pib_2010.ipynb`,
  com as mesmas cores, títulos, eixos e anotações, redesenhado em Matplotlib com os dados
  do dashboard. As estatísticas continuam calculadas sobre os 496 municípios; os filtros
  só destacam a seleção (o que está fora dela fica em cinza). Com todas as regiões
  marcadas, cada figura é igual à da Atividade 01.
- **Atividade 02** (verde) — o que foi criado nesta atividade: o mapa interativo em
  Folium, os indicadores e a tabela da seleção.

| | Pergunta | Mapa interativo (Atividade 02) | Gráficos (Atividade 01) |
|---|---|---|---|
| 1 | Municípios onde mais ocupados têm ensino médio completo pagam melhor? | Novo: renda observada − esperada pela escolaridade, em 4 classes de ±1 desvio-padrão | 6.1 — dispersão com reta e r de Pearson |
| 2 | Como muda a distribuição de faixas de renda conforme o nível de escolaridade do município? | Novo: quartil de escolaridade | 6.2.1 — barras 100% empilhadas por quartil de escolaridade |
| 3 | A proximidade da capital explica o rendimento, ou há regiões não metropolitanas com rendimento equivalente ou superior? | Versão interativa do mapa 6.3.3: quintis de renda, anéis de 100/200/300 km, contornos da RF1 e da RF3 | 6.3.2 — um ponto por município e o traço da mediana, por Região Funcional |
| 4 ✨ | Existem municípios cuja renda é incompatível com a produção local, e o que distingue os de PIB igualmente baixo? | Versão interativa do mapa 6.4.4: resíduo em relação ao PIB, contorno nos 13 municípios de PIB baixo e renda acima do esperado | 6.4.2 — dispersão PIB × renda; 6.4.3 — os dois grupos do tercil inferior de PIB |

**A pergunta 4 é uma novidade.** Ela não estava entre as três perguntas da proposta
original da Atividade 01: foi acrescentada em `atividade01_dados_pib_2010.ipynb` com um
terceiro conjunto de dados, o PIB dos municípios de 2010 (IBGE), e é a única que cruza a
renda dos moradores com a produção local. O dashboard a marca com o selo "novidade".

Bibliotecas de visualização: **Folium** (mapa) e **Matplotlib** (gráficos da Atividade 01).

## Cores dos mapas

Cada pergunta pinta o seu mapa numa **cor base própria** — azul na 1, laranja na 2,
aqua na 3, violeta na 4 — e trocar de pergunta troca a cor do mapa inteiro. As
quatro foram escolhidas como conjunto e verificadas par a par, em visão normal e
sob simulação de protanopia e deuteranopia.

As quatro escalas são **rampas sequenciais de um tom só**, do claro ao escuro:

| Pergunta | Escala | Do claro ao escuro |
|---|---|---|
| 1 | resíduo em relação à escolaridade | abaixo → acima do esperado |
| 2 | quartil de escolaridade | Q1 → Q4 |
| 3 | quintil de renda | 1º → 5º quintil |
| 4 | resíduo em relação ao PIB per capita | abaixo → acima do esperado |

Matizes diferentes dentro de uma escala anunciariam categorias sem ordem. Numa rampa
de um tom quem diz "mais" e "menos" é a luminosidade, que sobrevive à impressão em
cinza e a qualquer daltonismo. O passo mais claro fica em 2:1 contra o fundo, para
não sumir na superfície.

Duas consequências que vale conhecer:

- **As escalas de resíduo perderam o meio neutro.** Elas são divergentes por
  natureza — o resíduo tem sinal, e zero fica entre a 2ª e a 3ª classe. Numa rampa de
  um tom, "muito abaixo" e "muito acima" viram as duas pontas de uma mesma grandeza.
  Quem carrega o sinal agora é o rótulo de cada classe, que diz a direção em palavras.
- **O cinza de "sem dado" clareou** de `#d9d9d9` para `#e4e3e0`: contra as rampas
  novas, o tom antigo ficava perto demais do passo mais claro. Como o tom novo recua
  para perto da superfície, o município sem dado ganhou um traço escuro no mapa.

**Os gráficos da Atividade 01 não seguem esta paleta.** Eles mantêm as cores originais
do notebook de propósito: existem para corresponder ao trabalho anterior, e recolori-los
quebraria essa correspondência. Numa mesma página, portanto, mapa e gráfico podem usar
matizes diferentes — é intencional, e o selo de cada bloco diz de qual atividade ele vem.

## Controles

1. **Pergunta** — escolhe o que pinta o mapa e qual gráfico aparece.
2. **Região Funcional** — filtra mapa, gráficos, indicadores e tabela.
3. **COREDE** — lista só os COREDEs das regiões escolhidas; vazio = todos.
4. **Só o tercil inferior de PIB per capita** — aparece apenas na pergunta 4.

Retas, quartis, quintis, desvios-padrão e o tercil de PIB são calculados **uma vez,
sobre os 496 municípios**. O filtro só escolhe o que aparece; por isso um município
mantém sempre a mesma classe, e os números batem com a Atividade 01. Quando a
combinação de filtros não deixa nenhum município, o dashboard avisa em vez de mostrar
gráficos vazios.

## Instalação e execução

Requer Python 3.10 ou mais recente. A partir desta pasta (`dashboard/`):

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

O navegador abre em `http://localhost:8501`. Os dados já estão em `dados/`, então não
é preciso baixar nada; só as bibliotecas JavaScript do mapa (Leaflet) vêm da internet.

Para conferir que os cálculos reproduzem a Atividade 01 (correlação, limites dos
quartis, faixas de renda, medianas regionais, resíduos, o grupo de 13 municípios e os
p-valores do teste de permutação):

```bash
python analise.py
```

## Arquivos

```text
dashboard/
├── app.py                    # interface: controles, mapa, tabela
├── analise.py                # cálculos das 4 perguntas + autoverificação
├── graficos_atividade01.py   # gráficos da Atividade 01 (Matplotlib)
├── requirements.txt
└── dados/
    ├── municipios_web.geojson   # 497 municípios, indicadores de 2010
    └── regioes_web.geojson      # 9 Regiões Funcionais dissolvidas
```

Os dois GeoJSON são gerados pelo notebook `../regioes_funcionais_rs.ipynb`. Para
refazê-los a partir das fontes oficiais, execute o notebook inteiro: a seção 9 grava
as cópias nesta pasta. A procedência de cada fonte (URL, data e SHA-256) fica em
`../dados/regioes_funcionais/preparados/fontes_e_preparo.json`.

## Fontes

- Atlas do Desenvolvimento Humano no Brasil (Pnud, Ipea, FJP), com dados do Censo 2010 (IBGE) — rendimento, escolaridade e faixas de rendimento dos ocupados.
- PIB dos municípios 2010 (IBGE, SIDRA tabela 5938) — PIB per capita, população e valor adicionado por setor.
- Malha municipal 2022 (IBGE).
- Regiões Funcionais de Planejamento e COREDEs — Decreto 54.572/2019 (SEPLAG-RS).

## Limitações

- Corte único de 2010: nada aqui descreve tendência.
- A unidade é o município (falácia ecológica) e cada município pesa 1, independente da população.
- Pinto Bandeira, emancipado em 2013, não tem dado de 2010 e aparece em cinza.
- A distância à capital é em linha reta entre centroides, não tempo de deslocamento.
- Com R² = 0,21 na pergunta 4, o resíduo é sobretudo o que o PIB não explica.

## Nota técnica: por que o mapa não tem mapa-base

Os servidores de mosaicos do OpenStreetMap respondem **403 – Access blocked** a
pedidos sem cabeçalho `Referer`, como os de um HTML aberto com duplo clique ou de um
mapa exibido dentro do Jupyter. Como os polígonos cobrem todo o RS, o mapa usa
`tiles=None` e um fundo neutro: nada se perde na leitura e não há dependência de
servidor, conta ou chave de API.
