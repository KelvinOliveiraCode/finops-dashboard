"""Projecao fim de mes por regressao linear.

Month-end projection by linear regression.

Reta por minimos quadrados sobre os totais dos ultimos 3 meses, projetada um
mes adiante, com intervalo de mais-menos um desvio dos residuos. Sem numpy:
seis pontos cabem em aritmetica a mao, e dependencia para isso seria peso
morto.

## O calculo manual esperado

Com os totais 2026-07 = 2847.81, 2026-08 = 2769.72, 2026-09 = 3782.44, em
x = 0, 1, 2 (valores exatos, sem arredondar intermediarios):

- media de x = 1, media de y = 3133.3233
- inclinacao = [(0-1)(2847.81-3133.3233) + (2-1)(3782.44-3133.3233)] / 2
  = (285.5133 + 649.1167) / 2 = 467.315
- intercepto = 3133.3233 - 467.315 = 2666.0083
- projecao do mes 3 (2026-10) = 2666.0083 + 467.315 * 3 = 4067.9533

O intervalo e mais-menos um desvio padrao populacional dos residuos. O teste
`test_projecao_manual` confere esses numeros com tolerancia de centavos, para
que qualquer mudanca no metodo quebre o teste em vez de passar despercebida.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from .importador import Gasto, total_por_mes

JANELA = 3


@dataclass(frozen=True)
class Projecao:
    """A previsao de um mes.

    A forecast for one month.

    Attributes:
        mes: O mes projetado, `AAAA-MM`.
        valor: O valor central da reta.
        minimo: O piso do intervalo.
        maximo: O teto do intervalo.
        inclinacao: A inclinacao da reta, em unidades por mes.
    """

    mes: str
    valor: float
    minimo: float
    maximo: float
    inclinacao: float

    def largura(self) -> float:
        """A largura do intervalo.

        The interval width.

        Returns:
            `maximo - minimo`. Zero significa serie perfeitamente linear.
        """
        return self.maximo - self.minimo


def _proximo_mes(mes: str) -> str:
    """O mes seguinte a um `AAAA-MM`.

    The month after an `AAAA-MM`.

    Args:
        mes: O mes de referencia.

    Returns:
        O mes seguinte, com virada de ano.
    """
    ano, numero = int(mes[:4]), int(mes[5:7])
    if numero == 12:
        return f"{ano + 1}-01"
    return f"{ano}-{numero + 1:02d}"


def projetar(serie: list[tuple[str, float]]) -> Projecao:
    """Ajusta a reta e projeta um mes adiante.

    Fit the line and project one month ahead.

    Args:
        serie: Pares `(mes, valor)` em ordem. Usa no maximo os ultimos
            `JANELA` pontos; serie mais longa e truncada, nao rejeitada.

    Returns:
        A projecao. Com serie perfeitamente linear, o intervalo colapsa:
        residuos zero implicam desvio zero.

    Raises:
        ValueError: Se a serie tiver menos de 2 pontos.
    """
    pontos = serie[-JANELA:]
    if len(pontos) < 2:
        raise ValueError("projecao precisa de ao menos 2 pontos")

    n = len(pontos)
    media_x = (n - 1) / 2
    media_y = sum(valor for _, valor in pontos) / n
    numerador = sum(
        (indice - media_x) * (valor - media_y)
        for indice, (_, valor) in enumerate(pontos)
    )
    denominador = sum((indice - media_x) ** 2 for indice in range(n))
    inclinacao = numerador / denominador if denominador else 0.0
    intercepto = media_y - inclinacao * media_x

    valor = intercepto + inclinacao * n
    residuos = [
        valor_real - (intercepto + inclinacao * indice)
        for indice, (_, valor_real) in enumerate(pontos)
    ]
    desvio = statistics.pstdev(residuos) if len(residuos) > 1 else 0.0

    return Projecao(
        mes=_proximo_mes(pontos[-1][0]),
        valor=valor,
        minimo=valor - desvio,
        maximo=valor + desvio,
        inclinacao=inclinacao,
    )


def projetar_total(gastos: list[Gasto]) -> Projecao:
    """Projeta o total do proximo mes.

    Project next month's total.

    Args:
        gastos: Os gastos.

    Returns:
        A projecao a partir dos ultimos `JANELA` meses.
    """
    return projetar(total_por_mes(gastos))