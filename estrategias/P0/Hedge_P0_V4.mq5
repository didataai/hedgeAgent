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
         double vol = PositionGetDouble(POSITION_VOLUME);
         double profit = PositionGetDouble(POSITION_PROFIT);
         if (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) buyVol += vol;
         else sellVol += vol;
         totalProfit += profit;
      }
   }
   
   double netVol = buyVol - sellVol;
   
   if (ObjectFind(ChartID(), objNameBuy) >= 0)
      ObjectSetString(ChartID(), objNameBuy, OBJPROP_TEXT, "Buy: " + DoubleToString(buyVol, 2));
   if (ObjectFind(ChartID(), objNameSell) >= 0)
      ObjectSetString(ChartID(), objNameSell, OBJPROP_TEXT, "Sell: " + DoubleToString(sellVol, 2));
   if (ObjectFind(ChartID(), objNameNet) >= 0)
      ObjectSetString(ChartID(), objNameNet, OBJPROP_TEXT, "Net: " + DoubleToString(netVol, 2));
   if (ObjectFind(ChartID(), objNameLucro) >= 0)
      ObjectSetString(ChartID(), objNameLucro, OBJPROP_TEXT, "Profit: " + DoubleToString(totalProfit, 2) + " USD");
   
   ChartRedraw();
   Print("Resumo atualizado: Buy=", buyVol, " Sell=", sellVol, " Net=", netVol, " Profit=", totalProfit);
}

void CloseAllOurPositionsAndReset() {
   Print("=== Botão acionado - Fechando tudo e resetando ===");
   
   for (int i = PositionsTotal() - 1; i >= 0; i--) {
      ulong t = PositionGetTicket(i);
      if (t > 0) {
         long mag = PositionGetInteger(POSITION_MAGIC);
         if (mag >= MagicBase && mag < MagicBase + 100) ClosePosition(t);
      }
   }
   
   EA_State = 0.0;
   EA_Direction = 0.0;
   EA_SmallLot = HedgeSmallLot;
   EA_LargeLot = HedgeLargeLot;
   EA_SmallBuyTicket = 0;
   EA_SmallSellTicket = 0;
   EA_LargeBuyTicket = 0;
   EA_LargeSellTicket = 0;
   EA_SmallTicket = 0;
   EA_LargeTicket = 0;
   EA_DirectionalTicket = 0;
   
   GlobalVariableDel(GlobalPrefix + "State");
   GlobalVariableDel(GlobalPrefix + "Direction");
   GlobalVariableDel(GlobalPrefix + "SmallLot");
   GlobalVariableDel(GlobalPrefix + "LargeLot");
   GlobalVariableDel(GlobalPrefix + "SmallBuyTicket");
   GlobalVariableDel(GlobalPrefix + "SmallSellTicket");
   GlobalVariableDel(GlobalPrefix + "LargeBuyTicket");
   GlobalVariableDel(GlobalPrefix + "LargeSellTicket");
   GlobalVariableDel(GlobalPrefix + "SmallTicket");
   GlobalVariableDel(GlobalPrefix + "LargeTicket");
   GlobalVariableDel(GlobalPrefix + "DirectionalTicket");
   
   AtualizarResumoNoGrafico();
   Print("Reset completo. Próxima tick deve abrir hedges.");
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Expert initialization                                            |
//+------------------------------------------------------------------+
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

//+------------------------------------------------------------------+
//| Chart Event                                                      |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long& lparam, const double& dparam, const string& sparam) {
   if (id == CHARTEVENT_OBJECT_CLICK && sparam == BotaoCloseReset) {
      ObjectSetInteger(ChartID(), BotaoCloseReset, OBJPROP_STATE, false);
      ChartRedraw();
      CloseAllOurPositionsAndReset();
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() {
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

   int our_pos = CountOurPositions();
   double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / _Point;
   PrintFormat("OnTick | State=%.0f | Direction=%.0f | Posições=%d | SmallLot=%.2f | LargeLot=%.2f | Spread=%.1f | Suffix=%s",
               EA_State, EA_Direction, our_pos, EA_SmallLot, EA_LargeLot, spread, EA_InstanceSuffix);

   AtualizarResumoNoGrafico();

   if (EA_State == 0.0 && (our_pos == 0 || ForceInitialHedge)) {
      Print("=== Iniciando hedges iniciais ===");
      ulong sb = OpenPosition(EA_SmallLot, POSITION_TYPE_BUY, magic_small_buy, "Small Buy");
      ulong ss = OpenPosition(EA_SmallLot, POSITION_TYPE_SELL, magic_small_sell, "Small Sell");
      ulong lb = OpenPosition(EA_LargeLot, POSITION_TYPE_BUY, magic_large_buy, "Large Buy");
      ulong ls = OpenPosition(EA_LargeLot, POSITION_TYPE_SELL, magic_large_sell, "Large Sell");
      
      if (sb > 0 && ss > 0 && lb > 0 && ls > 0) {
         GlobalVariableSet(GlobalPrefix + "SmallBuyTicket", sb);
         GlobalVariableSet(GlobalPrefix + "SmallSellTicket", ss);
         GlobalVariableSet(GlobalPrefix + "LargeBuyTicket", lb);
         GlobalVariableSet(GlobalPrefix + "LargeSellTicket", ls);
         Print("Hedges iniciais abertos OK!");
         AtualizarResumoNoGrafico();
      } else {
         Print("Falha na abertura inicial.");
      }
   }

   // Trigger eliminação
   if (EA_State == 0.0) {
      bool trigger_up = IsTriggered(EA_LargeBuyTicket, EA_SmallSellTicket);
      if (trigger_up) {
         Print("Trigger UP acionado");
         if (ClosePosition(EA_LargeBuyTicket) && ClosePosition(EA_SmallSellTicket)) {
            GlobalVariableSet(GlobalPrefix + "Direction", 1.0);
            GlobalVariableSet(GlobalPrefix + "SmallTicket", EA_SmallBuyTicket);
            GlobalVariableSet(GlobalPrefix + "LargeTicket", EA_LargeSellTicket);
            double dir_lot = EA_LargeLot - EA_SmallLot + LotIncrease;  // Calcula direcional para net 0.01
            ulong dir = OpenPosition(dir_lot, POSITION_TYPE_BUY, magic_directional, "Directional Buy");
            if (dir > 0) {
               GlobalVariableSet(GlobalPrefix + "DirectionalTicket", dir);
               GlobalVariableSet(GlobalPrefix + "State", 1.0);
               Print("UP concluído - state=1");
               AtualizarResumoNoGrafico();
            }
         }
      }

      bool trigger_down = IsTriggered(EA_LargeSellTicket, EA_SmallBuyTicket);
      if (trigger_down) {
         Print("Trigger DOWN acionado");
         if (ClosePosition(EA_LargeSellTicket) && ClosePosition(EA_SmallBuyTicket)) {
            GlobalVariableSet(GlobalPrefix + "Direction", -1.0);
            GlobalVariableSet(GlobalPrefix + "SmallTicket", EA_SmallSellTicket);
            GlobalVariableSet(GlobalPrefix + "LargeTicket", EA_LargeBuyTicket);
            double dir_lot = EA_LargeLot - EA_SmallLot + LotIncrease;  // Calcula direcional para net 0.01
            ulong dir = OpenPosition(dir_lot, POSITION_TYPE_SELL, magic_directional, "Directional Sell");
            if (dir > 0) {
               GlobalVariableSet(GlobalPrefix + "DirectionalTicket", dir);
               GlobalVariableSet(GlobalPrefix + "State", 1.0);
               Print("DOWN concluído - state=1");
               AtualizarResumoNoGrafico();
            }
         }
      }
   }

   // Stop + sequência
   if (EA_State == 1.0) {
      double pl_small = GetProfit(EA_SmallTicket);
      double pl_dir = GetProfit(EA_DirectionalTicket);
      double net = pl_small + pl_dir;
      PrintFormat("Stop check | PL small=%.2f | PL dir=%.2f | Net=%.2f <= %.2f", pl_small, pl_dir, net, StopThresholdUSD);
      
      if (net <= StopThresholdUSD) {
         Print("STOP acionado - eliminando small + directional");
         if (ClosePosition(EA_SmallTicket) && ClosePosition(EA_DirectionalTicket)) {
            AtualizarResumoNoGrafico();
            double large_open = 0.0;
            if (PositionExists(EA_LargeTicket)) {
               large_open = PositionGetDouble(POSITION_PRICE_OPEN);
            } else {
               Print("ERRO: large_ticket = ", EA_LargeTicket, " não existe!");
               return;
            }
            double current_price = (EA_Direction == 1.0) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
            double range_pts = MathAbs(current_price - large_open) / _Point;
            PrintFormat("Range calculado: %.0f pts (threshold=%d)", range_pts, RangeThresholdPts);
            
            double effective_increase = LotIncrease;
            if (range_pts > RangeThresholdPts) {
               effective_increase += ExtraLotIncreaseOnRange;
               PrintFormat("Range > %d pts → extra increase! New increase=%.2f", RangeThresholdPts, effective_increase);
            }
            
            double new_small = EA_LargeLot;
            double new_large = EA_LargeLot + effective_increase;
            
            GlobalVariableSet(GlobalPrefix + "SmallLot", new_small);
            GlobalVariableSet(GlobalPrefix + "LargeLot", new_large);
            
            PrintFormat("Atualizado: new_small=%.2f | new_large=%.2f", new_small, new_large);
            
            ulong isolating = 0;
            ENUM_POSITION_TYPE iso_type = (EA_Direction == 1.0) ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
            isolating = OpenPosition(EA_LargeLot, iso_type, magic_isolating, "Isolating");
            
            if (isolating > 0) {
               ulong new_lb = OpenPosition(new_large, POSITION_TYPE_BUY, magic_large_buy, "New Large Buy");
               ulong new_ls = OpenPosition(new_large, POSITION_TYPE_SELL, magic_large_sell, "New Large Sell");
               
               if (new_lb > 0 && new_ls > 0) {
                  GlobalVariableSet(GlobalPrefix + "LargeBuyTicket", new_lb);
                  GlobalVariableSet(GlobalPrefix + "LargeSellTicket", new_ls);
                  
                  if (EA_Direction == 1.0) {
                     GlobalVariableSet(GlobalPrefix + "SmallBuyTicket", isolating);
                     GlobalVariableSet(GlobalPrefix + "SmallSellTicket", EA_LargeTicket);
                  } else {
                     GlobalVariableSet(GlobalPrefix + "SmallBuyTicket", EA_LargeTicket);
                     GlobalVariableSet(GlobalPrefix + "SmallSellTicket", isolating);
                  }
                  
                  GlobalVariableSet(GlobalPrefix + "State", 0.0);
                  GlobalVariableSet(GlobalPrefix + "Direction", 0.0);
                  GlobalVariableSet(GlobalPrefix + "SmallTicket", 0);
                  GlobalVariableSet(GlobalPrefix + "LargeTicket", 0);
                  GlobalVariableSet(GlobalPrefix + "DirectionalTicket", 0);
                  
                  Print("Sequência completa: novo hedge aberto - state resetado para 0");
                  AtualizarResumoNoGrafico();
               } else {
                  Print("Falha ao abrir novo hedge large - sequência interrompida");
               }
            } else {
               Print("Falha ao isolar large loss - sequência interrompida");
            }
         } else {
            Print("Falha ao fechar small/directional - stop não completado");
         }
      }
   }
}

// OnDeinit
void OnDeinit(const int reason) {
   ObjectDelete(ChartID(), objNameBuy);
   ObjectDelete(ChartID(), objNameSell);
   ObjectDelete(ChartID(), objNameNet);
   ObjectDelete(ChartID(), objNameLucro);
   ObjectDelete(ChartID(), BotaoCloseReset);
   ChartRedraw();
   Print("EA finalizado. Motivo: ", reason);
}