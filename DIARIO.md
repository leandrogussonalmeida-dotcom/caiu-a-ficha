# DIARIO — RITMO PIXEL

Cada melhoria do motor com a medida de antes e depois. Defeito vira teste antes de ser corrigido.

## 20/10/2026 — motor NO RITMO revisado para o RITMO PIXEL

Peça de referência: r01 (masmorra), mais r16 (cidade) e r28 (túnel). Antes = motor do ramo `no-ritmo-shorts`.

| o quê | antes | depois |
| --- | --- | --- |
| fonte do texto | DejaVu Mono rasterizada (traço irregular) | `pixelfonte.py`: 5x7 própria, escala inteira 1x/2x/3x |
| texto sobre o cenário | tarja preta atrás de cada texto | contorno de 1 px + sombra, sem tarja |
| HUD | "112 BPM" + "FASE 1/3" + placa em caixas pretas | painéis de jogo com borda; fases viram pontinhos |
| idioma na tela e no título | português | inglês (canal global); verificador reprova português |
| luz | nenhuma | brilho em degraus que respira no bumbo, vinheta pontilhada (Bayer), flash e aberração de 1 px no drop |
| troca de gênero | corte seco | tela fecha em blocos 4x4 e abre no quadro do drop |
| vinheta | ficha do CAIU A FICHA, 3,1 s | RITMO PIXEL: pixel quica 3x e vira o nome, 2,8 s |
| versões de cada som de bateria | 1 (mesmo arquivo em todo golpe) | 2 (bumbo) a 6 (chimbal), round-robin |
| força dos golpes | fixa por padrão | variação natural (chimbal ±13%, caixa ±6%) |
| tempo do chimbal | grade exata | até ±6 ms (bumbo e caixa continuam exatos) |
| energia 1-2,5 kHz / 2,5-6 kHz (r01) | -8,0 / -10,6 dB | -9,9 / -12,7 dB (menos estridente) |
| loudness / pico (r01) | -14,0 LUFS / -4,3 dBTP | -14,0 LUFS / -3,2 dBTP |
| sincronia som x evento | 0,0 ms | 0,0 ms (humanização mexe no evento, não no áudio) |
| tempo de render (r01, 2 núcleos) | 36 s | 54 s |

**Defeito que virou teste:** 178 dos 180 Shorts antigos saíram com 33 KB (um quadro só) e passaram como "ok", porque o render só conferia se havia vídeo e áudio. Agora `ritmo_render.probe` e `ritmo_verificar` exigem um quadro a cada 1/30 s e pelo menos 400 kb/s. Testado com um r01 de um quadro só: REPROVOU (antes passava).

**Teste novo de texto:** `ritmo_verificar.py --plano` reprova gancho que não cabe na margem segura em 2x (136 px), caractere sem glifo e palavra em português. Pegou 9 ganchos largos demais no primeiro rascunho em inglês.

**Defeito pego na revisão visual:** a placa "DRUM AND BASS" em 2x ocupava a tela inteira e passava sob os botões. Agora vira "DRUM & BASS" (122 px) e o `--plano` reprova placa de gênero acima de 136 px.

Arquivos novos: `pixelfonte.py`, `ritmo_acabamento.py`, `ritmo_marca.py`.
Arquivos mudados: `pixelengine.py`, `ritmo_base.py`, `ritmo_musica.py`, `ritmo_plano.py`, `ritmo_publicar.py`, `ritmo_render.py`, `ritmo_verificar.py`, as 10 `cena_*.py`.

## 22/10/2026 — a cidade saiu

Leandro aprovou masmorra (r01) e túnel (r28) e reprovou a cidade (r16): "não faz o menor sentido". O motivo: prédios pulando como equalizador não têm protagonista, objetivo nem progressão. r16 a r18 saíram do plano (30 -> 27). Virou o **teste da cena** no ESTADO.md: protagonista, objetivo que sobe, progressão, música como regra do jogo.
