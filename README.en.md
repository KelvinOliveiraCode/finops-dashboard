# finops-dashboard

**English** · [Português (Brasil)](README.md)

[![Python 3](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](#) [![PyYAML](https://img.shields.io/badge/PyYAML-only%20dep-3776AB?style=flat-square)](#) [![pytest](https://img.shields.io/badge/pytest-59%20tests-0A9EDC?style=flat-square&logo=pytest)](#) [![MIT License](https://img.shields.io/badge/License-MIT-f4c430?style=flat-square)](LICENSE)

## What it is

**A FinOps dashboard**: it imports simulated cloud invoices (CSV/JSON), attributes costs per team/service with rate allocation (preserves the total), detects anomalies (IQR, standard deviation, level-based), forecasts next month's spending and generates an HTML report. It is an educational FinOps lab in Python.

## Status

An educational lab, working and tested (59 tests).

## Features

- **Importer** (`importador.py`): `carregar` → `Gasto`, `meses`, `total_por_mes`.
- **Attribution** (`atribuicao.py`): `atribuir` (per team), `rateio` (preserves total), `por_equipe`.
- **Anomalies** (`anomalias.py`): `detectar_iqr`, `detectar_desvio`, `detectar_nivel` → `Anomalia` (month, category, value, method).
- **Forecast** (`projecao.py`): `projetar` (series → `Projecao`), `projetar_total`.
- **Report** (`relatorio.py`): `gerar` (HTML) and `salvar`.
- **CLI** (`finops`): `resumo`, `relatorio`, `projecao`.

## Architecture

A `finops` package with `importador`, `atribuicao`, `anomalias`, `projecao`, `relatorio` and `cli`.

## Stack

- Python ≥ 3.10, PyYAML ≥ 6.0
- pytest (dev)

## Repository layout

```
finops-dashboard/
├── src/finops/      # importador · atribuicao · anomalias · projecao · relatorio · cli
├── dados/ · docs/ · exemplos/
├── tests/           # 59 tests
└── LICENSE          # MIT
```

## Prerequisites and installation

```bash
pip install -e .
```

## How to run

```bash
finops <subcmd> dados/   # resumo|relatorio|projecao
```

## Tests and quality

```bash
PYTHONPATH=src python -m pytest tests/   # 59 passed
```

## Technical decisions

- Rate allocation preserves the total: attribution by team without inventing money.
- 3 anomaly-detection methods (IQR, standard deviation, level): covers different spending patterns.

## Known limitations

- Fictitious/example invoices — no AWS CUR, Azure EA or GCP BQ integration.
- Simple linear forecast.

## Development process

An individual project by Kelvin Oliveira, built with orchestrated AI agents and reviewed by the author.

## License and author

MIT — Copyright (c) 2026 Kelvin Rebelo de Oliveira. Author: [Kelvin Oliveira](https://github.com/KelvinOliveiraCode) · [Portfolio](https://kelvinoliveiracode.github.io/portfolio/)
