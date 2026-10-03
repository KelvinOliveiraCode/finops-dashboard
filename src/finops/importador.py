"""Leitura e validacao do CSV de cobranca ficticia.

Read and validate the fictitious billing CSV.

Este modulo e o contrato do projeto: todo o resto consome a lista de `Gasto`
que ele produz. Separar leitura de analise e o que permite que um CSV
malformado produza erro com linha e motivo, e nao um `ValueError` tres
niveis acima no calculo da projecao.

## O que e ficticio e o que e real

Os valores sao inventados, mas a **estrutura** e real: mes, servico, projeto,
custo. Uma fatura de nuvem tem exatamente essas colunas, e o resto do projeto
nao distingue uma fatura real de uma inventada. E por isso que o validador e
rigoroso com formato e frouxo com valor: formato errado quebra conta, valor
"estranho" e justamente o que as anomalias procuram.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

# Colunas exigidas, nesta ordem. A ordem importa porque o CSV e posicional:
# uma coluna trocada de lugar sem trocar o cabecalho corrompe tudo em
# silencio, e o validador precisa pegar isso antes de qualquer soma.
COLUNAS = ("mes", "servico", "projeto", "custo")

# Mes no formato AAAA-MM. Sem dia: fatura e mensal, e dia inventado e ruido.
PADRAO_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class ErroDeFatura(Exception):
    """O CSV nao pode ser lido como fatura.

    The CSV cannot be read as a bill.
    """


@dataclass(frozen=True)
class Gasto:
    """Uma linha de cobranca: quanto, de que, de quem, quando.

    A billing line: how much, of what, of whom, when.

    Attributes:
        mes: O mes de referencia, `AAAA-MM`.
        servico: O nome do servico, como aparece na fatura.
        projeto: O projeto ao qual o custo pertence.
        custo: O valor, em unidades ficticias de moeda.
        linha: O numero da linha no CSV, para o erro apontar o lugar.
    """

    mes: str
    servico: str
    projeto: str
    custo: float
    linha: int = 0

    def chave(self) -> tuple[str, str, str]:
        """A identidade da linha para agregacao.

        The line's identity for aggregation.

        Returns:
            O trio `(mes, servico, projeto)`.
        """
        return (self.mes, self.servico, self.projeto)


def carregar(caminho: str | Path) -> list[Gasto]:
    """Le o CSV e devolve os gastos validados.

    Read the CSV and return the validated charges.

    Args:
        caminho: O arquivo CSV.

    Returns:
        Os gastos, na ordem do arquivo.

    Raises:
        ErroDeFatura: Se o arquivo nao existir, o cabecalho divergir, ou
            alguma linha tiver mes ou custo invalido. A mensagem cita a
            linha, porque "linha 142" e acionavel e "dado invalido" nao e.
    """
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroDeFatura(f"arquivo nao encontrado: {caminho}")

    try:
        texto = caminho.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as erro:
        raise ErroDeFatura(f"{caminho}: nao decodifica como UTF-8 ({erro})") from None

    leitor = csv.reader(texto.splitlines())
    try:
        cabecalho = next(leitor)
    except StopIteration:
        raise ErroDeFatura(f"{caminho}: arquivo vazio") from None

    if tuple(c.strip() for c in cabecalho) != COLUNAS:
        raise ErroDeFatura(
            f"{caminho}: cabecalho {cabecalho} difere do esperado {list(COLUNAS)}"
        )

    gastos: list[Gasto] = []
    for numero, linha in enumerate(leitor, start=2):
        if not linha or all(not c.strip() for c in linha):
            continue
        if len(linha) != len(COLUNAS):
            raise ErroDeFatura(
                f"{caminho}: linha {numero} tem {len(linha)} colunas, "
                f"esperava {len(COLUNAS)}"
            )
        mes, servico, projeto, custo_bruto = (c.strip() for c in linha)
        if not PADRAO_MES.match(mes):
            raise ErroDeFatura(
                f"{caminho}: linha {numero}: mes {mes!r} fora do formato AAAA-MM"
            )
        if not servico:
            raise ErroDeFatura(f"{caminho}: linha {numero}: servico vazio")
        if not projeto:
            raise ErroDeFatura(f"{caminho}: linha {numero}: projeto vazio")
        try:
            custo = float(custo_bruto.replace(",", "."))
        except ValueError:
            raise ErroDeFatura(
                f"{caminho}: linha {numero}: custo {custo_bruto!r} nao e numero"
            ) from None
        if custo < 0:
            raise ErroDeFatura(
                f"{caminho}: linha {numero}: custo negativo {custo}"
            )
        gastos.append(
            Gasto(mes=mes, servico=servico, projeto=projeto, custo=custo, linha=numero)
        )

    if not gastos:
        raise ErroDeFatura(f"{caminho}: nenhuma linha de gasto valida")
    return gastos


def meses(gastos: list[Gasto]) -> list[str]:
    """Os meses presentes, em ordem.

    The months present, in order.

    Args:
        gastos: Os gastos.

    Returns:
        Os meses distintos, ordenados.
    """
    return sorted({g.mes for g in gastos})


def total_por_mes(gastos: list[Gasto]) -> list[tuple[str, float]]:
    """O total de cada mes, em ordem.

    Each month's total, in order.

    Args:
        gastos: Os gastos.

    Returns:
        Pares `(mes, total)`.
    """
    totais: dict[str, float] = {}
    for gasto in gastos:
        totais[gasto.mes] = totais.get(gasto.mes, 0.0) + gasto.custo
    return [(mes, totais[mes]) for mes in sorted(totais)]