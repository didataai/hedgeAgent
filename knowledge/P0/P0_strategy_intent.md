# Strategy Intent — P0

## Objetivo

Este arquivo resume a intenção humana da estratégia com base nos arquivos de notas, prompts e documentação da família.

## Fontes analisadas

- `PromptEA-P0.txt` (text_note): ok

## Conceitos detectados

- `initial_market_hedge`
- `four_initial_orders`
- `small_large_lots`
- `range_trigger`
- `winner_eliminates_loser`
- `directional_order`
- `return_stop_or_recovery`
- `lot_increment`
- `pending_vs_market_question`

## Pistas numéricas

- Lotes detectados: `['0.01', '0.02', '0.03', '0.04', '0.05', '0.06']`
- Preços/pontos detectados: `['3000', '3500', '500']`
- Valores USD detectados: `['-8USD', '10usd']`

## Resumo determinístico

- Família P0: intenção humana extraída de arquivos de notas/contexto.
- Esta leitura é determinística e deve ser validada por resolução por fontes.
- A estratégia parece nascer de um hedge/travamento inicial a mercado.
- Há pistas de dois blocos/lotes principais, especialmente 0.03 e 0.04.
- Há intenção de usar a ordem maior lucrativa para eliminar ordem menor perdedora.
- Após eliminação, há intenção de abrir uma ordem direcional.
- O retorno do preço contra a direcional é tratado como problema central de stop/recovery.
- Há pista de incremento de lote, que precisa ser avaliado por DD, margem e risco.

## Perguntas abertas

- A intenção menciona dúvida entre executar a mercado ou usar limits; isso precisa virar regra formal.
- Ainda é necessário transformar a intenção em uma especificação de estados, transições e eventos testáveis.
- Backtest ainda não foi executado; a robustez em tendência, range e zig-zag é desconhecida.
