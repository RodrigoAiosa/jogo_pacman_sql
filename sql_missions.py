"""
sql_missions.py
Define a missao apresentada ao jogador, a query "gabarito" (canonica) e
a logica para validar a query que o jogador escreveu, item por item.

A sequencia de nomes retornada pela query correta vira, no jogo, a ordem
em que o jogador precisa comer os bonus numerados no labirinto.
"""

import re
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

MISSION_TITLE = "Top clientes de 2024"
MISSION_CODE = "MISSAO_01"

MISSION_DESCRIPTION = """A diretoria quer saber quais clientes mais compraram em 2024.
Escreva uma query sobre `tb_Vendas`, `tb_Clientes` e `tb_Produtos` que atenda
aos 5 requisitos ao lado, e o acesso ao fliperama sera liberado."""

MISSION_HINT = (
    "Dica: `JOIN tb_Clientes`, filtre `strftime('%Y', data_venda) = '2024'`, "
    "agrupe por cliente com `GROUP BY` + `SUM`, e ordene com `ORDER BY total_vendas DESC`."
)

TABLE_SCHEMA = {
    "tb_Clientes": ["id_cliente", "nome", "cidade", "estado"],
    "tb_Produtos": ["id_produto", "nome", "categoria", "preco"],
    "tb_Vendas": ["id_venda", "id_cliente", "id_produto", "data_venda", "quantidade", "valor_total"],
}

# Os 5 itens abaixo sao a fonte da verdade da missao: aparecem como checklist
# na tela E sao exatamente o que validate_player_query confere, na ordem.
REQUIREMENTS = [
    "SELECT unico e somente-leitura",
    "Query executa sem erros",
    "Retorna a coluna nome_cliente",
    "total_vendas correto por cliente (2024, somado)",
    "Ordenado do maior para o menor total_vendas",
]

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
TOLERANCE = 0.01

FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "attach",
    "detach", "pragma", "vacuum", "replace into", "create",
]


@dataclass
class ValidationResult:
    ok: bool
    message: str
    sequence: List[str] = field(default_factory=list)
    result_preview: List[Tuple] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    # status de cada item de REQUIREMENTS: "ok" | "fail" | "pending"
    checklist: List[str] = field(default_factory=lambda: ["pending"] * len(REQUIREMENTS))


def _is_select_only(query: str) -> bool:
    q = query.strip().lower()
    if not q.startswith("select"):
        return False
    if ";" in q.strip().rstrip(";"):
        return False
    return not any(re.search(rf"\b{kw}\b", q) for kw in FORBIDDEN_KEYWORDS)


def get_expected_pairs(db_path: str) -> List[Tuple[str, float]]:
    """Retorna [(nome_cliente, total_vendas), ...] na ordem correta e COMPLETA
    (todos os clientes, sem corte). O corte para o numero de bonus do jogo
    e feito por quem consome o resultado (MAX_SEQUENCE_LEN)."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = conn.cursor()
        cur.execute(CANONICAL_QUERY)
        rows = cur.fetchall()
    finally:
        conn.close()
    return [(r[0], r[1]) for r in rows]


def get_expected_sequence(db_path: str) -> List[str]:
    return [name for name, _ in get_expected_pairs(db_path)]


def validate_player_query(db_path: str, player_query: str) -> ValidationResult:
    checklist = ["pending"] * len(REQUIREMENTS)

    if not player_query or not player_query.strip():
        return ValidationResult(False, "Escreva uma query antes de validar.", checklist=checklist)

    # 1) SELECT unico e seguro
    if not _is_select_only(player_query):
        checklist[0] = "fail"
        return ValidationResult(
            False,
            "Apenas um comando SELECT e permitido (sem INSERT/UPDATE/DELETE/"
            "DROP/ATTACH/PRAGMA e sem multiplos comandos separados por ';').",
            checklist=checklist,
        )
    checklist[0] = "ok"

    # 2) Executa sem erros (conexao somente-leitura)
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute(player_query)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description] if cur.description else []
    except sqlite3.Error as e:
        checklist[1] = "fail"
        return ValidationResult(False, f"Erro ao executar sua query: {e}", checklist=checklist)
    finally:
        conn.close()
    checklist[1] = "ok"

    # 3) Coluna nome_cliente presente
    col_lookup = {c.lower(): i for i, c in enumerate(columns)}
    if "nome_cliente" not in col_lookup:
        checklist[2] = "fail"
        return ValidationResult(
            False,
            "Sua query precisa de uma coluna chamada exatamente 'nome_cliente' "
            "(use um ALIAS, ex: c.nome AS nome_cliente).",
            checklist=checklist, result_preview=rows[:10], columns=columns,
        )
    checklist[2] = "ok"
    idx_nome = col_lookup["nome_cliente"]

    expected_pairs = get_expected_pairs(db_path)
    expected_totals: Dict[str, float] = dict(expected_pairs)
    expected_names_ordered = [n for n, _ in expected_pairs]

    submitted_names = [r[idx_nome] for r in rows]
    submitted_set = set(submitted_names)
    expected_set = set(expected_names_ordered)

    # 4) total_vendas correto (mesmos clientes e mesmos valores, ordem ainda nao conta aqui)
    totals_ok = False
    if "total_vendas" in col_lookup and submitted_set == expected_set and len(submitted_names) == len(set(submitted_names)):
        idx_total = col_lookup["total_vendas"]
        totals_ok = all(
            abs(float(r[idx_total]) - expected_totals.get(r[idx_nome], float("nan"))) < TOLERANCE
            for r in rows
        )

    if not totals_ok:
        checklist[3] = "fail"
        if "total_vendas" not in col_lookup:
            msg = "Falta a coluna 'total_vendas' (use um ALIAS, ex: SUM(v.valor_total) AS total_vendas)."
        elif submitted_set != expected_set:
            msg = "O conjunto de clientes nao bate com o esperado -- revise o JOIN, o WHERE (ano 2024) e o GROUP BY."
        else:
            msg = "Os valores de total_vendas nao batem -- confira se esta usando SUM(v.valor_total)."
        return ValidationResult(False, msg, checklist=checklist, result_preview=rows[:10], columns=columns)
    checklist[3] = "ok"

    # 5) Ordenacao correta
    if submitted_names != expected_names_ordered:
        checklist[4] = "fail"
        return ValidationResult(
            False,
            "Os valores estao corretos, mas a ordem nao esta -- use ORDER BY "
            "total_vendas DESC.",
            checklist=checklist, result_preview=rows[:10], columns=columns,
        )
    checklist[4] = "ok"

    return ValidationResult(
        True,
        "Todos os requisitos foram atendidos. Acesso ao fliperama liberado!",
        sequence=expected_names_ordered[:MAX_SEQUENCE_LEN],
        result_preview=rows[:10],
        columns=columns,
        checklist=checklist,
    )
