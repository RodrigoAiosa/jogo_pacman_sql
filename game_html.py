"""
game_html.py
Monta o HTML/CSS/JS de um Pac-Man classico (renderizado em <canvas>) que
roda dentro do Streamlit via streamlit.components.v1.html.

Sem missao SQL, sem bonus numerado: e o jogo classico puro --
pastilhas normais, 4 pastilhas de poder (power pellets) que deixam os
fantasmas vulneraveis por alguns segundos, e tunel lateral.

Identidade visual: gabinete de fliperama synthwave -- paredes do labirinto
em gradiente ciano->magenta, HUD em fonte pixel, moldura CRT com scanlines,
Pac-Man com boca animada e fantasmas com olhos que seguem o jogador.
"""

import json
from typing import List

# Dimensoes reais do fliperama classico: 28 colunas x 31 linhas
# (a tela original tinha 224x248px de area de labirinto, em tiles de 8px --
# a mesma proporcao 28:31 usada aqui).
MAZE_COLS = 28
MAZE_ROWS = 31
TILE_PX = 20  # 28*20=560 x 31*20=620, mantendo a proporcao original

# 4 pastilhas de poder, uma perto de cada canto do anel externo
POWER_PELLET_POSITIONS = [(2, 2), (2, 25), (28, 2), (28, 25)]

# Codigos de celula do labirinto:
#   0 = caminho com pastilha (dot)
#   1 = parede do labirinto
#   2 = parede da casa dos fantasmas (cor propria)
#   3 = caminho livre sem pastilha (portao/tunel/interior da casa)
PATH_DOT = 0
WALL = 1
HOUSE_WALL = 2
PATH_EMPTY = 3


def _build_maze() -> List[List[int]]:
    """Gera um labirinto 28x31 ORIGINAL, nas proporcoes reais do fliperama
    classico (nao e uma copia do mapa da Namco, que e uma obra protegida
    por direitos autorais): anel externo percorrivel, tunel lateral que
    teleporta de um lado para o outro, casa de fantasmas central com
    portao, e blocos internos simetricos.
    """
    cols, rows = MAZE_COLS, MAZE_ROWS
    maze = [[WALL for _ in range(cols)] for _ in range(rows)]

    for c in range(1, cols - 1):
        maze[1][c] = PATH_DOT
        maze[rows - 2][c] = PATH_DOT
    for r in range(1, rows - 1):
        maze[r][1] = PATH_DOT
        maze[r][cols - 2] = PATH_DOT

    for r in range(2, rows - 2):
        for c in range(2, cols - 2):
            maze[r][c] = PATH_DOT

    block_rows = [(3, 6), (24, 27)]
    block_col_groups = [(2, 4), (7, 9)]
    for r0, r1 in block_rows:
        for c0, c1 in block_col_groups:
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    maze[r][c] = WALL
                    mirror_c = cols - 1 - c
                    maze[r][mirror_c] = WALL

    house_c0, house_c1 = 12, 15
    house_r0, house_r1 = 14, 18
    for c in range(house_c0, house_c1 + 1):
        maze[house_r0][c] = HOUSE_WALL
        maze[house_r1][c] = HOUSE_WALL
    for r in range(house_r0, house_r1 + 1):
        maze[r][house_c0] = HOUSE_WALL
        maze[r][house_c1] = HOUSE_WALL
    for r in range(house_r0 + 1, house_r1):
        for c in range(house_c0 + 1, house_c1):
            maze[r][c] = PATH_EMPTY
    maze[house_r0][13] = PATH_EMPTY
    maze[house_r0][14] = PATH_EMPTY

    tunnel_row = rows // 2
    maze[tunnel_row][0] = PATH_EMPTY
    maze[tunnel_row][cols - 1] = PATH_EMPTY

    return maze


def build_game_html() -> str:
    """Gera o HTML/CSS/JS completo do jogo classico (sem parametros de
    missao -- e so o Pac-Man puro)."""
    maze = _build_maze()

    data = {
        "maze": maze,
        "powerPellets": [{"row": r, "col": c} for r, c in POWER_PELLET_POSITIONS],
        "playerStart": {"row": 25, "col": 13},
        "ghostStarts": [
            {"row": 16, "col": 13, "color": "#ff2e63"},
            {"row": 16, "col": 14, "color": "#08d9d6"},
            {"row": 15, "col": 13, "color": "#ffb347"},
            {"row": 15, "col": 14, "color": "#ff8cff"},
        ],
    }
    data_json = json.dumps(data)

    html = """
<div id="pacman-root">
  <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    #pacman-root {
      --cyan: #08d9d6;
      --magenta: #ff2e63;
      --gold: #ffd54f;
      --ok-green: #3ddc84;
      --scared: #2b4bff;
      font-family: 'JetBrains Mono', monospace;
      color: #f4f4f4;
      background: radial-gradient(ellipse at 50% 0%, #1a1030 0%, #05040c 65%);
      border-radius: 14px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
      position: relative;
      overflow: hidden;
    }
    #pacman-root::before {
      content: "";
      position: absolute; inset: 0; pointer-events: none; z-index: 5;
      background: repeating-linear-gradient(
        0deg, rgba(0,0,0,0.16) 0px, rgba(0,0,0,0.16) 1px,
        transparent 2px, transparent 4px
      );
      mix-blend-mode: multiply;
    }
    #pacman-hud {
      width: 100%; max-width: 600px;
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 10px; font-size: 13px; z-index: 2;
      background: rgba(0,0,0,0.35); border: 1px solid rgba(8,217,214,0.35);
      border-radius: 8px; padding: 8px 14px;
    }
    #pacman-hud .lives { color: var(--gold); letter-spacing: 3px; }
    #pacman-hud .score-val {
      font-variant-numeric: tabular-nums; letter-spacing: 2px;
      color: var(--ok-green); text-shadow: 0 0 8px rgba(61,220,132,0.6);
    }
    .canvas-frame {
      position: relative; z-index: 2;
      padding: 10px;
      border-radius: 14px;
      background: linear-gradient(160deg, #14102a, #05040c);
      border: 2px solid rgba(255,255,255,0.06);
      box-shadow:
        0 0 0 1px rgba(8,217,214,0.25),
        0 0 40px rgba(255,46,99,0.18),
        inset 0 0 30px rgba(0,0,0,0.6);
    }
    #pacman-canvas { background: #000; border-radius: 6px; display: block; }
    #pacman-msg {
      margin-top: 12px; font-size: 13px; min-height: 20px;
      color: var(--gold); text-align: center; z-index: 2;
      font-family: 'Press Start 2P', monospace; letter-spacing: 0.5px;
    }
    #pacman-restart {
      margin-top: 10px; padding: 10px 20px;
      background: var(--magenta); color: white; border: none; border-radius: 6px;
      cursor: pointer; font-size: 12px; display: none; z-index: 2;
      font-family: 'Press Start 2P', monospace; letter-spacing: 0.5px;
      box-shadow: 0 0 16px rgba(255,46,99,0.5);
    }
    #pacman-restart:hover { filter: brightness(1.15); }
    #pacman-restart:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
  </style>

  <div id="pacman-hud">
    <div>PONTOS <span class="score-val" id="hud-score">0000</span></div>
    <div class="lives" id="hud-lives">● ● ●</div>
  </div>

  <div class="canvas-frame">
    <canvas id="pacman-canvas" width="560" height="620"></canvas>
  </div>

  <div id="pacman-msg">SETAS OU WASD PARA JOGAR</div>
  <button id="pacman-restart">JOGAR NOVAMENTE</button>
</div>

<script>
(function() {
  const GAME_DATA = __DATA_JSON__;
  const TILE = 20;
  const maze = GAME_DATA.maze;
  const rows = maze.length;
  const cols = maze[0].length;
  const SCARED_TICKS = 45; // ~7s a 160ms por tick

  const canvas = document.getElementById("pacman-canvas");
  const ctx = canvas.getContext("2d");
  const scoreEl = document.getElementById("hud-score");
  const livesEl = document.getElementById("hud-lives");
  const msgEl = document.getElementById("pacman-msg");
  const restartBtn = document.getElementById("pacman-restart");

  const wallGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  wallGradient.addColorStop(0, "#08d9d6");
  wallGradient.addColorStop(1, "#ff2e63");

  let dots = [], pellets = [], player, ghosts, dir, nextDir;
  let score, lives, gameOver, tickHandle, frame = 0;

  function cellIsPath(r, c) {
    if (r < 0 || r >= rows || c < 0 || c >= cols) return false;
    return maze[r][c] === 0 || maze[r][c] === 3;
  }

  function resetState() {
    dots = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (maze[r][c] === 0) dots.push({row: r, col: c});
      }
    }
    pellets = GAME_DATA.powerPellets.map(p => ({...p, collected: false}));
    dots = dots.filter(d => !pellets.some(p => p.row === d.row && p.col === d.col));
    const ps = GAME_DATA.playerStart;
    dots = dots.filter(d => !(d.row === ps.row && d.col === ps.col));

    player = {row: ps.row, col: ps.col, facing: "left"};
    ghosts = GAME_DATA.ghostStarts.map(g => ({
      row: g.row, col: g.col, homeRow: g.row, homeCol: g.col,
      color: g.color, facing: "up", scared: false, scaredTimer: 0,
    }));
    dir = null; nextDir = null;
    score = 0; lives = 3; gameOver = false;

    scoreEl.textContent = String(score).padStart(4, "0");
    livesEl.textContent = "● ".repeat(lives).trim();
    msgEl.textContent = "SETAS OU WASD PARA JOGAR";
    restartBtn.style.display = "none";
  }

  function tryMove(entity, direction) {
    let {row, col} = entity;
    if (direction === "up") row -= 1;
    else if (direction === "down") row += 1;
    else if (direction === "left") col -= 1;
    else if (direction === "right") col += 1;

    if (col < 0 && cellIsPath(row, cols - 1)) return {row, col: cols - 1};
    if (col >= cols && cellIsPath(row, 0)) return {row, col: 0};

    if (cellIsPath(row, col)) return {row, col};
    return null;
  }

  function movePlayer() {
    if (nextDir) {
      const moved = tryMove(player, nextDir);
      if (moved) { player.row = moved.row; player.col = moved.col; dir = nextDir; player.facing = dir; nextDir = null; return; }
    }
    if (dir) {
      const moved = tryMove(player, dir);
      if (moved) { player.row = moved.row; player.col = moved.col; }
    }
  }

  function moveGhosts() {
    ghosts.forEach(g => {
      if (g.scared) {
        g.scaredTimer -= 1;
        if (g.scaredTimer <= 0) g.scared = false;
      }
      const options = ["up", "down", "left", "right"].map(d => ({d, pos: tryMove(g, d)})).filter(o => o.pos);
      if (options.length === 0) return;
      let choice;
      const wantsClose = !g.scared && Math.random() < 0.65;
      const wantsFar = g.scared && Math.random() < 0.75;
      if (wantsClose || wantsFar) {
        options.sort((a, b) => {
          const da = Math.abs(a.pos.row - player.row) + Math.abs(a.pos.col - player.col);
          const db = Math.abs(b.pos.row - player.row) + Math.abs(b.pos.col - player.col);
          return wantsClose ? da - db : db - da;
        });
        choice = options[0];
      } else {
        choice = options[Math.floor(Math.random() * options.length)];
      }
      g.row = choice.pos.row; g.col = choice.pos.col; g.facing = choice.d;
    });
  }

  function checkCollisions() {
    const dIdx = dots.findIndex(d => d.row === player.row && d.col === player.col);
    if (dIdx >= 0) { dots.splice(dIdx, 1); score += 10; }

    const pellet = pellets.find(p => p.row === player.row && p.col === player.col && !p.collected);
    if (pellet) {
      pellet.collected = true;
      score += 50;
      ghosts.forEach(g => { g.scared = true; g.scaredTimer = SCARED_TICKS; });
      msgEl.textContent = "OS FANTASMAS ESTAO VULNERAVEIS!";
    }
    scoreEl.textContent = String(score).padStart(4, "0");

    ghosts.forEach(g => {
      if (g.row === player.row && g.col === player.col) {
        if (g.scared) {
          g.scared = false;
          g.row = g.homeRow; g.col = g.homeCol;
          score += 200;
          msgEl.textContent = "FANTASMA COMIDO! +200";
        } else {
          lives -= 1;
          livesEl.textContent = lives > 0 ? "● ".repeat(lives).trim() : "";
          if (lives <= 0) {
            endGame(false);
          } else {
            player.row = GAME_DATA.playerStart.row; player.col = GAME_DATA.playerStart.col;
            dir = null; nextDir = null;
          }
        }
      }
    });
    scoreEl.textContent = String(score).padStart(4, "0");

    if (dots.length === 0 && pellets.every(p => p.collected)) {
      endGame(true);
    }
  }

  function endGame(victory) {
    gameOver = true;
    clearInterval(tickHandle);
    msgEl.textContent = victory ? "VOCE VENCEU!" : "FIM DE JOGO";
    msgEl.style.color = victory ? "#3ddc84" : "#ff2e63";
    restartBtn.style.display = "inline-block";
  }

  function drawGhost(g) {
    const gx = g.col * TILE + TILE / 2;
    const gy = g.row * TILE + TILE / 2;
    const flashing = g.scared && g.scaredTimer < 15 && Math.floor(frame / 4) % 2 === 0;
    ctx.fillStyle = g.scared ? (flashing ? "#e8ecff" : "#2b4bff") : g.color;
    ctx.beginPath();
    ctx.arc(gx, gy, TILE / 2 - 4, Math.PI, 0);
    ctx.lineTo(gx + TILE / 2 - 4, gy + TILE / 2 - 4);
    for (let i = 0; i < 3; i++) {
      ctx.lineTo(gx + TILE / 2 - 4 - (i + 0.5) * ((TILE - 8) / 3), gy + TILE / 2 - 4 - (i % 2 === 0 ? 5 : 0));
    }
    ctx.lineTo(gx - TILE / 2 + 4, gy + TILE / 2 - 4);
    ctx.closePath();
    ctx.fill();

    if (g.scared) {
      ctx.fillStyle = "#fff";
      [-3, 3].forEach(dx => {
        ctx.beginPath();
        ctx.arc(gx + dx, gy - 2, 1.5, 0, Math.PI * 2);
        ctx.fill();
      });
      return;
    }
    const offsets = {up: [0, -2], down: [0, 2], left: [-2, 0], right: [2, 0], undefined: [0, 0]};
    const [ox, oy] = offsets[g.facing] || [0, 0];
    [-3, 3].forEach(dx => {
      ctx.fillStyle = "#fff";
      ctx.beginPath();
      ctx.arc(gx + dx, gy - 2, 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#1a1a2e";
      ctx.beginPath();
      ctx.arc(gx + dx + ox, gy - 2 + oy, 1, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  function draw() {
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (maze[r][c] === 1) {
          ctx.fillStyle = wallGradient;
          ctx.fillRect(c * TILE, r * TILE, TILE, TILE);
        } else if (maze[r][c] === 2) {
          ctx.fillStyle = "rgba(255, 46, 99, 0.55)";
          ctx.fillRect(c * TILE, r * TILE, TILE, TILE);
        }
      }
    }

    ctx.fillStyle = "#ffe082";
    dots.forEach(d => {
      ctx.beginPath();
      ctx.arc(d.col * TILE + TILE / 2, d.row * TILE + TILE / 2, 2, 0, Math.PI * 2);
      ctx.fill();
    });

    const pulse = 1 + 0.3 * Math.sin(frame / 6);
    ctx.fillStyle = "#fff8dc";
    pellets.forEach(p => {
      if (p.collected) return;
      ctx.beginPath();
      ctx.arc(p.col * TILE + TILE / 2, p.row * TILE + TILE / 2, 6 * pulse, 0, Math.PI * 2);
      ctx.fill();
    });

    const angles = {up: 0.5, down: 1.5, left: 1, right: 0, undefined: 0};
    const baseAngle = (angles[player.facing] ?? 0) * Math.PI;
    const mouthOpen = Math.abs(Math.sin(frame / 5)) * 0.24 * Math.PI + 0.03;
    ctx.fillStyle = "#ffe600";
    ctx.beginPath();
    const px = player.col * TILE + TILE / 2;
    const py = player.row * TILE + TILE / 2;
    ctx.arc(px, py, TILE / 2 - 3, baseAngle + mouthOpen, baseAngle - mouthOpen + Math.PI * 2);
    ctx.lineTo(px, py);
    ctx.fill();

    ghosts.forEach(drawGhost);
  }

  function tick() {
    if (gameOver) return;
    frame += 1;
    movePlayer();
    moveGhosts();
    checkCollisions();
    draw();
  }

  window.addEventListener("keydown", (e) => {
    const map = {
      "ArrowUp": "up", "w": "up", "W": "up",
      "ArrowDown": "down", "s": "down", "S": "down",
      "ArrowLeft": "left", "a": "left", "A": "left",
      "ArrowRight": "right", "d": "right", "D": "right",
    };
    if (map[e.key]) { nextDir = map[e.key]; e.preventDefault(); }
  });

  restartBtn.addEventListener("click", () => {
    resetState();
    msgEl.style.color = "";
    draw();
    tickHandle = setInterval(tick, 160);
  });

  resetState();
  draw();
  tickHandle = setInterval(tick, 160);
})();
</script>
"""
    html = html.replace("__DATA_JSON__", data_json)
    return html
