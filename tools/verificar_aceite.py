"""Prova de aceite do finops.

finops acceptance proof.

O criterio de aceite tem duas metades:

1. **O relatorio identifica as 3 anomalias plantadas.** Nao e "acha
   anomalias": sao tres especificas, documentadas em `tools/gerar_csv.py`,
   e cada uma exercita um detector diferente. Uma que falte e um detector
   cego, nao um relatorio com menos linhas.
2. **A projecao bate com o calculo manual documentado.** O numero esta
   escrito em `src/finops/projecao.py` com a aritmetica aberta. Se o metodo
   mudar e o numero mudar sem o teste quebrar, o teste e decoracao.

O script verifica ainda que o CLI devolve saida 1 quando ha anomalia alta,
porque um job que relata e passa ensina a ignorar o relatorio.
"""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from finops import anomalias as modulo_anomalias  # noqa: E402
from finops import projecao as modulo_projecao  # noqa: E402
from finops.cli import main as cli_main  # noqa: E402
from finops.importador import carregar  # noqa: E402

CSV = RAIZ / "dados" / "cobranca-ficticia.csv"

# As 3 plantadas, com o detector que cada uma exercita. A tabela esta escrita
# aqui para que o script seja juiz e nao espelho: se o codigo mudar o metodo
# que acha cada uma, e aqui que a divergencia aparece.
ESPERADAS = {
    ("2026-07", "armazenamento-frio"): "pico isolado de 8x",
    ("2026-09", "trafego-saida"): "vazamento sustentado de 5x",
    ("2026-09", "compute-lote"): "pico unico de 6x",
}

PROJECAO_ESPERADA = 4067.95


class Falha(Exception):
    """Uma condicao de aceite nao foi satisfeita."""


def checar(condicao: bool, mensagem: str) -> None:
    """Falha se a condicao e falsa.

    Args:
        condicao: A condicao.
        mensagem: O que deu errado.

    Raises:
        Falha: Se a condicao for falsa.
    """
    if not condicao:
        raise Falha(mensagem)


def principal() -> int:
    """Roda a prova de aceite.

    Returns:
        0 se tudo passar, 1 se alguma condicao falhar.
    """
    try:
        gastos = carregar(CSV)
        print(f"1) CSV com {len(gastos)} linhas carregado")

        achadas = (
            modulo_anomalias.detectar_iqr(gastos)
            + modulo_anomalias.detectar_desvio(gastos)
            + modulo_anomalias.detectar_nivel(gastos)
        )
        encontradas = {(a.mes, a.servico) for a in achadas}
        for chave, descricao in sorted(ESPERADAS.items()):
            checar(
                chave in encontradas,
                f"anomalia plantada nao identificada: {chave} ({descricao})",
            )
        print("2) as 3 anomalias plantadas foram identificadas")
        for chave in sorted(ESPERADAS):
            metodos = sorted(
                {a.metodo for a in achadas if (a.mes, a.servico) == chave}
            )
            print(f"   {chave[0]} {chave[1]}: metodos {metodos}")

        proj = modulo_projecao.projetar_total(gastos)
        checar(
            abs(proj.valor - PROJECAO_ESPERADA) < 0.01,
            f"projecao {proj.valor:.2f} difere do calculo manual "
            f"{PROJECAO_ESPERADA:.2f}",
        )
        print(f"3) projecao {proj.valor:.2f} bate com o calculo manual")

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            codigo = cli_main(["resumo", str(CSV)])
        checar(
            codigo == 1,
            f"o CLI deveria sair com 1 havendo anomalia alta, saiu com {codigo}",
        )
        print("4) o CLI devolve saida 1 quando ha anomalia alta")
    except Falha as erro:
        print("\nACEITE FALHOU:")
        print(f"  - {erro}")
        return 1

    print("\nok: 3 anomalias identificadas, projecao confere, CLI sinaliza")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())