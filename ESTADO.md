# ESTADO — RITMO PIXEL

Atualizado em 22/10/2026. Ler só isto no começo de cada sessão.

## O canal
- Nome: **RITMO PIXEL** (decidido em 20/10). Público **global**: tudo na tela e nos títulos em inglês.
- Identidade: pixel art que a música controla (jogo + música), música sintetizada por código, sem voz.
- Sai o "tamanho das coisas". Os vídeos e Shorts antigos foram apagados; ficou só a série NO RITMO.

## O que existe
- `_motor\`: o motor. Ainda tem arquivos do quiz e dos simuladores antigos (pode apagar: `quiz*.py`, `voice.py`, `resgatar_voz.py`, `sim_*.py`, `decks\`, `out-v0*\`).
- Série NO RITMO: 27 Shorts no plano (`ritmo_plano.py`), 9 cenas x 3. A cidade saiu em 22/10.
- `REELS\NO RITMO\`: os 30 Shorts ANTIGOS (vinheta CAIU A FICHA, texto em português). Não publicar.
- Motor revisado em 20/10 (ver DIARIO.md): fonte de pixel própria, HUD de jogo, luz, vinheta RITMO PIXEL, bateria humanizada, inglês, verificador que pega arquivo vazio.

## Teste da cena (22/10, do julgamento do Leandro)
Masmorra e túnel aprovados; cidade reprovada ("não faz o menor sentido"). Uma cena só entra se tiver:
1. **Protagonista** que a gente acompanha (herói, nave).
2. **Objetivo que sobe** na tela (combo, portais passados).
3. **Progressão**: o mundo muda de fase (cor, perigo, velocidade).
4. **A música é a regra do jogo** (ele anda, pula ou passa NA batida), não enfeite.
Visualizador abstrato (prédio pulando como equalizador) reprova.

## Como rodar no PC
- `2-RENDERIZAR.bat`: T (os 27), U (um), V (verificar), P (títulos em inglês).
- Saída: `SHORTS\`. Publicar só o que o V marcar PASSOU.

## O que falta
1. Leandro julgar as outras 7 cenas (r04 rota, r07 foguete, r10 lousa, r13 corrida, r19 plataforma, r22 bolinha, r25 pistas). Masmorra e túnel já aprovados.
2. Renderizar no PC só as cenas aprovadas e verificar.
3. **Formato longo (16:9, 8-20 min)**: o motor só faz Shorts 9:16 de ~35 s. É o que monetiza; próximo grande passo.
4. Banner, foto de perfil e marca d'água RITMO PIXEL (`marca_canal.py` serve de modelo).
5. Repositório próprio do canal (hoje o código está no `caiu-a-ficha`, ramo `ritmo-pixel`).
6. Calendário: 1 a 2 Shorts por dia, alternando cena e paleta.

## Próximo passo
Leandro julgar as 7 cenas; depois, o modo longo ("jornada") construído a partir da masmorra e do túnel, que passaram no teste da cena.
