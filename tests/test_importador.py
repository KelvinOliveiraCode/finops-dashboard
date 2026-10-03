"""Testes do importador.

Importer tests.

O importador e o contrato do projeto: todo o resto consome a lista de `Gasto`
que ele produz. Um CSV malformado que passa daqui vira `ValueError` tres niveis
acima, no calculo da projecao, onde ninguem entende a origem.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from finops.importador import COLUNAS, ErroDeFatura, carregar, meses, total_por_mes

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "dados" / "cobranca-ficticia.csv"


class TestCsvReal:
    """O CSV do projeto carrega e tem a forma esperada."""

    def test_carrega_216_linhas(self) -> None:
        assert len(carregar(CSV)) == 216

    def test_seis_meses(self) -> None:
        assert meses(carregar(CSV)) == [
            "2026-04", "2026-05", "2026-06",
            "2026-07", "2026-08", "2026-09",
        ]

    def test_doze_servicos_tres_projetos(self) -> None:
        gastos = carregar(CSV)
        assert len({g.servico for g in gastos}) == 12
        assert {g.projeto for g in gastos} == {"atlas", "boreas", "cais"}

    def test_totais_batem_com_o_documentado(self) -> None:
        totais = dict(total_por_mes(carregar(CSV)))
        assert totais["2026-04"] == pytest.approx(1984.26, abs=0.01)
        assert totais["2026-07"] > 2700.0

    def test_nenhum_custo_negativo(self) -> None:
        assert all(g.custo >= 0 for g in carregar(CSV))


class TestCabecalho:
    """O cabecalho e a primeira coisa a quebrar."""

    def test_arquivo_inexistente(self, tmp_path: Path) -> None:
        with pytest.raises(ErroDeFatura):
            carregar(tmp_path / "nao-existe.csv")

    def test_arquivo_vazio(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "vazio.csv"
        arquivo.write_text("", encoding="utf-8")
        with pytest.raises(ErroDeFatura):
            carregar(arquivo)

    def test_cabecalho_trocado(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "x.csv"
        arquivo.write_text("mes,projeto,servico,custo\n", encoding="utf-8")
        with pytest.raises(ErroDeFatura):
            carregar(arquivo)


class TestLinhas:
    """Cada linha e validada com numero para o erro ser acionavel."""

    def _csv(self, tmp_path: Path, linhas: str) -> Path:
        arquivo = tmp_path / "x.csv"
        arquivo.write_text("mes,servico,projeto,custo\n" + linhas, encoding="utf-8")
        return arquivo

    def test_mes_fora_do_formato(self, tmp_path: Path) -> None:
        with pytest.raises(ErroDeFatura):
            carregar(self._csv(tmp_path, "04/2026,s,p,10\n"))

    def test_custo_nao_numero(self, tmp_path: Path) -> None:
        with pytest.raises(ErroDeFatura):
            carregar(self._csv(tmp_path, "2026-04,s,p,dez\n"))

    def test_custo_negativo(self, tmp_path: Path) -> None:
        with pytest.raises(ErroDeFatura):
            carregar(self._csv(tmp_path, "2026-04,s,p,-5\n"))

    def test_colunas_a_menos(self, tmp_path: Path) -> None:
        with pytest.raises(ErroDeFatura):
            carregar(self._csv(tmp_path, "2026-04,s,p\n"))

    def test_linha_vazia_ignorada(self, tmp_path: Path) -> None:
        gastos = carregar(self._csv(tmp_path, "2026-04,s,p,10\n\n"))
        assert len(gastos) == 1
        assert gastos[0].linha == 2

    def test_chave_de_agregacao(self, tmp_path: Path) -> None:
        gastos = carregar(self._csv(tmp_path, "2026-04,s,p,10\n"))
        assert gastos[0].chave() == ("2026-04", "s", "p")