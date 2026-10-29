# ESTADO — NOSSO MUNDO PIXEL

Atualizado em 29/10/2026. Ler só isto no começo de cada sessão.

## O canal
- Nome: **NOSSO MUNDO PIXEL** (decidido em 29/10; antes RITMO PIXEL). Público **global**: tela, títulos e descrições em inglês.
- **Vídeo longo (o que monetiza):** "como funciona" em pixel detalhado, sem voz, com música baixa e legendas grandes. Piloto: ep01, o motor de 4 tempos.
- **Shorts:** a série NO RITMO (jogo que a música controla) e, depois, recortes dos vídeos longos.

## Teste da cena (22/10)
Uma cena só entra se tiver: 1) protagonista que a gente acompanha; 2) objetivo que sobe na tela; 3) progressão (o mundo muda de fase); 4) a música, ou o mecanismo, é a regra (as coisas acontecem NA batida). Visualizador abstrato reprova (a cidade saiu por isso).

## Vídeo longo: como é feito
- `longo.py`: tela 480x270 ampliada 4x (1080p), legenda 2x em faixa embaixo (até 37 letras, 2 linhas, *palavra* em amarelo), trilha baixa por capítulo, efeitos, troca em blocos.
- `epNN_roteiro.py`: capítulos, legendas com tempo e **cada fato com fonte** (FONTES). `epNN_motor.py`: o desenho de cada capítulo.
- Antes do render: `longo_verificar.py --roteiro epNN_roteiro`. Depois: `longo_verificar.py video.mp4 epNN_roteiro` (1080p, quadros, -17 a -15 LUFS, pico ≤ -1).
- Toda explicação passa por uma **checagem de fatos independente** antes de publicar (no ep01 pegou 2 legendas).
- `longo_publicar.py`: título, descrição com capítulos (0:00...) e fontes.

## O que existe
- ep01 "How a Car Engine Works" (8 min 19 s): roteiro checado, render verificado. Aguardando o Leandro julgar a qualidade.
- 27 Shorts NO RITMO no plano (9 cenas); 7 cenas aguardando julgamento (r04, r07, r10, r13, r19, r22, r25).
- `_motor\` ainda tem o quiz e os simuladores antigos (pode apagar: `quiz*.py`, `voice.py`, `resgatar_voz.py`, `sim_*.py`, `decks\`, `out-v0*\`).

## Como rodar no PC
`2-RENDERIZAR.bat`: L (vídeo longo ep01), T (27 Shorts), U (um Short), V (verificar Shorts), P (títulos).

## O que falta
1. Leandro julgar o ep01 (imagem, legendas, ritmo, som).
2. Próximos temas (lista no documento do projeto): avião voando é o segundo sugerido.
3. Biblioteca de peças reutilizáveis (engrenagem, fluido, ar, corte) para acelerar os próximos episódios.
4. Banner, foto de perfil e marca d'água NOSSO MUNDO PIXEL; criar o canal no YouTube.
5. Repositório próprio do canal (hoje: `caiu-a-ficha`, ramo `ritmo-pixel`).

## Próximo passo
Opinião do Leandro sobre o ep01; ajustar o que ele apontar e escolher o ep02.
