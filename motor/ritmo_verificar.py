#!/usr/bin/env python3
"""Confere um Short NO RITMO pronto: duração, resolução, loudness, se o
bumbo do ÁUDIO FINAL (decodificado do mp4) cai no instante que o vídeo usou,
e se o arquivo tem vídeo DE VERDADE (quadros e bytes por segundo).

    python3 ritmo_verificar.py <arquivo.mp4> [...]
    python3 ritmo_verificar.py --plano          # só os textos, sem renderizar

A regra dos bytes nasceu de 178 Shorts de 33 KB que passaram como "ok":
rodar sem erro não prova que saiu vídeo.
"""
import json, os, subprocess, sys
import numpy as np
import scipy.signal as sg


def audio(c, sr=48000):
    o = subprocess.run(['ffmpeg', '-v', 'error', '-i', c, '-f', 'f32le', '-ac', '1', '-ar', str(sr), '-'],
                       capture_output=True)
    return np.frombuffer(o.stdout, np.float32), sr


def loud(c):
    o = subprocess.run(['ffmpeg', '-hide_banner', '-i', c, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    tail = o[o.rfind('Summary'):]
    I = float(tail.split('I:')[1].split('LUFS')[0])
    P = float(tail.split('Peak:')[1].split('dBFS')[0])
    return I, P


def sincronia(c):
    """Recompõe a faixa a partir do plano (determinística pelo seed: os
    eventos são os mesmos que o vídeo usou) e mede o atraso do áudio do mp4
    contra ela por correlação, em três trechos. 0 ms = cada bumbo está na
    amostra que o vídeo desenhou.

    (Detectar o bumbo direto no áudio dá ~30 ms de viés: a energia do bumbo
    só entra na faixa grave depois que o pitch dele cai. Por isso a régua é
    a correlação, não um detector.)"""
    import ritmo_musica as M
    from ritmo_plano import PLANO
    pid = os.path.basename(c).split('-')[0]
    p = [q for q in PLANO if q['id'] == pid][0]
    F = M.compor(p['secoes'], seed=p['seed'], raiz=p.get('raiz'))
    ref = F.audio.mean(1)
    x, sr = audio(c)
    lags = []
    for ini in (1.0, F.total * .45, F.total - 6):
        a, b = int(ini * sr), int((ini + 4) * sr)
        r, y = ref[a:b], x[a - 2400:b + 2400]
        cc = sg.correlate(y, r, 'valid', method='fft')
        lags.append((int(np.argmax(cc)) - 2400) / sr * 1000)
    return max(lags, key=abs), len(F.eventos)


def textos_do_plano():
    """Reprova texto que: não cabe na margem segura em 2x (gancho) ou 1x
    (subtítulo, pergunta), tem caractere que a fonte não desenha, ou ainda
    está em português."""
    import re
    import pixelengine as PX, pixelfonte as PF
    from ritmo_plano import PLANO
    from ritmo_base import quebrar
    t = PX.Tela()
    PT = re.compile(r"[ãõçáéíóúâêô]|\b(você|voce|não|nao|batida|inscreva|comenta|fase|gênero|música)\b", re.I)
    erros = []
    for p in PLANO:
        for l in p['gancho']:
            if t.largura_texto(l, 17) > 136: erros.append(f"{p['id']} gancho largo: {l}")
        if t.largura_texto(p['sub_gancho'], 9) > 136: erros.append(f"{p['id']} sub largo")
        if len(quebrar(t, p['pergunta'], 9, 132)) > 3: erros.append(f"{p['id']} pergunta longa")
        tela_txt = ' '.join(p['gancho']) + ' ' + p['sub_gancho'] + ' ' + p['pergunta']
        f = PF.faltando(tela_txt)
        if f: erros.append(f"{p['id']} sem glifo: {f}")
        for campo in (tela_txt, p['titulo']):
            m = PT.search(campo)
            if m: erros.append(f"{p['id']} português: '{m.group(0)}' em {campo!r}")
    return erros


if len(sys.argv) > 1 and sys.argv[1] == '--plano':
    e = textos_do_plano()
    print('\n'.join(e) if e else 'textos do plano: PASSOU')
    sys.exit(1 if e else 0)

def conferir(c):
    p = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-show_entries',
                                   'stream=codec_type,width,height,r_frame_rate,nb_read_packets,bit_rate',
                                   '-show_entries', 'format=duration,size', '-of', 'json', c], capture_output=True, text=True).stdout)
    v = [s for s in p['streams'] if s['codec_type'] == 'video'][0]
    dur = float(p['format']['duration'])
    quadros = int(v.get('nb_read_packets', 0))
    kbps = int(p['format']['size']) * 8 / 1000 / max(dur, 1e-3)
    video_ok = abs(quadros - dur * 30) <= 3 and kbps >= 400
    I, P = loud(c)
    lag, n = sincronia(c)
    ok = (v['width'], v['height']) == (1080, 1920) and dur < 59 and -15 <= I <= -13 and P <= -1.0 \
        and abs(lag) <= 1 and video_ok
    print(f"{os.path.basename(c):24s} {dur:5.1f}s {v['width']}x{v['height']} {I:6.1f} LUFS pico {P:5.1f} | "
          f"som x eventos: {lag:+.1f} ms ({n} eventos) | {quadros} quadros {kbps:.0f} kb/s | "
          f"{'PASSOU' if ok else 'REPROVOU'}")
    return ok


falhas = 0
for c in sys.argv[1:]:
    try:
        falhas += 0 if conferir(c) else 1
    except Exception as e:                 # arquivo que nem dá para medir também reprova
        falhas += 1
        print(f"{os.path.basename(c):24s} REPROVOU (não deu para medir: {type(e).__name__})")
sys.exit(1 if falhas else 0)
