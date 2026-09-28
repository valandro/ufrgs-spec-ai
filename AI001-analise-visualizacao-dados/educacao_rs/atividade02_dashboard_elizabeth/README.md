# Escolaridade, renda e produção nos municípios do RS — dashboard

Atividade 02 da disciplina IA001: dashboard em Streamlit que dá continuidade à
Atividade 01 e permite investigar
as suas quatro perguntas nos 496 municípios gaúchos, com dados do Censo 2010.

**Público:** técnicos de planejamento regional (COREDEs, SEPLAG-RS e secretarias
municipais) que precisam localizar, dentro do seu COREDE, os municípios que mais se
afastam do padrão estadual.

## Perguntas e origem de cada visualização

O dashboard tem uma **página por pergunta**, mais uma página **Início** com o público,
as quatro perguntas e como usar os filtros. A navegação fica no topo, e cada página tem
endereço próprio (por exemplo `/faixas-de-renda`). Cada página é uma coluna única, de
cima para baixo: indicadores da seleção, controles próprios da pergunta (quando há),
mapa interativo, gráficos e tabela dos municípios. Duas páginas invertem a ordem e
abrem pelo gráfico: a pergunta 1, com a dispersão escolaridade × rendimento, e a
pergunta 2, com o gráfico de faixas e o "Quem foge do padrão?". Cada bloco traz um
selo com a sua origem:

- **Atividade 01** (azul) — o mesmo gráfico daquele trabalho,
  com as mesmas cores, títulos, eixos e anotações, redesenhado em Matplotlib com os dados
  do dashboard. As estatísticas continuam calculadas sobre os 496 municípios; os filtros
  só destacam a seleção (o que está fora dela fica em cinza). Com todas as regiões
  marcadas, cada figura é igual à da Atividade 01.
- **Atividade 02** (verde) — o que foi criado nesta atividade: o mapa interativo em
  Folium, os indicadores e a tabela da seleção.

| | Pergunta | Mapa interativo (Atividade 02) | Gráficos (Atividade 01) |
|---|---|---|---|
| 1 | Municípios onde mais ocupados têm ensino médio completo pagam melhor? | Novo: renda observada − esperada pela escolaridade, em 4 classes de ±1 desvio-padrão | Dispersão escolaridade × rendimento com reta de tendência, em versão interativa (Altair), com Porto Alegre em destaque e filtros próprios de faixa de renda e escolaridade |
| 2 | Como muda a distribuição de faixas de renda conforme o nível de escolaridade do município? | Novo: grupo de escolaridade (tercis, quartis ou quintis, à escolha) | Barras 100% empilhadas por grupo de escolaridade, em versão interativa (Altair), com leitura automática ao lado e comparação entre tercis, quartis e quintis |
| 3 | A proximidade da capital explica o rendimento, ou há regiões não metropolitanas com rendimento equivalente ou superior? | Versão interativa do mapa: quintis de renda, anéis de 100/200/300 km, contornos da RF1 e da RF3 | Um ponto por município e o traço da mediana, por Região Funcional |
| 4 ✨ | Existem municípios cuja renda é incompatível com a produção local, e o que distingue os de PIB igualmente baixo? | Versão interativa do mapa: resíduo em relação ao PIB, contorno nos 13 municípios de PIB baixo e renda acima do esperado | Dispersão PIB × renda; e o contraste entre os dois grupos do tercil inferior de PIB |

**A dispersão da pergunta 1 vem do dashboard de `educacao/tarefa_02`**, e substituiu a
figura estática que a página trazia. Mantivemos o desenho de lá — pontos, reta de
tendência, Porto Alegre em destaque e o tooltip com município, COREDE, região e faixa de
renda — e os dois filtros próprios: faixa da renda média do município em múltiplos do
salário mínimo de 2010 e intervalo de escolaridade, que valem só para aquele gráfico.

Uma diferença: no `tarefa_02` a reta era reajustada a cada filtro; aqui ela é a do estado
inteiro. É a regra deste dashboard — os cortes não mudam com o filtro — e sem ela a reta
contradiria o mapa e a tabela da mesma página, que medem o resíduo contra a reta dos 496
municípios.

**A pergunta 2 ganhou uma visualização nova, "Quem foge do padrão?"** (Altair). O
gráfico de faixas mostra médias de grupos; esta mostra cada município. Para a faixa de renda
escolhida (a base da renda — sem rendimento + até 1 SM — por padrão), um ponto por
município contra a fatia **esperada pela escolaridade**, com a faixa de ±1 desvio-padrão,
e ao lado um ranking dos 10 municípios mais acima e dos 10 mais abaixo do esperado. O
município escolhido em "Destacar município" aparece circulado no gráfico, entra no
ranking mesmo fora das pontas e ganha um quadro com os seus números e a posição na
seleção. É o que permite ao técnico localizar, no seu COREDE, os casos fora do padrão:
Dezesseis de Novembro, Tupanci do Sul e Rio dos Índios têm muito mais ocupados na base
do que a escolaridade sugere; Nova Hartz, Araricá e Lindolfo Collor, muito menos.

**A pergunta 4 é uma novidade.** Ela não estava entre as três perguntas da proposta
original da Atividade 01: foi acrescentada com um
terceiro conjunto de dados, o PIB dos municípios de 2010 (IBGE), e é a única que cruza a
renda dos moradores com a produção local. O dashboard a marca com o selo "novidade".

Bibliotecas de visualização: **Folium** (mapas), **Altair** (dispersão da pergunta 1, gráfico de faixas e "Quem foge do padrão?", na pergunta 2) e **Matplotlib** (os demais gráficos da
Atividade 01).

## Cores

Cada pergunta pinta o seu mapa numa **cor base própria** — azul na 1, laranja na 2,
magenta na 3, violeta na 4 — e trocar de pergunta troca a cor do mapa inteiro. As
quatro escalas são **rampas sequenciais de um tom só**, do claro ao escuro:

| Pergunta | Escala | Do claro ao escuro |
|---|---|---|
| 1 | resíduo em relação à escolaridade | abaixo → acima do esperado |
| 2 | tercil, quartil ou quintil de escolaridade | T1 → T3, Q1 → Q4 ou 1º → 5º |
| 3 | quintil de renda | 1º → 5º quintil |
| 4 | resíduo em relação ao PIB per capita | abaixo → acima do esperado |

Matizes diferentes dentro de uma escala anunciariam categorias sem ordem. Numa rampa
de um tom quem diz "mais" e "menos" é a luminosidade, que sobrevive à impressão em
cinza e a qualquer daltonismo. Os municípios são pintados sem transparência, para que
o fundo não clareie os tons e aproxime os passos da escala.

Três decisões que vale conhecer:

- **As escalas de resíduo não têm meio neutro.** Elas são divergentes por natureza — o
  resíduo tem sinal, e zero fica entre a 2ª e a 3ª classe. Numa rampa de um tom, "muito
  abaixo" e "muito acima" viram as duas pontas de uma mesma grandeza; quem carrega o
  sinal é o rótulo de cada classe, que diz a direção em palavras.
- **O mapa da pergunta 3 foi refeito duas vezes.** Primeiro porque os quintis vizinhos
  ficavam a ΔE 10–12, abaixo do mínimo de 15 para serem distinguidos: a escala passou a
  descer até quase preto, com todos os vizinhos a ΔE ≥ 15. Depois porque, num verde
  assim, os anéis de distância sumiam — um cinza médio chegava a 1,07:1 contra o passo
  do meio da rampa. A escala virou **magenta**, e os anéis ganharam o mesmo traço branco
  por baixo que os contornos da RF1 e da RF3 já tinham: nenhuma cor única atravessa
  cinco passos de uma rampa sem desaparecer em algum deles. As fronteiras das 9 regiões
  seguem num cinza fino, para que o destaque fique com a RF1 e a RF3.
- **O cinza de "sem dado" é `#e4e3e0`**, perto da superfície; para não depender só do
  preenchimento, o município sem dado ganha um traço escuro no mapa.

**Os gráficos Matplotlib da Atividade 01 mantêm as cores originais do notebook**, de
propósito: existem para corresponder ao trabalho anterior. A exceção é a **página da
pergunta 2**, que usa um laranja só: o gráfico de faixas interativo passou do azul original
para seis tons do mesmo laranja do mapa (`CORES_FAIXAS_P2` em `analise.py`), e o "Quem
foge do padrão?" usa a escala do mapa. Todas as cores dos dados ficam em `analise.py`.

A **cor dos controles** (multiselect, rádio, botões) vem do tema do Streamlit, em
`.streamlit/config.toml` (`primaryColor`); aqui ela é um grafite neutro, `#2f3a45`, em
vez do vermelho padrão, para não competir com as cores dos dados. O tema só é lido
quando o Streamlit inicia.

## Controles

**Na barra lateral — valem para todas as páginas** e continuam marcados ao trocar de
pergunta:

1. **Região Funcional** — filtra mapa, gráficos, indicadores e tabela.
2. **COREDE** — lista só os COREDEs das regiões escolhidas; vazio = todos.

**Dentro da página — valem só para a pergunta dela**, e ficam junto do que mudam:

3. **Tercis · Quartis · Quintis** (pergunta 2) — quantos grupos de escolaridade usar no
   mapa e no gráfico de faixas.
   **Faixa de renda analisada** e **Destacar município** (pergunta 2, "Quem foge do
   padrão?") — qual faixa comparar com o esperado pela escolaridade (a base da renda, por
   padrão) e qual município marcar no gráfico, no ranking e no quadro-resumo.
4. **Só o tercil inferior de PIB per capita** (pergunta 4) — restringe a seleção.

Retas, grupos de escolaridade (tercis, quartis e quintis), quintis de renda, desvios-padrão e o tercil de PIB são calculados **uma vez,
sobre os 496 municípios**. O filtro só escolhe o que aparece; por isso um município
mantém sempre a mesma classe, e os números batem com a Atividade 01. Quando a
combinação de filtros não deixa nenhum município, o dashboard avisa em vez de mostrar
gráficos vazios.

## Instalação e execução

Requer Python 3.10 ou mais recente. A partir desta pasta (a que contém `app.py`):

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

O navegador abre em `http://localhost:8501`. Os dados já estão em `dados/`, então não
é preciso baixar nada; só as bibliotecas JavaScript do mapa (Leaflet) vêm da internet.

> Ao alterar `analise.py`, `comum.py`, os arquivos de gráficos ou `.streamlit/config.toml`,
> **pare o Streamlit (Ctrl+C) e rode `streamlit run app.py` de novo**: ele não recarrega
> os módulos importados pelas páginas nem o tema. Mudanças só em `paginas/` aparecem ao
> atualizar o navegador.

Para conferir que os cálculos reproduzem as Atividades 01 e 02 (correlação; limites e
faixas de renda dos quartis, dos tercis e dos quintis; os extremos e o desvio-padrão do
"Quem foge do padrão?"; medianas regionais; resíduos; o grupo de 13 municípios e os
p-valores do teste de permutação):

```bash
python analise.py
```

## Arquivos

```text
atividade02_dashboard_elizabeth/
├── .streamlit/config.toml    # tema: cor dos controles
├── app.py                    # entrada: navegação entre páginas + filtros da barra lateral
├── comum.py                  # peças de todas as páginas: cartões, mapa, tabela, rodapé
├── paginas/
│   ├── inicio.py             # público, as 4 perguntas, como usar
│   ├── p1_escolaridade_renda.py
│   ├── p2_faixas_de_renda.py
│   ├── p3_capital.py
│   └── p4_renda_producao.py
├── analise.py                # cálculos das 4 perguntas + autoverificação
├── graficos_atividade01.py   # gráficos da Atividade 01 (Matplotlib)
├── graficos_interativos.py   # Altair: dispersão da pergunta 1, faixas e "Quem foge do padrão?"
├── requirements.txt
└── dados/
    ├── municipios_web.geojson   # 497 municípios, indicadores de 2010
    └── regioes_web.geojson      # 9 Regiões Funcionais dissolvidas
```

Os dois GeoJSON são gerados pelo notebook `regioes_funcionais_rs.ipynb`, que está em
`../atividade02_lucas/`. Para refazê-los a partir das fontes oficiais, execute o notebook
inteiro: a seção 9 grava as cópias em `dados/` e registra a procedência de cada fonte
(URL, data e SHA-256) em `dados/regioes_funcionais/preparados/fontes_e_preparo.json`,
relativo à pasta do notebook.

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
- No "Quem foge do padrão?", a curva é uma só para o estado: um município "fora do
  padrão" está longe da média estadual para a sua escolaridade, o que indica onde
  olhar, não a causa. As faixas de renda são médias simples entre municípios.

## Nota técnica: por que o mapa não tem mapa-base

Os servidores de mosaicos do OpenStreetMap respondem **403 – Access blocked** a
pedidos sem cabeçalho `Referer`, como os de um HTML aberto com duplo clique ou de um
mapa exibido dentro do Jupyter. Como os polígonos cobrem todo o RS, o mapa usa
`tiles=None` e um fundo neutro: nada se perde na leitura e não há dependência de
servidor, conta ou chave de API.

## Nota técnica: a curva do "Quem foge do padrão?"

A fatia esperada é ajustada **uma vez, sobre os 496 municípios**, como as retas das
perguntas 1 e 4 (`afastamento_p2` em `analise.py`). Uma reta não serve aqui: a fatia é
uma porcentagem, e na base da renda a reta chega a −8,7% em Porto Alegre, que então
aparece como falso destaque. O ajuste é linear no logito da fatia, `log(p / (1 − p))`,
e a volta para % mantém a curva entre 0 e 100 — Porto Alegre passa a ter base esperada
de 5,1% e deixa de ser um extremo. O ajuste é tão bom quanto o da reta (R² 0,53 contra
0,52 na base da renda), e os extremos continuam os mesmos municípios. As classes usam o
mesmo critério de ±1 desvio-padrão das perguntas 1 e 4.
