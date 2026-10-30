# Manual de produção — vídeo longo do NOSSO MUNDO PIXEL

Para quem vai fazer um episódio (pessoa ou agente). O piloto `ep01` é o modelo:
leia `ep01_roteiro.py` inteiro e `ep01_motor.py` por amostra antes de começar.

## O que é o canal
Pixel art que explica como as coisas funcionam. **Sem voz.** Música baixa
(original, gerada). Legendas grandes em **português do Brasil** (com acento).
Público brasileiro geral, curioso, não técnico. O tom é de quem mostra, não de
quem dá aula: frases curtas, concretas, uma ideia por legenda.

## Regras que não se negociam
1. **Todo fato na tela tem fonte** em `FONTES` do roteiro, e a legenda aponta para ela
   (`('F3',)`). Fonte = página que você LEU (WebSearch → WebFetch), nunca um endereço
   montado de memória. Prefira: Britannica, Wikipedia, sites de governo, universidades,
   fabricantes, NASA, FAA, ANAC, Inmetro. Conta própria pode ser fonte ("conta a partir de F2").
2. **Simplificar pode, esconder não:** o que foi simplificado vai para a seção
   "Simplificado de propósito" da `DESCRICAO`.
3. **Teste da cena:** todo capítulo tem protagonista (a peça, a mala, a gota), um objetivo
   que sobe na tela (contador, etapa 2 de 5) e progressão. Visualizador abstrato reprova.
4. **Nada de marca, logo, personagem ou pessoa real desenhada** (nem avião com pintura de
   companhia aérea, nem logotipo de celular). Tudo genérico.
5. **Ritmo:** 7 a 9 min no total (8 min ou mais libera anúncio no meio). Câmera lenta só
   onde ensina; legenda fica no ar 4 a 8 s; nenhum trecho parado mais de ~8 s.
6. Texto na tela também em PT-BR. Números no formato brasileiro: 3.000 e 1,5
   (`idioma.milhar`, `idioma.decimal`).

## Os arquivos de um episódio
Você cria SÓ estes (não mexa em nenhum arquivo compartilhado; se precisar de algo novo
no `longo.py` ou na fonte, descreva no seu relatório):
- `epNN_roteiro.py` — `TITULO`, `CAPITULOS`, `LEGENDAS`, `FONTES`, `CAPITULOS_YT`,
  `DESCRICAO`, `PREFIXO`, `CORTES`. Mesma estrutura do ep01.
- `epNN_motor.py` — as cenas. Mesma estrutura do ep01: `SEED`, `RAIZ`, `GANHO_MUSICA`,
  `GANHO_EFEITOS`, `LUFS = -16.0`, `VERTICAL = False`, uma classe por capítulo (herdando
  a ideia de `Cena`: `desenhar(tela, t, tg)` e `sons(fx)`), `CENAS = {id: classe}` e o
  `__main__` com `--folha`. Pode copiar `Cena`, `escurecer`, `seta`, `engrenagem`,
  `amostrar_teta`, `cruzamentos` do ep01 para dentro do seu arquivo.
- Se o desenho for grande, um módulo de desenho próprio `epNN_desenho.py`
  (como o `motor_pixel.py` do ep01).

## A tela
- 480x270 desenhada, ampliada 4x (1080p). Palco: y 0..208. Legenda: faixa y 210..270
  (desenhada pelo `longo.py`; você só escreve o texto no roteiro).
- Paleta `oficina` (32 cores, nomes em `longo.py`: FUNDO, FUNDO2, FUNDO3, TRACO,
  ACO0..ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, CHAMA0..2, BRASA, MISTURA,
  MISTURA2, GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA,
  OLEO0, OLEO1). Pode registrar uma paleta própria do episódio se o tema pedir (céu,
  corpo humano), com a mesma convenção dos índices 0..15 (ver `pixelengine.py`).
- Desenho: `tela.ret`, `tela.disco`, `tela.anel`, `tela.linha`, `tela.px`,
  `longo.dither` (degradê 8-bit), `longo.poligono`, `longo.linha_grossa`,
  `longo.painel`, `longo.texto_marcado`. Texto: `tela.texto(txt, x, y, cor, tam=9|17|26,
  centro=True, contorno=PRETO)`; tam 9 = 1x (7 px), 17 = 2x, 26 = 3x.
- Capricho que o ep01 tem e o seu também precisa ter: sombreado com dither, contorno
  escuro nas peças, brilho nas partes quentes/luminosas, movimento contínuo (nada
  congelado), rótulos com fio até a peça, painel à direita com o estado do sistema.
- Quadro do canal: o lado direito (x 300..470) costuma ser o painel de informação; o
  protagonista fica à esquerda/centro.

## A trilha e o som
- `CAPITULOS`: cada capítulo tem gênero (`lofi`, `synthwave`, `house`, `chiptune`...),
  número de compassos e papel (`drop` = groove calmo, `break` = só pad). Duração =
  compassos x 4 x 60/bpm (lofi 80 → 3 s por compasso; synthwave 100 → 2,4 s).
- Efeitos: em `sons(fx)` use `fx.put(som, instante_global, ganho, pan)` com
  `fx.clique`, `fx.chiado(dur, f_lo, f_hi)`, `fx.explosao(lento)`, `fx.pulso()`,
  `fx.sino(nota_midi)`, `fx.blip(nota_midi)`. Som só do que se vê, discreto.

## Os cortes verticais (Shorts)
`CORTES` no roteiro: 5 a 6 trechos de 15 a 40 s, cada um com `de`/`ate`
(capítulo, segundo), `x` (coluna onde começa o recorte de 180 px da tela larga: o
protagonista tem que caber nesse recorte), `gancho` (2 linhas, cada uma até 136 px em 2x,
~11 letras), `titulo` e `descricao`. Em `VERTICAL = True` esconda o que fica cortado.

## Como testar (obrigatório antes de entregar)
```
cd /home/claude/repo/motor
python3 longo_verificar.py --roteiro epNN_roteiro           # largura, glifo, 4 s, fontes
python3 epNN_motor.py --folha /tmp/.../folha.png            # 2 quadros por capítulo
python3 longo_short.py epNN_motor --folha /tmp/.../cortes.png
```
Abra as folhas com Read e olhe de verdade: texto cortado, peça flutuando, tela vazia,
cor ilegível, mecanismo errado. Corrija e gere de novo. NÃO renderize o vídeo inteiro
(leva ~15 min e a máquina é compartilhada).

## O relatório final
Até 300 palavras: duração total, capítulos, lista de fatos com fonte, o que foi
simplificado, defeitos que você achou e corrigiu, e qualquer coisa que precise mudar
em arquivo compartilhado.
