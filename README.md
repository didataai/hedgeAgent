# hedgeAgent — Hedge Evolution Lab

## Objetivo

O `hedgeAgent` é um laboratório evolutivo para descobrir, simular, comparar, combinar e evoluir estratégias de hedge.

O foco não é criar apenas mais um Expert Advisor, mas construir uma máquina de descoberta capaz de:

- representar estratégias como genomas;
- simular cenários extremos de mercado;
- medir risco real, não apenas lucro;
- evoluir combinações de hedge;
- identificar falhas estruturais;
- comparar famílias de estratégias;
- registrar aprendizado dinâmico por estratégia;
- promover apenas estratégias robustas.

## Tese central

As estratégias de hedge não eliminam risco.

Elas transformam risco direcional em:

- tempo;
- margem;
- volume bruto;
- distância de recuperação;
- custo operacional;
- risco de tendência;
- risco de execução;
- risco de travamento estrutural.

O objetivo do projeto é encontrar estruturas que consigam:

- lucrar em ranges;
- sobreviver a spikes;
- reduzir dano em tendências fortes;
- controlar volume bruto;
- controlar `risk_debt`;
- evitar crescimento explosivo de posições;
- eliminar ordens antigas com lucro real;
- passar o risco para estruturas mais novas de forma controlada;
- manter robustez em múltiplos regimes.

## Estado atual do laboratório

O projeto já possui os primeiros blocos oficiais do Hedge Evolution Lab:

```text
P1_NET_V0
P1_MULTIPLIER_V0
Monte Carlo multi-strategy
Genetic Search multi-strategy
Strategy Cards
Strategy Learning Memory
Strategy Memory Comparison
```

Estratégias atuais:

| Strategy ID | Família | Descrição | Status |
|---|---|---|---|
| `P1_NET_V0` | `P1_NET` | Controle de NET absoluto fixo, alternando entre `+net_abs_lots` e `-net_abs_lots`. | Baseline atual |
| `P1_MULTIPLIER_V0` | `P1_MULTIPLIER` | Expansão alternada por multiplicador, onde o lado oposto busca `lado_referencia × multiplier`. | Experimental |

Comparações iniciais indicaram `P1_NET_V0` como baseline atual por `decision_score_v0`, enquanto `P1_MULTIPLIER_V0` mostrou menor gross, menor número de posições e menor variação entre regimes em alguns testes sintéticos.

## Arquitetura inicial

```text
hedgeAgent/
├── hedge_lab/
│   ├── analysis/
│   │   ├── build_strategy_learning_summary.py
│   │   └── compare_strategy_memories.py
│   ├── simulator/
│   │   ├── core.py
│   │   ├── run_simulation.py
│   │   └── run_monte_carlo.py
│   ├── strategies/
│   │   ├── p1_net.py
│   │   └── p1_multiplier.py
│   ├── scenarios/
│   ├── evolution/
│   │   └── run_genetic_search.py
│   ├── metrics/
│   └── agents/
├── configs/
├── datasets/
│   ├── strategies/
│   └── strategy_comparisons/
├── reports/
├── docs/
│   └── strategies/
└── tests/
```

## Contrato de datasets por estratégia

Todo experimento deve salvar resultados usando o contrato:

```text
datasets/strategies/<STRATEGY_ID>/<ASSET>/<TIMEFRAME>/<EXPERIMENT_TYPE>/<RUN_ID>/
```

Exemplos:

```text
datasets/strategies/P1_NET_V0/SYNTH/SIM/monte_carlo/protection_on/20260528_211003/
datasets/strategies/P1_MULTIPLIER_V0/SYNTH/SIM/genetic_search/20260528_215521/
```

Memória dinâmica por estratégia:

```text
datasets/strategies/<STRATEGY_ID>/_memory/strategy_learning_summary.json
datasets/strategies/<STRATEGY_ID>/_memory/strategy_learning_summary.md
```

Comparações entre estratégias:

```text
datasets/strategy_comparisons/<STRATEGY_A>__vs__<STRATEGY_B>/comparison.json
datasets/strategy_comparisons/<STRATEGY_A>__vs__<STRATEGY_B>/comparison.md
```

Os diretórios de datasets são gerados em runtime e normalmente ficam fora do Git.

## Strategy Cards

Toda estratégia oficial deve ter um documento conceitual em:

```text
docs/strategies/<STRATEGY_ID>.md
```

Esse arquivo descreve:

- identidade da estratégia;
- objetivo;
- lógica operacional;
- parâmetros;
- estado interno;
- regras de entrada;
- regras de rebalanceamento;
- regras de proteção;
- riscos conhecidos;
- contrato de dataset;
- como agentes/RAG devem interpretar a estratégia;
- perguntas abertas para evolução.

A Strategy Card é a verdade conceitual da estratégia.

A pasta `_memory` é a verdade empírica dinâmica, gerada pelos testes.

## Princípio de evolução

```text
Gerar estratégia
→ Simular
→ Medir risco
→ Identificar falha
→ Mutar
→ Cruzar
→ Comparar
→ Registrar memória
→ Repetir
→ Promover somente se sobreviver
```

## Processo oficial para adicionar uma nova estratégia

Este é o fluxo recomendado para adicionar qualquer nova estratégia ao Hedge Evolution Lab.

### 1. Definir identidade da estratégia

Escolha um `strategy_id` único, em caixa alta, com versão explícita:

```text
P1_NET_V0
P1_MULTIPLIER_V0
P1_HYBRID_NET_MULTIPLIER_V0
```

Contrato recomendado:

```text
<FAMILIA>_<VARIANTE>_V<N>
```

Boas práticas:

- não reutilizar `strategy_id` para lógica diferente;
- aumentar versão quando a lógica estrutural mudar;
- manter nomes legíveis para humano, orquestrador e LLM;
- evitar nomes acoplados a apenas um ativo ou timeframe.

### 2. Criar a Strategy Card

Criar:

```text
docs/strategies/<STRATEGY_ID>.md
```

A Strategy Card deve explicar a estratégia antes do código ser considerado completo.

Template mínimo:

```markdown
# <STRATEGY_ID> — Strategy Card

## 1. Identity

## 2. Purpose

## 3. Operational Logic

## 4. Parameters

## 5. State Variables

## 6. Entry Rules

## 7. Rebalance Rules

## 8. Protection Logic

## 9. Known Strengths

## 10. Known Weaknesses

## 11. Dataset Contract

## 12. Dynamic Learning Memory

## 13. Agent and RAG Usage

## 14. Open Questions
```

### 3. Criar o arquivo Python da estratégia

Criar em:

```text
hedge_lab/strategies/<strategy_name>.py
```

Exemplos:

```text
hedge_lab/strategies/p1_net.py
hedge_lab/strategies/p1_multiplier.py
```

Todo arquivo novo ou alterado deve começar com um cabeçalho explicando:

- `File`;
- `Purpose`;
- `Inputs`;
- `Outputs`;
- `Integrations`;
- `Notes`.

A estratégia deve seguir o padrão:

```text
Config dataclass
State dataclass
Strategy class
on_price(engine, price)
```

Exemplo conceitual:

```python
@dataclass(frozen=True)
class MyStrategyConfig:
    initial_side: Side
    start_lot: float
    range_points: float

@dataclass
class MyStrategyState:
    started: bool = False
    last_level: float | None = None
    rebalance_count: int = 0

class MyStrategy:
    def __init__(self, config: MyStrategyConfig):
        self.config = config
        self.state = MyStrategyState()

    def on_price(self, engine: ExecutionEngine, price: float) -> None:
        ...
```

### 4. Integrar no Monte Carlo

Atualizar:

```text
hedge_lab/simulator/run_monte_carlo.py
```

A nova estratégia deve ser registrada no `build_strategy(config)`.

Exemplo:

```python
if strategy_id == "P1_MULTIPLIER_V0":
    return P1MultiplierStrategy(
        P1MultiplierConfig(...)
    )
```

O CLI deve receber apenas parâmetros genéricos ou explicitamente documentados.

Exemplo:

```powershell
python -m hedge_lab.simulator.run_monte_carlo --strategy-id <STRATEGY_ID> --mode all --runs 20 --steps 60 --compare-protection --save-json
```

Se a estratégia precisar de um parâmetro novo, adicionar no parser e garantir que estratégias antigas continuem funcionando.

### 5. Integrar no Genetic Search

Atualizar:

```text
hedge_lab/evolution/run_genetic_search.py
```

A genética deve conseguir avaliar a nova estratégia usando `--strategy-id`.

Quando necessário, adicionar genes específicos da estratégia.

Exemplo:

```text
multiplier
range_points
enable_protection
max_gross_to_net_ratio
max_strategy_gross_lots
max_strategy_positions
```

Importante:

- genes específicos devem ser ignorados por estratégias que não os usam;
- estratégia antiga não pode quebrar;
- logs devem mostrar os genes relevantes no ranking final;
- o summary JSON deve manter `strategy_id`, `strategy_family`, `strategy_version`, `asset`, `timeframe` e `experiment_type`.

### 6. Rodar Monte Carlo inicial

Comando base:

```powershell
python -m hedge_lab.simulator.run_monte_carlo --strategy-id <STRATEGY_ID> --mode all --runs 20 --steps 60 --compare-protection --save-json
```

Para `P1_MULTIPLIER_V0`, exemplo:

```powershell
python -m hedge_lab.simulator.run_monte_carlo --strategy-id P1_MULTIPLIER_V0 --mode all --runs 20 --steps 60 --compare-protection --save-json --multiplier 2.0
```

Validar que foram criados:

```text
datasets/strategies/<STRATEGY_ID>/SYNTH/SIM/monte_carlo/protection_on/<RUN_ID>/summary.json
datasets/strategies/<STRATEGY_ID>/SYNTH/SIM/monte_carlo/protection_off/<RUN_ID>/summary.json
```

### 7. Rodar Genetic Search inicial

Comando base:

```powershell
python -m hedge_lab.evolution.run_genetic_search --strategy-id <STRATEGY_ID> --generations 2 --population 8 --runs 50 --steps 80 --save-json
```

Validar que foram criados:

```text
datasets/strategies/<STRATEGY_ID>/SYNTH/SIM/genetic_search/<RUN_ID>/summary.json
datasets/strategies/<STRATEGY_ID>/SYNTH/SIM/genetic_search/<RUN_ID>/genetic_evaluations.jsonl
```

### 8. Gerar memória dinâmica da estratégia

Comando:

```powershell
python -m hedge_lab.analysis.build_strategy_learning_summary --strategy-id <STRATEGY_ID>
```

Validar:

```text
datasets/strategies/<STRATEGY_ID>/_memory/strategy_learning_summary.json
datasets/strategies/<STRATEGY_ID>/_memory/strategy_learning_summary.md
```

A memória deve conter:

- melhor genome conhecido;
- score;
- regime mais forte;
- regime mais fraco;
- risco de gross expansion;
- risco de `risk_debt`;
- atividade média;
- próximos experimentos recomendados.

### 9. Comparar contra baseline

Comando:

```powershell
python -m hedge_lab.analysis.compare_strategy_memories --strategy-ids P1_NET_V0 <STRATEGY_ID>
```

Validar:

```text
datasets/strategy_comparisons/P1_NET_V0__vs__<STRATEGY_ID>/comparison.json
datasets/strategy_comparisons/P1_NET_V0__vs__<STRATEGY_ID>/comparison.md
```

O comparador avalia:

- `decision_score_v0`;
- score bruto;
- survival;
- drawdown;
- gross;
- número de posições;
- `risk_debt`;
- atividade;
- variação entre regimes;
- melhor e pior regime.

### 10. Validar antes de commit

Rodar pelo menos:

```powershell
python -m hedge_lab.simulator.run_monte_carlo --strategy-id P1_NET_V0 --mode all --runs 5 --steps 30 --save-json
python -m hedge_lab.simulator.run_monte_carlo --strategy-id <STRATEGY_ID> --mode all --runs 5 --steps 30 --save-json
python -m hedge_lab.evolution.run_genetic_search --strategy-id <STRATEGY_ID> --generations 1 --population 4 --runs 10 --steps 30 --save-json
```

Conferir:

```powershell
git status --short
```

Não commitar:

```text
datasets/strategies/**
datasets/strategy_comparisons/**
__pycache__/
*.pyc
*.bak
```

Commitar apenas código, docs e contratos.

### 11. Commit recomendado

Exemplo:

```powershell
git add docs/strategies/<STRATEGY_ID>.md
git add hedge_lab/strategies/<strategy_name>.py
git add hedge_lab/simulator/run_monte_carlo.py
git add hedge_lab/evolution/run_genetic_search.py

git commit -m "feat: add <STRATEGY_ID> strategy"
git push
```

Se a estratégia também criou ferramenta de análise ou comparação:

```powershell
git add hedge_lab/analysis/<tool>.py
git commit -m "feat: add strategy analysis tooling"
git push
```

## Comandos úteis atuais

### Rodar Monte Carlo para P1-Net

```powershell
python -m hedge_lab.simulator.run_monte_carlo --strategy-id P1_NET_V0 --mode all --runs 20 --steps 60 --compare-protection --save-json
```

### Rodar Monte Carlo para P1-Multiplier

```powershell
python -m hedge_lab.simulator.run_monte_carlo --strategy-id P1_MULTIPLIER_V0 --mode all --runs 20 --steps 60 --compare-protection --save-json --multiplier 2.0
```

### Rodar Genetic Search

```powershell
python -m hedge_lab.evolution.run_genetic_search --strategy-id P1_NET_V0 --generations 2 --population 8 --runs 50 --steps 80 --save-json
python -m hedge_lab.evolution.run_genetic_search --strategy-id P1_MULTIPLIER_V0 --generations 2 --population 8 --runs 50 --steps 80 --save-json
```

### Gerar memória dinâmica

```powershell
python -m hedge_lab.analysis.build_strategy_learning_summary --strategy-id P1_NET_V0
python -m hedge_lab.analysis.build_strategy_learning_summary --strategy-id P1_MULTIPLIER_V0
```

### Comparar estratégias

```powershell
python -m hedge_lab.analysis.compare_strategy_memories --strategy-ids P1_NET_V0 P1_MULTIPLIER_V0
```

## Regras globais do projeto

- Pensar sempre em multiativos.
- Pensar sempre em multitimes/timeframes.
- Manter compatibilidade Windows e Linux.
- Não hardcodar GOLD, H1, Windows ou Linux.
- Não inventar arquivos, contratos ou estado do repo.
- Não quebrar o que já funciona.
- Evitar criar muitos arquivos sem necessidade.
- Preferir contratos claros, legíveis para humano, orquestrador e LLM.
- Todo arquivo novo ou alterado deve ter cabeçalho explicando propósito, inputs, outputs, integrações e observações.
- Datasets gerados devem ser separados por `strategy_id`, `asset`, `timeframe`, `experiment_type` e `run_id`.
- Estratégia nova só deve ser considerada candidata depois de gerar memória dinâmica e comparação contra baseline.

## Regra de ouro

Não vence a estratégia que mais lucra.

Vence a estratégia que:

```text
lucra,
sobrevive,
não explode volume,
não acumula risk debt sem controle,
não depende de um único tipo de mercado,
e consegue reduzir risco quando o mercado muda.
```
