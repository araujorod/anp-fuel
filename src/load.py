"""
load.py — Carga incremental no PostgreSQL
Lê o Parquet tratado (Silver) e carrega na tabela precos_combustiveis via
UPSERT (INSERT ... ON CONFLICT): linhas novas são inseridas, linhas já
existentes (mesma chave de negócio) têm o valor atualizado — sem duplicar
e sem precisar apagar a tabela a cada execução.

Pré-requisitos:
  - PostgreSQL rodando (local ou container)
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
# 3.1 GARANTIR A CONSTRAINT DE UNICIDADE (idempotente)
# ------------------------------------------------------------------
# Postgres não tem "ADD CONSTRAINT IF NOT EXISTS" nativo; o bloco DO abaixo
# verifica no catálogo (pg_constraint) antes de criar, para o script poder
# ser executado repetidas vezes sem erro (ex.: banco recriado do zero).
cur.execute(
    f"""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'uq_coleta'
        ) THEN
            ALTER TABLE {TABELA}
            ADD CONSTRAINT uq_coleta UNIQUE (cnpj, produto, data_coleta);
        END IF;
    END $$;
    """
)

# ------------------------------------------------------------------
# 4. PREPARAR OS DADOS E FAZER O UPSERT (INSERT ... ON CONFLICT)
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

print(f"Iniciando upsert de {len(registros):,} linhas...")

cur.executemany(
    f"""
    INSERT INTO {TABELA}
        (revenda, cnpj, regiao, uf, cidade, bairro, cep,
         produto, data_coleta, valor_venda, unidade_medida,
         bandeira, ano_ref, semestre_ref)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (cnpj, produto, data_coleta) DO UPDATE SET
        revenda        = EXCLUDED.revenda,
        regiao         = EXCLUDED.regiao,
        uf             = EXCLUDED.uf,
        cidade         = EXCLUDED.cidade,
        bairro         = EXCLUDED.bairro,
        cep            = EXCLUDED.cep,
        valor_venda    = EXCLUDED.valor_venda,
        unidade_medida = EXCLUDED.unidade_medida,
        bandeira       = EXCLUDED.bandeira,
        ano_ref        = EXCLUDED.ano_ref,
        semestre_ref   = EXCLUDED.semestre_ref
    """,
    registros,
)

# ------------------------------------------------------------------
# 5. CONFIRMAR A TRANSAÇÃO E FECHAR
# ------------------------------------------------------------------
conn.commit()
cur.close()
conn.close()

print(
    f"✔ {len(registros):,} linhas processadas (inseridas ou atualizadas) em {TABELA}."
)
print("  Confira no banco: SELECT COUNT(*) FROM precos_combustiveis;")
