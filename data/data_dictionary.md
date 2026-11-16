# Dicionário de dados

## Identificação e fonte

- **Pesquisa:** Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD Contínua), IBGE.
- **Fonte de extração:** API pública do SIDRA, variável 4099 (taxa de desocupação, em %).
- **Tabela 6381:** Brasil, série de trimestres móveis, com uma observação por mês de encerramento.
- **Tabela 4099:** Unidades da Federação, por trimestre civil.
- **População de referência:** pessoas de 14 anos ou mais de idade, conforme definição do indicador do IBGE.
- **Data de extração:** registrada no arquivo `data/raw/*.json` e em `data/processed/etl_log.json` a cada execução.

## Arquivo `taxa_desocupacao_brasil_trimestre_movel`

| Campo | Significado | Tipo | Unidade/formato |
|---|---|---|---|
| `data` | Primeiro dia do mês que encerra o trimestre móvel | datetime | AAAA-MM-DD |
| `ano` | Ano do mês de encerramento | inteiro | AAAA |
| `mes` | Mês de encerramento | inteiro | 1 a 12 |
| `taxa` | Taxa de desocupação publicada pelo SIDRA | numérico | % |
| `variacao_12m_pp` | Diferença entre a taxa e a observação de 12 meses antes | numérico | pontos percentuais (p.p.) |
| `desvio_sazonal_pp` | Diferença entre a taxa e a média das 12 observações do mesmo ano | numérico | p.p.; calculado apenas quando o ano tem 12 taxas válidas |

## Arquivo `taxa_desocupacao_uf_trimestral`

| Campo | Significado | Tipo | Unidade/formato |
|---|---|---|---|
| `territorio_cod` | Código IBGE da UF | texto | código territorial |
| `uf` | Nome da Unidade da Federação | texto | nome oficial no SIDRA |
| `regiao` | Grande Região derivada do primeiro dígito do código IBGE | texto | Norte, Nordeste, Sudeste, Sul ou Centro-Oeste |
| `ano` | Ano de referência | inteiro | AAAA |
| `trimestre` | Trimestre civil | inteiro | 1 a 4 |
| `periodo` | Rótulo do período | texto | AAAA-Tn |
| `taxa` | Taxa de desocupação publicada pelo SIDRA | numérico | % |

## Tratamento e valores ausentes

- O conteúdo recebido do SIDRA é preservado sem alteração em `data/raw/`.
- A coluna `V` é convertida para número, substituindo vírgula decimal por ponto antes da conversão.
- Marcadores não numéricos (por exemplo, `-`, `...` e `X`) são mantidos no arquivo bruto e convertidos em `NaN` no dado processado. A contagem e os marcadores encontrados são registrados em `etl_log.json`.
- Nenhuma observação é removida automaticamente por conter valor ausente.
- `variacao_12m_pp` e `desvio_sazonal_pp` são métricas derivadas pelo projeto, não variáveis publicadas diretamente pelo SIDRA.
- As médias regionais do notebook são médias simples das UFs e não são ponderadas pelo tamanho da força de trabalho.

## Formatos e licença

Os dados tratados são exportados em CSV comprimido (`.csv.gz`) e Parquet (`.parquet`). Os dados originais permanecem sujeitos às condições de uso e atribuição do IBGE. O código está sob MIT e o texto/dados derivados do projeto estão sob CC BY 4.0, conforme os arquivos de licença do repositório.
