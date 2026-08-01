"""
sql_missions.py
Define a missao apresentada ao jogador, a query "gabarito" (canonica) e
a logica para validar a query que o jogador escreveu.

A sequencia de nomes retornada pela query correta vira, no jogo, a ordem
em que o jogador precisa comer os bonus numerados no labirinto.
"""

import re
import sqlite3
from dataclasses import dataclass
from typing import List, Tuple


MISSION_TITLE = "Missao: Top Clientes de 2024"

MISSION_DESCRIPTION = """
A diretoria quer saber quais clientes mais compraram em **2024**.

Escreva uma query SQL que retorne, para as vendas de 2024:

- uma coluna chamada **nome_cliente** com o nome do cliente
- uma coluna chamada **total_vendas** com a soma do valor total vendido para aquele cliente

O resultado deve vir **ordenado do maior para o menor total_vendas**.

Tabelas disponiveis:
- `tb_Clientes` (id_cliente, nome, cidade, estado)
- `tb_Produtos` (id_produto, nome, categoria, preco)
- `tb_Vendas` (id_venda, id_cliente, id_produto, data_venda, quantidade, valor_total)

Dica: use `JOIN`, `GROUP BY`, `SUM` e `ORDER BY` e filtre `data_venda` de 2024
(ex: `strftime('%Y', data_venda) = '2024'`).
"""

# Query canonica (gabarito) usada apenas para gerar a sequencia esperada
# e validar a resposta do jogador.
CANONICAL_QUERY = """
    SELECT
        c.nome AS nome_cliente,
        SUM(v.valor_total) AS total_vendas
    FROM tb_Vendas v
    INNER JOIN tb_Clientes c ON v.id_cliente = c.id_cliente
    WHERE strftime('%Y', v.data_venda) = '2024'
    GROUP BY c.id_cliente, c.nome
    ORDER BY total_vendas DESC
"""

MAX_SEQUENCE_LEN = 6  # quantidade maxima de bonus numerados no labirinto

FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "attach",
    "detach", "pragma", "vacuum", "replace into", "create",
]


@dataclass
class ValidationResult:
    ok: bool
    message: str
    sequence: List[str]
    result_preview: List[Tuple]
    columns: List[str]


def _is_select_only(query: str) -> bool:
    q = query.strip().lower()
    if not q.startswith("select"):
        return False
    if ";" in q.strip().rstrip(";"):
        # bloqueia multiplos statements (algo antes de um ';' no meio)
        return False
    return not any(re.search(rf"\b{kw}\b", q) for kw in FORBIDDEN_KEYWORDS)


def get_expected_sequence(db_path: str) -> List[str]:
    """Retorna a sequencia COMPLETA de nomes (na ordem correta), usada para
    validar a query do jogador. O corte para o numero de bonus do jogo
    (MAX_SEQUENCE_LEN) e feito separadamente por quem consome o resultado."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = conn.cursor()
        cur.execute(CANONICAL_QUERY)
        rows = cur.fetchall()
    finally:
        conn.close()
    return [row[0] for row in rows]


def validate_player_query(db_path: str, player_query: str) -> ValidationResult:
    if not player_query or not player_query.strip():
        return ValidationResult(False, "Escreva uma query antes de validar.", [], [], [])

    if not _is_select_only(player_query):
        return ValidationResult(
            False,
            "Apenas comandos SELECT unicos sao permitidos (sem INSERT/UPDATE/"
            "DELETE/DROP/ATTACH/PRAGMA e sem multiplos comandos).",
            [], [], [],
        )

    # Conexao somente-leitura: garante que nada seja alterado no banco.
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute(player_query)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description] if cur.description else []
    except sqlite3.Error as e:
        return ValidationResult(False, f"Erro ao executar sua query: {e}", [], [], [])
    finally:
        conn.close()

    col_lookup = {c.lower(): i for i, c in enumerate(columns)}
    if "nome_cliente" not in col_lookup:
        return ValidationResult(
            False,
            "Sua query precisa retornar uma coluna chamada exatamente "
            "'nome_cliente' (use um ALIAS, ex: c.nome AS nome_cliente).",
            [], rows[:10], columns,
        )

    idx_nome = col_lookup["nome_cliente"]
    submitted_sequence = [r[idx_nome] for r in rows]

    expected_sequence = get_expected_sequence(db_path)

    if submitted_sequence == expected_sequence:
        return ValidationResult(
            True,
            "Query correta! A sequencia de bonus do jogo foi liberada.",
            expected_sequence[:MAX_SEQUENCE_LEN],
            rows[:10],
            columns,
        )

    return ValidationResult(
        False,
        "A query rodou, mas o resultado (nomes e/ou ordem) nao bate com o "
        "esperado. Revise o filtro de ano, o agrupamento e o ORDER BY.",
        [], rows[:10], columns,
    )
