"""A linha de comando do finops.

The finops command line.

Tres comandos: `resumo` imprime totais e anomalias no terminal, `relatorio`
gera o HTML, e `projecao` mostra so a previsao. O codigo de saida e 1 quando
ha anomalia de severidade alta, porque um job que relata e passa e pior do
que um job que relata e falha - o primeiro ensina a ignorar o relatorio.
"""

from __future__ import annotations

import argparse
import sys

from . import anomalias as modulo_anomalias
from . import atribuicao as modulo_atribuicao
from . import importador as modulo_importador
from . import projecao as modulo_projecao
from . import relatorio as modulo_relatorio

SAIDA_OK = 0
SAIDA_ANOMALIA = 1
SAIDA_ERRO = 2


def _constroi_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos.

    Build the argument parser.

    Returns:
        O parser pronto.
    """
    parser = argparse.ArgumentParser(
        prog="finops",
        description=(
            "Analisa fatura ficticia de nuvem localmente. / "
            "Analyze a fictitious cloud bill locally."
        ),
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_resumo = sub.add_parser("resumo", help="totais e anomalias no terminal")
    p_resumo.add_argument("csv", help="o CSV de cobranca")
    p_resumo.add_argument("--fator", type=float, default=1.5)
    p_resumo.add_argument("--limiar", type=float, default=2.0)

    p_relatorio = sub.add_parser("relatorio", help="gera o HTML")
    p_relatorio.add_argument("csv", help="o CSV de cobranca")
    p_relatorio.add_argument("--saida", required=True)
    p_relatorio.add_argument("--fator", type=float, default=1.5)
    p_relatorio.add_argument("--limiar", type=float, default=2.0)

    p_projecao = sub.add_parser("projecao", help="mostra so a previsao")
    p_projecao.add_argument("csv", help="o CSV de cobranca")

    return parser


def _dados(argumentos):
    """Carrega e agrega o CSV.

    Load and aggregate the CSV.

    Args:
        argumentos: Os argumentos parseados.

    Returns:
        O trio `(gastos, totais, por_projeto)`.
    """
    gastos = modulo_importador.carregar(argumentos.csv)
    totais = modulo_importador.total_por_mes(gastos)
    por_projeto = modulo_atribuicao.atribuir(gastos)
    return gastos, totais, por_projeto


def _cmd_resumo(argumentos, destino) -> int:
    """Executa `resumo`.

    Run `resumo`.

    Args:
        argumentos: Os argumentos.
        destino: Onde imprimir.

    Returns:
        O codigo de saida.
    """
    gastos, totais, por_projeto = _dados(argumentos)
    print("TOTAL POR MES", file=destino)
    for mes, total in totais:
        print(f"  {mes}  {total:10.2f}", file=destino)
    print("TOTAL POR PROJETO", file=destino)
    for projeto, total in sorted(por_projeto.items()):
        print(f"  {projeto:<10} {total:10.2f}", file=destino)

    achadas = (
        modulo_anomalias.detectar_iqr(gastos, fator=argumentos.fator)
        + modulo_anomalias.detectar_desvio(gastos, limiar=argumentos.limiar)
        + modulo_anomalias.detectar_nivel(gastos)
    )
    print(f"ANOMALIAS: {len(achadas)}", file=destino)
    for anomalia in achadas:
        print(
            f"  {anomalia.mes} {anomalia.servico}/{anomalia.projeto} "
            f"{anomalia.valor:.2f} ({anomalia.metodo}, {anomalia.severidade})",
            file=destino,
        )

    altas = [a for a in achadas if a.severidade == "alta"]
    return SAIDA_ANOMALIA if altas else SAIDA_OK


def _cmd_relatorio(argumentos, destino) -> int:
    """Executa `relatorio`.

    Run `relatorio`.

    Args:
        argumentos: Os argumentos.
        destino: Onde imprimir.

    Returns:
        O codigo de saida.
    """
    gastos, totais, por_projeto = _dados(argumentos)
    achadas = (
        modulo_anomalias.detectar_iqr(gastos, fator=argumentos.fator)
        + modulo_anomalias.detectar_desvio(gastos, limiar=argumentos.limiar)
        + modulo_anomalias.detectar_nivel(gastos)
    )
    proj = modulo_projecao.projetar_total(gastos)
    html_texto = modulo_relatorio.gerar(
        "Relatorio de custo - fatura ficticia",
        totais,
        por_projeto,
        achadas,
        proj,
    )
    caminho = modulo_relatorio.salvar(html_texto, argumentos.saida)
    print(f"relatorio gravado em {caminho}", file=destino)
    print(
        f"projecao {proj.mes}: {proj.valor:.2f} "
        f"({proj.minimo:.2f} a {proj.maximo:.2f})",
        file=destino,
    )
    altas = [a for a in achadas if a.severidade == "alta"]
    return SAIDA_ANOMALIA if altas else SAIDA_OK


def _cmd_projecao(argumentos, destino) -> int:
    """Executa `projecao`.

    Run `projecao`.

    Args:
        argumentos: Os argumentos.
        destino: Onde imprimir.

    Returns:
        Sempre 0.
    """
    gastos = modulo_importador.carregar(argumentos.csv)
    proj = modulo_projecao.projetar_total(gastos)
    print(
        f"{proj.mes}: {proj.valor:.2f} "
        f"(intervalo {proj.minimo:.2f} a {proj.maximo:.2f}, "
        f"inclinacao {proj.inclinacao:.2f}/mes)",
        file=destino,
    )
    return SAIDA_OK


def main(argv: list[str] | None = None) -> int:
    """O ponto de entrada.

    The entry point.

    Args:
        argv: Os argumentos, sem `argv[0]`.

    Returns:
        O codigo de saida.
    """
    parser = _constroi_parser()
    argumentos = parser.parse_args(argv)

    acoes = {
        "resumo": _cmd_resumo,
        "relatorio": _cmd_relatorio,
        "projecao": _cmd_projecao,
    }
    acao = acoes.get(argumentos.comando)
    if acao is None:
        parser.error(f"comando desconhecido: {argumentos.comando}")
        return SAIDA_ERRO

    try:
        return acao(argumentos, sys.stdout)
    except modulo_importador.ErroDeFatura as erro:
        print(f"erro de fatura: {erro}", file=sys.stderr)
        return SAIDA_ERRO


if __name__ == "__main__":
    main()