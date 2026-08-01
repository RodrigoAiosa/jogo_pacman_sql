"""
database.py
Cria (se necessario) e popula um banco SQLite local com dados de teste
para as tabelas: tb_Clientes, tb_Produtos, tb_Vendas.

Estrutura assumida (ajuste os nomes de campo aqui se o seu schema real
for diferente - o resto do projeto (missao SQL + jogo) nao precisa mudar,
desde que as colunas usadas na query canonica em sql_missions.py sejam
atualizadas junto).
"""

import os
import random
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendas.db")

CLIENTES = [
    "Ana Souza", "Bruno Lima", "Carla Mendes", "Diego Alves",
    "Elaine Rocha", "Fabio Torres", "Gabriela Dias", "Henrique Silva",
]

PRODUTOS = [
    ("Notebook Pro 14", "Eletronicos", 4500.00),
    ("Mouse sem fio", "Eletronicos", 89.90),
    ("Cadeira Gamer", "Moveis", 1299.00),
    ("Monitor 27pol", "Eletronicos", 1899.00),
    ("Teclado Mecanico", "Eletronicos", 349.00),
    ("Mesa de Escritorio", "Moveis", 899.00),
    ("Headset Bluetooth", "Eletronicos", 259.00),
    ("Webcam Full HD", "Eletronicos", 199.00),
]


def build_database(force_rebuild: bool = False) -> str:
    """Cria o banco de dados de teste (idempotente). Retorna o caminho do arquivo."""
    if force_rebuild and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    if os.path.exists(DB_PATH):
        return DB_PATH

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE tb_Clientes (
            id_cliente   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome         TEXT NOT NULL,
            cidade       TEXT,
            estado       TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE tb_Produtos (
            id_produto   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome         TEXT NOT NULL,
            categoria    TEXT,
            preco        REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE tb_Vendas (
            id_venda      INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente    INTEGER NOT NULL,
            id_produto    INTEGER NOT NULL,
            data_venda    TEXT NOT NULL,
            quantidade    INTEGER NOT NULL,
            valor_total   REAL NOT NULL,
            FOREIGN KEY (id_cliente) REFERENCES tb_Clientes (id_cliente),
            FOREIGN KEY (id_produto) REFERENCES tb_Produtos (id_produto)
        )
    """)

    cidades_estados = [
        ("Sao Paulo", "SP"), ("Osasco", "SP"), ("Rio de Janeiro", "RJ"),
        ("Curitiba", "PR"), ("Porto Alegre", "RS"), ("Salvador", "BA"),
        ("Recife", "PE"), ("Belo Horizonte", "MG"),
    ]

    random.seed(42)  # reprodutibilidade

    for nome in CLIENTES:
        cidade, estado = random.choice(cidades_estados)
        cur.execute(
            "INSERT INTO tb_Clientes (nome, cidade, estado) VALUES (?, ?, ?)",
            (nome, cidade, estado),
        )

    for nome, categoria, preco in PRODUTOS:
        cur.execute(
            "INSERT INTO tb_Produtos (nome, categoria, preco) VALUES (?, ?, ?)",
            (nome, categoria, preco),
        )

    n_clientes = len(CLIENTES)
    n_produtos = len(PRODUTOS)

    # gera vendas em 2023 e 2024 (para a missao filtrar por ano fazer sentido)
    for _ in range(220):
        id_cliente = random.randint(1, n_clientes)
        id_produto = random.randint(1, n_produtos)
        ano = random.choice([2023, 2024])
        mes = random.randint(1, 12)
        dia = random.randint(1, 28)
        data_venda = f"{ano:04d}-{mes:02d}-{dia:02d}"
        quantidade = random.randint(1, 5)

        cur.execute("SELECT preco FROM tb_Produtos WHERE id_produto = ?", (id_produto,))
        preco = cur.fetchone()[0]
        valor_total = round(preco * quantidade, 2)

        cur.execute(
            """INSERT INTO tb_Vendas
               (id_cliente, id_produto, data_venda, quantidade, valor_total)
               VALUES (?, ?, ?, ?, ?)""",
            (id_cliente, id_produto, data_venda, quantidade, valor_total),
        )

    conn.commit()
    conn.close()
    return DB_PATH


if __name__ == "__main__":
    path = build_database(force_rebuild=True)
    print(f"Banco criado em: {path}")
