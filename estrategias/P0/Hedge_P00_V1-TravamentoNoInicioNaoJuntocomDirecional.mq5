//+------------------------------------------------------------------+
//| Hedge_P00_V1-TravamentoNoInicioNaoJuntocomDirecional.mq5         |
//| Diego + Grok                                                     |
//| Travamento inicial com pendings no preço base (LIMIT antes STOP) |
//+------------------------------------------------------------------+
#property strict
#property description "Hedge P00 V1: Start BUY+SELL; Fecha lucro no range; Abre DIR a mercado; Coloca hedges pendings no preço base com offset (LIMIT antes STOP); Resolve quando lucro base+hedge_same cobre perda DIR; Fecha DIR+opp+BASE, sobra hedge_same como novo base."

#include <Trade/Trade.mqh>
CTrade trade;

//---------------------- Inputs
input ulong MagicNumber     = 20260206;
input string CommentText    = "P2_A";
input bool   AutoStart      = true;
input double StartLot       = 0.02;
input int    RangePts       = 300;
input double StepLot        = 0.01;
input double HedgeExtraLot  = 0.01;
input int    DeviationPts   = 30;
input int    HedgeOffsetPts = 30;
input double MinLot         = 0.01;
input int    CooldownMs     = 800;
input int    TimerMs        = 1200;
input int    ReturnTolPts   = 5;

// UI Config
input color  CorBuy         = clrLime;
input color  CorSell        = clrTomato;
input color  CorNet         = clrDeepSkyBlue;
input color  CorProfit      = clrDodgerBlue;
input int    FonteUI        = 12;
input int    PosX_UI        = 90;
input int    PosY_UI        = 20;
input int    Esp_UI         = 18;

// Botão
input string BotaoCloseAll  = "Close_All_EA";
input int    BotaoPosX      = 20;
input int    BotaoPosY      = 20;
input int    BotaoW         = 120;
input int    BotaoH         = 30;
input color  CorBotao       = clrRed;
input color  CorTxtBotao    = clrWhite;

//---------------------- State
long   g_lastFireMs   = 0;
double g_startPrice   = 0.0;
bool   g_cycleActive  = false;
double g_basePrice    = 0.0;
int    g_moveDir      = 0;
ulong  g_baseTicket   = 0;
int    g_cycleId      = 1;

// UI Labels
string objBuy    = "EA_Buy_Label";
string objSell   = "EA_Sell_Label";
string objNet    = "EA_Net_Label";
string objProfit = "EA_Profit_Label";
string objCycle  = "EA_Cycle_Label";

//+------------------------------------------------------------------+
//| Helpers                                                          |
//+------------------------------------------------------------------+
double NormalizeLot(double lot)
{
   if(lot <= 0) return 0.0;
   double step   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minlot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxlot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   lot = step * MathRound(lot / step);
   lot = MathMax(minlot, MathMin(maxlot, lot));
   return lot;
}

bool IsTradeAllowedNow()
{
   if(!TerminalInfoInteger(TERMINAL_CONNECTED)) return false;
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))       return false;
   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) return false;
   return true;
}

bool IsMyPosByTicket(ulong t)
{
   if(t == 0) return false;
   if(!PositionSelectByTicket(t)) return false;
   if(PositionGetString(POSITION_SYMBOL) != _Symbol) return false;
   if((ulong)PositionGetInteger(POSITION_MAGIC) != MagicNumber) return false;
   return true;
}

bool IsMyOrderByTicket(ulong t)
{
   if(t == 0) return false;
   if(!OrderSelect(t)) return false;
   if(OrderGetString(ORDER_SYMBOL) != _Symbol) return false;
   if((ulong)OrderGetInteger(ORDER_MAGIC) != MagicNumber) return false;
   return true;
}

int MyPositionsCount()
{
   int c = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(IsMyPosByTicket(t)) c++;
   }
   return c;
}

string CycleTag() { return StringFormat("_C%03d", g_cycleId); }

string Cmt(string base) { return CommentText + "_" + base + CycleTag(); }

string Prefix(string base) { return CommentText + "_" + base; }

ulong FindTicketByExactComment(const string exact_comment) // sem & !!!
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(!IsMyPosByTicket(t)) continue;
      if(!PositionSelectByTicket(t)) continue;
      string c = PositionGetString(POSITION_COMMENT);
      if(c == exact_comment) return t;
   }
   return 0;
}

void PrintState(string msg)
{
   Print("[Hedge_P00_V1] ", msg,
         " | cycleId=", g_cycleId,
         " | active=", (g_cycleActive ? "Y" : "N"),
         " | dir=", (g_moveDir > 0 ? "UP" : (g_moveDir < 0 ? "DOWN" : "NONE")),
         " | basePrice=", DoubleToString(g_basePrice, _Digits),
         " | baseTk=", (string)g_baseTicket,
         " | posCnt=", (string)MyPositionsCount());
}

//+------------------------------------------------------------------+
//| UI - Resumo gráfico                                              |
//+------------------------------------------------------------------+
void CreateUI()
{
   ObjectDelete(ChartID(), objBuy);
   ObjectDelete(ChartID(), objSell);
   ObjectDelete(ChartID(), objNet);
   ObjectDelete(ChartID(), objProfit);
   ObjectDelete(ChartID(), objCycle);
   ObjectDelete(ChartID(), BotaoCloseAll);

   ObjectCreate(ChartID(), objBuy, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(ChartID(), objBuy, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(ChartID(), objBuy, OBJPROP_XDISTANCE, PosX_UI);
   ObjectSetInteger(ChartID(), objBuy, OBJPROP_YDISTANCE, PosY_UI);
   ObjectSetInteger(ChartID(), objBuy, OBJPROP_FONTSIZE, FonteUI);
   ObjectSetString(ChartID(), objBuy, OBJPROP_FONT, "Arial Bold");
   ObjectSetInteger(ChartID(), objBuy, OBJPROP_COLOR, CorBuy);

   ObjectCreate(ChartID(), objSell, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(ChartID(), objSell, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(ChartID(), objSell, OBJPROP_XDISTANCE, PosX_UI);
   ObjectSetInteger(ChartID(), objSell, OBJPROP_YDISTANCE, PosY_UI + Esp_UI);
   ObjectSetInteger(ChartID(), objSell, OBJPROP_FONTSIZE, FonteUI);
   ObjectSetString(ChartID(), objSell, OBJPROP_FONT, "Arial Bold");
   ObjectSetInteger(ChartID(), objSell, OBJPROP_COLOR, CorSell);

   ObjectCreate(ChartID(), objNet, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(ChartID(), objNet, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(ChartID(), objNet, OBJPROP_XDISTANCE, PosX_UI);
   ObjectSetInteger(ChartID(), objNet, OBJPROP_YDISTANCE, PosY_UI + Esp_UI * 2);
   ObjectSetInteger(ChartID(), objNet, OBJPROP_FONTSIZE, FonteUI);
   ObjectSetString(ChartID(), objNet, OBJPROP_FONT, "Arial Bold");
   ObjectSetInteger(ChartID(), objNet, OBJPROP_COLOR, CorNet);

   ObjectCreate(ChartID(), objProfit, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(ChartID(), objProfit, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(ChartID(), objProfit, OBJPROP_XDISTANCE, PosX_UI);
   ObjectSetInteger(ChartID(), objProfit, OBJPROP_YDISTANCE, PosY_UI + Esp_UI * 3);
   ObjectSetInteger(ChartID(), objProfit, OBJPROP_FONTSIZE, FonteUI);
   ObjectSetString(ChartID(), objProfit, OBJPROP_FONT, "Arial Bold");
   ObjectSetInteger(ChartID(), objProfit, OBJPROP_COLOR, CorProfit);

   ObjectCreate(ChartID(), objCycle, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(ChartID(), objCycle, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(ChartID(), objCycle, OBJPROP_XDISTANCE, PosX_UI);
   ObjectSetInteger(ChartID(), objCycle, OBJPROP_YDISTANCE, PosY_UI + Esp_UI * 4);
   ObjectSetInteger(ChartID(), objCycle, OBJPROP_FONTSIZE, FonteUI);
   ObjectSetString(ChartID(), objCycle, OBJPROP_FONT, "Arial Bold");
   ObjectSetInteger(ChartID(), objCycle, OBJPROP_COLOR, clrBlueViolet);

   ObjectCreate(ChartID(), BotaoCloseAll, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(ChartID(), BotaoCloseAll, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(ChartID(), BotaoCloseAll, OBJPROP_XDISTANCE, BotaoPosX);
   ObjectSetInteger(ChartID(), BotaoCloseAll, OBJPROP_YDISTANCE, BotaoPosY);
   ObjectSetInteger(ChartID(), BotaoCloseAll, OBJPROP_XSIZE, BotaoW);
   ObjectSetInteger(ChartID(), BotaoCloseAll, OBJPROP_YSIZE, BotaoH);
   ObjectSetInteger(ChartID(), BotaoCloseAll, OBJPROP_BGCOLOR, CorBotao);
   ObjectSetInteger(ChartID(), BotaoCloseAll, OBJPROP_COLOR, CorTxtBotao);
   ObjectSetInteger(ChartID(), BotaoCloseAll, OBJPROP_FONTSIZE, 10);
   ObjectSetString(ChartID(), BotaoCloseAll, OBJPROP_TEXT, "Close All");
   ObjectSetString(ChartID(), BotaoCloseAll, OBJPROP_FONT, "Arial Bold");

   ChartRedraw();
}

void UpdateUI()
{
   double buyLots = 0.0, sellLots = 0.0, totalProfit = 0.0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(!IsMyPosByTicket(t)) continue;
      double vol = PositionGetDouble(POSITION_VOLUME);
      double profit = PositionGetDouble(POSITION_PROFIT);
      if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) buyLots += vol;
      else sellLots += vol;
      totalProfit += profit;
   }
   double net = buyLots - sellLots;

   ObjectSetString(ChartID(), objBuy,    OBJPROP_TEXT, "Buy: "   + DoubleToString(buyLots,   2));
   ObjectSetString(ChartID(), objSell,   OBJPROP_TEXT, "Sell: "  + DoubleToString(sellLots,  2));
   ObjectSetString(ChartID(), objNet,    OBJPROP_TEXT, "Net: "   + DoubleToString(net,      2));
   ObjectSetString(ChartID(), objProfit, OBJPROP_TEXT, "Profit: " + DoubleToString(totalProfit, 2) + " USD");
   string st = g_cycleActive ? "ACTIVE" : "IDLE";
   ObjectSetString(ChartID(), objCycle, OBJPROP_TEXT, StringFormat("Cycle: %03d (%s) Base: %.5f", g_cycleId, st, g_basePrice));

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Close All                                                        |
//+------------------------------------------------------------------+
void CloseAllByMagic()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0) continue;
      if(!PositionSelectByTicket(t)) continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
      trade.PositionClose(t);
      Sleep(50);
   }

   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong tk = OrderGetTicket(i);
      if(tk == 0) continue;
      if(!OrderSelect(tk)) continue;
      if((ulong)OrderGetInteger(ORDER_MAGIC) != MagicNumber) continue;
      trade.OrderDelete(tk);
      Sleep(30);
   }

   g_lastFireMs  = 0;
   g_startPrice  = 0.0;
   g_cycleActive = false;
   g_basePrice   = 0.0;
   g_moveDir     = 0;
   g_baseTicket  = 0;
   g_cycleId     = 1;
   UpdateUI();
}

//+------------------------------------------------------------------+
//| Core Logic                                                       |
//+------------------------------------------------------------------+
bool OpenStartHedge()
{
   double lot = NormalizeLot(StartLot);
   if(lot < MinLot) return false;

   if(!trade.Buy(lot, _Symbol, 0, 0, 0, Cmt("START_BUY")))
   {
      Print("❌ START BUY fail: ", trade.ResultRetcode(), " ", trade.ResultRetcodeDescription());
      return false;
   }
   Sleep(80);

   if(!trade.Sell(lot, _Symbol, 0, 0, 0, Cmt("START_SELL")))
   {
      Print("❌ START SELL fail: ", trade.ResultRetcode(), " ", trade.ResultRetcodeDescription());
      return false;
   }

   g_startPrice  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   g_cycleActive = false;
   g_baseTicket  = 0;
   g_basePrice   = 0.0;
   g_moveDir     = 0;

   PrintState("Start hedge opened");
   UpdateUI();
   return true;
}

bool TriggerFromInitial(double distPts, double bid, double ask)
{
   ulong tkBuy  = FindTicketByExactComment(Cmt("START_BUY"));
   ulong tkSell = FindTicketByExactComment(Cmt("START_SELL"));
   if(tkBuy == 0 || tkSell == 0) return false;

   if(bid >= g_startPrice + distPts)
   {
      trade.PositionClose(tkBuy);
      Sleep(80);
      if(PositionSelectByTicket(tkSell))
      {
         g_baseTicket = tkSell;
         g_basePrice  = PositionGetDouble(POSITION_PRICE_OPEN);
      }
      g_moveDir = +1;
      PrintState("Trigger UP: closed START_BUY, BASE=START_SELL");
      UpdateUI();
      return true;
   }

   if(ask <= g_startPrice - distPts)
   {
      trade.PositionClose(tkSell);
      Sleep(80);
      if(PositionSelectByTicket(tkBuy))
      {
         g_baseTicket = tkBuy;
         g_basePrice  = PositionGetDouble(POSITION_PRICE_OPEN);
      }
      g_moveDir = -1;
      PrintState("Trigger DOWN: closed START_SELL, BASE=START_BUY");
      UpdateUI();
      return true;
   }
   return false;
}

bool OpenDirAndLockFromBase(int moveDir)
{
   if(!IsMyPosByTicket(g_baseTicket))
   {
      if(MyPositionsCount() == 1)
      {
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            ulong t = PositionGetTicket(i);
            if(IsMyPosByTicket(t)) { g_baseTicket = t; break; }
         }
      }
   }

   if(!IsMyPosByTicket(g_baseTicket)) return false;

   PositionSelectByTicket(g_baseTicket);
   double baseVol  = PositionGetDouble(POSITION_VOLUME);
   double baseOpen = PositionGetDouble(POSITION_PRICE_OPEN);
   g_basePrice = baseOpen;

   double dirLot   = NormalizeLot(baseVol + StepLot);
   double hedgeLot = NormalizeLot(dirLot + HedgeExtraLot);
   if(dirLot < MinLot || hedgeLot < MinLot) return false;

   string cDirBuy  = Cmt("DIR_BUY");
   string cDirSell = Cmt("DIR_SELL");
   string cHB      = Cmt("HEDGE_BUY");
   string cHS      = Cmt("HEDGE_SELL");

   bool ok = false;
   double pt = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double offset = HedgeOffsetPts * pt / 2.0;

   double hedgeBuyPrice  = 0.0;
   double hedgeSellPrice = 0.0;
   ENUM_ORDER_TYPE typeBuy  = ORDER_TYPE_BUY_LIMIT;
   ENUM_ORDER_TYPE typeSell = ORDER_TYPE_SELL_STOP;

   if(moveDir > 0)
   {
      ok = trade.Buy(dirLot, _Symbol, 0, 0, 0, cDirBuy);
      if(!ok) { Print("❌ DIR BUY fail: ", trade.ResultRetcode(), " ", trade.ResultRetcodeDescription()); return false; }
      Sleep(80);

      hedgeBuyPrice  = NormalizeDouble(baseOpen + offset, _Digits);
      hedgeSellPrice = NormalizeDouble(baseOpen - offset, _Digits);
      typeBuy  = ORDER_TYPE_BUY_LIMIT;
      typeSell = ORDER_TYPE_SELL_STOP;
   }
   else
   {
      ok = trade.Sell(dirLot, _Symbol, 0, 0, 0, cDirSell);
      if(!ok) { Print("❌ DIR SELL fail: ", trade.ResultRetcode(), " ", trade.ResultRetcodeDescription()); return false; }
      Sleep(80);

      hedgeSellPrice = NormalizeDouble(baseOpen - offset, _Digits);
      hedgeBuyPrice  = NormalizeDouble(baseOpen + offset, _Digits);
      typeSell = ORDER_TYPE_SELL_LIMIT;
      typeBuy  = ORDER_TYPE_BUY_STOP;
   }

   // Coloca LIMIT primeiro
   if(moveDir > 0)
   {
      ok = trade.OrderOpen(_Symbol, typeBuy, hedgeLot, 0, hedgeBuyPrice, 0, 0, 0, cHB, MagicNumber);
      if(!ok) { Print("❌ HEDGE BUY pending fail: ", trade.ResultRetcode(), " ", trade.ResultRetcodeDescription()); return false; }
      Sleep(80);
      ok = trade.OrderOpen(_Symbol, typeSell, hedgeLot, 0, hedgeSellPrice, 0, 0, 0, cHS, MagicNumber);
      if(!ok) { Print("❌ HEDGE SELL pending fail: ", trade.ResultRetcode(), " ", trade.ResultRetcodeDescription()); return false; }
   }
   else
   {
      ok = trade.OrderOpen(_Symbol, typeSell, hedgeLot, 0, hedgeSellPrice, 0, 0, 0, cHS, MagicNumber);
      if(!ok) { Print("❌ HEDGE SELL pending fail: ", trade.ResultRetcode(), " ", trade.ResultRetcodeDescription()); return false; }
      Sleep(80);
      ok = trade.OrderOpen(_Symbol, typeBuy, hedgeLot, 0, hedgeBuyPrice, 0, 0, 0, cHB, MagicNumber);
      if(!ok) { Print("❌ HEDGE BUY pending fail: ", trade.ResultRetcode(), " ", trade.ResultRetcodeDescription()); return false; }
   }

   g_cycleActive = true;
   g_moveDir     = moveDir;
   PrintState("Opened DIR market + HEDGE pendings @base with offset (LIMIT before STOP)");
   UpdateUI();
   return true;
}

bool ResolveOnHedgeProfit()
{
   if(!g_cycleActive) return false;

   ulong tkDirBuy   = FindTicketByExactComment(Cmt("DIR_BUY"));
   ulong tkDirSell  = FindTicketByExactComment(Cmt("DIR_SELL"));
   ulong tkHB       = FindTicketByExactComment(Cmt("HEDGE_BUY"));
   ulong tkHS       = FindTicketByExactComment(Cmt("HEDGE_SELL"));

   ulong dirTk = (tkDirBuy != 0 ? tkDirBuy : tkDirSell);
   if(dirTk == 0) { PrintState("Resolve fail: no DIR"); return false; }

   if(tkHB == 0 || tkHS == 0) { PrintState("Hedges not activated yet"); return false; }

   if(!IsMyPosByTicket(g_baseTicket)) { PrintState("Resolve fail: base invalid"); return false; }

   if(!PositionSelectByTicket(dirTk)) { PrintState("Resolve fail: select DIR"); return false; }

   long dirType = PositionGetInteger(POSITION_TYPE);
   ulong hedgeSameTk = (dirType == POSITION_TYPE_BUY ? tkHB : tkHS);
   ulong hedgeOppTk  = (dirType == POSITION_TYPE_BUY ? tkHS : tkHB);

   // FIX: declare all variables here
   double dirProfit       = 0.0;
   double baseProfit      = 0.0;
   double hedgeSameProfit = 0.0;
   double dirVol          = 0.0;
   double baseVol         = 0.0;
   double hedgeSameVol    = 0.0;

   if(PositionSelectByTicket(dirTk))
   {
      dirProfit = PositionGetDouble(POSITION_PROFIT);
      dirVol    = PositionGetDouble(POSITION_VOLUME);
   }

   if(PositionSelectByTicket(g_baseTicket))
   {
      baseProfit = PositionGetDouble(POSITION_PROFIT);
      baseVol    = PositionGetDouble(POSITION_VOLUME);
   }

   if(PositionSelectByTicket(hedgeSameTk))
   {
      hedgeSameProfit = PositionGetDouble(POSITION_PROFIT);
      hedgeSameVol    = PositionGetDouble(POSITION_VOLUME);
   }

   double combinedProfit = baseProfit + hedgeSameProfit;
   double dirLossAbs     = (dirProfit < 0 ? -dirProfit : 0.0);

   double avgVol = (dirVol + baseVol + hedgeSameVol) / 3.0;
   if(avgVol <= 0) avgVol = 1.0;
   double tol = ReturnTolPts * SymbolInfoDouble(_Symbol, SYMBOL_POINT) * avgVol;

   if(combinedProfit >= dirLossAbs + tol)
   {
      trade.PositionClose(dirTk);      Sleep(80);
      trade.PositionClose(hedgeOppTk); Sleep(80);
      trade.PositionClose(g_baseTicket); Sleep(80);

      g_baseTicket = hedgeSameTk;
      if(PositionSelectByTicket(g_baseTicket))
         g_basePrice = PositionGetDouble(POSITION_PRICE_OPEN);
      else
         g_basePrice = 0.0;

      g_cycleActive = false;
      g_moveDir     = 0;
      g_cycleId++;

      PrintState("Resolved by profit: closed DIR + hedge_opp + BASE; new base=hedge_same");
      UpdateUI();

      // Limpa pendings sobrando
      for(int i = OrdersTotal() - 1; i >= 0; i--)
      {
         ulong tk = OrderGetTicket(i);
         if(IsMyOrderByTicket(tk)) 
         {
            trade.OrderDelete(tk);
            Sleep(30);
         }
      }
      return true;
   }

   return false;
}

bool TryTriggerFromSingleBase(double dist, double bid, double ask)
{
   if(MyPositionsCount() != 1) return false;

   if(!IsMyPosByTicket(g_baseTicket))
   {
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         ulong t = PositionGetTicket(i);
         if(IsMyPosByTicket(t)) { g_baseTicket = t; break; }
      }
   }

   if(!IsMyPosByTicket(g_baseTicket)) return false;

   PositionSelectByTicket(g_baseTicket);
   long   baseType = PositionGetInteger(POSITION_TYPE);
   double baseOpen = PositionGetDouble(POSITION_PRICE_OPEN);
   g_basePrice = baseOpen;

   if(baseType == POSITION_TYPE_BUY)
   {
      if(ask <= (baseOpen - dist))
         return OpenDirAndLockFromBase(-1);
      return false;
   }

   if(baseType == POSITION_TYPE_SELL)
   {
      if(bid >= (baseOpen + dist))
         return OpenDirAndLockFromBase(+1);
      return false;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Events                                                           |
//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber((int)MagicNumber);
   trade.SetDeviationInPoints(DeviationPts);
   CreateUI();
   UpdateUI();
   EventSetMillisecondTimer(TimerMs);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectDelete(ChartID(), objBuy);
   ObjectDelete(ChartID(), objSell);
   ObjectDelete(ChartID(), objNet);
   ObjectDelete(ChartID(), objProfit);
   ObjectDelete(ChartID(), objCycle);
   ObjectDelete(ChartID(), BotaoCloseAll);
   ChartRedraw();
}

void OnTimer()
{
   UpdateUI();
}

void OnChartEvent(const int id, const long& lparam, const double& dparam, const string& sparam)
{
   if(id == CHARTEVENT_OBJECT_CLICK && sparam == BotaoCloseAll)
   {
      ObjectSetInteger(ChartID(), BotaoCloseAll, OBJPROP_STATE, false);
      ChartRedraw();
      CloseAllByMagic();
   }
}

void OnTick()
{
   if(!IsTradeAllowedNow()) return;

   long now_ms = (long)(GetMicrosecondCount() / 1000);
   if(now_ms - g_lastFireMs < CooldownMs) return;

   double pt   = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double dist = RangePts * pt;
   double bid  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   if(AutoStart && MyPositionsCount() == 0)
   {
      if(OpenStartHedge())
         g_lastFireMs = now_ms;
      UpdateUI();
      return;
   }

   if(g_cycleActive)
   {
      if(ResolveOnHedgeProfit())
         g_lastFireMs = now_ms;
      UpdateUI();
      return;
   }

   if(MyPositionsCount() == 2 && g_startPrice > 0.0)
   {
      if(TriggerFromInitial(dist, bid, ask))
      {
         if(OpenDirAndLockFromBase(g_moveDir))
            g_lastFireMs = now_ms;
      }
      UpdateUI();
      return;
   }

   if(MyPositionsCount() == 1)
   {
      if(TryTriggerFromSingleBase(dist, bid, ask))
         g_lastFireMs = now_ms;
      UpdateUI();
      return;
   }

   UpdateUI();
}
//+------------------------------------------------------------------+