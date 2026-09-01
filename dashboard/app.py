"""
dashboard/app.py — Painel analítico do anp-fuel
Lê as tabelas Gold do PostgreSQL e exibe filtros, KPIs e gráficos
interativos sobre a série histórica de preços de combustíveis da ANP.

Execução: uv run streamlit run dashboard/app.py (a partir da raiz do projeto)
"""

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ------------------------------------------------------------------
# 0. CONFIGURAÇÃO DA PÁGINA E CONEXÃO
# ------------------------------------------------------------------
st.set_page_config(
    page_title="anp-fuel · Painel de Preços",
    page_icon="⛽",
    layout="wide",
)

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

DB_URL = (
    f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 5433)}/{os.getenv('DB_NAME')}"
)


@st.cache_resource
def get_engine():
    return create_engine(DB_URL)


@st.cache_data(ttl=600)  # cache de 10 min — evita bater no banco a cada interação
def carregar(query: str) -> pd.DataFrame:
    return pd.read_sql(query, get_engine())


# ------------------------------------------------------------------
# 1. CARREGAR DADOS BASE (para popular os filtros)
# ------------------------------------------------------------------
try:
    ufs = carregar("SELECT DISTINCT uf FROM precos_combustiveis ORDER BY uf")[
        "uf"
    ].tolist()
    produtos = carregar(
        "SELECT DISTINCT produto FROM precos_combustiveis ORDER BY produto"
    )["produto"].tolist()
    resumo = carregar(
        "SELECT COUNT(*) AS total, MAX(data_coleta) AS ultima_coleta, "
        "MAX(ano_ref) AS ultimo_ano, MAX(semestre_ref) AS ultimo_semestre "
        "FROM precos_combustiveis"
    ).iloc[0]
except Exception as e:
    st.error(f"Não foi possível conectar ao banco de dados: {e}")
    st.info("Confirme que o container está de pé: `docker compose ps`")
    st.stop()

# ------------------------------------------------------------------
# 2. SIDEBAR — FILTROS
# ------------------------------------------------------------------
st.sidebar.title("⛽ anp-fuel")
st.sidebar.caption("Painel de preços de combustíveis (ANP)")
st.sidebar.divider()

uf_selecionada = st.sidebar.selectbox(
    "UF", options=ufs, index=ufs.index("SP") if "SP" in ufs else 0
)
produtos_selecionados = st.sidebar.multiselect(
    "Produto(s)",
    options=produtos,
    default=[p for p in ("GASOLINA", "ETANOL") if p in produtos],
)

st.sidebar.divider()
st.sidebar.caption(
    f"📅 Última coleta na série: **{resumo['ultima_coleta']}**  \n"
    f"🔢 Total de registros: **{int(resumo['total']):,}**".replace(",", ".")
)

if not produtos_selecionados:
    st.warning("Selecione ao menos um produto na barra lateral.")
    st.stop()

produtos_sql = "', '".join(produtos_selecionados)

# ------------------------------------------------------------------
# 3. CABEÇALHO E KPIs
# ------------------------------------------------------------------
st.title(f"Preços de Combustíveis — {uf_selecionada}")

kpi_df = carregar(
    f"""
    SELECT produto, AVG(valor_venda) AS preco_medio, MIN(valor_venda) AS preco_min,
           MAX(valor_venda) AS preco_max, COUNT(*) AS coletas
    FROM precos_combustiveis
    WHERE uf = '{uf_selecionada}' AND produto IN ('{produtos_sql}')
    GROUP BY produto
    """
)

cols = st.columns(len(kpi_df) if len(kpi_df) > 0 else 1)
for col, (_, row) in zip(cols, kpi_df.iterrows()):
    with col:
        st.metric(
            label=row["produto"],
            value=f"R$ {row['preco_medio']:.3f}",
            help=f"Mín: R$ {row['preco_min']:.3f} · Máx: R$ {row['preco_max']:.3f} · {int(row['coletas']):,} coletas",
        )

st.divider()

# ------------------------------------------------------------------
# 4. ABAS DE ANÁLISE
# ------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📈 Evolução Mensal",
        "🏷️ Ranking de Bandeiras",
        "⚖️ Etanol × Gasolina",
        "📊 Variação (%)",
    ]
)

with tab1:
    st.subheader("Preço médio mensal")
    df = carregar(
        f"""
        SELECT mes_coleta, produto, preco_medio
        FROM gold_preco_mensal_uf
        WHERE uf = '{uf_selecionada}' AND produto IN ('{produtos_sql}')
        ORDER BY mes_coleta
        """
    )
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
    else:
        fig = px.line(
            df,
            x="mes_coleta",
            y="preco_medio",
            color="produto",
            markers=True,
            labels={
                "mes_coleta": "Mês",
                "preco_medio": "Preço médio (R$)",
                "produto": "Produto",
            },
        )
        fig.update_layout(hovermode="x unified", legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader(f"Participação de mercado por bandeira — {uf_selecionada}")
    df = carregar(
        f"SELECT bandeira, participacao_pct, qtd_postos "
        f"FROM gold_ranking_bandeiras WHERE uf = '{uf_selecionada}' "
        f"ORDER BY participacao_pct DESC LIMIT 15"
    )
    if df.empty:
        st.info("Sem dados para esta UF.")
    else:
        fig = px.bar(
            df,
            x="participacao_pct",
            y="bandeira",
            orientation="h",
            text="participacao_pct",
            labels={"participacao_pct": "Participação (%)", "bandeira": "Bandeira"},
            hover_data={"qtd_postos": True},
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Quando o etanol compensa? (regra dos 70%)")
    df = carregar(
        f"""
        SELECT mes_coleta, preco_etanol, preco_gasolina, razao_etanol_gasolina, combustivel_vantajoso
        FROM gold_etanol_vs_gasolina
        WHERE uf = '{uf_selecionada}'
        ORDER BY mes_coleta
        """
    )
    if df.empty:
        st.info("Sem dados de etanol/gasolina para esta UF.")
    else:
        fig = px.line(
            df,
            x="mes_coleta",
            y=["preco_etanol", "preco_gasolina"],
            markers=True,
            labels={"value": "Preço médio (R$)", "mes_coleta": "Mês", "variable": ""},
        )
        fig.add_hline(
            y=None,
            line_dash="dot",
        )
        st.plotly_chart(fig, use_container_width=True)

        pct_etanol = (df["combustivel_vantajoso"] == "ETANOL").mean() * 100
        st.caption(
            f"Em **{pct_etanol:.0f}%** dos meses analisados, o etanol foi a opção mais vantajosa em {uf_selecionada}."
        )
        st.dataframe(
            df.rename(
                columns={
                    "mes_coleta": "Mês",
                    "preco_etanol": "Etanol (R$)",
                    "preco_gasolina": "Gasolina (R$)",
                    "razao_etanol_gasolina": "Razão E/G",
                    "combustivel_vantajoso": "Mais vantajoso",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

with tab4:
    st.subheader("Variação percentual mês a mês")
    df = carregar(
        f"""
        SELECT mes_coleta, produto, variacao_pct
        FROM gold_variacao_mensal
        WHERE uf = '{uf_selecionada}' AND produto IN ('{produtos_sql}')
        ORDER BY mes_coleta
        """
    )
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
    else:
        fig = px.bar(
            df,
            x="mes_coleta",
            y="variacao_pct",
            color="produto",
            barmode="group",
            labels={
                "mes_coleta": "Mês",
                "variacao_pct": "Variação (%)",
                "produto": "Produto",
            },
        )
        fig.add_hline(y=0, line_color="gray", line_width=1)
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# 5. RODAPÉ
# ------------------------------------------------------------------
st.divider()
st.caption(
    "Dados: Série Histórica de Preços de Combustíveis — ANP (dados abertos) · "
    "Pipeline: extract → transform → load → dbt (star schema + marts) · "
    f"Base atualizada até {resumo['ultimo_ano']}-{int(resumo['ultimo_semestre']):02d}"
)
