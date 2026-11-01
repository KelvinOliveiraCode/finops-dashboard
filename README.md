# finops-dashboard

[English](README.en.md) · **Português (Brasil)**

[![Python 3](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](#) [![PyYAML](https://img.shields.io/badge/PyYAML-%C3%BAnica%20dep-3776AB?style=flat-square)](#) [![pytest](https://img.shields.io/badge/pytest-59%20testes-0A9EDC?style=flat-square&logo=pytest)](#) [![MIT License](https://img.shields.io/badge/License-MIT-f4c430?style=flat-square)](LICENSE)

## O que é

**Dashboard FinOps**: importa faturas de nuvem fictícias (CSV/JSON), atribui custos por time/serviço com rateio (preserva o total), detecta anomalias (IQR, desvio-padrão, nível), projeta gasto do próximo mês e gera relatório HTML. É um laboratório educacional de FinOps em Python.

## Status

Laboratório educacional funcional e testado (59 testes).

## Funcionalidades

- **Importador** (`importador.py`): `carregar` → `Gasto`, `meses`, `total_por_mes`.
- **Atribuição** (`atribuicao.py`): `atribuir` (por time), `rateio` (preserva total), `por_equipe`.
- **Anomalias** (`anomalias.py`): `detectar_iqr`, `detectar_desvio`, `detectar_nivel` → `Anomalia` (mês, categoria, valor, método).
- **Projeção** (`projecao.py`): `projetar` (série → `Projecao`), `projetar_total`.
- **Relatório** (`relatorio.py`): `gerar` (HTML) e `salvar`.
- **CLI** (`finops`): `resumo`, `relatorio`, `projecao`.

## Arquitetura

Pacote `finops` com `importador`, `atribuicao`, `anomalias`, `projecao`, `relatorio` e `cli`.

## Stack

- Python ≥ 3.10, PyYAML ≥ 6.0
- pytest (dev)

## Estrutura

```
finops-dashboard/
├── src/finops/      # importador · atribuicao · anomalias · projecao · relatorio · cli
├── dados/
├── docs/
├── exemplos/
├── tests/           # 59 testes
└── LICENSE          # MIT
```

## Pré-requisitos e instalação

```bash
pip install -e .
```

## Como executar

```bash
finops <subcmd> dados/   # resumo|relatorio|projecao
```

## Testes e qualidade

```bash
PYTHONPATH=src python -m pytest tests/   # 59 passed
```

## Decisões técnicas

- Rateio preserva total: atribuição por time sem inventar dinheiro.
- 3 métodos de detecção de anomalia (IQR, desvio-padrão, nível): cobertura de diferentes padrões de gasto.

## Limitações

- Faturas fictícias/exemplos — sem integração com AWS CUR, Azure EA ou GCP BQ.
- Projeção linear simples.

## Processo de desenvolvimento

Projeto individual de Kelvin Oliveira, construído com agentes de IA orquestrados e revisado pelo autor.

## Licença e autor

MIT — Copyright (c) 2026 Kelvin Rebelo de Oliveira. Autor: [Kelvin Oliveira](https://github.com/KelvinOliveiraCode) · [Portfólio](https://kelvinoliveiracode.github.io/portfolio/)
