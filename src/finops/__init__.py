"""finops - analise local de fatura ficticia de nuvem.

finops - local analysis of a fictitious cloud bill.

Importa o CSV, atribui custo por projeto, detecta anomalia e projeta o fim
do mes. Nada acessa nuvem: o CSV e ficticio, os servicos sao nomes, e o resto
e aritmetica.
"""

from __future__ import annotations

__version__ = "1.0.0"

__all__ = ["__version__"]