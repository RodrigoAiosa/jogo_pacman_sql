"""
app.py
Pac-Man SQL Quest - Streamlit + SQLite + mini jogo em canvas/JS.

Fluxo:
1) Terminal ambar: mostra a missao (enunciado de negocio) e um editor SQL.
2) O jogador escreve a query e clica em "Validar query"; um checklist ao
   vivo mostra exatamente quais dos 5 requisitos foram atendidos.
3) Se todos passarem, a tela de "ACESSO LIBERADO" aparece e o jogo e liberado.
4) O jogo Pac-Man (fliperama synthwave) e renderizado com bonus numerados
   que devem ser coletados na mesma ordem retornada pela query.
"""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from database import build_database
from game_html import build_game_html
from sql_missions import (
    CANONICAL_QUERY,
    MISSION_CODE,
    MISSION_DESCRIPTION,
    MISSION_HINT,
    MISSION_TITLE,
    REQUIREMENTS,
    TABLE_SCHEMA,
    validate_player_query,
)
from theme import (
    CUSTOM_CSS,
    render_checklist,
    render_sequence_chips,
    render_terminal_header,
)

st.set_page_config(page_title="Pac-Man SQL Quest", page_icon="👾", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Estado inicial
# ---------------------------------------------------------------------------
if "db_path" not in st.session_state:
    st.session_state.db_path = build_database()

if "stage" not in st.session_state:
    st.session_state.stage = "missao"  # missao -> pronto_para_jogo -> jogo

if "sequence" not in st.session_state:
    st.session_state.sequence = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

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

# ---------------------------------------------------------------------------
# Etapa 1: Missao (terminal)
# ---------------------------------------------------------------------------
if st.session_state.stage == "missao":
    st.markdown(render_terminal_header("MISSION-TERMINAL v1.0"), unsafe_allow_html=True)

    result = st.session_state.last_result
    checklist_statuses = result.checklist if result else ["pending"] * len(REQUIREMENTS)

    st.markdown(
        f"""
        <div class="term-panel">
            <div class="mission-eyebrow">{MISSION_CODE} // ACESSO RESTRITO</div>
            <div class="mission-title">{MISSION_TITLE}</div>
            <p style="margin-top:-6px;">{MISSION_DESCRIPTION}</p>
            {render_checklist(REQUIREMENTS, checklist_statuses)}
            <div class="mission-hint">{MISSION_HINT}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.query_text = st.text_area(
        "QUERY.SQL",
        value=st.session_state.query_text,
        height=190,
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        validar = st.button("▶ VALIDAR QUERY", type="primary", use_container_width=True)
    with col2:
        ver_tabelas = st.button("▤ VER TABELAS", use_container_width=True)

    if ver_tabelas:
        schema_txt = "\n\n".join(
            f"**{tabela}**: {', '.join(campos)}" for tabela, campos in TABLE_SCHEMA.items()
        )
        st.info(schema_txt)

    if validar:
        resultado = validate_player_query(st.session_state.db_path, st.session_state.query_text)
        st.session_state.last_result = resultado

        if resultado.columns:
            st.caption("Preview do resultado da sua query (ate 10 linhas):")
            st.dataframe(pd.DataFrame(resultado.result_preview, columns=resultado.columns))

        if resultado.ok:
            st.session_state.sequence = resultado.sequence
            st.session_state.stage = "pronto_para_jogo"
            st.rerun()
        else:
            st.error(resultado.message)

elif st.session_state.stage == "pronto_para_jogo":
    st.markdown(
        """
        <div class="access-granted">
            <div class="tag">✓ ACESSO LIBERADO</div>
            <p style="margin:8px 0 0; color:#f4e9c1;">Sua query bateu com o gabarito. O fliperama esta pronto.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Sequencia de bonus liberada (na ordem do seu `ORDER BY`):**")
    st.markdown(render_sequence_chips(st.session_state.sequence), unsafe_allow_html=True)
    st.caption(
        "No jogo, cada bonus numerado so pode ser coletado depois do anterior -- "
        "a mesma ordem que sua query retornou."
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🕹 INICIAR JOGO", type="primary", use_container_width=True):
            st.session_state.stage = "jogo"
            st.rerun()
    with col2:
        if st.button("✎ REVISAR QUERY", use_container_width=True):
            st.session_state.stage = "missao"
            st.rerun()

# ---------------------------------------------------------------------------
# Etapa 2: Jogo (fliperama)
# ---------------------------------------------------------------------------
elif st.session_state.stage == "jogo":
    st.markdown('<div class="arcade-marquee">PAC-MAN SQL QUEST</div>', unsafe_allow_html=True)
    st.markdown(render_sequence_chips(st.session_state.sequence), unsafe_allow_html=True)

    html = build_game_html(st.session_state.sequence)
    components.html(html, height=860, scrolling=False)

    if st.button("⬅ VOLTAR PARA A MISSAO"):
        st.session_state.stage = "missao"
        st.rerun()
