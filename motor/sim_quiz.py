#!/usr/bin/env python3
"""O QUIZ, sob o mesmo contrato dos outros simuladores.

O quizengine nasceu antes do catalogo e tem CLI propria
('quizengine.py render decks/x.json out16'). Em vez de abrir excecao para
ele no renderizar.py - que foi exatamente o erro dos tres simuladores com
contrato proprio, e que fez o V001 sair vazio com 'ok' no relatorio -
o adaptador vem para ca.

A unidade do quiz e fina: ela aponta para um DECK e diz onde esta a
narracao. O conteudo de verdade vive no deck, que e o formato que o
quizengine ja sabe ler e que o checar_deck() ja sabe reprovar.

    {"id": "V064", "deck": "v01-palavras.json",
     "narracao": "outvoz/narracao", "formato": "16:9"}

A regra da voz continua valendo: qualquer .wav em <dir>/narracao/ VENCE a
voz sintetica, e o que faltar o motor sintetiza. Da para entregar um video
pela metade da gravacao pronta.
"""
import json, os, shutil, subprocess, sys

RAIZ = os.path.dirname(os.path.abspath(__file__))


def construir(u, seed=201, saida='quiz.mp4', dirsaida='out-quiz'):
    deck = u.get('deck')
    if not deck:
        raise SystemExit("unidade de quiz sem 'deck'")
    cam_deck = deck if os.path.isabs(deck) else os.path.join(RAIZ, 'decks', deck)
    if not os.path.exists(cam_deck):
        raise SystemExit(f'deck nao encontrado: {cam_deck}')

    os.makedirs(dirsaida, exist_ok=True)
    # a narracao gravada entra ANTES do render: o motor procura por ela em
    # <dir>/narracao/ e so sintetiza o que nao achar
    fonte = u.get('narracao')
    if fonte:
        orig = fonte if os.path.isabs(fonte) else os.path.join(RAIZ, fonte)
        destino = os.path.join(dirsaida, 'narracao')
        if os.path.isdir(orig):
            os.makedirs(destino, exist_ok=True)
            n = 0
            for f in os.listdir(orig):
                if f.endswith('.wav'):
                    shutil.copy2(os.path.join(orig, f), os.path.join(destino, f))
                    n += 1
            print(f'  {n} falas gravadas copiadas de {fonte}')
        else:
            print(f'  aviso: narracao {orig} nao existe, vai sintetizar tudo')

    amb = dict(os.environ, SEED=str(seed))
    if u.get('voz'): amb['VOZ'] = u['voz']
    cmd = [sys.executable, os.path.join(RAIZ, 'quizengine.py'),
           'short' if u.get('formato') == '9:16' else 'render', cam_deck, dirsaida]
    r = subprocess.run(cmd, env=amb, cwd=RAIZ)
    if r.returncode != 0:
        raise SystemExit(f'quizengine falhou com codigo {r.returncode}')

    # o quizengine escreve final.mp4 no 16:9 e short.mp4 no 9:16;
    # o catalogo espera <ID>.mp4
    feito = os.path.join(dirsaida,
                         'short.mp4' if u.get('formato') == '9:16'
                         else 'final.mp4')
    alvo = os.path.join(dirsaida, saida)
    if os.path.exists(feito) and feito != alvo:
        shutil.move(feito, alvo)
        # o meta.json aponta para o nome antigo; sem isso o VERIFY procura um
        # arquivo que nao existe mais e quebra. Renomear sem avisar o registro
        # e criar um valor fantasma: o arquivo diz uma coisa, o disco tem outra.
        cam_meta = os.path.join(dirsaida, 'meta.json')
        if os.path.exists(cam_meta):
            m = json.load(open(cam_meta, encoding='utf-8'))
            m['out'] = os.path.basename(alvo)
            json.dump(m, open(cam_meta, 'w', encoding='utf-8'),
                      indent=1, ensure_ascii=False)


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 201,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-quiz')
