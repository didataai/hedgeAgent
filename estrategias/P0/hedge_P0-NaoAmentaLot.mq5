//+------------------------------------------------------------------+
//|                    HedgeEA_Progressivo_v110.mq5                  |
//|                          xAI - Hedge Progressivo v1.10           |
//+------------------------------------------------------------------+
#property copyright "xAI"
#property link      ""
#property version   "1.10"
#property strict
#property description "Hedge Progressivo - Correção lotes globais não carregados + sequência garantida"

#include <Trade\Trade.mqh>

CTrade trade;

// --- Inputs ---
input double HedgeSmallLot      = 0.03;       // Lote inicial small hedge
input double HedgeLargeLot      = 0.04;       // Lote inicial large hedge
input double DirectionalLot     = 0.02;       // Lote direcional fixo
input double LotIncrease        = 0.01;       // Incremento por nível
input double StopThresholdUSD   = -8.0;       // Limite USD para stop (net small + directional)
input string TriggerMode        = "usd";      // "pts" ou "usd"
input double TriggerValue       = 10.0;       // Valor do trigger (pts ou net USD)
input int    MagicBase          = 12345;      // Magic base
input double MaxSpread          = 50.0;       // Spread max em points (0 = sem filtro)
input bool   IgnoreSpreadOnReset= true;       // Ignora spread após reset ou botão
input bool   ForceInitialHedge  = false;      // Força abertura mesmo com posições
input bool   ResetStateOnStart  = false;      // RESET ao iniciar (use 1x)

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
   
   if (StringCompare(TriggerMode, "pts", false) == 0) {
      return GetPointsProfit(winner) >= TriggerValue;
   } else {
      PrintFormat("Trigger USD check | PL win=%.2f | PL lose=%.2f | Net=%.2f >= %.2f", pl_win, pl_lose, net, TriggerValue);
      return net >= TriggerValue;
   }
}

ulong OpenPosition(double lot, ENUM_POSITION_TYPE type, int mag, string comment = "") {
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
   if (type == POSITION_TYPE_BUY) success = trade.Buy(lot, _Symbol, 0.0, 0.0, 0.0, comment);
   else success = trade.Sell(lot, _Symbol, 0.0, 0.0, 0.0, comment);
   
   if (!success) {
      PrintFormat("Falha abrir %s lot=%.2f mag=%d '%s' | Retcode=%d | %s | Spread=%.1f",
                  (type == POSITION_TYPE_BUY ? "BUY" : "SELL"), lot, mag, comment,
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
         Print("Aberto OK: ticket=", ticket, " | ", comment, " | Spread=", spread);
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
   
   GlobalVariableDel("EA_State");
   GlobalVariableDel("EA_Direction");
   GlobalVariableDel("EA_SmallLot");
   GlobalVariableDel("EA_LargeLot");
   GlobalVariableDel("EA_SmallBuyTicket");
   GlobalVariableDel("EA_SmallSellTicket");
   GlobalVariableDel("EA_LargeBuyTicket");
   GlobalVariableDel("EA_LargeSellTicket");
   GlobalVariableDel("EA_SmallTicket");
   GlobalVariableDel("EA_LargeTicket");
   GlobalVariableDel("EA_DirectionalTicket");
   
   Print("Reset completo. Próxima tick deve abrir hedges.");
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Expert initialization                                            |
//+------------------------------------------------------------------+
int OnInit() {
   Print("=== HedgeEA_Progressivo v1.10 iniciado ===");
   Print("Symbol=", _Symbol, " | Spread atual=", 
         (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / _Point);
   
   if (ResetStateOnStart) {
      CloseAllOurPositionsAndReset();
   } else if (GlobalVariableCheck("EA_State")) {
      EA_State             = GlobalVariableGet("EA_State");
      EA_Direction         = GlobalVariableGet("EA_Direction");
      EA_SmallLot          = GlobalVariableGet("EA_SmallLot");
      EA_LargeLot          = GlobalVariableGet("EA_LargeLot");
      EA_SmallBuyTicket    = (ulong)GlobalVariableGet("EA_SmallBuyTicket");
      EA_SmallSellTicket   = (ulong)GlobalVariableGet("EA_SmallSellTicket");
      EA_LargeBuyTicket    = (ulong)GlobalVariableGet("EA_LargeBuyTicket");
      EA_LargeSellTicket   = (ulong)GlobalVariableGet("EA_LargeSellTicket");
      EA_SmallTicket       = (ulong)GlobalVariableGet("EA_SmallTicket");
      EA_LargeTicket       = (ulong)GlobalVariableGet("EA_LargeTicket");
      EA_DirectionalTicket = (ulong)GlobalVariableGet("EA_DirectionalTicket");
      
      // Força recarga se globals estiverem zeradas
      if (EA_SmallLot <= 0.0) EA_SmallLot = HedgeSmallLot;
      if (EA_LargeLot <= 0.0) EA_LargeLot = HedgeLargeLot;
      
      Print("Estado restaurado | State=", EA_State, " | SmallLot=", EA_SmallLot, " | LargeLot=", EA_LargeLot, " | Posições=", CountOurPositions());
   } else {
      Print("Primeira execução - criando globals zeradas.");
      EA_State = 0.0;
      EA_Direction = 0.0;
      EA_SmallLot = HedgeSmallLot;
      EA_LargeLot = HedgeLargeLot;
      GlobalVariableSet("EA_State", EA_State);
      GlobalVariableSet("EA_Direction", EA_Direction);
      GlobalVariableSet("EA_SmallLot", EA_SmallLot);
      GlobalVariableSet("EA_LargeLot", EA_LargeLot);
   }
   
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
   EA_State             = GlobalVariableGet("EA_State");
   EA_Direction         = GlobalVariableGet("EA_Direction");
   EA_SmallLot          = GlobalVariableGet("EA_SmallLot");
   EA_LargeLot          = GlobalVariableGet("EA_LargeLot");
   EA_SmallBuyTicket    = (ulong)GlobalVariableGet("EA_SmallBuyTicket");
   EA_SmallSellTicket   = (ulong)GlobalVariableGet("EA_SmallSellTicket");
   EA_LargeBuyTicket    = (ulong)GlobalVariableGet("EA_LargeBuyTicket");
   EA_LargeSellTicket   = (ulong)GlobalVariableGet("EA_LargeSellTicket");
   EA_SmallTicket       = (ulong)GlobalVariableGet("EA_SmallTicket");
   EA_LargeTicket       = (ulong)GlobalVariableGet("EA_LargeTicket");
   EA_DirectionalTicket = (ulong)GlobalVariableGet("EA_DirectionalTicket");

   // Força lotes mínimos se globais zeradas
   if (EA_SmallLot <= 0.0) EA_SmallLot = HedgeSmallLot;
   if (EA_LargeLot <= 0.0) EA_LargeLot = HedgeLargeLot;

   int our_pos = CountOurPositions();
   double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / _Point;
   PrintFormat("OnTick | State=%.0f | Direction=%.0f | Posições=%d | SmallLot=%.2f | LargeLot=%.2f | Spread=%.1f",
               EA_State, EA_Direction, our_pos, EA_SmallLot, EA_LargeLot, spread);

   // Abrir hedges iniciais
   if (EA_State == 0.0 && (our_pos == 0 || ForceInitialHedge)) {
      Print("=== Iniciando hedges ===");
      ulong sb = OpenPosition(EA_SmallLot, POSITION_TYPE_BUY, magic_small_buy, "Small Buy");
      ulong ss = OpenPosition(EA_SmallLot, POSITION_TYPE_SELL, magic_small_sell, "Small Sell");
      ulong lb = OpenPosition(EA_LargeLot, POSITION_TYPE_BUY, magic_large_buy, "Large Buy");
      ulong ls = OpenPosition(EA_LargeLot, POSITION_TYPE_SELL, magic_large_sell, "Large Sell");
      
      if (sb > 0 && ss > 0 && lb > 0 && ls > 0) {
         GlobalVariableSet("EA_SmallBuyTicket", sb);
         GlobalVariableSet("EA_SmallSellTicket", ss);
         GlobalVariableSet("EA_LargeBuyTicket", lb);
         GlobalVariableSet("EA_LargeSellTicket", ls);
         Print("Hedges abertos OK!");
      } else {
         Print("Falha na abertura inicial - verifique log.");
      }
   }

   // Trigger eliminação
   if (EA_State == 0.0) {
      bool trigger_up = IsTriggered(EA_LargeBuyTicket, EA_SmallSellTicket);
      if (trigger_up) {
         Print("Trigger UP acionado");
         if (ClosePosition(EA_LargeBuyTicket) && ClosePosition(EA_SmallSellTicket)) {
            GlobalVariableSet("EA_Direction", 1.0);
            GlobalVariableSet("EA_SmallTicket", EA_SmallBuyTicket);
            GlobalVariableSet("EA_LargeTicket", EA_LargeSellTicket);
            ulong dir = OpenPosition(DirectionalLot, POSITION_TYPE_BUY, magic_directional, "Directional Buy");
            if (dir > 0) {
               GlobalVariableSet("EA_DirectionalTicket", dir);
               GlobalVariableSet("EA_State", 1.0);
               Print("UP concluído - state=1");
            }
         }
      }

      bool trigger_down = IsTriggered(EA_LargeSellTicket, EA_SmallBuyTicket);
      if (trigger_down) {
         Print("Trigger DOWN acionado");
         if (ClosePosition(EA_LargeSellTicket) && ClosePosition(EA_SmallBuyTicket)) {
            GlobalVariableSet("EA_Direction", -1.0);
            GlobalVariableSet("EA_SmallTicket", EA_SmallSellTicket);
            GlobalVariableSet("EA_LargeTicket", EA_LargeBuyTicket);
            ulong dir = OpenPosition(DirectionalLot, POSITION_TYPE_SELL, magic_directional, "Directional Sell");
            if (dir > 0) {
               GlobalVariableSet("EA_DirectionalTicket", dir);
               GlobalVariableSet("EA_State", 1.0);
               Print("DOWN concluído - state=1");
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
            Print("Small + Directional fechados - isolando large loss");
            ulong isolating = 0;
            ENUM_POSITION_TYPE iso_type = (EA_Direction == 1.0) ? POSITION_TYPE_BUY : POSITION_TYPE_SELL;
            isolating = OpenPosition(EA_LargeLot, iso_type, magic_isolating, (EA_Direction == 1.0 ? "Isolating Buy" : "Isolating Sell"));
            
            if (isolating > 0) {
               double new_small = EA_LargeLot;
               double new_large = EA_LargeLot + LotIncrease;
               GlobalVariableSet("EA_SmallLot", new_small);
               GlobalVariableSet("EA_LargeLot", new_large);
               
               PrintFormat("Atualizado: new_small=%.2f | new_large=%.2f - abrindo novo hedge", new_small, new_large);
               
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
                  
                  Print("Sequência completa: novo hedge aberto - state resetado para 0");
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
   ObjectDelete(ChartID(), BotaoCloseReset);
   Print("EA finalizado. Motivo: ", reason);
}