TASK: Convert MQL5 EA blocks into one Python StrategyModel.

Return ONLY valid JSON. No markdown. No explanation outside JSON.

JSON schema:
{
  "translation_summary": ["short item"],
  "source_unresolved": ["short item"],
  "assumptions": ["short item"],
  "python_code": "complete Python code as a single string"
}

python_code must:
- define class StrategyModel
- implement __init__, on_start, on_bar, get_positions, get_events, get_metrics_snapshot
- use only standard Python
- not use files, network, subprocess, pandas, numpy
- store positions as dicts with side, lot, open_price, tag
- store events as dicts with event_type, price, bar_index, details
- preserve MQL5 logic as much as possible
- mark unclear rules as TODO_SOURCE_UNRESOLVED

Context:
# Block Translation Context P0/P0_V4

## Spec compacto
{
  "family_id": "P0",
  "version_id": "P0_V4",
  "source_file": "Hedge_P0_V4.mq5",
  "description": "\"Hedge Progressivo - Globals para lotes cumulativos + directional = large - small + LotIncrease\"",
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
  }
}

## Inputs extraídos do MQL5
[
  {
    "type": "double",
    "name": "HedgeSmallLot",
    "default": "0.03",
    "comment": ""
  },
  {
    "type": "double",
    "name": "HedgeLargeLot",
    "default": "0.04",
    "comment": ""
  },
  {
    "type": "double",
    "name": "LotIncrease",
    "default": "0.01",
    "comment": ""
  },
  {
    "type": "double",
    "name": "ExtraLotIncreaseOnRange",
    "default": "0.01",
    "comment": ""
  },
  {
    "type": "int",
    "name": "RangeThresholdPts",
    "default": "400",
    "comment": ""
  },
  {
    "type": "double",
    "name": "StopThresholdUSD",
    "default": "-8.0",
    "comment": ""
  },
  {
    "type": "string",
    "name": "TriggerMode",
    "default": "\"usd\"",
    "comment": ""
  },
  {
    "type": "double",
    "name": "TriggerValue",
    "default": "10.0",
    "comment": ""
  },
  {
    "type": "int",
    "name": "MagicBase",
    "default": "12345",
    "comment": ""
  },
  {
    "type": "string",
    "name": "EA_InstanceSuffix",
    "default": "\"p0-1\"",
    "comment": ""
  },
  {
    "type": "double",
    "name": "MaxSpread",
    "default": "50.0",
    "comment": ""
  },
  {
    "type": "bool",
    "name": "IgnoreSpreadOnReset",
    "default": "true",
    "comment": ""
  },
  {
    "type": "bool",
    "name": "ForceInitialHedge",
    "default": "false",
    "comment": ""
  },
  {
    "type": "bool",
    "name": "ResetStateOnStart",
    "default": "false",
    "comment": ""
  },
  {
    "type": "color",
    "name": "CorBuy",
    "default": "clrGreen",
    "comment": ""
  },
  {
    "type": "color",
    "name": "CorSell",
    "default": "clrRed",
    "comment": ""
  },
  {
    "type": "color",
    "name": "CorNet",
    "default": "clrBlueViolet",
    "comment": ""
  },
  {
    "type": "color",
    "name": "CorLucro",
    "default": "clrBlue",
    "comment": ""
  },
  {
    "type": "int",
    "name": "TamanhoFonte",
    "default": "12",
    "comment": ""
  },
  {
    "type": "int",
    "name": "PosX",
    "default": "90",
    "comment": ""
  },
  {
    "type": "int",
    "name": "PosY",
    "default": "20",
    "comment": ""
  },
  {
    "type": "int",
    "name": "Espacamento",
    "default": "18",
    "comment": ""
  },
  {
    "type": "string",
    "name": "BotaoCloseReset",
    "default": "\"Close_All_Reset\"",
    "comment": ""
  },
  {
    "type": "int",
    "name": "BotaoPosX",
    "default": "20",
    "comment": ""
  },
  {
    "type": "int",
    "name": "BotaoPosY",
    "default": "20",
    "comment": ""
  },
  {
    "type": "int",
    "name": "BotaoLargura",
    "default": "140",
    "comment": ""
  },
  {
    "type": "int",
    "name": "BotaoAltura",
    "default": "30",
    "comment": ""
  },
  {
    "type": "color",
    "name": "CorBotao",
    "default": "clrRed",
    "comment": ""
  },
  {
    "type": "color",
    "name": "CorTextoBotao",
    "default": "clrWhite",
    "comment": ""
  }
]

## Análise estática resumida
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


## Blocos MQL5 selecionados
```mql5


// === FUNCTION OnInit ===

int OnInit() {
   Print("=== HedgeEA_Progressivo v1.16 iniciado ===");
   Print("MagicBase=", MagicBase, " | InstanceSuffix=", EA_InstanceSuffix, " | GlobalPrefix=", GlobalPrefix);
   Print("Inputs atuais: SmallLot=", DoubleToString(HedgeSmallLot, 2), " | LargeLot=", DoubleToString(HedgeLargeLot, 2));
   
   GlobalPrefix = "HedgeEA_" + IntegerToString(MagicBase) + "_";
   
   if (GlobalVariableCheck(GlobalPrefix + "State")) {
      EA_State             = GlobalVariableGet(GlobalPrefix + "State");
      EA_Direction         = GlobalVariableGet(GlobalPrefix + "Direction");
      EA_SmallLot          = GlobalVariableGet(GlobalPrefix + "SmallLot");
      EA_LargeLot          = GlobalVariableGet(GlobalPrefix + "LargeLot");
      EA_SmallBuyTicket    = (ulong)GlobalVariableGet(GlobalPrefix + "SmallBuyTicket");
      EA_SmallSellTicket   = (ulong)GlobalVariableGet(GlobalPrefix + "SmallSellTicket");
      EA_LargeBuyTicket    = (ulong)GlobalVariableGet(GlobalPrefix + "LargeBuyTicket");
      EA_LargeSellTicket   = (ulong)GlobalVariableGet(GlobalPrefix + "LargeSellTicket");
      EA_SmallTicket       = (ulong)GlobalVariableGet(GlobalPrefix + "SmallTicket");
      EA_LargeTicket       = (ulong)GlobalVariableGet(GlobalPrefix + "LargeTicket");
      EA_DirectionalTicket = (ulong)GlobalVariableGet(GlobalPrefix + "DirectionalTicket");
      
      if (EA_SmallLot <= 0.0) EA_SmallLot = HedgeSmallLot;
      if (EA_LargeLot <= 0.0) EA_LargeLot = HedgeLargeLot;
      
      Print("Estado restaurado | State=", EA_State, " | SmallLot=", EA_SmallLot, " | LargeLot=", EA_LargeLot, " | Posições=", CountOurPositions());
   } else {
      Print("Primeira execução - criando globals zeradas.");
      EA_State = 0.0;
      EA_Direction = 0.0;
      EA_SmallLot = HedgeSmallLot;
      EA_LargeLot = HedgeLargeLot;
      GlobalVariableSet(GlobalPrefix + "State", EA_State);
      GlobalVariableSet(GlobalPrefix + "Direction", EA_Direction);
      GlobalVariableSet(GlobalPrefix + "SmallLot", EA_SmallLot);
      GlobalVariableSet(GlobalPrefix + "LargeLot", EA_LargeLot);
   }
   
   if (ResetStateOnStart) {
      CloseAllOurPositionsAndReset();
   }
   
   // Cria labels do resumo
   if (!ObjectCreate(ChartID(), objNameBuy,   OBJ_LABEL, 0, 0, 0)) Print("Falha criar label Buy");
   if (!ObjectCreate(ChartID(), objNameSell,  OBJ_LABEL, 0, 0, 0)) Print("Falha criar label Sell");
   if (!ObjectCreate(ChartID(), objNameNet,   OBJ_LABEL, 0, 0, 0)) Print("Falha criar label Net");
   if (!ObjectCreate(ChartID(), objNameLucro, OBJ_LABEL, 0, 0, 0)) Print("Falha criar label Lucro");
   
   ObjectSetInteger(ChartID(), objNameBuy,   OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(ChartID(), objNameSell,  OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(ChartID(), objNameNet,   OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(ChartID(), objNameLucro, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   
   ObjectSetInteger(ChartID(), objNameBuy,   OBJPROP_XDISTANCE, PosX);
   ObjectSetInteger(ChartID(), objNameBuy,   OBJPROP_YDISTANCE, PosY);
   ObjectSetInteger(ChartID(), objNameSell,  OBJPROP_XDISTANCE, PosX);
   ObjectSetInteger(ChartID(), objNameSell,  OBJPROP_YDISTANCE, PosY + Espacamento);
   ObjectSetInteger(ChartID(), objNameNet,   OBJPROP_XDISTANCE, PosX);
   ObjectSetInteger(ChartID(), objNameNet,   OBJPROP_YDISTANCE, PosY + Espacamento * 2);
   ObjectSetInteger(ChartID(), objNameLucro, OBJPROP_XDISTANCE, PosX);
   ObjectSetInteger(ChartID(), objNameLucro, OBJPROP_YDISTANCE, PosY + Espacamento * 3);
   
   ObjectSetInteger(ChartID(), objNameBuy,   OBJPROP_FONTSIZE, TamanhoFonte);
   ObjectSetInteger(ChartID(), objNameSell,  OBJPROP_FONTSIZE, TamanhoFonte);
   ObjectSetInteger(ChartID(), objNameNet,   OBJPROP_FONTSIZE, TamanhoFonte);
   ObjectSetInteger(ChartID(), objNameLucro, OBJPROP_FONTSIZE, TamanhoFonte);
   
   ObjectSetString(ChartID(), objNameBuy,   OBJPROP_FONT, "Arial Bold");
   ObjectSetString(ChartID(), objNameSell,  OBJPROP_FONT, "Arial Bold");
   ObjectSetString(ChartID(), objNameNet,   OBJPROP_FONT, "Arial Bold");
   ObjectSetString(ChartID(), objNameLucro, OBJPROP_FONT, "Arial Bold");
   
   ObjectSetInteger(ChartID(), objNameBuy,   OBJPROP_COLOR, CorBuy);
   ObjectSetInteger(ChartID(), objNameSell,  OBJPROP_COLOR, CorSell);
   ObjectSetInteger(ChartID(), objNameNet,   OBJPROP_COLOR, CorNet);
   ObjectSetInteger(ChartID(), objNameLucro, OBJPROP_COLOR, CorLucro);
   
   // Botão
   if (!ObjectCreate(ChartID(), BotaoCloseReset, OBJ_BUTTON, 0, 0, 0)) {
      Print("Falha criar botão! Erro=", GetLastError());
   } else {
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_XDISTANCE, BotaoPosX);
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_YDISTANCE, BotaoPosY);
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_XSIZE, BotaoLargura);
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_YSIZE, BotaoAltura);
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_BGCOLOR, CorBotao);
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_COLOR, CorTextoBotao);
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_FONTSIZE, 11);
      ObjectSetString(ChartID(), BotaoCloseReset, OBJPROP_TEXT, "Close All & Reset");
      ObjectSetString(ChartID(), BotaoCloseReset, OBJPROP_FONT, "Arial Bold");
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_STATE, false);
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_HIDDEN, false);
      Print("Botão criado OK.");
   }
   
   AtualizarResumoNoGrafico();
   ChartRedraw();
   return(INIT_SUCCEEDED);
}

// === FUNCTION OnDeinit ===

void OnDeinit(const int reason) {
   ObjectDelete(ChartID(), objNameBuy);
   ObjectDelete(ChartID(), objNameSell);
   ObjectDelete(ChartID(), objNameNet);
   ObjectDelete(ChartID(), objNameLucro);
   ObjectDelete(ChartID(), BotaoCloseReset);
   ChartRedraw();
   Print("EA finalizado. Motivo: ", reason);
}

// === FUNCTION OnChartEvent ===

void OnChartEvent(const int id, const long& lparam, const double& dparam, const string& sparam) {
   if (id == CHARTEVENT_OBJECT_CLICK && sparam == BotaoCloseReset) {
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_STATE, false);
      ChartRedraw();
      CloseAllOurPositionsAndReset();
   }
}

// === FUNCTION ClosePosition ===


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

// === FUNCTION CountOurPositions ===


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

// === FUNCTION GetPointsProfit ===


double GetPointsProfit(ulong ticket) {
   if (!PositionExists(ticket)) return 0.0;
   double open = PositionGetDouble(POSITION_PRICE_OPEN);
   long type = PositionGetInteger(POSITION_TYPE);
   double curr = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   return (type == POSITION_TYPE_BUY ? (curr - open) : (open - curr)) / _Point;
}

// === FUNCTION GetProfit ===


double GetProfit(ulong ticket) {
   if (!PositionExists(ticket)) return 0.0;
   return PositionGetDouble(POSITION_PROFIT);
}

// === FUNCTION PositionExists ===

bool PositionExists(ulong ticket) { return PositionSelectByTicket(ticket); }
```