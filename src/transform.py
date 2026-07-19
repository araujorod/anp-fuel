import pandas as pd
import psycopg2
import psycopg
from psycopg2.extras import execute_values

# lê o arquivo Parquet e cria o DataFrame
file = "D:/ESTUDOS/projetos/anp-fuel/data/precos.parquet"
df = pd.read_parquet(file)

# carregando apenas as colunas desejadas

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

# carregando apenas as colunas desejadas

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
print("Colunas do dataframde renomeadas...")

# Normalizar o CNPJ

df["cnpj"] = df["cnpj"].str.replace(r"\D", "", regex=True)

# Converter campo data coleta para formada Date

df["data_coleta"] = pd.to_datetime(df["data_coleta"], format="%d/%m/%Y")
print("Colunas normalizadas e convertidas...")

# Verificar colunas invalidas

# print(df.isna().sum())  # quantos nulos por coluna
# print(
#     df[df["uf"].isna()]
# )  # ver as linhas onde uf é nula (com todas as colunas, para entender o padrão)


# Elimina as colunas inválidas

antes = len(df)
df = df.dropna(subset=["uf", "bairro", "produto", "data_coleta", "valor_venda"])
print(f"Removidas {antes - len(df)} linhas nulas...")


# Valida dados únicos
# valores categóricos devem pertencer a um conjunto conhecido

# print(df["produto"].unique())
# print(df["uf"].unique())
# print(df["regiao"].unique())


# conferindo a leitura

print(f"O Dataframe possui {df.shape[0]} linhas e {df.shape[1]} Colunas.\n")
# print(df.dtypes, "\n")  # tipo de cada coluna
# # print(df.head(5), end="\n\n")
# print(df)


# 2. CONECTAR AO POSTGRES

try:
    conn = psycopg.connect(
        host="localhost",
        port=5432,
        dbname="anp_fuel",
        user="postgres",
        password="123456",
    )
    print("✔ CONEXÃO OK:", conn.execute("SELECT version();").fetchone()[0])
    conn.close()
except Exception as e:
    print("✘ ERRO REAL:", e)

cur = conn.cursor()

# CRIAR A TABELA (se ainda não existir)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS anp_fuel (
        id           SERIAL PRIMARY KEY,
        # revenda      TEXT,
        # cnpj         VARCHAR(14),
        # regiao       VARCHAR(2),
        # uf           VARCHAR(2),
        # cidade       TEXT,
        # produto      TEXT,
        # data_coleta  DATE,
        # valor_venda  NUMERIC(10, 3),
        # bandeira     TEXT
    );
"""
)

# # ------------------------------------------------------------------
# # 4. PREPARAR OS DADOS E INSERIR EM LOTE
# # ------------------------------------------------------------------
# colunas = ["revenda", "cnpj", "regiao", "uf", "cidade",
#            "produto", "data_coleta", "valor_venda", "bandeira"]

# registros = list(df[colunas].itertuples(index=False, name=None))

# execute_values(
#     cur,
#     """
#     INSERT INTO precos_combustiveis
#         (revenda, cnpj, regiao, uf, cidade, produto, data_coleta, valor_venda, bandeira)
#     VALUES %s
#     """,
#     registros,
#     page_size=10_000,
# )

# # ------------------------------------------------------------------
# # 5. CONFIRMAR A TRANSAÇÃO E FECHAR
# # ------------------------------------------------------------------
# conn.commit()
# cur.close()
# conn.close()

# print(f"✔ {len(registros):,} linhas inseridas em precos_combustiveis")
