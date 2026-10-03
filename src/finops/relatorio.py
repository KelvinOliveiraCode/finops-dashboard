"""Relatorio HTML do custo.

Cost HTML report.

O relatorio e para gente, nao para maquina: tabela por mes, destaque para
anomalia, projecao com intervalo. HTML puro, sem dependencia, porque o
exemplo vai para o repositorio e precisa abrir com duplo clique em qualquer
maquina - inclusive sem internet, ja que nao ha CDN nem fonte externa.

## Por que HTML e nao texto

O criterio de aceite pede `exemplos/relatorio-custo.html`. Um relatorio em
texto listaria os mesmos numeros, mas anomalia em texto corrido e facil de
passar batido. A tabela com a linha destacada e o que faz o olho parar no
lugar certo, e e por isso que o formato importa aqui.
"""

from __future__ import annotations

import html
from pathlib import Path

# Cor da linha de anomalia. Vermelho claro sobre texto escuro: visivel sem
# gritar, e legivel para quem tem daltonismo comum.
COR_ANOMALIA = "#f8d7da"
COR_PROJECAO = "#d1ecf1"


def _celda(texto: str) -> str:
    """Uma celula escapada.

    An escaped cell.

    Args:
        texto: O conteudo.

    Returns:
        O HTML da celula, sem risco de injecao via nome de servico.
    """
    return f"<td>{html.escape(texto)}</td>"


def gerar(
    titulo: str,
    totais: list[tuple[str, float]],
    por_projeto: dict[str, float],
    anomalias: list,
    projecao,
) -> str:
    """Monta o HTML completo.

    Build the complete HTML.

    Args:
        titulo: O titulo da pagina.
        totais: Pares `(mes, total)`.
        por_projeto: Total por projeto.
        anomalias: As anomalias detectadas.
        projecao: A projecao com valor, minimo e maximo.

    Returns:
        O documento HTML.
    """
    meses_anomalos = {a.mes for a in anomalias}

    linhas_totais = []
    for mes, total in totais:
        destaque = (
            f' style="background:{COR_ANOMALIA}"' if mes in meses_anomalos else ""
        )
        linhas_totais.append(
            f"<tr{destaque}>{_celda(mes)}{_celda(f'{total:.2f}')}</tr>"
        )

    linhas_projeto = [
        f"<tr>{_celda(projeto)}{_celda(f'{total:.2f}')}</tr>"
        for projeto, total in sorted(por_projeto.items())
    ]

    linhas_anomalias = []
    for anomalia in anomalias:
        linhas_anomalias.append(
            "<tr>"
            f"{_celda(anomalia.mes)}{_celda(anomalia.servico)}"
            f"{_celda(anomalia.projeto)}{_celda(f'{anomalia.valor:.2f}')}"
            f"{_celda(anomalia.metodo)}{_celda(anomalia.severidade)}"
            "</tr>"
        )
    corpo_anomalias = (
        "\n".join(linhas_anomalias)
        if linhas_anomalias
        else '<tr><td colspan="6">nenhuma anomalia detectada</td></tr>'
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>{html.escape(titulo)}</title>
<style>
body {{ font-family: sans-serif; max-width: 900px; margin: 2em auto; padding: 0 1em; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 2em; }}
th, td {{ border: 1px solid #999; padding: 0.4em 0.8em; text-align: left; }}
th {{ background: #eee; }}
.projecao {{ background: {COR_PROJECAO}; padding: 1em; }}
</style>
</head>
<body>
<h1>{html.escape(titulo)}</h1>

<h2>Total por mes</h2>
<table>
<tr><th>Mes</th><th>Total</th></tr>
{"".join(linhas_totais)}
</table>

<h2>Total por projeto</h2>
<table>
<tr><th>Projeto</th><th>Total</th></tr>
{"".join(linhas_projeto)}
</table>

<h2>Anomalias detectadas</h2>
<table>
<tr><th>Mes</th><th>Servico</th><th>Projeto</th><th>Valor</th><th>Metodo</th><th>Severidade</th></tr>
{corpo_anomalias}
</table>

<h2>Projecao fim de mes</h2>
<div class="projecao">
<p><strong>{projecao.mes}:</strong> {projecao.valor:.2f}
(intervalo {projecao.minimo:.2f} a {projecao.maximo:.2f})</p>
</div>

<p><small>Valores ficticios. Gerado localmente, sem acesso a nuvem.</small></p>
</body>
</html>
"""


def salvar(html_texto: str, caminho: str | Path) -> Path:
    """Grava o HTML em disco.

    Write the HTML to disk.

    Args:
        html_texto: O documento.
        caminho: O destino.

    Returns:
        O caminho gravado.
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(html_texto + "\n", encoding="utf-8", newline="\n")
    return caminho