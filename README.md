# hedgeAgent — Hedge Evolution Lab

## Objetivo

O `hedgeAgent` é um laboratório evolutivo para descobrir, simular, combinar e evoluir estratégias de hedge.

O foco não é criar apenas mais um Expert Advisor, mas construir uma máquina de descoberta capaz de:

- representar estratégias como genomas;
- simular cenários extremos de mercado;
- medir risco real, não apenas lucro;
- evoluir combinações de hedge;
- identificar falhas estruturais;
- promover apenas estratégias robustas.

## Tese central

As estratégias de hedge não eliminam risco.

Elas transformam risco direcional em:

- tempo;
- margem;
- volume bruto;
- distância de recuperação;
- custo operacional;
- risco de tendência.

O objetivo do projeto é encontrar estruturas que consigam:

- lucrar em ranges;
- sobreviver a spikes;
- reduzir dano em tendências fortes;
- controlar volume bruto;
- eliminar ordens antigas com lucro real;
- passar o risco para estruturas mais novas de forma controlada.

## Famílias iniciais

1. P1-Net — controle de NET fixo.
2. HedgeCycle Recovery — eliminação seletiva de perdedores.
3. Worm Large/Small — controle dinâmico de net por hedges alternados.
4. P4/P5 Travamento Residual — passagem de bastão da ordem antiga para residual nova.
5. AntiMartingale Cycle Control — redução ou reset de lote por ciclo.

## Arquitetura inicial

```text
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
```

## Princípio de evolução

```text
Gerar estratégia
→ Simular
→ Medir risco
→ Identificar falha
→ Mutar
→ Cruzar
→ Repetir
→ Promover somente se sobreviver
```

## Regra de ouro

Não vence a estratégia que mais lucra.

Vence a estratégia que:

```text
lucra,
sobrevive,
não explode volume,
não depende de um único tipo de mercado,
e consegue reduzir risco quando o mercado muda.
```
