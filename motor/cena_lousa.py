#!/usr/bin/env python3
"""LOUSA NO RITMO — o traço anda em semicolcheias.

A lousa de dois botões, acelerada: a caneta avança um degrau em cada 1/16
da música, então o desenho tem o andamento da faixa. No house o traço é
firme; no drum and bass ele corre. Cada seção é um desenho; o desenho
termina uma batida antes da troca, o nome aparece no tempo, e a troca é o
chacoalhar — no bumbo do compasso seguinte.

"Adivinha antes de terminar" é o gancho: a pessoa tenta ler o traço
enquanto ele se forma, e a resposta só vem na batida.

O traço não levanta (como no brinquedo); as peças separadas do desenho
são ligadas pelo caminho mais curto, também em escada.
"""
import math
import numpy as np
import tracos as TR
from ritmo_base import CenaBase, W, H, ease, back, hsh

# o desenho tem nome interno em português; na tela o canal fala inglês
NOME_EN = {'AMPULHETA': 'HOURGLASS', 'AVIAO': 'PLANE', 'BARCO': 'BOAT', 'BICICLETA': 'BICYCLE', 'CACTO': 'CACTUS', 'CARACOL': 'SNAIL', 'CARRO': 'CAR', 'CASA': 'HOUSE', 'CHAVE': 'KEY', 'COGUMELO': 'MUSHROOM', 'FAROL': 'LIGHTHOUSE', 'FLOR': 'FLOWER', 'FOLHA': 'LEAF', 'GARRAFA': 'BOTTLE', 'GATO': 'CAT', 'GUARDA-CHUVA': 'UMBRELLA', 'IGREJA': 'CHURCH', 'LAMPADA': 'LIGHT BULB', 'OCULOS': 'GLASSES', 'PEIXE': 'FISH', 'PONTE': 'BRIDGE', 'RELOGIO': 'CLOCK', 'XICARA': 'CUP', 'TESOURA': 'SCISSORS', 'PANELA': 'POT'}

BX, BY, BW, BH = 12, 64, 156, 170          # moldura
VX, VY, VW, VH = BX + 9, BY + 10, BW - 18, BH - 42   # vidro


def escada(p0, p1):
    pts = []
    x, y = p0; x1, y1 = p1
    dx, dy = x1 - x, y1 - y
    n = max(1, int(max(abs(dx), abs(dy))))
    for i in range(n):
        if abs(dx) > abs(dy):
            x += dx / n; pts.append((x, y)); y += dy / n; pts.append((x, y))
        else:
            y += dy / n; pts.append((x, y)); x += dx / n; pts.append((x, y))
    pts.append((x1, y1))
    return pts


def trilha(nome):
    """Pontos do desenho -> lista de pixels em ordem de traço. Onde o desenho
    pede para levantar a caneta, levanta: ligar as peças cruzava o desenho
    com riscos que matavam a leitura (o gato saía com um X na barriga)."""
    pts = TR.caber(TR.TUDO[nome](), margem=8)
    px = []
    ant = None
    for p in pts:
        if p[0] is None:
            ant = None; continue
        q = (VX + 4 + p[0] / 100 * (VW - 8), VY + 4 + (100 - p[1]) / 100 * (VH - 8))
        if ant is not None:
            for r in escada(ant, q):
                c = (int(round(r[0])), int(round(r[1])))
                if not px or px[-1] != c: px.append(c)
        else:
            px.append((int(round(q[0])), int(round(q[1]))))
        ant = q
    return np.array(px, np.int32)


class Cena(CenaBase):
    zoom = 1

    def preparar(self):
        TR.desenho('GATO')                      # popula o catálogo
        TR.TUDO or TR.desenho('GATO')
        v = self.v
        nomes = v.get('desenhos')
        secs = [s for s in self.F.secoes if s['papel'] != 'fim']
        if not nomes:
            nomes = list(self.rng.choice(sorted(TR.TUDO), len(secs), replace=False))
        self.des = []
        for s, nome in zip(secs, nomes):
            px = trilha(nome)
            t_ini = s['t0'] + (.38 if s['i'] > 0 else 0.0)
            t_fim = s['t1'] - s['spb']
            # os degraus: um por semicolcheia entre t_ini e t_fim
            passos = [e['t'] for e in self.L.lista('batida') if t_ini - 1e-3 <= e['t'] <= t_fim]
            grade = []
            for b in passos:
                for k in range(4):
                    tt = b + k * s['spb'] / 4
                    if tt <= t_fim + 1e-6 and tt >= t_ini - 1e-6: grade.append(tt)
            if not grade or grade[0] > t_ini + 1e-3: grade = [t_ini] + grade
            self.des.append(dict(nome=nome, px=px, t0=t_ini, t1=t_fim, grade=np.array(grade),
                                 sec=s, fim_sec=s['t1']))
        self.cor_mold = v.get('moldura', 15)
        self.cor_vidro = v.get('vidro', 14)
        self.cor_traco = v.get('traco', 0)
        self.fundo = v.get('fundo', (1, 2))

    def _qtd(self, d, t):
        """Quantos pixels do traço já existem em t: degrau por semicolcheia,
        com um deslize curto dentro do degrau."""
        n = len(d['px'])
        g = d['grade']
        if t < g[0]: return 0
        if t >= d['t1']: return n
        k = int(np.searchsorted(g, t, 'right')) - 1
        N = len(g)
        alvo0 = n * k / N
        alvo1 = n * (k + 1) / N
        u = min(1.0, (t - g[k]) / .045)
        return int(alvo0 + (alvo1 - alvo0) * ease(u))

    def tremor(self, t):
        for d in self.des:
            u = t - d['fim_sec']
            if 0 <= u < .38:
                a = (1 - u / .38) * 7
                return (int(round(math.sin(u * 70) * a)), int(round(math.cos(u * 55) * a * .3)))
        return (0, 0)

    def mundo(self, tela, t, i):
        L = self.L
        sec = L.secao(t)
        nb = L.conta('batida', t)
        pk = L.env('kick', t, .12)
        # fundo: listras diagonais que andam meia faixa por batida
        a, b = self.fundo
        tela.limpar(a)
        off = int((nb + min(1, L.desde('batida', t) / .1) * .5) * 8) % 16
        for k in range(-20, 40):
            x0 = k * 16 + off
            for yy in range(0, H, 4):
                tela.ret(x0 + yy // 2, yy, 8, 4, b)
        # moldura (sem marca nenhuma: o original é marca registrada)
        mc = self.cor_mold
        tela.ret(BX + 4, BY, BW - 8, BH, mc)
        tela.ret(BX, BY + 4, BW, BH - 8, mc)
        tela.ret(BX + 2, BY + 2, BW - 4, BH - 4, mc)
        tela.ret(BX + 4, BY + BH, BW - 8, 3, 0)
        tela.ret(VX - 1, VY - 1, VW + 2, VH + 2, 0)
        tela.ret(VX, VY, VW, VH, self.cor_vidro)
        # botões giram com a caneta
        d_at = None
        for d in self.des:
            if d['t0'] - .4 <= t < d['fim_sec'] + .38: d_at = d
        ang_x = ang_y = 0.0
        if d_at is not None:
            q = self._qtd(d_at, t)
            apaga = t - d_at['fim_sec']
            px = d_at['px'][:q]
            if q > 0:
                if apaga > 0:
                    # o pó volta: some de baixo para cima em faixas
                    lim = VY + VH * (1 - apaga / .32)
                    px = px[px[:, 1] < lim]
                if len(px):
                    # traço de 2 px: 1 px some na tela do celular
                    tela.buf[px[:, 1], px[:, 0]] = self.cor_traco
                    tela.buf[np.minimum(px[:, 1] + 1, H - 1), px[:, 0]] = self.cor_traco
                    tela.buf[px[:, 1], np.minimum(px[:, 0] + 1, W - 1)] = self.cor_traco
                    if apaga <= 0 and q < len(d_at['px']):
                        cx_, cy_ = d_at['px'][q - 1]
                        tela.ret(cx_ - 1, cy_ - 1, 3, 3, 15 if pk > .3 else self.cor_traco)
                    cx_, cy_ = d_at['px'][max(0, q - 1)]
                    ang_x = cx_ * .25; ang_y = cy_ * .25
        for kx, ang in ((BX + 16, ang_x), (BX + BW - 16, ang_y)):
            ky = BY + BH - 15
            tela.disco(kx, ky, 9, 11)
            tela.anel(kx, ky, 9, 0, .8)
            tela.linha(kx, ky, kx + math.cos(ang) * 7, ky + math.sin(ang) * 7, 0)
        # luz da batida na moldura, entre os botões
        for k in range(4):
            on = (L.conta('batida', t) - 1) % 4 == k and L.desde('batida', t) < .2
            tela.ret(W // 2 - 22 + k * 12, BY + BH - 17, 8, 5, 11 if on else 0)

    def sobre(self, tela, t, i):
        L = self.L
        for k, d in enumerate(self.des):
            u = t - d['t1']
            if 0 <= u < (d['fim_sec'] - d['t1']) + .5:
                e = back(u / .22)
                txt = NOME_EN.get(d['nome'], d['nome']).replace('-', ' ') + '!'
                tam = int(10 + 8 * min(1, e))
                y = BY + 6
                w = tela.largura_texto(txt, tam)
                tela.texto(txt, W // 2, y, 9, tam=tam, centro=True, contorno=0)
            # contagem: "DESENHO 2/5"
            if d['t0'] <= t < d['t1'] and t > 2.6:
                txt = f"DRAWING {k + 1}/{len(self.des)}"
                w = tela.largura_texto(txt, 10)
                tela.texto(txt, W // 2, 46, 11, tam=10, centro=True, contorno=0)
