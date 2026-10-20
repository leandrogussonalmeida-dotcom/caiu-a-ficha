#!/usr/bin/env python3
"""Renderiza os Shorts NO RITMO (canal RITMO PIXEL).

    python3 ritmo_render.py <dir_saida> [r01 r02 ...]

Pula o que já existe (e passou no ffprobe). Grava um relatório por peça e
um `titulos.txt` com título, descrição e hashtags para publicar.
"""
import importlib, json, os, subprocess, sys, time
import ritmo_base as B
from ritmo_plano import PLANO

NOMES = {'masmorra': 'masmorra', 'rota': 'rota', 'foguete': 'foguete', 'lousa': 'lousa',
         'corrida': 'corrida', 'cidade': 'cidade', 'plataforma': 'plataforma',
         'bolinha': 'bolinha', 'pistas': 'pistas', 'tunel': 'tunel'}


def arquivo(p):
    return f"{p['id']}-{p['cena']}.mp4"


def probe(c):
    try:
        o = subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-show_entries',
                            'stream=codec_type,width,height,nb_read_packets',
                            '-show_entries', 'format=duration', '-of', 'json', c], capture_output=True, text=True)
        j = json.loads(o.stdout)
        tipos = [s['codec_type'] for s in j['streams']]
        v = [s for s in j['streams'] if s['codec_type'] == 'video'][0]
        dur = float(j['format']['duration'])
        quadros = int(v.get('nb_read_packets', 0))
        # vídeo e áudio presentes não bastam: tem que ter um quadro a cada 1/30 s
        return dict(ok='video' in tipos and 'audio' in tipos and v['width'] == 1080 and v['height'] == 1920
                    and abs(quadros - dur * B.FPS) <= 3, dur=dur, quadros=quadros)
    except Exception as e:
        return dict(ok=False, erro=str(e))


def main():
    out = sys.argv[1]
    ids = sys.argv[2:]
    os.makedirs(out, exist_ok=True)
    for p in PLANO:
        if ids and p['id'] not in ids: continue
        c = os.path.join(out, arquivo(p))
        if os.path.exists(c) and probe(c).get('ok'):
            print(p['id'], 'já existe', flush=True); continue
        t0 = time.time()
        mod = importlib.import_module('cena_' + p['cena'])
        r = B.renderizar(mod.Cena, dict(p), arquivo(p), out)
        pr = probe(c)
        r.update(pr)
        r['seg'] = round(time.time() - t0, 1)
        print(json.dumps({k: (float(v) if hasattr(v, 'item') else v) for k, v in r.items()}), flush=True)
        if not pr.get('ok'):
            print('FALHOU', p['id'], flush=True)


if __name__ == '__main__':
    main()
