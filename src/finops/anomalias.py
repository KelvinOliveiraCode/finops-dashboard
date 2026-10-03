"""Deteccao de anomalias por IQR e desvio padrao.

Anomaly detection by IQR and standard deviation.

Dois detectores independentes sobre a serie mensal de cada servico, mais uma
regra de nivel para mudanca sustentada. Cada um tem um ponto cego que e o
ponto forte de outro, e e por isso que o projeto roda os tres e mostra os
tres: nenhum numero magico separa normal de anomalo.

## IQR: posicao relativa, sem forma assumida

O intervalo interquartil olha onde o mes atual cai na distribuicao e nao
assume crescimento, queda ou oscilacao. Com seis meses, um unico pico move os
quartis - e e por isso que o `pico-armazenamento` (8x isolado) e o caso ideal:
nenhum quartil o absorve.

## Desvio padrao: distancia da media

O z-score acusa o que esta longe da media. Um pico unico gigante puxa a media
para cima e pode mascarar a si mesmo se o limiar for alto - e e por isso que o
limiar e parametro, nao constante.

## Nivel: mudanca sustentada, nao ponto isolado

Uma elevacao de 5x durante dois meses em seis nao e outlier: e um terco dos
dados, e nenhuma cerca estatistica a pega. E mudanca de nivel, e se detecta
comparando metades - media da segunda metade contra media da primeira. Sem
esta regra, o `vazamento-trafego` passa pelos dois detectores acima em
silencio, e e justamente o caso mais caro dos tres: um vazamento que continua
custa todo mes, enquanto um pico custa uma vez.

## Piso de razao

Nenhum detector reporta razao abaixo de 1.5x. Series pequenas (14 unidades
contra ruido de 8%) cruzam qualquer cerca por acaso, e um "achado" de 1.1x
nao e anomalia: e o metodo dizendo que nao sabe medir serie pequena. O piso
nao esconde o problema, ele declara o limite.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from .importador import Gasto

METODO_IQR = "iqr"
METODO_DESVIO = "desvio"
METODO_NIVEL = "nivel"

SEVERIDADE_ALTA = "alta"
SEVERIDADE_MEDIA = "media"

# Piso de razao: abaixo disso, nenhum detector reporta. Series pequenas
# cruzam qualquer cerca por ruido, e um "achado" de 1.1x declara o limite do
# metodo em vez de esconder.
PISO_RAZAO = 1.5


@dataclass(frozen=True)
class Anomalia:
    """Um mes estranho em um servico.

    A strange month in a service.

    Attributes:
        mes: O mes acusado, `AAAA-MM`.
        servico: O servico.
        projeto: O projeto.
        valor: O custo observado.
        esperado: O centro da distribuicao (mediana ou media).
        metodo: `iqr` ou `desvio`.
        severidade: `alta` ou `media`.
    """

    mes: str
    servico: str
    projeto: str
    valor: float
    esperado: float
    metodo: str
    severidade: str

    def razao(self) -> float:
        """Quantas vezes acima do esperado.

        How many times above expected.

        Returns:
            `valor / esperado`, ou infinito se o esperado e zero.
        """
        if self.esperado == 0:
            return float("inf")
        return self.valor / self.esperado


def _series(gastos: list[Gasto]) -> dict[tuple[str, str], list[tuple[str, float]]]:
    """Agrupa os gastos em series mensais por servico e projeto.

    Group charges into monthly series per service and project.

    Args:
        gastos: Os gastos.

    Returns:
        Mapa `(servico, projeto)` para lista de `(mes, custo)` ordenada.
    """
    series: dict[tuple[str, str], dict[str, float]] = {}
    for gasto in gastos:
        chave = (gasto.servico, gasto.projeto)
        series.setdefault(chave, {})[gasto.mes] = (
            series.setdefault(chave, {}).get(gasto.mes, 0.0) + gasto.custo
        )
    return {
        chave: sorted(meses.items()) for chave, meses in series.items()
    }


def _quartis(valores: list[float]) -> tuple[float, float, float]:
    """Os tres quartis por interpolacao linear.

    The three quartiles by linear interpolation.

    `statistics.quantiles` exige n>=4 em algumas versoes e arredonda de um
    jeito que move o limiar entre execucoes. Interpolacao propria, deterministica.

    Args:
        valores: Os valores.

    Returns:
        O trio `(q1, mediana, q3)`.
    """
    ordenados = sorted(valores)
    n = len(ordenados)

    def percentil(p: float) -> float:
        if n == 1:
            return ordenados[0]
        posicao = p * (n - 1)
        base = int(posicao)
        resto = posicao - base
        if base + 1 >= n:
            return ordenados[-1]
        return ordenados[base] * (1 - resto) + ordenados[base + 1] * resto

    return percentil(0.25), percentil(0.5), percentil(0.75)


def detectar_iqr(
    gastos: list[Gasto], fator: float = 1.5
) -> list[Anomalia]:
    """Detecta por intervalo interquartil.

    Detect by interquartile range.

    Args:
        gastos: Os gastos.
        fator: Multiplicador da largura da caixa. Menor acha mais, com mais
            falso positivo.

    Returns:
        As anomalias, ordenadas por mes e servico.
    """
    achadas: list[Anomalia] = []
    for (servico, projeto), serie in _series(gastos).items():
        valores = [valor for _, valor in serie]
        if len(valores) < 4:
            continue
        q1, mediana, q3 = _quartis(valores)
        largura = q3 - q1
        teto = q3 + fator * largura
        for mes, valor in serie:
            if valor > teto:
                razao = valor / mediana if mediana else float("inf")
                if razao < PISO_RAZAO:
                    continue
                achadas.append(
                    Anomalia(
                        mes=mes,
                        servico=servico,
                        projeto=projeto,
                        valor=valor,
                        esperado=mediana,
                        metodo=METODO_IQR,
                        severidade=SEVERIDADE_ALTA if razao >= 3.0 else SEVERIDADE_MEDIA,
                    )
                )
    return sorted(achadas, key=lambda a: (a.mes, a.servico))


def detectar_desvio(
    gastos: list[Gasto], limiar: float = 2.0
) -> list[Anomalia]:
    """Detecta por distancia da media em desvios.

    Detect by distance from the mean in deviations.

    Args:
        gastos: Os gastos.
        limiar: Z-score minimo. Maior acha menos, com mais falso negativo.

    Returns:
        As anomalias, ordenadas por mes e servico.
    """
    achadas: list[Anomalia] = []
    for (servico, projeto), serie in _series(gastos).items():
        valores = [valor for _, valor in serie]
        if len(valores) < 3:
            continue
        media = statistics.fmean(valores)
        desvio = statistics.pstdev(valores)
        if desvio == 0:
            continue
        for mes, valor in serie:
            escore = (valor - media) / desvio
            if escore >= limiar:
                razao = valor / media if media else float("inf")
                if razao < PISO_RAZAO:
                    continue
                achadas.append(
                    Anomalia(
                        mes=mes,
                        servico=servico,
                        projeto=projeto,
                        valor=valor,
                        esperado=media,
                        metodo=METODO_DESVIO,
                        severidade=SEVERIDADE_ALTA if razao >= 3.0 else SEVERIDADE_MEDIA,
                    )
                )
    return sorted(achadas, key=lambda a: (a.mes, a.servico))


def detectar_nivel(
    gastos: list[Gasto], razao_minima: float = 3.0
) -> list[Anomalia]:
    """Detecta mudanca sustentada de nivel entre metades.

    Detect sustained level change between halves.

    Uma elevacao longa nao e outlier: e um terco dos dados, e nenhuma cerca a
    pega. E mudanca de nivel, e so aparece comparando metades - media da
    segunda contra media da primeira. Sem esta regra, um vazamento que continua
    custa todo mes e passa pelos dois detectores acima em silencio.

    Args:
        gastos: Os gastos.
        razao_minima: Razao minima entre metades para acusar.

    Returns:
        As anomalias, ordenadas por mes e servico. O mes acusado e o de maior
        valor na segunda metade, porque e para la que o olho vai primeiro.
    """
    achadas: list[Anomalia] = []
    for (servico, projeto), serie in _series(gastos).items():
        valores = [valor for _, valor in serie]
        if len(valores) < 4:
            continue
        meio = len(valores) // 2
        base = sum(valores[:meio]) / meio
        recente = sum(valores[meio:]) / (len(valores) - meio)
        if base == 0:
            continue
        razao = recente / base
        if razao >= razao_minima:
            mes_pico, valor_pico = max(serie[meio:], key=lambda par: par[1])
            achadas.append(
                Anomalia(
                    mes=mes_pico,
                    servico=servico,
                    projeto=projeto,
                    valor=valor_pico,
                    esperado=base,
                    metodo=METODO_NIVEL,
                    severidade=SEVERIDADE_ALTA,
                )
            )
    return sorted(achadas, key=lambda a: (a.mes, a.servico))