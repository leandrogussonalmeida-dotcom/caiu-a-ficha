#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep17 (série POR DENTRO): Como funciona a fechadura e a chave.

A ideia: cortar ao meio um cilindro de pinos comum (genérico, sem marca) e
mostrar, peça por peça, por que só a chave certa gira o rotor. Protagonista: a
chave entrando e cada pilha de pinos subindo até a altura certa, com o placar
PINOS NO LUGAR (k DE 5) e o rotor girando. Depois o came empurra a lingueta, o
trinco de mola, as combinações, a chave mestra, a tetra e a história.

A conta da fechadura é uma só (`ep17_desenho.Cilindro`): a ponta de cada pino
encosta na chave; os comprimentos dos pinos saem da chave certa; o rotor só
gira se TODO vão cai exatamente na linha de corte (conferido em números por
`ep17_desenho.checar()`). No capítulo `batida` (house a 120 BPM) a chave lisa
ganha um dente por compasso e o pino desse dente cai no lugar na 4ª batida.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Cilindro de pinos: um corpo com um furo onde fica o rotor (plug); furos,
      normalmente 5 ou 6, com pinos de chave de tamanhos diferentes, de ponta
      arredondada, e por cima contrapinos com mola; o encontro do rotor com o
      corpo é a linha de corte; sem chave os pinos ficam atravessados na linha
      e o rotor não gira; com a chave certa os vãos caem na linha e ele gira;
      chave errada: os pinos não alinham; na ponta do rotor um came ou alavanca
      move o mecanismo que puxa a lingueta; chave mestra: uma terceira peça
      (espaçador) cria dois pontos de corte, um para cada chave. Wikipedia,
      "Pin tumbler lock".
  F2  Britannica, "lock": fechadura egípcia de madeira, pinos que caem em furos
      do ferrolho, chave erguida que levanta os pinos; o exemplo mais antigo,
      achado em Khorsabad perto de Nínive, talvez 2.700 a 4.000 anos; Linus Yale
      patenteou em 1848 uma fechadura de pinos baseada no princípio egípcio;
      nos anos 1860 o filho, Linus Yale Jr., criou o cilindro com a chave
      pequena e chata de borda serrilhada; os dentes erguem os pinos à altura
      certa; o número de pinos costuma ser cinco; a chave torta e o buraco
      torto somam um efeito de segredo (guarda).
  F3  Wikipedia, "Lock and key": 1848, Linus Yale Sr., a versão moderna do
      pino; 1861, Linus Yale Jr. patenteia a chave chata e serrilhada menor; a
      chave mestra abre um conjunto de fechaduras.
  F4  LockWiki, "Differs": combinações teóricas = alturas elevado a pinos;
      5 pinos com 10 alturas = 100.000; tolerâncias e regras de corte (como a
      diferença máxima entre cortes vizinhos) reduzem muito o número real.
  F5  Wikipedia, "Latch": trinco = lingueta com mola e borda inclinada; ao
      fechar, a borda inclinada bate na contratesta e o trinco recolhe; depois
      sai sozinho para dentro da contratesta; a maçaneta recolhe o trinco.
  F6  Wikipedia, "Dead bolt": a lingueta (tranca) só abre com a chave ou um
      puxador, diferente do trinco de mola, que recua se empurrado; ela é
      lançada para dentro do batente.
  F7  Olhar Digital (30/08/2026): "tetra" não é fechadura de 4 pinos; é a
      chave cruzada, com o segredo distribuído em 4 faces, o que aumenta a
      complexidade; lingueta, cilindro, porta e batente entram na conta da
      segurança.
  F8  Contas a partir de F4: 10 x 10 x 10 x 10 x 10 = 100.000;
      10 elevado a 6 = 1.000.000.
"""

TITULO = "Como funciona a fechadura e a chave | O cilindro de pinos por dentro, em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),           # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),           # 6 s
    dict(id='porta', gen='lofi', bars=8, papel='drop'),             # 24 s
    dict(id='pecas', gen='synthwave', bars=25, papel='drop'),       # 60 s (6 peças x 10 s)
    dict(id='semchave', gen='lofi', bars=8, papel='drop'),          # 24 s
    dict(id='errada', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='certa', gen='lofi', bars=12, papel='break'),           # 36 s (câmera lenta)
    dict(id='batida', gen='house', bars=16, papel='drop', bpm=120),  # 32 s (1 pino por compasso)
    dict(id='giro', gen='lofi', bars=8, papel='drop'),              # 24 s
    dict(id='lingueta', gen='lofi', bars=12, papel='drop'),         # 36 s
    dict(id='trinco', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='chave', gen='lofi', bars=8, papel='drop'),             # 24 s
    dict(id='combinacoes', gen='synthwave', bars=15, papel='drop'),  # 36 s
    dict(id='mestra', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='tetra', gen='lofi', bars=8, papel='drop'),             # 24 s
    dict(id='historia', gen='lofi', bars=10, papel='break'),        # 30 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),              # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "UMA CHAVE ENTRA E A PORTA ABRE.", "O QUE ACONTECE LÁ DENTRO?", ()),
        (6.0, 11.6, "CINCO PINOS PRECISAM PARAR NA", "*ALTURA EXATA*, TODOS JUNTOS.", ('F1', 'F2')),
    ],
    'porta': [
        (0.8, 7.8, "UMA FECHADURA COMUM DE PORTA.", "TUDO COMEÇA NO *CILINDRO*.", ()),
        (8.0, 15.8, "A CHAVE GIRA O MIOLO DO CILINDRO,", "E ELE MOVE A *LINGUETA*.", ('F1',)),
        (16.0, 23.6, "VAMOS CORTAR O CILINDRO AO MEIO", "E OLHAR POR DENTRO.", ()),
    ],
    'pecas': [
        (0.3, 9.6, "O *CORPO*: A PARTE QUE FICA PRESA", "NA PORTA E NÃO GIRA.", ('F1',)),
        (10.3, 19.6, "DENTRO DELE, O *ROTOR*: O MIOLO", "QUE GIRA COM A CHAVE.", ('F1',)),
        (20.3, 29.6, "EM CADA FURO, UM *PINO* DE TAMANHO", "DIFERENTE, DE PONTA ARREDONDADA.", ('F1',)),
        (30.3, 39.6, "EM CIMA DE CADA PINO, UM", "*CONTRAPINO*, NO MESMO FURO.", ('F1',)),
        (40.3, 49.6, "E UMA *MOLA* QUE EMPURRA TUDO", "PARA BAIXO.", ('F1',)),
        (50.3, 59.6, "ONDE O ROTOR ENCONTRA O CORPO:", "A *LINHA DE CORTE*.", ('F1',)),
    ],
    'semchave': [
        (0.5, 7.6, "SEM CHAVE, AS MOLAS EMPURRAM", "OS PINOS PARA BAIXO.", ('F1',)),
        (7.8, 15.6, "CADA CONTRAPINO FICA *ATRAVESSADO*", "NA LINHA: PARTE EM CADA LADO.", ('F1',)),
        (15.8, 23.6, "É COMO UMA TRAVA EM CADA FURO:", "O ROTOR *NÃO CONSEGUE GIRAR*.", ('F1',)),
    ],
    'errada': [
        (0.5, 7.6, "AGORA, UMA *CHAVE ERRADA*.", "ELA ENTRA E EMPURRA OS PINOS.", ()),
        (7.8, 15.6, "UM CORTE RASO DEMAIS: O PINO SOBE", "*ALTO DEMAIS* E PASSA DA LINHA.", ('F1',)),
        (15.8, 22.6, "UM CORTE FUNDO DEMAIS: O CONTRAPINO", "FICA *BAIXO DEMAIS*.", ('F1',)),
        (22.8, 29.6, "3 DE 5 NO LUGAR NÃO BASTA.", "O ROTOR *CONTINUA TRAVADO*.", ('F1',)),
    ],
    'certa': [
        (0.5, 8.6, "AGORA A *CHAVE CERTA*, BEM DEVAGAR.", "OS PINOS SOBEM E DESCEM NOS DENTES.", ()),
        (8.8, 17.6, "CADA DENTE TEM UMA ALTURA. É O", "*SEGREDO* GRAVADO NA CHAVE.", ('F2',)),
        (17.8, 26.6, "NO FIM, CADA VÃO ENTRE PINO E", "CONTRAPINO CAI *NA LINHA DE CORTE*.", ('F1',)),
        (26.8, 35.6, "A LINHA FICA LIVRE E O ROTOR", "*GIRA*. A PORTA PODE ABRIR.", ('F1',)),
    ],
    'batida': [
        (0.5, 7.6, "NO RITMO: A CADA COMPASSO, UMA", "CHAVE LISA GANHA *UM DENTE*.", ()),
        (7.8, 13.6, "CADA DENTE CERTO PÕE MAIS UM PINO", "NO LUGAR. *5 DE 5: GIRA!*", ('F1',)),
        (14.0, 22.6, "NA VELOCIDADE DE VERDADE: A CERTA", "GIRA, A ERRADA *TRAVA*.", ('F1',)),
        (22.8, 31.6, "E É ASSIM TODA VEZ QUE VOCÊ", "*GIRA A CHAVE* NA PORTA.", ()),
    ],
    'giro': [
        (0.5, 7.6, "VISTO DE FRENTE: O ROTOR É REDONDO", "E A PILHA DE PINOS FICA EM CIMA.", ('F1',)),
        (7.8, 15.6, "COM O VÃO NA LINHA, O PINO GIRA", "JUNTO E O *CONTRAPINO FICA*.", ('F1',)),
        (15.8, 23.6, "ATRÁS DO ROTOR FICA O *CAME*,", "UM DENTE QUE GIRA JUNTO.", ('F1',)),
    ],
    'lingueta': [
        (0.5, 8.6, "A FECHADURA ABERTA: O CILINDRO", "FICA NO MEIO DA *CAIXA*.", ()),
        (8.8, 17.6, "AO GIRAR, O *CAME* ENGANCHA NUM", "DENTE DA LINGUETA E EMPURRA.", ('F1',)),
        (17.8, 26.6, "UMA VOLTA DA CHAVE: A *LINGUETA*", "SAI E ENTRA NO BATENTE.", ('F6',)),
        (26.8, 35.6, "NÃO RECUA SE EMPURRADA: SÓ VOLTA", "*COM A CHAVE* OU UM BOTÃO DE GIRAR.", ('F6',)),
    ],
    'trinco': [
        (0.5, 7.6, "O *TRINCO* É DIFERENTE: TEM MOLA", "E A PONTA INCLINADA.", ('F5',)),
        (7.8, 15.6, "AO FECHAR, A RAMPA BATE NA CHAPA", "DO BATENTE E O TRINCO *ENTRA*.", ('F5',)),
        (15.8, 22.6, "PASSOU, A MOLA O EMPURRA PARA", "O BURACO: *CLIC*. PORTA FECHADA.", ('F5',)),
        (22.8, 29.6, "PARA ABRIR, A *MAÇANETA* PUXA", "O TRINCO PARA DENTRO.", ('F5',)),
    ],
    'chave': [
        (0.5, 7.6, "A CHAVE: A *CABEÇA*, A HASTE E OS", "*DENTES*, QUE ERGUEM OS PINOS.", ('F2',)),
        (7.8, 15.6, "OS SULCOS DO LADO TÊM QUE CASAR", "COM O *FORMATO* DO BURACO.", ('F2',)),
        (15.8, 23.6, "CHAVE DE OUTRO FORMATO", "*NEM ENTRA* NO ROTOR.", ('F2',)),
    ],
    'combinacoes': [
        (0.5, 8.6, "QUANTOS SEGREDOS DIFERENTES?", "DEPENDE DOS PINOS E DAS ALTURAS.", ('F4',)),
        (8.8, 17.6, "COM *5 PINOS* E *10 ALTURAS*:", "10 X 10 X 10 X 10 X 10.", ('F4', 'F8')),
        (17.8, 26.6, "DÁ *100.000* COMBINAÇÕES.", "COM 6 PINOS, *1 MILHÃO*.", ('F4', 'F8')),
        (26.8, 35.6, "NA PRÁTICA SÃO MENOS: HÁ REGRAS", "PARA DENTES VIZINHOS.", ('F4',)),
    ],
    'mestra': [
        (0.5, 7.6, "MUITOS PRÉDIOS USAM *CHAVE MESTRA*:", "UMA SÓ CHAVE ABRE VÁRIAS PORTAS.", ('F3',)),
        (7.8, 15.6, "O TRUQUE: UMA PEÇA *EXTRA*, FININHA,", "ENTRE O PINO E O CONTRAPINO.", ('F1',)),
        (15.8, 22.6, "ELA CRIA *2 VÃOS*: UM PARA A SUA", "CHAVE, OUTRO PARA A MESTRA.", ('F1',)),
        (22.8, 29.6, "AS DUAS GIRAM O MESMO ROTOR,", "CADA UMA COM O SEU VÃO NA LINHA.", ('F1',)),
    ],
    'tetra': [
        (0.5, 7.6, "E A CHAVE *TETRA*? ELA É CRUZADA:", "O SEGREDO FICA EM *4 FACES*.", ('F7',)),
        (7.8, 15.6, "MAIS FACES, MAIS DENTES PARA CASAR:", "UM SEGREDO *MAIS COMPLEXO*.", ('F7', 'F9')),
        (15.8, 23.6, "MAS A SEGURANÇA DEPENDE DE TUDO:", "PORTA, BATENTE E LINGUETA.", ('F7',)),
    ],
    'historia': [
        (0.5, 7.6, "A IDEIA É ANTIGA. NO EGITO, PINOS", "DE *MADEIRA* PRENDIAM O FERROLHO.", ('F2',)),
        (7.8, 15.6, "A CHAVE ERGUIA OS PINOS. A IDEIA", "TEM *MILHARES DE ANOS*.", ('F2',)),
        (15.8, 22.6, "EM *1848*, LINUS YALE PATENTEOU", "UMA FECHADURA DE PINOS.", ('F2', 'F3')),
        (22.8, 29.6, "NOS ANOS *1860*, O FILHO CRIOU O", "CILINDRO DE CHAVE CHATA.", ('F2', 'F3')),
    ],
    'resumo': [
        (0.5, 9.6, "A *CHAVE* ERGUE CADA PINO", "ATÉ A ALTURA CERTA.", ('F1', 'F2')),
        (9.8, 19.6, "TODOS OS VÃOS NA *LINHA DE CORTE*:", "O ROTOR GIRA.", ('F1',)),
        (19.8, 29.6, "O *CAME* MOVE A LINGUETA", "E A PORTA ABRE.", ('F1',)),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Pin tumbler lock"', 'https://en.wikipedia.org/wiki/Pin_tumbler_lock'),
    'F2': ('Encyclopaedia Britannica, "lock"', 'https://www.britannica.com/technology/lock-security/Introduction'),
    'F3': ('Wikipedia, "Lock and key"', 'https://en.wikipedia.org/wiki/Lock_and_key'),
    'F4': ('LockWiki, "Differs"', 'https://lockwiki.com/index.php/Differs'),
    'F5': ('Wikipedia, "Latch"', 'https://en.wikipedia.org/wiki/Latch'),
    'F6': ('Wikipedia, "Dead bolt"', 'https://en.wikipedia.org/wiki/Dead_bolt'),
    'F7': ('Olhar Digital, "Fechadura tetra pode reforçar a segurança da porta, mas há um detalhe mais importante que o formato da chave"',
           'https://olhardigital.com.br/curiosidades/?p=18008'),
    'F9': ('Guia Fácil, chave tetra: quatro fileiras de dentes ou segredos, com pinos em diferentes posições', 'https://guiafacil.com/blog/?p=4869'),
    'F8': ('Conta a partir de F4: 10 x 10 x 10 x 10 x 10 = 100.000; 10 elevado a 6 = 1.000.000', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'porta': 'A fechadura da porta', 'pecas': 'As peças do cilindro',
                'semchave': 'Sem chave: travado', 'errada': 'A chave errada', 'certa': 'A chave certa, devagar',
                'batida': 'Pino por pino, no ritmo', 'giro': 'O rotor visto de frente',
                'lingueta': 'O came e a lingueta', 'trinco': 'O trinco de mola', 'chave': 'As partes da chave',
                'combinacoes': 'Quantas combinações?', 'mestra': 'A chave mestra', 'tetra': 'E a chave tetra?',
                'historia': 'Do Egito a 1860', 'resumo': 'Resumo'}

DESCRICAO = """Por que só a sua chave abre a sua porta? A gente corta ao meio um cilindro de fechadura comum (genérico, sem marca) e mostra peça por peça: o corpo, o rotor, os pinos, os contrapinos, as molas e a linha de corte. Primeiro sem chave, depois com uma chave errada e por fim com a certa, em câmera lenta, com um placar que conta os pinos no lugar.

Num trecho, uma chave lisa ganha um dente por compasso e cada pino cai no lugar no ritmo da música. Também: o came que move a lingueta, o trinco de mola, quantas combinações existem, a chave mestra, a chave tetra e a fechadura de madeira do Egito antigo.

Este é um vídeo sobre como a fechadura funciona. Cada quadro é pixel art desenhada por código, e a música é original.

Capítulos
{capitulos}

Simplificado de propósito
- O cilindro é genérico e desenhado em corte, com 5 pinos (o número mais comum). As medidas são inventadas; num cilindro de verdade os pinos são bem menores.
- Os pinos se encaixam no nosso desenho com precisão de 1 pixel. Num cilindro de verdade existe uma folga pequena, de fábrica.
- Usamos 10 alturas de corte, que é um exemplo de fonte (LockWiki); cada fabricante usa o seu número de alturas e de pinos. Os 100.000 são combinações teóricas.
- Quando o rotor gira na vista de lado, mostramos o pino e a chave "achatando" em direção ao eixo: é como um objeto que gira fica visto de lado.
- No capítulo no ritmo, a chave lisa ganha os dentes enquanto entra e sai da fechadura; na vida real a chave é cortada numa máquina, fora dela.
- A caixa da fechadura (cilindro, came, lingueta, trinco, maçaneta) é um esquema genérico. Em muitas fechaduras a lingueta precisa de mais de uma volta da chave; aqui ela sai com uma volta.
- No trinco, a porta está desenhada vista de cima e chegando em linha reta ao batente (na vida real ela gira na dobradiça).
- A chave tetra está desenhada de frente, com uma fila de pinos em cada face, como esquema.

Fontes
{fontes}

#fechadura #chave #comofunciona #pixelart #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. Nos cortes, o
# cilindro é desenhado compacto (passo 26 px) de x 62 a 240 (no `batida`, 78..256,
# para o esmeril caber); a caixa da fechadura com o batente ocupa 76..264 e o
# trinco visto de cima 60..240.
PREFIXO = 'ep17-fechadura'
CORTES = [
    dict(id='c1', de=('certa', 0.0), ate=('certa', 36.0), x=60, gancho=['A CHAVE', 'POR DENTRO'],
         titulo='O que a chave faz dentro da fechadura 🔑',
         descricao='A chave certa em câmera lenta: cada pino sobe até o vão dele cair exatamente na linha de corte. Só aí o rotor gira.'),
    dict(id='c2', de=('batida', 0.0), ate=('batida', 32.0), x=60, gancho=['PINO POR', 'PINO'],
         titulo='Uma chave ganhando dente por dente, no ritmo 🎵',
         descricao='Cada dente certo põe mais um pino no lugar. Com 5 de 5, o rotor gira. Depois, a chave certa e a errada na velocidade de verdade.'),
    dict(id='c3', de=('errada', 0.0), ate=('errada', 30.0), x=60, gancho=['CHAVE', 'ERRADA'],
         titulo='Por que a chave errada não gira?',
         descricao='Um corte raso demais empurra o pino acima da linha de corte; um fundo demais deixa o contrapino atravessado. 3 de 5 no lugar não basta.'),
    dict(id='c4', de=('lingueta', 0.0), ate=('lingueta', 36.0), x=84, gancho=['O QUE A', 'CHAVE GIRA?'],
         titulo='Como a chave move a lingueta da porta',
         descricao='Atrás do rotor fica o came. Numa volta da chave ele engancha no dente da lingueta e empurra ela para dentro do batente.'),
    dict(id='c5', de=('trinco', 0.0), ate=('trinco', 30.0), x=60, gancho=['O CLIC DA', 'PORTA'],
         titulo='O clic da porta: como o trinco funciona',
         descricao='O trinco tem mola e a ponta inclinada: ao fechar, a rampa bate na chapa do batente, ele entra e depois salta para o buraco. Para abrir, a maçaneta puxa.'),
    dict(id='c6', de=('mestra', 0.0), ate=('mestra', 30.0), x=60, gancho=['CHAVE', 'MESTRA'],
         titulo='Como uma chave mestra abre várias portas',
         descricao='Uma peça extra, fininha, entre o pino e o contrapino cria dois vãos: um para a sua chave e outro para a mestra.'),
]
