import pandas as pd

ano_inicio = 2025
ano_fim = 2025
# count = 0

dfs = []  # lista vazia que vai guardar um DataFrame por semestre

for ano in range(ano_inicio, (ano_fim + 1)):
    for semestre in range(1, 3):
        url = f"https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsas/ca/ca-{ano}-0{semestre}.zip"
        df_semestre = pd.read_csv(url, sep=";", encoding="utf-8", decimal=",")
        dfs.append(df_semestre)
        print(f"Importado o semeste: {ano}-0{semestre}.")
        # count += 1


df = pd.concat(dfs, ignore_index=True)  # junta tudo num único DataFrame

print(
    f"Foram importados e inseridos no dataframe {len(dfs)} semestres."
)  # quantos arquivos foram lidos, o LEN da lista vai listar a quantidade de elementos dentro da lista.

print(df.shape)  # total de linhas e colunas do DataFrame final

print(df.head())
