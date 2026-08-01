"""
app.py
Pac-Man classico - Streamlit + Canvas/JS.

Sem missao SQL, sem gate: abre o app e o jogo ja esta na tela.
"""

import streamlit as st
import streamlit.components.v1 as components

from game_html import build_game_html

st.set_page_config(page_title="Pac-Man Classico", page_icon="👾", layout="centered")

st.html("""
<style>
[data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: radial-gradient(ellipse at 50% -10%, #14102a 0%, #05040c 60%) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 2rem !important; max-width: 700px; }
</style>
<div style="text-align:center; padding: 6px 0 4px; font-family: 'Press Start 2P', monospace;
     font-size: 22px; background: linear-gradient(90deg, #08d9d6, #ff2e63);
     -webkit-background-clip: text; background-clip: text; color: transparent; letter-spacing: 1px;">
  PAC-MAN
</div>
""")

html = build_game_html()
components.html(html, height=920, scrolling=False)
