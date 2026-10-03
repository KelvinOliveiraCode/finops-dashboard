"""Testes do relatorio e da CLI.

Report and CLI tests.

O relatorio e HTML para gente ler, e a CLI e o portao que decide o codigo de
saida. Um relatorio que escapa errado e uma pagina quebrada; uma CLI que
devolve zero com anomalia alta e um job que ensina a ignorar o relatorio.
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest

from finops import anomalias, relatorio
from finops.importador import carregar, total_por_mes
from finops import atribuicao
from finops import projecao
from finops.cli import main as cli_main

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "dados" / "cobranca-ficticia.csv"


@pytest.fixture(scope="module")
def contexto():
    gastos = carregar(CSV)
    return {
        "gastos": gastos,
        "totais": total_por_mes(gastos),
        "por_projeto": atribuicao.atribuir(gastos),
        "anomalias": (
            anomalias.detectar_iqr(gastos)
            + anomalias.detectar_desvio(gastos)
            + anomalias.detectar_nivel(gastos)
        ),
        "projecao": projecao.projetar_total(gastos),
    }


class TestRelatorio:
    """O HTML gerado."""

    def test_tem_as_tabelas(self, contexto) -> None:
        html_texto = relatorio.gerar(
            "T", contexto["totais"], contexto["por_projeto"],
            contexto["anomalias"], contexto["projecao"],
        )
        assert "<table>" in html_texto
        assert "2026-07" in html_texto
        assert "armazenamento-frio" in html_texto

    def test_mes_anomalo_destacado(self, contexto) -> None:
        html_texto = relatorio.gerar(
            "T", contexto["totais"], contexto["por_projeto"],
            contexto["anomalias"], contexto["projecao"],
        )
        assert "background:" in html_texto

    def test_projecao_com_intervalo(self, contexto) -> None:
        html_texto = relatorio.gerar(
            "T", contexto["totais"], contexto["por_projeto"],
            contexto["anomalias"], contexto["projecao"],
        )
        assert "4067.95" in html_texto

    def test_escapa_nome_malicioso(self, contexto) -> None:
        html_texto = relatorio.gerar(
            "<script>alert(1)</script>", contexto["totais"],
            contexto["por_projeto"], [], contexto["projecao"],
        )
        assert "<script>" not in html_texto

    def test_salvar_cria_o_arquivo(self, contexto, tmp_path: Path) -> None:
        destino = relatorio.salvar("<html></html>", tmp_path / "sub" / "r.html")
        assert destino.exists()

    def test_sem_anomalias_mostra_mensagem(self, contexto) -> None:
        html_texto = relatorio.gerar(
            "T", contexto["totais"], contexto["por_projeto"],
            [], contexto["projecao"],
        )
        assert "nenhuma anomalia" in html_texto


class TestCli:
    """Os tres comandos e o codigo de saida."""

    def _roda(self, argv):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            codigo = cli_main(argv)
        return codigo, buffer.getvalue()

    def test_resumo_mostra_totais(self) -> None:
        codigo, saida = self._roda(["resumo", str(CSV)])
        assert "TOTAL POR MES" in saida
        assert "2026-09" in saida
        assert codigo == 1

    def test_projecao_mostra_numero(self) -> None:
        codigo, saida = self._roda(["projecao", str(CSV)])
        assert codigo == 0
        assert "4067.95" in saida
        assert "2026-10" in saida

    def test_relatorio_gera_html(self, tmp_path: Path) -> None:
        destino = tmp_path / "r.html"
        codigo, _ = self._roda(["relatorio", str(CSV), "--saida", str(destino)])
        assert destino.exists()
        assert "armazenamento-frio" in destino.read_text(encoding="utf-8")

    def test_csv_inexistente_saida_dois(self, tmp_path: Path) -> None:
        codigo = cli_main(["resumo", str(tmp_path / "nao-existe.csv")])
        assert codigo == 2

    def test_help_sai_com_zero(self) -> None:
        with pytest.raises(SystemExit) as erro:
            cli_main(["--help"])
        assert erro.value.code == 0

    @pytest.mark.parametrize("comando", ["resumo", "relatorio", "projecao"])
    def test_help_de_cada_comando(self, comando: str) -> None:
        with pytest.raises(SystemExit) as erro:
            cli_main([comando, "--help"])
        assert erro.value.code == 0

    def test_sem_comando_falha(self) -> None:
        with pytest.raises(SystemExit):
            cli_main([])