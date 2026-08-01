"""
app.py
Pac-Man SQL Quest - Streamlit + SQLite + mini jogo em canvas/JS.

Fluxo:
1) Mostra a missao (enunciado de negocio) e um editor de SQL.
2) O jogador escreve a query e clica em "Validar query".
3) Se a query bater com o gabarito (mesmas colunas nome_cliente/total_vendas,
   mesmo filtro e mesma ordenacao), libera o jogo.
4) O jogo Pac-Man e renderizado com bonus numerados que devem ser coletados
   na mesma ordem retornada pela query (o ORDER BY vira a "sequencia" do jogo).
"""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from database import build_database
from game_html import build_game_html
from sql_missions import (
    MISSION_DESCRIPTION,
    MISSION_TITLE,
    validate_player_query,
)

st.set_page_config(page_title="Pac-Man SQL Quest", page_icon="👾", layout="centered")

# ---------------------------------------------------------------------------
# Estado inicial
# ---------------------------------------------------------------------------
if "db_path" not in st.session_state:
    st.session_state.db_path = build_database()

if "stage" not in st.session_state:
    st.session_state.stage = "missao"  # missao -> jogo

if "sequence" not in st.session_state:
    st.session_state.sequence = []

if "query_text" not in st.session_state:
    st.session_state.query_text = (
        "SELECT\n"
        "    c.nome AS nome_cliente,\n"
        "    SUM(v.valor_total) AS total_vendas\n"
        "FROM tb_Vendas v\n"
        "JOIN tb_Clientes c ON v.id_cliente = c.id_cliente\n"
        "WHERE strftime('%Y', v.data_venda) = '2024'\n"
        "GROUP BY c.id_cliente, c.nome\n"
        "ORDER BY total_vendas DESC;"
    )

st.title("👾 Pac-Man SQL Quest")

# ---------------------------------------------------------------------------
# Etapa 1: Missao
# ---------------------------------------------------------------------------
if st.session_state.stage == "missao":
    st.subheader(MISSION_TITLE)
    st.markdown(MISSION_DESCRIPTION)

    st.session_state.query_text = st.text_area(
        "Sua query SQL:",
        value=st.session_state.query_text,
        height=200,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        validar = st.button("✅ Validar query", type="primary", use_container_width=True)
    with col2:
        ver_tabelas = st.button("📋 Ver estrutura das tabelas", use_container_width=True)

    if ver_tabelas:
        st.info(
            "**tb_Clientes**: id_cliente, nome, cidade, estado\n\n"
            "**tb_Produtos**: id_produto, nome, categoria, preco\n\n"
            "**tb_Vendas**: id_venda, id_cliente, id_produto, data_venda, "
            "quantidade, valor_total"
        )

    if validar:
        resultado = validate_player_query(st.session_state.db_path, st.session_state.query_text)

        if resultado.columns:
            st.caption("Preview do resultado da sua query (ate 10 linhas):")
            st.dataframe(pd.DataFrame(resultado.result_preview, columns=resultado.columns))

        if resultado.ok:
            st.success(resultado.message)
            st.session_state.sequence = resultado.sequence
            st.session_state.stage = "pronto_para_jogo"
            st.rerun()
        else:
            st.error(resultado.message)

elif st.session_state.stage == "pronto_para_jogo":
    st.subheader(MISSION_TITLE)
    st.success("Missao cumprida! Sequencia de bonus liberada:")
    st.write(" ➜ ".join(f"**{i+1}. {nome}**" for i, nome in enumerate(st.session_state.sequence)))

    st.markdown(
        "No jogo, os bonus numerados so podem ser coletados **na ordem acima** "
        "(a mesma ordem que sua query retornou). Use as setas do teclado para "
        "mover o Pac-Man, coma os pontinhos e os bonus na ordem certa, e fuja "
        "dos fantasmas!"
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🕹️ Iniciar jogo", type="primary", use_container_width=True):
            st.session_state.stage = "jogo"
            st.rerun()
    with col2:
        if st.button("✏️ Voltar e revisar query", use_container_width=True):
            st.session_state.stage = "missao"
            st.rerun()

# ---------------------------------------------------------------------------
# Etapa 2: Jogo
# ---------------------------------------------------------------------------
elif st.session_state.stage == "jogo":
    st.subheader("🕹️ Pac-Man SQL Quest")
    st.caption(
        "Sequencia de bonus (da sua query): "
        + " ➜ ".join(st.session_state.sequence)
    )

    html = build_game_html(st.session_state.sequence)
    components.html(html, height=760, scrolling=False)

    if st.button("⬅️ Voltar para a missao"):
        st.session_state.stage = "missao"
        st.rerun()
