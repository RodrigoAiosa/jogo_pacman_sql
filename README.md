# 👾 Pac-Man SQL Quest

Jogo clássico do Pac-Man (Streamlit + Canvas/JS) com uma pegadinha: antes de
jogar, o jogador precisa resolver uma **missão em SQL**. A ordem retornada
pela query correta (o `ORDER BY`) vira a sequência em que os **bônus
numerados** devem ser coletados dentro do labirinto.

## Como funciona

1. No início de cada sessão, **1 entre 10 missões SQL** é sorteada
   aleatoriamente (top clientes, produtos mais vendidos, faturamento por
   categoria/estado/cidade, ticket médio, clientes que menos compraram etc).
2. O app mostra a missão sorteada sobre `tb_Clientes`, `tb_Produtos` e
   `tb_Vendas`, com um checklist de 5 requisitos.
3. O jogador escreve a query SQL em um editor dentro do Streamlit.
4. Ao clicar em **Validar query**, a query roda (somente leitura) contra um
   banco SQLite local de teste. O checklist se atualiza ao vivo mostrando
   exatamente quais requisitos foram atendidos.
5. Se todos os 5 requisitos passarem, o jogo Pac-Man é liberado. No
   labirinto existem bônus numerados (1, 2, 3...) — cada número corresponde,
   em ordem, a um grupo do resultado da query (cliente, produto, categoria
   etc., dependendo da missão sorteada). O jogador só consegue "comer" o
   bônus `N` depois de já ter comido o bônus `N-1`.
6. Objetivo: comer todos os pontinhos + todos os bônus na ordem certa,
   sem ser pego pelos fantasmas. Controles: setas do teclado ou WASD.

## Identidade visual

O projeto tem uma direção de design proposital, em duas fases que contrastam:

- **Fase missão — "terminal CRT âmbar"**: a query SQL roda dentro de um
  console de dados com fósforo âmbar, scanlines sutis e cursor piscando.
  Cada um dos 5 requisitos da missão vira um item de **checklist ao vivo**
  (✓ / ✕ / pendente) que se atualiza a cada tentativa — o jogador vê
  exatamente qual parte da query ainda precisa de ajuste (coluna faltando,
  filtro errado, `ORDER BY` incorreto etc.), em vez de um "certo/errado" seco.
- **Transição — "acesso liberado"**: um painel dourado confirma a missão
  cumprida e mostra a sequência de bônus como *chips* numerados.
- **Fase jogo — "fliperama synthwave"**: paredes do labirinto em gradiente
  ciano→magenta, HUD em fonte pixel (`Press Start 2P`), Pac-Man com boca
  animada, fantasmas com olhos que acompanham a direção, bônus pulsantes,
  e controle via teclado (setas ou WASD).

Tipografia: `Press Start 2P` (títulos/HUD arcade), `JetBrains Mono`
(terminal/editor SQL/dados) e `Inter` (texto corrido). Os estilos respeitam
`prefers-reduced-motion` e mantêm foco de teclado visível nos botões/campos.

## Estrutura do projeto

```
pacman-sql-quest/
├── app.py            # App Streamlit (missão -> validação -> jogo)
├── database.py        # Cria/popula o banco SQLite de teste (vendas.db)
├── sql_missions.py     # Enunciado, requisitos, query gabarito e validação item a item
├── game_html.py        # Gera o HTML/CSS/JS do jogo (canvas) embutido
├── theme.py            # CSS do terminal + componentes visuais (checklist, chips)
├── requirements.txt
└── README.md
```

## Estrutura de dados assumida

Como o schema real de vocês não foi enviado junto, o projeto usa esta
estrutura de exemplo (ajuste `database.py` e a `CANONICAL_QUERY` em
`sql_missions.py` se os nomes de campo do schema real forem diferentes):

```sql
tb_Clientes (id_cliente, nome, cidade, estado)
tb_Produtos (id_produto, nome, categoria, preco)
tb_Vendas   (id_venda, id_cliente, id_produto, data_venda, quantidade, valor_total)
```

### As 10 missões

Todas seguem o mesmo contrato de colunas para permitir validação genérica:
a query deve retornar `resultado_nome` (a dimensão pedida: cliente, produto,
categoria, cidade ou estado) e `resultado_valor` (a métrica: soma, contagem
ou média), ordenados conforme pedido no enunciado.

| Código | Missão | Agregação | Ordem |
|---|---|---|---|
| MISSAO_01 | Top clientes de 2024 | SUM(valor_total) | DESC |
| MISSAO_02 | Produtos mais vendidos (quantidade) | SUM(quantidade) | DESC |
| MISSAO_03 | Faturamento por categoria | SUM(valor_total) | DESC |
| MISSAO_04 | Cidades com mais vendas | COUNT(*) | DESC |
| MISSAO_05 | Ticket médio por cliente | AVG(valor_total) | DESC |
| MISSAO_06 | Clientes que menos compraram em 2023 | SUM(valor_total) | ASC |
| MISSAO_07 | Faturamento por estado | SUM(valor_total) | DESC |
| MISSAO_08 | Categorias com mais unidades em 2024 | SUM(quantidade) | DESC |
| MISSAO_09 | Clientes que mais gastaram em Eletrônicos | SUM(valor_total) | DESC |
| MISSAO_10 | Produtos com maior receita em 2023 | SUM(valor_total) | DESC |

As queries gabarito completas estão em `sql_missions.py` (`MISSIONS`).

## Rodando localmente

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

O banco `vendas.db` é criado automaticamente na primeira execução (dados
fictícios, gerados com seed fixa para reprodutibilidade).

## Publicando no GitHub

```bash
git init
git add .
git commit -m "Pac-Man SQL Quest: jogo + missao SQL"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/pacman-sql-quest.git
git push -u origin main
```

Depois é só apontar o [Streamlit Community Cloud](https://streamlit.io/cloud)
para o repositório (arquivo principal `app.py`) para publicar o app.

## Personalizando

- **Adicionar/editar missões**: edite a lista `MISSIONS` em `sql_missions.py`.
  Cada missão precisa de uma `canonical_query` que retorne as colunas
  `resultado_nome` e `resultado_valor` — o resto (checklist, validação,
  sequência de bônus) funciona automaticamente para qualquer missão nesse
  formato.
- **Mudar o schema real**: ajuste as `CREATE TABLE` em `database.py` e as
  `canonical_query` de cada missão para bater com os nomes de coluna reais
  de `tb_Vendas`, `tb_Clientes` e `tb_Produtos`.
- **Layout do labirinto / posição dos bônus**: `game_html.py`, funções
  `_build_maze()` e `BONUS_POSITIONS`.
- **Dificuldade**: velocidade do jogo (`setInterval(tick, 160)`), número
  de vidas (`lives = 3`) e comportamento dos fantasmas (chance de
  perseguir vs. mover aleatoriamente) também estão em `game_html.py`.
