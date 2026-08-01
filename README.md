# 👾 Pac-Man SQL Quest

Jogo clássico do Pac-Man (Streamlit + Canvas/JS) com uma pegadinha: antes de
jogar, o jogador precisa resolver uma **missão em SQL**. A ordem retornada
pela query correta (o `ORDER BY`) vira a sequência em que os **bônus
numerados** devem ser coletados dentro do labirinto.

## Como funciona

1. O app mostra uma missão de negócio (ex: *"top clientes de 2024"*) sobre
   as tabelas `tb_Clientes`, `tb_Produtos` e `tb_Vendas`.
2. O jogador escreve a query SQL em um editor dentro do Streamlit.
3. Ao clicar em **Validar query**, a query roda (somente leitura) contra um
   banco SQLite local de teste. Se o resultado bater com o gabarito
   (mesmas colunas `nome_cliente` / `total_vendas`, mesmo filtro, mesma
   ordenação), a missão é considerada cumprida.
4. O jogo Pac-Man é liberado. No labirinto existem bônus numerados
   (1, 2, 3...) — cada número corresponde, em ordem, a um cliente do
   resultado da query. O jogador só consegue "comer" o bônus `N` depois de
   já ter comido o bônus `N-1`.
5. Objetivo: comer todos os pontinhos + todos os bônus na ordem certa,
   sem ser pego pelos fantasmas.

## Estrutura do projeto

```
pacman-sql-quest/
├── app.py            # App Streamlit (missão -> validação -> jogo)
├── database.py        # Cria/popula o banco SQLite de teste (vendas.db)
├── sql_missions.py     # Enunciado da missão, query gabarito e validação
├── game_html.py        # Gera o HTML/CSS/JS do jogo (canvas) embutido
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

### Query gabarito da missão atual

```sql
SELECT
    c.nome AS nome_cliente,
    SUM(v.valor_total) AS total_vendas
FROM tb_Vendas v
INNER JOIN tb_Clientes c ON v.id_cliente = c.id_cliente
WHERE strftime('%Y', v.data_venda) = '2024'
GROUP BY c.id_cliente, c.nome
ORDER BY total_vendas DESC;
```

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

- **Trocar a missão / query gabarito**: edite `MISSION_DESCRIPTION` e
  `CANONICAL_QUERY` em `sql_missions.py`.
- **Mudar o schema real**: ajuste as `CREATE TABLE` em `database.py` e a
  `CANONICAL_QUERY` para bater com os nomes de coluna reais de
  `tb_Vendas`, `tb_Clientes` e `tb_Produtos`.
- **Layout do labirinto / posição dos bônus**: `game_html.py`, funções
  `_build_maze()` e `BONUS_POSITIONS`.
- **Dificuldade**: velocidade do jogo (`setInterval(tick, 160)`), número
  de vidas (`lives = 3`) e comportamento dos fantasmas (chance de
  perseguir vs. mover aleatoriamente) também estão em `game_html.py`.
