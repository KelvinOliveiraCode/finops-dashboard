"""Testes dos detectores.

Detector tests.

Cada detector tem um ponto cego documentado, e os testes provam os dois
lados: o que cada um acha e o que cada um perde. Um teste que so verifica o
que o detector acha nao prova nada sobre o ponto cego - e o ponto cego e onde
mora o vazamento que continua custando todo mes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from finops import anomalias
from finops.anomalias import (
    METODO_DESVIO,
    METODO_IQR,
    METODO_NIVEL,
    detectar_desvio,
    detectar_iqr,
    detectar_nivel,
)
from finops.importador import carregar

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "dados" / "cobranca-ficticia.csv"


@pytest.fixture(scope="module")
def gastos():
    return carregar(CSV)


def _ids(achadas) -> set[tuple[str, str]]:
    return {(a.mes, a.servico) for a in achadas}


class TestPicoIsolado:
    """O pico de 8x em julho: os tres metodos acham."""

    @pytest.mark.parametrize("detector", [detectar_iqr, detectar_desvio, detectar_nivel])
    def test_pico_armazenamento(self, gastos, detector) -> None:
        assert ("2026-07", "armazenamento-frio") in _ids(detector(gastos))


class TestVazamentoSustentado:
    """A elevacao de 5x por dois meses: so o nivel acha."""

    def test_iqr_nao_acha(self, gastos) -> None:
        # Dois meses em seis nao e outlier: e um terco dos dados. O IQR nao
        # tem como ver isso, e o teste prova a limitacao em vez de esconder.
        assert ("2026-09", "trafego-saida") not in _ids(detectar_iqr(gastos))

    def test_desvio_nao_acha(self, gastos) -> None:
        assert ("2026-09", "trafego-saida") not in _ids(detectar_desvio(gastos))

    def test_nivel_acha(self, gastos) -> None:
        achadas = detectar_nivel(gastos)
        assert ("2026-09", "trafego-saida") in _ids(achadas)

    def test_nivel_acusa_o_pico(self, gastos) -> None:
        achada = next(
            a for a in detectar_nivel(gastos) if a.servico == "trafego-saida"
        )
        assert achada.valor == pytest.approx(750.64, abs=0.01)
        assert achada.severidade == "alta"


class TestFantasma:
    """O pico unico de 6x em setembro: iqr e desvio acham."""

    def test_compute_fantasma(self, gastos) -> None:
        assert ("2026-09", "compute-lote") in _ids(detectar_iqr(gastos))
        assert ("2026-09", "compute-lote") in _ids(detectar_desvio(gastos))


class TestSemRuido:
    """Serie pequena com ruido normal nao e anomalia."""

    def test_nenhum_detector_acusa_1_1x(self, gastos) -> None:
        for detector in (detectar_iqr, detectar_desvio, detectar_nivel):
            for achada in detector(gastos):
                assert achada.razao() >= 1.5, (
                    f"{achada.servico}: razao {achada.razao():.2f} abaixo do piso"
                )

    def test_meses_normais_limpos(self, gastos) -> None:
        for detector in (detectar_iqr, detectar_desvio, detectar_nivel):
            meses = {a.mes for a in detector(gastos)}
            assert "2026-04" not in meses
            assert "2026-05" not in meses
            assert "2026-06" not in meses


class TestContrato:
    """O formato que o relatorio consome."""

    def test_metodos_distintos(self, gastos) -> None:
        assert detectar_iqr(gastos)[0].metodo == METODO_IQR
        assert detectar_desvio(gastos)[0].metodo == METODO_DESVIO
        assert detectar_nivel(gastos)[0].metodo == METODO_NIVEL

    def test_razao(self, gastos) -> None:
        achada = next(
            a for a in detectar_iqr(gastos) if a.servico == "armazenamento-frio"
        )
        assert achada.razao() == pytest.approx(8.2, abs=0.1)

    def test_serie_curta_nao_quebra(self) -> None:
        from finops.importador import Gasto

        poucos = [
            Gasto(mes="2026-01", servico="s", projeto="p", custo=10.0, linha=1),
            Gasto(mes="2026-02", servico="s", projeto="p", custo=12.0, linha=2),
        ]
        assert detectar_iqr(poucos) == []
        assert detectar_desvio(poucos) == []
        assert detectar_nivel(poucos) == []