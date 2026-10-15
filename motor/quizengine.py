#!/usr/bin/env python3
"""quizengine v2 - videos de quiz gerados inteiramente por codigo.

  python3 quizengine.py render <deck.json> <dir>              video 16:9
  python3 quizengine.py short  <deck.json> <dir> [i0] [i1]    Short 9:16
  python3 quizengine.py srt      <deck.json> <dir>            legendas para o yovoice (Import subtitles)
  python3 quizengine.py narracao <deck.json> <dir>            exporta o roteiro para voz propria
  python3 quizengine.py verify <dir>                          medicao e checagens
  python3 quizengine.py split  <dir>                          partes de 28 MB + .bat

Cada quadro, cada som e cada palavra falada nascem aqui. O SEED sorteia fundo,
paleta, trilha, kit de percussao, voz e transicoes, entao dois videos nunca
saem iguais. Registre o SEED usado de cada video na receita tecnica.
"""
import sys, os, json, math, subprocess, numpy as np
import fontes as FT
import quizaudio as A
import quizbg as BG

SR = 48000
FPS = 30
SEED = int(os.environ.get('SEED', 0))
VOZ = os.environ.get('VOZ', '')          # faber | cadu | jeff | dora | '' = sorteia
SEM_VOZ = os.environ.get('SEM_VOZ', '') == '1'
NARR = os.environ.get('NARR', '')        # pasta de onde vêm os .wav de narração
VELOC = float(os.environ.get('VELOC', 1.0))   # acelera a voz sem mudar o tom
REUSO = os.environ.get('REUSO', '') == '1'    # Short reaproveita a fala do longo

F_HEAVY = FT.f('Poppins-Bold.ttf')
F_MED = FT.f('Inter-SemiBold.otf')
F_TXT = FT.f('Inter-Medium.otf')

PAD_Q = .35          # respiro depois da pergunta falada
PAD_O = .30          # respiro depois das alternativas faladas
REV_HOLD = 1.5       # revelacao antes de a explicacao entrar
OUT_S = .45


# =============================================================== narração
def narration_plan(deck, idxs, curto=False):
    """Textos falados de cada pergunta. No Short a fala é enxuta: a pergunta e a
    resposta com uma explicação curta, porque o formato tem 60 s de teto."""
    L = 'ABCDEFG'
    out = {}
    for k in idxs:
        q = deck['perguntas'][k]
        fala_q = q.get('fala_q') or q['q'].replace('___', 'o quê')
        certo = q.get('fala_ok') or f"É a letra {L[q['ok']]}: {q['opts'][q['ok']]}."
        if curto and not REUSO:
            out[k] = dict(q=fala_q, opts='', rev=f"{certo} {q.get('fato_curto', '')}".strip())
        elif curto:
            # reuso: a fala é a mesma do vídeo longo, então o .wav já gravado
            # serve sem regravar nada. As alternativas ficam de fora: no Short
            # elas cabem na tela e ler as três queima 8 s dos 60.
            out[k] = dict(q=fala_q, opts='', rev=f"{certo} {q.get('fato','')}")
        else:
            opts = '. '.join(f'{L[i]}: {o}' for i, o in enumerate(q['opts']))
            out[k] = dict(q=fala_q, opts=opts, rev=f"{certo} {q.get('fato','')}")
    return out


def fala_abertura(deck, curto=False):
    """Texto falado na abertura. O Short tem abertura propria quando o deck
    define `intro_short`: a do longo anuncia 30 perguntas e nao serve em 60 s."""
    if curto:
        # chave presente e vazia desliga a fala: é o caso do Short, em que a
        # vinheta da marca já faz a abertura e sobra tempo para o conteúdo
        if 'fala_intro_short' in deck: return deck['fala_intro_short'] or ''
        c = deck.get('intro_short')
        if c: return c
    return deck.get('fala_intro') or deck.get('intro', '')


def fala_fecho(deck, curto=False):
    """Idem para o encerramento."""
    if curto:
        if 'fala_outro_short' in deck: return deck['fala_outro_short'] or ''
        c = deck.get('outro_short')
        if c: return c
    return deck.get('fala_outro') or deck.get('outro', '')


def arquivo_narracao(key):
    """Nome de arquivo seguro no Windows para a chave de um trecho."""
    return key.replace(':', '-') + '.wav'


def acelerar(p, fator, cache):
    """Acelera um WAV sem subir o tom, com o atempo do ffmpeg. Encadeia
    fatores quando passa de 2x, que é o limite de um atempo só."""
    if abs(fator - 1.0) < .01: return p
    os.makedirs(cache, exist_ok=True)
    dst = os.path.join(cache, f'{fator:.3f}_' + os.path.basename(p))
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(p): return dst
    f, cad = fator, []
    while f > 2.0: cad.append(2.0); f /= 2.0
    while f < 0.5: cad.append(0.5); f /= 0.5
    cad.append(f)
    filtro = ','.join(f'atempo={x:.4f}' for x in cad)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-filter:a', filtro, dst],
                   check=True)
    return dst


def carregar_externo(D, key):
    """Lê um WAV de narração própria, se existir em <dir>/narracao/.
    É assim que a sua voz gravada (ou clonada) entra no lugar da sintética.
    NARR aponta para outra pasta — é o que deixa o Short reaproveitar a
    narração que já foi gerada para o vídeo longo, sem regravar."""
    base = NARR or D
    p = os.path.join(base, 'narracao', arquivo_narracao(key))
    if not os.path.exists(p): return None
    if VELOC != 1.0:
        p = acelerar(p, VELOC, os.path.join(D, '_veloc'))
    import soundfile as sf, scipy.signal as sg
    a, sr = sf.read(p, dtype='float32', always_2d=True)
    a = a.mean(1)
    if sr != SR: a = sg.resample_poly(a, SR, sr).astype(np.float32)
    m = np.abs(a).max()
    if m > 0: a = a * (0.72 / m)
    return a.astype(np.float32), len(a) / SR


def exportar_roteiro(deck_path, D, vertical=False, i0=None, i1=None):
    """Escreve <dir>/narracao/ com um .txt por trecho e os scripts que o
    yovoice (ou qualquer TTS de linha de comando) roda em cima deles.

    O motor não fala com o yovoice: ele só consome os .wav que aparecerem
    nessa pasta. Isso vale igual para voz clonada e para voz gravada por você,
    e não prende o canal a nenhuma ferramenta."""
    deck = json.load(open(deck_path, encoding='utf-8'))
    checar_deck(deck, deck_path)
    n = len(deck['perguntas'])
    if i0 is None:
        idxs = list(range(n))
    elif isinstance(i0, str) and ',' in i0:
        # lista explícita: no Short as melhores perguntas quase nunca são
        # vizinhas, então faixa contínua desperdiça o formato
        idxs = [int(x) for x in i0.split(',') if x.strip() != '']
    else:
        idxs = list(range(int(i0), min(int(i1) + 1, n)))
    idxs = [k for k in idxs if 0 <= k < n]
    plan = narration_plan(deck, idxs, vertical)
    nd = os.path.join(D, 'narracao'); os.makedirs(nd, exist_ok=True)
    itens = [('intro', fala_abertura(deck, vertical)),
             ('outro', fala_fecho(deck, vertical))]
    for k in idxs:
        for part in ('q', 'opts', 'rev'):
            itens.append((f'{k}:{part}', plan[k][part]))
    itens = [(k, t) for k, t in itens if t.strip()]

    manifesto, roteiro = [], []
    for key, txt in itens:
        base = arquivo_narracao(key)[:-4]
        open(f'{nd}/{base}.txt', 'w', encoding='utf-8').write(txt + '\n')
        manifesto.append(dict(chave=key, arquivo=base + '.wav', texto=txt))
        roteiro.append(base)
    json.dump(manifesto, open(f'{nd}/manifesto.json', 'w'), indent=1, ensure_ascii=False)

    # --- yovoice: clonagem a partir de uma referência de 1 a 60 s
    # .bat autossuficiente. Usa sub-rotina em vez de if/else numa linha so:
    # o & dentro de parenteses quebra o set /a no cmd do Windows.
    ref_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voz-referencia-aprovada.wav')
    ref_nome = 'voz-referencia.wav'
    if os.path.exists(ref_src):
        import shutil; shutil.copy(ref_src, os.path.join(nd, ref_nome))

    bat = [
        '@echo off', 'setlocal enabledelayedexpansion', 'chcp 65001 >nul',
        'cd /d "%~dp0"',
        'set "REF=' + ref_nome + '"',
        'if "%MODELO%"=="" set "MODELO=qwen3-tts-1.7b-base-q8"',
        'echo ============================================',
        'echo  Gerando a narracao na sua voz',
        'echo ============================================', 'echo.',
        '',
        'rem --- procura o yovoice.exe de verdade (dir /s /b so lista o que existe)',
        'if defined YV goto :achou_yv',
        'where yovoice.exe >nul 2>&1 && set "YV=yovoice.exe" && goto :achou_yv',
        'echo Procurando o yovoice.exe...',
        'for %%R in ("%USERPROFILE%\\Downloads" "%LOCALAPPDATA%\\Programs" "%USERPROFILE%\\Desktop" "%USERPROFILE%\\Documents" "%ProgramFiles%") do (',
        '  if not defined YV for /f "delims=" %%F in (\'dir /s /b "%%~R\\yovoice.exe" 2^>nul\') do (',
        '    if not defined YV set "YV=%%F"',
        '  )',
        ')',
        'if not defined YV for /f "delims=" %%F in (\'dir /s /b "%SystemDrive%\\yovoice.exe" 2^>nul\') do (',
        '  if not defined YV set "YV=%%F"',
        ')',
        'if not defined YV goto :sem_yovoice',
        ':achou_yv',
        'if not exist "%YV%" goto :sem_yovoice',
        'if not exist "%REF%" goto :sem_ref',
        'echo yovoice : %YV%',
        'echo voz     : %REF%',
        'echo modelo  : %MODELO%',
        'echo.',
        '',
        'set /a FEITOS=0',
        'set /a PULADOS=0',
        'set /a ERROS=0',
        'set "PRIMEIRO=1"',
        '',
    ]
    for b_ in roteiro:
        bat.append(f'call :gera "{b_}"')
    bat += [
        '',
        'goto :fim',
        '',
        ':gera',
        'set "N=%~1"',
        'if exist "!N!.wav" (',
        '  set /a PULADOS+=1',
        '  goto :eof',
        ')',
        'echo   [gerando] !N!',
        'if "!PRIMEIRO!"=="1" (',
        '  "%YV%" generate --model %MODELO% --reference "%REF%" --text-file "!N!.txt" --output "!N!.wav"',
        ') else (',
        '  "%YV%" generate --model %MODELO% --reference "%REF%" --text-file "!N!.txt" --output "!N!.wav" >nul 2>&1',
        ')',
        'if exist "!N!.wav" (',
        '  set /a FEITOS+=1',
        '  set "PRIMEIRO=0"',
        ') else (',
        '  set /a ERROS+=1',
        '  if "!PRIMEIRO!"=="1" goto :falha_primeira',
        ')',
        'goto :eof',
        '',
        ':falha_primeira',
        'echo.',
        'echo ============================================',
        'echo  A PRIMEIRA GERACAO FALHOU. Parei aqui.',
        'echo  O erro do yovoice esta logo acima desta linha.',
        'echo ============================================',
        'echo.',
        'echo Modelos instalados nesta maquina:',
        '"%YV%" models list',
        'echo.',
        'echo Se o modelo %MODELO% nao estiver na lista, rode assim,',
        'echo trocando pelo nome exato que aparecer:',
        'echo.',
        'echo    set MODELO=nome-do-modelo',
        'echo    GERAR_VOZ.bat',
        'echo.',
        'pause',
        'exit /b 1',
        '',
        ':sem_yovoice',
        'echo.',
        'echo ============================================',
        'echo  NAO ACHEI o yovoice.exe no seu computador.',
        'echo ============================================',
        'echo.',
        'echo Procurei em Downloads, Programas, Area de Trabalho, Documentos',
        'echo e no disco inteiro, e nao encontrei nenhum yovoice.exe.',
        'echo.',
        'echo O QUE FAZER:',
        'echo  1. Ache o arquivo yovoice.exe no seu computador',
        'echo     (ele veio no zip yovoice-v0.2.0-cli-windows-x64)',
        'echo  2. Clique na barra de endereco da pasta onde ele esta e copie o caminho',
        'echo  3. Abra o Prompt de Comando NESTA pasta e rode:',
        'echo.',
        'echo     set YV=C:\\caminho\\que\\voce\\copiou\\yovoice.exe',
        'echo     GERAR_VOZ.bat',
        'echo.',
        'pause',
        'exit /b 1',
        '',
        ':sem_ref',
        'echo NAO ACHEI o arquivo %REF% nesta pasta.',
        'pause',
        'exit /b 1',
        '',
        ':fim',
        'echo.',
        'echo ============================================',
        'echo  Gerados: !FEITOS!   Ja existiam: !PULADOS!   Falharam: !ERROS!',
        'echo ============================================',
        'if !ERROS! GTR 0 echo Rode de novo: ele pula os que ja ficaram prontos.',
        'echo.',
        'pause',
    ]
    open(f'{nd}/GERAR_VOZ.bat', 'w', newline='', encoding='utf-8').write('\r\n'.join(bat))

    # --- guia de gravação, para quem for narrar na própria voz
    guia = ['ROTEIRO DE NARRACAO — ' + (deck.get('titulo') or ''), '',
            f'{len(itens)} trechos. Grave cada um como o arquivo .wav indicado,',
            'na mesma pasta. O motor usa o que encontrar aqui e sintetiza o resto.', '',
            'Deixe meio segundo de silencio no comeco e no fim de cada trecho.', '',
            '=' * 60, '']
    for key, txt in itens:
        guia += [arquivo_narracao(key), txt, '', '-' * 60, '']
    open(f'{nd}/ROTEIRO.txt', 'w', encoding='utf-8').write('\n'.join(guia))

    dur = sum(len(t) for _, t in itens) / 14.0
    print(f'{len(itens)} trechos em {nd}')
    print(f'~{dur/60:.1f} min de fala no total')
    print('Para clonar: de dois cliques no GERAR_VOZ.bat (ele acha o yovoice e a sua voz sozinho)')
    print('Para narrar: siga o ROTEIRO.txt e grave cada arquivo')
    print('Depois, renderize normalmente: o motor acha os .wav sozinho')


def exportar_srt(deck_path, D, vertical=False, i0=None, i1=None):
    """Gera um .srt com um trecho por legenda, para o Import subtitles do yovoice.

    O yovoice Story narration importa legendas, gera a fala de cada linha com a
    voz salva e exporta a linha do tempo inteira. Uma importacao, um clique,
    um arquivo de volta. O manifesto guarda a ordem para o corte aqui."""
    deck = json.load(open(deck_path, encoding='utf-8'))
    checar_deck(deck, deck_path)
    n = len(deck['perguntas'])
    if i0 is None:
        idxs = list(range(n))
    elif isinstance(i0, str) and ',' in i0:
        # lista explícita: no Short as melhores perguntas quase nunca são
        # vizinhas, então faixa contínua desperdiça o formato
        idxs = [int(x) for x in i0.split(',') if x.strip() != '']
    else:
        idxs = list(range(int(i0), min(int(i1) + 1, n)))
    idxs = [k for k in idxs if 0 <= k < n]
    plan = narration_plan(deck, idxs, vertical)
    os.makedirs(D, exist_ok=True)

    itens = [('intro', fala_abertura(deck, vertical))]
    for k in idxs:
        for part in ('q', 'opts', 'rev'):
            itens.append((f'{k}:{part}', plan[k][part]))
    itens.append(('outro', fala_fecho(deck, vertical)))
    itens = [(k, ' '.join(t.split())) for k, t in itens if t.strip()]

    def tc(seg):
        h = int(seg // 3600); m = int(seg % 3600 // 60); s = seg % 60
        return f'{h:02d}:{m:02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}'

    CPS, GAP = 13.5, 0.9          # fala ~13,5 caracteres por segundo
    linhas, man, t = [], [], 1.0
    for i, (key, txt) in enumerate(itens, 1):
        dur = max(1.2, len(txt) / CPS)
        linhas += [str(i), f'{tc(t)} --> {tc(t + dur)}', txt, '']
        man.append(dict(n=i, chave=key, texto=txt, inicio=round(t, 3), dur=round(dur, 3)))
        t += dur + GAP

    open(f'{D}/narracao.srt', 'w', encoding='utf-8-sig').write('\n'.join(linhas))
    json.dump(man, open(f'{D}/manifesto.json', 'w'), indent=1, ensure_ascii=False)
    print(f'{len(itens)} trechos -> {D}/narracao.srt')
    print(f'duracao estimada da linha do tempo: {t/60:.1f} min')
    partes = _partir_srt(D, itens, tc)
    if partes:
        print(f'o arquivo inteiro passa do limite do yovoice; '
              f'partido em {len(partes)} partes:')
        for p, qt, ch in partes:
            print(f'  {p}  {qt} falas, {ch} caracteres')
        print('importe uma parte por vez, NA ORDEM: o resgate dos .wav casa '
              'pela ordem cronologica.')
    # NUNCA 'Export timeline': falha em projeto longo e e desnecessario -
    # o yovoice ja salva cada fala como .wav separado em ~/.yovoice/outputs.
    print('No yovoice: Story narration > Import subtitles > narrador SOSIA > Generate speech')
    print('Terminou, nao use Export timeline: os .wav de cada fala ja estao em disco.')


def _partir_srt(D, itens, tc, teto=11000):
    """O yovoice recusa legenda acima de 12.000 caracteres: 'Invalid subtitles'.
    Um deck de 30 perguntas da 13 a 19 mil, entao o arquivo inteiro nunca entra.

    Cada parte e um .srt valido por si: numeracao propria a partir de 1 e
    tempos recomecando perto do zero. Isso nao atrapalha nada, porque o que
    importa sao os .wav de cada fala, e eles sao casados pela ORDEM
    cronologica no state.json, nao pelos tempos do arquivo.

    Devolve [] quando cabe inteiro - ai nao ha motivo para partir.
    """
    CPS, GAP = 13.5, 0.9
    def bloco(i, t, txt):
        dur = max(1.2, len(txt) / CPS)
        return [str(i), f'{tc(t)} --> {tc(t + dur)}', txt, ''], dur

    inteiro = sum(len(t) for _, t in itens) + 40 * len(itens)
    if inteiro <= 12000: return []

    n_partes = math.ceil(inteiro / teto)
    por_parte = math.ceil(len(itens) / n_partes)

    # o corte cai no comeco de uma pergunta, nunca no meio dela: uma parte
    # que comecasse pelas alternativas deixaria ele sem saber onde parou.
    def inicio_de_pergunta(i):
        return i >= len(itens) or itens[i][0].endswith(':q') or itens[i][0] == 'outro'

    cortes = [0]
    for p in range(1, n_partes):
        i = min(p * por_parte, len(itens))
        while i > cortes[-1] + 1 and not inicio_de_pergunta(i):
            i -= 1
        cortes.append(i)
    cortes.append(len(itens))

    saidas = []
    for p in range(len(cortes) - 1):
        fatia = itens[cortes[p]:cortes[p + 1]]
        if not fatia: continue
        linhas, t = [], 1.0
        for i, (_, txt) in enumerate(fatia, 1):
            bl, dur = bloco(i, t, txt)
            linhas += bl
            t += dur + GAP
        nome = f'{D}/narracao-p{p + 1}.srt'
        corpo = '\n'.join(linhas)
        open(nome, 'w', encoding='utf-8-sig').write(corpo)
        saidas.append((os.path.basename(nome), len(fatia), len(corpo)))
    return saidas


def synth_all(deck, idxs, D, voice, curto=False):
    """Devolve {chave: (audio, dur)}. Um WAV em <dir>/narracao/ sempre vence
    a voz sintética: é assim que a sua voz entra sem mudar mais nada."""
    if SEM_VOZ: return {}
    cache = os.path.join(D, '_voz')
    plan = narration_plan(deck, idxs, curto)
    clips = {}
    sp = float(deck.get('velocidade_voz', 1.06))
    todo = [('intro', fala_abertura(deck, curto)),
            ('outro', fala_fecho(deck, curto))]
    for k in idxs:
        for part in ('q', 'opts', 'rev'):
            todo.append((f'{k}:{part}', plan[k][part]))
    todo = [(k, t) for k, t in todo if t.strip()]

    externos = 0
    for key, _ in todo:
        got = carregar_externo(D, key)
        if got: clips[key] = got; externos += 1
    if externos:
        print(f'narração própria: {externos} de {len(todo)} trechos vindos de narracao/', flush=True)
    faltam = [(k, t) for k, t in todo if k not in clips]
    if faltam and not voice:
        print('aviso: faltam trechos e nenhuma voz sintética escolhida'); return clips
    if faltam:
        import voice as V
        print(f'sintetizando {len(faltam)} trechos com a voz {voice}', flush=True)
        for i, (key, txt) in enumerate(faltam):
            clips[key] = V.synth_cached(txt, voice, cache, sp)
            if i % 10 == 0: print(f'  {i}/{len(faltam)}', flush=True)
    return clips


# =============================================================== linha do tempo
def build_timeline(deck, idxs, clips, curto=False):
    """Marcas absolutas de cada fase. A fala manda no ritmo."""
    def dur(key, fallback):
        return clips[key][1] if key in clips else fallback

    t = dur('intro', 0) + deck.get('intro_s', 3.0)
    tl = []
    for k in idxs:
        q = deck['perguntas'][k]
        nopt = len(q['opts'])
        d_q = dur(f'{k}:q', .8 + .055 * len(q['q']))
        d_o = dur(f'{k}:opts', 0 if curto else .55 * nopt)
        d_r = dur(f'{k}:rev', 2.2 + .045 * len(q.get('fato', '')))
        timer = float(q.get('tempo', deck.get('tempo', 6)))
        seg = dict(k=k, q=q, nopt=nopt, timer=timer, t0=t)
        hold = (1.0 if curto else REV_HOLD)
        seg['tq'] = t + (.30 if curto else .45)      # pergunta entra e começa a ser lida
        seg['topts'] = seg['tq'] + d_q + (.18 if curto else PAD_Q)
        seg['tread'] = seg['topts'] + d_o + (.22 if curto else PAD_O)
        seg['ttimer'] = seg['tread'] + timer          # revelação
        seg['tfact'] = seg['ttimer'] + hold           # explicação entra
        seg['t1'] = seg['tfact'] + max(d_r - hold, (.8 if curto else 1.2)) + OUT_S
        seg['d_r'] = d_r
        tl.append(seg); t = seg['t1']
    total = t + dur('outro', 0) + deck.get('outro_s', 4.0)
    return tl, total


# =============================================================== áudio
def build_audio(deck, tl, total, D, clips, kit):
    rng = np.random.default_rng(SEED * 31 + 7)
    key = kit['root']

    def energy(t):
        for s in tl:
            if s['t0'] <= t < s['t1']:
                if t < s['tread']: return .42
                if t < s['ttimer']: return .72 + .28 * (t - s['tread']) / max(.1, s['timer'])
                return .95 if t < s['tfact'] else .52
        return .30

    mix = A.groove(total, kit, SEED, energy)

    wh_up = A.whoosh(rng, .72, True); wh_dn = A.whoosh(rng, .55, False)
    pops = [A.pop(rng, i) for i in range(6)]
    ok_sfx = A.correct(rng, key); pg = A.page(rng, key)

    A.put(mix, A.page(rng, key) * 1.5, .25)
    for s in tl:
        A.put(mix, wh_up, s['t0'], 1.0)
        for i in range(s['nopt']):
            A.put(mix, pops[i % 6], s['topts'] + .14 * i, .95, -.32 + .64 * i / max(1, s['nopt'] - 1))
        n_tick = int(round(s['timer']))
        for i in range(n_tick):
            A.put(mix, A.tick(rng, i, n_tick), s['tread'] + i, 1.0)
        rz = min(1.6, s['timer'] * .42)
        A.put(mix, A.riser(rng, rz, key), s['ttimer'] - rz, .95)
        A.put(mix, ok_sfx, s['ttimer'], 1.0)
        A.put(mix, pg, s['tfact'], .85)
        A.put(mix, wh_dn, s['t1'] - OUT_S, .55)
    A.put(mix, A.fanfare(rng, key, kit), max(0, total - 5.0), 1.0)

    # --- narração por cima, com a trilha abaixando sob a voz
    spoken = []
    if clips:
        def lay(key_, t0, gain=1.0):
            if key_ not in clips: return
            a, d = clips[key_]
            i = int(t0 * SR); j = min(i + len(a), len(mix))
            if j > i:
                mix[i:j, 0] += a[:j - i] * gain; mix[i:j, 1] += a[:j - i] * gain
                spoken.append((t0, d))
        lay('intro', .9)
        for s in tl:
            lay(f"{s['k']}:q", s['tq'])
            lay(f"{s['k']}:opts", s['topts'])
            lay(f"{s['k']}:rev", s['ttimer'] + .55)
        lay('outro', tl[-1]['t1'] + .8)
        # a trilha e os efeitos já estão somados; o duck age no conjunto
        mix = A.duck(mix, spoken, depth=.42)

    mix, L, tp = A.master(mix, deck.get('lufs', -14.0))
    import soundfile as sf
    sf.write(f'{D}/audio.wav', mix, SR, subtype='PCM_24')
    return L, tp, len(spoken)


# =============================================================== layout
def layout(W, H, nopt_max):
    """Áreas de segurança. No 9:16 a interface do Shorts cobre topo, rodapé e a
    coluna de botões da direita, então nada de conteúdo fora da faixa central."""
    v = H > W
    s = W / 1080.0 if v else W / 1920.0
    L = dict(W=W, H=H, v=v, s=s)
    if v:
        L.update(head_y=int(248 * s), ring=(int(540 * s), int(398 * s), int(88 * s)),
                 card_x=int(70 * s), card_w=int(940 * s), card_y=int(520 * s),
                 opt_x=int(100 * s), opt_w=int(820 * s),
                 band_y0=int(940 * s), band_y1=int(1392 * s),
                 f_q=int(64 * s), f_o=int(46 * s), f_h=int(32 * s), f_n=int(52 * s), f_f=int(37 * s))
    else:
        L.update(head_y=int(58 * s), ring=(int(1738 * s), int(292 * s), int(96 * s)),
                 card_x=int(300 * s), card_w=int(1320 * s), card_y=int(170 * s),
                 opt_x=int(370 * s), opt_w=int(1180 * s),
                 band_y0=int(430 * s), band_y1=int(930 * s),
                 f_q=int(60 * s), f_o=int(43 * s), f_h=int(31 * s), f_n=int(48 * s), f_f=int(35 * s))
    gap = int((26 if v else 22) * s)
    band = L['band_y1'] - L['band_y0']
    L['opt_gap'] = gap
    L['opt_h'] = int(min((126 if v else 100) * s, (band - gap * (nopt_max - 1)) / nopt_max))
    return L


def wrap(d, txt, font, maxw):
    out, cur = [], ''
    for w in txt.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= maxw or not cur: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out


def fit_font(d, txt, path, size, maxw, maxlines, minsize):
    """Diminui a fonte até o texto caber nas linhas disponíveis."""
    from PIL import ImageFont
    while size > minsize:
        f = ImageFont.truetype(path, size)
        if len(wrap(d, txt, f, maxw)) <= maxlines: return f
        size -= 2
    return ImageFont.truetype(path, minsize)


def rr(d, box, r, **kw): d.rounded_rectangle(box, radius=r, **kw)


# =============================================================== camadas
def question_layers(q, n, L, pal, fonts):
    from PIL import ImageFont
    from PIL import Image, ImageDraw
    fo, fh, fn, ff = fonts[1:]
    probe = ImageDraw.Draw(Image.new('RGB', (8, 8)))
    s = L['s']
    inner = L['card_w'] - int(92 * s)
    maxlines = 3 if L['v'] else 2
    fq = fit_font(probe, q['q'], F_HEAVY, L['f_q'], inner, maxlines, int(L['f_q'] * .62))
    lines = wrap(probe, q['q'], fq, inner)
    lh = int(fq.size * 1.24)
    ch = int(78 * s) + lh * len(lines)

    card = Image.new('RGBA', (L['card_w'], ch), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    rr(d, [0, 0, L['card_w'] - 1, ch - 1], int(32 * s), fill=tuple(pal['card']) + (252,))
    y = int(38 * s)
    for ln in lines:
        d.text((L['card_w'] / 2, y), ln, font=fq, fill=tuple(pal['ink']) + (255,), anchor='ma'); y += lh

    bs = int(88 * s)
    badge = Image.new('RGBA', (bs, bs), (0, 0, 0, 0)); bd = ImageDraw.Draw(badge)
    rr(bd, [0, 0, bs - 1, bs - 1], int(24 * s), fill=tuple(pal['accent']) + (255,))
    bd.text((bs / 2, bs / 2 - int(2 * s)), str(n), font=fn, fill=(20, 16, 6, 255), anchor='mm')

    ok_col = (34, 176, 112); dim_col = (128, 126, 142)
    letters = 'ABCDEFG'
    oh = L['opt_h']; ow = L['opt_w']
    pills = []
    for i, opt in enumerate(q['opts']):
        fop = fit_font(probe, opt, F_HEAVY, L['f_o'], ow - oh - int(40 * s), 1, int(L['f_o'] * .55))
        st = []
        for mode in ('idle', 'ok', 'dim'):
            im = Image.new('RGBA', (ow, oh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            if mode == 'ok': bg, ink, edge, al = ok_col, (255, 255, 255), ok_col, 252
            elif mode == 'dim': bg, ink, edge, al = dim_col, (250, 250, 252), dim_col, 140
            else: bg, ink, edge, al = pal['card'], pal['ink'], (206, 202, 222), 250
            rr(d, [0, 0, ow - 1, oh - 1], oh // 2, fill=tuple(bg) + (al,),
               outline=tuple(edge) + (255,), width=max(2, int(3 * s)))
            m = int(12 * s)
            d.ellipse([m, m, oh - m, oh - m], fill=tuple(pal['accent'] if mode == 'idle' else ink) + (255,))
            d.text((oh / 2, oh / 2 - int(2 * s)), letters[i], font=fo,
                   fill=tuple((20, 16, 6) if mode == 'idle' else bg) + (255,), anchor='mm')
            d.text((oh + int(16 * s), oh / 2 - int(2 * s)), opt, font=fop, fill=tuple(ink) + (255,), anchor='lm')
            st.append(im)
        pills.append(st)

    fw = ow
    # no Short normal entra o fato curto; no reuso entra o longo, porque a
    # voz está lendo o longo e texto na tela tem que bater com o que se ouve
    texto_fato = (q.get('fato_curto') if L['v'] and not REUSO and q.get('fato_curto')
                  else q.get('fato', ''))
    # no 9:16 o painel só tem o que sobra entre a alternativa certa (que sobe)
    # e o fim da área de segurança: a fonte encolhe até caber, em vez de o
    # texto vazar por baixo da interface do Shorts
    if L['v']:
        topo = L['band_y0'] + L['opt_h'] + int(34 * s)
        disp = max(int(140 * s), L['band_y1'] - topo)
        tam = ff.size
        while tam > int(23 * s):
            fteste = ImageFont.truetype(F_TXT, tam)
            nl = len(wrap(probe, texto_fato, fteste, fw - int(66 * s)))
            if int(56 * s) + int(tam * 1.36) * max(1, nl) <= disp: break
            tam -= 2
        ff = ImageFont.truetype(F_TXT, tam)
    flines = wrap(probe, texto_fato, ff, fw - int(66 * s))
    flh = int(ff.size * 1.36)
    fhh = int(56 * s) + flh * max(1, len(flines))
    fact = Image.new('RGBA', (fw, fhh), (0, 0, 0, 0)); d = ImageDraw.Draw(fact)
    fbg = (14, 16, 34) if pal['dark'] else (250, 247, 238)
    fink = (228, 224, 246) if pal['dark'] else (46, 40, 34)
    rr(d, [0, 0, fw - 1, fhh - 1], int(22 * s), fill=fbg + (240,))
    d.rectangle([0, 0, int(7 * s), fhh - 1], fill=tuple(pal['accent']) + (255,))
    y = int(28 * s)
    for ln in flines:
        d.text((int(34 * s), y), ln, font=ff, fill=fink + (255,)); y += flh
    return dict(card=card, badge=badge, pills=pills, fact=fact, ch=ch)


def ring_layer(L, pal, frac, hot):
    from PIL import Image, ImageDraw
    cx, cy, R = L['ring']; S = 4; side = (2 * R + 36) * S
    im = Image.new('RGBA', (side, side), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    w = int(13 * L['s'] * S); box = [18 * S, 18 * S, side - 18 * S, side - 18 * S]
    d.ellipse(box, outline=(255, 255, 255, 52), width=w)
    if frac > 0:
        col = (240, 86, 86) if hot else tuple(pal['accent'])
        d.arc(box, -90, -90 + 360 * frac, fill=col + (255,), width=w)
    return im.resize((side // S, side // S), Image.LANCZOS), (cx - side // (2 * S), cy - side // (2 * S))


def comp(base, layer, xy, alpha=1.0):
    x, y = int(xy[0]), int(xy[1]); H, W = base.shape[:2]
    a = layer if isinstance(layer, np.ndarray) else np.asarray(layer, np.float32)
    lh, lw = a.shape[:2]
    x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + lw, W), min(y + lh, H)
    if x1 <= x0 or y1 <= y0 or alpha <= .002: return
    sub = a[y0 - y:y1 - y, x0 - x:x1 - x]
    al = (sub[..., 3:] * (alpha / 255.0))
    base[y0:y1, x0:x1] *= (1 - al); base[y0:y1, x0:x1] += sub[..., :3] * al


def arr(im): return np.asarray(im, np.float32)
def ease(u): return 1 - (1 - min(max(u, 0.0), 1.0)) ** 3
def ease_io(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)
def overshoot(u):
    u = min(max(u, 0.0), 1.0)
    return 1 + 2.2 * (u - 1) ** 3 + 1.4 * (u - 1) ** 2


# =============================================================== vídeo
def render_video(deck, tl, total, D, pal, fam, W, H, out_name):
    from PIL import Image, ImageDraw, ImageFont
    nmax = max(s['nopt'] for s in tl)
    L = layout(W, H, nmax)
    rng = np.random.default_rng(SEED * 13 + 3)
    fonts = (None, ImageFont.truetype(F_HEAVY, L['f_o']), ImageFont.truetype(F_MED, L['f_h']),
             ImageFont.truetype(F_HEAVY, L['f_n']), ImageFont.truetype(F_TXT, L['f_f']))
    fh, fn, ff = fonts[2], fonts[3], fonts[4]

    chrome = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(chrome)
    topo = deck.get('tema_curto', deck.get('tema', '')).upper()
    d.text((W / 2, L['head_y']), '   '.join(topo), font=fh, fill=tuple(pal['head']) + (205,), anchor='ma')

    # trilho da barra de progresso, no topo absoluto da tela
    bar_h = max(4, int(7 * L['s']))
    d.rectangle([0, 0, W, bar_h], fill=tuple(pal['head']) + (38,))

    vy, vx = np.mgrid[0:H, 0:W].astype(np.float32)
    vig = np.clip(1 - .48 * (((vx / W - .5) * 1.25) ** 2 + ((vy / H - .5) * 1.45) ** 2), .42, 1)[..., None]
    del vy, vx

    HOLD, NUNIQ = 4, 75        # 10 s de loop de fundo
    lows = BG.render(fam, pal, W, H, NUNIQ, SEED)
    bg = []
    for lo in lows:
        im = np.asarray(Image.fromarray(lo).resize((W, H), Image.BICUBIC), np.float32) * vig
        comp(im, arr(chrome), (0, 0))
        bg.append(np.clip(im, 0, 255).astype(np.uint8))
    del lows, vig
    print(f'fundo {fam} pronto', flush=True)

    STEPS = 48
    rings = [[tuple((arr(a), b) for a, b in [ring_layer(L, pal, i / STEPS, hot)])[0]
              for i in range(STEPS + 1)] for hot in (False, True)]
    maxt = int(math.ceil(max(s['timer'] for s in tl)))
    digits = {}
    for n in range(maxt + 1):
        im = Image.new('RGBA', (L['ring'][2] * 2, L['ring'][2] * 2), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((L['ring'][2], L['ring'][2]), str(n), font=fn,
                                fill=tuple(pal['head']) + (242,), anchor='mm')
        digits[n] = arr(im)
    print('anéis prontos', flush=True)

    TRANS = ['desliza', 'escala', 'gira', 'sobe']
    layers = {}
    # numeração pela posição no vídeo, não pelo índice no deck: um Short com
    # as perguntas 24 e 25 do deck longo tem que mostrar 1 e 2
    for pos, s in enumerate(tl, 1):
        q = dict(s['q'])
        ly = question_layers(q, pos, L, pal, fonts)
        src = ly['pills'][q['ok']][1]
        ly['pop'] = [arr(src.resize((int(src.size[0] * (1 + .07 * math.sin(math.pi * j / 10))),
                                     int(src.size[1] * (1 + .07 * math.sin(math.pi * j / 10)))), Image.BICUBIC))
                     for j in range(11)]
        for key in ('card', 'badge', 'fact'):
            ly[key] = arr(ly[key])
        ly['pills'] = [[arr(x) for x in st] for st in ly['pills']]
        ly['trans'] = TRANS[int(rng.integers(len(TRANS)))]
        layers[s['k']] = ly
    print(f'cartões prontos: {len(layers)}', flush=True)

    # --- polimento: flash da revelação, pulso do cronômetro, barra de progresso
    bar_h = max(4, int(7 * L['s']))
    barra = np.zeros((bar_h, W, 4), np.float32)
    barra[..., :3] = np.array(pal['accent'], np.float32); barra[..., 3] = 255.0

    # brilho radial curto que estoura no acerto, somado ao fundo
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
    cxf, cyf = W / 2.0, (L['band_y0'] + L['band_y1']) / 2.0
    flash = np.exp(-(((gx - cxf) / (W * .40)) ** 2 + ((gy - cyf) / (H * .26)) ** 2)).astype(np.float32)
    flash_rgb = (flash[..., None] * np.array(pal['accent'], np.float32)).astype(np.float32)
    del gy, gx

    rings_big = [[tuple((arr(a), b) for a, b in [ring_layer(L, pal, i / STEPS, True)])[0]
                  for i in range(STEPS + 1)]]
    print('polimento pronto', flush=True)

    def textcard(title, sub, big):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
        ft = fit_font(dd, title, F_HEAVY, int(big * L['s']), int(W * .84), 4, int(big * L['s'] * .5))
        lines = wrap(dd, title, ft, int(W * .84))
        lh = int(ft.size * 1.2); y = H / 2 - lh * len(lines) / 2 - int(50 * L['s'])
        for ln in lines:
            dd.text((W / 2, y), ln, font=ft, fill=tuple(pal['head']) + (255,), anchor='ma'); y += lh
        if sub:
            y += int(30 * L['s'])
            for ln in wrap(dd, sub, ff, int(W * .72))[:4]:
                dd.text((W / 2, y), ln, font=ff, fill=tuple(pal['head']) + (178,), anchor='ma')
                y += int(ff.size * 1.45)
        return arr(im)
    curto_ = L['v']
    txt_intro = (deck.get('intro_short') if curto_ and deck.get('intro_short') else deck.get('intro', ''))
    txt_outro = (deck.get('outro_short') if curto_ and deck.get('outro_short') else deck.get('outro', ''))
    intro_im = textcard(deck.get('titulo_short', deck.get('titulo', deck.get('tema', ''))) if curto_
                        else deck.get('titulo', deck.get('tema', '')), txt_intro, 86)
    outro_im = textcard(deck.get('outro_titulo', 'Quantas você acertou?'), txt_outro, 74)

    NF = int(round(total * FPS))
    ffp = subprocess.Popen(
        ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
         '-r', str(FPS), '-i', '-', '-i', f'{D}/audio.wav', '-map', '0:v', '-map', '1:a',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-g', str(FPS * 2),
         '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest', '-movflags', '+faststart',
         f'{D}/{out_name}'], stdin=subprocess.PIPE)

    si = 0
    for fi in range(NF):
        t = fi / FPS
        img = bg[(fi // HOLD) % NUNIQ].astype(np.float32)

        if t < tl[0]['t0']:
            u = min(1.0, t / 1.0) * min(1.0, (tl[0]['t0'] - t) / .55)
            comp(img, intro_im, (0, int(-26 * L['s'] * (1 - ease(min(1, t / 1.3))))), u)
        elif t >= tl[-1]['t1']:
            u = min(1.0, (t - tl[-1]['t1']) / .75)
            comp(img, outro_im, (0, int(-26 * L['s'] * (1 - ease(u)))), u)
        else:
            while si < len(tl) - 1 and t >= tl[si]['t1']: si += 1
            s = tl[si]; ly = layers[s['k']]; ok = s['q']['ok']
            fade = min(1.0, max(0.0, (s['t1'] - t) / OUT_S))

            # ---- cartão da pergunta, com a transição sorteada
            u = ease(( t - s['t0']) / .55); tr = ly['trans']
            cx, cy = L['card_x'], L['card_y']; csc = 1.0
            if tr == 'desliza': cx += int((W * .55) * (1 - u))
            elif tr == 'sobe': cy += int(120 * L['s'] * (1 - u))
            elif tr == 'escala': csc = .80 + .20 * overshoot(min(1, (t - s['t0']) / .6))
            else: cy += int(70 * L['s'] * (1 - u))
            card = ly['card']
            if abs(csc - 1) > .005:
                from PIL import Image as I
                nw, nh = int(card.shape[1] * csc), int(card.shape[0] * csc)
                card = arr(I.fromarray(card.astype(np.uint8)).resize((nw, nh), I.BICUBIC))
                cx += (ly['card'].shape[1] - nw) // 2
            comp(img, card, (cx, cy), u * fade)
            bu = min(1.0, (t - s['t0']) / .5)
            if bu < 1:
                from PIL import Image as _I
                k = overshoot(bu)
                bg_ = ly['badge']
                nb = max(8, int(bg_.shape[0] * k))
                bim = _I.fromarray(bg_.astype(np.uint8)).rotate(18 * (1 - bu), resample=_I.BICUBIC,
                                                                expand=False).resize((nb, nb), _I.BICUBIC)
                off = (nb - bg_.shape[0]) // 2
                comp(img, arr(bim), (cx - int(34 * L['s']) - off, cy - int(34 * L['s']) - off), u * fade)
            else:
                comp(img, ly['badge'], (cx - int(34 * L['s']), cy - int(34 * L['s'])), u * fade)

            # ---- alternativas
            revealed = t >= s['ttimer']
            shrink = ease_io((t - s['tfact']) / .5) if (L['v'] and t >= s['tfact']) else 0.0
            oy = L['band_y0']
            step = L['opt_h'] + L['opt_gap']
            for i, st in enumerate(ly['pills']):
                ap = (t - (s['topts'] + .14 * i)) / .34
                if ap <= 0:
                    oy += step; continue
                a = ease(ap)
                if not revealed: im = st[0]
                elif i != ok: im = st[2]
                else:
                    b = (t - s['ttimer']) / .36
                    im = ly['pop'][min(10, max(0, int(b * 10)))] if b < 1 else st[1]
                y = oy
                vis = a * fade
                if shrink > 0:                       # no 9:16 as erradas somem e a certa sobe
                    if i != ok: vis *= (1 - shrink)
                    else: y = int(oy + (L['band_y0'] - oy) * shrink)
                ox = L['opt_x'] + (L['opt_w'] - im.shape[1]) // 2
                comp(img, im, (ox, y - (im.shape[0] - L['opt_h']) // 2 + int(26 * L['s'] * (1 - a))), vis)
                oy += step

            # ---- estouro de luz no acerto (0,45 s, some rapido)
            fl = (t - s['ttimer']) / .38
            if 0 <= fl < 1:
                img += flash_rgb * (((1 - fl) ** 3) * .26)

            # ---- cronômetro
            if s['topts'] <= t < s['ttimer'] + .25:
                falta = max(0.0, s['ttimer'] - t)
                left = falta / s['timer']
                av = min(1.0, (t - s['topts']) / .3)
                quente = falta <= 2.0
                rim, rxy = rings[1 if quente else 0][min(STEPS, int(round(left * STEPS)))]
                # nos ultimos 2 s o anel pulsa uma vez por segundo
                if quente:
                    pul = .5 + .5 * math.cos(2 * math.pi * (falta % 1.0))
                    comp(img, rim, rxy, av * (.55 + .45 * pul))
                else:
                    comp(img, rim, rxy, av)
                n_seg = max(0, min(maxt, int(math.ceil(falta))))
                nd = digits[n_seg]
                if quente:
                    # o numero cresce no instante em que troca
                    k = 1.0 + .22 * (1 - min(1.0, (falta % 1.0) / .28))
                    from PIL import Image as _I
                    nw, nh = int(nd.shape[1] * k), int(nd.shape[0] * k)
                    nd2 = arr(_I.fromarray(nd.astype(np.uint8)).resize((nw, nh), _I.BICUBIC))
                    comp(img, nd2, (L['ring'][0] - nw // 2, L['ring'][1] - nh // 2), av)
                else:
                    comp(img, nd, (L['ring'][0] - L['ring'][2], L['ring'][1] - L['ring'][2]), av)

            # ---- explicação
            if t >= s['tfact']:
                a = ease((t - s['tfact']) / .45)
                if L['v']:
                    # logo abaixo da alternativa certa, que subiu para band_y0
                    fy = L['band_y0'] + L['opt_h'] + int(34 * L['s'])
                    fy = min(fy, L['band_y1'] - ly['fact'].shape[0])
                    fy = max(fy, L['band_y0'] + L['opt_h'] + int(14 * L['s']))
                    fy += int(26 * L['s'] * (1 - a))
                else:
                    # ancora abaixo da ultima alternativa, nunca por cima dela
                    last = L['band_y0'] + s['nopt'] * (L['opt_h'] + L['opt_gap'])
                    fy = max(last + int(18 * L['s']), L['band_y1'] - ly['fact'].shape[0])
                    fy += int(30 * L['s'] * (1 - a))
                comp(img, ly['fact'], (L['opt_x'] + (L['opt_w'] - ly['fact'].shape[1]) // 2, fy), a * fade)

        # --- barra de progresso: quanto do quiz ja passou
        if tl[0]['t0'] <= t < tl[-1]['t1']:
            prog = (si + ease_io((t - tl[si]['t0']) / max(.1, tl[si]['t1'] - tl[si]['t0']))) / len(tl)
            w = int(W * min(1.0, max(0.0, prog)))
            if w > 2: img[:bar_h, :w] = img[:bar_h, :w] * .12 + barra[:, :w, :3] * .88

        ffp.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
        if fi == int(NF * .42):
            Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(f'{D}/frame.png')
        if fi % 900 == 0: print(f'  quadro {fi}/{NF}', flush=True)
    ffp.stdin.close(); ffp.wait()
    print('vídeo ok', out_name, os.path.getsize(f'{D}/{out_name}') // 2 ** 20, 'MiB', NF, 'quadros')
    return NF


# =============================================================== comandos
def checar_deck(deck, path):
    """Recusa o deck antes de gastar meia hora de render. Erro de conteúdo é
    o mais caro de todos: só aparece depois do vídeo pronto."""
    erros = []
    if not deck.get('perguntas'): erros.append('deck sem perguntas')
    for i, q in enumerate(deck.get('perguntas', []), 1):
        o = q.get('opts') or []
        if len(o) < 2: erros.append(f'pergunta {i}: menos de 2 alternativas')
        if len(set(o)) != len(o):
            rep = [x for x in set(o) if o.count(x) > 1]
            erros.append(f'pergunta {i}: alternativa repetida {rep}')
        if not isinstance(q.get('ok'), int) or not 0 <= q['ok'] < len(o):
            erros.append(f'pergunta {i}: campo ok fora da faixa')
        if not (q.get('fato') or '').strip():
            erros.append(f'pergunta {i}: sem explicação (campo fato)')
        if not (q.get('q') or '').strip(): erros.append(f'pergunta {i}: sem enunciado')
    # fundo e paleta fixados no deck tem que EXISTIR. Escrever 'mapa' num
    # campo que so aceita onze familias nao da erro nenhum: o motor sorteia
    # outro pelo SEED e o video sai com a cara errada, calado. E a mesma
    # classe do valor fantasma que fez a crosta ter dois numeros diferentes.
    import quizbg as _BG
    if deck.get('fundo') and deck['fundo'] not in _BG.FAMILIAS:
        erros.append(f"fundo {deck['fundo']!r} nao existe. Ha: "
                     + ', '.join(_BG.FAMILIAS))
    if deck.get('paleta') and deck['paleta'] not in _BG.PALETAS:
        erros.append(f"paleta {deck['paleta']!r} nao existe. Ha: "
                     + ', '.join(_BG.PALETAS))
    if erros:
        raise SystemExit('DECK RECUSADO (' + path + '):\n  ' + '\n  '.join(erros))
    sem_curto = [i for i, q in enumerate(deck['perguntas'], 1) if not (q.get('fato_curto') or '').strip()]
    if sem_curto:
        print(f'aviso: {len(sem_curto)} perguntas sem fato_curto; o Short vai usar o fato longo')
    print(f'deck ok: {len(deck["perguntas"])} perguntas, todas com explicação')


def _rotulo_voz(clips, voice, D):
    """O que ficou registrado em meta.json tem que ser o que se ouve.
    Gravamos 92 falas na voz do Leandro e o meta dizia 'cadu', uma das
    vozes sinteticas: o arquivo afirmava uma coisa e o video dizia outra."""
    if not clips: return None
    proprios = sum(1 for k in clips
                   if os.path.exists(os.path.join(D, 'narracao', arquivo_narracao(k))))
    if proprios == len(clips): return 'gravada'
    if proprios: return f'gravada+{voice}'
    return voice


def render(deck_path, D, vertical=False, i0=None, i1=None):
    deck = json.load(open(deck_path, encoding='utf-8')); os.makedirs(D, exist_ok=True)
    checar_deck(deck, deck_path)
    n = len(deck['perguntas'])
    if i0 is None:
        idxs = list(range(n))
    elif isinstance(i0, str) and ',' in i0:
        # lista explícita: no Short as melhores perguntas quase nunca são
        # vizinhas, então faixa contínua desperdiça o formato
        idxs = [int(x) for x in i0.split(',') if x.strip() != '']
    else:
        idxs = list(range(int(i0), min(int(i1) + 1, n)))
    idxs = [k for k in idxs if 0 <= k < n]
    if vertical:
        deck = dict(deck, intro_s=deck.get('short_intro_s', .8), outro_s=deck.get('short_outro_s', 1.6),
                    tempo=deck.get('tempo_short', deck.get('tempo', 5)))

    rng = np.random.default_rng(SEED * 7 + 11)
    fam = deck.get('fundo') or BG.escolher(SEED)[0]
    pal_name = deck.get('paleta') or BG.escolher(SEED)[1]
    pal = BG.PALETAS[pal_name]
    kit = A.pick_kit(SEED)
    # deck com "voz": null desliga a síntese: só entra o que existir em narracao/
    voice = VOZ or (deck['voz'] if 'voz' in deck else ['faber', 'cadu', 'jeff', 'dora'][int(rng.integers(4))])
    print(f'SEED {SEED} · fundo {fam} · paleta {pal_name} · trilha {kit["name"]} {kit["bpm"]}bpm · voz {voice}')

    clips = synth_all(deck, idxs, D, voice, vertical)
    tl, total = build_timeline(deck, idxs, clips, vertical)
    print(f'{len(idxs)} perguntas · {total:.1f} s ({total/60:.1f} min)')
    L_, tp, nspoken = build_audio(deck, tl, total, D, clips, kit)
    W, H = (1080, 1920) if vertical else (1920, 1080)
    out = 'short.mp4' if vertical else 'final.mp4'
    NF = render_video(deck, tl, total, D, pal, fam, W, H, out)

    meta = dict(deck=os.path.basename(deck_path), tema=deck.get('tema'), titulo=deck.get('titulo'),
                seed=SEED, fundo=fam, paleta=pal_name, trilha=kit['name'], bpm=kit['bpm'],
                voz=_rotulo_voz(clips, voice, D), trechos_falados=nspoken,
                trechos_proprios=sum(1 for k in clips if os.path.exists(
                    os.path.join(D, 'narracao', arquivo_narracao(k)))),
                vertical=vertical, idxs=idxs, total_s=round(total, 2), frames=NF, fps=FPS,
                lufs=L_, true_peak=tp, out=out, W=W, H=H,
                marks=[dict(n=pos, deck_i=s['k'] + 1, t0=round(s['t0'], 2),
                            reveal=round(s['ttimer'], 2), tempo=s['timer'])
                       for pos, s in enumerate(tl, 1)])
    json.dump(meta, open(f'{D}/meta.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps({k: meta[k] for k in ('total_s', 'frames', 'lufs', 'true_peak', 'voz', 'out')},
                     ensure_ascii=False))


def vinheta(deck_path, D, vertical=False):
    """Renderiza a abertura e o encerramento da marca CAIU A FICHA como mp4
    avulsos, prontos para serem colados nas pontas do vídeo pelo `montar`.

    Ficam fora do render principal de propósito: a vinheta não depende do
    deck nem da narração, então pode ser feita uma vez e reaproveitada, e um
    erro nela nunca custa meia hora de render do corpo do vídeo.
    """
    import quizbrand as VB
    import soundfile as sf
    deck = json.load(open(deck_path, encoding='utf-8'))
    os.makedirs(D, exist_ok=True)
    pal = BG.PALETAS[deck.get('paleta') or BG.escolher(SEED)[1]]
    W, H = (1080, 1920) if vertical else (1920, 1080)

    linhas = deck.get('chamadas_outro') or ['Inscreva-se no CAIU A FICHA',
                                            'Vídeo novo toda semana']
    feitos = []
    for nome, gerador, som, dur in (
            ('intro', VB.abertura(W, H, FPS, pal, SEED), VB.som_abertura(SEED), VB.INTRO_S),
            ('outro', VB.encerramento(W, H, FPS, pal, linhas, SEED), VB.som_encerramento(SEED),
             VB.OUTRO_S)):
        wav = f'{D}/_{nome}.wav'
        sf.write(wav, som, SR)
        out = f'{D}/{nome}.mp4'
        ffp = subprocess.Popen(
            ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
             '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
             '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
             '-pix_fmt', 'yuv420p', '-g', str(FPS * 2), '-c:a', 'aac', '-b:a', '256k',
             '-ar', '48000', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        n = 0
        for fr in gerador:
            ffp.stdin.write(fr.tobytes()); n += 1
        ffp.stdin.close(); ffp.wait()
        print(f'vinheta {nome}: {n} quadros, {dur:.2f} s -> {out}', flush=True)
        feitos.append(out)
    return feitos


def montar(D, corpo, saida='completo.mp4'):
    """Cola abertura + corpo + encerramento. Reencoda tudo com os mesmos
    parâmetros: o concat demuxer é mais rápido, mas exige fluxos idênticos e
    engasga quando a vinheta e o corpo saíram de encodes diferentes."""
    partes = [f'{D}/intro.mp4', f'{D}/{corpo}', f'{D}/outro.mp4']
    faltam = [p for p in partes if not os.path.exists(p)]
    if faltam:
        print('faltam partes: ' + ', '.join(faltam)); return
    args = ['ffmpeg', '-y', '-loglevel', 'error']
    for p in partes: args += ['-i', p]
    fc = ''.join(f'[{i}:v][{i}:a]' for i in range(3)) + 'concat=n=3:v=1:a=1[v][a]'
    args += ['-filter_complex', fc, '-map', '[v]', '-map', '[a]',
             '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p',
             '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart',
             f'{D}/{saida}']
    subprocess.run(args, check=True)
    mb = os.path.getsize(f'{D}/{saida}') // 2 ** 20
    print(f'montado {saida} · {mb} MiB')


def verify(D):
    import soundfile as sf
    from PIL import Image
    meta = json.load(open(f'{D}/meta.json', encoding='utf-8')); ok = True
    path = f"{D}/{meta['out']}"
    pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                         'format=duration:stream=codec_type,width,height,r_frame_rate',
                         '-of', 'json', path], capture_output=True, text=True)
    if not os.path.exists(path):
        raise SystemExit(f'VERIFY: {path} nao existe. O meta.json aponta para '
                         f"{meta['out']!r}; se o arquivo foi renomeado depois do "
                         'render, o meta tem que ser atualizado junto.')
    info = json.loads(pr.stdout or '{}')
    if 'format' not in info:
        raise SystemExit(f'VERIFY: ffprobe nao leu {path}: {pr.stderr.strip()}')
    dur = float(info['format']['duration'])
    v = [s for s in info['streams'] if s['codec_type'] == 'video'][0]
    a = [s for s in info['streams'] if s['codec_type'] == 'audio']

    def chk(label, good):
        nonlocal ok; ok &= bool(good); print(f"{label} {'OK' if good else 'FALHOU'}")
    chk(f"duração {dur:.2f}s (esperado {meta['total_s']}s)", abs(dur - meta['total_s']) < .7)
    chk(f"resolução {v['width']}x{v['height']}", (v['width'], v['height']) == (meta['W'], meta['H']))
    chk(f"fps {eval(v['r_frame_rate']):g}", eval(v['r_frame_rate']) == FPS)
    chk(f"faixas de áudio {len(a)}", len(a) == 1)
    chk(f"loudness {meta['lufs']} LUFS", abs(meta['lufs'] + 14.0) < 1.5)
    chk(f"true peak {meta['true_peak']} dBTP (limite -1)", meta['true_peak'] <= -0.99)
    m, _ = sf.read(f'{D}/audio.wav', dtype='float32', always_2d=True)
    pres = (np.abs(m).max(1) > 1e-4).mean()
    chk(f"áudio presente em {pres*100:.1f}% da faixa", pres > .97)
    if meta.get('voz'):
        chk(f"narração: {meta['trechos_falados']} trechos com a voz {meta['voz']}", meta['trechos_falados'] > 0)

    # a revelação precisa mudar a tela
    for mk in meta['marks'][:3]:
        fs = []
        for off in (-.4, .6):
            p = f'{D}/_p.png'
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(mk['reveal'] + off),
                            '-i', path, '-frames:v', '1', p], check=True)
            fs.append(np.asarray(Image.open(p).convert('RGB'), np.float32))
        chk(f"pergunta {mk['n']}: revelação muda a tela (Δ {np.abs(fs[0]-fs[1]).mean():.1f})",
            np.abs(fs[0] - fs[1]).mean() > 3.0)

    # áreas de segurança do Short: nada de conteúdo fora da faixa central
    if meta['vertical']:
        p = f'{D}/_p.png'
        bad = 0
        for mk in meta['marks'][:3]:
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(mk['reveal'] - .3),
                            '-i', path, '-frames:v', '1', p], check=True)
            im = np.asarray(Image.open(p).convert('L'), np.float32)
            base = np.asarray(Image.open(f'{D}/frame.png').convert('L'), np.float32)
            # texto claro = pixels bem acima do fundo local
            for y0, y1, nome in [(0, 230, 'topo'), (1400, 1920, 'rodapé')]:
                faixa = im[y0:y1]
                if (faixa > 215).mean() > .012: bad += 1; print(f"  conteúdo claro no {nome}")
        chk("áreas de segurança do Short livres", bad == 0)
    if os.path.exists(f'{D}/_p.png'): os.remove(f'{D}/_p.png')
    print('VERIFY', 'PASSOU' if ok else 'FALHOU'); return ok


def split(D):
    import hashlib, re, unicodedata
    meta = json.load(open(f'{D}/meta.json', encoding='utf-8'))
    od = f'/mnt/user-data/outputs/{os.path.basename(os.path.abspath(D))}'
    os.makedirs(od, exist_ok=True)
    data = open(f"{D}/{meta['out']}", 'rb').read()
    base = unicodedata.normalize('NFKD', meta.get('tema') or 'quiz').encode('ascii', 'ignore').decode()
    base = re.sub(r'[^A-Za-z0-9]+', '_', base).strip('_')[:40]
    out = f"{base}{'_short' if meta['vertical'] else ''}.mp4"
    parts = ['cabecalho.bin']; open(f'{od}/cabecalho.bin', 'wb').write(data[:64])
    body = data[64:]
    for k, i in enumerate(range(0, len(body), 28_000_000)):
        nm = f'video_{k:02d}.bin'; open(f'{od}/{nm}', 'wb').write(body[i:i + 28_000_000]); parts.append(nm)
    open(f'{od}/JUNTAR_VIDEO.bat', 'w', newline='').write(
        '@echo off\r\ncd /d "%~dp0"\r\necho Juntando o video...\r\n'
        f'copy /b {"+".join(parts)} "{out}" >nul\r\n'
        f'if exist "{out}" (del video_*.bin & del cabecalho.bin & echo Pronto!) else (echo Falhou.)\r\npause\r\n')
    print(json.dumps(dict(dir=od, parts=parts, md5=hashlib.md5(data).hexdigest(), mp4=out)))


if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'render': render(sys.argv[2], sys.argv[3])
    elif c == 'short': render(sys.argv[2], sys.argv[3], True, *(sys.argv[4:6] or [0, 2]))
    elif c == 'srt': exportar_srt(sys.argv[2], sys.argv[3], *(sys.argv[4:5] and [False] + sys.argv[4:6] or []))
    elif c == 'srt-short': exportar_srt(sys.argv[2], sys.argv[3], True, *(sys.argv[4:6] or [0, 2]))
    elif c == 'narracao': exportar_roteiro(sys.argv[2], sys.argv[3], *(sys.argv[4:5] and [False] + sys.argv[4:6] or []))
    elif c == 'verify': verify(sys.argv[2])
    elif c == 'split': split(sys.argv[2])
    elif c == 'vinheta': vinheta(sys.argv[2], sys.argv[3], len(sys.argv) > 4 and sys.argv[4] == 'v')
    elif c == 'montar': montar(sys.argv[2], *(sys.argv[3:5] or ['short.mp4']))
    else: raise SystemExit(__doc__)
