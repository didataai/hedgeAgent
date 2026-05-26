Você é o Strategy Understanding Agent do projeto hedgeAgent.

Sua tarefa é interpretar a estratégia a partir de arquivos humanos e análises MQL5.

Regras obrigatórias:
- Não invente fatos.
- Use somente o contexto fornecido.
- Separe o que está confirmado pelo prompt humano do que está confirmado pelo código.
- O que for interpretação deve entrar como hipótese.
- Marque pontos desconhecidos.
- Preencha obrigatoriamente `evolution_notes` com a evolução BASE -> V1 -> V2 -> V3 -> V4 quando houver dados.
- Explique, no markdown, por que os EAs parecem ter sido criados e qual problema cada versão tentou resolver.
- Responda APENAS um objeto JSON válido. Não escreva introdução, conclusão fora do JSON, nem markdown fora do JSON.
- O JSON precisa ter EXATAMENTE o schema abaixo no topo. Não responda objetos pequenos como {"confidence": ..., "point": ...}.
- Se não souber algum campo, use lista vazia, mas mantenha todas as chaves obrigatórias.

Schema obrigatório:
{
  "strategy_brain_markdown": "texto markdown completo em português",
  "confirmed_from_prompt": ["..."],
  "confirmed_from_code": ["..."],
  "inferred_hypotheses": ["..."],
  "known_limitations": ["..."],
  "unknown_points": ["..."],
  "evolution_notes": ["..."],
  "subfamilies": {"nome_da_sublinha": ["P0_BASE"]},
  "next_research_steps": ["..."]
}

Contexto:
# Contexto para Strategy Brain — P0

## Regra crítica
Não invente. Separe fatos confirmados de hipóteses. Use somente o contexto abaixo.

## Intenção determinística
{
  "family_id": "P0",
  "generated_at_utc": "2026-05-26T21:09:40.309043+00:00",
  "source_files": [
    {
      "source_file": "PromptEA-P0.txt",
      "file_type": "text_note",
      "status": "ok",
      "char_count": 2265,
      "truncated": false
    }
  ],
  "detected_concepts": [
    "initial_market_hedge",
    "four_initial_orders",
    "small_large_lots",
    "range_trigger",
    "winner_eliminates_loser",
    "directional_order",
    "return_stop_or_recovery",
    "lot_increment",
    "pending_vs_market_question"
  ],
  "numeric_cues": {
    "lot_values": [
      "0.01",
      "0.02",
      "0.03",
      "0.04",
      "0.05",
      "0.06"
    ],
    "price_or_point_values": [
      "3000",
      "3500",
      "500"
    ],
    "usd_values": [
      "-8USD",
      "10usd"
    ]
  },
  "deterministic_summary": [
    "Família P0: intenção humana extraída de arquivos de notas/contexto.",
    "Esta leitura é determinística e deve ser validada por resolução por fontes.",
    "A estratégia parece nascer de um hedge/travamento inicial a mercado.",
    "Há pistas de dois blocos/lotes principais, especialmente 0.03 e 0.04.",
    "Há intenção de usar a ordem maior lucrativa para eliminar ordem menor perdedora.",
    "Após eliminação, há intenção de abrir uma ordem direcional.",
    "O retorno do preço contra a direcional é tratado como problema central de stop/recovery.",
    "Há pista de incremento de lote, que precisa ser avaliado por DD, margem e risco."
  ],
  "open_questions": [
    "A intenção menciona dúvida entre executar a mercado ou usar limits; isso precisa virar regra formal.",
    "Ainda é necessário transformar a intenção em uma especificação de estados, transições e eventos testáveis.",
    "Backtest ainda não foi executado; a robustez em tendência, range e zig-zag é desconhecida."
  ]
}

## Fontes humanas
### PromptEA-P0.txt

hoje vamos criar um EA de hedge para metatrader5 mql5 .



Basicamente ele vai começar lançando hedge de travamenteo a mercado . 

valores hedge 1 no input (0.03)

valroes hedge 2 no input. (0.04)



Ele inicia compra de venda do lot (0.03)

Ele inicia compra de venda do lot (0.04)

ou seja, 4 ordens. 



Digamos que iniciou no preço 3000. 



em um range de pts (Input) tb - digamos 500 pts. 



3500 - ele vai pegar a ordem de 0.04 para eliminar a de 0.03 - como preço subiu ele vai pegar a compra de 0.04 para eliminar a venda de 0.03 (com lucro de 20 pts (input) OU - 10usd (input ) posso escolher se vai ser em pts ou quando houver 10usd de lucro 0.04 eliminando 0.03. - por exemplo. 



Logo após eliminar , ele coloca ordem direcional (input tb) - nesse caso ordem com lot de 0.02 ... 

com misso, vamos ter 

3000 - sell 0.04 - buy 0.03

3500 - buy 0.02 

total 0.05 comprado x 0.04 vendido. 



Agora, se o preço voltar, precisamos definir a estratégia de stop .

Preço voltando eu preciso fazer com que a ordem de 0.03 elimine a ordem de compra de 0.02 no stop em 0 praticamnte - ou seja, lucro da ordem de 0.03 + stop da ordem de 0.02 seja 0 (ou valor a ser definido nos inputs) - exemplo  (-8USD) .. quando a dif entre as ordens chegar a -8 - ele usa a ordem de 0.03 para fechar a ordem de 0.02. 



mesmo tempo a eliminação - ele coloca ordem a mercado de um compra de 0.04 (isolando a ordem de venda de 3000) 

poderiamos fazer buy limit ? porem, como vai saber exato a eliminação o ponto, entre as ordens de 0.03 x 0.02 - por isso, pensei a mercado , mas se houvesse uma forma d ser limit - seria melhor na exec. 



entao, ele colocar a ordem de compra de 0.04 - mais um hedge aumentando um lot (Input) - 0.01 por exemplo - entao ele compraria e venderia 0.05 . 

de novo, buy limit de 0.05 junto com limit de 0.04 seria possivel ? senao, vamos a mercado mesmo . 

como podemos separar essa ordem de hedge da ordem inicial que vai ter outro lot ?

entao , apos a eliminação, ficaria . 



venda de 0.04 3000 - compra e vende de 0.05 e compra de de 0.04 ...



e a logica segue, quando for possivel a ordem de 0.05 eliminar a ordem de 0.04 - coloca o hedge direcional - no caso , seria 0.02 , ficando 0.05 - 0.04 - 0.02 (0.05 x 0.06 (somados) ). 


## Linha de raciocínio evolutiva detectada
- P0_BASE: versão inicial analisada. Descrição detectada: "Hedge Progressivo - Correção lotes globais não carregados + sequência garantida".
- P0_BASE -> P0_V1; descrição detectada: "Hedge P00 V1: Start BUY+SELL; Fecha lucro no range; Abre DIR a mercado; Coloca hedges pendings no preço base com offset (LIMIT antes STOP); Resolve quando lucro base+hedge_same cobre perda DIR; Fecha DIR+opp+BASE, sobra hedge_same como novo base."; inputs adicionados: ['AutoStart', 'BotaoCloseAll', 'BotaoH', 'BotaoW', 'CommentText', 'CooldownMs', 'CorBuy', 'CorNet', 'CorProfit', 'CorSell', '...(+15)']; inputs removidos: ['BotaoAltura', 'BotaoCloseReset', 'BotaoLargura', 'CorTextoBotao', 'DirectionalLot', 'ForceInitialHedge', 'HedgeLargeLot', 'HedgeSmallLot', 'IgnoreSpreadOnReset', 'LotIncrease', '...(+6)']; defaults alterados: ['BotaoPosX', 'BotaoPosY']; funções adicionadas: ['CloseAllByMagic', 'Cmt', 'CreateUI', 'CycleTag', 'FindTicketByExactComment', 'IsMyOrderByTicket', 'IsMyPosByTicket', 'IsTradeAllowedNow', 'MyPositionsCount', 'NormalizeLot', '...(+9)']; funções removidas: ['CloseAllOurPositionsAndReset', 'ClosePosition', 'CountOurPositions', 'GetPointsProfit', 'GetProfit', 'IsTriggered', 'OpenPosition', 'PositionExists']; mudanças de pistas: ['has_spread_filter: True -> False', 'has_initial_hedge_cue: True -> False', 'has_lot_increase_cue: True -> False', 'has_pending_order_cue: False -> True', 'has_recovery_cue: False -> True', 'has_reset_state_cue: True -> False', 'has_timer_event: False -> True'].
- P0_V1 -> P0_V2; descrição detectada: "Hedge Progressivo - Extra lot quando range isolating > 400 pts + directional dinâmico (diferença)"; inputs adicionados: ['BotaoAltura', 'BotaoCloseReset', 'BotaoLargura', 'CorTextoBotao', 'DirectionalLot', 'ExtraLotWhenFar', 'FarRangePts', 'ForceInitialHedge', 'HedgeLargeLot', 'HedgeSmallLot', '...(+8)']; inputs removidos: ['AutoStart', 'BotaoCloseAll', 'BotaoH', 'BotaoW', 'CommentText', 'CooldownMs', 'CorBuy', 'CorNet', 'CorProfit', 'CorSell', '...(+15)']; defaults alterados: ['BotaoPosX', 'BotaoPosY']; funções adicionadas: ['CloseAllOurPositionsAndReset', 'ClosePosition', 'CountOurPositions', 'GetPointsProfit', 'GetProfit', 'IsTriggered', 'OpenPosition', 'PositionExists']; funções removidas: ['CloseAllByMagic', 'Cmt', 'CreateUI', 'CycleTag', 'FindTicketByExactComment', 'IsMyOrderByTicket', 'IsMyPosByTicket', 'IsTradeAllowedNow', 'MyPositionsCount', 'NormalizeLot', '...(+9)']; mudanças de pistas: ['has_spread_filter: False -> True', 'has_initial_hedge_cue: False -> True', 'has_lot_increase_cue: False -> True', 'has_pending_order_cue: True -> False', 'has_recovery_cue: True -> False', 'has_reset_state_cue: False -> True', 'has_timer_event: True -> False'].
- P0_V2 -> P0_V3; descrição detectada: "Hedge Progressivo - Correção tracking/sequência após aumento de lot"; inputs adicionados: ['CorBuy', 'CorLucro', 'CorNet', 'CorSell', 'EA_InstanceSuffix', 'Espacamento', 'ExtraLotIncreaseOnRange', 'PosX', 'PosY', 'RangeThresholdPts', '...(+1)']; inputs removidos: ['ExtraLotWhenFar', 'FarRangePts']; defaults alterados: ['BotaoAltura', 'BotaoLargura', 'BotaoPosX', 'BotaoPosY']; funções adicionadas: ['AtualizarResumoNoGrafico'].
- P0_V3 -> P0_V4; descrição detectada: "Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease"; inputs removidos: ['DirectionalLot'].

## Sublinha(s) detectadas por pistas
{
  "progressive_hedge_or_lot_increase": [
    "P0_BASE",
    "P0_V2",
    "P0_V3",
    "P0_V4"
  ],
  "pending_recovery_or_initial_lock": [
    "P0_V1"
  ],
  "spread_magic_operational_control": [
    "P0_BASE",
    "P0_V1",
    "P0_V2",
    "P0_V3",
    "P0_V4"
  ]
}

## Versões MQL5 analisadas
{
  "version_id": "P0_BASE",
  "source_file": "hedge_P0-NaoAmentaLot.mq5",
  "properties": [
    {
      "line": 5,
      "name": "copyright",
      "value": "\"xAI\""
    },
    {
      "line": 6,
      "name": "link",
      "value": "\"\""
    },
    {
      "line": 7,
      "name": "version",
      "value": "\"1.10\""
    },
    {
      "line": 8,
      "name": "strict",
      "value": ""
    },
    {
      "line": 9,
      "name": "description",
      "value": "\"Hedge Progressivo - Correção lotes globais não carregados + sequência garantida\""
    }
  ],
  "inputs": [
    {
      "line": 16,
      "raw": "input double HedgeSmallLot      = 0.03;       // Lote inicial small hedge",
      "type": "double",
      "name": "HedgeSmallLot",
      "default": "0.03",
      "comment": "Lote inicial small hedge"
    },
    {
      "line": 17,
      "raw": "input double HedgeLargeLot      = 0.04;       // Lote inicial large hedge",
      "type": "double",
      "name": "HedgeLargeLot",
      "default": "0.04",
      "comment": "Lote inicial large hedge"
    },
    {
      "line": 18,
      "raw": "input double DirectionalLot     = 0.02;       // Lote direcional fixo",
      "type": "double",
      "name": "DirectionalLot",
      "default": "0.02",
      "comment": "Lote direcional fixo"
    },
    {
      "line": 19,
      "raw": "input double LotIncrease        = 0.01;       // Incremento por nível",
      "type": "double",
      "name": "LotIncrease",
      "default": "0.01",
      "comment": "Incremento por nível"
    },
    {
      "line": 20,
      "raw": "input double StopThresholdUSD   = -8.0;       // Limite USD para stop (net small + directional)",
      "type": "double",
      "name": "StopThresholdUSD",
      "default": "-8.0",
      "comment": "Limite USD para stop (net small + directional)"
    },
    {
      "line": 21,
      "raw": "input string TriggerMode        = \"usd\";      // \"pts\" ou \"usd\"",
      "type": "string",
      "name": "TriggerMode",
      "default": "\"usd\"",
      "comment": "\"pts\" ou \"usd\""
    },
    {
      "line": 22,
      "raw": "input double TriggerValue       = 10.0;       // Valor do trigger (pts ou net USD)",
      "type": "double",
      "name": "TriggerValue",
      "default": "10.0",
      "comment": "Valor do trigger (pts ou net USD)"
    },
    {
      "line": 23,
      "raw": "input int    MagicBase          = 12345;      // Magic base",
      "type": "int",
      "name": "MagicBase",
      "default": "12345",
      "comment": "Magic base"
    },
    {
      "line": 24,
      "raw": "input double MaxSpread          = 50.0;       // Spread max em points (0 = sem filtro)",
      "type": "double",
      "name": "MaxSpread",
      "default": "50.0",
      "comment": "Spread max em points (0 = sem filtro)"
    },
    {
      "line": 25,
      "raw": "input bool   IgnoreSpreadOnReset= true;       // Ignora spread após reset ou botão",
      "type": "bool",
      "name": "IgnoreSpreadOnReset",
      "default": "true",
      "comment": "Ignora spread após reset ou botão"
    },
    {
      "line": 26,
      "raw": "input bool   ForceInitialHedge  = false;      // Força abertura mesmo com posições",
      "type": "bool",
      "name": "ForceInitialHedge",
      "default": "false",
      "comment": "Força abertura mesmo com posições"
    },
    {
      "line": 27,
      "raw": "input bool   ResetStateOnStart  = false;      // RESET ao iniciar (use 1x)",
      "type": "bool",
      "name": "ResetStateOnStart",
      "default": "false",
      "comment": "RESET ao iniciar (use 1x)"
    },
    {
      "line": 30,
      "raw": "input string BotaoCloseReset    = \"Close_All_Reset\";",
      "type": "string",
      "name": "BotaoCloseReset",
      "default": "\"Close_All_Reset\"",
      "comment": null
    },
    {
      "line": 31,
      "raw": "input int    BotaoPosX          = 30;",
      "type": "int",
      "name": "BotaoPosX",
      "default": "30",
      "comment": null
    },
    {
      "line": 32,
      "raw": "input int    BotaoPosY          = 30;",
      "type": "int",
      "name": "BotaoPosY",
      "default": "30",
      "comment": null
    },
    {
      "line": 33,
      "raw": "input int    BotaoLargura       = 160;",
      "type": "int",
      "name": "BotaoLargura",
      "default": "160",
      "comment": null
    },
    {
      "line": 34,
      "raw": "input int    BotaoAltura        = 40;",
      "type": "int",
      "name": "BotaoAltura",
      "default": "40",
      "comment": null
    },
    {
      "line": 35,
      "raw": "input color  CorBotao           = clrRed;",
      "type": "color",
      "name": "CorBotao",
      "default": "clrRed",
      "comment": null
    },
    {
      "line": 36,
      "raw": "input color  CorTextoBotao      = clrWhite;",
      "type": "color",
      "name": "CorTextoBotao",
      "default": "clrWhite",
      "comment": null
    }
  ],
  "event_functions": [
    "OnInit",
    "OnChartEvent",
    "OnTick",
    "OnDeinit"
  ],
  "logic_cues": {
    "has_magic_number": true,
    "has_spread_filter": true,
    "has_initial_hedge_cue": true,
    "has_directional_cue": true,
    "has_lot_increase_cue": true,
    "has_no_lot_increase_cue": false,
    "has_pending_order_cue": false,
    "has_recovery_cue": false,
    "has_close_all_button_cue": true,
    "has_reset_state_cue": true,
    "has_timer_event": false,
    "has_tick_event": true,
    "has_chart_event": true,
    "trade_keyword_hits": {
      "CTrade": 1,
      "trade.Buy": 1,
      "trade.Sell": 1,
      "PositionSelect": 1,
      "PositionSelectByTicket": 1,
      "PositionsTotal": 3,
      "PositionClose": 1
    },
    "lot_keyword_hits": {
      "lot": 13,
      "Lot": 64,
      "lote": 2,
      "HedgeSmallLot": 5,
      "HedgeLargeLot": 5,
      "DirectionalLot": 3,
      "LotIncrease": 2
    },
    "hedge_keyword_hits": {
      "hedge": 8,
      "Hedge": 17,
      "small": 16,
      "Small": 67,
      "large": 16,
      "Large": 69,
      "directional": 6,
      "Directional": 18,
      "direcional": 1,
      "isolating": 7,
      "Isolating": 2,
      "base": 1,
      "Base": 11
    },
    "pending_keyword_hits": {},
    "risk_keyword_hits": {
      "StopThreshold": 3,
      "MaxSpread": 4,
      "DD": 1,
      "stop": 2,
      "Stop": 5,
      "margin": 6
    }
  },
  "candidate_strengths": [
    {
      "confidence": "medium",
      "point": "Possui pista de MagicNumber/magic, útil para separar instâncias e multi-EA."
    },
    {
      "confidence": "medium",
      "point": "Possui pista de filtro de spread, útil para evitar entradas em condição ruim."
    },
    {
      "confidence": "low",
      "point": "Possui pistas de estrutura hedge small/large ou travamento inicial."
    },
    {
      "confidence": "medium",
      "point": "Possui pista de botão/rotina de fechamento ou reset operacional."
    }
  ],
  "candidate_weaknesses": [
    {
      "confidence": "medium",
      "point": "Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida."
    }
  ],
  "unknown_points": [
    "Há pistas de aumento de lote, mas esta etapa ainda não prova quando e por que o lote aumenta.",
    "Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código."
  ]
}

{
  "version_id": "P0_V1",
  "source_file": "Hedge_P00_V1-TravamentoNoInicioNaoJuntocomDirecional.mq5",
  "properties": [
    {
      "line": 6,
      "name": "strict",
      "value": ""
    },
    {
      "line": 7,
      "name": "description",
      "value": "\"Hedge P00 V1: Start BUY+SELL; Fecha lucro no range; Abre DIR a mercado; Coloca hedges pendings no preço base com offset (LIMIT antes STOP); Resolve quando lucro base+hedge_same cobre perda DIR; Fecha DIR+opp+BASE, sobra hedge_same como novo base.\""
    }
  ],
  "inputs": [
    {
      "line": 13,
      "raw": "input ulong MagicNumber     = 20260206;",
      "type": "ulong",
      "name": "MagicNumber",
      "default": "20260206",
      "comment": null
    },
    {
      "line": 14,
      "raw": "input string CommentText    = \"P2_A\";",
      "type": "string",
      "name": "CommentText",
      "default": "\"P2_A\"",
      "comment": null
    },
    {
      "line": 15,
      "raw": "input bool   AutoStart      = true;",
      "type": "bool",
      "name": "AutoStart",
      "default": "true",
      "comment": null
    },
    {
      "line": 16,
      "raw": "input double StartLot       = 0.02;",
      "type": "double",
      "name": "StartLot",
      "default": "0.02",
      "comment": null
    },
    {
      "line": 17,
      "raw": "input int    RangePts       = 300;",
      "type": "int",
      "name": "RangePts",
      "default": "300",
      "comment": null
    },
    {
      "line": 18,
      "raw": "input double StepLot        = 0.01;",
      "type": "double",
      "name": "StepLot",
      "default": "0.01",
      "comment": null
    },
    {
      "line": 19,
      "raw": "input double HedgeExtraLot  = 0.01;",
      "type": "double",
      "name": "HedgeExtraLot",
      "default": "0.01",
      "comment": null
    },
    {
      "line": 20,
      "raw": "input int    DeviationPts   = 30;",
      "type": "int",
      "name": "DeviationPts",
      "default": "30",
      "comment": null
    },
    {
      "line": 21,
      "raw": "input int    HedgeOffsetPts = 30;",
      "type": "int",
      "name": "HedgeOffsetPts",
      "default": "30",
      "comment": null
    },
    {
      "line": 22,
      "raw": "input double MinLot         = 0.01;",
      "type": "double",
      "name": "MinLot",
      "default": "0.01",
      "comment": null
    },
    {
      "line": 23,
      "raw": "input int    CooldownMs     = 800;",
      "type": "int",
      "name": "CooldownMs",
      "default": "800",
      "comment": null
    },
    {
      "line": 24,
      "raw": "input int    TimerMs        = 1200;",
      "type": "int",
      "name": "TimerMs",
      "default": "1200",
      "comment": null
    },
    {
      "line": 25,
      "raw": "input int    ReturnTolPts   = 5;",
      "type": "int",
      "name": "ReturnTolPts",
      "default": "5",
      "comment": null
    },
    {
      "line": 28,
      "raw": "input color  CorBuy         = clrLime;",
      "type": "color",
      "name": "CorBuy",
      "default": "clrLime",
      "comment": null
    },
    {
      "line": 29,
      "raw": "input color  CorSell        = clrTomato;",
      "type": "color",
      "name": "CorSell",
      "default": "clrTomato",
      "comment": null
    },
    {
      "line": 30,
      "raw": "input color  CorNet         = clrDeepSkyBlue;",
      "type": "color",
      "name": "CorNet",
      "default": "clrDeepSkyBlue",
      "comment": null
    },
    {
      "line": 31,
      "raw": "input color  CorProfit      = clrDodgerBlue;",
      "type": "color",
      "name": "CorProfit",
      "default": "clrDodgerBlue",
      "comment": null
    },
    {
      "line": 32,
      "raw": "input int    FonteUI        = 12;",
      "type": "int",
      "name": "FonteUI",
      "default": "12",
      "comment": null
    },
    {
      "line": 33,
      "raw": "input int    PosX_UI        = 90;",
      "type": "int",
      "name": "PosX_UI",
      "default": "90",
      "comment": null
    },
    {
      "line": 34,
      "raw": "input int    PosY_UI        = 20;",
      "type": "int",
      "name": "PosY_UI",
      "default": "20",
      "comment": null
    },
    {
      "line": 35,
      "raw": "input int    Esp_UI         = 18;",
      "type": "int",
      "name": "Esp_UI",
      "default": "18",
      "comment": null
    },
    {
      "line": 38,
      "raw": "input string BotaoCloseAll  = \"Close_All_EA\";",
      "type": "string",
      "name": "BotaoCloseAll",
      "default": "\"Close_All_EA\"",
      "comment": null
    },
    {
      "line": 39,
      "raw": "input int    BotaoPosX      = 20;",
      "type": "int",
      "name": "BotaoPosX",
      "default": "20",
      "comment": null
    },
    {
      "line": 40,
      "raw": "input int    BotaoPosY      = 20;",
      "type": "int",
      "name": "BotaoPosY",
      "default": "20",
      "comment": null
    },
    {
      "line": 41,
      "raw": "input int    BotaoW         = 120;",
      "type": "int",
      "name": "BotaoW",
      "default": "120",
      "comment": null
    },
    {
      "line": 42,
      "raw": "input int    BotaoH         = 30;",
      "type": "int",
      "name": "BotaoH",
      "default": "30",
      "comment": null
    },
    {
      "line": 43,
      "raw": "input color  CorBotao       = clrRed;",
      "type": "color",
      "name": "CorBotao",
      "default": "clrRed",
      "comment": null
    },
    {
      "line": 44,
      "raw": "input color  CorTxtBotao    = clrWhite;",
      "type": "color",
      "name": "CorTxtBotao",
      "default": "clrWhite",
      "comment": null
    }
  ],
  "event_functions": [
    "OnInit",
    "OnDeinit",
    "OnTimer",
    "OnChartEvent",
    "OnTick"
  ],
  "logic_cues": {
    "has_magic_number": true,
    "has_spread_filter": false,
    "has_initial_hedge_cue": false,
    "has_directional_cue": true,
    "has_lot_increase_cue": false,
    "has_no_lot_increase_cue": false,
    "has_pending_order_cue": true,
    "has_recovery_cue": true,
    "has_close_all_button_cue": true,
    "has_reset_state_cue": false,
    "has_timer_event": true,
    "has_tick_event": true,
    "has_chart_event": true,
    "trade_keyword_hits": {
      "CTrade": 1,
      "trade.Buy": 2,
      "trade.Sell": 2,
      "PositionSelect": 12,
      "PositionSelectByTicket": 12,
      "PositionsTotal": 6,
      "OrdersTotal": 2,
      "PositionClose": 6,
      "OrderDelete": 2
    },
    "lot_keyword_hits": {
      "lot": 15,
      "Lot": 33,
      "StepLot": 2,
      "MinLot": 4
    },
    "hedge_keyword_hits": {
      "hedge": 33,
      "Hedge": 12,
      "base": 64,
      "Base": 7
    },
    "pending_keyword_hits": {
      "pending": 8,
      "BUY_LIMIT": 2,
      "SELL_LIMIT": 1,
      "BUY_STOP": 1,
      "SELL_STOP": 2
    },
    "risk_keyword_hits": {}
  },
  "candidate_strengths": [
    {
      "confidence": "medium",
      "point": "Possui pista de MagicNumber/magic, útil para separar instâncias e multi-EA."
    },
    {
      "confidence": "medium",
      "point": "Possui pista de botão/rotina de fechamento ou reset operacional."
    }
  ],
  "candidate_weaknesses": [
    {
      "confidence": "low",
      "point": "Não foi detectada pista clara de filtro de spread nesta análise textual."
    }
  ],
  "unknown_points": [
    "Há pistas de ordens pendentes, mas a sequência exata de criação/renovação ainda precisa ser interpretada.",
    "Há pistas de recovery/resolve, mas a regra matemática de recuperação ainda precisa ser validada.",
    "Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código."
  ]
}

{
  "version_id": "P0_V2",
  "source_file": "Hedge_P0_V2-RangeAumentoLot-NaoFunciona2EAS.mq5",
  "properties": [
    {
      "line": 5,
      "name": "copyright",
      "value": "\"xAI\""
    },
    {
      "line": 6,
      "name": "link",
      "value": "\"\""
    },
    {
      "line": 7,
      "name": "version",
      "value": "\"1.11\""
    },
    {
      "line": 8,
      "name": "strict",
      "value": ""
    },
    {
      "line": 9,
      "name": "description",
      "value": "\"Hedge Progressivo - Extra lot quando range isolating > 400 pts + directional dinâmico (diferença)\""
    }
  ],
  "inputs": [
    {
      "line": 16,
      "raw": "input double HedgeSmallLot      = 0.03;       // Lote inicial small hedge",
      "type": "double",
      "name": "HedgeSmallLot",
      "default": "0.03",
      "comment": "Lote inicial small hedge"
    },
    {
      "line": 17,
      "raw": "input double HedgeLargeLot      = 0.04;       // Lote inicial large hedge",
      "type": "double",
      "name": "HedgeLargeLot",
      "default": "0.04",
      "comment": "Lote inicial large hedge"
    },
    {
      "line": 18,
      "raw": "input double DirectionalLot     = 0.02;       // Lote direcional base (fixo fallback)",
      "type": "double",
      "name": "DirectionalLot",
      "default": "0.02",
      "comment": "Lote direcional base (fixo fallback)"
    },
    {
      "line": 19,
      "raw": "input double LotIncrease        = 0.01;       // Incremento padrão por nível",
      "type": "double",
      "name": "LotIncrease",
      "default": "0.01",
      "comment": "Incremento padrão por nível"
    },
    {
      "line": 20,
      "raw": "input double ExtraLotWhenFar    = 0.01;       // Extra lot se range isolating > FarRangePts",
      "type": "double",
      "name": "ExtraLotWhenFar",
      "default": "0.01",
      "comment": "Extra lot se range isolating > FarRangePts"
    },
    {
      "line": 21,
      "raw": "input int    FarRangePts        = 400;        // Threshold range pts para extra lot",
      "type": "int",
      "name": "FarRangePts",
      "default": "400",
      "comment": "Threshold range pts para extra lot"
    },
    {
      "line": 22,
      "raw": "input double StopThresholdUSD   = -8.0;       // Limite USD para stop",
      "type": "double",
      "name": "StopThresholdUSD",
      "default": "-8.0",
      "comment": "Limite USD para stop"
    },
    {
      "line": 23,
      "raw": "input string TriggerMode        = \"usd\";      // \"pts\" ou \"usd\"",
      "type": "string",
      "name": "TriggerMode",
      "default": "\"usd\"",
      "comment": "\"pts\" ou \"usd\""
    },
    {
      "line": 24,
      "raw": "input double TriggerValue       = 10.0;       // Valor do trigger",
      "type": "double",
      "name": "TriggerValue",
      "default": "10.0",
      "comment": "Valor do trigger"
    },
    {
      "line": 25,
      "raw": "input int    MagicBase          = 12345;      // Magic base",
      "type": "int",
      "name": "MagicBase",
      "default": "12345",
      "comment": "Magic base"
    },
    {
      "line": 26,
      "raw": "input double MaxSpread          = 50.0;       // Spread max",
      "type": "double",
      "name": "MaxSpread",
      "default": "50.0",
      "comment": "Spread max"
    },
    {
      "line": 27,
      "raw": "input bool   IgnoreSpreadOnReset= true;",
      "type": "bool",
      "name": "IgnoreSpreadOnReset",
      "default": "true",
      "comment": null
    },
    {
      "line": 28,
      "raw": "input bool   ForceInitialHedge  = false;",
      "type": "bool",
      "name": "ForceInitialHedge",
      "default": "false",
      "comment": null
    },
    {
      "line": 29,
      "raw": "input bool   ResetStateOnStart  = false;",
      "type": "bool",
      "name": "ResetStateOnStart",
      "default": "false",
      "comment": null
    },
    {
      "line": 32,
      "raw": "input string BotaoCloseReset    = \"Close_All_Reset\";",
      "type": "string",
      "name": "BotaoCloseReset",
      "default": "\"Close_All_Reset\"",
      "comment": null
    },
    {
      "line": 33,
      "raw": "input int    BotaoPosX          = 30;",
      "type": "int",
      "name": "BotaoPosX",
      "default": "30",
      "comment": null
    },
    {
      "line": 34,
      "raw": "input int    BotaoPosY          = 30;",
      "type": "int",
      "name": "BotaoPosY",
      "default": "30",
      "comment": null
    },
    {
      "line": 35,
      "raw": "input int    BotaoLargura       = 160;",
      "type": "int",
      "name": "BotaoLargura",
      "default": "160",
      "comment": null
    },
    {
      "line": 36,
      "raw": "input int    BotaoAltura        = 40;",
      "type": "int",
      "name": "BotaoAltura",
      "default": "40",
      "comment": null
    },
    {
      "line": 37,
      "raw": "input color  CorBotao           = clrRed;",
      "type": "color",
      "name": "CorBotao",
      "default": "clrRed",
      "comment": null
    },
    {
      "line": 38,
      "raw": "input color  CorTextoBotao      = clrWhite;",
      "type": "color",
      "name": "CorTextoBotao",
      "default": "clrWhite",
      "comment": null
    }
  ],
  "event_functions": [
    "OnInit",
    "OnChartEvent",
    "OnTick",
    "OnDeinit"
  ],
  "logic_cues": {
    "has_magic_number": true,
    "has_spread_filter": true,
    "has_initial_hedge_cue": true,
    "has_directional_cue": true,
    "has_lot_increase_cue": true,
    "has_no_lot_increase_cue": false,
    "has_pending_order_cue": false,
    "has_recovery_cue": false,
    "has_close_all_button_cue": true,
    "has_reset_state_cue": true,
    "has_timer_event": false,
    "has_tick_event": true,
    "has_chart_event": true,
    "trade_keyword_hits": {
      "CTrade": 1,
      "trade.Buy": 1,
      "trade.Sell": 1,
      "PositionSelect": 3,
      "PositionSelectByTicket": 3,
      "PositionsTotal": 3,
      "PositionClose": 1
    },
    "lot_keyword_hits": {
      "lot": 15,
      "Lot": 62,
      "HedgeSmallLot": 5,
      "HedgeLargeLot": 5,
      "DirectionalLot": 3,
      "LotIncrease": 2
    },
    "hedge_keyword_hits": {
      "hedge": 3,
      "Hedge": 16,
      "small": 7,
      "Small": 64,
      "large": 17,
      "Large": 69,
      "directional": 4,
      "Directional": 17,
      "direcional": 1,
      "isolating": 11,
      "Isolating": 2,
      "base": 2,
      "Base": 11
    },
    "pending_keyword_hits": {},
    "risk_keyword_hits": {
      "StopThreshold": 2,
      "MaxSpread": 4,
      "stop": 1,
      "Stop": 2
    }
  },
  "candidate_strengths": [
    {
      "confidence": "medium",
      "point": "Possui pista de MagicNumber/magic, útil para separar instâncias e multi-EA."
    },
    {
      "confidence": "medium",
      "point": "Possui pista de filtro de spread, útil para evitar entradas em condição ruim."
    },
    {
      "confidence": "low",
      "point": "Possui pistas de estrutura hedge small/large ou travamento inicial."
    },
    {
      "confidence": "medium",
      "point": "Possui pista de botão/rotina de fechamento ou reset operacional."
    }
  ],
  "candidate_weaknesses": [
    {
      "confidence": "medium",
      "point": "Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida."
    }
  ],
  "unknown_points": [
    "Há pistas de aumento de lote, mas esta etapa ainda não prova quando e por que o lote aumenta.",
    "Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código."
  ]
}

{
  "version_id": "P0_V3",
  "source_file": "Hedge_P0_V3.mq5",
  "properties": [
    {
      "line": 5,
      "name": "copyright",
      "value": "\"xAI\""
    },
    {
      "line": 6,
      "name": "link",
      "value": "\"\""
    },
    {
      "line": 7,
      "name": "version",
      "value": "\"1.16\""
    },
    {
      "line": 8,
      "name": "strict",
      "value": ""
    },
    {
      "line": 9,
      "name": "description",
      "value": "\"Hedge Progressivo - Correção tracking/sequência após aumento de lot\""
    }
  ],
  "inputs": [
    {
      "line": 16,
      "raw": "input double HedgeSmallLot             = 0.03;   // Lote inicial small hedge",
      "type": "double",
      "name": "HedgeSmallLot",
      "default": "0.03",
      "comment": "Lote inicial small hedge"
    },
    {
      "line": 17,
      "raw": "input double HedgeLargeLot             = 0.04;   // Lote inicial large hedge",
      "type": "double",
      "name": "HedgeLargeLot",
      "default": "0.04",
      "comment": "Lote inicial large hedge"
    },
    {
      "line": 18,
      "raw": "input double LotIncrease               = 0.01;   // Incremento normal por nível",
      "type": "double",
      "name": "LotIncrease",
      "default": "0.01",
      "comment": "Incremento normal por nível"
    },
    {
      "line": 19,
      "raw": "input double ExtraLotIncreaseOnRange   = 0.01;   // Extra se range > threshold",
      "type": "double",
      "name": "ExtraLotIncreaseOnRange",
      "default": "0.01",
      "comment": "Extra se range > threshold"
    },
    {
      "line": 20,
      "raw": "input int    RangeThresholdPts         = 400;    // Range em pts para extra increase",
      "type": "int",
      "name": "RangeThresholdPts",
      "default": "400",
      "comment": "Range em pts para extra increase"
    },
    {
      "line": 21,
      "raw": "input double DirectionalLot            = 0.02;   // Lote direcional FIXO (se preferir dinâmico, altere no código)",
      "type": "double",
      "name": "DirectionalLot",
      "default": "0.02",
      "comment": "Lote direcional FIXO (se preferir dinâmico, altere no código)"
    },
    {
      "line": 22,
      "raw": "input double StopThresholdUSD          = -8.0;   // Limite USD para stop (net small + directional)",
      "type": "double",
      "name": "StopThresholdUSD",
      "default": "-8.0",
      "comment": "Limite USD para stop (net small + directional)"
    },
    {
      "line": 23,
      "raw": "input string TriggerMode               = \"usd\";  // \"pts\" ou \"usd\"",
      "type": "string",
      "name": "TriggerMode",
      "default": "\"usd\"",
      "comment": "\"pts\" ou \"usd\""
    },
    {
      "line": 24,
      "raw": "input double TriggerValue              = 10.0;   // Valor do trigger (pts ou net USD)",
      "type": "double",
      "name": "TriggerValue",
      "default": "10.0",
      "comment": "Valor do trigger (pts ou net USD)"
    },
    {
      "line": 25,
      "raw": "input int    MagicBase                 = 12345;  // Magic base (mude para cada instância!)",
      "type": "int",
      "name": "MagicBase",
      "default": "12345",
      "comment": "Magic base (mude para cada instância!)"
    },
    {
      "line": 26,
      "raw": "input string EA_InstanceSuffix         = \"p0-1\"; // Sufixo único no INÍCIO dos comentários",
      "type": "string",
      "name": "EA_InstanceSuffix",
      "default": "\"p0-1\"",
      "comment": "Sufixo único no INÍCIO dos comentários"
    },
    {
      "line": 27,
      "raw": "input double MaxSpread                 = 50.0;   // Spread max em points",
      "type": "double",
      "name": "MaxSpread",
      "default": "50.0",
      "comment": "Spread max em points"
    },
    {
      "line": 28,
      "raw": "input bool   IgnoreSpreadOnReset       = true;   // Ignora spread após reset ou botão",
      "type": "bool",
      "name": "IgnoreSpreadOnReset",
      "default": "true",
      "comment": "Ignora spread após reset ou botão"
    },
    {
      "line": 29,
      "raw": "input bool   ForceInitialHedge         = false;  // Força abertura mesmo com posições",
      "type": "bool",
      "name": "ForceInitialHedge",
      "default": "false",
      "comment": "Força abertura mesmo com posições"
    },
    {
      "line": 30,
      "raw": "input bool   ResetStateOnStart         = false;  // RESET ao iniciar",
      "type": "bool",
      "name": "ResetStateOnStart",
      "default": "false",
      "comment": "RESET ao iniciar"
    },
    {
      "line": 33,
      "raw": "input color CorBuy                     = clrGreen;",
      "type": "color",
      "name": "CorBuy",
      "default": "clrGreen",
      "comment": null
    },
    {
      "line": 34,
      "raw": "input color CorSell                    = clrRed;",
      "type": "color",
      "name": "CorSell",
      "default": "clrRed",
      "comment": null
    },
    {
      "line": 35,
      "raw": "input color CorNet                     = clrBlueViolet;",
      "type": "color",
      "name": "CorNet",
      "default": "clrBlueViolet",
      "comment": null
    },
    {
      "line": 36,
      "raw": "input color CorLucro                   = clrBlue;",
      "type": "color",
      "name": "CorLucro",
      "default": "clrBlue",
      "comment": null
    },
    {
      "line": 37,
      "raw": "input int   TamanhoFonte               = 12;",
      "type": "int",
      "name": "TamanhoFonte",
      "default": "12",
      "comment": null
    },
    {
      "line": 38,
      "raw": "input int   PosX                       = 90;",
      "type": "int",
      "name": "PosX",
      "default": "90",
      "comment": null
    },
    {
      "line": 39,
      "raw": "input int   PosY                       = 20;",
      "type": "int",
      "name": "PosY",
      "default": "20",
      "comment": null
    },
    {
      "line": 40,
      "raw": "input int   Espacamento                = 18;",
      "type": "int",
      "name": "Espacamento",
      "default": "18",
      "comment": null
    },
    {
      "line": 43,
      "raw": "input string BotaoCloseReset           = \"Close_All_Reset\";",
      "type": "string",
      "name": "BotaoCloseReset",
      "default": "\"Close_All_Reset\"",
      "comment": null
    },
    {
      "line": 44,
      "raw": "input int    BotaoPosX                 = 20;",
      "type": "int",
      "name": "BotaoPosX",
      "default": "20",
      "comment": null
    },
    {
      "line": 45,
      "raw": "input int    BotaoPosY                 = 20;",
      "type": "int",
      "name": "BotaoPosY",
      "default": "20",
      "comment": null
    },
    {
      "line": 46,
      "raw": "input int    BotaoLargura              = 140;",
      "type": "int",
      "name": "BotaoLargura",
      "default": "140",
      "comment": null
    },
    {
      "line": 47,
      "raw": "input int    BotaoAltura               = 30;",
      "type": "int",
      "name": "BotaoAltura",
      "default": "30",
      "comment": null
    },
    {
      "line": 48,
      "raw": "input color  CorBotao                  = clrRed;",
      "type": "color",
      "name": "CorBotao",
      "default": "clrRed",
      "comment": null
    },
    {
      "line": 49,
      "raw": "input color  CorTextoBotao             = clrWhite;",
      "type": "color",
      "name": "CorTextoBotao",
      "default": "clrWhite",
      "comment": null
    }
  ],
  "event_functions": [
    "OnInit",
    "OnChartEvent",
    "OnTick",
    "OnDeinit"
  ],
  "logic_cues": {
    "has_magic_number": true,
    "has_spread_filter": true,
    "has_initial_hedge_cue": true,
    "has_directional_cue": true,
    "has_lot_increase_cue": true,
    "has_no_lot_increase_cue": false,
    "has_pending_order_cue": false,
    "has_recovery_cue": false,
    "has_close_all_button_cue": true,
    "has_reset_state_cue": true,
    "has_timer_event": false,
    "has_tick_event": true,
    "has_chart_event": true,
    "trade_keyword_hits": {
      "CTrade": 1,
      "trade.Buy": 1,
      "trade.Sell": 1,
      "PositionSelect": 1,
      "PositionSelectByTicket": 1,
      "PositionsTotal": 4,
      "PositionClose": 1
    },
    "lot_keyword_hits": {
      "lot": 15,
      "Lot": 34,
      "lote": 1,
      "HedgeSmallLot": 6,
      "HedgeLargeLot": 9,
      "DirectionalLot": 3,
      "LotIncrease": 4
    },
    "hedge_keyword_hits": {
      "hedge": 5,
      "Hedge": 28,
      "small": 19,
      "Small": 53,
      "large": 21,
      "Large": 54,
      "directional": 10,
      "Directional": 19,
      "direcional": 1,
      "isolating": 7,
      "Isolating": 1,
      "base": 4,
      "Base": 17
    },
    "pending_keyword_hits": {},
    "risk_keyword_hits": {
      "StopThreshold": 3,
      "MaxSpread": 4,
      "DD": 1,
      "stop": 1,
      "Stop": 5,
      "margin": 6
    }
  },
  "candidate_strengths": [
    {
      "confidence": "medium",
      "point": "Possui pista de MagicNumber/magic, útil para separar instâncias e multi-EA."
    },
    {
      "confidence": "medium",
      "point": "Possui pista de filtro de spread, útil para evitar entradas em condição ruim."
    },
    {
      "confidence": "low",
      "point": "Possui pistas de estrutura hedge small/large ou travamento inicial."
    },
    {
      "confidence": "medium",
      "point": "Possui pista de botão/rotina de fechamento ou reset operacional."
    }
  ],
  "candidate_weaknesses": [
    {
      "confidence": "medium",
      "point": "Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida."
    }
  ],
  "unknown_points": [
    "Há pistas de aumento de lote, mas esta etapa ainda não prova quando e por que o lote aumenta.",
    "Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código."
  ]
}

{
  "version_id": "P0_V4",
  "source_file": "Hedge_P0_V4.mq5",
  "properties": [
    {
      "line": 5,
      "name": "copyright",
      "value": "\"xAI\""
    },
    {
      "line": 6,
      "name": "link",
      "value": "\"\""
    },
    {
      "line": 7,
      "name": "version",
      "value": "\"1.17\""
    },
    {
      "line": 8,
      "name": "strict",
      "value": ""
    },
    {
      "line": 9,
      "name": "description",
      "value": "\"Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease\""
    }
  ],
  "inputs": [
    {
      "line": 16,
      "raw": "input double HedgeSmallLot             = 0.03;   // Lote inicial small hedge",
      "type": "double",
      "name": "HedgeSmallLot",
      "default": "0.03",
      "comment": "Lote inicial small hedge"
    },
    {
      "line": 17,
      "raw": "input double HedgeLargeLot             = 0.04;   // Lote inicial large hedge",
      "type": "double",
      "name": "HedgeLargeLot",
      "default": "0.04",
      "comment": "Lote inicial large hedge"
    },
    {
      "line": 18,
      "raw": "input double LotIncrease               = 0.01;   // Incremento normal por nível + net direcional fixed",
      "type": "double",
      "name": "LotIncrease",
      "default": "0.01",
      "comment": "Incremento normal por nível + net direcional fixed"
    },
    {
      "line": 19,
      "raw": "input double ExtraLotIncreaseOnRange   = 0.01;   // Extra se range > threshold",
      "type": "double",
      "name": "ExtraLotIncreaseOnRange",
      "default": "0.01",
      "comment": "Extra se range > threshold"
    },
    {
      "line": 20,
      "raw": "input int    RangeThresholdPts         = 400;    // Range em pts para extra increase",
      "type": "int",
      "name": "RangeThresholdPts",
      "default": "400",
      "comment": "Range em pts para extra increase"
    },
    {
      "line": 21,
      "raw": "input double StopThresholdUSD          = -8.0;   // Limite USD para stop (net small + directional)",
      "type": "double",
      "name": "StopThresholdUSD",
      "default": "-8.0",
      "comment": "Limite USD para stop (net small + directional)"
    },
    {
      "line": 22,
      "raw": "input string TriggerMode               = \"usd\";  // \"pts\" ou \"usd\"",
      "type": "string",
      "name": "TriggerMode",
      "default": "\"usd\"",
      "comment": "\"pts\" ou \"usd\""
    },
    {
      "line": 23,
      "raw": "input double TriggerValue              = 10.0;   // Valor do trigger (pts ou net USD)",
      "type": "double",
      "name": "TriggerValue",
      "default": "10.0",
      "comment": "Valor do trigger (pts ou net USD)"
    },
    {
      "line": 24,
      "raw": "input int    MagicBase                 = 12345;  // Magic base (mude para cada instância!)",
      "type": "int",
      "name": "MagicBase",
      "default": "12345",
      "comment": "Magic base (mude para cada instância!)"
    },
    {
      "line": 25,
      "raw": "input string EA_InstanceSuffix         = \"p0-1\"; // Sufixo único no INÍCIO dos comentários",
      "type": "string",
      "name": "EA_InstanceSuffix",
      "default": "\"p0-1\"",
      "comment": "Sufixo único no INÍCIO dos comentários"
    },
    {
      "line": 26,
      "raw": "input double MaxSpread                 = 50.0;   // Spread max em points",
      "type": "double",
      "name": "MaxSpread",
      "default": "50.0",
      "comment": "Spread max em points"
    },
    {
      "line": 27,
      "raw": "input bool   IgnoreSpreadOnReset       = true;   // Ignora spread após reset ou botão",
      "type": "bool",
      "name": "IgnoreSpreadOnReset",
      "default": "true",
      "comment": "Ignora spread após reset ou botão"
    },
    {
      "line": 28,
      "raw": "input bool   ForceInitialHedge         = false;  // Força abertura mesmo com posições",
      "type": "bool",
      "name": "ForceInitialHedge",
      "default": "false",
      "comment": "Força abertura mesmo com posições"
    },
    {
      "line": 29,
      "raw": "input bool   ResetStateOnStart         = false;  // RESET ao iniciar",
      "type": "bool",
      "name": "ResetStateOnStart",
      "default": "false",
      "comment": "RESET ao iniciar"
    },
    {
      "line": 32,
      "raw": "input color CorBuy                     = clrGreen;",
      "type": "color",
      "name": "CorBuy",
      "default": "clrGreen",
      "comment": null
    },
    {
      "line": 33,
      "raw": "input color CorSell                    = clrRed;",
      "type": "color",
      "name": "CorSell",
      "default": "clrRed",
      "comment": null
    },
    {
      "line": 34,
      "raw": "input color CorNet                     = clrBlueViolet;",
      "type": "color",
      "name": "CorNet",
      "default": "clrBlueViolet",
      "comment": null
    },
    {
      "line": 35,
      "raw": "input color CorLucro                   = clrBlue;",
      "type": "color",
      "name": "CorLucro",
      "default": "clrBlue",
      "comment": null
    },
    {
      "line": 36,
      "raw": "input int   TamanhoFonte               = 12;",
      "type": "int",
      "name": "TamanhoFonte",
      "default": "12",
      "comment": null
    },
    {
      "line": 37,
      "raw": "input int   PosX                       = 90;",
      "type": "int",
      "name": "PosX",
      "default": "90",
      "comment": null
    },
    {
      "line": 38,
      "raw": "input int   PosY                       = 20;",
      "type": "int",
      "name": "PosY",
      "default": "20",
      "comment": null
    },
    {
      "line": 39,
      "raw": "input int   Espacamento                = 18;",
      "type": "int",
      "name": "Espacamento",
      "default": "18",
      "comment": null
    },
    {
      "line": 42,
      "raw": "input string BotaoCloseReset           = \"Close_All_Reset\";",
      "type": "string",
      "name": "BotaoCloseReset",
      "default": "\"Close_All_Reset\"",
      "comment": null
    },
    {
      "line": 43,
      "raw": "input int    BotaoPosX                 = 20;",
      "type": "int",
      "name": "BotaoPosX",
      "default": "20",
      "comment": null
    },
    {
      "line": 44,
      "raw": "input int    BotaoPosY                 = 20;",
      "type": "int",
      "name": "BotaoPosY",
      "default": "20",
      "comment": null
    },
    {
      "line": 45,
      "raw": "input int    BotaoLargura              = 140;",
      "type": "int",
      "name": "BotaoLargura",
      "default": "140",
      "comment": null
    },
    {
      "line": 46,
      "raw": "input int    BotaoAltura               = 30;",
      "type": "int",
      "name": "BotaoAltura",
      "default": "30",
      "comment": null
    },
    {
      "line": 47,
      "raw": "input color  CorBotao                  = clrRed;",
      "type": "color",
      "name": "CorBotao",
      "default": "clrRed",
      "comment": null
    },
    {
      "line": 48,
      "raw": "input color  CorTextoBotao             = clrWhite;",
      "type": "color",
      "name": "CorTextoBotao",
      "default": "clrWhite",
      "comment": null
    }
  ],
  "event_functions": [
    "OnInit",
    "OnChartEvent",
    "OnTick",
    "OnDeinit"
  ],
  "logic_cues": {
    "has_magic_number": true,
    "has_spread_filter": true,
    "has_initial_hedge_cue": true,
    "has_directional_cue": true,
    "has_lot_increase_cue": true,
    "has_no_lot_increase_cue": false,
    "has_pending_order_cue": false,
    "has_recovery_cue": false,
    "has_close_all_button_cue": true,
    "has_reset_state_cue": true,
    "has_timer_event": false,
    "has_tick_event": true,
    "has_chart_event": true,
    "trade_keyword_hits": {
      "CTrade": 1,
      "trade.Buy": 1,
      "trade.Sell": 1,
      "PositionSelect": 1,
      "PositionSelectByTicket": 1,
      "PositionsTotal": 4,
      "PositionClose": 1
    },
    "lot_keyword_hits": {
      "lot": 16,
      "Lot": 73,
      "lote": 1,
      "HedgeSmallLot": 6,
      "HedgeLargeLot": 6,
      "LotIncrease": 7
    },
    "hedge_keyword_hits": {
      "hedge": 6,
      "Hedge": 25,
      "small": 17,
      "Small": 70,
      "large": 20,
      "Large": 75,
      "directional": 7,
      "Directional": 14,
      "direcional": 3,
      "isolating": 7,
      "Isolating": 1,
      "base": 3,
      "Base": 17
    },
    "pending_keyword_hits": {},
    "risk_keyword_hits": {
      "StopThreshold": 3,
      "MaxSpread": 4,
      "DD": 1,
      "stop": 2,
      "Stop": 5,
      "margin": 6
    }
  },
  "candidate_strengths": [
    {
      "confidence": "medium",
      "point": "Possui pista de MagicNumber/magic, útil para separar instâncias e multi-EA."
    },
    {
      "confidence": "medium",
      "point": "Possui pista de filtro de spread, útil para evitar entradas em condição ruim."
    },
    {
      "confidence": "low",
      "point": "Possui pistas de estrutura hedge small/large ou travamento inicial."
    },
    {
      "confidence": "medium",
      "point": "Possui pista de botão/rotina de fechamento ou reset operacional."
    }
  ],
  "candidate_weaknesses": [
    {
      "confidence": "medium",
      "point": "Possui pista de aumento de lote. Precisa medir impacto em DD, margem e exposição líquida."
    }
  ],
  "unknown_points": [
    "Há pistas de aumento de lote, mas esta etapa ainda não prova quando e por que o lote aumenta.",
    "Backtest ainda não foi executado; pontos fortes/fracos são apenas candidatos baseados em leitura de código."
  ]
}

## Evolution map compacto
{
  "versions_order": [
    "P0_BASE",
    "P0_V1",
    "P0_V2",
    "P0_V3",
    "P0_V4"
  ],
  "evolution_notes": [
    "P0_BASE: versão inicial analisada. Descrição detectada: \"Hedge Progressivo - Correção lotes globais não carregados + sequência garantida\".",
    "P0_BASE -> P0_V1; descrição detectada: \"Hedge P00 V1: Start BUY+SELL; Fecha lucro no range; Abre DIR a mercado; Coloca hedges pendings no preço base com offset (LIMIT antes STOP); Resolve quando lucro base+hedge_same cobre perda DIR; Fecha DIR+opp+BASE, sobra hedge_same como novo base.\"; inputs adicionados: ['AutoStart', 'BotaoCloseAll', 'BotaoH', 'BotaoW', 'CommentText', 'CooldownMs', 'CorBuy', 'CorNet', 'CorProfit', 'CorSell', '...(+15)']; inputs removidos: ['BotaoAltura', 'BotaoCloseReset', 'BotaoLargura', 'CorTextoBotao', 'DirectionalLot', 'ForceInitialHedge', 'HedgeLargeLot', 'HedgeSmallLot', 'IgnoreSpreadOnReset', 'LotIncrease', '...(+6)']; defaults alterados: ['BotaoPosX', 'BotaoPosY']; funções adicionadas: ['CloseAllByMagic', 'Cmt', 'CreateUI', 'CycleTag', 'FindTicketByExactComment', 'IsMyOrderByTicket', 'IsMyPosByTicket', 'IsTradeAllowedNow', 'MyPositionsCount', 'NormalizeLot', '...(+9)']; funções removidas: ['CloseAllOurPositionsAndReset', 'ClosePosition', 'CountOurPositions', 'GetPointsProfit', 'GetProfit', 'IsTriggered', 'OpenPosition', 'PositionExists']; mudanças de pistas: ['has_spread_filter: True -> False', 'has_initial_hedge_cue: True -> False', 'has_lot_increase_cue: True -> False', 'has_pending_order_cue: False -> True', 'has_recovery_cue: False -> True', 'has_reset_state_cue: True -> False', 'has_timer_event: False -> True'].",
    "P0_V1 -> P0_V2; descrição detectada: \"Hedge Progressivo - Extra lot quando range isolating > 400 pts + directional dinâmico (diferença)\"; inputs adicionados: ['BotaoAltura', 'BotaoCloseReset', 'BotaoLargura', 'CorTextoBotao', 'DirectionalLot', 'ExtraLotWhenFar', 'FarRangePts', 'ForceInitialHedge', 'HedgeLargeLot', 'HedgeSmallLot', '...(+8)']; inputs removidos: ['AutoStart', 'BotaoCloseAll', 'BotaoH', 'BotaoW', 'CommentText', 'CooldownMs', 'CorBuy', 'CorNet', 'CorProfit', 'CorSell', '...(+15)']; defaults alterados: ['BotaoPosX', 'BotaoPosY']; funções adicionadas: ['CloseAllOurPositionsAndReset', 'ClosePosition', 'CountOurPositions', 'GetPointsProfit', 'GetProfit', 'IsTriggered', 'OpenPosition', 'PositionExists']; funções removidas: ['CloseAllByMagic', 'Cmt', 'CreateUI', 'CycleTag', 'FindTicketByExactComment', 'IsMyOrderByTicket', 'IsMyPosByTicket', 'IsTradeAllowedNow', 'MyPositionsCount', 'NormalizeLot', '...(+9)']; mudanças de pistas: ['has_spread_filter: False -> True', 'has_initial_hedge_cue: False -> True', 'has_lot_increase_cue: False -> True', 'has_pending_order_cue: True -> False', 'has_recovery_cue: True -> False', 'has_reset_state_cue: False -> True', 'has_timer_event: True -> False'].",
    "P0_V2 -> P0_V3; descrição detectada: \"Hedge Progressivo - Correção tracking/sequência após aumento de lot\"; inputs adicionados: ['CorBuy', 'CorLucro', 'CorNet', 'CorSell', 'EA_InstanceSuffix', 'Espacamento', 'ExtraLotIncreaseOnRange', 'PosX', 'PosY', 'RangeThresholdPts', '...(+1)']; inputs removidos: ['ExtraLotWhenFar', 'FarRangePts']; defaults alterados: ['BotaoAltura', 'BotaoLargura', 'BotaoPosX', 'BotaoPosY']; funções adicionadas: ['AtualizarResumoNoGrafico'].",
    "P0_V3 -> P0_V4; descrição detectada: \"Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease\"; inputs removidos: ['DirectionalLot']."
  ],
  "subfamilies": {
    "progressive_hedge_or_lot_increase": [
      "P0_BASE",
      "P0_V2",
      "P0_V3",
      "P0_V4"
    ],
    "pending_recovery_or_initial_lock": [
      "P0_V1"
    ],
    "spread_magic_operational_control": [
      "P0_BASE",
      "P0_V1",
      "P0_V2",
      "P0_V3",
      "P0_V4"
    ]
  },
  "cue_matrix": {
    "has_chart_event": {
      "P0_BASE": true,
      "P0_V1": true,
      "P0_V2": true,
      "P0_V3": true,
      "P0_V4": true
    },
    "has_close_all_button_cue": {
      "P0_BASE": true,
      "P0_V1": true,
      "P0_V2": true,
      "P0_V3": true,
      "P0_V4": true
    },
    "has_directional_cue": {
      "P0_BASE": true,
      "P0_V1": true,
      "P0_V2": true,
      "P0_V3": true,
      "P0_V4": true
    },
    "has_initial_hedge_cue": {
      "P0_BASE": true,
      "P0_V1": false,
      "P0_V2": true,
      "P0_V3": true,
      "P0_V4": true
    },
    "has_lot_increase_cue": {
      "P0_BASE": true,
      "P0_V1": false,
      "P0_V2": true,
      "P0_V3": true,
      "P0_V4": true
    },
    "has_magic_number": {
      "P0_BASE": true,
      "P0_V1": true,
      "P0_V2": true,
      "P0_V3": true,
      "P0_V4": true
    },
    "has_no_lot_increase_cue": {
      "P0_BASE": false,
      "P0_V1": false,
      "P0_V2": false,
      "P0_V3": false,
      "P0_V4": false
    },
    "has_pending_order_cue": {
      "P0_BASE": false,
      "P0_V1": true,
      "P0_V2": false,
      "P0_V3": false,
      "P0_V4": false
    },
    "has_recovery_cue": {
      "P0_BASE": false,
      "P0_V1": true,
      "P0_V2": false,
      "P0_V3": false,
      "P0_V4": false
    },
    "has_reset_state_cue": {
      "P0_BASE": true,
      "P0_V1": false,
      "P0_V2": true,
      "P0_V3": true,
      "P0_V4": true
    },
    "has_spread_filter": {
      "P0_BASE": true,
      "P0_V1": false,
      "P0_V2": true,
      "P0_V3": true,
      "P0_V4": true
    },
    "has_tick_event": {
      "P0_BASE": true,
      "P0_V1": true,
      "P0_V2": true,
      "P0_V3": true,
      "P0_V4": true
    },
    "has_timer_event": {
      "P0_BASE": false,
      "P0_V1": true,
      "P0_V2": false,
      "P0_V3": false,
      "P0_V4": false
    }
  },
  "comparisons": [
    {
      "version_id": "P0_BASE",
      "source_file": "hedge_P0-NaoAmentaLot.mq5",
      "compared_to": null,
      "is_first_version": true,
      "property_version": "\"1.10\"",
      "property_description": "\"Hedge Progressivo - Correção lotes globais não carregados + sequência garantida\"",
      "input_names": [
        "BotaoAltura",
        "BotaoCloseReset",
        "BotaoLargura",
        "BotaoPosX",
        "BotaoPosY",
        "CorBotao",
        "CorTextoBotao",
        "DirectionalLot",
        "ForceInitialHedge",
        "HedgeLargeLot",
        "HedgeSmallLot",
        "IgnoreSpreadOnReset",
        "LotIncrease",
        "MagicBase",
        "MaxSpread",
        "ResetStateOnStart",
        "StopThresholdUSD",
        "TriggerMode",
        "TriggerValue"
      ],
      "function_names": [
        "CloseAllOurPositionsAndReset",
        "ClosePosition",
        "CountOurPositions",
        "GetPointsProfit",
        "GetProfit",
        "IsTriggered",
        "OnChartEvent",
        "OnDeinit",
        "OnInit",
        "OnTick",
        "OpenPosition",
        "PositionExists"
      ],
      "event_functions": [
        "OnInit",
        "OnChartEvent",
        "OnTick",
        "OnDeinit"
      ],
      "introduced_inputs": [
        "BotaoAltura",
        "BotaoCloseReset",
        "BotaoLargura",
        "BotaoPosX",
        "BotaoPosY",
        "CorBotao",
        "CorTextoBotao",
        "DirectionalLot",
        "ForceInitialHedge",
        "HedgeLargeLot",
        "HedgeSmallLot",
        "IgnoreSpreadOnReset",
        "LotIncrease",
        "MagicBase",
        "MaxSpread",
        "ResetStateOnStart",
        "StopThresholdUSD",
        "TriggerMode",
        "TriggerValue"
      ],
      "removed_inputs": [],
      "changed_input_defaults": [],
      "introduced_functions": [
        "CloseAllOurPositionsAndReset",
        "ClosePosition",
        "CountOurPositions",
        "GetPointsProfit",
        "GetProfit",
        "IsTriggered",
        "OnChartEvent",
        "OnDeinit",
        "OnInit",
        "OnTick",
        "OpenPosition",
        "PositionExists"
      ],
      "removed_functions": [],
      "logic_cues": {
        "has_magic_number": true,
        "has_spread_filter": true,
        "has_initial_hedge_cue": true,
        "has_directional_cue": true,
        "has_lot_increase_cue": true,
        "has_no_lot_increase_cue": false,
        "has_pending_order_cue": false,
        "has_recovery_cue": false,
        "has_close_all_button_cue": true,
        "has_reset_state_cue": true,
        "has_timer_event": false,
        "has_tick_event": true,
        "has_chart_event": true,
        "trade_keyword_hits": {
          "CTrade": 1,
          "trade.Buy": 1,
          "trade.Sell": 1,
          "PositionSelect": 1,
          "PositionSelectByTicket": 1,
          "PositionsTotal": 3,
          "PositionClose": 1
        },
        "lot_keyword_hits": {
          "lot": 13,
          "Lot": 64,
          "lote": 2,
          "HedgeSmallLot": 5,
          "HedgeLargeLot": 5,
          "DirectionalLot": 3,
          "LotIncrease": 2
        },
        "hedge_keyword_hits": {
          "hedge": 8,
          "Hedge": 17,
          "small": 16,
          "Small": 67,
          "large": 16,
          "Large": 69,
          "directional": 6,
          "Directional": 18,
          "direcional": 1,
          "isolating": 7,
          "Isolating": 2,
          "base": 1,
          "Base": 11
        },
        "pending_keyword_hits": {},
        "risk_keyword_hits": {
          "StopThreshold": 3,
          "MaxSpread": 4,
          "DD": 1,
          "stop": 2,
          "Stop": 5,
          "margin": 6
        }
      },
      "candidate_strengths": [
        {
          "confidence": "medium",
          "point": "Possui pista de MagicNumber/magic, útil para separar instâncias e multi-EA."
        },
        {
          "confidence": "medium",
          "point": "Possui pista de filtro de spread, útil para evitar entradas em condição ruim."
        },
        {
          "confidence": "low",
          "point": "Possui pistas de estrutura hedge small/large ou travamento inicial."
        },
        {
          "confidence": "medium",
          "point": "Possui pista de botão/rotina de fechamento