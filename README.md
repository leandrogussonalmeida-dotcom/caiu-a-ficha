# CAIU A FICHA

Motor de produção do canal **CAIU A FICHA**. Todo vídeo do canal é gerado por
código: nada de banco de imagens, nada de banco de sons, nenhum recurso
externo. O fundo é numpy, a trilha é sintetizada, a vinheta é desenhada.

O nome é o conceito: "caiu a ficha" é o instante em que a pessoa entende. O
canal entrega esse instante de dois jeitos — pelo erro (quiz) e pela escala
(simulação).

## Os dois motores

### `motor/quizengine.py` — quiz com voz
Linha do tempo, layout, quadros, VERIFY, split, legendas para narração.
A voz é um clone da voz do Leandro; os `.wav` entram por `narracao/` e vencem
qualquer voz sintética. Shorts saem do mesmo áudio, acelerados sem mudar o tom.

### `motor/pixelengine.py` — simulação em pixel, sem voz
Desenha em 180×320 e amplia 6× por vizinho mais próximo: 36 vezes menos conta
por quadro, e o 8-bit sai de verdade em vez de filtro por cima.

**A sincronia é construída, não detectada.** Como a trilha é nossa, o instante
de cada batida é `n × 60/bpm`, exato na amostra. Não existe detecção de beat em
lugar nenhum do código. `Batida.pulso(t)` devolve 1 na batida e cai até a
próxima — multiplique qualquer coisa por ela e ela dança.

## Simuladores

| arquivo | série | o que faz |
|---|---|---|
| `motor/sim_torre.py` | A TORRE | bloco cai na batida, câmera sobe, marcos brasileiros |
| `motor/sim_escala.py` | ESCALA | a referência encolhe até virar um tracinho |
| `motor/sim_lousa.py` | A LOUSA | traço contínuo de dois botões, chacoalhar entre desenhos |

Faltam: `viagem`, `cadeia`, `extremo`, `corrida`, `descida`, `estrada`,
`revelar`, `ambiente`.

## Apoio

| arquivo | o que é |
|---|---|
| `motor/quizaudio.py` | trilha (bateria, baixo, acordes), efeitos, masterização a −14 LUFS |
| `motor/quizbg.py` | 11 famílias de fundo × 10 paletas |
| `motor/quizbrand.py` | vinheta de colagem (papel rasgado, letra de revista) |
| `motor/formas.py` | silhuetas em pixel como lista de retângulos |
| `motor/voice.py` | 4 vozes sintéticas de reserva |
| `motor/alocar.py` | reserva fundo e paleta por peça; falha se repetir |
| `motor/fazer_shorts.py` | corta Shorts do longo reaproveitando a narração |

## Comandos

```bash
# quiz
SEED=<n> python3 motor/quizengine.py render  decks/<deck>.json out16
SEED=<n> python3 motor/quizengine.py vinheta decks/<deck>.json out16 [v]
         python3 motor/quizengine.py verify  out16

# simulação
python3 motor/sim_escala.py unidades/<arq>.json <seed> out-escala
python3 motor/sim_lousa.py  unidades/<arq>.json <seed> out-lousa
python3 motor/sim_torre.py  <seed> <blocos> out-torre
```

Variáveis de ambiente: `SEED` · `MUDO=1` (sem faixa de áudio, para casar com
som da plataforma) · `BPM=<n>` (trava o visual no andamento de uma música de
fora) · `VOZ` · `SEM_VOZ=1` · `NARR` · `VELOC` · `REUSO=1`.

Todo render exporta `batidas.json` com os instantes de batida ao milésimo, em
segundos e em quadro, para alinhar em qualquer editor.

## Regras que não mudam

- Nenhuma pergunta sem explicação verificável; nenhuma unidade sem fonte.
- Nada de personagem, logo, mascote ou marca nos desenhos — nem na moldura da
  lousa, cujo original é marca registrada.
- Nada de saúde; finanças só como matemática de progressão.
- Título é um número com unidade, nunca frase de caça-clique.
- Série nunca numerada no título.
- SEED novo sempre, anotado; fundo e paleta reservados, nunca sorteados.

O plano dos 80 vídeos e 200 Shorts e as receitas técnicas vivem nos docs do
projeto MOTION SO, no claude.ai.
