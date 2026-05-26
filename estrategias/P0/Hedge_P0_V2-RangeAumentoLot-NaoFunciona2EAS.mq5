//+------------------------------------------------------------------+
//|                    HedgeEA_Progressivo_v111.mq5                  |
//|                          xAI - Hedge Progressivo v1.11           |
//+------------------------------------------------------------------+
#property copyright "xAI"
#property link      ""
#property version   "1.11"
#property strict
#property description "Hedge Progressivo - Extra lot quando range isolating > 400 pts + directional dinâmico (diferença)"

#include <Trade\Trade.mqh>

CTrade trade;

// --- Inputs ---
input double HedgeSmallLot      = 0.03;       // Lote inicial small hedge
input double HedgeLargeLot      = 0.04;       // Lote inicial large hedge
input double DirectionalLot     = 0.02;       // Lote direcional base (fixo fallback)
input double LotIncrease        = 0.01;       // Incremento padrão por nível
input double ExtraLotWhenFar    = 0.01;       // Extra lot se range isolating > FarRangePts
input int    FarRangePts        = 400;        // Threshold range pts para extra lot
input double StopThresholdUSD   = -8.0;       // Limite USD para stop
input string TriggerMode        = "usd";      // "pts" ou "usd"
input double TriggerValue       = 10.0;       // Valor do trigger
input int    MagicBase          = 12345;      // Magic base
input double MaxSpread          = 50.0;       // Spread max
input bool   IgnoreSpreadOnReset= true;
input bool   ForceInitialHedge  = false;
input bool   ResetStateOnStart  = false;

// --- Botão ---
input string BotaoCloseReset    = "Close_All_Reset";
input int    BotaoPosX          = 30;
input int    BotaoPosY          = 30;
input int    BotaoLargura       = 160;
input int    BotaoAltura        = 40;
input color  CorBotao           = clrRed;
input color  CorTextoBotao      = clrWhite;

// --- Magics ---
int magic_small_buy    = MagicBase + 1;
int magic_small_sell   = MagicBase + 2;
int magic_large_buy    = MagicBase + 3;
int magic_large_sell   = MagicBase + 4;
int magic_directional  = MagicBase + 5;
int magic_isolating    = MagicBase + 6;

// --- Globais ---
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

// Funções auxiliares
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
   if (StringCompare(TriggerMode, "pts", false) == 0) return GetPointsProfit(winner) >= TriggerValue;
   return net >= TriggerValue;
}

ulong OpenPosition(double lot, ENUM_POSITION_TYPE type, int mag, string comment = "") {
   if (lot <= 0.0) {
      Print("Erro: lot inválido = ", DoubleToString(lot, 2));
      return 0;
   }
   double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / _Point;
   bool ignore = IgnoreSpreadOnReset;
   if (MaxSpread > 0.0 && spread > MaxSpread && !ignore) {
      PrintFormat("Spread bloqueado: %.1f > %.1f", spread, MaxSpread);
      return 0;
   }
   trade.SetExpertMagicNumber(mag);
   trade.SetDeviationInPoints(5);
   bool success = (type == POSITION_TYPE_BUY) ? trade.Buy(lot, _Symbol, 0.0, 0.0, 0.0, comment) : trade.Sell(lot, _Symbol, 0.0, 0.0, 0.0, comment);
   if (!success) {
      PrintFormat("Falha abrir %s lot=%.2f mag=%d '%s' Retcode=%d %s", (type == POSITION_TYPE_BUY?"BUY":"SELL"), lot, mag, comment, trade.ResultRetcode(), trade.ResultRetcodeDescription());
      return 0;
   }
   for (int i = PositionsTotal()-1; i>=0; i--) {
      ulong t = PositionGetTicket(i);
      if (PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == mag && PositionGetInteger(POSITION_TYPE) == type && MathAbs(PositionGetDouble(POSITION_VOLUME)-lot)<0.0001) {
         Print("Aberto OK: ticket=", t, " | ", comment);
         return t;
      }
   }
   return 0;
}

bool ClosePosition(ulong ticket) {
   if (ticket == 0 || !PositionExists(ticket)) return true;
   trade.PositionClose(ticket, 5);
   return trade.ResultRetcode() == TRADE_RETCODE_DONE;
}

int CountOurPositions() {
   int c = 0;
   for (int i=PositionsTotal()-1; i>=0; i--) {
      ulong t = PositionGetTicket(i);
      if (t>0 && PositionGetString(POSITION_SYMBOL)==_Symbol) {
         long m = PositionGetInteger(POSITION_MAGIC);
         if (m >= MagicBase && m < MagicBase+100) c++;
      }
   }
   return c;
}

void CloseAllOurPositionsAndReset() {
   Print("=== Botão Close All & Reset ===");
   for (int i=PositionsTotal()-1; i>=0; i--) {
      ulong t = PositionGetTicket(i);
      if (t>0) {
         long m = PositionGetInteger(POSITION_MAGIC);
         if (m >= MagicBase && m < MagicBase+100) ClosePosition(t);
      }
   }
   EA_State = 0.0; EA_Direction = 0.0;
   EA_SmallLot = HedgeSmallLot; EA_LargeLot = HedgeLargeLot;
   EA_SmallBuyTicket = EA_SmallSellTicket = EA_LargeBuyTicket = EA_LargeSellTicket = EA_SmallTicket = EA_LargeTicket = EA_DirectionalTicket = 0;
   GlobalVariableDel("EA_State"); GlobalVariableDel("EA_Direction");
   GlobalVariableDel("EA_SmallLot"); GlobalVariableDel("EA_LargeLot");
   GlobalVariableDel("EA_SmallBuyTicket"); GlobalVariableDel("EA_SmallSellTicket");
   GlobalVariableDel("EA_LargeBuyTicket"); GlobalVariableDel("EA_LargeSellTicket");
   GlobalVariableDel("EA_SmallTicket"); GlobalVariableDel("EA_LargeTicket"); GlobalVariableDel("EA_DirectionalTicket");
   Print("Reset completo.");
   ChartRedraw();
}

//+------------------------------------------------------------------+
int OnInit() {
   Print("=== v1.11 iniciado ===");
   if (ResetStateOnStart) CloseAllOurPositionsAndReset();
   else if (GlobalVariableCheck("EA_State")) {
      EA_State = GlobalVariableGet("EA_State");
      EA_Direction = GlobalVariableGet("EA_Direction");
      EA_SmallLot = GlobalVariableGet("EA_SmallLot");
      EA_LargeLot = GlobalVariableGet("EA_LargeLot");
      EA_SmallBuyTicket = (ulong)GlobalVariableGet("EA_SmallBuyTicket");
      EA_SmallSellTicket = (ulong)GlobalVariableGet("EA_SmallSellTicket");
      EA_LargeBuyTicket = (ulong)GlobalVariableGet("EA_LargeBuyTicket");
      EA_LargeSellTicket = (ulong)GlobalVariableGet("EA_LargeSellTicket");
      EA_SmallTicket = (ulong)GlobalVariableGet("EA_SmallTicket");
      EA_LargeTicket = (ulong)GlobalVariableGet("EA_LargeTicket");
      EA_DirectionalTicket = (ulong)GlobalVariableGet("EA_DirectionalTicket");
      if (EA_SmallLot <= 0.0) EA_SmallLot = HedgeSmallLot;
      if (EA_LargeLot <= 0.0) EA_LargeLot = HedgeLargeLot;
   } else {
      EA_State = 0.0; EA_Direction = 0.0;
      EA_SmallLot = HedgeSmallLot; EA_LargeLot = HedgeLargeLot;
      GlobalVariableSet("EA_State", EA_State); GlobalVariableSet("EA_Direction", EA_Direction);
      GlobalVariableSet("EA_SmallLot", EA_SmallLot); GlobalVariableSet("EA_LargeLot", EA_LargeLot);
   }
   ObjectCreate(ChartID(), BotaoCloseReset, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_XDISTANCE, BotaoPosX);
   ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_YDISTANCE, BotaoPosY);
   ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_XSIZE, BotaoLargura);
   ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_YSIZE, BotaoAltura);
   ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_BGCOLOR, CorBotao);
   ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_COLOR, CorTextoBotao);
   ObjectSetString(ChartID(), BotaoCloseReset, OBJPROP_TEXT, "Close All & Reset");
   ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_STATE, false);
   ChartRedraw();
   return(INIT_SUCCEEDED);
}

void OnChartEvent(const int id, const long& lparam, const double& dparam, const string& sparam) {
   if (id == CHARTEVENT_OBJECT_CLICK && sparam == BotaoCloseReset) {
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_STATE, false);
      ChartRedraw();
      CloseAllOurPositionsAndReset();
   }
}

void OnTick() {
   EA_State = GlobalVariableGet("EA_State");
   EA_Direction = GlobalVariableGet("EA_Direction");
   EA_SmallLot = GlobalVariableGet("EA_SmallLot");
   EA_LargeLot = GlobalVariableGet("EA_LargeLot");
   EA_SmallBuyTicket = (ulong)GlobalVariableGet("EA_SmallBuyTicket");
   EA_SmallSellTicket = (ulong)GlobalVariableGet("EA_SmallSellTicket");
   EA_LargeBuyTicket = (ulong)GlobalVariableGet("EA_LargeBuyTicket");
   EA_LargeSellTicket = (ulong)GlobalVariableGet("EA_LargeSellTicket");
   EA_SmallTicket = (ulong)GlobalVariableGet("EA_SmallTicket");
   EA_LargeTicket = (ulong)GlobalVariableGet("EA_LargeTicket");
   EA_DirectionalTicket = (ulong)GlobalVariableGet("EA_DirectionalTicket");

   if (EA_SmallLot <= 0.0) EA_SmallLot = HedgeSmallLot;
   if (EA_LargeLot <= 0.0) EA_LargeLot = HedgeLargeLot;

   int our_pos = CountOurPositions();
   double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / _Point;
   PrintFormat("OnTick | State=%.0f | Pos=%d | SmallLot=%.2f | LargeLot=%.2f | Spread=%.1f", EA_State, our_pos, EA_SmallLot, EA_LargeLot, spread);

   if (EA_State == 0.0 && (our_pos == 0 || ForceInitialHedge)) {
      Print("=== Iniciando hedges ===");
      ulong sb = OpenPosition(EA_SmallLot, POSITION_TYPE_BUY, magic_small_buy, "Small Buy");
      ulong ss = OpenPosition(EA_SmallLot, POSITION_TYPE_SELL, magic_small_sell, "Small Sell");
      ulong lb = OpenPosition(EA_LargeLot, POSITION_TYPE_BUY, magic_large_buy, "Large Buy");
      ulong ls = OpenPosition(EA_LargeLot, POSITION_TYPE_SELL, magic_large_sell, "Large Sell");
      if (sb>0 && ss>0 && lb>0 && ls>0) {
         GlobalVariableSet("EA_SmallBuyTicket", sb); GlobalVariableSet("EA_SmallSellTicket", ss);
         GlobalVariableSet("EA_LargeBuyTicket", lb); GlobalVariableSet("EA_LargeSellTicket", ls);
         Print("Hedges iniciais OK");
      }
   }

   if (EA_State == 0.0) {
      if (IsTriggered(EA_LargeBuyTicket, EA_SmallSellTicket)) {
         if (ClosePosition(EA_LargeBuyTicket) && ClosePosition(EA_SmallSellTicket)) {
            GlobalVariableSet("EA_Direction", 1.0);
            GlobalVariableSet("EA_SmallTicket", EA_SmallBuyTicket);
            GlobalVariableSet("EA_LargeTicket", EA_LargeSellTicket);
            ulong dir = OpenPosition(DirectionalLot, POSITION_TYPE_BUY, magic_directional, "Directional Buy");
            if (dir > 0) {
               GlobalVariableSet("EA_DirectionalTicket", dir);
               GlobalVariableSet("EA_State", 1.0);
            }
         }
      } else if (IsTriggered(EA_LargeSellTicket, EA_SmallBuyTicket)) {
         if (ClosePosition(EA_LargeSellTicket) && ClosePosition(EA_SmallBuyTicket)) {
            GlobalVariableSet("EA_Direction", -1.0);
            GlobalVariableSet("EA_SmallTicket", EA_SmallSellTicket);
            GlobalVariableSet("EA_LargeTicket", EA_LargeBuyTicket);
            ulong dir = OpenPosition(DirectionalLot, POSITION_TYPE_SELL, magic_directional, "Directional Sell");
            if (dir > 0) {
               GlobalVariableSet("EA_DirectionalTicket", dir);
               GlobalVariableSet("EA_State", 1.0);
            }
         }
      }
   }

   if (EA_State == 1.0) {
      double pl_small = GetProfit(EA_SmallTicket);
      double pl_dir = GetProfit(EA_DirectionalTicket);
      double net = pl_small + pl_dir;
      if (net <= StopThresholdUSD) {
         if (ClosePosition(EA_SmallTicket) && ClosePosition(EA_DirectionalTicket)) {
            ulong isolating = 0;
            ENUM_POSITION_TYPE iso_type = (EA_Direction == 1.0) ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
            isolating = OpenPosition(EA_LargeLot, iso_type, magic_isolating, (EA_Direction == 1.0 ? "Isolating Buy" : "Isolating Sell"));
            if (isolating > 0) {
               double large_open = 0.0, iso_open = 0.0;
               if (PositionSelectByTicket(EA_LargeTicket)) large_open = PositionGetDouble(POSITION_PRICE_OPEN);
               if (PositionSelectByTicket(isolating)) iso_open = PositionGetDouble(POSITION_PRICE_OPEN);
               double range_pts = MathAbs(large_open - iso_open) / _Point;
               double extra = (range_pts > FarRangePts) ? ExtraLotWhenFar : 0.0;
               double new_large = EA_LargeLot + LotIncrease + extra;
               double dir_lot = new_large - EA_LargeLot; // dinâmico
               GlobalVariableSet("EA_SmallLot", EA_LargeLot);
               GlobalVariableSet("EA_LargeLot", new_large);
               ulong new_lb = OpenPosition(new_large, POSITION_TYPE_BUY, magic_large_buy, "New Large Buy");
               ulong new_ls = OpenPosition(new_large, POSITION_TYPE_SELL, magic_large_sell, "New Large Sell");
               if (new_lb > 0 && new_ls > 0) {
                  GlobalVariableSet("EA_LargeBuyTicket", new_lb);
                  GlobalVariableSet("EA_LargeSellTicket", new_ls);
                  if (EA_Direction == 1.0) {
                     GlobalVariableSet("EA_SmallBuyTicket", isolating);
                     GlobalVariableSet("EA_SmallSellTicket", EA_LargeTicket);
                  } else {
                     GlobalVariableSet("EA_SmallBuyTicket", EA_LargeTicket);
                     GlobalVariableSet("EA_SmallSellTicket", isolating);
                  }
                  GlobalVariableSet("EA_State", 0.0);
                  GlobalVariableSet("EA_Direction", 0.0);
                  GlobalVariableSet("EA_SmallTicket", 0);
                  GlobalVariableSet("EA_LargeTicket", 0);
                  GlobalVariableSet("EA_DirectionalTicket", 0);
                  PrintFormat("Range isolating=%.0f pts > %d → extra=%.2f | new_large=%.2f | dir_lot dinâmico=%.2f", range_pts, FarRangePts, extra, new_large, dir_lot);
               }
            }
         }
      }
   }
}

void OnDeinit(const int reason) {
   ObjectDelete(ChartID(), BotaoCloseReset);
}