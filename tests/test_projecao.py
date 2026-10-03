"""Testes da projecao.

Projection tests.

A projecao tem um numero que nao pode mudar sem motivo: o calculo manual
documentado no modulo. Se alguem trocar o metodo e o numero mudar, o teste
quebra - e e para quebrar, porque projecao que muda sem aviso e projecao em
que ninguem confia.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from finops import projecao
from finops.importador import carregar, total_por_mes
from finops.projecao import JANELA, Projecao, projetar, projetar_total

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "dados" / "cobranca-ficticia.csv"


class TestCalculoManual:
    """O numero documentado no modulo."""

    def test_projecao_do_csv(self) -> None:
        resultado = projetar_total(carregar(CSV))
        assert resultado.mes == "2026-10"
        assert resultado.valor == pytest.approx(4067.95, abs=0.01)
        assert resultado.inclinacao == pytest.approx(467.32, abs=0.01)

    def test_intervalo_contem_o_valor(self) -> None:
        resultado = projetar_total(carregar(CSV))
        assert resultado.minimo < resultado.valor < resultado.maximo

    def test_intervalo_nao_e_zero_com_ruido(self) -> None:
        assert projetar_total(carregar(CSV)).largura() > 0


class TestReta:
    """A matematica, isolada dos dados."""

    def test_serie_linear_tem_intervalo_zero(self) -> None:
        serie = [("2026-01", 100.0), ("2026-02", 200.0), ("2026-03", 300.0)]
        resultado = projetar(serie)
        assert resultado.valor == pytest.approx(400.0)
        assert resultado.largura() == pytest.approx(0.0)
        assert resultado.inclinacao == pytest.approx(100.0)

    def test_serie_constante(self) -> None:
        serie = [("2026-01", 50.0), ("2026-02", 50.0), ("2026-03", 50.0)]
        resultado = projetar(serie)
        assert resultado.valor == pytest.approx(50.0)
        assert resultado.inclinacao == pytest.approx(0.0)

    def test_usa_no_maximo_a_janela(self) -> None:
        serie = [(f"2026-{m:02d}", 10.0) for m in range(1, 7)]
        serie.append(("2026-07", 1000.0))
        resultado = projetar(serie)
        assert resultado.valor > 500.0

    def test_serie_curta_falha(self) -> None:
        with pytest.raises(ValueError):
            projetar([("2026-01", 10.0)])

    def test_virada_de_ano(self) -> None:
        serie = [("2026-10", 10.0), ("2026-11", 20.0), ("2026-12", 30.0)]
        assert projetar(serie).mes == "2027-01"


class TestContrato:
    """O formato que o relatorio consome."""

    def test_campos(self) -> None:
        resultado = projetar_total(carregar(CSV))
        for campo in ("mes", "valor", "minimo", "maximo", "inclinacao"):
            assert getattr(resultado, campo) is not None

    def test_projecao_e_imutavel(self) -> None:
        resultado = projetar_total(carregar(CSV))
        with pytest.raises(AttributeError):
            resultado.valor = 0.0  # type: ignore[misc]