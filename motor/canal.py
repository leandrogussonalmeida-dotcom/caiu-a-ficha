#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — produção do canal inteiro num comando (roda no PC).

    python3 canal.py lista              # o que está pronto, o que já foi renderizado
    python3 canal.py textos             # títulos e descrições de tudo (rápido)
    python3 canal.py longos [ep02 ...]  # vídeos longos prontos -> ../VIDEOS
    python3 canal.py cortes [ep02 ...]  # Shorts cortados dos longos -> ../SHORTS/CORTES
    python3 canal.py ritmo              # Shorts NO RITMO -> ../SHORTS/NO RITMO

Só entra o episódio com estado 'pronto' no `catalogo.py` (roteiro + desenho +
checagem de fatos aprovados). Pula o que já existe e passa no verificador:
dá para fechar a janela e rodar de novo, ele continua de onde parou.
"""
import importlib, os, subprocess, sys, unicodedata
import catalogo as CAT

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
VIDEOS = os.path.join(RAIZ, 'VIDEOS')
CORTES = os.path.join(RAIZ, 'SHORTS', 'CORTES')
RITMO = os.path.join(RAIZ, 'SHORTS', 'NO RITMO')
PUBLICAR = os.path.join(RAIZ, 'PUBLICAR')


def slug(txt):
    t = unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode().lower()
    return '-'.join(''.join(c if c.isalnum() else ' ' for c in t).split())[:60]


def prontos(ids=None):
    eps = [e for e in CAT.EPISODIOS if e['estado'] == 'pronto']
    return [e for e in eps if not ids or e['id'] in ids]


def arquivo_longo(e):
    return os.path.join(VIDEOS, f"{e['id']}-{slug(e['titulo'])}.mp4")


def ok_longo(c, roteiro):
    if not os.path.exists(c): return False
    r = subprocess.run([sys.executable, 'longo_verificar.py', c, roteiro], capture_output=True, text=True)
    return r.returncode == 0


def textos():
    import longo_publicar as LP
    os.makedirs(os.path.join(PUBLICAR, 'LONGOS'), exist_ok=True)
    os.makedirs(os.path.join(PUBLICAR, 'CORTES'), exist_ok=True)
    n = 0
    for e in prontos():
        tit, desc = LP.montar(f"{e['id']}_roteiro")
        open(os.path.join(PUBLICAR, 'LONGOS', f"{e['id']}-{slug(e['titulo'])}.txt"), 'w', encoding='utf-8').write(
            f"TÍTULO\n{tit}\n\nDESCRIÇÃO\n{desc}\n\nMINIATURA\n(a fazer)\n")
        n += 1
        R = importlib.import_module(f"{e['id']}_roteiro")
        for c in getattr(R, 'CORTES', []):
            nome = f"{R.PREFIXO}-{c['id']}"
            d = (f"{c['descricao']}\n\nVídeo completo no canal: {R.TITULO.split('|')[0].strip()}.\n\n"
                 f"#shorts #comofunciona #pixelart #nossomundopixel")
            open(os.path.join(PUBLICAR, 'CORTES', nome + '.txt'), 'w', encoding='utf-8').write(
                f"TÍTULO\n{c['titulo']}\n\nDESCRIÇÃO\n{d}\n\nMINIATURA\n(a fazer)\n")
            n += 1
    subprocess.run([sys.executable, 'ritmo_publicar.py', os.path.join(PUBLICAR, 'NO RITMO')], check=False)
    print(f"{n} textos de longos e cortes em {PUBLICAR}")


def longos(ids=None):
    os.makedirs(VIDEOS, exist_ok=True)
    for e in prontos(ids):
        c = arquivo_longo(e)
        rot = f"{e['id']}_roteiro"
        if ok_longo(c, rot):
            print(e['id'], 'já pronto', flush=True); continue
        print(e['id'], 'renderizando (10-30 min)...', flush=True)
        # cada episódio no seu próprio processo: paleta e estado de um não vazam para o outro
        subprocess.run([sys.executable, f"{e['id']}_motor.py", c], check=False)
        print(e['id'], 'PASSOU' if ok_longo(c, rot) else 'REPROVOU: rode de novo ou me mande a tela', flush=True)


def cortes(ids=None):
    os.makedirs(CORTES, exist_ok=True)
    for e in prontos(ids):
        R = importlib.import_module(f"{e['id']}_roteiro")
        faltam = [c['id'] for c in getattr(R, 'CORTES', [])
                  if not os.path.exists(os.path.join(CORTES, f"{R.PREFIXO}-{c['id']}.mp4"))]
        if not faltam:
            print(e['id'], 'cortes já prontos', flush=True); continue
        subprocess.run([sys.executable, 'longo_short.py', f"{e['id']}_motor", CORTES] + faltam, check=False)


def ritmo():
    os.makedirs(RITMO, exist_ok=True)
    subprocess.run([sys.executable, 'ritmo_render.py', RITMO], check=False)


def lista():
    for e in CAT.EPISODIOS:
        feito = ''
        if e['estado'] == 'pronto':
            feito = 'vídeo OK' if os.path.exists(arquivo_longo(e)) else 'falta renderizar'
        print(f"{e['id']}  {CAT.SERIES[e['serie']]:18s} {e['estado']:7s} {feito:17s} {e['titulo']}")


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    cmd, args = sys.argv[1], sys.argv[2:]
    {'lista': lambda: lista(), 'textos': lambda: textos(), 'longos': lambda: longos(args),
     'cortes': lambda: cortes(args), 'ritmo': lambda: ritmo()}[cmd]()
