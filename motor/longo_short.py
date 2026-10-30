#!/usr/bin/env python3
"""Cortes verticais (Shorts) de um vídeo longo do NOSSO MUNDO PIXEL.

Reaproveita o MESMO desenho e o MESMO som do episódio: a cena é desenhada na
tela larga (480x270, sem a faixa de legenda), um recorte de 180 px de largura
vai para a tela vertical (180x320, ampliada 6x = 1080x1920) e a legenda é
redesenhada para o celular.

  palco      recorte 180x208 em y 34..242 (zona segura do Short)
  gancho     2 linhas grandes no quadro 0 (a capa), somem em 2,6 s
  legenda    as legendas do roteiro que caem no trecho, em 1x (30 px por letra
             em 1080), até 3 linhas, sobre o pé do palco (y 206..242)
  fim        vinheta NOSSO MUNDO PIXEL vertical (2,8 s)
  áudio      o mix do episódio no trecho, masterizado a -14 LUFS

O roteiro do episódio lista os cortes em CORTES:
    dict(id='c1', de=('potencia', 0.0), ate=('potencia', 24.0), x=75,
         gancho=['A QUEIMA', 'EM CÂMERA LENTA'], titulo='...', descricao='...')

    python3 longo_short.py ep01_motor <pasta_saida> [c1 c2 ...]
    python3 longo_short.py ep01_motor --folha <saida.png>
"""
import importlib, json, os, subprocess, sys
import numpy as np
import soundfile as sf
import pixelengine as PX
import pixelfonte as PF
import quizaudio as QA
import ritmo_marca as RM
import longo as LG
from longo import W, H, PALCO_H, FUNDO, PRETO, BRANCO, AMARELO, CIANO, ACO3, texto_marcado
from ritmo_base import quebrar

WV, HV, ESCV = 180, 320, 6
Y_PALCO = 34
Y_LEG = 206


def _tempo(trilha, ref):
    cap, dt = ref
    c = next(x for x in trilha.caps if x['id'] == cap)
    return c['t0'] + dt


def _legendas(ep, trilha):
    out = []
    for c in trilha.caps:
        for a, b, l1, l2, _ in ep.LEGENDAS.get(c['id'], []):
            out.append((c['t0'] + a, c['t0'] + b, (l1 + ' ' + l2).strip()))
    return out


class Corte:
    def __init__(self, ep, prep, corte):
        self.ep, self.c = ep, corte
        self.trilha, self.fx, self.cenas = prep
        self.t0 = _tempo(self.trilha, corte['de'])
        self.t1 = _tempo(self.trilha, corte['ate'])
        self.x = corte.get('x', 75)
        self.leg = [(a, b, txt) for a, b, txt in _legendas(ep, self.trilha) if b > self.t0 and a < self.t1]
        self.larga = PX.Tela(W, H, paleta=LG.PAL)
        self.vert = PX.Tela(WV, HV, paleta=LG.PAL)
        self.acab = LG.Acabamento16(self.trilha)
        self.vin = list(RM.encerramento(WV, HV, LG.FPS, ['INSCREVA-SE', 'VÍDEO COMPLETO NO CANAL'], 7, baixo=True))
        self.dur = self.t1 - self.t0 + RM.OUTRO_S

    def quadro(self, u):
        """u = segundos desde o começo do corte."""
        if u >= self.t1 - self.t0:
            k = min(len(self.vin) - 1, int((u - (self.t1 - self.t0)) * LG.FPS))
            return self.vin[k]
        t = self.t0 + u
        cap = self.trilha.cap(t)
        cena = self.cenas[cap['id']]
        L, V = self.larga, self.vert
        L.buf[:] = FUNDO
        self.ep.VERTICAL = True
        cena.desenhar(L, t - cap['t0'], t)
        self.ep.VERTICAL = False
        V.buf[:] = FUNDO
        V.buf[Y_PALCO:Y_PALCO + PALCO_H, :] = L.buf[:PALCO_H, self.x:self.x + WV]
        V.ret(0, Y_PALCO - 1, WV, 1, LG.TRACO)
        V.ret(0, Y_PALCO + PALCO_H, WV, 1, LG.TRACO)
        # legenda do roteiro, em até 3 linhas 1x
        for a, b, txt in self.leg:
            if a <= t < b:
                n = int((t - a) / .25 * 60)
                linhas = quebrar(V, txt.replace('*', ''), 9, WV - 14)
                linhas_m = _remarcar(txt, linhas)
                y = Y_LEG + (3 - len(linhas_m)) * 6
                usados = 0
                for l in linhas_m[:3]:
                    texto_marcado(V, l, WV // 2, y, 9, n_letras=max(0, n - usados), centro=True)
                    usados += len(l.replace('*', '')) + 1
                    y += 12
        # gancho no começo (o quadro 0 é a capa)
        if u < 2.6:
            sai = max(0.0, (u - 2.25) / .35)
            if sai < .05:
                w = max(V.largura_texto(l, 17) for l in self.c['gancho']) + 16
                LG.painel(V, WV // 2 - w // 2, 56, w, 22 * len(self.c['gancho']) + 10, borda=AMARELO)
            for k, l in enumerate(self.c['gancho']):
                yy = 64 + k * 22 - int(sai * 120)
                V.texto(l, WV // 2, yy, BRANCO if k == 0 else AMARELO, tam=17, centro=True, contorno=PRETO, sombra=PRETO)
        x = V.rgb[V.buf].astype(np.float32) / 255
        x[Y_PALCO:Y_PALCO + PALCO_H] = LG.AC.iluminar(x[Y_PALCO:Y_PALCO + PALCO_H], .42, .62, 1.3, 4.5, 1.0)
        return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def _remarcar(txt, linhas):
    """Devolve as linhas quebradas com os asteriscos de destaque de volta."""
    marcadas = set()
    dentro = False
    palavras = []
    for tok in txt.split():
        abre = tok.startswith('*'); fecha = tok.endswith('*') and len(tok.strip('*')) > 0
        limpo = tok.replace('*', '')
        if abre: dentro = True
        palavras.append((limpo, dentro))
        if fecha or (abre and tok.count('*') == 2): dentro = False
    out = []
    i = 0
    for l in linhas:
        n = len(l.split())
        pedaco = palavras[i:i + n]
        i += n
        out.append(' '.join(f"*{p}*" if m else p for p, m in pedaco))
    return out


def renderizar(ep_nome, pasta, ids=None, crf=20):
    ep = importlib.import_module(ep_nome)
    prep = LG.preparar(ep)
    trilha, fx, cenas = prep
    mix = LG.mixar(ep, trilha, fx)
    os.makedirs(pasta, exist_ok=True)
    rel = []
    for corte in ep.CORTES:
        if ids and corte['id'] not in ids: continue
        C = Corte(ep, prep, corte)
        nome = f"{ep.PREFIXO}-{corte['id']}"
        saida = os.path.join(pasta, nome + '.mp4')
        i0, i1 = int(C.t0 * LG.SR), int(C.t1 * LG.SR)
        a = mix[i0:i1].copy()
        k = int(.03 * LG.SR); a[:k] *= np.linspace(0, 1, k)[:, None]
        vin = RM.som_encerramento(7)
        a = np.concatenate([a, np.zeros((len(vin), 2), np.float32)])
        a[-len(vin):] += vin * .8
        a, lufs, tp = QA.master(a, -14.0)
        a = LG.limitar(a, QA.g(-2.2))
        wav = saida.replace('.mp4', '.wav')
        sf.write(wav, a, LG.SR, subtype='PCM_16')
        args = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                '-s', f'{WV * ESCV}x{HV * ESCV}', '-r', str(LG.FPS), '-i', '-', '-i', wav,
                '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                '-c:v', 'libx264', '-preset', 'medium', '-tune', 'animation', '-crf', str(crf),
                '-pix_fmt', 'yuv420p', '-g', str(LG.FPS), '-movflags', '+faststart', '-shortest', saida]
        p = subprocess.Popen(args, stdin=subprocess.PIPE)
        nq = int(round(C.dur * LG.FPS))
        for q in range(nq):
            b = C.quadro(q / LG.FPS)
            p.stdin.write(np.ascontiguousarray(np.repeat(np.repeat(b, ESCV, 0), ESCV, 1)).tobytes())
        p.stdin.close(); p.wait()
        os.remove(wav)
        r = dict(arquivo=saida, dur=round(C.dur, 2), quadros=nq, lufs=lufs)
        print(json.dumps(r), flush=True)
        rel.append(r)
    return rel


def folha(ep_nome, saida):
    from PIL import Image
    ep = importlib.import_module(ep_nome)
    prep = LG.preparar(ep)
    ims = []
    for corte in ep.CORTES:
        C = Corte(ep, prep, corte)
        d = C.t1 - C.t0
        for u in (0.5, d * .5):
            ims.append(Image.fromarray(C.quadro(u)).resize((WV * 2, HV * 2), Image.NEAREST))
    o = Image.new('RGB', (len(ims) * (WV * 2 + 6), HV * 2), (40, 40, 40))
    for k, im in enumerate(ims): o.paste(im, (k * (WV * 2 + 6), 0))
    o.save(saida)


if __name__ == '__main__':
    if sys.argv[2] == '--folha':
        folha(sys.argv[1], sys.argv[3])
    else:
        renderizar(sys.argv[1], sys.argv[2], sys.argv[3:] or None)
