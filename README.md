# finops-dashboard

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/licen%C3%A7a-MIT-yellow?style=flat-square" alt="Licença">
  <img src="https://img.shields.io/badge/plataforma-independente-blue?style=flat-square" alt="Plataforma">
  <img src="https://img.shields.io/badge/depend%C3%Aancias-zero-brightgreen?style=flat-square" alt="Dependências">
</p>

Analise local de fatura fictícia de nuvem: importa CSV, atribui custo por projeto, detecta gasto anômalo e projeta o custo de fim de mês. Zero dependência de execução.

## Problema / Por que existe

Corte de custo é tarefa real de quem administra infraestrutura, e a fatura é onde o desperdício aparece primeiro. Mas fatura sem atribuição é número sem dono: ninguém age sobre "subiu 400 reais" sem saber de quem é o recurso que subiu. Nenhum número mágico separa normal de anômalo, então detectar com um método só deixa pontos cegos — um vazamento que continua custa todo mês, não uma vez.

## O que faz

Lê um CSV de cobrança com colunas `mes`, `servico`, `projeto`, `custo` (216 linhas, seis meses, doze serviços, três projetos no arquivo de exemplo), soma totais por mês e por projeto, executa três detectores de anomalia independentes (IQR, desvio padrão, nível), projeta o custo do mês seguinte por regressão linear sobre os últimos três meses, e emite um relatório HTML. O código de saída é 1 quando há anomalia de severidade alta, porque um job que relata e passa ensina a ignorar o relatório.

## Stack

- Python 3.10+
- Biblioteca padrão apenas (`csv`, `statistics`, `argparse`, `pathlib`, `dataclasses`, `html`, `re`) — zero dependência de execução
- pytest para testes de desenvolvimento
- Empacotamento com setuptools, layout `src/`

## Como funciona

O importador lê e valida o CSV linha a linha: cabeçalho fixo, mês no formato `AAAA-MM`, custo não negativo, e erros que citam a linha do arquivo.

A atribuição soma cada gasto ao projeto informado no CSV e preserva o total: o maior grupo recebe total menos a soma dos demais, para que a soma dos grupos bata com a soma direta dos gastos.

Os três detectores operam por série mensal de serviço:

- IQR: pico isolado fora do intervalo interquartil.
- Desvio padrão: distância da média em desvios (z-score).
- Nível: elevação sustentada entre a primeira e a segunda metade da série.

Nenhum detector reporta razão abaixo de 1.5x, para não declarar ruído de série pequena como anomalia.

A projeção ajusta uma reta por mínimos quadrados sobre os totais dos últimos três meses e projeta um mês adiante, com intervalo de mais-menos um desvio padrão populacional dos resíduos.

O relatório HTML destaca meses com anomalia e mostra a projeção com intervalo.

## Como rodar

Crie o ambiente e instale:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

Execute os testes:

```powershell
python -m pytest tests/ -v
```

Fluxo principal:

```powershell
python -m finops resumo dados/cobranca-ficticia.csv
```

Saída de exemplo:

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

Relatório HTML:

```powershell
python -m finops relatorio dados/cobranca-ficticia.csv --saida exemplos/relatorio-custo.html
```

Apenas projeção:

```powershell
python -m finops projecao dados/cobranca-ficticia.csv
```

Rodar sem instalar:

```powershell
$env:PYTHONPATH="$PWD\src"; python -m finops resumo dados/cobranca-ficticia.csv
```

Prova de aceite (as três anomalias plantadas, projeção contra cálculo manual, saída 1 do CLI):

```powershell
python tools/verificar_aceite.py
```

Conferência de encoding dos arquivos:

```powershell
python tools/verificar_encoding.py
```

## Estrutura do projeto

```
finops-dashboard/
├── dados/
│   └── cobranca-ficticia.csv   # fatura fictícia: 216 linhas, 6 meses, 12 serviços, 3 projetos
├── docs/
│   ├── como-funciona-finops.md
│   └── metodo-de-deteccao-de-anomalia.md
├── exemplos/
│   └── relatorio-custo.html    # relatório HTML gerado
├── src/
│   └── finops/
│       ├── __init__.py         # versão 1.0.0
│       ├── __main__.py         # permite python -m finops
│       ├── cli.py              # 3 comandos: resumo, relatorio, projecao
│       ├── importador.py       # leitura e validação do CSV (Gasto, ErroDeFatura)
│       ├── atribuicao.py       # soma por projeto, por equipe, rateio compartilhado
│       ├── anomalias.py        # detectores IQR, desvio, nível (Anomalia)
│       └── projecao.py         # regressão linear, 3 meses, intervalo (Projecao)
├── tests/                      # testes pytest
├── tools/
│   ├── gerar_csv.py            # gera o CSV de forma determinística (semente fixa)
│   ├── verificar_aceite.py     # prova de aceite: 3 anomalias, projeção, saída CLI
│   └── verificar_encoding.py   # confere corrompimento de arquivos
├── pyproject.toml              # metadados, scripts, config de pytest e coverage
├── requirements.txt            # zero dependência de execução; pytest para dev
├── LICENSE                     # MIT
└── README.md
```

## Trade-offs e decisões

Zero dependência de execução: a estatística usa `statistics` e o restante é aritmética. Custa escrever a regressão e os quartis à mão, mas o pacote roda em qualquer Python 3.10 sem instalar nada além.

Três detectores em vez de um: cada um tem um ponto cego que é o ponto forte de outro. IQR não vê elevação sustentada (dois meses em seis é um terço dos dados, não outlier); desvio padrão pode ser mascarado por um pico gigante que puxa a média; nível não pega pico único. O relatório mostra os três em vez de fingir que existe um número mágico.

Piso de razão 1.5x: séries pequenas cruzam qualquer cerca por ruído. Um "achado" de 1.1x declara o limite do método, não esconde.

Soma preservada na atribuição: o maior grupo recebe total menos a soma dos demais, para que a soma dos grupos bata com a soma direta dos 216 gastos. Rateio que perde centavos é rateio em que ninguém confia.

Projeção em janela de 3 meses sem sazonalidade: dezembro custa diferente de fevereiro, e a reta não sabe disso. É projeção linear com incerteza declarada, não previsão precisa.

HTML puro sem CDN nem fonte externa: o exemplo abre com duplo clique em qualquer máquina, inclusive sem internet.

Código de saída 1 com anomalia alta: um job que relata e passa é pior que um que relata e falha.

## Limitações conhecidas

Seis meses é pouco histórico. Com mais dados, os quartis estabilizam e o z-score ganha poder; com seis, a regra de nível faz o trabalho pesado.

Sem sazonalidade: projeção linear em série sazonal erra com confiança.

Atribuição é contábil, não causal: dizer que o atlas gastou 8467.81 não diz por que, nem se deveria.

O intervalo da projeção é honesto e largo: mais-menos um desvio dos resíduos em três pontos não é previsão precisa, é a incerteza declarada.

Sem custo real: nenhum número corresponde a preço de provedor. O CSV é fictício, os serviços são nomes, nenhuma nuvem é acessada.

## Licença

MIT.

## Autor

Kelvin Oliveira
