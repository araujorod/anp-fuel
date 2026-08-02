# ⛽ anp-fuel — Pipeline de Preços de Combustíveis (ANP)

Pipeline de dados completo (ELT) que ingere a **Série Histórica de Preços de
Combustíveis** da ANP (Agência Nacional do Petróleo), organiza os dados em
**arquitetura medalhão** (Bronze → Silver → Gold) e disponibiliza tabelas
analíticas prontas para consulta no PostgreSQL, com transformações
gerenciadas e testadas via **dbt**.

## 🏗 Arquitetura

```
ANP (gov.br)
   │
   │  extract.py          (download dos CSVs semestrais)
   ▼
🥉 Bronze — data/bronze/precos_raw.parquet          [dado cru, fiel à fonte]
   │
   │  transform.py        (limpeza, tipos, validações)
   ▼
🥈 Silver — data/silver/precos_tratado.parquet      [dado limpo e validado]
   │
   │  load.py             (carga full idempotente)
   ▼
🥈 Silver no PostgreSQL — precos_combustiveis       [~2,9M linhas]
   │
   │  dbt run + dbt test  (modelagem analítica em SQL)
   ▼
🥇 Gold — 4 modelos analíticos                      [prontos para consumo]
```

## 📊 Camada Gold

| Modelo | Pergunta que responde | Técnicas SQL |
|---|---|---|
| `gold_preco_mensal_uf` | Qual o preço médio/mín/máx mensal por UF e produto? | Agregações, `DATE_TRUNC` |
| `gold_ranking_bandeiras` | Qual a participação de mercado de cada bandeira por UF? | Window functions (`RANK`, `SUM OVER`) |
| `gold_etanol_vs_gasolina` | Quando o etanol compensa? (regra dos 70%) | CTEs, pivot com `CASE WHEN` |
| `gold_variacao_mensal` | Como o preço variou mês a mês? | `LAG`, séries temporais |

## 🛠 Stack

- **Python 3.14** — gerenciado com [`uv`](https://docs.astral.sh/uv/)
- **pandas + pyarrow** — extração e transformação (camadas Bronze/Silver)
- **Apache Parquet** — formato colunar das camadas de arquivo
- **PostgreSQL 18** — data warehouse local
- **psycopg 3** — driver de conexão e carga
- **dbt (dbt-postgres)** — modelagem, testes e documentação da camada Gold

## 📁 Estrutura do projeto

```
anp-fuel/
├── src/
│   └── setup_db.py         # Criação do banco de dados (roda 1x)
│   ├── extract.py          # ANP → Bronze (parquet)
│   ├── transform.py        # Bronze → Silver (limpeza + validações)
│   └── load.py             # Silver → PostgreSQL
├── dbt/
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/        # sources + stg_precos (view)
│       └── marts/          # modelos gold (tables)
├── data/                   # bronze/ e silver/ (fora do Git)
├── .env.example            # template das credenciais
└── pyproject.toml
```

## 🚀 Como executar

### Pré-requisitos

- Python 3.14+ e [`uv`](https://docs.astral.sh/uv/) instalados
- PostgreSQL rodando em `localhost:5432`

### Setup

```bash
# 1. Clonar e instalar dependências
git clone https://github.com/araujorod/anp-fuel.git
cd anp-fuel
uv sync

# 2. Criar o database
psql -U postgres -h localhost -c "CREATE DATABASE anp_fuel;"

# 3. Configurar credenciais
copy .env.example .env      # e editar com seu usuário/senha

# 4. Configurar o profile do dbt em ~/.dbt/profiles.yml
#    (ver dbt/README ou documentação do dbt-postgres)
```

### Pipeline

```bash
uv run python src/extract.py     # baixa os semestres da ANP → Bronze
uv run python src/transform.py   # limpa e valida → Silver
uv run python src/load.py        # carrega no PostgreSQL

cd dbt
uv run dbt run                   # materializa staging + gold
uv run dbt test                  # valida a qualidade dos dados
```

## 🧠 Decisões técnicas

**Parquet como camada intermediária.** As camadas Bronze e Silver usam
Parquet em vez de CSV: formato colunar comprimido, preserva tipos de dados
entre etapas e permite leitura seletiva de colunas. O Bronze funciona como
"backup fiel" da fonte — mudanças de regra de transformação não exigem novo
download da ANP.

**Seleção explícita de colunas (contrato de dados).** O `transform.py`
seleciona as colunas por lista explícita em vez de `drop()`. Se a ANP
renomear ou adicionar colunas, o pipeline falha imediatamente com erro claro
na fronteira de entrada — em vez de propagar dados inesperados até o banco.

**Validações que falham cedo.** Antes de gravar o Silver, asserts verificam
nulos em campos obrigatórios, preços não positivos, datas fora do intervalo
da série (2004–hoje) e CNPJs malformados. Dado inválido interrompe o
pipeline em vez de contaminar as análises.

**psycopg 3 em vez de psycopg2.** Além de ser o sucessor oficial, o psycopg2
no Windows com locale pt-BR mascara erros de conexão com `UnicodeDecodeError`
ilegível — o psycopg 3 reporta os erros reais.

**Carga full idempotente.** O `load.py` faz `TRUNCATE` + `INSERT`: executar
o pipeline N vezes produz o mesmo estado final, sem duplicação. A evolução
natural (carga incremental com chave de negócio `cnpj + produto +
data_coleta`) está no roadmap.

**ELT com dbt para a camada analítica.** As transformações Silver → Gold
acontecem dentro do PostgreSQL, via SQL versionado no dbt — que resolve o
grafo de dependências entre modelos, aplica testes declarativos
(`not_null`, `accepted_values`) e gera documentação com linhagem. A
fronteira escolhida: saneamento em pandas (ingestão), modelagem analítica em
SQL (dbt).

**Ambientes por projeto com uv.** Cada dependência é declarada no
`pyproject.toml` e instalada no `.venv` do projeto — reprodutível com um
`uv sync`. O cache global do uv (hard links) elimina o custo de duplicação
em disco.

## 🗺 Roadmap

- [ ] Modelagem dimensional (star schema): `dim_posto`, `dim_produto`,
      `dim_tempo`, `fato_coleta`
- [ ] Carga incremental (upsert com `ON CONFLICT` / dbt incremental)
- [ ] PostgreSQL containerizado com Docker Compose
- [ ] Orquestração com Apache Airflow
- [ ] Dashboard analítico (Metabase ou Streamlit)

## 📚 Fonte dos dados

[Série Histórica de Preços de Combustíveis — ANP](https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis)
— pesquisa semanal de preços de revendedores, publicada semestralmente
(dados abertos, Lei nº 9.478/1997).