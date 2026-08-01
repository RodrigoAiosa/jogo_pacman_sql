"""
game_html.py
Monta o HTML/CSS/JS do mini Pac-Man (renderizado em <canvas>) que roda
dentro do Streamlit via streamlit.components.v1.html.

Identidade visual: gabinete de fliperama synthwave -- paredes do labirinto
em gradiente ciano->magenta, HUD em fonte pixel, moldura CRT com scanlines,
Pac-Man com boca animada e fantasmas com olhos que seguem o jogador.

A "torcao" do jogo: existem bonus numerados (1, 2, 3...) espalhados no
labirinto. Eles correspondem, em ordem, ao resultado da query SQL que o
jogador resolveu na missao. O jogador so consegue "comer" o bonus de
numero N depois de ja ter comido o bonus N-1 -- ou seja, ele precisa
respeitar a mesma ordem (ORDER BY) que a query correta produziu.
"""

import json
from typing import List


# Posicoes fixas (linha, coluna) para ate 6 bonus no labirinto 21x21.
BONUS_POSITIONS = [
    (1, 1), (1, 17), (9, 1), (9, 17), (17, 1), (17, 17),
]


def _build_maze() -> List[List[int]]:
    """Gera um labirinto 21x21 em formato de grade (lattice):
    linhas impares = corredor horizontal totalmente livre
    colunas pares em linhas pares = corredor vertical
    0 = caminho, 1 = parede
    """
    size = 21
    maze = [[1 for _ in range(size)] for _ in range(size)]
    for r in range(1, size - 1):
        for c in range(1, size - 1):
            if r % 2 == 1:
                maze[r][c] = 0
            elif c % 2 == 0:
                maze[r][c] = 0
    return maze


def build_game_html(sequence_labels: List[str], height: int = 700) -> str:
    """
    sequence_labels: lista de nomes (na ordem correta) vinda da query do
    jogador, ex: ["Ana Souza", "Bruno Lima", ...]. Define quantos e quais
    bonus numerados existem no labirinto.
    """
    n_bonus = min(len(sequence_labels), len(BONUS_POSITIONS))
    bonuses = []
    for i in range(n_bonus):
        r, c = BONUS_POSITIONS[i]
        bonuses.append({"row": r, "col": c, "number": i + 1, "label": sequence_labels[i]})

    maze = _build_maze()

    data = {
        "maze": maze,
        "bonuses": bonuses,
        "playerStart": {"row": 19, "col": 10},
        "ghostStarts": [{"row": 9, "col": 9}, {"row": 9, "col": 11}],
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
      width: 100%; max-width: 620px;
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
    #hud-sequence b { color: var(--gold); text-shadow: 0 0 8px rgba(255,213,79,0.5); }
    #pacman-legend {
      max-width: 620px; width: 100%; font-size: 12px; margin-bottom: 10px;
      color: #cfd3da; line-height: 1.6; z-index: 2; text-align: center;
    }
    #pacman-legend b { color: var(--gold); }
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
    <div id="hud-sequence">BONUS &rarr; <b>1</b></div>
    <div class="lives" id="hud-lives">● ● ●</div>
  </div>

  <div id="pacman-legend"></div>

  <div class="canvas-frame">
    <canvas id="pacman-canvas" width="588" height="588"></canvas>
  </div>

  <div id="pacman-msg">SETAS OU WASD PARA JOGAR</div>
  <button id="pacman-restart">JOGAR NOVAMENTE</button>
</div>

<script>
(function() {
  const GAME_DATA = __DATA_JSON__;
  const TILE = 28;
  const maze = GAME_DATA.maze;
  const rows = maze.length;
  const cols = maze[0].length;

  const canvas = document.getElementById("pacman-canvas");
  const ctx = canvas.getContext("2d");
  const scoreEl = document.getElementById("hud-score");
  const livesEl = document.getElementById("hud-lives");
  const seqEl = document.getElementById("hud-sequence");
  const msgEl = document.getElementById("pacman-msg");
  const restartBtn = document.getElementById("pacman-restart");
  const legendEl = document.getElementById("pacman-legend");

  // gradiente synthwave para as paredes (ciano no topo -> magenta embaixo)
  const wallGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  wallGradient.addColorStop(0, "#08d9d6");
  wallGradient.addColorStop(1, "#ff2e63");

  if (GAME_DATA.bonuses.length > 0) {
    let legendHtml = "<b>SEQUENCIA DE BONUS (ordem da sua query):</b><br>";
    legendHtml += GAME_DATA.bonuses.map(b => (b.number + ") " + b.label)).join(" &rarr; ");
    legendEl.innerHTML = legendHtml;
  } else {
    legendEl.innerHTML = "<b>Nenhum bonus numerado disponivel.</b>";
  }

  let dots = [], bonuses = [], player, ghosts, dir, nextDir;
  let score, lives, nextExpected, gameOver, tickHandle, frame = 0;

  function cellIsPath(r, c) {
    if (r < 0 || r >= rows || c < 0 || c >= cols) return false;
    return maze[r][c] === 0;
  }

  function resetState() {
    dots = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (maze[r][c] === 0) dots.push({row: r, col: c});
      }
    }
    bonuses = GAME_DATA.bonuses.map(b => ({...b, collected: false}));
    dots = dots.filter(d => !bonuses.some(b => b.row === d.row && b.col === d.col));
    const ps = GAME_DATA.playerStart;
    dots = dots.filter(d => !(d.row === ps.row && d.col === ps.col));

    player = {row: ps.row, col: ps.col, facing: "left", mouthPhase: 0};
    ghosts = GAME_DATA.ghostStarts.map((g, i) => ({
      row: g.row, col: g.col, color: i === 0 ? "#ff2e63" : "#08d9d6", facing: "up",
    }));
    dir = null; nextDir = null;
    score = 0; lives = 3; nextExpected = 1; gameOver = false;

    scoreEl.textContent = String(score).padStart(4, "0");
    livesEl.textContent = "● ".repeat(lives).trim();
    updateSeqHud();
    msgEl.textContent = "SETAS OU WASD PARA JOGAR";
    restartBtn.style.display = "none";
  }

  function updateSeqHud() {
    const remaining = bonuses.filter(b => !b.collected);
    if (bonuses.length === 0) {
      seqEl.innerHTML = "";
    } else if (remaining.length === 0) {
      seqEl.innerHTML = "BONUS &rarr; <b>completo!</b>";
    } else {
      const nextB = bonuses.find(b => b.number === nextExpected);
      seqEl.innerHTML = "BONUS &rarr; <b>" + (nextB ? nextB.number : "-") + "</b>";
    }
  }

  function tryMove(entity, direction) {
    let {row, col} = entity;
    if (direction === "up") row -= 1;
    else if (direction === "down") row += 1;
    else if (direction === "left") col -= 1;
    else if (direction === "right") col += 1;
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
      const options = ["up", "down", "left", "right"].map(d => ({d, pos: tryMove(g, d)})).filter(o => o.pos);
      if (options.length === 0) return;
      let choice;
      if (Math.random() < 0.65) {
        options.sort((a, b) => {
          const da = Math.abs(a.pos.row - player.row) + Math.abs(a.pos.col - player.col);
          const db = Math.abs(b.pos.row - player.row) + Math.abs(b.pos.col - player.col);
          return da - db;
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

    const bonus = bonuses.find(b => b.row === player.row && b.col === player.col && !b.collected);
    if (bonus) {
      if (bonus.number === nextExpected) {
        bonus.collected = true;
        score += 100 * bonus.number;
        nextExpected += 1;
        msgEl.textContent = "BONUS " + bonus.number + " OK!";
      } else {
        msgEl.textContent = "AINDA NAO -- PROXIMO E O " + nextExpected;
      }
    }
    scoreEl.textContent = String(score).padStart(4, "0");
    updateSeqHud();

    if (ghosts.some(g => g.row === player.row && g.col === player.col)) {
      lives -= 1;
      livesEl.textContent = lives > 0 ? "● ".repeat(lives).trim() : "";
      if (lives <= 0) {
        endGame(false);
      } else {
        player.row = GAME_DATA.playerStart.row; player.col = GAME_DATA.playerStart.col;
        dir = null; nextDir = null;
      }
    }

    if (dots.length === 0 && bonuses.every(b => b.collected)) {
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
    ctx.fillStyle = g.color;
    ctx.beginPath();
    ctx.arc(gx, gy, TILE / 2 - 4, Math.PI, 0);
    ctx.lineTo(gx + TILE / 2 - 4, gy + TILE / 2 - 4);
    for (let i = 0; i < 3; i++) {
      ctx.lineTo(gx + TILE / 2 - 4 - (i + 0.5) * ((TILE - 8) / 3), gy + TILE / 2 - 4 - (i % 2 === 0 ? 5 : 0));
    }
    ctx.lineTo(gx - TILE / 2 + 4, gy + TILE / 2 - 4);
    ctx.closePath();
    ctx.fill();

    // olhos que acompanham a direcao do movimento
    const offsets = {up: [0, -2], down: [0, 2], left: [-2, 0], right: [2, 0], undefined: [0, 0]};
    const [ox, oy] = offsets[g.facing] || [0, 0];
    [-5, 5].forEach(dx => {
      ctx.fillStyle = "#fff";
      ctx.beginPath();
      ctx.arc(gx + dx, gy - 3, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#1a1a2e";
      ctx.beginPath();
      ctx.arc(gx + dx + ox, gy - 3 + oy, 2, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  function draw() {
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = wallGradient;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (maze[r][c] === 1) ctx.fillRect(c * TILE + 1, r * TILE + 1, TILE - 2, TILE - 2);
      }
    }

    ctx.fillStyle = "#ffe082";
    dots.forEach(d => {
      ctx.beginPath();
      ctx.arc(d.col * TILE + TILE / 2, d.row * TILE + TILE / 2, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    const pulse = 1 + 0.18 * Math.sin(frame / 8);
    bonuses.forEach(b => {
      if (b.collected) return;
      const isNext = b.number === nextExpected;
      const radius = (isNext ? 11 : 9) * (isNext ? pulse : 1);
      ctx.beginPath();
      ctx.arc(b.col * TILE + TILE / 2, b.row * TILE + TILE / 2, radius, 0, Math.PI * 2);
      ctx.fillStyle = isNext ? "#ffd54f" : "#4a4f5e";
      if (isNext) { ctx.shadowColor = "#ffd54f"; ctx.shadowBlur = 10; }
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = isNext ? "#1a1a1a" : "#ccc";
      ctx.font = "bold 12px 'JetBrains Mono', monospace";
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(b.number), b.col * TILE + TILE / 2, b.row * TILE + TILE / 2 + 1);
    });

    // pac-man com boca animada
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
