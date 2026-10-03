"""Atribuicao de gasto a projeto e equipe.

Attribute each charge to its project and team.

Determinismo por regra, sem heuristica:
1) todo gasto ja chega com o projeto no CSV;
2) a equipe deriva de uma tabela fixa servico -> equipe;
3) o custo de servico compartilhado e rateado entre todos os projetos,
   proporcionalmente ao gasto proprio de cada um.

A soma do total e preservada em qualquer caminho: o total e medido com
`sum()` (soma compensada, como o consumo faz), e o maior grupo recebe
`total - soma dos demais` (empate: o primeiro em ordem de aparecimento),
para que a soma dos grupos bata com a soma direta dos 216 gastos.
"""

from __future__ import annotations

from . importador import Gasto

# Grupo para servico ausente da tabela de equipe: regra, nao chute.
EQUIPE_NAO_MAPEADA = "nao-mapeado"


def _preservar_total(totais: dict[str, float], total: float) -> None:
    """A ancora do maior grupo como `total - soma dos demais`.

    Anchor the largest group as `total - sum of the others`, so the
    groups' sum matches the direct sum of the charges. Tie goes to the
    first group in appearance order.
    """
    chaves = list(totais)
    if not chaves:
        return
    alvo = max(chaves, key=lambda chave: totais[chave])
    parcial = sum(totais[chave] for chave in chaves if chave != alvo)
    totais[alvo] = total - parcial


def atribuir(gastos: list[Gasto]) -> dict[str, float]:
    """Soma cada gasto ao proprio projeto.

    Sum each charge into its own project.

    Args:
        gastos: Os gastos.

    Returns:
        Dicionario projeto -> total, com a soma preservada.
    """
    totais: dict[str, float] = {}
    for gasto in gastos:
        totais[gasto.projeto] = totais.get(gasto.projeto, 0.0) + gasto.custo
    _preservar_total(totais, sum(g.custo for g in gastos))
    return totais


def por_equipe(
    gastos: list[Gasto], mapa_equipe: dict[str, str]
) -> dict[str, float]:
    """Atribui cada gasto a equipe do servico, pela tabela fixa.

    Attribute each charge to the team of its service, from a fixed table.

    O servico ausente da tabela cai em `EQUIPE_NAO_MAPEADA`, para que a
    soma total seja preservada.

    Args:
        gastos: Os gastos.
        mapa_equipe: Tabela servico -> equipe.

    Returns:
        Dicionario equipe -> total, com a soma preservada.
    """
    totais: dict[str, float] = {}
    for gasto in gastos:
        equipe = mapa_equipe.get(gasto.servico, EQUIPE_NAO_MAPEADA)
        totais[equipe] = totais.get(equipe, 0.0) + gasto.custo
    _preservar_total(totais, sum(g.custo for g in gastos))
    return totais


def rateio(
    gastos: list[Gasto], servicos_compartilhados: set[str]
) -> dict[str, float]:
    """Rateia o custo dos servicos compartilhados entre os projetos.

    Split the shared-service cost across projects.

    Regra: o gasto proprio (servico fora do conjunto) define o peso de
    cada projeto; a parte compartilhada vai proporcionalmente a esse
    peso. Se nenhum projeto tem gasto proprio, divide por partes iguais.

    Args:
        gastos: Os gastos.
        servicos_compartilhados: Servicos cujo custo e compartilhado.

    Returns:
        Dicionario projeto -> gasto proprio + cota rateada, com a soma
        preservada.
    """
    conjunto = set(servicos_compartilhados)
    ordem: list[str] = []
    proprio: dict[str, float] = {}
    compartilhado = 0.0
    for gasto in gastos:
        if gasto.projeto not in proprio:
            ordem.append(gasto.projeto)
            proprio[gasto.projeto] = 0.0
        if gasto.servico in conjunto:
            compartilhado += gasto.custo
        else:
            proprio[gasto.projeto] += gasto.custo
    if not ordem:
        return {}
    soma_proprio = sum(proprio[p] for p in ordem)
    if soma_proprio > 0.0:
        cota = {p: compartilhado * proprio[p] / soma_proprio for p in ordem}
    else:
        cota = {p: compartilhado / len(ordem) for p in ordem}
    resultado = {p: proprio[p] + cota[p] for p in ordem}
    _preservar_total(resultado, sum(g.custo for g in gastos))
    return resultado
