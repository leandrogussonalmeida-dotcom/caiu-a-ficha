#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — episódio 01: How a car engine works (o motor de 4 tempos).

O roteiro é dado, não código: capítulos, trilha de cada um e legendas com o
instante (em segundos, relativos ao começo do capítulo). O desenho de cada
capítulo mora em `ep01_motor.py`; o verificador (`longo_verificar.py`)
reprova legenda que não cabe, caractere sem glifo e fato sem fonte.

Legenda: até 2 linhas, até 37 caracteres na fonte 2x (448 px). Palavra entre
asteriscos sai em amarelo. Mínimo de leitura: 4 s por legenda.

FATOS E FONTES (cada número na tela aponta para uma destas):
  F1  4 tempos: admissão, compressão, combustão/potência, escape; válvula
      de admissão aberta na admissão, as duas fechadas na compressão e na
      potência, a de escape aberta no escape. Um ciclo = 2 voltas do
      virabrequim.  Britannica, "four-stroke cycle"; Wikipedia, "Four-stroke engine".
  F2  O comando de válvulas gira a metade da velocidade do virabrequim.
      Wikipedia, "Camshaft" ("geared to rotate at half the speed of the crankshaft").
  F3  Taxa de compressão de motor a gasolina de carro: entre 8:1 e 12:1.
      Wikipedia, "Compression ratio".
  F4  A faísca acontece antes do ponto morto superior (~20° antes).
      Univ. of Windsor, "Four Stroke Cycle Engines" (manual, via courses.washington.edu).
  F5  Marcha lenta típica: 600 a 1.000 RPM. MechanicBase, "What RPM should a car idle at?".
  F6  A 3.000 RPM: 50 voltas/s, 1 ignição a cada 2 voltas = 25 por segundo
      por cilindro; a 6.000, 50. (conta, a partir de F1)
  F7  Volante: mantém o momento entre os impulsos. Univ. of Windsor (idem F4).
  F8  Ordem de ignição mais comum do 4 cilindros em linha: 1-3-4-2.
      Rick's Free Auto Repair Advice, "What is the firing order for a 4-cylinder engine".
  F9  Só 12-30% da energia do combustível move o carro (combinado 16-25%);
      perdas no motor 68-72% no uso combinado, principalmente calor.
      fueleconomy.gov (U.S. DOE), "Where the Energy Goes: Gasoline Vehicles".
  F10 Otto construiu um motor de quatro tempos em 1876 ("ciclo Otto").
      Britannica, "Nikolaus Otto".
  F11 Injeção direta: o injetor joga gasolina dentro do cilindro; e o motor
      de Otto (1876) foi o primeiro a comprimir a mistura antes de queimar,
      "far more efficient". Wikipedia, "Four-stroke engine".
"""

TITULO = "How a Car Engine Works | The Four-Stroke Cycle in Pixel Art"

# trilha de cada capítulo: gênero, compassos, papel ('drop' = groove calmo do
# gênero, 'break' = só pad e melodia). Duração do capítulo = compassos x 4 x 60/bpm.
CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),          # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),          # 6 s
    dict(id='carro', gen='lofi', bars=12, papel='drop'),           # 36 s
    dict(id='pecas', gen='synthwave', bars=28, papel='drop'),      # 67,2 s (7 peças x 4 compassos)
    dict(id='admissao', gen='lofi', bars=12, papel='drop'),        # 36 s
    dict(id='compressao', gen='lofi', bars=12, papel='drop'),      # 36 s
    dict(id='potencia', gen='lofi', bars=12, papel='drop'),        # 36 s
    dict(id='escape', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='ciclo', gen='lofi', bars=4, papel='break'),           # 12 s
    dict(id='batidas', gen='house', bars=16, papel='drop', bpm=120),   # 32 s
    dict(id='rpm', gen='synthwave', bars=18, papel='break'),       # 43,2 s
    dict(id='cilindros', gen='lofi', bars=20, papel='drop'),       # 60 s
    dict(id='energia', gen='lofi', bars=12, papel='break'),        # 36 s
    dict(id='resumo', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),             # 15 s (tela final do YouTube)
]

# legendas: capítulo -> [(início, fim, linha1, linha2, fatos)]
LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "INSIDE A CAR ENGINE, FUEL BURNS", "IN A FLASH, OVER AND OVER.", ()),
        (6.0, 11.6, "AT 3,000 RPM: *25 TIMES A SECOND*", "IN EVERY CYLINDER.", ('F6',)),
    ],
    'carro': [
        (1.0, 8.5, "THIS IS A GASOLINE (PETROL) CAR.", "LET'S SEE WHAT MOVES IT.", ()),
        (9.0, 17.5, "UNDER THE HOOD: THE *ENGINE*.", "MANY CARS HAVE 4 CYLINDERS IN A ROW.", ()),
        (18.0, 27.5, "EACH CYLINDER DOES THE SAME JOB,", "JUST AT A DIFFERENT MOMENT.", ('F8',)),
        (28.0, 35.5, "LET'S OPEN *ONE CYLINDER*.", "", ()),
    ],
    'pecas': [
        (0.3, 9.4, "THE *CYLINDER*: A STRONG METAL TUBE.", "EVERYTHING HAPPENS IN HERE.", ()),
        (9.9, 19.0, "THE *PISTON* SLIDES UP AND DOWN.", "RINGS AROUND IT SEAL THE GAP.", ()),
        (19.5, 28.6, "THE *CONNECTING ROD* LINKS THE", "PISTON TO THE CRANKSHAFT.", ()),
        (29.1, 38.2, "THE *CRANKSHAFT* TURNS UP-AND-DOWN", "MOTION INTO ROTATION.", ()),
        (38.7, 47.8, "*VALVES*: INTAKE LETS AIR AND FUEL", "IN, EXHAUST LETS BURNT GAS OUT.", ('F1',)),
        (48.3, 57.4, "THE *CAMSHAFTS* PUSH THE VALVES OPEN,", "TURNING AT HALF THE CRANK'S SPEED.", ('F2',)),
        (57.9, 67.0, "THE *SPARK PLUG* MAKES A TINY SPARK", "THAT LIGHTS THE MIXTURE.", ()),
    ],
    'admissao': [
        (3.0, 13.5, "THE PISTON MOVES DOWN AND THE", "*INTAKE VALVE* OPENS.", ('F1',)),
        (14.0, 24.5, "AIR AND FUEL ARE DRAWN INTO", "THE CYLINDER.", ('F1',)),
        (25.0, 35.6, "(SOME ENGINES SPRAY THE FUEL", "STRAIGHT INTO THE CYLINDER.)", ('F11',)),
    ],
    'compressao': [
        (3.0, 13.5, "*BOTH VALVES CLOSE.*", "THE PISTON MOVES BACK UP.", ('F1',)),
        (14.0, 24.5, "THE MIXTURE IS SQUEEZED INTO A SPACE", "ABOUT *8 TO 12 TIMES* SMALLER.", ('F3',)),
        (25.0, 35.6, "SQUEEZING IT FIRST MAKES THE ENGINE", "FAR MORE EFFICIENT.", ('F11',)),
    ],
    'potencia': [
        (3.0, 12.0, "JUST BEFORE THE PISTON REACHES THE", "TOP, THE *SPARK PLUG* FIRES.", ('F4',)),
        (12.5, 22.5, "THE MIXTURE BURNS IN A FLASH. HOT", "GAS EXPANDS AND PUSHES THE PISTON.", ('F1',)),
        (23.0, 35.6, "THIS IS THE *ONLY STROKE*", "THAT MAKES POWER.", ('F1',)),
    ],
    'escape': [
        (3.0, 13.5, "THE *EXHAUST VALVE* OPENS.", "THE PISTON MOVES UP AGAIN.", ('F1',)),
        (14.0, 24.5, "IT PUSHES THE BURNT GAS OUT", "TO THE EXHAUST PIPE.", ('F1',)),
        (25.0, 35.6, "THEN THE WHOLE CYCLE", "STARTS AGAIN.", ()),
    ],
    'ciclo': [
        (0.5, 11.6, "4 STROKES = *2 CRANKSHAFT TURNS*.", "ONE FULL CYCLE.", ('F1',)),
    ],
    'batidas': [
        (0.5, 10.5, "4 STROKES, 4 BEATS: ONE STROKE", "ON EVERY BEAT OF THIS MUSIC.", ()),
        (11.0, 21.0, "AT THIS TEMPO THE CRANKSHAFT TURNS", "60 TIMES A MINUTE: *60 RPM*.", ('F1',)),
        (21.5, 31.6, "A REAL ENGINE IS MUCH FASTER.", "LET'S SPEED IT UP.", ()),
    ],
    'rpm': [
        (6.0, 14.0, "*800 RPM*: ABOUT IDLE, LIKE WAITING", "AT A RED LIGHT (600-1,000 RPM).", ('F5',)),
        (20.0, 29.5, "*3,000 RPM*: EACH CYLINDER FIRES", "25 TIMES EVERY SECOND.", ('F6',)),
        (35.0, 42.8, "*6,000 RPM*: 50 TIMES A SECOND.", "TOO FAST TO SEE: WE DRAW IT BLURRED.", ('F6',)),
    ],
    'cilindros': [
        (0.5, 11.5, "ONLY 1 STROKE IN 4 PUSHES.", "SO WHAT KEEPS IT TURNING?", ('F1',)),
        (12.0, 23.5, "A HEAVY *FLYWHEEL* ON THE CRANKSHAFT", "KEEPS IT SPINNING BETWEEN PUSHES.", ('F7',)),
        (24.0, 35.5, "AND *MORE CYLINDERS*: IN A 4-CYLINDER", "ENGINE, THEY TAKE TURNS.", ()),
        (36.0, 47.5, "A COMMON FIRING ORDER IS *1-3-4-2*.", "ONE CYLINDER IS ALWAYS PUSHING.", ('F8',)),
        (48.0, 59.6, "LISTEN: EACH CYLINDER'S SPARK", "PLAYS ITS OWN NOTE.", ()),
    ],
    'energia': [
        (0.5, 11.5, "WHERE DOES THE FUEL'S ENERGY GO?", "", ()),
        (12.0, 23.5, "IN A TYPICAL GASOLINE CAR, ONLY ABOUT", "*12-30%* MOVES IT DOWN THE ROAD.", ('F9',)),
        (24.0, 35.6, "MOST IS LOST IN THE ENGINE,", "MAINLY AS *HEAT*.", ('F9',)),
    ],
    'resumo': [
        (0.5, 11.5, "NIKOLAUS OTTO BUILT A FOUR-STROKE", "ENGINE IN *1876*. THE IDEA STILL RUNS.", ('F10',)),
        (12.0, 23.5, "MECHANICS HAVE A NICKNAME FOR IT:", "", ()),
        (23.5, 35.6, "*SUCK, SQUEEZE, BANG, BLOW.*", "", ()),
    ],
}

FONTES = {
    'F1': ('Encyclopaedia Britannica, "four-stroke cycle"', 'https://www.britannica.com/technology/four-stroke-cycle'),
    'F2': ('Wikipedia, "Camshaft"', 'https://en.wikipedia.org/wiki/Camshaft'),
    'F3': ('Wikipedia, "Compression ratio"', 'https://en.wikipedia.org/wiki/Compression_ratio'),
    'F4': ('University of Windsor, "Four Stroke Cycle Engines"',
           'https://courses.washington.edu/engr100/Section_Wei/engine/UofWindsorManual/Four%20Stroke%20Cycle%20Engines.htm'),
    'F5': ('MechanicBase, "What RPM Should a Car Idle at?"', 'https://mechanicbase.com/?p=34863'),
    'F6': ('Calculation from the four-stroke cycle (1 firing every 2 crankshaft turns)', None),
    'F7': ('University of Windsor, "Four Stroke Cycle Engines"',
           'https://courses.washington.edu/engr100/Section_Wei/engine/UofWindsorManual/Four%20Stroke%20Cycle%20Engines.htm'),
    'F8': ('Rick\'s Free Auto Repair Advice, "Firing order for a 4-cylinder engine"',
           'https://ricksfreeautorepairadvice.com/what-is-the-firing-order-for-a-4-cylinder-engine/'),
    'F9': ('fueleconomy.gov (U.S. Department of Energy), "Where the Energy Goes: Gasoline Vehicles"',
           'https://www.fueleconomy.gov/feg/atv.shtml'),
    'F10': ('Encyclopaedia Britannica, "Nikolaus Otto"', 'https://www.britannica.com/biography/Nikolaus-Otto'),
    'F11': ('Wikipedia, "Four-stroke engine"', 'https://en.wikipedia.org/wiki/Four-stroke_engine'),
}

DESCRICAO = """How does a car engine actually work? We take one cylinder apart, block by block, and run it in slow motion: intake, compression, power, exhaust. Then we speed it up to real engine speed, add three more cylinders, and follow where the fuel's energy really goes.

Every frame is pixel art drawn by code, and the music is original. In one part, the engine runs exactly on the beat: four strokes, four beats.

Chapters
{capitulos}

Simplified on purpose
- We show 2 valves per cylinder; many engines have 4 (2 intake, 2 exhaust).
- Real valves open a little before and close a little after the strokes; we show them opening and closing at the stroke boundaries.
- Spark timing changes with engine speed; it is shown about 20 degrees before the top.
- The energy split shown (about 70% engine losses, 20% to the wheels, 10% other) is the combined city and highway range from the U.S. Department of Energy.

Sources
{fontes}

#engine #howitworks #pixelart #cars #science"""
