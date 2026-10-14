#!/usr/bin/env python3
"""Onde estao as fontes. Um lugar so, que funciona no Linux e no Windows.

Os motores nasceram com o caminho do Linux escrito direto no codigo
('/usr/share/fonts/...'). Funcionou enquanto eu era o unico a renderizar.
Na maquina do Leandro todo render morria com 'OSError: cannot open
resource', e 178 Shorts seguidos falharam pelo mesmo motivo.

A correcao: as fontes vao JUNTO com o motor, em `fontes/`. Nada de depender
do que o sistema tem instalado - o canal inteiro usaria outra tipografia na
maquina de outra pessoa, e isso e tao grave quanto nao renderizar.

Todas sao de licenca aberta (OFL ou equivalente), entao embutir e permitido.
"""
import os

AQUI = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fontes')

_LINUX = '/usr/share/fonts/'
# nome do arquivo -> onde o sistema PODE ter, se o pacote nao vier junto
SISTEMA = {
    'Inter-Bold.otf': _LINUX + 'opentype/inter/Inter-Bold.otf',
    'Inter-Medium.otf': _LINUX + 'opentype/inter/Inter-Medium.otf',
    'Inter-SemiBold.otf': _LINUX + 'opentype/inter/Inter-SemiBold.otf',
    'InterDisplay-Black.otf': _LINUX + 'opentype/inter/InterDisplay-Black.otf',
    'DejaVuSansMono-Bold.ttf': _LINUX + 'truetype/dejavu/DejaVuSansMono-Bold.ttf',
    'DejaVuSerif-Bold.ttf': _LINUX + 'truetype/dejavu/DejaVuSerif-Bold.ttf',
    'Lora-Variable.ttf': _LINUX + 'truetype/google-fonts/Lora-Variable.ttf',
    'Poppins-Bold.ttf': _LINUX + 'truetype/google-fonts/Poppins-Bold.ttf',
}


def f(nome):
    """Caminho da fonte: junto do motor primeiro, o sistema so como ultimo
    recurso. Nessa ordem para o resultado ser o MESMO em qualquer maquina."""
    junto = os.path.join(AQUI, nome)
    if os.path.exists(junto): return junto
    alt = SISTEMA.get(nome)
    if alt and os.path.exists(alt): return alt
    raise FileNotFoundError(
        f'fonte {nome} nao encontrada. Ela deveria estar em {AQUI}. '
        f'Se a pasta fontes nao veio junto, baixe o motor de novo.')


def conferir():
    """Chamado antes de gastar horas de maquina. Falhar no comeco e barato;
    falhar no video 178 nao e."""
    return [n for n in SISTEMA
            if not os.path.exists(os.path.join(AQUI, n))
            and not os.path.exists(SISTEMA[n])]


if __name__ == '__main__':
    faltam = conferir()
    print('todas as fontes no lugar' if not faltam
          else 'FALTAM: ' + ', '.join(faltam))
