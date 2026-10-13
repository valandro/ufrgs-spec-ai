"""Preparação dos dados derivados de reviews.csv — prova IA001.

Uso:
    python preparar_dados.py            # baixa reviews.csv.gz se necessário e gera os agregados
    python preparar_dados.py --forcar   # recalcula os agregados mesmo que já existam

O que faz:
1. Procura reviews.csv ou reviews.csv.gz nesta pasta; se não houver, baixa reviews.csv.gz
   (cerca de 155 MB) do Inside Airbnb, coleta de 24/06/2026 do Rio de Janeiro.
2. Classifica o idioma de cada comentário (indicador aproximado da origem do hóspede:
   português = doméstico; qualquer outro idioma identificado = estrangeiro).
3. Grava dois arquivos pequenos, lidos por analise.ipynb e dashboard.py:
   - reviews_idioma_anuncio.csv: avaliações domésticas e estrangeiras por anúncio (jul/2025 a jun/2026);
   - reviews_idioma_bairro_mes.csv: as mesmas contagens por mês, bairro e tipo de acomodação (desde jul/2022).

Requer listings.csv na mesma pasta. Fonte: https://insideairbnb.com/get-the-data/ (licença CC BY 4.0).
"""
import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
URL_REVIEWS = 'https://data.insideairbnb.com/brazil/rj/rio-de-janeiro/2026-06-24/data/reviews.csv.gz'

ARQ_LISTINGS = PASTA / 'listings.csv'
ARQ_REVIEWS_CSV = PASTA / 'reviews.csv'
ARQ_REVIEWS_GZ = PASTA / 'reviews.csv.gz'
ARQ_ANUNCIO = PASTA / 'reviews_idioma_anuncio.csv'        # 1 linha por anúncio (últimos 12 meses)
ARQ_BAIRRO_MES = PASTA / 'reviews_idioma_bairro_mes.csv'  # 1 linha por mês x bairro x tipo de acomodação

INICIO_12M = '2025-07-01'    # janela dos gráficos 2 e 3: jul/2025 a jun/2026
INICIO_SERIE = '2022-07-01'  # início da série do gráfico 4 (após o período de pandemia)
COLUNAS_REVIEWS = ['listing_id', 'date', 'comments']
BLOCO_DOWNLOAD = 1024 * 1024  # 1 MB
TEMPO_LIMITE_S = 60

# Palavras funcionais de cada idioma. O idioma com mais ocorrências vence;
# empate ou menos de 2 ocorrências fica como 'indefinido' e sai da análise.
PALAVRAS = {
    'pt': 'não muito muita uma com você também ótimo ótima foi bem localização apartamento tudo mais são '
          'estadia anfitrião anfitriã recomendo perto tem obrigado obrigada limpo ficamos fiquei boa bom '
          'lugar do da em e o os as ao pra voltarei',
    'es': 'muy el los las y una ubicación departamento fue cerca pero gracias también anfitrión anfitriona '
          'limpio bien estadía hay playa del al nos lo estuvo estancia volvería súper lugar es en',
    'en': 'the and was is very great place location we to of with in for it stay host clean this had are '
          'apartment would recommend',
    'fr': 'très et le les est nous avec appartement pour dans un une pas propre séjour emplacement merci '
          'je du des bien situé',
    'de': 'und die der das sehr ist wir war mit wohnung lage nicht gut auch ein eine ich zu',
    'it': 'molto è il di che posizione appartamento siamo stato ottimo ottima pulito grazie per vicino '
          'della anche con una e',
}
OUTRO_ALFABETO = r'[Ѐ-ӿ֐-׿؀-ۿ぀-ヿ一-鿿가-힯]'


def localizar_reviews() -> Path | None:
    """Devolve o arquivo de avaliações já presente na pasta (CSV ou CSV compactado), se houver."""
    for caminho in (ARQ_REVIEWS_CSV, ARQ_REVIEWS_GZ):
        if caminho.exists():
            return caminho
    return None


def baixar_reviews(url: str = URL_REVIEWS, destino: Path = ARQ_REVIEWS_GZ) -> Path:
    """Baixa reviews.csv.gz para `destino`, gravando primeiro em arquivo temporário."""
    parcial = destino.parent / (destino.name + '.part')
    # o servidor recusa o agente padrão do urllib em algumas redes; um User-Agent explícito evita o bloqueio
    requisicao = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (prova IA001; preparar_dados.py)'})
    print(f'Baixando {url}')
    try:
        with urllib.request.urlopen(requisicao, timeout=TEMPO_LIMITE_S) as resposta, open(parcial, 'wb') as saida:
            esperado = int(resposta.headers.get('Content-Length') or 0)
            recebido = 0
            proximo_aviso = 0
            while bloco := resposta.read(BLOCO_DOWNLOAD):
                saida.write(bloco)
                recebido += len(bloco)
                if recebido >= proximo_aviso:
                    total = f' de {esperado / 1e6:.0f} MB' if esperado else ''
                    print(f'  {recebido / 1e6:.0f} MB{total}')
                    proximo_aviso += 25 * BLOCO_DOWNLOAD
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        parcial.unlink(missing_ok=True)
        raise RuntimeError(
            f'Não foi possível baixar {url} ({erro}). Baixe o arquivo manualmente em '
            f'https://insideairbnb.com/get-the-data/ (Rio de Janeiro, reviews.csv.gz) e salve-o em {destino.parent}.'
        ) from erro

    # um download interrompido geraria agregados incompletos sem nenhum erro aparente
    if esperado and recebido != esperado:
        parcial.unlink(missing_ok=True)
        raise RuntimeError(f'Download incompleto: {recebido} de {esperado} bytes. Execute novamente.')
    parcial.replace(destino)
    print(f'Salvo em {destino.name} ({recebido / 1e6:.0f} MB)')
    return destino


def classificar_idioma(comentarios: pd.Series) -> pd.Series:
    """Devolve 'pt', 'es', 'en', 'fr', 'de', 'it', 'outro' ou 'indefinido' para cada comentário."""
    texto = comentarios.fillna('').str.lower().str.replace(r'<br\s*/?>', ' ', regex=True)
    contagem = pd.DataFrame({
        idioma: texto.str.count(r'(?<!\w)(?:' + '|'.join(map(re.escape, palavras.split())) + r')(?!\w)')
        for idioma, palavras in PALAVRAS.items()
    })
    maior = contagem.max(axis=1)
    segundo = np.sort(contagem.values, axis=1)[:, -2]
    idioma = contagem.idxmax(axis=1).where((maior >= 2) & (maior > segundo), 'indefinido')
    return idioma.mask(texto.str.contains(OUTRO_ALFABETO), 'outro')


def gerar_agregados(caminho_reviews: Path) -> None:
    """Lê as avaliações, classifica o idioma e grava os dois arquivos usados no notebook e no dashboard."""
    listings = pd.read_csv(ARQ_LISTINGS, usecols=['id', 'neighbourhood', 'room_type'])

    print(f'Lendo {caminho_reviews.name}')
    reviews = pd.read_csv(caminho_reviews, usecols=COLUNAS_REVIEWS, parse_dates=['date'])  # .gz é lido direto
    total = len(reviews)
    reviews = reviews[reviews['date'] >= INICIO_SERIE].copy()

    print(f'Classificando o idioma de {len(reviews):,} comentários (de {total:,} no arquivo)')
    reviews['idioma'] = classificar_idioma(reviews['comments'])
    classificadas = reviews[reviews['idioma'] != 'indefinido'].copy()
    # português = doméstico; qualquer outro idioma identificado = estrangeiro
    classificadas['n_estrangeiro'] = (classificadas['idioma'] != 'pt').astype(int)
    classificadas['n_domestico'] = 1 - classificadas['n_estrangeiro']
    colunas = ['n_domestico', 'n_estrangeiro']

    (classificadas[classificadas['date'] >= INICIO_12M]
        .groupby('listing_id')[colunas].sum().reset_index()
        .to_csv(ARQ_ANUNCIO, index=False))

    classificadas = classificadas.merge(listings, left_on='listing_id', right_on='id')
    classificadas['mes'] = classificadas['date'].dt.strftime('%Y-%m')
    (classificadas.groupby(['mes', 'neighbourhood', 'room_type'])[colunas].sum().reset_index()
        .to_csv(ARQ_BAIRRO_MES, index=False))

    print(f'Comentários com idioma identificado: {len(classificadas):,} ({len(classificadas) / len(reviews):.1%}); '
          f'estrangeiros: {classificadas["n_estrangeiro"].mean():.1%}')
    print(f'Gravados: {ARQ_ANUNCIO.name} e {ARQ_BAIRRO_MES.name}')


def garantir_agregados(forcar: bool = False, url: str = URL_REVIEWS) -> None:
    """Gera os agregados se faltarem (ou se `forcar`), baixando as avaliações quando não estão na pasta."""
    if not forcar and ARQ_ANUNCIO.exists() and ARQ_BAIRRO_MES.exists():
        print('Agregados já existem; nada a fazer (use --forcar para recalcular).')
        return
    # conferido antes do download, para não baixar 155 MB e só então falhar
    if not ARQ_LISTINGS.exists():
        raise FileNotFoundError(f'{ARQ_LISTINGS.name} precisa estar em {PASTA}.')
    gerar_agregados(localizar_reviews() or baixar_reviews(url))


def main() -> int:
    parser = argparse.ArgumentParser(description='Baixa reviews.csv.gz do Inside Airbnb e gera os agregados de idioma.')
    parser.add_argument('--forcar', action='store_true', help='recalcula os agregados mesmo que já existam')
    parser.add_argument('--url', default=URL_REVIEWS, help='endereço alternativo de reviews.csv.gz')
    argumentos = parser.parse_args()
    try:
        garantir_agregados(forcar=argumentos.forcar, url=argumentos.url)
    except (RuntimeError, FileNotFoundError) as erro:
        print(f'Erro: {erro}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
