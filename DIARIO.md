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

## 29/10/2026 — NOSSO MUNDO PIXEL e o primeiro vídeo longo

Nome do canal: NOSSO MUNDO PIXEL. Formato longo novo: "como funciona" sem voz, música baixa, legendas grandes. Piloto: ep01, o motor de 4 tempos (8 min 19 s, 15 capítulos).

| o quê | medida |
| --- | --- |
| resolução | 480x270 desenhado, 4x = 1920x1080 (Shorts: 180x320 x6) |
| geometria | pistão pela fórmula da biela; comando a meia rotação; abertura da válvula lida do perfil do came; faísca a 20° antes do PMS; taxa visual ~9,8:1 |
| legenda | fonte 2x (14 px = 56 px em 1080p), até 37 letras, mínimo 4 s no ar |
| render | 13 min para 8 min 19 s (2 núcleos) |
| áudio | -16 LUFS integrado; trilha a -10 dB dos efeitos; limitador final a -2,2 dBFS |

**Defeitos pegos antes de entregar:**
- Fonte: a vírgula parecia ponto ("3,000" lido como "3.000") e depois barra; o V parecia U ("VALVES" -> "UALUES"). Glifos refeitos; testadas 3 vírgulas lado a lado.
- Comando de válvulas girava ao contrário do virabrequim (no motor real giram no mesmo sentido).
- Dutos convergiam para o meio (funil); agora cada um desce até a sua válvula.
- Fonte de marcha lenta: eu tinha montado um endereço; trocado pelo endereço que foi lido de fato.
- Áudio: pico -0,7 dBTP depois do AAC (reprovou); capítulos rápidos 5 dB acima dos lentos; efeitos da câmera lenta inaudíveis. Limitador com folga e ganhos refeitos.

**Checagem independente de fatos (agente separado, 41 legendas):** 39 OK. Corrigidas: "one cylinder is always pushing" (exagero: o impulso começa a cada meia volta, mas não dura a meia volta toda) e 12-30% na legenda contra 16-25% no gráfico (mesma fonte, medidas diferentes; ficou 16-25%). "Burns in a flash" virou "burns fast".

## 29-30/10/2026 — produção em massa, PT-BR primeiro

Leandro aprovou o piloto ("detalhes muito bons", música baixa funciona) e achou lento. Pedido: as 4 séries, longos + cortes, títulos e descrições em txt, tudo em português do Brasil; miniaturas e inglês depois.

- Tela, títulos e descrições voltaram para PT-BR (`idioma.py`: `T(pt, en)`, `milhar`, `decimal`; fonte com acento e cedilha). O ep01 em inglês ficou guardado.
- Catálogo de 25 episódios em 4 séries (`catalogo.py`); `canal.py` renderiza só o que está `pronto`, cada episódio no seu processo.
- Esteira: agente de produção (`PRODUCAO.md`) → revisão das folhas → checagem de fatos por outro agente → correções → pronto.
- Ritmo mais rápido: legenda 4 a 8 s, nada parado mais de ~8 s.

**A checagem independente pegou em cada episódio de 2 a 6 legendas.** Exemplos: ep02 "mais velocidade, menos pressão"; ep06 data do iceberg; ep07 o servidor lê o envelope, não a mensagem; ep08 "60 fps é o mínimo" era opinião de coluna e virou "para muitos jogadores".

**Defeitos de código pegos:** a paleta própria do ep04 vazava para os outros episódios (agora um processo por episódio); método `pos` de um agente colidia com o gancho do fim; estouro de uint8 na folha do ep08.

## 30/10/2026 — catálogo completo

Os 25 episódios das 4 séries passaram pela esteira (produção → revisão das folhas → checagem independente → correções). Exemplos do que a checagem pegou: gerador de Itaipu é 18 kV (não 13,8); ep13 dizia 30% de eficiência da gasolina contra 16-25% do ep01; "60 fps é o mínimo" era opinião; Wi-Fi de 6 GHz mudou em 2026 (Anatel limita a faixa a partir de 2027); "lado mais comprido do sifão" é mito; o estômago aparecia espelhado; Alcântara é a base *em terra* mais perto do equador.

Ritmo: todos entre 480 e 503 s. Dois saíram curtos (balão 7:42, gota 7:30) e ganharam um capítulo novo, sem desacelerar nada. O piloto ep01 (6:06 depois de acelerado) está ganhando 2 min de conteúdo.

Gosto: na garfada, a saída virou uma esteira neutra até a porta (o tubo cor de pele podia ser lido de outro jeito). Na fechadura, nada ensina a abrir sem chave.
