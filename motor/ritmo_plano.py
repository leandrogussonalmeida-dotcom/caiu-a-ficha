#!/usr/bin/env python3
"""RITMO PIXEL, série NO RITMO — os 30 Shorts (textos em inglês: canal global).

9 cenas x 3 (a cidade saiu em 22/10). Nenhum par (cena, paleta) se repete, e cada Short tem trilha
própria (seed, tônica, gêneros e andamentos). O BPM sempre sobe dentro do
Short: é a promessa do gancho e o que segura até o fim.

Formato de cada entrada:
  id, cena, paleta, seed, gancho (2 linhas), sub_gancho, pergunta (comentário),
  secoes (gênero, compassos, papel, bpm opcional), variante, titulo, descricao
"""


def J(*partes, fim=2):
    """Jornada: ('gen', compassos[, bpm]) ... ; 'B' antes de um item põe um
    build de 1 compasso no gênero anterior. O último gênero repete no 'fim'
    (cartão de inscrição)."""
    out = []
    ant = None
    for p in partes:
        if p == 'B':
            out.append(dict(gen=ant['gen'], bars=1, papel='build', **({'bpm': ant['bpm']} if 'bpm' in ant else {})))
            continue
        d = dict(gen=p[0], bars=p[1], papel='drop')
        if len(p) > 2: d['bpm'] = p[2]
        out.append(d)
        ant = d
    f = dict(gen=ant['gen'], bars=fim, papel='fim')
    if 'bpm' in ant: f['bpm'] = ant['bpm']
    out.append(f)
    return out


DESENHOS_OK = ['AMPULHETA', 'AVIAO', 'BARCO', 'BICICLETA', 'CACTO', 'CARACOL', 'CARRO',
               'CASA', 'CHAVE', 'COGUMELO', 'FAROL', 'FLOR', 'FOLHA', 'GARRAFA', 'GATO',
               'GUARDA-CHUVA', 'IGREJA', 'LAMPADA', 'OCULOS', 'PEIXE', 'PONTE', 'RELOGIO',
               'XICARA', 'TESOURA', 'PANELA']

PLANO = [
    # ---------------------------------------------------------------- masmorra
    dict(id='r01', cena='masmorra', paleta='espaco', seed=1001, scanlines=True,
         gancho=['HE MOVES', 'ON THE BEAT'], sub_gancho='SOUND ON',
         pergunta='WHICH STAGE HIT HARDEST?',
         secoes=J(('chiptune', 4, 112), 'B', ('chiptune', 4, 150), 'B', ('dnb', 6)),
         titulo='He only moves on the beat (112 → 174 BPM)'),
    dict(id='r02', cena='masmorra', paleta='brasa', seed=1002,
         variante=dict(piso=(2, 1), luz=(9, 10, 11, 8), parede=(5, 3, 7), roupa=12),
         gancho=['DUNGEON', 'PHONK'], sub_gancho='STAY TILL THE END',
         pergunta='PHONK OR HARDSTYLE?',
         secoes=J(('phonk', 4, 126), 'B', ('phonk', 4, 140), 'B', ('hardstyle', 6)),
         titulo='A dungeon that runs on phonk 🔥'),
    dict(id='r03', cena='masmorra', paleta='gelo', seed=1003, scanlines=True,
         variante=dict(piso=(2, 1), luz=(11, 8, 9, 12), parede=(4, 3, 7), roupa=10, geleca=9),
         gancho=['TRY NOT', 'TO NOD'], sub_gancho='',
         pergunta='DID YOU NOD?',
         secoes=J(('techno', 4), 'B', ('trance', 5), 'B', ('gabber', 6)),
         titulo='Try not to nod your head (132 → 190 BPM)'),
    # ---------------------------------------------------------------- rota
    dict(id='r04', cena='rota', paleta='rota', seed=1004,
         paletas_secao=['rota', 'rota', 'rota', 'rota_noite', 'rota_noite', 'rota_noite'],
         variante=dict(zonas=['campo', 'praia', 'cidade', 'caverna', 'neon', 'neon']),
         gancho=['SLOWEST', 'TO FASTEST'], sub_gancho='80 TO 174 BPM',
         pergunta='WHICH ZONE IS YOURS?',
         secoes=J(('lofi', 2), ('dembow', 3), ('house', 4), ('dubstep', 4), ('dnb', 6)),
         titulo='From the slowest genre to the fastest 🎮'),
    dict(id='r05', cena='rota', paleta='rota_outono', seed=1005,
         paletas_secao=['rota_outono', 'rota_outono', 'rota', 'rota_noite', 'rota_noite', 'rota_noite'],
         variante=dict(zonas=['outono', 'cidade', 'neve', 'caverna', 'neon', 'neon']),
         gancho=['EVERY ZONE', 'A NEW GENRE'], sub_gancho='HEAR THE SWITCH',
         pergunta='WHICH ZONE GOT YOU?',
         secoes=J(('synthwave', 3), ('garage', 4), ('chiptune', 4), ('trap', 4), ('future', 5)),
         titulo='Every zone is a different genre (100 → 150 BPM)'),
    dict(id='r06', cena='rota', paleta='rota_noite', seed=1006, scanlines=True,
         paletas_secao=['rota_noite'],
         variante=dict(zonas=['campo', 'praia', 'cidade', 'caverna', 'neon', 'neon']),
         gancho=['5 GENRES', 'ONE ROAD'], sub_gancho='LO-FI TO DNB',
         pergunta='WHICH GENRE WOULD YOU SKIP?',
         secoes=J(('lofi', 2, 86), ('funk', 4), ('techno', 4), ('hardstyle', 4), ('dnb', 6)),
         titulo='A road trip through 5 electronic genres'),
    # ---------------------------------------------------------------- foguete
    dict(id='r07', cena='foguete', paleta='neon', seed=1007,
         gancho=['GATES BREAK', 'ON THE KICK'], sub_gancho='WATCH THE DROP',
         pergunta='HOW MANY GATES DID YOU COUNT?',
         secoes=J(('synthwave', 4), 'B', ('trance', 6), 'B', ('hardstyle', 6)),
         titulo='Every gate explodes on the kick 🚀'),
    dict(id='r08', cena='foguete', paleta='espaco', seed=1008, scanlines=True,
         variante=dict(cores=[12, 9, 15, 7], nariz=10, aleta=10),
         gancho=['HOW HIGH', 'CAN IT GO?'], sub_gancho='',
         pergunta='DID IT REACH SPACE?',
         secoes=J(('house', 4), 'B', ('dubstep', 6), 'B', ('dnb', 8)),
         titulo='How high does the rocket go on the beat? (124 → 174 BPM)'),
    dict(id='r09', cena='foguete', paleta='sangria', seed=1009,
         variante=dict(cores=[9, 12, 10, 11], nariz=12, aleta=12),
         gancho=['FULL SPEED', 'TO 190 BPM'], sub_gancho='CAN YOU KEEP UP?',
         pergunta='DID YOU SURVIVE 190?',
         secoes=J(('techno', 4), 'B', ('techno', 4, 145), 'B', ('gabber', 8)),
         titulo='Rocket speeding up to 190 BPM'),
    # ---------------------------------------------------------------- lousa
    dict(id='r10', cena='lousa', paleta='carvao', seed=1010, y_placa=238,
         variante=dict(desenhos=['GATO', 'FAROL', 'BICICLETA', 'GUARDA-CHUVA', 'CARACOL']),
         gancho=['GUESS IT', 'IN TIME'], sub_gancho='5 DRAWINGS',
         pergunta='HOW MANY DID YOU GET?',
         secoes=J(('house', 3), ('garage', 3), ('trap', 3), ('dnb', 4), ('dnb', 4, 180)),
         titulo='Guess the drawing before the beat finishes ✏️'),
    dict(id='r11', cena='lousa', paleta='menta', seed=1011, y_placa=238,
         variante=dict(desenhos=['CASA', 'PEIXE', 'AVIAO', 'IGREJA', 'XICARA'], moldura=9, vidro=6, traco=0),
         gancho=['THE DRAWING', 'SPEEDS UP'], sub_gancho='GUESS FIRST',
         pergunta='WHICH ONE WAS HARDEST?',
         secoes=J(('lofi', 2), ('synthwave', 3), ('house', 3), ('future', 3), ('dnb', 4)),
         titulo='The drawing speeds up with the music (80 → 174 BPM)'),
    dict(id='r12', cena='lousa', paleta='mostarda', seed=1012, y_placa=238,
         variante=dict(desenhos=['CACTO', 'CARRO', 'AMPULHETA', 'LAMPADA', 'BARCO'], moldura=15, vidro=8, traco=0, fundo=(2, 1)),
         gancho=['CAN YOU GET', 'ALL 5?'], sub_gancho='BEFORE THE BEAT',
         pergunta='DID YOU GET ALL 5?',
         secoes=J(('dembow', 3), ('chiptune', 3, 130), ('phonk', 3, 140), ('hardstyle', 4), ('gabber', 4)),
         titulo='Can you guess all 5 drawings before the beat?'),
    # ---------------------------------------------------------------- corrida
    dict(id='r13', cena='corrida', paleta='por_do_sol', seed=1013, y_placa=92,
         variante=dict(ceu='sol', carro=15),
         gancho=['LAST PLACE', 'TO FIRST'], sub_gancho='ON THE BEAT',
         pergunta='WHERE WOULD YOU FINISH?',
         secoes=J(('synthwave', 4), 'B', ('house', 6), 'B', ('dnb', 8)),
         titulo='Last to first place, one beat at a time 🏁'),
    dict(id='r14', cena='corrida', paleta='noite_cidade', seed=1014, y_placa=92, scanlines=True,
         variante=dict(ceu='noite', carro=10),
         gancho=['OVERTAKE', 'ON THE SNARE'], sub_gancho='COUNT WITH ME',
         pergunta='TECHNO OR HARDSTYLE?',
         secoes=J(('techno', 4), 'B', ('trance', 6), 'B', ('hardstyle', 7)),
         titulo='Every overtake lands on the snare'),
    dict(id='r15', cena='corrida', paleta='deserto', seed=1015, y_placa=92,
         variante=dict(ceu='deserto', carro=15),
         gancho=['DESERT RACE', 'BAILE FUNK'], sub_gancho='REGGAETON TO DNB',
         pergunta='FUNK OR DRUM AND BASS?',
         secoes=J(('dembow', 4), ('funk', 5), 'B', ('trap', 5), 'B', ('dnb', 6)),
         titulo='A desert race to Brazilian funk 🏜️'),
    # cidade (r16-r18) saiu em 22/10/2026: prédios pulando como equalizador não
    # têm protagonista, objetivo nem progressão. Visualizador abstrato não é vídeo.
    # ---------------------------------------------------------------- plataforma
    dict(id='r19', cena='plataforma', paleta='floresta', seed=1019, scanlines=True,
         variante=dict(fundo='colinas', roupa=10, espinho=15),
         gancho=['HE JUMPS', 'ON THE KICK'], sub_gancho='NEVER MISSES',
         pergunta='CAN YOU JUMP ALONG?',
         secoes=J(('chiptune', 4, 132), 'B', ('chiptune', 6, 160), 'B', ('dnb', 6)),
         titulo='He jumps exactly on the kick 🎮'),
    dict(id='r20', cena='plataforma', paleta='noite_cidade', seed=1020,
         variante=dict(fundo='cidade', roupa=9, espinho=10),
         gancho=['NOT ONE', 'MISSED JUMP'], sub_gancho='PROVE ME WRONG',
         pergunta='DID HE MISS ANY?',
         secoes=J(('house', 4), 'B', ('techno', 6), 'B', ('dnb', 8)),
         titulo='Not a single missed jump (124 → 174 BPM)'),
    dict(id='r21', cena='plataforma', paleta='uva', seed=1021,
         variante=dict(fundo='colinas', roupa=12, espinho=9),
         gancho=['JUMP TO', 'THE FUNK'], sub_gancho='FUNK TO HARDSTYLE',
         pergunta='FUNK, PHONK OR HARDSTYLE?',
         secoes=J(('funk', 5), 'B', ('phonk', 5, 140), 'B', ('hardstyle', 7)),
         titulo='Jumping from funk to hardstyle'),
    # ---------------------------------------------------------------- bolinha
    dict(id='r22', cena='bolinha', paleta='neon', seed=1022, variante=dict(fundo='grade'),
         gancho=['THE BALL', 'IS THE SONG'], sub_gancho='EVERY BOUNCE IS A NOTE',
         pergunta='IS THE MELODY STUCK IN YOUR HEAD?',
         secoes=J(('trance', 4), 'B', ('trance', 8), fim=2),
         titulo='The ball that plays the song 🎵'),
    dict(id='r23', cena='bolinha', paleta='espaco', seed=1023, variante=dict(fundo='estrelas'),
         gancho=['EACH BOUNCE', 'IS A NOTE'], sub_gancho='LO-FI TO FUTURE',
         pergunta='LO-FI OR FUTURE BASS?',
         secoes=J(('lofi', 3), ('synthwave', 4), 'B', ('future', 8)),
         titulo='Every bounce is a note of the melody (80 → 150 BPM)'),
    dict(id='r24', cena='bolinha', paleta='sangria', seed=1024, variante=dict(fundo='bolhas'), scanlines=True,
         gancho=['LISTEN TO', 'THE MELODY'], sub_gancho='AND WATCH THE BALL',
         pergunta='CAN YOU HUM ALONG?',
         secoes=J(('chiptune', 4, 128), 'B', ('house', 5), 'B', ('chiptune', 6, 160)),
         titulo='Watch the ball, hear the melody'),
    # ---------------------------------------------------------------- pistas
    dict(id='r25', cena='pistas', paleta='neon', seed=1025,
         gancho=['CAN YOU', 'PLAY THIS?'], sub_gancho='4 LANES',
         pergunta='WHICH LANE IS THE HARDEST?',
         secoes=J(('house', 4), 'B', ('dubstep', 5), 'B', ('dnb', 7)),
         titulo='Can you play this rhythm? 🥁'),
    dict(id='r26', cena='pistas', paleta='carvao', seed=1026, variante=dict(quarta='baixo'), scanlines=True,
         gancho=['EVERY GENRE', 'HAS A GROOVE'], sub_gancho='WATCH THE HI-HAT',
         pergunta='WHICH GROOVE IS HARDEST?',
         secoes=J(('trap', 4), ('phonk', 4), 'B', ('gabber', 7)),
         titulo='The groove of each genre, note by note'),
    dict(id='r27', cena='pistas', paleta='menta', seed=1027,
         gancho=['REGGAETON', 'FUNK, TECHNO'], sub_gancho='SEE THE DIFFERENCE',
         pergunta='WHICH ONE DO YOU DANCE TO?',
         secoes=J(('dembow', 4), ('funk', 5), 'B', ('techno', 7)),
         titulo='Reggaeton vs funk vs techno: see the rhythm 🥁'),
    # ---------------------------------------------------------------- túnel
    dict(id='r28', cena='tunel', paleta='espaco', seed=1028, scanlines=True,
         variante=dict(lados=[4, 6, 3, 8], cores=[12, 9, 15, 6]),
         gancho=['ENTER', 'THE TUNNEL'], sub_gancho='HEADPHONES ON',
         pergunta='HOW MANY PORTALS DID YOU PASS?',
         secoes=J(('trance', 4), 'B', ('trance', 6), 'B', ('hardstyle', 7)),
         titulo='Enter the rhythm tunnel (138 → 150 BPM)'),
    dict(id='r29', cena='tunel', paleta='sangria', seed=1029,
         variante=dict(lados=[6, 3, 4, 6], cores=[9, 12, 10, 11]),
         gancho=['EACH PORTAL', 'IS A BEAT'], sub_gancho='',
         pergunta='DUBSTEP OR DRUM AND BASS?',
         secoes=J(('dubstep', 5), 'B', ('dubstep', 4), 'B', ('dnb', 8)),
         titulo='Every portal is a beat 🌀'),
    dict(id='r30', cena='tunel', paleta='gelo', seed=1030,
         variante=dict(lados=[3, 4, 6, 8, 4], cores=[11, 9, 12, 15, 10]),
         gancho=['TUNNEL', 'AT 190 BPM'], sub_gancho='MAKE IT TO THE END?',
         pergunta='DID YOU MAKE IT?',
         secoes=J(('synthwave', 4), 'B', ('future', 6), 'B', ('gabber', 8)),
         titulo='A tunnel that speeds up to 190 BPM'),
]

# nenhuma combinação (cena, paleta) repete
assert len({(p['cena'], p['paleta']) for p in PLANO}) == len(PLANO)
assert len({p['seed'] for p in PLANO}) == len(PLANO)
assert len(PLANO) == 27
# desenhos da lousa: nenhum repete entre os três vídeos e todos da lista boa
_des = [d for p in PLANO if p['cena'] == 'lousa' for d in p['variante']['desenhos']]
assert len(_des) == len(set(_des)) and all(d in DESENHOS_OK for d in _des)
