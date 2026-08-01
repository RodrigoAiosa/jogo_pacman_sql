"""
game_html.py
Monta o HTML/CSS/JS do mini Pac-Man (renderizado em <canvas>) que roda
dentro do Streamlit via streamlit.components.v1.html.

A "torcao" do jogo: existem bonus numerados (1, 2, 3...) espalhados no
labirinto. Eles correspondem, em ordem, ao resultado da query SQL que o
jogador resolveu na missao (ex: os clientes que mais compraram em 2024,
do maior para o menor). O jogador so consegue "comer" o bonus de numero N
depois de ja ter comido o bonus N-1 -- ou seja, ele precisa respeitar a
mesma ordem (ORDER BY) que a query correta produziu.
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
  <style>
    #pacman-root {
      font-family: 'Segoe UI', Arial, sans-serif;
      color: #f4f4f4;
      background: #05070d;
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    #pacman-hud {
      width: 100%;
      max-width: 640px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 16px;
    }
    #pacman-hud .lives { color: #ffcc00; }
    #pacman-hud .score { color: #58d68d; }
    #pacman-legend {
      max-width: 640px;
      width: 100%;
      font-size: 13px;
      margin-bottom: 10px;
      color: #cfd3da;
      line-height: 1.5;
    }
    #pacman-legend b { color: #ffd54f; }
    #pacman-canvas {
      background: #000;
      border: 3px solid #2a4dff;
      border-radius: 8px;
      box-shadow: 0 0 24px rgba(42, 77, 255, 0.45);
    }
    #pacman-msg {
      margin-top: 10px;
      font-size: 15px;
      min-height: 24px;
      color: #ffd54f;
      text-align: center;
    }
    #pacman-restart {
      margin-top: 8px;
      padding: 8px 18px;
      background: #2a4dff;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      display: none;
    }
    #pacman-restart:hover { background: #1c37cc; }
  </style>

  <div id="pacman-hud">
    <div class="score">Pontos: <span id="hud-score">0</span></div>
    <div id="hud-sequence">Proximo bonus: <b>1</b></div>
    <div class="lives">Vidas: <span id="hud-lives">3</span></div>
  </div>

  <div id="pacman-legend"></div>

  <canvas id="pacman-canvas" width="588" height="588"></canvas>
  <div id="pacman-msg">Use as setas do teclado (ou W A S D) para jogar</div>
  <button id="pacman-restart">Jogar novamente</button>
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

  // Legenda com a ordem de bonus esperada
  if (GAME_DATA.bonuses.length > 0) {
    let legendHtml = "<b>Sequencia de bonus (ordem da sua query SQL):</b><br>";
    legendHtml += GAME_DATA.bonuses.map(b => (b.number + ") " + b.label)).join(" &rarr; ");
    legendEl.innerHTML = legendHtml;
  } else {
    legendEl.innerHTML = "<b>Nenhum bonus numerado disponivel.</b>";
  }

  let dots = [];       // {row, col}
  let bonuses = [];     // {row, col, number, label, collected}
  let player, ghosts, dir, nextDir, score, lives, nextExpected, gameOver, won, tickHandle;

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
    // remove dot regular nas celulas de bonus (o bonus substitui o pontinho)
    dots = dots.filter(d => !bonuses.some(b => b.row === d.row && b.col === d.col));
    // remove dots nas posicoes iniciais de player/ghosts
    const ps = GAME_DATA.playerStart;
    dots = dots.filter(d => !(d.row === ps.row && d.col === ps.col));

    player = {row: GAME_DATA.playerStart.row, col: GAME_DATA.playerStart.col};
    ghosts = GAME_DATA.ghostStarts.map((g, i) => ({row: g.row, col: g.col, color: i === 0 ? "#ff4d4d" : "#ff8cff"}));
    dir = null;
    nextDir = null;
    score = 0;
    lives = 3;
    nextExpected = 1;
    gameOver = false;
    won = false;

    scoreEl.textContent = score;
    livesEl.textContent = lives;
    updateSeqHud();
    msgEl.textContent = "Use as setas do teclado (ou W A S D) para jogar";
    restartBtn.style.display = "none";
  }

  function updateSeqHud() {
    const remaining = bonuses.filter(b => !b.collected);
    if (remaining.length === 0) {
      seqEl.innerHTML = bonuses.length > 0 ? "Bonus: <b>todos coletados!</b>" : "";
    } else {
      const nextB = bonuses.find(b => b.number === nextExpected);
      seqEl.innerHTML = "Proximo bonus: <b>" + (nextB ? nextB.number + " (" + nextB.label + ")" : "-") + "</b>";
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
      if (moved) { player = moved; dir = nextDir; nextDir = null; return; }
    }
    if (dir) {
      const moved = tryMove(player, dir);
      if (moved) { player = moved; }
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
      g.row = choice.pos.row;
      g.col = choice.pos.col;
    });
  }

  function checkCollisions() {
    // dots
    const dIdx = dots.findIndex(d => d.row === player.row && d.col === player.col);
    if (dIdx >= 0) {
      dots.splice(dIdx, 1);
      score += 10;
    }
    // bonus (so conta se for o proximo esperado da sequencia)
    const bonus = bonuses.find(b => b.row === player.row && b.col === player.col && !b.collected);
    if (bonus) {
      if (bonus.number === nextExpected) {
        bonus.collected = true;
        score += 100 * bonus.number;
        nextExpected += 1;
        msgEl.textContent = "Bonus " + bonus.number + " (" + bonus.label + ") coletado!";
      } else {
        msgEl.textContent = "Ainda nao! Esse bonus e o numero " + bonus.number +
          ", mas o proximo da sequencia e o " + nextExpected + ".";
      }
    }
    scoreEl.textContent = score;
    updateSeqHud();

    // ghosts
    if (ghosts.some(g => g.row === player.row && g.col === player.col)) {
      lives -= 1;
      livesEl.textContent = lives;
      if (lives <= 0) {
        endGame(false);
      } else {
        player = {row: GAME_DATA.playerStart.row, col: GAME_DATA.playerStart.col};
        dir = null; nextDir = null;
      }
    }

    if (dots.length === 0 && bonuses.every(b => b.collected)) {
      endGame(true);
    }
  }

  function endGame(victory) {
    gameOver = true;
    won = victory;
    clearInterval(tickHandle);
    msgEl.textContent = victory
      ? "Voce venceu! Todos os pontos e bonus foram coletados na ordem certa."
      : "Fim de jogo! Os fantasmas pegaram voce.";
    restartBtn.style.display = "inline-block";
  }

  function draw() {
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // paredes
    ctx.fillStyle = "#132a91";
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (maze[r][c] === 1) ctx.fillRect(c * TILE, r * TILE, TILE, TILE);
      }
    }

    // dots
    ctx.fillStyle = "#ffe082";
    dots.forEach(d => {
      ctx.beginPath();
      ctx.arc(d.col * TILE + TILE / 2, d.row * TILE + TILE / 2, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    // bonus numerados
    bonuses.forEach(b => {
      if (b.collected) return;
      const isNext = b.number === nextExpected;
      ctx.beginPath();
      ctx.arc(b.col * TILE + TILE / 2, b.row * TILE + TILE / 2, 11, 0, Math.PI * 2);
      ctx.fillStyle = isNext ? "#ffd54f" : "#555b6e";
      ctx.fill();
      ctx.fillStyle = isNext ? "#1a1a1a" : "#ccc";
      ctx.font = "bold 13px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(b.number), b.col * TILE + TILE / 2, b.row * TILE + TILE / 2 + 1);
    });

    // player (pac-man)
    ctx.fillStyle = "#ffe600";
    ctx.beginPath();
    const px = player.col * TILE + TILE / 2;
    const py = player.row * TILE + TILE / 2;
    ctx.arc(px, py, TILE / 2 - 3, 0.25 * Math.PI, 1.75 * Math.PI);
    ctx.lineTo(px, py);
    ctx.fill();

    // ghosts
    ghosts.forEach(g => {
      ctx.fillStyle = g.color;
      const gx = g.col * TILE + TILE / 2;
      const gy = g.row * TILE + TILE / 2;
      ctx.beginPath();
      ctx.arc(gx, gy, TILE / 2 - 4, Math.PI, 0);
      ctx.lineTo(gx + TILE / 2 - 4, gy + TILE / 2 - 4);
      ctx.lineTo(gx - TILE / 2 + 4, gy + TILE / 2 - 4);
      ctx.fill();
    });
  }

  function tick() {
    if (gameOver) return;
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
    if (map[e.key]) {
      nextDir = map[e.key];
      e.preventDefault();
    }
  });

  restartBtn.addEventListener("click", () => {
    resetState();
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
