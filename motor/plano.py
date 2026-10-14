#!/usr/bin/env python3
"""Reserva a identidade de cada uma das 280 peças do canal.

Sorteio não serve. Em 80 seeds aleatórios saem repetições de aparência muito
antes do vídeo 80 — e repetição visual é exatamente o que a política de
conteúdo inautêntico do YouTube procura. A alocação é **reservada**: cada par
(simulador, aparência) é usado no máximo uma vez, e o `assert` no fim do
arquivo recusa o plano se algum repetir.

Aparência é a paleta no motor pixel e o estilo no motor alta. São coisas
diferentes, então andam em espaços separados e nunca disputam o mesmo slot.

Este arquivo é a fonte da verdade do catálogo: `renderizar.py` lê o JSON que
ele gera e não decide nada por conta própria.
"""
import json, sys

# as paletas que o motor tem de fato. 'marca' fica de fora de propósito: ela
# é a da vinheta, e a marca tem de sair idêntica em todo vídeo.
PALETAS = ['brasa', 'floresta', 'menta', 'neon', 'uva', 'gelo', 'carvao',
           'papelao', 'asfalto', 'espaco', 'mostarda', 'sangria']
ESTILOS = ['planta', 'editorial', 'bauhaus', 'noturno', 'jornal']

# série: (simulador, motor, [temas...])
SERIES = [
 ('A1', 'sim_escala',    'pixel', 'ESCALA BRASIL', [
   # todo tema da ESCALA tem de ser uma grandeza LINEAR: o simulador
   # escala a silhueta pela altura. Capacidade de estádio é contagem e
   # entraria errado aqui — foi para a escada, onde é honesta.
   'Cristo Redentor contra os prédios mais altos do Brasil',
   'O Pão de Açúcar contra as montanhas do Brasil',
   'Um ônibus contra os maiores bichos que já existiram',
   'Uma pessoa contra as ondas mais altas já surfadas',
   'O Brasil de norte a sul, contra as distancias do mundo']),
 ('A1', 'sim_planta',    'alta',  'ESCALA EM PLANTA', [
   'A Torre Eiffel contra o que o Brasil tem de mais alto',
   'Uma pessoa contra as maiores árvores do mundo',
   'Um carro popular contra os maiores veículos que já rodaram']),
 ('A2', 'sim_viagem',    'pixel', 'QUANTO TEMPO LEVA', [
   'A luz saindo do Sol até bater na sua janela',
   'De carro, sem parar, até a Lua',
   'Andando do Oiapoque ao Chuí',
   'Um avião até cada capital do Brasil',
   'Um dado atravessando a internet e dando a volta no mundo',
   'Uma carta de 1900 contra uma mensagem de hoje',
   'O som atravessando o Brasil de ponta a ponta',
   'Uma gota de chuva, da nuvem até o chão']),
 ('A3', 'sim_cadeia',    'pixel', 'REAÇÃO EM CADEIA', [
   'Dobrando uma folha de papel 50 vezes',
   'Um grão de arroz dobrando em cada casa do tabuleiro',
   'Um boato contado para duas pessoas por dia',
   'Uma célula se dividindo por 24 horas',
   'Um real rendendo juros por cem anos',
   'Um espirro num vagão de metrô lotado']),
 ('A4', 'sim_extremo',   'pixel', 'O LIMITE', [
   'Do morno até o mais quente que existe',
   'Do fresco até o zero absoluto',
   'Da superfície até a Fossa das Marianas',
   'Da caminhada até a velocidade da luz',
   'Da pressão do pneu até o centro de Júpiter',
   'Do sussurro até o som mais alto já registrado']),
 ('A5', 'sim_corrida',   'pixel', 'CORRIDA', [
   'Os bichos mais rápidos do Brasil, lado a lado',
   'Todos os meios de transporte na mesma pista',
   'Os homens mais rápidos da história, correndo juntos']),
 ('A5', 'sim_autodromo', 'pixel', 'AUTÓDROMO', [
   'Uma volta em Interlagos, no tempo de cada categoria',
   'Os traçados mais famosos do mundo, um por um',
   'A mesma volta, de bicicleta até Fórmula 1']),
 ('A6', 'sim_torre',     'pixel', 'A TORRE', [
   'Empilhando Cristos Redentores até a órbita',
   'Empilhando ônibus até passar das nuvens',
   'Empilhando notas de duzentos até um milhão de reais',
   'Empilhando pessoas até o topo do Everest',
   'Empilhando celulares até a Estação Espacial']),
 ('A7', 'sim_descida',   'pixel', 'A DESCIDA', [
   'Descendo até o centro da Terra',
   'Descendo um prédio de cem andares',
   'Descendo a mina mais funda do mundo',
   'Descendo o Rio Amazonas da nascente à foz',
   'Descendo da estratosfera até o chão']),
 ('A8', 'sim_estrada',   'pixel', 'ESTRADA INFINITA', [
   'A BR-116 inteira, de Fortaleza a Jaguarão',
   'A Transamazônica, do começo ao fim',
   'Dirigindo a noite inteira sem parar',
   'A estrada do amanhecer até o anoitecer']),
 ('B1', 'sim_revelar',   'pixel', 'ADIVINHA O DESENHO', [
   'Objetos que todo brasileiro teve em casa',
   'Bichos do Brasil, quadradinho por quadradinho',
   'Ferramentas que ninguém mais usa',
   'Comida brasileira em pixel',
   'Instrumentos musicais revelados aos poucos']),
 ('B2', 'sim_lousa',     'pixel', 'A LOUSA', [
   'Desenhos de uma linha só: casa, barco, chave',
   'Meios de transporte sem levantar o traço',
   'Animais numa linha contínua',
   'Objetos da cozinha na lousa',
   'Prédios e monumentos na lousa']),
 ('B4', 'sim_traco',     'alta',  'A NANQUIM', [
   'Desenhos a nanquim: o que a mão revela devagar',
   'Plantas e folhas, traço por traço',
   'Objetos antigos desenhados à pena',
   'Bichos a nanquim',
   'Arquitetura brasileira à mão livre']),
 ('C1', 'quizengine',    'quiz',  'QUIZ RELÂMPAGO', [
   'Português que todo mundo erra',
   'Anos 80, 90 e 2000',
   'Brasil de ponta a ponta',
   'Países e bandeiras',
   'Ciência do dia a dia',
   'Bicho e natureza',
   'Cinema, TV e música',
   'Lógica e pegadinha',
   'Comida e bebida',
   'Objetos que sumiram']),
 ('D1', 'sim_ambiente',  'pixel', 'MODO FOCO', [
   'Chuva na janela, uma hora',
   'Fogueira acesa, uma hora',
   'Mar batendo na praia, uma hora',
   'Vento no campo, uma hora']),
 ('D2', 'sim_corda',     'alta',  'A CORDA', [
   'Descendo até o Titanic',
   'Descendo até a Fossa das Marianas',
   'O elevador que não para de descer']),
]


def montar():
    usados, videos, seed = set(), [], 1001
    ip, ie = 0, 0
    for serie, sim, motor, rotulo, temas in SERIES:
        for t, tema in enumerate(temas):
            if motor == 'alta':
                looks, i = ESTILOS, ie
            else:
                looks, i = PALETAS, ip
            # primeiro par livre: gira a ordem para vídeos seguidos da mesma
            # série não caírem todos na mesma cara
            esc = None
            for d in range(len(looks)):
                c = looks[(i + d) % len(looks)]
                if (sim, c) not in usados:
                    usados.add((sim, c)); esc = c; break
            if esc is None:
                sys.exit(f'aparências esgotadas em {sim}')
            if motor == 'alta': ie += 1
            else: ip += 1
            videos.append(dict(
                id=f'V{len(videos)+1:03d}', serie=serie, rotulo=rotulo,
                simulador=sim, motor=motor, aparencia=esc, seed=seed,
                tema=tema, unidade=f'{serie.lower()}-v{len(videos)+1:03d}.json'))
            seed += 1

    # 200 Shorts: cada um sai de um vídeo e nunca repete a cara do pai
    shorts, seed = [], 5001
    for i in range(200):
        pai = videos[i % len(videos)]
        looks = ESTILOS if pai['motor'] == 'alta' else PALETAS
        esc = looks[(i * 3 + 1) % len(looks)]
        if esc == pai['aparencia']:
            esc = looks[(i * 3 + 2) % len(looks)]
        shorts.append(dict(id=f'S{i+1:03d}', pai=pai['id'], serie=pai['serie'],
                           simulador=pai['simulador'], motor=pai['motor'],
                           aparencia=esc, seed=seed, tema=pai['tema']))
        seed += 1

    # o plano confere a si mesmo contra os motores. Uma paleta que não existe
    # só aparecia na hora do render, no meio de um lote de horas — e o lote
    # morria no vídeo 23.
    try:
        import pixelengine as PX, altaengine as AL
        for v in videos + shorts:
            val = PX.PALETAS if v['motor'] == 'pixel' else (
                AL.ESTILOS if v['motor'] == 'alta' else {v['aparencia']: 1})
            assert v['aparencia'] in val, \
                f"{v['id']}: aparência {v['aparencia']!r} não existe em {v['motor']}"
    except ImportError:
        print('aviso: motores não importáveis, aparências não conferidas')

    pares = [(v['simulador'], v['aparencia']) for v in videos]
    assert len(pares) == len(set(pares)), 'REPETIU a cara de um vídeo longo'
    for s in shorts:
        pai = next(v for v in videos if v['id'] == s['pai'])
        assert s['aparencia'] != pai['aparencia'], f"{s['id']} igual ao pai"
    return {'videos': videos, 'shorts': shorts}


if __name__ == '__main__':
    p = montar()
    json.dump(p, open('plano-280.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f"{len(p['videos'])} longos + {len(p['shorts'])} Shorts = "
          f"{len(p['videos']) + len(p['shorts'])} peças")
    for s, n in sorted({v['serie']: sum(1 for x in p['videos'] if x['serie'] == v['serie'])
                        for v in p['videos']}.items()):
        print(f'  {s}: {n} longos')
