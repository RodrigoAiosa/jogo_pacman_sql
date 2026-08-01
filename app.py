"""
app.py
Pac-Man SQL Quest - Streamlit + SQLite + mini jogo em canvas/JS.

Fluxo:
1) No inicio da sessao, uma entre 10 missoes SQL e sorteada aleatoriamente.
2) Terminal ambar: mostra a missao (enunciado de negocio) e um editor SQL.
3) O jogador escreve a query e clica em "Validar query"; um checklist ao
   vivo mostra exatamente quais dos 5 requisitos foram atendidos.
4) Se todos passarem, a tela de "ACESSO LIBERADO" aparece e o jogo e liberado.
5) O jogo Pac-Man (fliperama synthwave) e renderizado com bonus numerados
   que devem ser coletados na mesma ordem retornada pela query.

Nota de implementacao: todo HTML/CSS bruto e injetado com st.html() (nao
st.markdown(..., unsafe_allow_html=True)). st.markdown roda o conteudo por
um parser de Markdown antes de liberar o HTML, e linhas de CSS/HTML
indentadas com 4+ espacos sao interpretadas como bloco de codigo (regra do
Markdown), escapando as tags e fazendo o CSS aparecer como texto na tela em
vez de ser aplicado. st.html() injeta o HTML diretamente, sem esse parser.
"""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from database import build_database
from game_html import build_game_html
from sql_missions import (
    TABLE_SCHEMA,
    build_requirements,
    pick_random_mission,
    validate_player_query,
)
from theme import (
    CUSTOM_CSS,
    inline_code,
    render_checklist,
    render_sequence_chips,
    render_terminal_header,
)

st.set_page_config(page_title="Pac-Man SQL Quest", page_icon="👾", layout="centered")
st.html(CUSTOM_CSS)

# ---------------------------------------------------------------------------
# Estado inicial
# ---------------------------------------------------------------------------
if "db_path" not in st.session_state:
    st.session_state.db_path = build_database()

if "mission" not in st.session_state:
    # sorteada uma unica vez por sessao (nao muda a cada rerun/clique)
    st.session_state.mission = pick_random_mission()

if "stage" not in st.session_state:
    st.session_state.stage = "missao"  # missao -> pronto_para_jogo -> jogo

if "sequence" not in st.session_state:
    st.session_state.sequence = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "query_text" not in st.session_state:
    st.session_state.query_text = ""

QUERY_PLACEHOLDER = (
    "SELECT\n"
    "    coluna AS resultado_nome,\n"
    "    agregacao(...) AS resultado_valor\n"
    "FROM tb_Vendas v\n"
    "-- JOIN ...\n"
    "-- WHERE ...\n"
    "-- GROUP BY ...\n"
    "-- ORDER BY resultado_valor DESC;"
)

mission = st.session_state.mission
requirements = build_requirements(mission)

# ---------------------------------------------------------------------------
# Etapa 1: Missao (terminal)
# ---------------------------------------------------------------------------
if st.session_state.stage == "missao":
    st.html(render_terminal_header("MISSION-TERMINAL v1.0"))

    result = st.session_state.last_result
    checklist_statuses = result.checklist if result else ["pending"] * len(requirements)

    st.html(f"""
        <div class="term-panel">
            <div class="mission-eyebrow">{mission.code} // ACESSO RESTRITO</div>
            <div class="mission-title">{mission.title}</div>
            <p style="margin-top:-6px;">{inline_code(mission.description)}</p>
            {render_checklist(requirements, checklist_statuses)}
            <div class="mission-hint">{inline_code(mission.hint)}</div>
        </div>
    """)

    st.session_state.query_text = st.text_area(
        "QUERY.SQL",
        value=st.session_state.query_text,
        placeholder=QUERY_PLACEHOLDER,
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
        resultado = validate_player_query(st.session_state.db_path, st.session_state.query_text, mission)
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
    st.html("""
        <div class="access-granted">
            <div class="tag">✓ ACESSO LIBERADO</div>
            <p style="margin:8px 0 0; color:#f4e9c1;">Sua query bateu com o gabarito. O fliperama esta pronto.</p>
        </div>
    """)

    st.markdown("**Sequencia de bonus liberada (na ordem do seu `ORDER BY`):**")
    st.html(render_sequence_chips(st.session_state.sequence))
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
    st.html('<div class="arcade-marquee">PAC-MAN SQL QUEST</div>')
    st.html(render_sequence_chips(st.session_state.sequence))

    html = build_game_html(st.session_state.sequence)
    components.html(html, height=920, scrolling=False)

    if st.button("⬅ VOLTAR PARA A MISSAO"):
        st.session_state.stage = "missao"
        st.rerun()
