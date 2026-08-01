import pandas as pd
import psycopg

# ------------------------------------------------------------------
# 1. LER O PARQUET
# ------------------------------------------------------------------
file = "D:/ESTUDOS/projetos/anp-fuel/data/precos.parquet"
df = pd.read_parquet(file)

# ------------------------------------------------------------------
# 2. SELECIONAR COLUNAS
# ------------------------------------------------------------------
colunas = [
    "Revenda",
    "CNPJ da Revenda",
    "Regiao - Sigla",
    "Estado - Sigla",
    "Municipio",
    "Bairro",
    "Cep",
    "Produto",
    "Data da Coleta",
    "Valor de Venda",
    "Unidade de Medida",
    "Bandeira",
    "ano_ref",
    "semestre_ref",
]
df = df[colunas]
print("Selecionadas as colunas do dataframe...")

# ------------------------------------------------------------------
# 3. RENOMEAR COLUNAS
# ------------------------------------------------------------------
df = df.rename(
    columns={
        "Regiao - Sigla": "regiao",
        "Estado - Sigla": "uf",
        "Municipio": "cidade",
        "Revenda": "revenda",
        "CNPJ da Revenda": "cnpj",
        "Bairro": "bairro",
        "Cep": "cep",
        "Produto": "produto",
        "Data da Coleta": "data_coleta",
        "Valor de Venda": "valor_venda",
        "Unidade de Medida": "unidade_medida",
        "Bandeira": "bandeira",
    }
)
print("Colunas do dataframe renomeadas...")

# ------------------------------------------------------------------
# 4. NORMALIZAR E CONVERTER
# ------------------------------------------------------------------
df["cnpj"] = df["cnpj"].str.replace(r"\D", "", regex=True)
df["data_coleta"] = pd.to_datetime(df["data_coleta"], format="%d/%m/%Y")
print("Colunas normalizadas e convertidas...")

# ------------------------------------------------------------------
# 5. REMOVER LINHAS NULAS
# ------------------------------------------------------------------
antes = len(df)
df = df.dropna(subset=["uf", "bairro", "produto", "data_coleta", "valor_venda"])
print(f"Removidas {antes - len(df)} linhas nulas...")

print(f"O Dataframe possui {df.shape[0]} linhas e {df.shape[1]} colunas.\n")

# ------------------------------------------------------------------
# 6. CONECTAR AO POSTGRES (uma conexão só, fechada apenas no final)
# ------------------------------------------------------------------
conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="anp_fuel",
    user="postgres",
    password="123456",
)
cur = conn.cursor()
print("✔ Conectado ao PostgreSQL.")

# ------------------------------------------------------------------
# 7. CRIAR A TABELA (se ainda não existir)
# ------------------------------------------------------------------
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS precos_combustiveis (
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
# 8. PREPARAR OS DADOS E INSERIR
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
registros = list(df[cols_insert].itertuples(index=False, name=None))

cur.executemany(
    """
    INSERT INTO precos_combustiveis
        (revenda, cnpj, regiao, uf, cidade, bairro, cep,
         produto, data_coleta, valor_venda, unidade_medida,
         bandeira, ano_ref, semestre_ref)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """,
    registros,
)

# ------------------------------------------------------------------
# 9. CONFIRMAR E FECHAR
# ------------------------------------------------------------------
conn.commit()
cur.close()
conn.close()

print(f"✔ {len(registros):,} linhas inseridas em precos_combustiveis")
