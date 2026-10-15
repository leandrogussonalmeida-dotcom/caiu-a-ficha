#!/usr/bin/env python3
"""Confere um Short NO RITMO pronto: duração, resolução, loudness e se o
bumbo do ÁUDIO FINAL (decodificado do mp4) cai no instante que o vídeo usou.

    python3 ritmo_verificar.py <arquivo.mp4> [...]
"""
import json, subprocess, sys
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
    pid = c.split('/')[-1].split('-')[0]
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


for c in sys.argv[1:]:
    p = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate',
                                   '-show_entries', 'format=duration', '-of', 'json', c], capture_output=True, text=True).stdout)
    v = [s for s in p['streams'] if s['codec_type'] == 'video'][0]
    dur = float(p['format']['duration'])
    I, P = loud(c)
    lag, n = sincronia(c)
    ok = (v['width'], v['height']) == (1080, 1920) and dur < 59 and -15 <= I <= -13 and P <= -1.0 and abs(lag) <= 1
    print(f"{c.split('/')[-1]:24s} {dur:5.1f}s {v['width']}x{v['height']} {I:6.1f} LUFS pico {P:5.1f} | "
          f"som x eventos: {lag:+.1f} ms ({n} eventos) | {'PASSOU' if ok else 'REPROVOU'}")
