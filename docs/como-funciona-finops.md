# Como Funciona FinOps: as quatro alavancas de custo

Esta documentação explica as quatro alavancas que determinam o custo de executar cargas de trabalho, sem depender de nenhum provedor específico. O raciocínio vale para qualquer ambiente e usa os valores de `dados/cobranca-ficticia.csv` (estrutura `mes`, `servico`, `projeto`, `custo`).

## 1. Compute: o que é e por que domina a fatura

Compute é o custo de executar código: servidores, máquinas virtuais, containers e funções. Quase sempre lidera a fatura: paga-se pelo tempo de processamento ativo, que é praticamente tudo o que uma aplicação faz. Enquanto um arquivo é guardado no disco, o custo é pequeno; enquanto um programa roda, o preço é cobrado por cada momento em que a máquina está trabalhando.

O exemplo mais claro compara o mesmo serviço em projetos diferentes. Em abril de 2026, `compute-web` no projeto atlas registrou 388.29, enquanto a mesma categoria no projeto boreas custou 67.25, mais de cinco vezes menos. A diferença não vem do preço do serviço — vem de quantas instâncias ficam ligadas e por quanto tempo. `compute-web` representa aplicações web com tráfego constante: elas não param, e a fatura acompanha esse ritmo. Em agosto do mesmo mês, atlas chegou a 482.64, mostrando crescimento contido no comportamento de uso.

A alavanca de compute é a correspondência entre capacidade provisionada e demanda real. Instâncias dimensionadas para o pico, mas operando abaixo da capacidade durante a maior parte do dia, geram desperdício invisível no dia a dia. A correção passa por dimensionar conforme o uso efetivo, escalar diante de demanda crescente e desligar recursos que não são necessários.

`compute-lote` ilustra uma armadilha diferente. É trabalho executado em lotes agendados — extração e transformação de dados, relatórios, processamento em massa — e deveria ser intermitente. Contudo, em setembro de 2026, `compute-lote` no projeto atlas marcou 1148.71, mais de seis vezes o valor de abril (169.73). Um lote que se arrasta, fica retido ou escapa da janela planejada transforma um custo controlável em item caro da conta. A lição: vigie duração e frequência dos lotes e desligue o recurso assim que o trabalho terminar.

`funcao-sem-servidor` muda a lógica de cobrança: cobra-se por execução, não por hora ociosa. Para cargas esporádicas e variáveis, isso evita pagar por capacidade reservada que nunca é utilizada. Quando a demanda é previsível e constante, entretanto, instâncias contínuas costumam ser mais econômicas — e é exatamente o cenário de `compute-web` e `banco-relacional`, os dois itens mais caros do extrato.

## 2. Armazenamento: custo parado que cresce sozinho

Armazenamento é o oposto de compute: o dinheiro não é gasto pelo que você faz com os dados, mas pelo simples fato de eles existirem no disco, guardados, mês após mês. Por isso é chamado de custo parado que cresce sozinho — sobe sem que ninguém execute nenhum comando, basta deixar os arquivos lá.

O exemplo mais revelador é `armazenamento-frio` no projeto atlas: 97.50 em abril de 2026 e 799.93 em julho, um salto de quase oito vezes em três meses. Enquanto boreas e cais permaneciam na faixa de 14 a 16 no mesmo período, atlas acumulou dados sem política de descarte ou movimento. Arquivos de teste, snapshots antigos e cópias de projetos encerrados continuam gerando conta; o impacto só aparece ao comparar a série histórica.

`backup-diario` reforça a mesma dinâmica por outro ângulo: cada cópia criada é um objeto que nunca desaparece por si só. No projeto cais, o custo passou de 77.78 em abril para 81.35 em agosto, e a acumulação é cumulativa — cada rotina adiciona quase nada remove. A alavanca de armazenamento são políticas de ciclo de vida explícitas: definir data de expiração, mover cópias antigas para camadas mais baratas e apagar o que não tem valor. Sem isso, `armazenamento-frio` e `backup-diario` são as categorias que sobem de forma mais silenciosa e previsível.

## 3. Tráfego: custo invisível até a fatura chegar

Tráfego é o custo de mover dados para fora do ambiente de origem. Diferente de compute e armazenamento, ele não aparece como linha fixa no painel de uso: consome-se tráfego todos os dias, não se vê a conta crescer em tempo real e só se descobre o impacto quando a cobrança chega. Daí ser chamado de custo invisível até a fatura.

`trafego-saida` no projeto boreas permaneceu estável em torno de 145 a 154 entre abril e setembro, mas saltou para 709.09 em agosto e para 750.64 em setembro. O mês anterior era rotineiro; de repente, o projeto triplicou de custo. Sem monitorar a saída por dia, essa mudança passou despercebida até a cobrança. `cdn-distribuicao` comporta-se igual: boreas oscilou entre 107.53 e 128.78, sempre muito acima de atlas (16.53 a 18.69) e de cais (16.62 a 19.54), porque recebe e entrega mais dados.

`dns-zonas` completa o trio de tráfego. Embora seja um item pequeno — de 3.19 a 3.69 em atlas e de 20.68 a 25.03 em cais — cobra-se por zona registrada, e zonas esquecidas ou duplicadas somam itens inúteis na fatura. A alavanca é a visibilidade diária: acompanhar a saída por dia, dimensionar `cdn-distribuicao` apenas para quem realmente precisa de entrega distribuída e revisar `dns-zonas` periodicamente para cancelar zonas inativas. Quando se olha apenas o total do mês, o tráfego surpresa chega pronto e sem aviso.

## 4. Tempo de atividade: o multiplicador silencioso

Tempo de atividade multiplica todas as demais: cada hora extra que um recurso fica ligado aumenta compute, armazenamento, tráfego e monitoramento na mesma proporção. Um serviço que roda o dia inteiro consome o dobro de um expediente comercial; o calendário é o fator de multiplicação, e ele se aplica a tudo.

`banco-relacional` no projeto atlas manteve 315.96 em abril e 354.62 em agosto: o custo sobe porque o banco permanece acessível o dia todo, todos os dias, mesmo em turnos sem operações. `fila-mensagens` segue o mesmo padrão, embora seja menor — de 6.58 a 6.87 em cais, com pico de 53.64 em setembro: mensagens são entregues a qualquer hora e o consumo acompanha o tempo ligado. `monitoramento` e `registros-log` ilustram melhor o multiplicador: ficam ativos o tempo todo para cumprir a função, e por isso `monitoramento` em cais chegou a 41.01 e `registros-log` a 60.61, os maiores de suas categorias. Se desligarem, o problema passa despercebido; por isso ficam ligadas, e o custo se fixa como uma taxa.

A alavanca de tempo de atividade não é apagar tudo: é separar o que precisa estar online o tempo todo do que poderia ser agendado. Aplicações web e bancos de dados de produção geralmente exigem atividade contínua, mas lotes, janelas de manutenção, ambientes de desenvolvimento e projetos em desuso podem ficar parados fora da janela útil. Desligar um recurso por uma fração do mês reduz proporcionalmente `compute-web`, `banco-relacional` e tudo o que eles acionam.

Ao final, as quatro alavancas são interdependentes: compute determina o piso da conta, armazenamento sobe sem aviso, tráfego chega disfarçado e tempo de atividade multiplica cada uma delas. Gerenciar custo não é renegociar preços; é saber qual alavanca mover em cada item da fatura.
