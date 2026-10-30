# ESTADO — NOSSO MUNDO PIXEL

Atualizado em 30/10/2026. Ler só isto no começo de cada sessão.

## O canal
- Nome: **NOSSO MUNDO PIXEL**. **Primeiro em português do Brasil** (tela, títulos, descrições). Inglês fica para depois (o ep01 em inglês está guardado).
- **Vídeo longo (o que monetiza):** "como funciona" em pixel detalhado, sem voz, música baixa por baixo dos efeitos, legendas grandes. 7 a 9 min (8 min ou mais libera anúncio no meio).
- **Shorts:** 5 a 6 cortes verticais de cada longo + a série NO RITMO (27, jogo que a música controla).
- **Miniaturas:** ficam para depois (todo txt de publicação termina com "MINIATURA (a fazer)").

## As 4 séries (25 episódios, `catalogo.py`)
POR DENTRO (máquina aberta) · A JORNADA (seguir um protagonista) · COMO VOA / FLUTUA (força e física) · FEITO DE PIXELS (mundo digital).

## Opinião do Leandro sobre o piloto (29/10)
Gostou dos detalhes e da música baixa. **Achou lento.** Daí em diante: câmera lenta só onde ensina, legenda 4 a 8 s, nada parado mais de ~8 s.

## Teste da cena
Protagonista que a gente acompanha; objetivo que sobe na tela; progressão; o mecanismo (ou a música) é a regra. Visualizador abstrato reprova.

## Como um episódio fica pronto
1. Produção: `epNN_roteiro.py` + `epNN_motor.py` (+ `epNN_desenho.py`), seguindo `PRODUCAO.md`.
2. Revisão das folhas (quadros de cada capítulo e dos cortes).
3. Checagem de fatos por agente independente; correções aplicadas.
4. `estado='pronto'` no `catalogo.py`. Só o que está pronto entra no render.

## Situação em 30/10 (fim do dia)
- **Os 25 episódios estão prontos** (roteiro + desenho + checagem de fatos independente): ep01 a ep25, 8 a 8,5 min cada, todos com 5 a 6 cortes verticais.
- ep01 (piloto) está ganhando ~2 min de conteúdo novo para passar de 8 min (anúncio no meio).
- Nada foi renderizado no PC ainda: o computador estava desconectado. Render estimado: 15 a 30 min por longo.

## Como rodar no PC (`2-RENDERIZAR.bat`)
1 lista · 2 textos (títulos e descrições em `PUBLICAR\`) · 3 longos (`VIDEOS\`) · 4 cortes (`SHORTS\CORTES\`) · 5 NO RITMO (`SHORTS\NO RITMO\`) · 6 um episódio · T tudo · V verificar.
Pula o que já está feito e passa no verificador: dá para fechar e rodar de novo. Cada longo leva 10 a 30 min.

## Regras técnicas
- Áudio do longo -16 LUFS, limitador -2,2 dBFS; Shorts -14 LUFS.
- Verificador: 1080p, um quadro a cada 1/30 s, ≥ 400 kb/s, duração ±1 s.
- Cada episódio renderiza no seu próprio processo (paleta própria não vaza).
- Método de cena chamado `pos` é reservado (gancho de pós-processamento do fim).

## O que falta
1. Terminar ep08 a ep25 e entregar no PC.
2. Miniaturas de cada longo e de cada Short.
3. Banner, foto de perfil, marca d'água; criar o canal.
4. Versão em inglês.
