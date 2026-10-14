#!/usr/bin/env python3
"""Titulo, descricao e hashtags de cada peca, prontos para colar.

    python publicar.py            # todas as pecas que tem unidade
    python publicar.py A1 V007    # so estas
    python publicar.py --planilha # so o catalogo.csv

Sai em PUBLICAR/: um .txt por peca e um catalogo.csv com tudo.

O canal nao tem voz. Entao **a educacao inteira mora na descricao** - e por
isso que o formato funciona sem narracao. A descricao carrega o que o video
mostra em 30 segundos: de onde vem cada numero, e principalmente a RESSALVA.

A ressalva e o ponto. "O falcao faz 389 km/h" sozinho engana; "em mergulho,
nao em voo nivelado" e o que separa um canal de numeros de um canal de
numeros confiavel. Todas as notas que escrevi nas unidades vem para ca.

O TITULO leva o numero na frente. Foi o que a analise da referencia mostrou:
o numero no titulo e o que ganha o clique, nao o adjetivo.
"""
import csv, json, os, re, sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.environ.get('CF_PUBLICAR') or (
    os.path.join(os.path.dirname(RAIZ), 'PUBLICAR')
    if os.path.basename(RAIZ) == '_motor' else os.path.join(RAIZ, 'publicar'))
UNID = os.path.join(RAIZ, 'unidades')

TAGS_FIXAS = ['#caiuaficha', '#curiosidades']
CHAVES = ('unidades', 'marcos', 'marcas', 'passos', 'camadas',
          'corredores', 'desenhos', 'itens')


def _num(v):
    """Numero do jeito brasileiro: ponto no milhar, virgula no decimal."""
    if abs(v - round(v)) < 1e-9:
        return f'{int(round(v)):,}'.replace(',', '.')
    return f'{v:,.2f}'.rstrip('0').rstrip('.').replace(',', '@') \
                      .replace('.', ',').replace('@', '.')


def itens_de(d):
    return next((d[k] for k in CHAVES if isinstance(d.get(k), list) and d[k]), [])


def maior_razao(d):
    """Nas comparacoes, o titulo e a RAZAO, nao o valor absoluto.
    '700 m' nao diz nada; '18 Cristos empilhados' diz tudo."""
    melhor, rot = None, ''
    for it in itens_de(d):
        if not isinstance(it, dict) or 'alvo' not in it: continue
        a, b = it['ref'], it['alvo']
        if not a.get('valor'): continue
        r = b['valor'] / a['valor']
        if melhor is None or r > melhor:
            melhor, rot = r, a.get('rotulo') or a['nome']
    return melhor, rot


def maior_numero(d):
    """O maior numero da peca. E ele que vira o titulo."""
    itens, un = itens_de(d), d.get('unidade', '')
    melhor, rot = None, ''
    for it in itens:
        if not isinstance(it, dict): continue
        for campo in ('v', 't', 'ate', 'valor'):
            if campo in it and isinstance(it[campo], (int, float)):
                if melhor is None or it[campo] > melhor:
                    melhor, rot = it[campo], it.get('nome', '')
        alvo = it.get('alvo')
        if alvo and isinstance(alvo.get('valor'), (int, float)):
            if melhor is None or alvo['valor'] > melhor:
                melhor, rot, un = alvo['valor'], alvo.get('nome', ''), alvo.get('un', un)
    if melhor is None and isinstance(d.get('geracoes'), int):
        melhor = d['por_geracao'] ** d['geracoes']
        rot, un = f"{d['geracoes']} passos", ''
    return melhor, rot, un


def titulo(d):
    """Numero na frente. O adjetivo nao ganha clique; o numero ganha."""
    base = d['titulo'].strip()
    r, rot_r = maior_razao(d)
    if r is not None and r >= 2:
        return f'{base} — {_num(round(r, 1))}x {rot_r}'
    n, rot, un = maior_numero(d)
    if n is None: return base
    if n >= 1e12: txt = f'{n/1e12:.1f}'.replace('.0', '').replace('.', ',') + ' TRILHOES'
    elif n >= 1e9: txt = f'{n/1e9:.1f}'.replace('.0', '').replace('.', ',') + ' BILHOES'
    elif n >= 1e6: txt = f'{n/1e6:.1f}'.replace('.0', '').replace('.', ',') + ' MILHOES'
    else: txt = _num(n)
    alvo = f'{txt} {un}'.strip()
    if alvo.lower() in base.lower(): return base
    return f'{base} — {alvo}'


def fatos(d, limite=8):
    out, un = [], d.get('unidade', '')
    for it in itens_de(d):
        if not isinstance(it, dict): continue
        nome = it.get('nome') or (it.get('alvo') or {}).get('nome')
        if not nome: continue
        nota = f" ({it['nota']})" if it.get('nota') else ''
        if 'alvo' in it:
            a, b = it['ref'], it['alvo']
            vezes = b['valor'] / a['valor'] if a['valor'] else 0
            out.append(f"{b['nome']}: {_num(b['valor'])} {b.get('un','')} — "
                       f"{_num(round(vezes,1))}x {a['nome']}{nota}")
            continue
        for campo in ('v', 't', 'ate', 'valor'):
            if campo in it and isinstance(it[campo], (int, float)):
                out.append(f'{nome}: {_num(it[campo])} {un}'.strip() + nota)
                break
        else:
            if it.get('ancora'): out.append(f"{nome} — {it['ancora']}")
            else: out.append(nome)
    return out[:limite]


def fontes(d):
    f = {d['fonte']} if d.get('fonte') else set()
    for it in itens_de(d):
        if isinstance(it, dict) and it.get('fonte'): f.add(it['fonte'])
    # fonte do item igual a do documento nao precisa aparecer duas vezes
    f.discard('ver fonte do documento'); f.discard('calculo')
    return sorted(f)


def descricao(d, curto=False):
    L = []
    if d.get('chamada'): L += [d['chamada'], '']
    fs = fatos(d, 4 if curto else 8)
    if fs: L += ['\n'.join('• ' + x for x in fs), '']
    if d.get('nota'):
        # a ressalva vem ANTES das fontes, porque e o que o espectador
        # precisa ler para nao sair com a ideia errada
        L += ['⚠ ' + d['nota'], '']
    fo = fontes(d)
    if fo: L += ['Fontes:', '\n'.join('— ' + x for x in fo), '']
    tags = TAGS_FIXAS + [t for t in d.get('tags', []) if t not in TAGS_FIXAS]
    L += ['Tudo neste canal e feito por codigo: o fundo, a trilha e a animacao.',
          '', ' '.join(tags[:6])]
    return '\n'.join(L).strip()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    so_planilha = '--planilha' in sys.argv
    plano = json.load(open(os.path.join(RAIZ, 'plano-280.json'), encoding='utf-8'))
    pecas = []
    for v in plano['videos']:
        arq = os.path.join(UNID, v['unidade'])
        if os.path.exists(arq):
            pecas.append((v, json.load(open(arq, encoding='utf-8')), False))
    # O Short mostra menos itens que o longo. A legenda tem de descrever O
    # SHORT: listar seis numeros num video que mostra dois e prometer o que
    # nao se entrega. Por isso o mesmo corte do shorts.py entra aqui.
    import shorts as _sh
    for s in plano['shorts']:
        pai = next(x for x in plano['videos'] if x['id'] == s['pai'])
        arq = os.path.join(UNID, pai['unidade'])
        if os.path.exists(arq):
            du = json.load(open(arq, encoding='utf-8'))
            quantos, _ = _sh.RECEITA.get(s['simulador'], (2, {}))
            pecas.append((s, _sh.cortar(du, quantos), True))
    if args:
        alvos = {a.upper() for a in args}
        pecas = [p for p in pecas if p[0]['id'] in alvos or p[0]['serie'] in alvos]

    os.makedirs(SAIDA, exist_ok=True)
    linhas = []
    for meta, d, curto in pecas:
        t = titulo(d)
        if curto:
            # titulo igual ao do longo vira duplicata no feed. O Short entra
            # com a pergunta; o longo, com a afirmacao.
            n, _, un = maior_numero(d)
            r, rot_r = maior_razao(d)
            if r is not None and r >= 2:
                t = f'Quantos {rot_r.capitalize()} cabem nisso?'
            elif n is not None:
                t = f'{_num(n)} {un}'.strip() + '. Voce imaginava?'
            else:
                t = d['titulo'].strip() + ' #shorts'
            if '#shorts' not in t: t += ' #shorts'
        txt = descricao(d, curto)
        if not so_planilha:
            with open(os.path.join(SAIDA, f"{meta['id']}.txt"), 'w',
                      encoding='utf-8') as fh:
                fh.write(f'TITULO\n{t}\n\nDESCRICAO\n{txt}\n')
        linhas.append({'id': meta['id'], 'tipo': 'Short' if curto else 'longo',
                       'serie': meta['serie'], 'titulo': t,
                       'tema': meta.get('tema', ''),
                       'confianca': d.get('confianca', ''),
                       'fontes': ' | '.join(fontes(d))})
    with open(os.path.join(SAIDA, 'catalogo.csv'), 'w', encoding='utf-8-sig',
              newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader(); w.writerows(linhas)
    print(f'{len(linhas)} pecas em {SAIDA}')
    print(f"  {sum(1 for l in linhas if l['tipo']=='longo')} longos · "
          f"{sum(1 for l in linhas if l['tipo']=='Short')} Shorts")


if __name__ == '__main__':
    main()
