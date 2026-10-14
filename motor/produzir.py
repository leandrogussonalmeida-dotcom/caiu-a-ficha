#!/usr/bin/env python3
"""Fecha a peça: vinheta 8-bit nas pontas do que o simulador produziu.

Separado dos simuladores de propósito: a vinheta não depende do conteúdo,
então pode ser feita uma vez por SEED e reaproveitada, e um erro nela nunca
custa o render do corpo do vídeo.
"""
import os, subprocess, sys
import numpy as np
import soundfile as sf
import pixelengine as PX
import pixelmarca as MK


def vinheta(dirsaida, W=PX.LARG * PX.ESCALA, H=PX.ALT * PX.ESCALA, seed=0,
            chamadas=('INSCREVA-SE', 'VIDEO NOVO TODA SEMANA')):
    os.makedirs(dirsaida, exist_ok=True)
    lw, lh = W // PX.ESCALA, H // PX.ESCALA
    feitos = []
    for nome, ger, som in (
            ('intro', MK.abertura(lw, lh, PX.FPS, seed), MK.som_abertura(seed)),
            ('outro', MK.encerramento(lw, lh, PX.FPS, list(chamadas), seed),
             MK.som_encerramento(seed))):
        wav = f'{dirsaida}/_{nome}.wav'
        sf.write(wav, som, PX.SR)
        out = f'{dirsaida}/{nome}.mp4'
        p = subprocess.Popen(
            ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
             '-s', f'{W}x{H}', '-r', str(PX.FPS), '-i', '-', '-i', wav,
             '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium',
             '-crf', '18', '-pix_fmt', 'yuv420p', '-g', str(PX.FPS * 2),
             '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest',
             '-sws_flags', 'neighbor', '-movflags', '+faststart', out],
            stdin=subprocess.PIPE)
        n = 0
        for fr in ger:
            p.stdin.write(fr.tobytes()); n += 1
        p.stdin.close(); p.wait()
        print(f'vinheta {nome}: {n} quadros -> {out}', flush=True)
        feitos.append(out)
    return feitos


def montar(D, corpo, saida='completo.mp4'):
    """Cola abertura + corpo + encerramento, reencodando com os mesmos
    parâmetros. O concat demuxer é mais rápido mas exige fluxos idênticos."""
    partes = [f'{D}/intro.mp4', f'{D}/{corpo}', f'{D}/outro.mp4']
    faltam = [p for p in partes if not os.path.exists(p)]
    if faltam:
        print('faltam partes: ' + ', '.join(faltam)); return
    args = ['ffmpeg', '-y', '-loglevel', 'error']
    for p in partes: args += ['-i', p]
    fc = ''.join(f'[{i}:v][{i}:a]' for i in range(3)) + 'concat=n=3:v=1:a=1[v][a]'
    args += ['-filter_complex', fc, '-map', '[v]', '-map', '[a]',
             '-c:v', 'libx264', '-preset', 'medium', '-crf', '19',
             '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
             '-movflags', '+faststart', f'{D}/{saida}']
    subprocess.run(args, check=True)
    print(f'montado {saida} · {os.path.getsize(f"{D}/{saida}") // 2**20} MiB')


if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'vinheta':
        vert = len(sys.argv) < 4 or sys.argv[3] != 'h'
        W, H = (1080, 1920) if vert else (1920, 1080)
        vinheta(sys.argv[2], W, H, int(sys.argv[4]) if len(sys.argv) > 4 else 0)
    elif c == 'montar':
        montar(sys.argv[2], *(sys.argv[3:5] or ['corpo.mp4']))
