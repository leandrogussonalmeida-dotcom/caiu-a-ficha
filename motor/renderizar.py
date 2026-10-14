#!/usr/bin/env python3
"""Roda o catálogo. É este arquivo que transforma o repositório em vídeos.

    python renderizar.py            # o que der para renderizar agora
    python renderizar.py A1         # só a série A1
    python renderizar.py V007       # só uma peça
    python renderizar.py --faltam   # o que falta de conteúdo, sem renderizar

Ele não decide nada: lê `plano-280.json` (quem é o simulador, qual a cara,
qual a seed) e `unidades/<arquivo>.json` (os dados e as fontes). Se a unidade
não existe, a peça é pulada e aparece na lista do fim — é o jeito de separar
**o que falta de código** do **que falta de conteúdo**, que são gargalos
diferentes e quase sempre o segundo.

Retomável de propósito: peça já renderizada é pulada. Um lote de 20 vídeos
leva horas, e nenhuma delas pode ser perdida porque a máquina dormiu.
"""
import importlib, json, os, subprocess, sys, time, traceback

RAIZ = os.path.dirname(os.path.abspath(__file__))
# rodando de dentro de _motor (a cópia no PC), os vídeos saem na pasta de
# cima, ao lado do motor, e não escondidos dentro dele
SAIDA = os.environ.get('CF_SAIDA') or (
    os.path.join(os.path.dirname(RAIZ), 'VIDEOS')
    if os.path.basename(RAIZ) == '_motor' else os.path.join(RAIZ, 'saida'))
UNID = os.path.join(RAIZ, 'unidades')


def conferir(mp4):
    """Confere que saiu vídeo de verdade, e não um arquivo vazio.

    O V001 saiu com zero stream e o relatório disse 'ok': o simulador tinha
    outro contrato, recebeu o dicionário no lugar da lista e o ffmpeg fechou
    sem nada. Um lote de vinte peças pode sair inteiro assim, e só se
    descobre ao abrir um por um. Agora cada peça é aberta aqui."""
    if not os.path.exists(mp4) or os.path.getsize(mp4) < 50_000:
        return 'arquivo vazio ou pequeno demais'
    try:
        r = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=codec_type,nb_frames',
             '-show_entries', 'format=duration', '-of', 'default=nw=1', mp4],
            capture_output=True, text=True, timeout=60)
    except Exception as e:
        return f'ffprobe falhou: {e}'
    if r.returncode != 0 or 'codec_type=video' not in r.stdout:
        return 'sem fluxo de vídeo'
    for ln in r.stdout.splitlines():
        if ln.startswith('duration=') and float(ln.split('=')[1] or 0) < 3.0:
            return 'duração menor que 3 s'
    return None


def carregar(nome):
    if RAIZ not in sys.path: sys.path.insert(0, RAIZ)
    return importlib.import_module(nome)


def uma(v, forcar=False):
    """Renderiza uma peça. Devolve ('ok'|'pulou'|'sem-unidade'|'erro', texto)."""
    dest = os.path.join(SAIDA, v['id'])
    mp4 = os.path.join(dest, f"{v['id']}.mp4")
    if os.path.exists(mp4) and not forcar:
        return 'pulou', f"{v['id']} já existe"
    arq = os.path.join(UNID, v['unidade'])
    if not os.path.exists(arq):
        return 'sem-unidade', f"{v['id']} {v['serie']} · {v['tema']}"
    u = json.load(open(arq, encoding='utf-8'))
    # PORTAO: unidade que nao passa na conferencia nao vira video. Enquanto
    # o checar.py era cego a metade dos formatos, ele so dizia "sem itens" e
    # o conteudo passava sem conferencia nenhuma - quatro videos foram
    # entregues com numeros sem fonte declarada. O portao fecha isso por
    # construcao, nao por disciplina.
    import checar
    erros, _avisos = checar.checar_unidades(arq)
    if erros:
        return 'reprovado', f"{v['id']} reprovado na conferencia: " + '; '.join(erros)
    # a cara vem do plano, não da unidade: é o plano que garante que ninguém
    # repete. Uma unidade que traz a própria paleta seria um furo nisso.
    u['paleta' if v['motor'] == 'pixel' else 'estilo'] = v['aparencia']
    mod = carregar(v['simulador'])
    os.makedirs(dest, exist_ok=True)
    t0 = time.time()
    mod.construir(u, seed=v['seed'], saida=f"{v['id']}.mp4", dirsaida=dest)
    ruim = conferir(mp4)
    if ruim:
        return 'erro', f"{v['id']} rodou mas o vídeo não presta: {ruim}"
    return 'ok', f"{v['id']} em {time.time()-t0:.0f}s"


def _portao_fontes():
    """Confere as fontes ANTES de comecar. Falhar no primeiro segundo e
    barato; falhar depois de duas horas de maquina, no video 178, nao e -
    foi exatamente o que aconteceu na primeira vez que isso rodou fora da
    minha maquina."""
    try:
        import fontes as FT
    except ImportError:
        return
    faltam = FT.conferir()
    if faltam:
        print()
        print('  [x] Faltam fontes, e sem elas NADA renderiza:')
        for n in faltam: print('      -', n)
        print()
        print(f'      Elas deveriam estar em {FT.AQUI}')
        print('      Se a pasta fontes nao veio junto, baixe o motor de novo.')
        print()
        raise SystemExit(1)


def main():
    _portao_fontes()
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    so_faltam = '--faltam' in sys.argv
    forcar = '--forcar' in sys.argv
    plano = json.load(open(os.path.join(RAIZ, 'plano-280.json'), encoding='utf-8'))
    fila = plano['videos']
    if args:
        alvos = {a.upper() for a in args}
        fila = [v for v in fila if v['id'] in alvos or v['serie'] in alvos
                or v['simulador'] in {a.lower() for a in args}]
    if not fila:
        sys.exit(f'nada bate com {args!r}')

    os.makedirs(SAIDA, exist_ok=True)
    contas = {'ok': 0, 'pulou': 0, 'sem-unidade': 0, 'erro': 0, 'reprovado': 0}
    faltam, t0 = [], time.time()
    for n, v in enumerate(fila, 1):
        if so_faltam:
            if not os.path.exists(os.path.join(UNID, v['unidade'])):
                faltam.append(f"{v['id']} {v['serie']} · {v['tema']}")
            continue
        print(f"[{n}/{len(fila)}] {v['id']} {v['simulador']} {v['aparencia']}", flush=True)
        try:
            st, msg = uma(v, forcar)
        except Exception:
            st, msg = 'erro', f"{v['id']}\n{traceback.format_exc()}"
        contas[st] += 1
        if st == 'sem-unidade': faltam.append(msg)
        if st in ('erro', 'reprovado'): print('  ' + msg, flush=True)

    if so_faltam:
        # painel por serie: e a unica forma de olhar 280 pecas e entender
        # onde esta o trabalho. O total sozinho nao diz nada.
        por = {}
        for v in plano['videos']:
            tem = os.path.exists(os.path.join(UNID, v['unidade']))
            feito = os.path.exists(os.path.join(SAIDA, v['id'], v['id'] + '.mp4'))
            d = por.setdefault((v['serie'], v['rotulo']), [0, 0, 0])
            d[0] += 1
            d[1] += 1 if tem else 0
            d[2] += 1 if feito else 0
        print()
        print('  serie                          total  escritas  rendidas')
        print('  ' + '-' * 56)
        tt = ew = rr = 0
        for (sr, rot), (t, w, r) in sorted(por.items()):
            barra = '#' * round(w / t * 10) + '.' * (10 - round(w / t * 10))
            print(f'  {sr} {rot[:24]:<25} {t:>4}  {w:>6}  {r:>7}  {barra}')
            tt += t; ew += w; rr += r
        print('  ' + '-' * 56)
        print(f'  {"TOTAL":<29} {tt:>4}  {ew:>6}  {rr:>7}'
              f'   ({ew/tt*100:.0f}% escrito)')
        print(f'\n  Shorts: {len(plano["shorts"])} planejados, saem dos longos '
              f'prontos.')
        if faltam:
            print(f'\n  as {len(faltam)} proximas sem unidade:')
            for f in faltam[:12]: print('    ', f)
            if len(faltam) > 12: print(f'     ... e mais {len(faltam)-12}')
        return
    dt = time.time() - t0
    print(f"\nfeitos {contas['ok']} · pulados {contas['pulou']} · "
          f"sem unidade {contas['sem-unidade']} · reprovados "
          f"{contas['reprovado']} · erros {contas['erro']} · {dt/60:.0f} min")
    if faltam:
        print('\nfalta escrever a unidade de:')
        for f in faltam: print('  ', f)


if __name__ == '__main__':
    main()
