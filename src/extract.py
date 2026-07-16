import pandas as pd

# 1. URL direta do arquivo CSV no site da ANP
url = "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsas/ca/ca-2026-01.zip"

# 2. Leitura direta da URL para um DataFrame
#    - sep=';'          -> arquivos da ANP usam ponto e vírgula como separador
#    - encoding='utf-8' -> se der erro de caracteres, troque por 'latin-1'
#    - decimal=','      -> preços vêm com vírgula decimal (padrão brasileiro)
df = pd.read_csv(url, sep=";", encoding="utf-8", decimal=",")

# 3. Conferir se leu corretamente
print(df.shape)
print(df.head())

# # 4. Salvar em Parquet (compressão snappy é o padrão, boa para análise)
# df.to_parquet("data/precos_2026_s1.parquet", index=False)
