# finops-dashboard

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-independent-blue?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square" alt="Dependencies">
</p>

Local analysis of a fictional cloud bill: imports CSV, attributes cost per project, detects anomalous spend, and projects end-of-month cost. Zero runtime dependencies.

## Problem / Why it exists

Cost cutting is a real task for whoever runs infrastructure, and the bill is where waste shows up first. But a bill without attribution is a number without an owner: nobody acts on "rose 400 reais" without knowing which resource rose. No magic number separates normal from anomalous, so detecting with a single method leaves blind spots — a leak that keeps running costs every month, not once.

## What it does

Reads a billing CSV with columns `month`, `service`, `project`, `cost` (216 rows, six months, twelve services, three projects in the example file), sums totals per month and per project, runs three independent anomaly detectors (IQR, standard deviation, level), projects next month's cost by linear regression over the last three months, and emits an HTML report. Exit code is 1 when there is a high-severity anomaly, because a job that reports and passes teaches people to ignore the report.

## Stack

- Python 3.10+
- Standard library only (`csv`, `statistics`, `argparse`, `pathlib`, `dataclasses`, `html`, `re`) — zero runtime dependencies
- pytest for development tests
- setuptools packaging, `src/` layout

## How it works

The importer reads and validates the CSV row by row: fixed header, month in `YYYY-MM` format, non-negative cost, and errors that cite the file line.

Attribution sums each spend to the project named in the CSV and preserves the total: the largest group receives total minus the sum of the others, so the sum of the groups matches the direct sum of spend.

The three detectors operate on the monthly series per service:

- IQR: isolated peak outside the interquartile range.
- Standard deviation: distance from the mean in deviations (z-score).
- Level: sustained elevation between the first and second half of the series.

No detector reports a ratio below 1.5x, to avoid declaring small-series noise as an anomaly.

The projection fits a line by least squares over the totals of the last three months and projects one month ahead, with an interval of plus-minus one population standard deviation of the residuals.

The HTML report highlights months with anomalies and shows the projection with its interval.

## How to run

Create the environment and install:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

Run the tests:

```powershell
python -m pytest tests/ -v
```

Main flow:

```powershell
python -m finops resumo dados/cobranca-ficticia.csv
```

Example output:

```
TOTAL POR MES
  2026-04     1984.26
  2026-05     2020.70
  2026-06     2102.25
  2026-07     2847.81
  2026-08     2769.72
  2026-09     3782.44
TOTAL POR PROJETO
  atlas         8467.81
  boreas        4565.24
  cais          2474.13
ANOMALIAS: 6
  2026-07 armazenamento-frio/atlas 799.93 (iqr, alta)
  2026-09 compute-lote/atlas 1148.71 (iqr, alta)
  2026-07 armazenamento-frio/atlas 799.93 (desvio, alta)
  2026-09 compute-lote/atlas 1148.71 (desvio, alta)
  2026-07 armazenamento-frio/atlas 799.93 (nivel, alta)
  2026-09 trafego-saida/boreas 750.64 (nivel, alta)
```

HTML report:

```powershell
python -m finops relatorio dados/cobranca-ficticia.csv --saida exemplos/relatorio-custo.html
```

Projection only:

```powershell
python -m finops projecao dados/cobranca-ficticia.csv
```

Run without installing:

```powershell
$env:PYTHONPATH="$PWD\src"; python -m finops resumo dados/cobranca-ficticia.csv
```

Acceptance proof (three planted anomalies, projection against manual calculation, CLI exit code 1):

```powershell
python tools/verificar_aceite.py
```

Encoding check for files:

```powershell
python tools/verificar_encoding.py
```

## Project structure

```
finops-dashboard/
├── dados/
│   └── cobranca-ficticia.csv   # fictional bill: 216 rows, 6 months, 12 services, 3 projects
├── docs/
│   ├── como-funciona-finops.md
│   └── metodo-de-deteccao-de-anomalia.md
├── exemplos/
│   └── relatorio-custo.html    # generated HTML report
├── src/
│   └── finops/
│       ├── __init__.py         # version 1.0.0
│       ├── __main__.py         # enables python -m finops
│       ├── cli.py              # 3 commands: resumo, relatorio, projecao
│       ├── importador.py       # CSV reading and validation (Gasto, ErroDeFatura)
│       ├── atribuicao.py       # sum by project, by team, shared allocation
│       ├── anomalias.py        # IQR, deviation, level detectors (Anomalia)
│       └── projecao.py         # linear regression, 3 months, interval (Projecao)
├── tests/                      # pytest tests
├── tools/
│   ├── gerar_csv.py            # generates the CSV deterministically (fixed seed)
│   ├── verificar_aceite.py     # acceptance proof: 3 anomalies, projection, CLI output
│   └── verificar_encoding.py   # checks file corruption
├── pyproject.toml              # metadata, scripts, pytest and coverage config
├── requirements.txt            # zero runtime dependencies; pytest for dev
├── LICENSE                     # MIT
└── README.md
```

## Trade-offs and decisions

Zero runtime dependencies: statistics uses `statistics` and the rest is arithmetic. Writing the regression and quartiles by hand costs effort, but the package runs on any Python 3.10 without installing anything beyond.

Three detectors instead of one: each has a blind spot that is another's strength. IQR does not see sustained elevation (two months out of six is a third of the data, not an outlier); standard deviation can be masked by a huge peak that pulls the mean; level does not catch a single peak. The report shows all three instead of pretending a magic number exists.

1.5x ratio floor: small series cross any fence by noise. A "finding" of 1.1x declares the method's limit, not hides it.

Preserved sum in attribution: the largest group receives total minus the sum of the others, so the sum of the groups matches the direct sum of the 216 spends. Allocation that loses cents is allocation nobody trusts.

Three-month projection window without seasonality: December costs differently from February, and the line does not know that. It is linear projection with declared uncertainty, not precise forecast.

Pure HTML without CDN or external font: the example opens with a double click on any machine, including without internet.

Exit code 1 with high anomaly: a job that reports and passes is worse than one that reports and fails.

## Known limitations

Six months is little history. With more data, quartiles stabilize and z-score gains power; with six, the level rule does the heavy lifting.

No seasonality: linear projection on a seasonal series is wrong with confidence.

Attribution is accounting, not causal: saying atlas spent 8467.81 does not say why, nor whether it should.

The projection interval is honest and wide: plus-minus one deviation of residuals across three points is not a precise forecast, it is the declared uncertainty.

No real cost: no number matches a provider's price. The CSV is fictional, services are names, no cloud is accessed.

## License

MIT.

## Author

Kelvin Oliveira