Mestre, vamos continuar o projeto hedgeAgent / Hedge Evolution Lab.

Contexto geral:
Estou construindo do zero um projeto chamado hedgeAgent, agora focado no Hedge Evolution Lab: um laboratório evolutivo para descobrir, simular, combinar e evoluir estratégias de hedge híbridas, principalmente inspiradas nas minhas estratégias de hedge para GOLD/XAUUSD, mas sempre pensando em multiativos e multitimes/timeframes.

Objetivo maior:
Não quero apenas criar mais um EA de hedge. Quero construir uma máquina de descoberta de estratégias, capaz de:

- representar estratégias como genomas;
- simular milhares/milhões/bilhões de cenários;
- testar range, spike, tendência, gap, spread alto, slippage e mercados laterais;
- medir risco real, não apenas lucro;
- evoluir combinações de lógicas de hedge;
- descobrir estratégias novas, possivelmente misturando ideias que já criei;
- identificar falhas estruturais;
- promover apenas estratégias robustas;
- futuramente usar agentes/LLM para inventar, criticar, mutar e julgar estratégias.

Tese central:
As estratégias de hedge não eliminam risco. Elas transformam risco direcional em:

- tempo;
- margem;
- volume bruto;
- distância de recuperação;
- custo operacional;
- risco de tendência;
- risco de gap;
- risco de execução.

Então o objetivo não é buscar ilusão de lucro infinito sem risco. O objetivo é descobrir estruturas que:

- lucrem bem em ranges;
- sobrevivam a spikes;
- reduzam dano em tendências fortes;
- controlem volume bruto;
- controlem net exposure;
- eliminem ordens antigas com lucro real;
- passem o risco para estruturas mais novas de forma controlada;
- saibam parar de abrir novas camadas quando o risco fica ruim;
- possam operar com lógica multiativo/multitimeframe.

Famílias de estratégias que deram origem ao projeto:

1. P1-Net:
Estratégia que mantém o NET fixo em módulo.
Exemplo:
NET = BuyLots - SellLots.
O EA tenta ficar sempre em +NetAbsLots ou -NetAbsLots.
Se está NET +0.02 e o preço cai RangePts, abre SELL suficiente para virar para -0.02.
Se está NET -0.02 e o preço sobe RangePts, abre BUY suficiente para virar para +0.02.
Ponto forte: matemática limpa, controle de net.
Ponto fraco: net pequeno não significa risco pequeno, pois gross lots pode crescer muito.

2. HedgeCycle Recovery:
Estratégia que abre posição inicial, monta hedge/travamento quando preço anda contra e faz recovery fechando a ordem perdedora antiga usando lucro de hedges/opostos.
Ponto forte: elimina perdedores antigos de forma seletiva.
Ponto fraco: em tendência forte pode acumular posições e margem.

3. HedgeCycle-Pending:
Variação com ordens pendentes em níveis. Usa same limit, opposite stop, hedge especial menor e buffer de pendings.
Recovery busca a pior posição perdedora e usa lucro combinado dos melhores hedges para eliminá-la.
Ponto forte: usa spikes para montar inventário de hedge.
Ponto fraco: gaps, slippage e tendência sem retorno podem desorganizar/pressionar o sistema.

4. HedgeCycle-Worm:
Grid direcional com hedge alternado Large/Small.
Mantém net próximo de um alvo, como NetPositiveThreshold.
Ajusta somente a próxima pending Large quando o net excede o limite.
Ponto forte: controle dinâmico do net sem reforçar todas as pendings.
Ponto fraco: precisa de controle forte de estado, sequência rígida, spread e cooldown.

5. P4/P5 Travamento Residual:
Estratégias de passagem de bastão.
Exemplo:
Começa com BUY/SELL 0.02.
Preço sobe, fecha a BUY com lucro e sobra SELL.
Abre nova BUY maior e cria travamento BUY/SELL maior.
Se o preço volta, usa o lado do travamento para eliminar a direcional e a residual antiga, sobrando uma nova residual.
A lógica continua invertendo.
Ponto forte: passagem de risco para uma posição residual mais nova.
Ponto fraco: depende de boa execução e de retorno suficiente do preço.

6. HedgeAcima:
Lógica onde, após eliminar a ordem antiga, o EA não repete simplesmente o ciclo original; ele usa a posição que sobrou como novo centro.
Exemplo:
SELL 0.02 em 3000.
Preço sobe para 3200, abre BUY 0.01 + BUY/SELL 0.02.
BUY 0.01 + BUY 0.02 eliminam SELL 0.02 antiga de 3000.
Sobra SELL 0.02 em 3200.
A nova estrutura é montada em função dessa SELL residual.
Ponto forte: “passagem de bastão”.
Ponto fraco: precisa controlar quando montar nova estrutura para não aumentar risco sem necessidade.

7. AntiMartingale Cycle Control:
Arquitetura limpa para controle de lote por ciclo.
Usa uma variável central como BaseLotThisCycle.
Pode resetar para InitialLot após recovery ou reduzir lote até MinLot.
Ponto forte: controle limpo de estado e lote.
Ponto fraco: Reset=true pode repetir risco indefinidamente; Reset=false pode parar antes de recuperar tudo.

Ideia principal da estratégia híbrida:
A estratégia perfeita provavelmente não é uma lógica única. Deve ser uma fusão de:

- P1-Net para controle matemático de net;
- HedgeCycle/Worm para hedge e recovery seletivo;
- P4/P5/HedgeAcima para passagem de bastão residual;
- AntiMartingale para controle de lote/ciclo;
- Protection Engine para limites de sobrevivência.

Arquitetura desejada do Hedge Evolution Lab:

hedgeAgent/
├── hedge_lab/
│   ├── simulator/
│   ├── strategies/
│   ├── scenarios/
│   ├── evolution/
│   ├── metrics/
│   └── agents/
├── configs/
├── datasets/
├── reports/
├── docs/
└── tests/

Estado atual do repo:
O repo hedgeAgent foi limpo e reiniciado.
Foi feito backup local do estado anterior.
Foi commitado e enviado para o GitHub em main.
A fundação inicial já foi criada com:

- README.md
- .gitignore
- docs/ARCHITECTURE.md
- docs/STRATEGY_GENOME.md
- hedge_lab/simulator/core.py
- hedge_lab/**/__init__.py
- .gitkeep nas pastas vazias

Regras globais obrigatórias do projeto:

1. Sempre pensar multiativos.
Nada hardcoded exclusivamente para GOLD/XAUUSD.

2. Sempre pensar multitimes/multitimeframes.
Nada preso a M5, M15, H1, H4 ou D1.

3. Windows e Linux desde o início.
Usar pathlib em Python.
Evitar comandos ou paths que funcionem só em Linux.
Quando necessário, fornecer comando PowerShell e Bash separadamente.

4. Nunca inventar estado do repositório.
Se não souber o arquivo real, pedir tree, dir, log, arquivo ou conteúdo.
Não supor que existe arquivo que não foi confirmado.

5. Não quebrar o que já funciona.
Toda alteração deve ser incremental, testável e com validação.

6. Evitar criar muitos arquivos.
Preferir poucos arquivos oficiais, bem organizados e fáceis de manter.
Não criar file sprawl.

7. Cada arquivo novo ou alterado precisa ter um resumo inicial no topo.
Esse resumo deve explicar:
- para que serve;
- inputs esperados;
- outputs gerados;
- integrações;
- observações de manutenção;
- cuidado com multiativo/multitimeframe;
- compatibilidade Windows/Linux.

Exemplo de cabeçalho Python desejado:

"""
File: hedge_lab/simulator/core.py

Purpose:
    Core simulation primitives for the Hedge Evolution Lab.

Inputs:
    - Strategy decisions
    - Market prices/events
    - SimulationConfig parameters

Outputs:
    - AccountState
    - PortfolioState
    - SimulationResult

Integrations:
    - Used by strategy modules
    - Used by scenario runners
    - Later used by evolution and agent layers

Notes:
    - Must remain multi-asset and multi-timeframe ready.
    - Must work on Windows and Linux.
    - Avoid hardcoded symbol/timeframe assumptions.
"""

Próximo passo recomendado:
Criar o primeiro simulador rodável, com o mínimo de arquivos possível, para testar P1-Net v0.

Sugestão de próximos arquivos, se realmente necessário:

- hedge_lab/scenarios/basic_paths.py
- hedge_lab/strategies/p1_net.py
- hedge_lab/simulator/run_simulation.py

Mas antes de criar, avaliar se dá para consolidar e evitar muitos arquivos.

Primeiro cenário de teste:
Preço:
3000 → 3300 → 3000 → 3300 → 3000

Objetivo:
Validar que o motor calcula corretamente:

- BUY;
- SELL;
- NET;
- GROSS;
- PNL flutuante;
- PNL realizado;
- drawdown;
- max positions;
- max gross lots;
- survived/failure_reason.

Métricas principais que toda estratégia deve registrar:

- final_balance;
- final_equity;
- realized_profit;
- floating_profit;
- max_drawdown;
- net_lots;
- gross_lots;
- max_gross_lots;
- max_positions;
- survival status;
- failure reason;
- recovery power;
- risk debt;
- cycle age;
- number of levels;
- exposure by asset/timeframe no futuro.

Filosofia de avaliação:
Não vence a estratégia que mais lucra.
Vence a estratégia que:

- lucra;
- sobrevive;
- não explode volume bruto;
- não depende de um único regime;
- consegue reduzir risco quando o mercado muda;
- passa em cenários de range, spike, tendência, gap, spread alto e slippage.

Ordem correta do projeto:

1. Simulador.
2. Métricas.
3. Estratégias base.
4. Cenários sintéticos.
5. Fitness/risk score.
6. Evolução.
7. Agentes.
8. Exportação futura para MQL5/EA.

Importante:
Não começar direto com muitos agentes ou MQL5.
Primeiro precisamos provar a matemática no simulador Python.
Depois evoluímos para agentes e, só no final, exportação/adaptação para EA.