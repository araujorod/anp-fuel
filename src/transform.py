"""
transform.py — Camada Silver
Lê o Parquet bruto (Bronze), aplica limpeza/padronização e grava o
Parquet tratado (Silver). Nenhuma conexão com banco acontece aqui.

Execução: python src/transform.py (a partir da raiz do projeto)
"""

from pathlib import Path

import pandas as pd

# ------------------------------------------------------------------
# 0. CAMINHOS (relativos à raiz do projeto, imunes à pasta de execução)
# ------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent  # sobe de src/ para anp-fuel/
ARQUIVO_BRONZE = RAIZ / "data" / "bronze" / "precos_raw.parquet"
ARQUIVO_SILVER = RAIZ / "data" / "silver" / "precos_tratado.parquet"

# ------------------------------------------------------------------
# 1. LER O BRONZE
# ------------------------------------------------------------------
df = pd.read_parquet(ARQUIVO_BRONZE)
print(f"Bronze lido: {len(df):,} linhas.")

# ------------------------------------------------------------------
# 2. SELECIONAR COLUNAS (seleção explícita = contrato de dados)
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
# 3. RENOMEAR COLUNAS (snake_case, pronto para o banco)
# ------------------------------------------------------------------
df = df.rename(
    columns={
        "Revenda": "revenda",
        "CNPJ da Revenda": "cnpj",
        "Regiao - Sigla": "regiao",
        "Estado - Sigla": "uf",
        "Municipio": "cidade",
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
# CNPJ: manter apenas dígitos (continua string, para preservar zeros à esquerda)
df["cnpj"] = df["cnpj"].str.replace(r"\D", "", regex=True)

# Data: string dd/mm/aaaa -> tipo datetime64 (formato interno, sem "formato visual")
df["data_coleta"] = pd.to_datetime(df["data_coleta"], format="%d/%m/%Y")

# Padronizar categóricos (evita "GASOLINA " vs "GASOLINA" em GROUP BY futuros)
df["produto"] = df["produto"].str.strip().str.upper()
df["uf"] = df["uf"].str.strip().str.upper()
print("Colunas normalizadas e convertidas...")

# ------------------------------------------------------------------
# 5. REMOVER LINHAS NULAS NAS COLUNAS OBRIGATÓRIAS
# ------------------------------------------------------------------
antes = len(df)
df = df.dropna(subset=["uf", "bairro", "produto", "data_coleta", "valor_venda"])
print(f"Removidas {antes - len(df):,} linhas nulas...")

# ------------------------------------------------------------------
# 6. VALIDAÇÕES (falhar cedo e alto, antes de gravar o Silver)
# ------------------------------------------------------------------
# 6.1 Nulos residuais em colunas obrigatórias
obrigatorias = ["cnpj", "uf", "produto", "data_coleta", "valor_venda"]
nulos = df[obrigatorias].isna().sum()
assert nulos.sum() == 0, f"Nulos em colunas obrigatórias:\n{nulos[nulos > 0]}"

# 6.2 Preços inválidos (combustível não tem preço zero ou negativo)
invalidos = (df["valor_venda"] <= 0).sum()
assert invalidos == 0, f"{invalidos} linhas com valor_venda <= 0"

# 6.3 Datas fora do intervalo plausível da série da ANP
fora = df[
    (df["data_coleta"] < "2004-01-01") | (df["data_coleta"] > pd.Timestamp.today())
]
assert len(fora) == 0, f"{len(fora)} linhas com data_coleta fora do intervalo"

# 6.4 CNPJ sem 14 dígitos: apenas alerta (não bloqueia a carga)
cnpj_ruim = (df["cnpj"].str.len() != 14).sum()
if cnpj_ruim > 0:
    print(f"⚠ Atenção: {cnpj_ruim:,} CNPJs sem 14 dígitos (verificar origem).")

print("✔ Validações concluídas sem erros.")

# ------------------------------------------------------------------
# 6.5 DEDUPLICAR PELA CHAVE DE NEGÓCIO (agregando por média)
# ------------------------------------------------------------------
# A fonte (ANP) ocasionalmente reporta mais de um preço para o mesmo
# posto+produto+dia (ex.: duas amostragens na mesma semana). Como não há
# timestamp de hora para desempatar, consolidamos por média — mesma lógica
# de agregação já usada nos modelos Gold (AVG(valor_venda)).
chave_negocio = ["cnpj", "produto", "data_coleta"]

antes_dedup = len(df)
duplicatas = df.duplicated(subset=chave_negocio, keep=False).sum()

if duplicatas > 0:
    print(
        f"⚠ {duplicatas:,} linhas duplicadas na chave (cnpj+produto+data_coleta) — agregando por média..."
    )
    colunas_agrupar = [c for c in df.columns if c != "valor_venda"]
    df = df.groupby(colunas_agrupar, as_index=False, dropna=False)["valor_venda"].mean()
    print(f"  {antes_dedup - len(df):,} linhas consolidadas.")

# Garantia: a chave de negócio deve ser única após a deduplicação
restantes = df.duplicated(subset=chave_negocio).sum()
assert (
    restantes == 0
), f"Ainda há {restantes} duplicatas na chave de negócio após deduplicação"

# ------------------------------------------------------------------
# 7. GRAVAR O SILVER
# ------------------------------------------------------------------
ARQUIVO_SILVER.parent.mkdir(parents=True, exist_ok=True)  # cria data/silver se faltar
df.to_parquet(ARQUIVO_SILVER, index=False)

print(f"✔ Silver gravado em {ARQUIVO_SILVER}")
print(f"  {df.shape[0]:,} linhas e {df.shape[1]} colunas.")
