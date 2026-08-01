"""
theme.py
Identidade visual do Pac-Man SQL Quest.

Conceito: a missao SQL roda dentro de um terminal CRT ambar (fosforo ambar,
scanlines, cursor piscando) -- a estetica de "console de dados". Quando a
query correta e validada, a tela faz a transicao "ACESSO LIBERADO" e o
jogo abre como um fliperama synthwave (magenta/ciano) de verdade. O
contraste entre as duas fases e a assinatura visual do projeto.
"""

FONT_IMPORT = (
    "https://fonts.googleapis.com/css2?"
    "family=Press+Start+2P&family=JetBrains+Mono:wght@400;500;700&"
    "family=Inter:wght@400;500;600;700&display=swap"
)

CUSTOM_CSS = f"""
<link href="{FONT_IMPORT}" rel="stylesheet">
<style>
:root {{
    --bg: #0a0d09;
    --panel: #12160f;
    --panel-border: #2b3320;
    --amber: #ffb300;
    --amber-dim: #7a5200;
    --amber-soft: rgba(255, 179, 0, 0.14);
    --amber-glow: rgba(255, 179, 0, 0.45);
    --danger: #ff5d5d;
    --success: #3ddc84;
    --text-soft: #d8dccf;
    --font-display: 'Press Start 2P', monospace;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
    --font-body: 'Inter', -apple-system, sans-serif;
}}

/* fundo geral em ambiente de terminal */
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {{
    background: radial-gradient(ellipse at 50% -10%, #161c0f 0%, var(--bg) 60%) !important;
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container {{ padding-top: 2.2rem !important; max-width: 860px; }}

/* scanlines sutis sobre toda a pagina (nao interfere com cliques) */
.crt-overlay {{
    position: fixed; inset: 0; pointer-events: none; z-index: 9999;
    background: repeating-linear-gradient(
        0deg, rgba(0,0,0,0.09) 0px, rgba(0,0,0,0.09) 1px,
        transparent 2px, transparent 3px
    );
    mix-blend-mode: multiply;
}}

body, .stMarkdown, p, li, span {{ color: var(--text-soft); font-family: var(--font-body); }}

/* ---------- cabecalho de terminal ---------- */
.term-topbar {{
    display: flex; align-items: center; justify-content: space-between;
    font-family: var(--font-mono); color: var(--amber);
    border: 1px solid var(--panel-border); border-bottom: none;
    background: var(--panel); padding: 8px 16px; border-radius: 10px 10px 0 0;
    font-size: 13px; letter-spacing: 0.5px;
}}
.term-dot {{
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    background: var(--amber); margin-right: 8px;
    box-shadow: 0 0 6px var(--amber-glow);
    animation: blink 1.4s steps(2) infinite;
}}
@media (prefers-reduced-motion: reduce) {{ .term-dot {{ animation: none; }} }}
@keyframes blink {{ 50% {{ opacity: 0.15; }} }}

.term-panel {{
    border: 1px solid var(--panel-border); border-top: none;
    background: linear-gradient(180deg, #0e1209 0%, #0a0d07 100%);
    border-radius: 0 0 10px 10px; padding: 22px 26px 26px;
    box-shadow: 0 0 0 1px #000, inset 0 0 60px rgba(255,179,0,0.03);
    margin-bottom: 18px;
}}

.mission-eyebrow {{
    font-family: var(--font-display); font-size: 10px; color: var(--amber);
    letter-spacing: 1px; margin-bottom: 10px; opacity: 0.9;
}}
.mission-title {{
    font-family: var(--font-display); font-size: 20px; color: #fff;
    margin: 0 0 16px 0; line-height: 1.6;
    text-shadow: 0 0 14px var(--amber-glow);
}}
.mission-hint {{
    font-family: var(--font-mono); font-size: 12.5px; color: var(--amber-dim);
    border-left: 2px solid var(--amber-dim); padding-left: 10px; margin-top: 14px;
}}

/* ---------- checklist de requisitos ---------- */
.req-list {{ list-style: none; padding: 0; margin: 14px 0 4px; }}
.req-item {{
    font-family: var(--font-mono); font-size: 13.5px; padding: 7px 0;
    display: flex; align-items: center; gap: 10px;
    border-bottom: 1px dashed rgba(255,255,255,0.06);
}}
.req-item .box {{
    width: 18px; height: 18px; flex: 0 0 18px; border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; border: 1px solid var(--panel-border);
}}
.req-item.pending .box {{ color: var(--amber-dim); border-color: var(--amber-dim); }}
.req-item.ok .box {{ background: var(--success); color: #06210f; border-color: var(--success); }}
.req-item.fail .box {{ background: var(--danger); color: #2b0505; border-color: var(--danger); }}
.req-item.ok span.label {{ color: var(--success); }}
.req-item.fail span.label {{ color: var(--danger); }}
.req-item.pending span.label {{ color: var(--text-soft); opacity: 0.7; }}

/* ---------- editor SQL como terminal ---------- */
[data-testid="stTextArea"] textarea {{
    background: #050603 !important; color: #ffd166 !important;
    font-family: var(--font-mono) !important; font-size: 14px !important;
    border: 1px solid var(--amber-dim) !important; border-radius: 8px !important;
    box-shadow: inset 0 0 22px rgba(255,179,0,0.04) !important;
}}
[data-testid="stTextArea"] textarea:focus {{
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 1px var(--amber), 0 0 18px var(--amber-glow) !important;
}}

/* ---------- botoes estilo arcade ---------- */
[data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {{
    font-family: var(--font-mono) !important; font-weight: 600 !important;
    letter-spacing: 0.4px; border-radius: 6px !important;
    border: 1px solid var(--amber-dim) !important;
    background: #14180d !important; color: var(--amber) !important;
    transition: all 0.15s ease;
}}
[data-testid="stButton"] button:hover {{
    border-color: var(--amber) !important; color: #fff !important;
    box-shadow: 0 0 14px var(--amber-glow) !important;
}}
[data-testid="stButton"] button[kind="primary"] {{
    background: var(--amber) !important; color: #1a1200 !important;
    border-color: var(--amber) !important; font-weight: 700 !important;
}}
[data-testid="stButton"] button[kind="primary"]:hover {{
    box-shadow: 0 0 22px var(--amber-glow) !important; filter: brightness(1.08);
}}
[data-testid="stButton"] button:focus-visible,
[data-testid="stTextArea"] textarea:focus-visible {{
    outline: 2px solid #fff !important; outline-offset: 2px;
}}

/* ---------- alertas (success / error / info) ---------- */
[data-testid="stAlertContentSuccess"], [data-testid="stAlertContentSuccess"] p {{ color: var(--success) !important; }}
[data-testid="stAlertContentError"], [data-testid="stAlertContentError"] p {{ color: var(--danger) !important; }}
[data-testid="stAlertContentInfo"], [data-testid="stAlertContentInfo"] p {{ color: var(--amber) !important; }}
[data-testid="stAlert"] {{
    background: var(--panel) !important; border: 1px solid var(--panel-border) !important;
    font-family: var(--font-mono) !important;
}}

/* ---------- painel "ACESSO LIBERADO" ---------- */
.access-granted {{
    text-align: center; padding: 26px 10px; margin-bottom: 6px;
    border: 1px solid #ffd54f; border-radius: 10px;
    background: linear-gradient(180deg, rgba(255,213,79,0.10), rgba(255,213,79,0.02));
    box-shadow: 0 0 30px rgba(255,213,79,0.15);
}}
.access-granted .tag {{
    font-family: var(--font-display); font-size: 22px; color: #ffd54f;
    letter-spacing: 2px; text-shadow: 0 0 18px rgba(255,213,79,0.6);
}}

/* ---------- chips da sequencia de bonus ---------- */
.chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0; }}
.chip {{
    font-family: var(--font-mono); font-size: 13px; padding: 6px 12px;
    border-radius: 20px; border: 1px solid #ffd54f; color: #ffd54f;
    background: rgba(255, 213, 79, 0.08);
}}
.chip b {{ font-family: var(--font-display); font-size: 10px; margin-right: 6px; }}

/* ---------- marquee do jogo ---------- */
.arcade-marquee {{
    text-align: center; padding: 14px 8px 10px;
    font-family: var(--font-display); font-size: 22px;
    background: linear-gradient(90deg, #08d9d6, #ff2e63);
    -webkit-background-clip: text; background-clip: text; color: transparent;
    text-shadow: none; letter-spacing: 1px;
}}
</style>
<div class="crt-overlay"></div>
"""


def render_terminal_header(label: str) -> str:
    return f"""
    <div class="term-topbar">
        <span><span class="term-dot"></span>{label}</span>
        <span>root@sql-quest:~$</span>
    </div>
    """


def render_checklist(labels, statuses) -> str:
    icons = {"ok": "✓", "fail": "✕", "pending": "·"}
    items = "".join(
        f'<li class="req-item {status}"><span class="box">{icons[status]}</span>'
        f'<span class="label">{label}</span></li>'
        for label, status in zip(labels, statuses)
    )
    return f'<ul class="req-list">{items}</ul>'


def render_sequence_chips(sequence) -> str:
    chips = "".join(
        f'<span class="chip"><b>{i + 1}</b>{name}</span>'
        for i, name in enumerate(sequence)
    )
    return f'<div class="chip-row">{chips}</div>'
