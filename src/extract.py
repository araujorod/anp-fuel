"""
extract.py — Camada Bronze (incremental)
Baixa os arquivos semestrais de preços da ANP e grava em Parquet (Bronze).

Modo incremental: se já existe um Bronze gravado, o script detecta o último
ano/semestre presente e baixa somente os períodos publicados depois dele —
sem reprocessar o histórico inteiro a cada execução.

Execução: python src/extract.py (a partir da raiz do projeto)
"""

from datetime import date
from pathlib import Path

import pandas as pd

# ------------------------------------------------------------------
# 0. CAMINHOS E CONFIGURAÇÃO
# ------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_BRONZE = RAIZ / "data" / "bronze" / "precos_raw.parquet"

# Usado apenas quando NÃO existe Bronze anterior (primeira execução do zero).
ANO_INICIO_PADRAO = 2020

URL_BASE = (
    "https://www.gov.br/anp/pt-br/centrais-de-conteudo/"
    "dados-abertos/arquivos/shpc/dsas/ca/ca-{ano}-0{semestre}.zip"
)


# ------------------------------------------------------------------
# 1. HELPERS DE PERÍODO (ano/semestre)
# ------------------------------------------------------------------
def semestre_atual(hoje: date | None = None) -> tuple[int, int]:
    """Retorna (ano, semestre) correspondente à data de hoje."""
    hoje = hoje or date.today()
    return hoje.year, (1 if hoje.month <= 6 else 2)


def proximo_semestre(ano: int, semestre: int) -> tuple[int, int]:
    """Avança um período: (2024, 1) -> (2024, 2) -> (2025, 1) ..."""
    return (ano, 2) if semestre == 1 else (ano + 1, 1)


def gerar_periodos(
    inicio: tuple[int, int], fim: tuple[int, int]
) -> list[tuple[int, int]]:
    """Lista todos os (ano, semestre) entre inicio e fim, inclusive."""
    periodos = []
    atual = inicio
    while atual <= fim:
        periodos.append(atual)
        atual = proximo_semestre(*atual)
    return periodos


# ------------------------------------------------------------------
# 2. DESCOBRIR O PONTO DE PARTIDA (o que já temos no Bronze)
# ------------------------------------------------------------------
bronze_existente = None
if ARQUIVO_BRONZE.exists():
    bronze_existente = pd.read_parquet(ARQUIVO_BRONZE)
    ultimo_ano = int(bronze_existente["ano_ref"].max())
    ultimo_semestre = int(
        bronze_existente.loc[
            bronze_existente["ano_ref"] == ultimo_ano, "semestre_ref"
        ].max()
    )
    inicio = proximo_semestre(ultimo_ano, ultimo_semestre)
    print(
        f"Bronze existente: {len(bronze_existente):,} linhas. "
        f"Último período: {ultimo_ano}-{ultimo_semestre:02d}."
    )
else:
    inicio = (ANO_INICIO_PADRAO, 1)
    print("Nenhum Bronze existente — carga completa desde o início configurado.")

fim = semestre_atual()
periodos = gerar_periodos(inicio, fim)

if not periodos:
    print(f"✔ Nada a fazer — Bronze já está atualizado até {fim[0]}-{fim[1]:02d}.")
    raise SystemExit(0)

print(
    f"Períodos a verificar: {periodos[0][0]}-{periodos[0][1]:02d} "
    f"até {periodos[-1][0]}-{periodos[-1][1]:02d} ({len(periodos)} período(s))."
)


# ------------------------------------------------------------------
# 3. BAIXAR OS PERÍODOS NOVOS
# ------------------------------------------------------------------
dfs_novos: list = []

for ano, semestre in periodos:
    url = URL_BASE.format(ano=ano, semestre=semestre)
    try:
        df_semestre = pd.read_csv(
            url,
            sep=";",
            encoding="utf-8",
            decimal=",",
            dtype={"CNPJ da Revenda": str},
        )
        df_semestre["ano_ref"] = ano
        df_semestre["semestre_ref"] = semestre

        dfs_novos.append(df_semestre)
        print(f"OK   -> {ano}-{semestre:02d}: {len(df_semestre):,} linhas")
    except Exception as e:
        # Arquivo ainda não publicado (comum para o semestre corrente em
        # andamento) ou instabilidade pontual na URL — não é erro fatal.
        print(f"ERRO -> {ano}-{semestre:02d}: {e}")

if not dfs_novos:
    print("✔ Nenhum período novo disponível para download no momento.")
    raise SystemExit(0)

df_novo = pd.concat(dfs_novos, ignore_index=True)
print(f"\nBaixados agora: {len(df_novo):,} linhas | {df_novo.shape[1]} colunas")

# ------------------------------------------------------------------
# 4. CONSOLIDAR COM O BRONZE EXISTENTE
# ------------------------------------------------------------------
if bronze_existente is not None:
    df_final = pd.concat([bronze_existente, df_novo], ignore_index=True)
else:
    df_final = df_novo

print(f"Bronze final: {len(df_final):,} linhas | {df_final.shape[1]} colunas")

# ------------------------------------------------------------------
# 5. GRAVAR O BRONZE ATUALIZADO
# ------------------------------------------------------------------
ARQUIVO_BRONZE.parent.mkdir(parents=True, exist_ok=True)
df_final.to_parquet(ARQUIVO_BRONZE, index=False)

print(f"✔ Bronze gravado em {ARQUIVO_BRONZE}")
