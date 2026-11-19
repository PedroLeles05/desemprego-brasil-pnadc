# Taxa de desocupação no Brasil — PNAD Contínua (2012–2026)

**Projeto final:** Linguagem de Programação — Análise e Visualização de Dados com Python  
**Curso:** Bacharelado em Sistemas de Informação — 6º período  
**Instituição:** Unilasalle · **Semestre/ano:** 2026.2  
**Autores:** Pedro Henrique Leles Mello e Alvim ([GitHub](https://github.com/PedroLeles05)) e Gabriel Hierro Amorim dos Santos ([GitHub](https://github.com/gabrielhierro))  
**Professor:** Alexandre Neves Louzada

**Repositório do projeto:** [https://github.com/PedroLeles05/desemprego-brasil-pnadc](https://github.com/PedroLeles05/desemprego-brasil-pnadc)  
**Link do Pages:** [https://github.com/PedroLeles05/desemprego-brasil-pnadc](https://github.com/PedroLeles05/desemprego-brasil-pnadc)
**Clonar o projeto:** `git clone https://github.com/PedroLeles05/desemprego-brasil-pnadc.git`  
O endereço do GitHub Pages será divulgado após a ativação e publicação em **Settings → Pages**.

## Resumo

O projeto analisa a taxa de desocupação da PNAD Contínua em três dimensões: (RQ1) evolução nacional; (RQ2) diferenças entre Unidades da Federação e Grandes Regiões; e (RQ3) comportamento sazonal descritivo. Os dados são obtidos na API pública do SIDRA/IBGE, tratados com Python e apresentados em um artigo HTML com gráficos Plotly.

**Palavras-chave:** desocupação; PNAD Contínua; mercado de trabalho; análise exploratória; visualização de dados.

## Fonte dos dados

- [SIDRA — Tabela 6381](https://sidra.ibge.gov.br/tabela/6381): Brasil, trimestre móvel, variável 4099.
- [SIDRA — Tabela 4099](https://sidra.ibge.gov.br/tabela/4099): Unidades da Federação, trimestre civil, variável 4099.
- [Painel de indicadores do IBGE — Desemprego](https://www.ibge.gov.br/indicadores#desemprego).

A série nacional e a série estadual possuem granularidades diferentes: a tabela 6381 apresenta trimestres móveis com mês de encerramento; a tabela 4099 apresenta trimestres civis. O artigo e o notebook deixam essa diferença explícita.

## Como executar

Requisito: Python 3.12 e conexão com a internet na primeira execução.

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
python -m src.etl
jupyter notebook notebooks/analise_exploratoria.ipynb
```

Após instalar e testar o ambiente definitivo usado na entrega, gere o congelamento completo das dependências com `python -m pip freeze > requirements.txt`. O arquivo incluído lista as dependências diretas fixadas; o comando registra também as dependências transitivas instaladas no seu ambiente.

O ETL baixa e preserva os JSON originais em `data/raw/`, gera os dados tratados em CSV comprimido e Parquet em `data/processed/`, cria os JSON usados pelo artigo em `docs/assets/` e registra a extração em `data/processed/etl_log.json`.

Depois da primeira extração, é possível reproduzir o processamento sem consultar a internet:

```bash
python -m src.etl --offline
```

O modo offline exige que os dois arquivos brutos já existam em `data/raw/`; se algum estiver ausente, o programa encerra com erro em vez de acessar a internet silenciosamente.

Para visualizar o artigo localmente, execute em outro terminal:

```bash
python -m http.server -d docs 8000
```

Acesse `http://localhost:8000`.

## Estrutura

```text
├── README.md
├── LICENSE
├── LICENSE-CC-BY-4.0.md
├── requirements.txt
├── data/
│   ├── raw/                 # JSON originais do SIDRA (gerados pelo ETL)
│   ├── processed/           # CSV.gz, Parquet e log (gerados pelo ETL)
│   └── data_dictionary.md
├── notebooks/
│   └── analise_exploratoria.ipynb
├── src/
│   └── etl.py
└── docs/
    ├── index.html
    └── assets/              # JSON consumidos pelos gráficos (gerados pelo ETL)
```

## Reprodutibilidade e limitações

Os arquivos brutos preservam a resposta utilizada. O log registra data de extração, URL, hash SHA-256, quantidade de observações e marcadores não numéricos. Para reproduzir os resultados de uma versão, mantenha juntos os arquivos brutos e o código correspondente.

A análise é descritiva. As estimativas da PNAD Contínua estão sujeitas à incerteza amostral. As médias regionais do notebook são médias simples das UFs, não ponderadas pela força de trabalho. Trimestres móveis consecutivos compartilham dois meses.

## Publicação no GitHub Pages

O código-fonte está disponível no [repositório do projeto](https://github.com/PedroLeles05/desemprego-brasil-pnadc). Para publicar o artigo, abra **Settings → Pages**, selecione a branch principal e a pasta `/docs`. O endereço público do artigo depende da ativação do GitHub Pages no repositório.

## Licenças

- Código-fonte: MIT (`LICENSE`).
- Texto e dados derivados: CC BY 4.0 (`LICENSE-CC-BY-4.0.md`).
- Dados brutos: fonte IBGE/SIDRA; manter a atribuição à fonte original.
