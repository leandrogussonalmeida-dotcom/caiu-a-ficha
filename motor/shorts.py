#!/usr/bin/env python3
"""Os 200 Shorts, cortados dos longos que ja existem.

    python shorts.py              # tudo o que der
    python shorts.py S001 S002    # so estes
    python shorts.py A1           # so os de uma serie
    python shorts.py --faltam     # o que falta

O Short NAO e um arquivo novo de conteudo. Ele e o MESMO dado do longo,
rodado pelo mesmo simulador com tres mudancas:

  1. menos itens — so o comeco e a virada, porque o Short vive de chegar
     rapido no numero que espanta;
  2. outra aparencia — paleta ou estilo diferente do pai, garantido pelo
     plano, para o feed nao parecer o mesmo video duas vezes;
  3. seed propria — trilha e sorteios diferentes.

Por que isso e honesto e nao preguica: o dado ja foi conferido uma vez, com
fonte. Cortar um video nao inventa numero nenhum. O que muda e o ritmo.

**O teto e 60 s.** Abaixo disso o Short roda em laco, e o laco e o que infla
a retencao. Cada simulador conta o tempo de um jeito, entao cada um tem a
sua receita de corte aqui embaixo — nao da para ter uma regra so.
"""
import importlib, json, os, subprocess, sys, time, traceback

RAIZ = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.environ.get('CF_SAIDA_SHORTS') or (
    os.path.join(os.path.dirname(RAIZ), 'SHORTS')
    if os.path.basename(RAIZ) == '_motor' else os.path.join(RAIZ, 'saida-shorts'))
UNID = os.path.join(RAIZ, 'unidades')
TETO = 58.0                      # segundos; abaixo de 60 o Short roda em laco

# chave da lista de itens de cada formato
CHAVES = ('unidades', 'marcos', 'marcas', 'passos', 'camadas',
          'corredores', 'desenhos', 'itens')

# simulador: (quantos itens manter, ajustes de duracao na unidade)
RECEITA = {
    'sim_escala':    (2, {'dur': 20}),
    'sim_fileira':   (2, {'dur': 16, 'batidas_por_item': 1}),
    'sim_planta':    (2, {'batidas_por_passo': 5}),
    'sim_viagem':    (0, {'dur': 26}),          # 0 = mantem todos os marcos
    'sim_extremo':   (4, {'batidas_por_passo': 3}),
    'sim_cadeia':    (0, {'geracoes': 24}),
    'sim_corrida':   (4, {'segundos': 18}),
    'sim_autodromo': (4, {'segundos': 20, 'voltas': 2}),
    'sim_descida':   (3, {'batidas_por_camada': 5}),
    'sim_estrada':   (0, {'segundos': 20}),
    'sim_revelar':   (2, {'dur': 18}),
    'sim_lousa':     (2, {'dur': 20}),
    'sim_traco':     (2, {'dur': 20}),
    'sim_torre':     (0, {'blocos': 26}),
    'sim_corda':     (0, {'duracao': 40}),
    'sim_ambiente':  (0, {'segundos': 45}),
}


def cortar(u, quantos):
    """Fica com o comeco e a virada. O meio e o que o Short nao tem tempo de
    contar — e o destaque, quando existe, e justamente a virada."""
    if not quantos: return u
    for k in CHAVES:
        lista = u.get(k)
        if not isinstance(lista, list) or len(lista) <= quantos: continue
        dest = [x for x in lista if isinstance(x, dict) and x.get('destaque')]
        fim = dest[-1] if dest else lista[-1]
        escolha, vistos = [], set()
        for x in list(lista[:quantos - 1]) + [fim]:
            marca = id(x)
            if marca not in vistos:
                vistos.add(marca); escolha.append(x)
        u[k] = escolha
    return u


def conferir(mp4):
    if not os.path.exists(mp4) or os.path.getsize(mp4) < 30_000:
        return 'arquivo vazio ou pequeno demais'
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                        '-show_entries', 'stream=codec_type',
                        '-show_entries', 'format=duration',
                        '-of', 'default=nw=1', mp4],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or 'codec_type=video' not in r.stdout:
        return 'sem fluxo de video'
    for ln in r.stdout.splitlines():
        if ln.startswith('duration='):
            d = float(ln.split('=')[1] or 0)
            if d < 5: return f'curto demais: {d:.0f}s'
            if d > TETO: return f'passou do teto de {TETO:.0f}s: {d:.1f}s'
    return None


# ------------------------------------------------- Shorts de quiz
# O Short de quiz nao se monta cortando itens: a unidade do quiz e fina
# (aponta para um deck). Aqui ficam as DUAS perguntas de cada Short e o
# visual proprio dele. Duas, nao tres: tres estouram os 60 s, e abaixo de
# 60 o Short roda em laco - e o laco e o que segura a retencao.
#
# Nenhuma combinacao de fundo e paleta se repete entre os 20 Shorts, nem
# bate com a do video longo de onde cada um saiu: o YouTube trata design
# repetido como conteudo repetido.
QUIZ_SHORTS = {
    'S064': dict(perguntas=[4, 17], fundo='aurora', paleta='menta', trilha='eletro'),
    'S065': dict(perguntas=[3, 17], fundo='grade', paleta='floresta', trilha='arcade'),
    'S066': dict(perguntas=[0, 8], fundo='ondas', paleta='ferrugem', trilha='eletro'),
    'S067': dict(perguntas=[0, 14], fundo='losangos', paleta='uva', trilha='arcade'),
    'S068': dict(perguntas=[2, 20], fundo='pixel', paleta='papel', trilha='eletro'),
    'S069': dict(perguntas=[21, 17], fundo='raios', paleta='floresta', trilha='arcade'),
    'S070': dict(perguntas=[6, 0], fundo='bolhas', paleta='ferrugem', trilha='eletro'),
    'S071': dict(perguntas=[0, 1], fundo='confete', paleta='uva', trilha='arcade'),
    'S072': dict(perguntas=[1, 23], fundo='synthwave', paleta='oceano', trilha='eletro'),
    'S073': dict(perguntas=[0, 17], fundo='pixel', paleta='menta', trilha='arcade'),
    'S144': dict(perguntas=[23, 10], fundo='raios', paleta='noite', trilha='neonwave'),
    'S145': dict(perguntas=[19, 24], fundo='bolhas', paleta='grafite', trilha='funk'),
    'S146': dict(perguntas=[2, 28], fundo='confete', paleta='brasa', trilha='neonwave'),
    'S147': dict(perguntas=[1, 16], fundo='bauhaus', paleta='oceano', trilha='funk'),
    'S148': dict(perguntas=[9, 19], fundo='aurora', paleta='noite', trilha='neonwave'),
    'S149': dict(perguntas=[23, 28], fundo='grade', paleta='grafite', trilha='funk'),
    'S150': dict(perguntas=[16, 26], fundo='ondas', paleta='brasa', trilha='neonwave'),
    'S151': dict(perguntas=[28, 25], fundo='losangos', paleta='neon', trilha='funk'),
    'S152': dict(perguntas=[0, 24], fundo='bauhaus', paleta='papel', trilha='neonwave'),
    'S153': dict(perguntas=[11, 12], fundo='hud', paleta='noite', trilha='funk'),
}

def um(s, plano, forcar=False):
    dest = os.path.join(SAIDA, s['id'])
    mp4 = os.path.join(dest, f"{s['id']}.mp4")
    if os.path.exists(mp4) and not forcar:
        return 'pulou', f"{s['id']} ja existe"
    pai = next(v for v in plano['videos'] if v['id'] == s['pai'])
    arq = os.path.join(UNID, pai['unidade'])
    if not os.path.exists(arq):
        return 'sem-unidade', f"{s['id']} (de {pai['id']}) · {s['tema']}"

    u = json.load(open(arq, encoding='utf-8'))
    import checar
    erros, _ = checar.checar_unidades(arq)
    if erros:
        return 'reprovado', f"{s['id']}: o pai {pai['id']} nao passa na conferencia"

    if s['simulador'] == 'sim_quiz':
        rec = QUIZ_SHORTS.get(s['id'])
        if not rec:
            return 'sem-receita', f"{s['id']}: Short de quiz sem perguntas escolhidas"
        u = dict(u, **rec)
        u['formato'] = '9:16'
        # a voz do longo vale para o Short: nunca regravar
        u['narr'] = u.get('narracao')
        u['id'] = s['id']
    else:
        quantos, ajustes = RECEITA.get(s['simulador'], (2, {}))
        u = cortar(u, quantos)
        u.update(ajustes)
        u['id'] = s['id']
        u['paleta' if s['motor'] == 'pixel' else 'estilo'] = s['aparencia']

    if RAIZ not in sys.path: sys.path.insert(0, RAIZ)
    mod = importlib.import_module(s['simulador'])
    os.makedirs(dest, exist_ok=True)
    t0 = time.time()
    mod.construir(u, seed=s['seed'], saida=f"{s['id']}.mp4", dirsaida=dest)
    ruim = conferir(mp4)
    if ruim:
        return 'erro', f"{s['id']} rodou mas o video nao presta: {ruim}"
    return 'ok', f"{s['id']} em {time.time()-t0:.0f}s"


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
    fila = plano['shorts']
    if args:
        alvos = {a.upper() for a in args}
        fila = [s for s in fila if s['id'] in alvos or s['serie'] in alvos
                or s['pai'] in alvos]
    if not fila: sys.exit(f'nada bate com {args!r}')

    os.makedirs(SAIDA, exist_ok=True)
    contas = {'ok': 0, 'pulou': 0, 'sem-unidade': 0, 'erro': 0, 'reprovado': 0}
    faltam, t0 = [], time.time()
    for n, s in enumerate(fila, 1):
        if so_faltam:
            pai = next(v for v in plano['videos'] if v['id'] == s['pai'])
            if not os.path.exists(os.path.join(UNID, pai['unidade'])):
                faltam.append(f"{s['id']} (de {pai['id']}) · {s['tema']}")
            continue
        print(f"[{n}/{len(fila)}] {s['id']} de {s['pai']} · {s['simulador']} "
              f"{s['aparencia']}", flush=True)
        try:
            st, msg = um(s, plano, forcar)
        # SystemExit NAO e Exception: sem isto, uma peca reprovada
        # derruba a fila inteira e as outras nunca rodam.
        except (Exception, SystemExit):
            st, msg = 'erro', f"{s['id']}\n{traceback.format_exc()}"
        contas[st] += 1
        if st == 'sem-unidade': faltam.append(msg)
        if st in ('erro', 'reprovado'): print('  ' + msg, flush=True)

    if so_faltam:
        print(f'{len(faltam)} Shorts sem o longo escrito:')
        for f in faltam[:15]: print('  ', f)
        if len(faltam) > 15: print(f'   ... e mais {len(faltam)-15}')
        return
    dt = time.time() - t0
    print(f"\nfeitos {contas['ok']} · pulados {contas['pulou']} · sem unidade "
          f"{contas['sem-unidade']} · reprovados {contas['reprovado']} · erros "
          f"{contas['erro']} · {dt/60:.0f} min")


if __name__ == '__main__':
    main()
