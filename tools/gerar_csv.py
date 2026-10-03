"""Gera o CSV de cobranca ficticia de forma deterministica.

Generate the fictitious billing CSV deterministically.

Seis meses, doze servicos, tres projetos: 216 linhas. Os valores tem uma
tendencia suave de alta (2% ao mes) mais um ruido fixo por semente, para que o
arquivo pareca uma fatura real sem que nenhum numero precise ser inventado a
mao - e para que a projecao por regressao tenha algo estavel para projetar.

## As 3 anomalias plantadas

Elas estao documentadas aqui e no relatorio de aceite, e nao escondidas: o
criterio de aceite do projeto e que o relatorio as identifique, e uma anomalia
que ninguem sabe onde esta nao e criterio, e loteria.

1. **pico-armazenamento** (2026-07, `armazenamento-frio`, projeto `atlas`):
   custo 8x o normal. Um bucket que alguem esqueceu de limpar depois de um
   teste de carga. O detector por IQR pega; o de desvio padrao tambem.
2. **vazamento-trafego** (2026-08, `trafego-saida`, projeto `boreas`): custo
   5x o normal por tres meses seguidos a partir de agosto. Um endpoint publico
   sem limite. So aparece como anomalia quando comparado mes a mes dentro do
   servico, nao no total.
3. **compute-fantasma** (2026-09, `compute-lote`, projeto `atlas`): custo 6x
   em um unico mes e volta ao normal. Um job que rodou no tamanho errado uma
   vez. O detector precisa achar sem que os meses vizinhos o mascarem.

Os valores normais crescem 2% ao mes com ruido de +-8% fixo por semente. Sem
tendencia, a regressao projetaria ruido; sem ruido, qualquer limiar
detectaria tudo e o teste nao provaria nada.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "dados" / "cobranca-ficticia.csv"

SEMENTE = 20261003
MESES = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]
PROJETOS = ["atlas", "boreas", "cais"]

# (servico, custo base mensal, dono principal)
SERVICOS = [
    ("compute-web", 420.0, "atlas"),
    ("compute-lote", 180.0, "atlas"),
    ("banco-relacional", 310.0, "atlas"),
    ("armazenamento-frio", 95.0, "atlas"),
    ("trafego-saida", 140.0, "boreas"),
    ("cdn-distribuicao", 110.0, "boreas"),
    ("fila-mensagens", 45.0, "boreas"),
    ("funcao-sem-servidor", 60.0, "boreas"),
    ("monitoramento", 38.0, "cais"),
    ("registros-log", 52.0, "cais"),
    ("backup-diario", 74.0, "cais"),
    ("dns-zonas", 22.0, "cais"),
]

CRESCIMENTO = 1.02
RUIDO = 0.08

# (mes, servico, projeto, multiplicador, motivo)
ANOMALIAS = [
    ("2026-07", "armazenamento-frio", "atlas", 8.0, "pico-armazenamento"),
    ("2026-08", "trafego-saida", "boreas", 5.0, "vazamento-trafego"),
    ("2026-09", "trafego-saida", "boreas", 5.0, "vazamento-trafego"),
    ("2026-09", "compute-lote", "atlas", 6.0, "compute-fantasma"),
]


def principal() -> int:
    """Gera o CSV.

    Generate the CSV.

    Returns:
        Sempre 0.
    """
    rng = random.Random(SEMENTE)
    ruido = {
        (mes, servico, projeto): 1.0 + rng.uniform(-RUIDO, RUIDO)
        for mes in MESES
        for servico, _, _ in SERVICOS
        for projeto in PROJETOS
    }
    anomalia = {(m, s, p): mult for m, s, p, mult, _ in ANOMALIAS}

    linhas = [("mes", "servico", "projeto", "custo")]
    for indice_mes, mes in enumerate(MESES):
        for servico, base, dono in SERVICOS:
            for projeto in PROJETOS:
                peso = 1.0 if projeto == dono else 0.15
                valor = base * peso * (CRESCIMENTO ** indice_mes)
                valor *= ruido[(mes, servico, projeto)]
                mult = anomalia.get((mes, servico, projeto), 1.0)
                linhas.append(
                    (mes, servico, projeto, f"{valor * mult:.2f}")
                )

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerows(linhas)

    print(f"csv gravado em {DESTINO.relative_to(RAIZ)}: {len(linhas) - 1} linhas")
    print("anomalias plantadas: pico-armazenamento, vazamento-trafego, compute-fantasma")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())