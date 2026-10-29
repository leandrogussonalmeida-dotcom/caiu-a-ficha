#!/usr/bin/env python3
"""Confere um vídeo longo do NOSSO MUNDO PIXEL antes de publicar.

    python3 longo_verificar.py --roteiro ep01_roteiro      # só o texto, sem render
    python3 longo_verificar.py ep01-engine.mp4 ep01_roteiro

Roteiro: cada legenda cabe em 2x (448 px), tem glifo, fica no ar 4 s ou mais,
não sai do capítulo, e todo fato citado tem fonte em FONTES.
Arquivo: 1920x1080, um quadro a cada 1/30 s, ≥ 400 kb/s, duração igual à do
roteiro (±1 s), loudness entre -17 e -15 LUFS, pico ≤ -1 dBTP.
"""
import importlib, json, os, subprocess, sys
import pixelfonte as PF


def roteiro(nome):
    R = importlib.import_module(nome)
    import ritmo_musica as M
    erros = []
    durs = {}
    for c in R.CAPITULOS:
        bpm = c.get('bpm', M.GENEROS[c['gen']]['bpm'])
        durs[c['id']] = c['bars'] * 4 * 60.0 / bpm
    for cap, itens in R.LEGENDAS.items():
        if cap not in durs: erros.append(f"legenda de capítulo inexistente: {cap}")
        for a, b, l1, l2, fatos in itens:
            for l in (l1, l2):
                t = l.replace('*', '')
                if PF.largura(t, 2) > 448: erros.append(f"{cap}: larga demais: {l}")
                f = PF.faltando(t)
                if f: erros.append(f"{cap}: sem glifo {f}: {l}")
                if l.count('*') % 2: erros.append(f"{cap}: asterisco sem par: {l}")
            if b - a < 4: erros.append(f"{cap}: menos de 4 s no ar: {l1}")
            if b > durs.get(cap, 0): erros.append(f"{cap}: passa do fim do capítulo: {l1}")
            for x in fatos:
                if x not in R.FONTES: erros.append(f"{cap}: fato {x} sem fonte")
    total = sum(durs.values())
    return erros, total


def arquivo(c, total_esperado):
    p = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-show_entries',
                                   'stream=codec_type,width,height,nb_read_packets',
                                   '-show_entries', 'format=duration,size', '-of', 'json', c],
                                  capture_output=True, text=True).stdout)
    v = [s for s in p['streams'] if s['codec_type'] == 'video'][0]
    tem_audio = any(s['codec_type'] == 'audio' for s in p['streams'])
    dur = float(p['format']['duration'])
    q = int(v.get('nb_read_packets', 0))
    kbps = int(p['format']['size']) * 8 / 1000 / max(dur, 1e-3)
    o = subprocess.run(['ffmpeg', '-hide_banner', '-i', c, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    tail = o[o.rfind('Summary'):]
    I = float(tail.split('I:')[1].split('LUFS')[0])
    P = float(tail.split('Peak:')[1].split('dBFS')[0])
    ok = ((v['width'], v['height']) == (1920, 1080) and tem_audio and abs(q - dur * 30) <= 3 and kbps >= 400
          and abs(dur - total_esperado) <= 1.0 and -17 <= I <= -15 and P <= -1.0)
    print(f"{os.path.basename(c)}: {dur:.1f}s (roteiro {total_esperado:.1f}s) {v['width']}x{v['height']} "
          f"{q} quadros {kbps:.0f} kb/s | {I:.1f} LUFS pico {P:.1f} | {'PASSOU' if ok else 'REPROVOU'}")
    return ok


if __name__ == '__main__':
    if sys.argv[1] == '--roteiro':
        e, total = roteiro(sys.argv[2])
        print('\n'.join(e) if e else f"roteiro: PASSOU ({total:.1f} s)")
        sys.exit(1 if e else 0)
    e, total = roteiro(sys.argv[2])
    if e: print('\n'.join(e))
    ok = arquivo(sys.argv[1], total + 0.0) and not e
    sys.exit(0 if ok else 1)
