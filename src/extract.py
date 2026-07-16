import pandas as pd
import pyarrow


def carregar_precos(ano_inicio: int, ano_fim: int) -> pd.DataFrame:
    dfs = []  # lista que acumula um DataFrame por semestre

    for ano in range(ano_inicio, ano_fim + 1):
        for semestre in (1, 2):
            url = (
                "https://www.gov.br/anp/pt-br/centrais-de-conteudo/"
                f"dados-abertos/arquivos/shpc/dsas/ca/ca-{ano}-0{semestre}.zip"
            )
            try:
                df_semestre = pd.read_csv(
                    url,
                    sep=";",
                    encoding="utf-8",
                    decimal=",",
                    dtype={
                        "CNPJ da Revenda": str
                    },  # força a coluna a ser lida como texto
                )  # (opcional) registrar a origem de cada linha
                df_semestre["ano_ref"] = ano
                df_semestre["semestre_ref"] = semestre

                dfs.append(df_semestre)
                print(f"OK   -> {ano}-0{semestre}: {len(df_semestre):,} linhas")
            except Exception as e:
                # arquivo ainda não publicado, URL fora do ar, etc.
                print(f"ERRO -> {ano}-0{semestre}: {e}")

    if not dfs:
        raise ValueError("Nenhum arquivo foi carregado. Verifique as URLs.")

    # concatena tudo num único DataFrame, reindexando as linhas
    return pd.concat(dfs, ignore_index=True)


df = carregar_precos(2025, 2025)
print(f"\nTotal: {len(df):,} linhas | {df.shape[1]} colunas")
# print(df.head())

# Grava parquet
df.to_parquet("D:/ESTUDOS/projetos/anp-fuel/data/precos.parquet", index=False)
