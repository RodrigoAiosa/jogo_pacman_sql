"""
sql_missions.py
Banco de 10 missoes SQL (perguntas de negocio variadas sobre tb_Clientes,
tb_Produtos e tb_Vendas). Uma missao e sorteada aleatoriamente no inicio
de cada sessao de jogo.

Para que a validacao funcione de forma generica para qualquer missao, toda
query gabarito usa duas colunas com nomes fixos:
    resultado_nome   -> a dimensao pedida (cliente, produto, categoria, cidade...)
    resultado_valor  -> a metrica pedida (soma, contagem, media...)

A sequencia de valores de resultado_nome retornada pela query correta vira,
no jogo, a ordem em que o jogador precisa comer os bonus numerados.
"""

import random
import re
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

TABLE_SCHEMA = {
    "tb_Clientes": ["id_cliente", "nome", "cidade", "estado"],
    "tb_Produtos": ["id_produto", "nome", "categoria", "preco"],
    "tb_Vendas": ["id_venda", "id_cliente", "id_produto", "data_venda", "quantidade", "valor_total"],
}

MAX_SEQUENCE_LEN = 6  # quantidade maxima de bonus numerados no labirinto
TOLERANCE = 0.01

FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "attach",
    "detach", "pragma", "vacuum", "replace into", "create",
]


@dataclass
class Mission:
    code: str
    title: str
    description: str
    hint: str
    canonical_query: str
    value_description: str   # usado no texto do requisito 4 (o que resultado_valor representa)
    order_desc: bool = True  # True = maior->menor, False = menor->maior


MISSIONS: List[Mission] = [
    Mission(
        code="MISSAO_01",
        title="Top clientes de 2024",
        description=(
            "A diretoria quer saber quais clientes mais compraram em 2024. "
            "Escreva uma query sobre `tb_Vendas` e `tb_Clientes` que atenda "
            "aos 5 requisitos ao lado, e o acesso ao fliperama sera liberado."
        ),
        hint=(
            "Dica: `JOIN tb_Clientes`, filtre `strftime('%Y', data_venda) = '2024'`, "
            "agrupe com `GROUP BY` + `SUM`, e ordene com `ORDER BY resultado_valor DESC`."
        ),
        canonical_query="""
            SELECT
                c.nome AS resultado_nome,
                SUM(v.valor_total) AS resultado_valor
            FROM tb_Vendas v
            INNER JOIN tb_Clientes c ON v.id_cliente = c.id_cliente
            WHERE strftime('%Y', v.data_venda) = '2024'
            GROUP BY c.id_cliente, c.nome
            ORDER BY resultado_valor DESC
        """,
        value_description="soma do valor total gasto por cliente em 2024",
        order_desc=True,
    ),
    Mission(
        code="MISSAO_02",
        title="Produtos mais vendidos (em quantidade)",
        description=(
            "O time de estoque quer saber quais produtos venderam mais unidades, "
            "considerando todo o historico de vendas. Escreva uma query sobre "
            "`tb_Vendas` e `tb_Produtos` que atenda aos 5 requisitos ao lado."
        ),
        hint=(
            "Dica: `JOIN tb_Produtos`, agrupe por produto com `GROUP BY` + "
            "`SUM(quantidade)`, e ordene com `ORDER BY resultado_valor DESC`."
        ),
        canonical_query="""
            SELECT
                p.nome AS resultado_nome,
                SUM(v.quantidade) AS resultado_valor
            FROM tb_Vendas v
            INNER JOIN tb_Produtos p ON v.id_produto = p.id_produto
            GROUP BY p.id_produto, p.nome
            ORDER BY resultado_valor DESC
        """,
        value_description="soma da quantidade vendida por produto (todo o periodo)",
        order_desc=True,
    ),
    Mission(
        code="MISSAO_03",
        title="Faturamento por categoria de produto",
        description=(
            "A area financeira quer o faturamento total agrupado por categoria "
            "de produto. Escreva uma query sobre `tb_Vendas` e `tb_Produtos` que "
            "atenda aos 5 requisitos ao lado."
        ),
        hint="Dica: `JOIN tb_Produtos`, `GROUP BY categoria` + `SUM(valor_total)`, `ORDER BY resultado_valor DESC`.",
        canonical_query="""
            SELECT
                p.categoria AS resultado_nome,
                SUM(v.valor_total) AS resultado_valor
            FROM tb_Vendas v
            INNER JOIN tb_Produtos p ON v.id_produto = p.id_produto
            GROUP BY p.categoria
            ORDER BY resultado_valor DESC
        """,
        value_description="soma do valor total vendido por categoria",
        order_desc=True,
    ),
    Mission(
        code="MISSAO_04",
        title="Cidades com mais vendas registradas",
        description=(
            "O time comercial quer saber em quais cidades dos clientes ha mais "
            "vendas registradas (numero de vendas, nao valor). Escreva uma query "
            "sobre `tb_Vendas` e `tb_Clientes` que atenda aos 5 requisitos ao lado."
        ),
        hint="Dica: `JOIN tb_Clientes`, `GROUP BY cidade` + `COUNT(*)`, `ORDER BY resultado_valor DESC`.",
        canonical_query="""
            SELECT
                c.cidade AS resultado_nome,
                COUNT(*) AS resultado_valor
            FROM tb_Vendas v
            INNER JOIN tb_Clientes c ON v.id_cliente = c.id_cliente
            GROUP BY c.cidade
            ORDER BY resultado_valor DESC
        """,
        value_description="numero de vendas (COUNT) por cidade",
        order_desc=True,
    ),
    Mission(
        code="MISSAO_05",
        title="Ticket medio por cliente",
        description=(
            "A diretoria quer saber o valor medio gasto por venda, para cada "
            "cliente, considerando todo o historico. Escreva uma query sobre "
            "`tb_Vendas` e `tb_Clientes` que atenda aos 5 requisitos ao lado."
        ),
        hint="Dica: `JOIN tb_Clientes`, `GROUP BY cliente` + `AVG(valor_total)`, `ORDER BY resultado_valor DESC`.",
        canonical_query="""
            SELECT
                c.nome AS resultado_nome,
                AVG(v.valor_total) AS resultado_valor
            FROM tb_Vendas v
            INNER JOIN tb_Clientes c ON v.id_cliente = c.id_cliente
            GROUP BY c.id_cliente, c.nome
            ORDER BY resultado_valor DESC
        """,
        value_description="media (AVG) do valor por venda, por cliente",
        order_desc=True,
    ),
    Mission(
        code="MISSAO_06",
        title="Clientes que menos compraram em 2023",
        description=(
            "O time de retencao quer identificar os clientes com MENOR total "
            "de compras em 2023, para uma campanha de reativacao. Escreva uma "
            "query sobre `tb_Vendas` e `tb_Clientes` que atenda aos 5 requisitos ao lado."
        ),
        hint=(
            "Dica: filtre `strftime('%Y', data_venda) = '2023'`, agrupe com "
            "`GROUP BY` + `SUM`, e ordene com `ORDER BY resultado_valor ASC` "
            "(do menor para o maior, ao contrario das outras missoes)."
        ),
        canonical_query="""
            SELECT
                c.nome AS resultado_nome,
                SUM(v.valor_total) AS resultado_valor
            FROM tb_Vendas v
            INNER JOIN tb_Clientes c ON v.id_cliente = c.id_cliente
            WHERE strftime('%Y', v.data_venda) = '2023'
            GROUP BY c.id_cliente, c.nome
            ORDER BY resultado_valor ASC
        """,
        value_description="soma do valor total gasto por cliente em 2023",
        order_desc=False,
    ),
    Mission(
        code="MISSAO_07",
        title="Faturamento por estado",
        description=(
            "A diretoria regional quer o faturamento total agrupado pelo estado "
            "dos clientes. Escreva uma query sobre `tb_Vendas` e `tb_Clientes` "
            "que atenda aos 5 requisitos ao lado."
        ),
        hint="Dica: `JOIN tb_Clientes`, `GROUP BY estado` + `SUM(valor_total)`, `ORDER BY resultado_valor DESC`.",
        canonical_query="""
            SELECT
                c.estado AS resultado_nome,
                SUM(v.valor_total) AS resultado_valor
            FROM tb_Vendas v
            INNER JOIN tb_Clientes c ON v.id_cliente = c.id_cliente
            GROUP BY c.estado
            ORDER BY resultado_valor DESC
        """,
        value_description="soma do valor total vendido por estado",
        order_desc=True,
    ),
    Mission(
        code="MISSAO_08",
        title="Categorias com mais unidades vendidas em 2024",
        description=(
            "O time de compras quer saber quais categorias de produto venderam "
            "mais UNIDADES (nao valor) em 2024, para planejar reposicao de "
            "estoque. Escreva uma query sobre `tb_Vendas` e `tb_Produtos` que "
            "atenda aos 5 requisitos ao lado."
        ),
        hint=(
            "Dica: `JOIN tb_Produtos`, filtre `strftime('%Y', data_venda) = '2024'`, "
            "`GROUP BY categoria` + `SUM(quantidade)`, `ORDER BY resultado_valor DESC`."
        ),
        canonical_query="""
            SELECT
                p.categoria AS resultado_nome,
                SUM(v.quantidade) AS resultado_valor
            FROM tb_Vendas v
            INNER JOIN tb_Produtos p ON v.id_produto = p.id_produto
            WHERE strftime('%Y', v.data_venda) = '2024'
            GROUP BY p.categoria
            ORDER BY resultado_valor DESC
        """,
        value_description="soma da quantidade vendida por categoria em 2024",
        order_desc=True,
    ),
    Mission(
        code="MISSAO_09",
        title="Clientes que mais gastaram em Eletronicos",
        description=(
            "O time de marketing quer saber quais clientes mais gastaram "
            "especificamente na categoria 'Eletronicos', em qualquer ano. "
            "Escreva uma query sobre `tb_Vendas`, `tb_Clientes` e `tb_Produtos` "
            "que atenda aos 5 requisitos ao lado."
        ),
        hint=(
            "Dica: junte as tres tabelas, filtre `p.categoria = 'Eletronicos'`, "
            "`GROUP BY cliente` + `SUM(valor_total)`, `ORDER BY resultado_valor DESC`."
        ),
        canonical_query="""
            SELECT
                c.nome AS resultado_nome,
                SUM(v.valor_total) AS resultado_valor
            FROM tb_Vendas v
            INNER JOIN tb_Clientes c ON v.id_cliente = c.id_cliente
            INNER JOIN tb_Produtos p ON v.id_produto = p.id_produto
            WHERE p.categoria = 'Eletronicos'
            GROUP BY c.id_cliente, c.nome
            ORDER BY resultado_valor DESC
        """,
        value_description="soma do valor gasto em Eletronicos, por cliente",
        order_desc=True,
    ),
    Mission(
        code="MISSAO_10",
        title="Produtos com maior receita em 2023",
        description=(
            "A diretoria quer saber quais produtos geraram mais receita em "
            "2023. Escreva uma query sobre `tb_Vendas` e `tb_Produtos` que "
            "atenda aos 5 requisitos ao lado."
        ),
        hint=(
            "Dica: `JOIN tb_Produtos`, filtre `strftime('%Y', data_venda) = '2023'`, "
            "`GROUP BY produto` + `SUM(valor_total)`, `ORDER BY resultado_valor DESC`."
        ),
        canonical_query="""
            SELECT
                p.nome AS resultado_nome,
                SUM(v.valor_total) AS resultado_valor
            FROM tb_Vendas v
            INNER JOIN tb_Produtos p ON v.id_produto = p.id_produto
            WHERE strftime('%Y', v.data_venda) = '2023'
            GROUP BY p.id_produto, p.nome
            ORDER BY resultado_valor DESC
        """,
        value_description="soma do valor total vendido por produto em 2023",
        order_desc=True,
    ),
]


def pick_random_mission() -> Mission:
    return random.choice(MISSIONS)


def build_requirements(mission: Mission) -> List[str]:
    order_txt = "do maior para o menor" if mission.order_desc else "do menor para o maior"
    return [
        "SELECT unico e somente-leitura",
        "Query executa sem erros",
        "Retorna a coluna resultado_nome",
        f"resultado_valor correto ({mission.value_description})",
        f"Ordenado {order_txt} resultado_valor",
    ]


@dataclass
class ValidationResult:
    ok: bool
    message: str
    sequence: List[str] = field(default_factory=list)
    result_preview: List[Tuple] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    checklist: List[str] = field(default_factory=list)


def _is_select_only(query: str) -> bool:
    q = query.strip().lower()
    if not q.startswith("select"):
        return False
    if ";" in q.strip().rstrip(";"):
        return False
    return not any(re.search(rf"\b{kw}\b", q) for kw in FORBIDDEN_KEYWORDS)


def get_expected_pairs(db_path: str, mission: Mission) -> List[Tuple[str, float]]:
    """Retorna [(resultado_nome, resultado_valor), ...] na ordem correta e
    COMPLETA (todos os grupos, sem corte) para a missao informada."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = conn.cursor()
        cur.execute(mission.canonical_query)
        rows = cur.fetchall()
    finally:
        conn.close()
    return [(r[0], r[1]) for r in rows]


def get_expected_sequence(db_path: str, mission: Mission) -> List[str]:
    return [name for name, _ in get_expected_pairs(db_path, mission)]


def validate_player_query(db_path: str, player_query: str, mission: Mission) -> ValidationResult:
    n_req = len(build_requirements(mission))
    checklist = ["pending"] * n_req

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

    # 3) Coluna resultado_nome presente
    col_lookup = {c.lower(): i for i, c in enumerate(columns)}
    if "resultado_nome" not in col_lookup:
        checklist[2] = "fail"
        return ValidationResult(
            False,
            "Sua query precisa de uma coluna chamada exatamente 'resultado_nome' "
            "(use um ALIAS, ex: c.nome AS resultado_nome).",
            checklist=checklist, result_preview=rows[:10], columns=columns,
        )
    checklist[2] = "ok"
    idx_nome = col_lookup["resultado_nome"]

    expected_pairs = get_expected_pairs(db_path, mission)
    expected_values: Dict[str, float] = dict(expected_pairs)
    expected_names_ordered = [n for n, _ in expected_pairs]

    submitted_names = [r[idx_nome] for r in rows]
    submitted_set = set(submitted_names)
    expected_set = set(expected_names_ordered)

    # 4) resultado_valor correto (mesmos grupos e mesmos valores; ordem ainda nao conta aqui)
    values_ok = False
    if "resultado_valor" in col_lookup and submitted_set == expected_set and len(submitted_names) == len(set(submitted_names)):
        idx_valor = col_lookup["resultado_valor"]
        values_ok = all(
            abs(float(r[idx_valor]) - expected_values.get(r[idx_nome], float("nan"))) < TOLERANCE
            for r in rows
        )

    if not values_ok:
        checklist[3] = "fail"
        if "resultado_valor" not in col_lookup:
            msg = "Falta a coluna 'resultado_valor' (use um ALIAS na sua agregacao, ex: SUM(...) AS resultado_valor)."
        elif submitted_set != expected_set:
            msg = "O conjunto de grupos (resultado_nome) nao bate com o esperado -- revise o JOIN, o WHERE e o GROUP BY."
        else:
            msg = "Os valores de resultado_valor nao batem -- confira a funcao de agregacao usada."
        return ValidationResult(False, msg, checklist=checklist, result_preview=rows[:10], columns=columns)
    checklist[3] = "ok"

    # 5) Ordenacao correta
    if submitted_names != expected_names_ordered:
        checklist[4] = "fail"
        order_txt = "DESC" if mission.order_desc else "ASC"
        return ValidationResult(
            False,
            f"Os valores estao corretos, mas a ordem nao esta -- use ORDER BY resultado_valor {order_txt}.",
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
