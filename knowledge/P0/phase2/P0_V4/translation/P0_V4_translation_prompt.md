TASK: Convert the provided MQL5 Expert Advisor logic into Python.

OUTPUT RULES:
Return ONLY valid JSON.
Do not explain.
Do not summarize.
Do not write markdown.
Do not say what the code appears to be.
Do not provide MQL4 examples.
Do not provide pseudo-code.

Required JSON schema:
{
  "translation_summary": ["short item"],
  "source_unresolved": ["short item"],
  "assumptions": ["short item"],
  "python_code": "complete Python code as one string"
}

python_code requirements:
- Must define class StrategyModel.
- Must implement:
  - __init__(self, params: dict)
  - on_start(self, price: float) -> None
  - on_bar(self, price: float, bar_index: int) -> None
  - get_positions(self) -> list[dict]
  - get_events(self) -> list[dict]
  - get_metrics_snapshot(self) -> dict
- Use only standard Python.
- No pandas, numpy, files, network, subprocess.
- If an MQL5 rule is unclear, put TODO_SOURCE_UNRESOLVED inside python_code.
- Positions must be dicts with side, lot, open_price, tag.
- Events must be dicts with event_type, price, bar_index, details.

CONTEXT:
# Translation Context P0/P0_V4

## Objetivo
Traduzir MQL5 para Python StrategyModel sem inventar regra.

## Contrato obrigatório
class StrategyModel:
    def __init__(self, params: dict): ...
    def on_start(self, price: float) -> None: ...
    def on_bar(self, price: float, bar_index: int) -> None: ...
    def get_positions(self) -> list[dict]: ...
    def get_events(self) -> list[dict]: ...
    def get_metrics_snapshot(self) -> dict: ...

## Spec compacto
{
  "family_id": "P0",
  "version_id": "P0_V4",
  "version": {
    "version_id": "P0_V4",
    "source_file": "Hedge_P0_V4.mq5",
    "description": "\"Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease\"",
    "subfamilies": [
      "progressive_hedge_or_lot_increase",
      "spread_magic_operational_control"
    ],
    "status": "draft_from_static_analysis",
    "primary_mechanisms": [
      "initial_hedge_or_small_large_structure",
      "directional_order_or_directional_exposure",
      "lot_increase_or_progressive_lot",
      "spread_filter",
      "magic_or_instance_separation"
    ],
    "parameter_candidates": {
      "HedgeSmallLot": {
        "default": "0.03",
        "type": "double",
        "comment": "Lote inicial small hedge",
        "line": 16
      },
      "HedgeLargeLot": {
        "default": "0.04",
        "type": "double",
        "comment": "Lote inicial large hedge",
        "line": 17
      },
      "LotIncrease": {
        "default": "0.01",
        "type": "double",
        "comment": "Incremento normal por nível + net direcional fixed",
        "line": 18
      },
      "ExtraLotIncreaseOnRange": {
        "default": "0.01",
        "type": "double",
        "comment": "Extra se range > threshold",
        "line": 19
      },
      "RangeThresholdPts": {
        "default": "400",
        "type": "int",
        "comment": "Range em pts para extra increase",
        "line": 20
      },
      "StopThresholdUSD": {
        "default": "-8.0",
        "type": "double",
        "comment": "Limite USD para stop (net small + directional)",
        "line": 21
      },
      "TriggerMode": {
        "default": "\"usd\"",
        "type": "string",
        "comment": "\"pts\" ou \"usd\"",
        "line": 22
      },
      "TriggerValue": {
        "default": "10.0",
        "type": "double",
        "comment": "Valor do trigger (pts ou net USD)",
        "line": 23
      },
      "MaxSpread": {
        "default": "50.0",
        "type": "double",
        "comment": "Spread max em points",
        "line": 26
      },
      "MagicBase": {
        "default": "12345",
        "type": "int",
        "comment": "Magic base (mude para cada instância!)",
        "line": 24
      },
      "EA_InstanceSuffix": {
        "default": "\"p0-1\"",
        "type": "string",
        "comment": "Sufixo único no INÍCIO dos comentários",
        "line": 25
      }
    },
    "event_functions": [
      "OnInit",
      "OnChartEvent",
      "OnTick",
      "OnDeinit"
    ],
    "evidence": {
      "inputs_count": 29,
      "functions_count": 13,
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
    },
    "source_verification_required": true,
    "resolution_status": "unresolved_from_sources",
    "checked_sources": [
      "Hedge_P0_V4.mq5",
      "versions/P0_V4_analysis.json"
    ]
  },
  "states": [
    {
      "id": "S0_EMPTY_OR_RESET",
      "description": "Nenhuma estrutura ativa da família ou estado resetado.",
      "entry_condition": "EA iniciado, resetado ou sem posições controladas pela instância."
    },
    {
      "id": "S1_INITIAL_MARKET_HEDGE",
      "description": "Travamento inicial a mercado com pares small/large BUY+SELL.",
      "entry_condition": "AutoStart/ForceInitialHedge ou condição inicial validada."
    },
    {
      "id": "S2_RANGE_TRIGGER_REACHED",
      "description": "Preço andou range/trigger suficiente para uma ordem maior lucrativa eliminar uma menor perdedora.",
      "entry_condition": "Trigger por pontos ou USD conforme configuração."
    },
    {
      "id": "S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL",
      "description": "Fecha par vencedor/perdedor e abre ordem direcional de exposição líquida controlada.",
      "entry_condition": "Eliminação validada e ordem direcional permitida."
    },
    {
      "id": "S4_RETURN_STOP_OR_RECOVERY",
      "description": "Preço retorna contra a direcional e tenta neutralizar stop/prejuízo com ordem remanescente.",
      "entry_condition": "Diferença/lucro combinado atinge threshold de stop/recovery."
    },
    {
      "id": "S5_NEXT_CYCLE_REBUILD",
      "description": "Recria/continua a estrutura com novo hedge, possivelmente com incremento de lote.",
      "entry_condition": "Recovery/eliminação concluída e próximo ciclo permitido."
    }
  ],
  "transitions": [
    {
      "from": "S0_EMPTY_OR_RESET",
      "to": "S1_INITIAL_MARKET_HEDGE",
      "event": "start_or_reset",
      "rule_draft": "Abrir BUY e SELL para small_hedge e BUY e SELL para large_hedge, se permitido.",
      "evidence": "Prompt humano descreve início com 4 ordens: compra/venda 0.03 e compra/venda 0.04.",
      "confidence": "medium"
    },
    {
      "from": "S1_INITIAL_MARKET_HEDGE",
      "to": "S2_RANGE_TRIGGER_REACHED",
      "event": "range_or_profit_trigger",
      "rule_draft": "Aguardar range em pontos ou lucro configurado para permitir eliminação entre large e small.",
      "evidence": "Prompt humano cita range 500 pts e trigger por 20 pts ou 10 USD.",
      "confidence": "medium"
    },
    {
      "from": "S2_RANGE_TRIGGER_REACHED",
      "to": "S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL",
      "event": "winner_eliminates_loser",
      "rule_draft": "Usar ordem large lucrativa para eliminar ordem small perdedora e abrir direcional.",
      "evidence": "Prompt humano descreve buy 0.04 eliminando sell 0.03 e depois buy 0.02.",
      "confidence": "medium"
    },
    {
      "from": "S3_PARTIAL_ELIMINATION_AND_DIRECTIONAL",
      "to": "S4_RETURN_STOP_OR_RECOVERY",
      "event": "price_returns_against_directional",
      "rule_draft": "Usar lucro da ordem remanescente para fechar a direcional com resultado próximo de zero ou threshold configurado.",
      "evidence": "Prompt humano cita lucro da 0.03 + stop da 0.02 próximo de 0 ou -8 USD.",
      "confidence": "medium"
    },
    {
      "from": "S4_RETURN_STOP_OR_RECOVERY",
      "to": "S5_NEXT_CYCLE_REBUILD",
      "event": "recovery_completed",
      "rule_draft": "Abrir/reconstruir novo hedge, possivelmente com incremento de lote, e continuar ciclo.",
      "evidence": "Prompt humano cita novo hedge 0.05 e continuidade da lógica.",
      "confidence": "medium"
    }
  ],
  "entities": [
    {
      "name": "small_hedge",
      "role": "ordem/lote menor usado como parte do travamento inicial ou base de neutralização",
      "evidence": "Prompt humano menciona lote 0.03; códigos progressivos usam HedgeSmallLot quando presente.",
      "confidence": "medium"
    },
    {
      "name": "large_hedge",
      "role": "ordem/lote maior usado para eliminar a ordem menor perdedora quando houver lucro suficiente",
      "evidence": "Prompt humano menciona lote 0.04; códigos progressivos usam HedgeLargeLot quando presente.",
      "confidence": "medium"
    },
    {
      "name": "directional_order",
      "role": "ordem direcional aberta após eliminação parcial para criar exposição líquida controlada",
      "evidence": "Prompt humano menciona lote 0.02; várias versões têm pista de directional.",
      "confidence": "medium"
    },
    {
      "name": "recovery_or_stop_pair",
      "role": "combinação de lucro da ordem remanescente com stop/prejuízo da direcional para tentar fechar perto de zero",
      "evidence": "Prompt humano cita retorno do preço e diferença próxima de -8USD.",
      "confidence": "medium"
    },
    {
      "name": "next_cycle_hedge",
      "role": "novo par de hedge com incremento de lote após uma eliminação/recovery",
      "evidence": "Prompt humano cita compra/venda 0.05 após incremento 0.01; versões progressivas têm pista de LotIncrease.",
      "confidence": "medium"
    }
  ],
  "thesis": {
    "summary": "Família P0 tenta transformar um hedge inicial em ciclos de eliminação, exposição direcional controlada e recovery/neutralização.",
    "confirmed_from_prompt": [
      "Família P0: intenção humana extraída de arquivos de notas/contexto.",
      "Esta leitura é determinística e deve ser validada por resolução por fontes.",
      "A estratégia parece nascer de um hedge/travamento inicial a mercado.",
      "Há pistas de dois blocos/lotes principais, especialmente 0.03 e 0.04.",
      "Há intenção de usar a ordem maior lucrativa para eliminar ordem menor perdedora.",
      "Após eliminação, há intenção de abrir uma ordem direcional.",
      "O retorno do preço contra a direcional é tratado como problema central de stop/recovery.",
      "Há pista de incremento de lote, que precisa ser avaliado por DD, margem e risco."
    ],
    "confirmed_from_code": [
      "P0_BASE: property description = \"Hedge Progressivo - Correção lotes globais não carregados + sequência garantida\"",
      "P0_BASE: detectados 19 inputs, 12 funções e eventos ['OnInit', 'OnChartEvent', 'OnTick', 'OnDeinit'].",
      "P0_V1: property description = \"Hedge P00 V1: Start BUY+SELL; Fecha lucro no range; Abre DIR a mercado; Coloca hedges pendings no preço base com offset (LIMIT antes STOP); Resolve quando lucro base+hedge_same cobre perda DIR; Fecha DIR+opp+BASE, sobra hedge_same como novo base.\"",
      "P0_V1: detectados 28 inputs, 23 funções e eventos ['OnInit', 'OnDeinit', 'OnTimer', 'OnChartEvent', 'OnTick'].",
      "P0_V2: property description = \"Hedge Progressivo - Extra lot quando range isolating > 400 pts + directional dinâmico (diferença)\"",
      "P0_V2: detectados 21 inputs, 12 funções e eventos ['OnInit', 'OnChartEvent', 'OnTick', 'OnDeinit'].",
      "P0_V3: property description = \"Hedge Progressivo - Correção tracking/sequência após aumento de lot\"",
      "P0_V3: detectados 30 inputs, 13 funções e eventos ['OnInit', 'OnChartEvent', 'OnTick', 'OnDeinit'].",
      "P0_V4: property description = \"Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease\"",
      "P0_V4: detectados 29 inputs, 13 funções e eventos ['OnInit', 'OnChartEvent', 'OnTick', 'OnDeinit']."
    ],
    "inferred_hypotheses": [
      "A família P0 parece testar mecanismos de hedge progressivo com eliminação de ordens e controle direcional."
    ]
  }
}

## Análise estática
{
  "family_id": "P0",
  "version_id": "P0_V4",
  "source_file": "Hedge_P0_V4.mq5",
  "source_path": "estrategias\\P0\\Hedge_P0_V4.mq5",
  "generated_at_utc": "2026-05-27T19:52:03.872366+00:00",
  "line_count": 541,
  "char_count": 25569,
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
  "includes": [
    {
      "line": 11,
      "value": "<Trade\\Trade.mqh>"
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
  "functions": [
    {
      "line": 81,
      "name": "PositionExists",
      "return_type": "bool",
      "parameters": "ulong ticket",
      "is_event_function": false
    },
    {
      "line": 83,
      "name": "GetProfit",
      "return_type": "double",
      "parameters": "ulong ticket",
      "is_event_function": false
    },
    {
      "line": 88,
      "name": "GetPointsProfit",
      "return_type": "double",
      "parameters": "ulong ticket",
      "is_event_function": false
    },
    {
      "line": 96,
      "name": "IsTriggered",
      "return_type": "bool",
      "parameters": "ulong winner, ulong loser",
      "is_event_function": false
    },
    {
      "line": 110,
      "name": "OpenPosition",
      "return_type": "ulong",
      "parameters": "double lot, ENUM_POSITION_TYPE type, int mag, string base_comment = \"\"",
      "is_event_function": false
    },
    {
      "line": 166,
      "name": "ClosePosition",
      "return_type": "bool",
      "parameters": "ulong ticket",
      "is_event_function": false
    },
    {
      "line": 177,
      "name": "CountOurPositions",
      "return_type": "int",
      "parameters": "",
      "is_event_function": false
    },
    {
      "line": 188,
      "name": "AtualizarResumoNoGrafico",
      "return_type": "void",
      "parameters": "",
      "is_event_function": false
    },
    {
      "line": 218,
      "name": "CloseAllOurPositionsAndReset",
      "return_type": "void",
      "parameters": "",
      "is_event_function": false
    },
    {
      "line": 261,
      "name": "OnInit",
      "return_type": "int",
      "parameters": "",
      "is_event_function": true
    },
    {
      "line": 363,
      "name": "OnChartEvent",
      "return_type": "void",
      "parameters": "const int id, const long& lparam, const double& dparam, const string& sparam",
      "is_event_function": true
    },
    {
      "line": 374,
      "name": "OnTick",
      "return_type": "void",
      "parameters": "",
      "is_event_function": true
    },
    {
      "line": 533,
      "name": "OnDeinit",
      "return_type": "void",
      "parameters": "const int reason",
      "is_event_function": true
    }
  ],
  "event_functions": [
    "OnInit",
    "OnChartEvent",
    "OnTick",
    "OnDeinit"
  ],
  "trade_keyword_hits": {
    "CTrade": 1,
    "trade.Buy": 1,
    "trade.Sell": 1,
    "PositionSelect": 1,
    "PositionSelectByTicket": 1,
    "PositionsTotal": 4,
    "PositionClose": 1
  },
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
  "comments_sample": [
    "+------------------------------------------------------------------+",
    "|                    HedgeEA_Progressivo_v117.mq5                  |",
    "|                          xAI - Hedge Progressivo v1.17           |",
    "+------------------------------------------------------------------+",
    "--- Inputs ---",
    "Lote inicial small hedge",
    "Lote inicial large hedge",
    "Incremento normal por nível + net direcional fixed",
    "Extra se range > threshold",
    "Range em pts para extra increase",
    "Limite USD para stop (net small + directional)",
    "\"pts\" ou \"usd\"",
    "Valor do trigger (pts ou net USD)",
    "Magic base (mude para cada instância!)",
    "Sufixo único no INÍCIO dos comentários",
    "Spread max em points",
    "Ignora spread após reset ou botão",
    "Força abertura mesmo com posições",
    "RESET ao iniciar",
    "--- Resumo gráfico ---",
    "--- Botão ---",
    "--- Magics ---",
    "--- Prefixo globals ---",
    "--- Labels gráficos ---",
    "--- Globais persistentes ---",
    "--- Funções auxiliares ---",
    "+------------------------------------------------------------------+",
    "| Expert initialization                                            |",
    "+------------------------------------------------------------------+",
    "Cria labels do resumo",
    "Botão",
    "+------------------------------------------------------------------+",
    "| Chart Event                                                      |",
    "+------------------------------------------------------------------+",
    "+------------------------------------------------------------------+",
    "| Expert tick function                                             |",
    "+------------------------------------------------------------------+",
    "Trigger eliminação",
    "Calcula direcional para net 0.01",
    "Calcula direcional para net 0.01"
  ],
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
  ],
  "needs_source_resolution": true
}

## Arquivo MQL5: estrategias\P0\Hedge_P0_V4.mq5

```mql5
//+------------------------------------------------------------------+
//|                    HedgeEA_Progressivo_v117.mq5                  |
//|                          xAI - Hedge Progressivo v1.17           |
//+------------------------------------------------------------------+
#property copyright "xAI"
#property link      ""
#property version   "1.17"
#property strict
#property description "Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease"

#include <Trade\Trade.mqh>

CTrade trade;

// --- Inputs ---
input double HedgeSmallLot             = 0.03;   // Lote inicial small hedge
input double HedgeLargeLot             = 0.04;   // Lote inicial large hedge
input double LotIncrease               = 0.01;   // Incremento normal por nível + net direcional fixed
input double ExtraLotIncreaseOnRange   = 0.01;   // Extra se range > threshold
input int    RangeThresholdPts         = 400;    // Range em pts para extra increase
input double StopThresholdUSD          = -8.0;   // Limite USD para stop (net small + directional)
input string TriggerMode               = "usd";  // "pts" ou "usd"
input double TriggerValue              = 10.0;   // Valor do trigger (pts ou net USD)
input int    MagicBase                 = 12345;  // Magic base (mude para cada instância!)
input string EA_InstanceSuffix         = "p0-1"; // Sufixo único no INÍCIO dos comentários
input double MaxSpread                 = 50.0;   // Spread max em points
input bool   IgnoreSpreadOnReset       = true;   // Ignora spread após reset ou botão
input bool   ForceInitialHedge         = false;  // Força abertura mesmo com posições
input bool   ResetStateOnStart         = false;  // RESET ao iniciar

// --- Resumo gráfico ---
input color CorBuy                     = clrGreen;
input color CorSell                    = clrRed;
input color CorNet                     = clrBlueViolet;
input color CorLucro                   = clrBlue;
input int   TamanhoFonte               = 12;
input int   PosX                       = 90;
input int   PosY                       = 20;
input int   Espacamento                = 18;

// --- Botão ---
input string BotaoCloseReset           = "Close_All_Reset";
input int    BotaoPosX                 = 20;
input int    BotaoPosY                 = 20;
input int    BotaoLargura              = 140;
input int    BotaoAltura               = 30;
input color  CorBotao                  = clrRed;
input color  CorTextoBotao             = clrWhite;

// --- Magics ---
int magic_small_buy    = MagicBase + 1;
int magic_small_sell   = MagicBase + 2;
int magic_large_buy    = MagicBase + 3;
int magic_large_sell   = MagicBase + 4;
int magic_directional  = MagicBase + 5;
int magic_isolating    = MagicBase + 6;

// --- Prefixo globals ---
string GlobalPrefix = "HedgeEA_" + IntegerToString(MagicBase) + "_";

// --- Labels gráficos ---
string objNameBuy   = "Hedge_Buy_Label_"   + EA_InstanceSuffix;
string objNameSell  = "Hedge_Sell_Label_"  + EA_InstanceSuffix;
string objNameNet   = "Hedge_Net_Label_"   + EA_InstanceSuffix;
string objNameLucro = "Hedge_Lucro_Label_" + EA_InstanceSuffix;

// --- Globais persistentes ---
double EA_State             = 0.0;
double EA_Direction         = 0.0;
double EA_SmallLot          = 0.0;
double EA_LargeLot          = 0.0;
ulong  EA_SmallBuyTicket    = 0;
ulong  EA_SmallSellTicket   = 0;
ulong  EA_LargeBuyTicket    = 0;
ulong  EA_LargeSellTicket   = 0;
ulong  EA_SmallTicket       = 0;
ulong  EA_LargeTicket       = 0;
ulong  EA_DirectionalTicket = 0;

// --- Funções auxiliares ---
bool PositionExists(ulong ticket) { return PositionSelectByTicket(ticket); }

double GetProfit(ulong ticket) {
   if (!PositionExists(ticket)) return 0.0;
   return PositionGetDouble(POSITION_PROFIT);
}

double GetPointsProfit(ulong ticket) {
   if (!PositionExists(ticket)) return 0.0;
   double open = PositionGetDouble(POSITION_PRICE_OPEN);
   long type = PositionGetInteger(POSITION_TYPE);
   double curr = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   return (type == POSITION_TYPE_BUY ? (curr - open) : (open - curr)) / _Point;
}

bool IsTriggered(ulong winner, ulong loser) {
   if (winner == 0 || loser == 0) return false;
   double pl_win = GetProfit(winner);
   double pl_lose = GetProfit(loser);
   double net = pl_win + pl_lose;
   PrintFormat("IsTriggered | Winner ticket=%llu P/L=%.2f | Loser ticket=%llu P/L=%.2f | Net=%.2f >= %.2f", winner, pl_win, loser, pl_lose, net, TriggerValue);
   
   if (StringCompare(TriggerMode, "pts", false) == 0) {
      return GetPointsProfit(winner) >= TriggerValue;
   } else {
      return net >= TriggerValue;
   }
}

ulong OpenPosition(double lot, ENUM_POSITION_TYPE type, int mag, string base_comment = "") {
   string full_comment = EA_InstanceSuffix + " " + base_comment;
   if (lot <= 0.0) {
      Print("Erro: lot inválido = ", DoubleToString(lot, 2));
      return 0;
   }
   
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double spread = (ask - bid) / _Point;
   bool ignore_spread = IgnoreSpreadOnReset;
   
   if (MaxSpread > 0.0 && spread > MaxSpread && !ignore_spread) {
      PrintFormat("Spread bloqueado: %.1f > %.1f | %s | Lot: %.2f | Mag: %d", spread, MaxSpread, 
                  (type == POSITION_TYPE_BUY ? "BUY" : "SELL"), lot, mag);
      return 0;
   }
   
   double free_margin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   double margin_req = lot * SymbolInfoDouble(_Symbol, SYMBOL_MARGIN_INITIAL);
   if (free_margin < margin_req * 1.5) {
      Print("Margem insuficiente: Free=", free_margin, " Req≈", margin_req);
      return 0;
   }
   
   trade.SetExpertMagicNumber(mag);
   trade.SetDeviationInPoints(5);
   
   bool success = false;
   if (type == POSITION_TYPE_BUY) success = trade.Buy(lot, _Symbol, 0.0, 0.0, 0.0, full_comment);
   else success = trade.Sell(lot, _Symbol, 0.0, 0.0, 0.0, full_comment);
   
   if (!success) {
      PrintFormat("Falha abrir %s lot=%.2f mag=%d '%s' | Retcode=%d | %s | Spread=%.1f",
                  (type == POSITION_TYPE_BUY ? "BUY" : "SELL"), lot, mag, full_comment,
                  trade.ResultRetcode(), trade.ResultRetcodeDescription(), spread);
      return 0;
   }
   
   ulong ticket = 0;
   for (int i = PositionsTotal() - 1; i >= 0; i--) {
      ulong t = PositionGetTicket(i);
      if (PositionGetString(POSITION_SYMBOL) == _Symbol &&
          PositionGetInteger(POSITION_MAGIC) == mag &&
          PositionGetInteger(POSITION_TYPE) == type &&
          MathAbs(PositionGetDouble(POSITION_VOLUME) - lot) < 0.0001) {
         ticket = t;
         Print("Aberto OK: ticket=", ticket, " | ", full_comment, " | Spread=", spread);
         break;
      }
   }
   
   if (ticket == 0) Print("Ticket não encontrado após abertura!");
   return ticket;
}

bool ClosePosition(ulong ticket) {
   if (ticket == 0 || !PositionExists(ticket)) return true;
   trade.PositionClose(ticket, 5);
   if (trade.ResultRetcode() != TRADE_RETCODE_DONE) {
      Print("Falha fechar ", ticket, ": ", trade.ResultRetcodeDescription());
      return false;
   }
   Print("Fechado OK: ", ticket);
   return true;
}

int CountOurPositions() {
   int count = 0;
   for (int i = PositionsTotal() - 1; i >= 0; i--) {
      ulong t = PositionGetTicket(i);
      if (t == 0) continue;
      long mag = PositionGetInteger(POSITION_MAGIC);
      if (PositionGetString(POSITION_SYMBOL) == _Symbol && mag >= MagicBase && mag < MagicBase + 100) count++;
   }
   return count;
}

void AtualizarResumoNoGrafico() {
   double buyVol = 0.0, sellVol = 0.0, totalProfit = 0.0;
   for (int i = PositionsTotal() - 1; i >= 0; i--) {
      ulong t = PositionGetTicket(i);
      if (t == 0) continue;
      long mag = PositionGetInteger(POSITION_MAGIC);
      if (PositionGetString(POSITION_SYMBOL) == _Symbol && mag >= MagicBase && mag < MagicBase + 100) {
         double vol = PositionGetDouble(POSITION_VOL
```