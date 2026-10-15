#!/usr/bin/env python3
"""Pega as falas gravadas no yovoice e poe onde o motor procura.

O yovoice salva cada fala como um .wav de nome em hash, em
%USERPROFILE%\\.yovoice\\outputs. O mapa hash->texto esta no state.json,
na lista `history`. Este script casa o texto de cada fala com o manifesto
de cada video e copia o .wav ja renomeado para out-<id>/narracao/.

Nao precisa de Export timeline, que falha em projeto longo: os arquivos
ja estao em disco desde o instante em que foram gerados.

O casamento e por PREFIXO DO TEXTO em ordem cronologica, e cada .wav e
consumido uma vez so. Isso importa porque textos curtos se repetem entre
decks ("Como se escreve?"), e sem consumo unico um video roubaria a fala
do outro.

    python3 resgatar_voz.py            # todos os videos
    python3 resgatar_voz.py V065 V072  # so esses
"""
import json, os, re, shutil, sys, unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
MANIF = os.path.join(AQUI, 'manifestos')
# a ordem importa: o consumo e global, entao decks antigos primeiro
ORDEM = ['V064', 'V065', 'V066', 'V067', 'V068', 'V069',
         'V070', 'V071', 'V072', 'V073']


def normal(s):
    return re.sub(r'[^a-z0-9]+', '', unicodedata.normalize('NFKD', s or '')
                  .encode('ascii', 'ignore').decode().lower())


def _duracao(caminho):
    """Segundos de um .wav, lendo so o cabecalho."""
    try:
        import wave, contextlib
        with contextlib.closing(wave.open(caminho, 'rb')) as w:
            return w.getnframes() / float(w.getframerate() or 1)
    except Exception:
        return 0.0


def achar_state():
    cands = [os.path.join(os.path.expanduser('~'), '.yovoice', 'state.json')]
    if os.environ.get('USERPROFILE'):
        cands.insert(0, os.path.join(os.environ['USERPROFILE'], '.yovoice', 'state.json'))
    if os.environ.get('YOVOICE'):
        cands.insert(0, os.environ['YOVOICE'])
    for c in cands:
        if os.path.exists(c): return c
    raise SystemExit('nao achei o state.json do yovoice. Procurei em:\n  '
                     + '\n  '.join(cands))


def main(quais):
    cam = achar_state()
    st = json.load(open(cam, encoding='utf-8'))
    hist = sorted(st.get('history', []), key=lambda h: h.get('createdAt', ''))
    saida = os.path.dirname(cam)
    outputs = os.path.join(saida, 'outputs')
    print(f'{len(hist)} falas no historico do yovoice')

    livres = list(hist)
    relatorio = []
    suspeitos = []
    for vid in ORDEM:
        cm = os.path.join(MANIF, vid + '.json')
        if not os.path.exists(cm): continue
        man = json.load(open(cm, encoding='utf-8'))
        pares, faltam = [], []
        for m in man:
            alvo = normal(m['texto']); achou = None
            for h in livres:
                t = normal(h.get('title'))
                if t and alvo.startswith(t[:40]): achou = h; break
            if achou: livres.remove(achou); pares.append((m, achou))
            else: faltam.append(m)
        if vid not in quais and quais: continue
        if not pares:
            relatorio.append((vid, 0, len(man), 'nada gravado'))
            continue

        destino = os.path.join(AQUI, 'out-' + vid.lower(), 'narracao')
        os.makedirs(destino, exist_ok=True)
        copiados = 0
        for m, h in pares:
            orig = os.path.join(outputs, h.get('fileName') or '')
            if not os.path.exists(orig): continue
            arq = m['chave'].replace(':', '-') + '.wav'
            shutil.copy2(orig, os.path.join(destino, arq))
            copiados += 1
            # take ruim: o yovoice as vezes desanda e gera minutos de fala
            # onde cabiam segundos. Um 14-rev de 11 minutos passou despercebido
            # porque nada conferia a DURACAO - so se o arquivo existia.
            # a duracao vem do ARQUIVO, nao do registro do app: o state.json
            # do yovoice ja declarou 20 s para um .wav de 11 minutos.
            real = _duracao(os.path.join(destino, arq)) or (h.get('duration') or 0)
            prev = m.get('dur') or 1
            if real > prev * 2.2 + 5 or (real and real < prev * .35):
                suspeitos.append((vid, arq, real, prev))
        relatorio.append((vid, copiados, len(man),
                          'completo' if not faltam else f'faltam {len(faltam)}'))

    print()
    print('  video   copiadas  estado')
    print('  ' + '-' * 34)
    for vid, c, tot, est in relatorio:
        print(f'  {vid}    {c:>3}/{tot}   {est}')
    print()
    if suspeitos:
        print('TAKES SUSPEITOS (duracao fora do esperado) - regrave estes:')
        for vid, arq, real, prev in suspeitos:
            print(f'  {vid} {arq}: {real:.0f}s gravados contra {prev:.0f}s de texto')
        print()
    incompletos = [v for v, c, t, e in relatorio if e != 'completo']
    if incompletos:
        print('Falta gravar no yovoice: ' + ', '.join(incompletos))
        print('O que ja veio e usado assim mesmo; o motor sintetiza o resto.')
    else:
        print('Tudo no lugar. Pode renderizar.')


if __name__ == '__main__':
    main([a.upper() for a in sys.argv[1:]])
