# finops

Análise local de fatura fictícia de nuvem: importa o CSV, atribui custo por
projeto, detecta gasto anômalo e projeta o custo de fim de mês.

Local analysis of a fictitious cloud bill: import the CSV, attribute cost per
project, detect anomalous spend and project month-end cost.

> **Nada aqui é real.** Os valores são inventados, os serviços são nomes e
> nenhuma nuvem é acessada. O pacote tem **zero dependência de execução**.

## O que é

Seis meses, doze serviços, três projetos: 216 linhas de fatura. A ferramenta
soma por mês e por projeto, roda três detectores de anomalia independentes e
projeta o próximo mês por regressão linear — tudo com biblioteca padrão.

## Por que foi feito

Corte de custo é tarefa real de quem administra infraestrutura, e a fatura é
o lugar onde o desperdício aparece primeiro. Mas fatura sem atribuição é
número sem dono: ninguém age sobre "subiu 400 reais" sem saber de quem é o
recurso que subiu.

O argumento deste projeto é que detecção honesta precisa de mais de um
método. Nenhum número mágico separa normal de anômalo, e é por isso que três
detectores rodam e o relatório mostra os três.

## Como rodar

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
  ...
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

## English

Local analysis of a fictitious cloud bill: 6 months, 12 services, 3 projects,
216 lines. Totals per month and project, three independent anomaly detectors,
next-month projection by linear regression — stdlib only.

### The three detectors

IQR catches the isolated 8x spike; standard deviation catches distance from
the mean; a level rule catches sustained 5x elevation that no fence can see
(two months out of six is a third of the data, not an outlier). No detector
reports below 1.5x ratio — small series cross any fence by noise.

### The 3 planted anomalies

Documented in `tools/gerar_csv.py`: an 8x storage spike, a sustained 5x
traffic leak, a one-off 6x batch job. The report must identify all three.

### Projection

Least squares on the last 3 months, projected to 2026-10: **4067.95**. The
open arithmetic lives in `src/finops/projecao.py`.

### Tests

59 tests, 93% coverage.

```powershell
python -m pytest -v
python tools/verificar_aceite.py
python tools/verificar_encoding.py
```

### Limitations

Six months is thin; no seasonality; attribution is accounting, not causality;
the interval is honestly wide; no real prices.

### License

MIT.