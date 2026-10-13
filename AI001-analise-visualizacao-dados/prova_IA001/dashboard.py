"""Dashboard da prova IA001 — oferta do Airbnb no Rio de Janeiro e público estrangeiro.

Execução: streamlit run dashboard.py

Lê listings.csv e os dois agregados gerados por preparar_dados.py
(reviews_idioma_anuncio.csv e reviews_idioma_bairro_mes.csv), todos na mesma pasta.

Interações:
- filtro global de tipo de acomodação (vale para os quatro gráficos e os indicadores);
- clique nos bairros do gráfico 1 para compará-los no gráfico 2 e localizá-los no gráfico 3;
- clique na legenda dos gráficos 2, 3 e 4 para isolar uma série;
- passe o cursor nos gráficos 3 e 4 para comparar as duas origens no mesmo ponto;
- controles próprios de cada gráfico logo acima dele.
"""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

PASTA = Path(__file__).parent
ARQ_LISTINGS = PASTA / 'listings.csv'
ARQ_ANUNCIO = PASTA / 'reviews_idioma_anuncio.csv'
ARQ_BAIRRO_MES = PASTA / 'reviews_idioma_bairro_mes.csv'

TIPOS = {
    'Entire home/apt': 'Imóvel inteiro',
    'Private room': 'Quarto privativo',
    'Shared room': 'Quarto compartilhado',
    'Hotel room': 'Quarto de hotel',
}
ORLA_ZONA_SUL = ['Copacabana', 'Ipanema', 'Leblon', 'Leme']
BAIRROS_PADRAO = ['Ipanema', 'Copacabana', 'Barra da Tijuca', 'Centro']
MAX_BAIRROS_DESTAQUE = 4  # limite de séries com cores distinguíveis
FAIXAS = ['Q1 (mais baratos)', 'Q2', 'Q3', 'Q4 (mais caros)']
MAX_BAIRROS_CURVA = 15
ALTURA_GRAFICO = 420
MIN_ANUNCIOS_QUARTIL = 20  # abaixo disso os quartis de preço de um bairro não são confiáveis
ORDENACOES = {'Preço mediano': 'mediana', 'Número de anúncios': 'anuncios'}
GRANULARIDADES = {'Trimestral': 'Q', 'Mensal': 'M'}
SELECAO_BAIRROS = 'bairros_clicados'

# A mesma cor sempre representa a mesma série, como no notebook
COR_UNICA = '#2a78d6'
COR_NEUTRA = '#8a8984'
ORIGENS = ['Doméstico (português)', 'Estrangeiro (outros idiomas)']
CORES_ORIGEM = ['#2a78d6', '#eb6834']
CORES_BAIRRO = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']

alt.data_transformers.disable_max_rows()


@st.cache_data
def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve a base por anúncio (listings + idioma das avaliações) e a série mensal por bairro."""
    listings = pd.read_csv(ARQ_LISTINGS)
    idioma_anuncio = pd.read_csv(ARQ_ANUNCIO)
    idioma_bairro_mes = pd.read_csv(ARQ_BAIRRO_MES)

    anuncios = listings.merge(idioma_anuncio, left_on='id', right_on='listing_id', how='left')
    colunas = ['n_domestico', 'n_estrangeiro']
    anuncios[colunas] = anuncios[colunas].fillna(0).astype(int)
    anuncios['n_classificadas'] = anuncios['n_domestico'] + anuncios['n_estrangeiro']
    anuncios['pct_estrangeiro'] = (
        anuncios['n_estrangeiro'] / anuncios['n_classificadas']
    ).where(anuncios['n_classificadas'] > 0)
    return anuncios, idioma_bairro_mes


def curvas_de_concentracao(anuncios: pd.DataFrame) -> pd.DataFrame:
    """Participação acumulada das avaliações por bairro; cada origem tem o seu próprio ranking."""
    por_bairro = anuncios.groupby('neighbourhood')[['n_domestico', 'n_estrangeiro']].sum()
    curvas = []
    for coluna, origem in zip(['n_domestico', 'n_estrangeiro'], ORIGENS):
        ordenado = por_bairro[coluna].sort_values(ascending=False)
        if ordenado.sum() == 0:
            continue
        participacao = ordenado / ordenado.sum()
        curvas.append(pd.DataFrame({
            'origem': origem,
            'posicao': range(1, len(ordenado) + 1),
            'bairro': ordenado.index,
            'participacao': participacao.values,
            'acumulado': participacao.cumsum().values,
        }))
    return pd.concat(curvas) if curvas else pd.DataFrame()


def bairros_para_nivel(curvas: pd.DataFrame, origem: str, nivel: float) -> int | None:
    """Quantos bairros, do mais ao menos avaliado, somam a participação `nivel` (0 a 1)."""
    curva = curvas[curvas['origem'] == origem] if not curvas.empty else curvas
    return int((curva['acumulado'] < nivel).sum() + 1) if len(curva) else None


def isolar_pela_legenda(campo: str, nome: str):
    """Seleção ligada à legenda: clicar em um item esmaece as outras séries."""
    selecao = alt.selection_point(name=nome, fields=[campo], bind='legend')
    return selecao, alt.condition(selecao, alt.value(1), alt.value(0.12))


def grafico_preco_bairro(anuncios: pd.DataFrame, min_anuncios: int, ordenar_por: str):
    com_preco = anuncios[anuncios['price'].notna()]
    dados = (
        com_preco.groupby('neighbourhood')['price']
        .agg(anuncios='size', q1=lambda s: s.quantile(0.25), mediana='median', q3=lambda s: s.quantile(0.75))
        .reset_index()
    )
    dados = dados[dados['anuncios'] >= min_anuncios]
    if dados.empty:
        return None, dados

    # o domínio acompanha os dados filtrados para o intervalo nunca sair do eixo
    minimo, maximo = dados['q1'].min() * 0.85, dados['q3'].max() * 1.15
    dados = dados.assign(minimo=minimo, maximo=maximo)
    eixo = alt.Scale(type='log', domain=[minimo, maximo])
    marcas = [v for v in (20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000) if minimo <= v <= maximo]

    # cada clique liga ou desliga um bairro; clicar fora dos bairros limpa a seleção
    clique = alt.selection_point(name=SELECAO_BAIRROS, fields=['neighbourhood'], toggle='true')
    destaque = alt.condition(clique, alt.value(1), alt.value(0.25))

    base = alt.Chart(dados).encode(
        y=alt.Y('neighbourhood:N', sort=alt.EncodingSortField(ordenar_por, order='descending'), title='Bairro',
                axis=alt.Axis(labelOverlap=False, labelLimit=0)),
        tooltip=[
            alt.Tooltip('neighbourhood:N', title='Bairro'),
            alt.Tooltip('anuncios:Q', title='Anúncios', format=','),
            alt.Tooltip('q1:Q', title='1º quartil (R$)', format=',.0f'),
            alt.Tooltip('mediana:Q', title='Mediana (R$)', format=',.0f'),
            alt.Tooltip('q3:Q', title='3º quartil (R$)', format=',.0f'),
        ],
    )
    faixa = base.mark_rule(strokeWidth=3, color=COR_UNICA).encode(
        x=alt.X('q1:Q', scale=eixo, title='Preço da diária (R$, escala logarítmica)',
                axis=alt.Axis(format=',.0f', values=marcas)),
        x2='q3:Q',
        opacity=alt.condition(clique, alt.value(0.35), alt.value(0.1)),
    )
    ponto = base.mark_point(size=70, filled=True, color=COR_UNICA).encode(
        x=alt.X('mediana:Q', scale=eixo), opacity=destaque,
    )
    # faixa invisível na largura toda: a linha inteira do bairro é clicável, não só o ponto
    area_de_clique = base.mark_rule(strokeWidth=20, opacity=0, cursor='pointer').encode(
        x=alt.X('minimo:Q', scale=eixo), x2='maximo:Q',
    ).add_params(clique)
    grafico = (faixa + ponto + area_de_clique).properties(height=alt.Step(22))
    return grafico, dados.drop(columns=['minimo', 'maximo']).sort_values(ordenar_por, ascending=False)


def grafico_estrangeiro_por_preco(anuncios: pd.DataFrame, bairros: list[str], min_avaliacoes: int):
    dados = anuncios[
        anuncios['price'].notna() & (anuncios['n_classificadas'] >= min_avaliacoes)
        & anuncios['neighbourhood'].isin(bairros)
    ].copy()
    # só entram bairros com anúncios suficientes para formar quatro faixas de preço
    tamanho = dados['neighbourhood'].value_counts()
    dados = dados[dados['neighbourhood'].isin(tamanho[tamanho >= MIN_ANUNCIOS_QUARTIL].index)]
    if dados.empty:
        return None, dados

    # o quartil é calculado dentro de cada bairro; rank(method='first') evita falha com preços repetidos
    dados['faixa_preco'] = dados.groupby('neighbourhood')['price'].transform(
        lambda preco: pd.qcut(preco.rank(method='first'), 4, labels=FAIXAS)
    ).astype(str)
    resumo = (
        dados.groupby(['neighbourhood', 'faixa_preco'])
        .agg(pct_estrangeiro=('pct_estrangeiro', 'mean'), anuncios=('id', 'size'), preco_mediano=('price', 'median'))
        .reset_index()
    )
    # a cor segue o bairro (posição na seleção), não o resultado do filtro
    presentes = [b for b in bairros if b in set(resumo['neighbourhood'])]
    cores = [CORES_BAIRRO[bairros.index(b)] for b in presentes]
    legenda, opacidade = isolar_pela_legenda('neighbourhood', 'legenda_g2')

    grafico = alt.Chart(resumo).mark_line(
        strokeWidth=2, point=alt.OverlayMarkDef(size=70, filled=True)
    ).encode(
        x=alt.X('faixa_preco:N', sort=FAIXAS, title='Faixa de preço dentro do bairro (quartis)',
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y('pct_estrangeiro:Q', title=['Avaliações em idioma estrangeiro', '(média por anúncio)'],
                scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format='.0%')),
        color=alt.Color('neighbourhood:N', title='Bairro (clique para isolar)', sort=presentes,
                        scale=alt.Scale(domain=presentes, range=cores), legend=alt.Legend(orient='bottom', labelLimit=0)),
        opacity=opacidade,
        tooltip=[
            alt.Tooltip('neighbourhood:N', title='Bairro'),
            alt.Tooltip('faixa_preco:N', title='Faixa de preço'),
            alt.Tooltip('pct_estrangeiro:Q', title='Avaliações estrangeiras', format='.1%'),
            alt.Tooltip('preco_mediano:Q', title='Preço mediano (R$)', format=',.0f'),
            alt.Tooltip('anuncios:Q', title='Anúncios', format=','),
        ],
    ).add_params(legenda).properties(height=ALTURA_GRAFICO)
    return grafico, resumo


def grafico_concentracao(curvas: pd.DataFrame, nivel: float, bairros_destaque: list[str], marcar_destaques: bool):
    dados = curvas[curvas['posicao'] <= MAX_BAIRROS_CURVA]
    legenda, opacidade = isolar_pela_legenda('origem', 'legenda_g3')
    eixo_x = alt.X('posicao:Q', title=['Número de bairros', '(do mais ao menos avaliado por cada grupo)'],
                   scale=alt.Scale(domain=[1, MAX_BAIRROS_CURVA], nice=False),
                   axis=alt.Axis(values=list(range(1, MAX_BAIRROS_CURVA + 1)), format='d', grid=False))
    eixo_y = alt.Y('acumulado:Q', title=['Participação acumulada', 'nas avaliações do grupo'],
                   scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format='.0%'))
    cor = alt.Color('origem:N', title='Origem (clique para isolar)', sort=ORIGENS,
                    scale=alt.Scale(domain=ORIGENS, range=CORES_ORIGEM), legend=alt.Legend(orient='bottom', labelLimit=0))

    linhas = alt.Chart(dados).mark_line(
        strokeWidth=2, point=alt.OverlayMarkDef(size=60, filled=True)
    ).encode(x=eixo_x, y=eixo_y, color=cor, opacity=opacidade).add_params(legenda)

    referencia = alt.Chart(pd.DataFrame({'y': [nivel]})).mark_rule(strokeDash=[4, 4], color=COR_NEUTRA).encode(y='y:Q')

    # régua vertical: ao passar o cursor, compara as duas origens na mesma posição do ranking
    lado_a_lado = dados.pivot(index='posicao', columns='origem', values=['bairro', 'acumulado'])
    lado_a_lado.columns = [f'{medida}_{"dom" if origem == ORIGENS[0] else "est"}' for medida, origem in lado_a_lado.columns]
    lado_a_lado = lado_a_lado.reset_index()
    colunas_dica = [alt.Tooltip('posicao:Q', title='Posição no ranking')]
    for sufixo, rotulo in (('dom', 'Doméstico'), ('est', 'Estrangeiro')):
        if f'bairro_{sufixo}' in lado_a_lado:
            colunas_dica += [
                alt.Tooltip(f'bairro_{sufixo}:N', title=f'{rotulo}: bairro'),
                alt.Tooltip(f'acumulado_{sufixo}:Q', title=f'{rotulo}: acumulado', format='.1%'),
            ]
    cursor = alt.selection_point(name='cursor_g3', on='pointerover', nearest=True, fields=['posicao'],
                                 empty=False, clear='pointerout')
    regua = alt.Chart(lado_a_lado).mark_rule(color=COR_NEUTRA, strokeWidth=1).encode(
        x='posicao:Q', opacity=alt.condition(cursor, alt.value(0.7), alt.value(0)), tooltip=colunas_dica,
    ).add_params(cursor)

    camadas = [referencia, linhas, regua]
    destacados = dados[dados['bairro'].isin(bairros_destaque)]
    if marcar_destaques and len(destacados):
        # anel em volta dos pontos que correspondem aos bairros em destaque (os nomes vão na tabela abaixo do gráfico)
        camadas.append(alt.Chart(destacados).mark_point(size=190, filled=False, strokeWidth=2).encode(
            x='posicao:Q', y='acumulado:Q', color=alt.Color('origem:N', legend=None),
        ))
    return alt.layer(*camadas).properties(height=ALTURA_GRAFICO)


def grafico_area_no_tempo(serie_mensal: pd.DataFrame, area: list[str], frequencia: str, periodo: tuple[str, str]):
    serie = serie_mensal[(serie_mensal['mes'] >= periodo[0]) & (serie_mensal['mes'] <= periodo[1])].copy()
    serie['periodo'] = pd.PeriodIndex(serie['mes'], freq=frequencia).start_time
    serie['na_area'] = serie['neighbourhood'].isin(area)
    serie = serie.melt(
        id_vars=['periodo', 'na_area'], value_vars=['n_domestico', 'n_estrangeiro'],
        var_name='origem', value_name='avaliacoes',
    )
    serie['origem'] = serie['origem'].map(dict(zip(['n_domestico', 'n_estrangeiro'], ORIGENS)))
    total = serie.groupby(['periodo', 'origem'])['avaliacoes'].sum().rename('avaliacoes')
    na_area = serie[serie['na_area']].groupby(['periodo', 'origem'])['avaliacoes'].sum().rename('na_area')
    dados = pd.concat([total, na_area], axis=1).fillna(0).reset_index()
    dados = dados[dados['avaliacoes'] > 0]
    if dados.empty:
        return None, dados
    dados['pct_area'] = dados['na_area'] / dados['avaliacoes']

    legenda, opacidade = isolar_pela_legenda('origem', 'legenda_g4')
    rotulo_periodo = 'Trimestre' if frequencia == 'Q' else 'Mês'
    linhas = alt.Chart(dados).mark_line(
        strokeWidth=2, point=alt.OverlayMarkDef(size=50, filled=True)
    ).encode(
        x=alt.X('periodo:T', title=f'{rotulo_periodo} da avaliação' + (' (mês de início)' if frequencia == 'Q' else ''),
                axis=alt.Axis(format='%m/%Y', tickCount=8, grid=False)),
        y=alt.Y('pct_area:Q', title=['Avaliações em anúncios', 'da área de referência'],
                scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format='.0%')),
        color=alt.Color('origem:N', title='Origem (clique para isolar)', sort=ORIGENS,
                        scale=alt.Scale(domain=ORIGENS, range=CORES_ORIGEM), legend=alt.Legend(orient='bottom', labelLimit=0)),
        opacity=opacidade,
    ).add_params(legenda)

    # régua vertical: compara as duas origens no mesmo período
    lado_a_lado = dados.pivot(index='periodo', columns='origem', values=['pct_area', 'avaliacoes'])
    lado_a_lado.columns = [f'{medida}_{"dom" if origem == ORIGENS[0] else "est"}' for medida, origem in lado_a_lado.columns]
    lado_a_lado = lado_a_lado.reset_index()
    colunas_dica = [alt.Tooltip('periodo:T', title=rotulo_periodo, format='%m/%Y')]
    for sufixo, rotulo in (('dom', 'Doméstico'), ('est', 'Estrangeiro')):
        if f'pct_area_{sufixo}' in lado_a_lado:
            colunas_dica += [
                alt.Tooltip(f'pct_area_{sufixo}:Q', title=f'{rotulo}: na área', format='.1%'),
                alt.Tooltip(f'avaliacoes_{sufixo}:Q', title=f'{rotulo}: avaliações', format=',.0f'),
            ]
    cursor = alt.selection_point(name='cursor_g4', on='pointerover', nearest=True, fields=['periodo'],
                                 empty=False, clear='pointerout')
    regua = alt.Chart(lado_a_lado).mark_rule(color=COR_NEUTRA, strokeWidth=1).encode(
        x='periodo:T', opacity=alt.condition(cursor, alt.value(0.7), alt.value(0)), tooltip=colunas_dica,
    ).add_params(cursor)
    return (linhas + regua).properties(height=ALTURA_GRAFICO), dados


def posicoes_dos_destaques(curvas: pd.DataFrame, bairros: list[str]) -> pd.DataFrame:
    """Posição e participação de cada bairro em destaque no ranking de cada origem."""
    destacados = curvas[curvas['bairro'].isin(bairros)]
    tabela = destacados.pivot(index='bairro', columns='origem', values=['posicao', 'participacao'])
    saida = pd.DataFrame(index=[b for b in bairros if b in tabela.index])
    for origem, rotulo in zip(ORIGENS, ['doméstico', 'estrangeiro']):
        if ('posicao', origem) in tabela:
            saida[f'Posição ({rotulo})'] = tabela[('posicao', origem)].astype('Int64')
            saida[f'Participação ({rotulo}, %)'] = (tabela[('participacao', origem)] * 100).round(1)
    return saida.rename_axis('Bairro').reset_index()


def bairros_clicados(evento) -> list[str]:
    """Extrai os bairros selecionados por clique no gráfico 1 (lista vazia se não houver)."""
    try:
        pontos = evento['selection'][SELECAO_BAIRROS]
    except (KeyError, TypeError):
        return []
    return [p['neighbourhood'] for p in pontos if isinstance(p, dict) and 'neighbourhood' in p]


def cabecalho(titulo: str, subtitulo: str) -> None:
    st.markdown(f'**{titulo}**')
    st.caption(subtitulo)


def formatar_inteiro(valor: float) -> str:
    return f'{valor:,.0f}'.replace(',', '.')


def formatar_mes(mes: str) -> str:
    return f'{mes[5:]}/{mes[:4]}'


st.set_page_config(page_title='Airbnb Rio — público estrangeiro', layout='wide')

faltando = [arq.name for arq in (ARQ_LISTINGS, ARQ_ANUNCIO, ARQ_BAIRRO_MES) if not arq.exists()]
if faltando:
    st.error(
        f'Arquivo(s) ausente(s) na pasta do dashboard: {", ".join(faltando)}. '
        'Os agregados reviews_idioma_*.csv são gerados por: python preparar_dados.py'
    )
    st.stop()

anuncios, idioma_bairro_mes = carregar_dados()
bairros_por_tamanho = anuncios['neighbourhood'].value_counts().index.tolist()

# ---------------------------------------------------------------- filtros globais
st.sidebar.header('Filtros')
tipos = st.sidebar.multiselect(
    'Tipo de acomodação', options=list(TIPOS), default=['Entire home/apt'], format_func=TIPOS.get,
    help='Aplica-se aos quatro gráficos e aos indicadores.',
)
bairros_escolhidos = st.sidebar.multiselect(
    'Bairros em destaque', options=bairros_por_tamanho, default=BAIRROS_PADRAO,
    max_selections=MAX_BAIRROS_DESTAQUE,
    help='Comparados no gráfico 2 e localizados no gráfico 3. Clicar em bairros no gráfico 1 substitui esta lista.',
)
area_referencia = st.sidebar.multiselect(
    'Área de referência (gráfico 4)', options=bairros_por_tamanho, default=ORLA_ZONA_SUL,
    help='O gráfico 4 mostra a parcela das avaliações que fica nestes bairros. Padrão: orla da Zona Sul.',
)
st.sidebar.caption(
    'Origem do hóspede estimada pelo idioma do comentário: português = doméstico; '
    'demais idiomas = estrangeiro. Idioma não é nacionalidade.'
)
st.sidebar.markdown(
    '**Como interagir**\n'
    '- Clique em bairros no gráfico 1 para compará-los no gráfico 2 e localizá-los no gráfico 3; '
    'clique fora deles para limpar.\n'
    '- Clique na legenda dos gráficos 2, 3 e 4 para isolar uma série.\n'
    '- Passe o cursor nos gráficos 3 e 4 para comparar as duas origens.'
)

st.title('Airbnb no Rio de Janeiro: preço, território e público estrangeiro')
st.caption('Inside Airbnb, coleta de junho de 2026 — 48.729 anúncios. Prova IA001, UFRGS.')
st.caption(
    'O filtro "Tipo de acomodação" vale para os quatro gráficos. No notebook, os gráficos 1 e 2 usam imóveis '
    'inteiros e os gráficos 3 e 4 usam todos os tipos; selecione os quatro tipos para reproduzir os gráficos 3 e 4.'
)

if not tipos:
    st.warning('Selecione pelo menos um tipo de acomodação.')
    st.stop()

rotulo_tipo = TIPOS[tipos[0]].lower() if len(tipos) == 1 else (
    'todos os tipos' if len(tipos) == len(TIPOS) else f'{len(tipos)} tipos de acomodação'
)
filtrados = anuncios[anuncios['room_type'].isin(tipos)]
serie_filtrada = idioma_bairro_mes[idioma_bairro_mes['room_type'].isin(tipos)]
curvas = curvas_de_concentracao(filtrados)

indicadores = st.container()  # preenchido no fim, porque depende do nível de referência do gráfico 3

# ---------------------------------------------------------------- pergunta 1
st.header('Pergunta 1 — O preço varia entre bairros, e os anúncios mais caros atendem mais estrangeiros?')
esquerda, direita = st.columns(2)

with esquerda:
    controle_a, controle_b = st.columns(2)
    min_anuncios = controle_a.slider(
        'Mínimo de anúncios por bairro', min_value=30, max_value=500, value=100, step=10,
        help='Bairros com menos anúncios com preço ficam fora do gráfico 1.',
    )
    ordenacao = controle_b.selectbox('Ordenar bairros por', options=list(ORDENACOES))
    cabecalho(
        f'Gráfico 1 — Preço da diária por bairro ({rotulo_tipo})',
        f'Ponto = mediana; barra = do 1º ao 3º quartil. Bairros com pelo menos {min_anuncios} anúncios com preço. '
        'Clique em um bairro para destacá-lo.',
    )
    grafico, tabela = grafico_preco_bairro(filtrados, min_anuncios, ORDENACOES[ordenacao])
    clicados = []
    if grafico is None:
        st.info('Nenhum bairro atinge o mínimo de anúncios com preço nesta seleção.')
    else:
        evento = st.altair_chart(
            grafico, width='stretch', on_select='rerun', selection_mode=SELECAO_BAIRROS, key='grafico_1',
        )
        clicados = bairros_clicados(evento)
        with st.expander('Ver dados do gráfico 1'):
            st.dataframe(
                tabela.rename(columns={'neighbourhood': 'Bairro', 'anuncios': 'Anúncios', 'q1': '1º quartil',
                                       'mediana': 'Mediana', 'q3': '3º quartil'}),
                hide_index=True, width='stretch',
            )

# os cliques no gráfico 1 têm prioridade sobre a lista da barra lateral
bairros_destaque = (clicados or bairros_escolhidos)[:MAX_BAIRROS_DESTAQUE]

with direita:
    controle_a, controle_b = st.columns(2)
    min_avaliacoes = controle_a.slider(
        'Mínimo de avaliações por anúncio', min_value=1, max_value=20, value=5,
        help='Avaliações com idioma identificado nos últimos 12 meses.',
    )
    with controle_b:
        if clicados:
            st.caption(
                f'Bairros vindos dos cliques no gráfico 1: {", ".join(bairros_destaque)}.'
                + (f' Só os {MAX_BAIRROS_DESTAQUE} primeiros são usados.' if len(clicados) > MAX_BAIRROS_DESTAQUE else '')
            )
        else:
            st.caption('Bairros vindos da lista "Bairros em destaque" da barra lateral.')
    cabecalho(
        f'Gráfico 2 — Avaliações estrangeiras por faixa de preço ({rotulo_tipo})',
        f'Anúncios com pelo menos {min_avaliacoes} avaliações classificadas entre jul/2025 e jun/2026. '
        'O resultado vale para os bairros em destaque.',
    )
    if not bairros_destaque:
        st.info('Selecione ao menos um bairro na barra lateral ou clique em um bairro no gráfico 1.')
    else:
        grafico, tabela = grafico_estrangeiro_por_preco(filtrados, bairros_destaque, min_avaliacoes)
        if grafico is None:
            st.info(f'Nenhum bairro em destaque tem {MIN_ANUNCIOS_QUARTIL} anúncios ou mais com avaliações suficientes.')
        else:
            st.altair_chart(grafico, width='stretch')
            sem_dados = [b for b in bairros_destaque if b not in set(tabela['neighbourhood'])]
            if sem_dados:
                st.caption(f'Sem anúncios suficientes nesta seleção: {", ".join(sem_dados)}.')
            with st.expander('Ver dados do gráfico 2'):
                st.dataframe(
                    tabela.assign(pct_estrangeiro=(tabela['pct_estrangeiro'] * 100).round(1)).rename(columns={
                        'neighbourhood': 'Bairro', 'faixa_preco': 'Faixa de preço',
                        'pct_estrangeiro': 'Avaliações estrangeiras (%)', 'anuncios': 'Anúncios',
                        'preco_mediano': 'Preço mediano',
                    }),
                    hide_index=True, width='stretch',
                )

# ---------------------------------------------------------------- pergunta 2
st.header('Pergunta 2 — O turismo estrangeiro se concentra em menos bairros, e isso está diminuindo?')
esquerda, direita = st.columns(2)

with esquerda:
    controle_a, controle_b = st.columns(2)
    nivel = controle_a.slider(
        'Nível de referência da concentração (%)', min_value=50, max_value=95, value=80, step=5,
        help='Quantos bairros são necessários para somar esta parcela das avaliações de cada grupo.',
    ) / 100
    marcar_destaques = controle_b.toggle('Marcar bairros em destaque', value=True)
    cabecalho(
        f'Gráfico 3 — Concentração das avaliações por bairro ({rotulo_tipo})',
        f'Avaliações classificadas entre jul/2025 e jun/2026. Cada grupo tem o seu próprio ranking de bairros. '
        f'Linha tracejada = {nivel:.0%} das avaliações.',
    )
    if curvas.empty:
        st.info('Não há avaliações classificadas nesta seleção.')
    else:
        st.altair_chart(grafico_concentracao(curvas, nivel, bairros_destaque, marcar_destaques), width='stretch')
        if marcar_destaques and bairros_destaque:
            st.caption('Bairros em destaque (pontos com anel) e a posição de cada um no ranking das duas origens:')
            st.dataframe(posicoes_dos_destaques(curvas, bairros_destaque), hide_index=True, width='stretch')
        with st.expander('Ver dados do gráfico 3'):
            tabela = curvas[curvas['posicao'] <= MAX_BAIRROS_CURVA]
            st.dataframe(
                tabela.assign(participacao=(tabela['participacao'] * 100).round(1),
                              acumulado=(tabela['acumulado'] * 100).round(1)).rename(columns={
                    'origem': 'Origem', 'posicao': 'Posição', 'bairro': 'Bairro',
                    'participacao': 'Participação (%)', 'acumulado': 'Acumulado (%)',
                }),
                hide_index=True, width='stretch',
            )

with direita:
    meses = sorted(idioma_bairro_mes['mes'].unique())
    controle_a, controle_b = st.columns([1, 2])
    granularidade = controle_a.radio('Agregação', options=list(GRANULARIDADES), horizontal=True)
    periodo = controle_b.select_slider(
        'Período das avaliações', options=meses, value=(meses[0], meses[-1]), format_func=formatar_mes,
    )
    rotulo_area = 'orla da Zona Sul' if set(area_referencia) == set(ORLA_ZONA_SUL) else 'área de referência'
    cabecalho(
        f'Gráfico 4 — Participação da {rotulo_area} nas avaliações ({rotulo_tipo})',
        f'Área de referência = {", ".join(area_referencia) if area_referencia else "nenhum bairro"}. '
        f'Avaliações de {formatar_mes(periodo[0])} a {formatar_mes(periodo[1])}.',
    )
    if not area_referencia:
        st.info('Selecione ao menos um bairro em "Área de referência" na barra lateral.')
    else:
        grafico, tabela = grafico_area_no_tempo(serie_filtrada, area_referencia, GRANULARIDADES[granularidade], periodo)
        if grafico is None:
            st.info('Não há avaliações classificadas nesta seleção.')
        else:
            st.altair_chart(grafico, width='stretch')
            with st.expander('Ver dados do gráfico 4'):
                st.dataframe(
                    tabela.assign(periodo=tabela['periodo'].dt.strftime('%m/%Y'),
                                  pct_area=(tabela['pct_area'] * 100).round(1))[
                        ['periodo', 'origem', 'pct_area', 'avaliacoes']
                    ].rename(columns={'periodo': 'Início do período', 'origem': 'Origem',
                                      'pct_area': 'Na área de referência (%)', 'avaliacoes': 'Avaliações'}),
                    hide_index=True, width='stretch',
                )

# ---------------------------------------------------------------- indicadores (topo da página)
total_classificadas = filtrados['n_classificadas'].sum()
n_estrangeiro = bairros_para_nivel(curvas, ORIGENS[1], nivel)
n_domestico = bairros_para_nivel(curvas, ORIGENS[0], nivel)

with indicadores:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Anúncios', formatar_inteiro(len(filtrados)))
    c2.metric(
        'Diária mediana',
        f'R$ {formatar_inteiro(filtrados["price"].median())}' if filtrados['price'].notna().any() else '—',
    )
    c3.metric(
        'Avaliações estrangeiras (12 meses)',
        f'{filtrados["n_estrangeiro"].sum() / total_classificadas:.1%}'.replace('.', ',') if total_classificadas else '—',
    )
    c4.metric(
        f'Bairros para {nivel:.0%} das avaliações',
        f'{n_estrangeiro} e {n_domestico}' if n_estrangeiro and n_domestico else '—',
        help='Número de bairros que somam essa parcela das avaliações: estrangeiras e domésticas, nessa ordem.',
    )
    c4.caption('estrangeiras e domésticas')
