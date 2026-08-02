"""
load.py — Carga no PostgreSQL
Lê o Parquet tratado (Silver) e carrega na tabela precos_combustiveis.
Nenhuma regra de negócio/limpeza acontece aqui — apenas movimentação.

Pré-requisitos:
  - PostgreSQL rodando em localhost:5432
  - Database anp_fuel criado (CREATE DATABASE anp_fuel;)
  - transform.py executado (data/silver/precos_tratado.parquet existente)

Execução: python src/load.py (a partir da raiz do projeto)
"""

from pathlib import Path
import pandas as pd
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()  # lê o .env da raiz do projeto para as variáveis de ambiente

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# ------------------------------------------------------------------
# 0. CAMINHOS E CONFIGURAÇÃO
# ------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_SILVER = RAIZ / "data" / "silver" / "precos_tratado.parquet"

# ⚠ Para estudo local. Antes de subir ao GitHub, mover para um .env!
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "anp_fuel",
    "user": "postgres",
    "password": "123456",
}

TABELA = "precos_combustiveis"

# ------------------------------------------------------------------
# 1. LER O SILVER
# ------------------------------------------------------------------
df = pd.read_parquet(ARQUIVO_SILVER)
print(f"Silver lido: {df.shape[0]:,} linhas e {df.shape[1]} colunas.")

# ------------------------------------------------------------------
# 2. CONECTAR AO POSTGRES (uma conexão, fechada apenas no final)
# ------------------------------------------------------------------
conn = psycopg.connect(**DB_CONFIG)
cur = conn.cursor()
print("✔ Conectado ao PostgreSQL.")

# ------------------------------------------------------------------
# 3. CRIAR A TABELA (idempotente: IF NOT EXISTS)
# ------------------------------------------------------------------
cur.execute(
    f"""
    CREATE TABLE IF NOT EXISTS {TABELA} (
        id             SERIAL PRIMARY KEY,
        revenda        TEXT,
        cnpj           VARCHAR(14),
        regiao         VARCHAR(2),
        uf             VARCHAR(2),
        cidade         TEXT,
        bairro         TEXT,
        cep            VARCHAR(10),
        produto        TEXT,
        data_coleta    DATE,
        valor_venda    NUMERIC(10, 3),
        unidade_medida TEXT,
        bandeira       TEXT,
        ano_ref        INTEGER,
        semestre_ref   INTEGER
    );
    """
)

# ------------------------------------------------------------------
# 4. LIMPAR A TABELA (carga full: o banco espelha o Silver a cada rodada)
# ------------------------------------------------------------------
cur.execute(f"TRUNCATE TABLE {TABELA};")
print("Tabela truncada — iniciando a carga...")

# ------------------------------------------------------------------
# 5. PREPARAR OS DADOS E INSERIR EM LOTE
# ------------------------------------------------------------------
cols_insert = [
    "revenda",
    "cnpj",
    "regiao",
    "uf",
    "cidade",
    "bairro",
    "cep",
    "produto",
    "data_coleta",
    "valor_venda",
    "unidade_medida",
    "bandeira",
    "ano_ref",
    "semestre_ref",
]

# lista de tuplas puras, na MESMA ordem das colunas do INSERT
registros = list(df[cols_insert].itertuples(index=False, name=None))

cur.executemany(
    f"""
    INSERT INTO {TABELA}
        (revenda, cnpj, regiao, uf, cidade, bairro, cep,
         produto, data_coleta, valor_venda, unidade_medida,
         bandeira, ano_ref, semestre_ref)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """,
    registros,
)

# ------------------------------------------------------------------
# 6. CONFIRMAR A TRANSAÇÃO E FECHAR
# ------------------------------------------------------------------
conn.commit()
cur.close()
conn.close()

print(f"✔ {len(registros):,} linhas inseridas em {TABELA}.")
print("  Confira no banco: SELECT COUNT(*) FROM precos_combustiveis;")
