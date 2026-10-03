# finops-dashboard

Análise local de fatura fictícia de nuvem: importa CSV, atribui custo por projeto, detecta gasto anômalo e projeta o custo de fim de mês.

Local analysis of a fictitious cloud bill: import the CSV, attribute cost per project, detect anomalous spend, and project month-end cost.

> **Nada aqui é real.** Os valores são inventados, os serviços são nomes e nenhuma nuvem é acessada. O pacote tem **zero dependência de execução**.

## O que é

Seis meses, doze serviços, três projetos: 216 linhas de fatura. A ferramenta soma por mês e por projeto, roda três detectores de anomalia independentes e projeta o próximo mês por regressão linear — tudo com biblioteca padrão.

## Por que foi feito

Corte de custo é tarefa real de quem administra infraestrutura, e a fatura é o lugar onde o desperdício aparece primeiro. Mas fatura sem atribuição é número sem dono: ninguém age sobre "subiu 400 reais" sem saber de quem é o recurso que subiu.

O argumento deste projeto é que detecção honesta precisa de mais de um método. Nenhum número mágico separa normal de anômalo, e é por isso que três detectores rodam e o relatório mostra os três.

## Como rodar

```powershell
python -m venv .venv
.\\.venv\\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
python -m pytest tests/ -v
python -m finops --help
```

Com o ambiente ativo, o fluxo principal:

```powershell
python -m finops resumo dados/cobranca-ficticia.csv
```

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

Rodar sem instalar (útil para conferência rápida):

```powershell
$env:PYTHONPATH="$PWD\src"; python -m finops resumo dados/cobranca-ficticia.csv
```

O relatório HTML:

```powershell
python -m finops relatorio dados/cobranca-ficticia.csv --saida exemplos/relatorio-custo.html
```

Instalação:

```powershell
pip install -e ".[dev]"
```

## Os três detectores

| Método | O que pega | O que perde |
|---|---|---|
| IQR | pico isolado de 8x | elevação sustentada (é um terço dos dados, não outlier) |
| Desvio padrão | distância da média | pico único pode mascarar a si mesmo |
| Nível | segunda metade 3x acima da primeira | pico único que não move a média das metades |

Uma elevação de 5x durante dois meses em seis **não é outlier** — é mudança
de nível, e nenhuma cerca estatística a pega. Sem a terceira regra, o
vazamento mais caro dos três passava em silêncio. Cada método tem um ponto
cego que é o ponto forte de outro, e o relatório mostra os três em vez de
fingir que existe um número mágico.

Nenhum detector reporta razão abaixo de 1.5x. Séries pequenas cruzam qualquer
cerca por ruído, e um "achado" de 1.1x declara o limite do método em vez de
esconder.

## As 3 anomalias plantadas

Elas estão documentadas em `tools/gerar_csv.py`, não escondidas — uma
anomalia que ninguém sabe onde está não é critério, é loteria:

1. **pico-armazenamento** (2026-07, 8x): bucket esquecido após teste de carga.
   Os três métodos acham.
2. **vazamento-trafego** (2026-08/09, 5x): endpoint público sem limite. Só o
   nível acha.
3. **compute-fantasma** (2026-09, 6x): job no tamanho errado, uma vez. IQR e
   desvio acham.

## A projeção e o cálculo manual

Reta por mínimos quadrados nos últimos 3 meses (2847.81, 2769.72, 3782.44),
projetada para 2026-10: **4067.95**, intervalo 3810.85–4325.06. A aritmética
aberta está em `src/finops/projecao.py`, e o teste quebra se o número mudar
sem aviso.

## O que aprendi

- **Elevação sustentada não é outlier.** Dois meses em seis é um terço dos
  dados; IQR e z-score não têm como ver. Precisou de uma terceira regra, e a
  regra precisou de um nome honesto.
- **Piso de razão é declarar o limite.** Sem ele, série de 14 unidades com
  ruído de 8% gerava "anomalia" de 1.1x.
- **Dinheiro não some na agregação.** Todo caminho de soma termina conferindo
  o total; rateio que perde centavos é rateio em que ninguém confia.
- **Anomalia plantada escondida é loteria.** O critério de aceite exige as
  três identificadas, e só dá para exigir o que está documentado.
- **CLI que relata e passa ensina a ignorar.** Com anomalia alta, a saída é 1.

## Testes

```powershell
python -m pytest -v
```

59 testes, 93% de cobertura. Cobrem o importador (216 linhas, cabeçalho,
validação por linha), a atribuição com soma preservada, os três detectores
incluindo o que cada um **perde**, a projeção contra o cálculo manual, o
relatório HTML e a CLI.

```powershell
python tools/verificar_aceite.py     # as 3 anomalias + projecao + saida do CLI
python tools/verificar_encoding.py   # nenhum caractere corrompido
```

## Limitações

- **Seis meses é pouco.** Com mais história, os quartis estabilizam e o
  z-score ganha poder. Com seis, o nível faz o trabalho pesado.
- **Sem sazonalidade.** A reta não sabe que dezembro custa diferente de
  fevereiro. Projeção linear em série sazonal erra com confiança.
- **Atribuição é contábil, não causal.** Dizer que o atlas gastou 8467.81 não
  diz por que, nem se deveria.
- **O intervalo é honesto e largo.** Mais-menos um desvio dos resíduos em três
  pontos não é previsão precisa; é a incerteza declarada.
- **Sem custo real.** Nenhum número aqui corresponde a preço de provedor.

## Licença

MIT.

---

## EN

### What it is

Local analysis of a fictitious cloud bill: 6 months, 12 services, 3 projects,
216 lines. Totals per month and project, three independent anomaly detectors,
next-month projection by linear regression — stdlib only.

### Why it was built

Cost cutting is real work for anyone who administers infrastructure, and the
bill is where waste shows up first. But a bill without attribution is a number
without an owner: nobody acts on "it went up 400 reals" without knowing whose
resource went up.

The argument of this project is that honest detection needs more than one
method. No magic number separates normal from anomalous, which is why three
detectors run and the report shows all three.

### How to run

```powershell
python -m venv .venv
.\\.venv\\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
python -m pytest tests/ -v
python -m finops --help
```

Main flow:

```powershell
python -m finops resumo dados/cobranca-ficticia.csv
```

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

Run without installing (quick check):

```powershell
$env:PYTHONPATH="$PWD\src"; python -m finops resumo dados/cobranca-ficticia.csv
```

HTML report:

```powershell
python -m finops relatorio dados/cobranca-ficticia.csv --saida exemplos/relatorio-custo.html
```

### The three detectors

IQR catches the isolated 8x spike; standard deviation catches distance from
the mean; a level rule catches a sustained 5x elevation that no fence can see
(two months out of six is a third of the data, not an outlier). No detector
reports below 1.5x ratio — small series cross any fence by noise.

A 5x elevation over two months in six is **not an outlier** — it is a level
change, and no statistical fence catches it. Without the third rule, the most
expensive leak of the three passed in silence. Each method has a blind spot
that is the strength of another, and the report shows all three instead of
pretending there is a magic number.

### The 3 planted anomalies

Documented in `tools/gerar_csv.py`: an 8x storage spike, a sustained 5x
traffic leak, a one-off 6x batch job. The report must identify all three.

### Projection

Least squares on the last 3 months (2847.81, 2769.72, 3782.44), projected to
2026-10: **4067.95**, interval 3810.85–4325.06. The open arithmetic lives in
`src/finops/projecao.py`.

### Tests

59 tests, 93% coverage. They cover the importer (216 lines, header, per-line
validation), attribution with preserved sum, the three detectors including
what each one **loses**, the projection against the manual calculation, the
HTML report, and the CLI.

```powershell
python -m pytest -v
python tools/verificar_aceite.py
python tools/verificar_encoding.py
```

### What I learned

- **Sustained elevation is not an outlier.** Two out of six months is a third
  of the data; IQR and z-score cannot see it. A third rule was needed, and
  the rule needed an honest name.
- **A ratio floor declares the limit.** Without it, a series of 14 units with
  8% noise produced a "1.1x anomaly".
- **Money does not disappear in aggregation.** Every sum path ends by
  verifying the total; allocation that loses cents is one nobody trusts.
- **A hidden planted anomaly is a lottery.** The acceptance criterion demands
  all three identified, and you can only demand what is documented.
- **A CLI that reports and still passes teaches you to ignore it.** With high
  anomaly, the exit code is 1.

### Limitations

- **Six months is thin.** With more history the quartiles stabilize and z-score
  gains power; with six, the level rule does the heavy lifting.
- **No seasonality.** The line doesn't know December costs differently from
  February. Linear projection on a seasonal series is wrong with confidence.
- **Attribution is accounting, not causality.** Saying atlas spent 8467.81 does
  not say why, or whether it should have.
- **The interval is honest and wide.** Plus-minus one residual standard
  deviation over three points is not a precise forecast; it is the declared
  uncertainty.
- **No real cost.** None of these numbers corresponds to a provider's price.

### License

MIT.
