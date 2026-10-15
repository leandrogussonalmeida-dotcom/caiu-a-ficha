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


def _falas_faltando(u, cam_deck, dirsaida):
    """Chaves que o render vai precisar e para as quais nao existe .wav.

    Para o Short so contam as duas perguntas escolhidas; para o longo, todas.
    E so olha onde o motor realmente procura: a pasta do longo quando ha
    `narr`, a pasta de saida quando nao ha.
    """
    deck = json.load(open(cam_deck, encoding='utf-8'))
    n = len(deck.get('perguntas', []))
    if u.get('formato') == '9:16':
        idx = [i for i in (u.get('perguntas') or []) if 0 <= i < n]
        partes = ('q', 'rev')          # no Short as alternativas nao sao lidas
    else:
        # o longo pode levar um subconjunto: so cobra o que vai ao ar
        idx = [i for i in (u.get('perguntas') or range(n)) if 0 <= i < n]
        partes = ('q', 'opts', 'rev')

    base = u.get('narr') or u.get('narracao') or ''
    base = base if os.path.isabs(base) else os.path.join(RAIZ, base)
    if os.path.basename(base.rstrip('/\\')) != 'narracao':
        base = os.path.join(base, 'narracao')
    if not os.path.isdir(base):
        base = os.path.join(dirsaida, 'narracao')

    falta = []
    for i in idx:
        for p in partes:
            arq = f'{i}-{p}.wav'
            if not os.path.exists(os.path.join(base, arq)): falta.append(arq)
    return falta


def construir(u, seed=201, saida='quiz.mp4', dirsaida='out-quiz'):
    deck = u.get('deck')
    if not deck:
        raise RuntimeError("unidade de quiz sem 'deck'")
    cam_deck = deck if os.path.isabs(deck) else os.path.join(RAIZ, 'decks', deck)
    if not os.path.exists(cam_deck):
        raise RuntimeError(f'deck nao encontrado: {cam_deck}')

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

    # ---- portao: nenhum video sai meio sintetizado sem avisar.
    # O motor sintetiza o que faltar, e isso e util para rascunho - mas numa
    # peca do catalogo significa a voz do canal trocando no meio do video,
    # e o unico aviso era uma linha no log que ninguem le.
    if not u.get('permitir_sintetico'):
        falta = _falas_faltando(u, cam_deck, dirsaida)
        if falta:
            raise RuntimeError(
                f"{u.get('id')}: faltam {len(falta)} falas gravadas "
                f"(a primeira e {falta[0]}). Grave no yovoice e rode o 3-VOZ, "
                f"ou ponha \"permitir_sintetico\": true na unidade para aceitar "
                f"a voz sintetica no lugar.")

    amb = dict(os.environ, SEED=str(seed))
    if u.get('voz'): amb['VOZ'] = u['voz']

    curto = u.get('formato') == '9:16'
    cmd = [sys.executable, os.path.join(RAIZ, 'quizengine.py'),
           'short' if curto else 'render', cam_deck, dirsaida]

    # O longo normalmente leva o deck inteiro, mas pode levar um subconjunto:
    # e assim que uma peca sai so com as perguntas que tem voz gravada, em vez
    # de meio video na voz dele e meio numa voz sintetica.
    if not curto and u.get('perguntas'):
        cmd += [','.join(str(i) for i in u['perguntas']), '0']

    if curto:
        # O Short NAO regrava voz: ele reaproveita os .wav do longo.
        # NARR aponta para a pasta do longo, VELOC acelera sem mudar o tom e
        # REUSO faz a tela mostrar o fato LONGO, que e o que existe gravado.
        # Sem REUSO a fala e o texto na tela nao batem.
        if u.get('narr'):
            # NARR e a pasta do LONGO; o motor acrescenta 'narracao' sozinho.
            # Apontar direto para .../narracao faz ele procurar em
            # .../narracao/narracao e nao achar nada - e o Short sai todo
            # sintetizado sem dizer uma palavra sobre isso.
            n = u['narr'] if os.path.isabs(u['narr']) else os.path.join(RAIZ, u['narr'])
            if os.path.basename(n.rstrip('/\\')) == 'narracao':
                n = os.path.dirname(n.rstrip('/\\'))
            amb['NARR'] = n
            amb['REUSO'] = '1'
            amb['VELOC'] = str(u.get('veloc', 1.18))
        # duas perguntas, escolhidas a dedo: as melhores quase nunca sao vizinhas,
        # e tres estouram os 60 s (abaixo de 60 o Short roda em laco)
        perg = u.get('perguntas')
        if not perg:
            raise RuntimeError(f"{u.get('id')}: Short de quiz sem 'perguntas'")
        cmd += [','.join(str(i) for i in perg), '0']

        # visual proprio: o Short nao pode parecer o longo nem os outros Shorts
        if u.get('fundo') or u.get('paleta') or u.get('trilha'):
            d = json.load(open(cam_deck, encoding='utf-8'))
            for campo in ('fundo', 'paleta', 'trilha'):
                if u.get(campo): d[campo] = u[campo]
            d['fala_intro_short'] = ''      # a vinheta faz a abertura
            d['fala_outro_short'] = ''
            cam_deck = os.path.join(dirsaida, 'deck-derivado.json')
            json.dump(d, open(cam_deck, 'w', encoding='utf-8'), ensure_ascii=False)
            cmd[3] = cam_deck

    # intro/outro desligaveis pela unidade. Fala vazia o motor descarta, entao
    # nao ha o que sintetizar: a vinheta faz a abertura.
    if any(k in u for k in ('intro', 'outro')):
        d = json.load(open(cam_deck, encoding='utf-8'))
        for k in ('intro', 'outro'):
            if k in u: d[k] = u[k]
        cam_deck = os.path.join(dirsaida, 'deck-ajustado.json')
        json.dump(d, open(cam_deck, 'w', encoding='utf-8'), ensure_ascii=False)
        cmd[3] = cam_deck

    r = subprocess.run(cmd, env=amb, cwd=RAIZ)
    if r.returncode != 0:
        raise RuntimeError(f'quizengine falhou com codigo {r.returncode}')

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
