### Estrutura do arquivo

**Verificar:** O CSV tem uma linha em branco (separador) cheia de espaços em vez de vazio de verdade, e isso faz o pandas ler colunas inteiras como texto em vez de número — qualquer correlação ou média vai quebrar ou dar resultado errado até vocês limparem essas linhas e converter com pd.to_numeric(..., errors='coerce'). Vale documentar isso na seção de "Carregamento dos dados".

### Colunas Válidas

Tirando as 432 colunas de "Desagregação", sobram 72 (mais a coluna `Territorialidades`). Mas dessas 72, a maioria também está vazia no nível municipal — só um núcleo pequeno é realmente utilizável:

**Cobertura 100% (14 colunas, todas do Censo 2010 + PIB 2013-2016)**:

% ensino médio completo, rendimento médio, % sem rendimento, % até 1/2/3/5 salários mínimos, % água encanada, esperança de vida ao nascer, mortalidade infantil (todas 2010) + PIB per capita 2013, 2014, 2015 e 2016.

**Cobertura parcial boa (~78-81%, 5 colunas)** — série de 2013 a 2017:

Existência de coleta seletiva.

**Uma coluna isolada 100%:** Média de anos de estudo 2018 — a única entre as 13 colunas anuais (2012-2024) dessa família que tem dado municipal de verdade.

**Praticamente inúteis no nível municipal (0% a 1,6% preenchido, ~52 colunas):** todas as 12 outras colunas de "Média de anos de estudo", "% de 25+ com ensino médio", "% de 18-20 com ensino médio" (todos os anos), "Renda per capita dos pobres" e "IDHM Educação" (todos os anos). Essas séries existem no arquivo mas só têm valor em nível Brasil/RS — no nível de município ficam quase sempre em branco.
