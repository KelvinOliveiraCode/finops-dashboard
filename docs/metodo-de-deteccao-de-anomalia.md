# Método de detecção de anomalia

Este documento explica os dois detectores do projeto, quando cada um funciona
e quando cada um mente. A tese e simples: nenhum metodo sozinho distingue
"gasto alto porque cresceu" de "gasto alto porque vazou", e e por isso que o
projeto roda os dois e mostra os dois.

## IQR: a caixa que ignora os extremos

O metodo do intervalo interquartil olha a distribuicao dos ultimos meses e
pergunta se o mes atual esta fora da caixa. Com fator 1.5, tudo que esta a
mais de uma caixa e meia acima do terceiro quartil e anomalia.

O ponto forte do IQR e que ele nao assume forma: a serie pode crescer, cair
ou oscilar, e o metodo so olha posicao relativa. O ponto fraco e amostra
pequena - com seis meses, um unico pico move os quartis e o metodo pode
engolir a propria anomalia que deveria achar.

E por isso que o `pico-armazenamento` (8x em 2026-07) e o caso ideal para o
IQR: um ponto isolado, longe de tudo, que nenhum quartil absorve.

## Desvio padrão: a distância da média

O z-score pergunta a quantos desvios o mes atual esta da media. Com limiar
2.0, tudo alem de dois desvios e anomalia.

O ponto forte e a sensibilidade a sequencia: tres meses seguidos 5x acima
(`vazamento-trafego`, de agosto em diante) deslocam a media e inflam o
desvio, e o metodo continua acusando porque a distancia persiste. O ponto
fraco e o inverso do IQR: um unico pico gigante (`compute-fantasma`, 6x em
setembro) puxa a media para cima e pode mascarar a si mesmo se o limiar for
alto demais.

## Por que os dois, e por que separados

Cada metodo tem um ponto cego que e o ponto forte do outro. Rodar os dois e
mostrar os dois no relatorio nao e redundancia: e a unica forma honesta de
dizer "este mes e estranho" sem fingir que existe um numero magico que
separa normal de anomalo.

Os dois detectores operam **por servico**, nunca no total. Uma anomalia de
um servico some no total quando os outros onze estao normais, e um total
anormal sem servico apontado nao diz onde olhar. A granularidade e parte do
metodo, nao detalhe de apresentacao.

## Limiares: o que muda quando mudam

`--fator` e `--limiar` existem na CLI porque nao ha valor certo. Fator menor
acha mais, com mais falso positivo; limiar maior acha menos, com mais falso
negativo. O padrao (1.5 e 2.0) e o da literatura, e qualquer mudanca deve vir
com o motivo escrito - "o time ignorava o relatorio" e motivo, "quero menos
linha" nao e.
