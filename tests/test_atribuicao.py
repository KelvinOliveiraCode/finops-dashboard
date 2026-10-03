"""Testes da atribuicao.

Attribution tests.

A atribuicao tem uma propriedade que nenhum teste de formato pega: **a soma
total e preservada em qualquer caminho**. Dinheiro nao some nem aparece quando
muda de coluna. Todo teste aqui termina conferindo isso, porque um rateio que
perde centavos e um rateio que ninguem confia.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from finops import atribuicao
from finops.importador import carregar

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "dados" / "cobranca-ficticia.csv"


@pytest.fixture(scope="module")
def gastos():
    return carregar(CSV)


def _soma(gastos) -> float:
    return sum(g.custo for g in gastos)


class TestAtribuir:
    """Soma por projeto."""

    def test_tres_projetos(self, gastos) -> None:
        por_projeto = atribuicao.atribuir(gastos)
        assert set(por_projeto) == {"atlas", "boreas", "cais"}

    def test_soma_preservada(self, gastos) -> None:
        por_projeto = atribuicao.atribuir(gastos)
        assert sum(por_projeto.values()) == pytest.approx(_soma(gastos))

    def test_atlas_domina(self, gastos) -> None:
        por_projeto = atribuicao.atribuir(gastos)
        assert por_projeto["atlas"] > por_projeto["boreas"] > por_projeto["cais"]


class TestPorEquipe:
    """Agregacao por equipe via tabela fixa."""

    def test_mapa_total(self, gastos) -> None:
        mapa = {s: "todas" for s in {g.servico for g in gastos}}
        resultado = atribuicao.por_equipe(gastos, mapa)
        assert sum(resultado.values()) == pytest.approx(_soma(gastos))

    def test_servico_fora_do_mapa(self, gastos) -> None:
        resultado = atribuicao.por_equipe(gastos, {})
        assert sum(resultado.values()) == pytest.approx(_soma(gastos))


class TestRateio:
    """Custo compartilhado dividido proporcionalmente."""

    def test_rateio_preserva_soma(self, gastos) -> None:
        resultado = atribuicao.rateio(gastos, {"monitoramento", "dns-zonas"})
        assert sum(resultado.values()) == pytest.approx(_soma(gastos))

    def test_rateio_vazio_e_atribuicao_direta(self, gastos) -> None:
        assert atribuicao.rateio(gastos, set()) == pytest.approx(
            atribuicao.atribuir(gastos)
        )