#!/usr/bin/env python3
"""Idioma do canal. PT-BR primeiro (decisão de 29/10/2026); o inglês fica
guardado ao lado de cada texto para a versão global.

    LINGUA=en python3 ...      # renderiza em inglês
"""
import os

LINGUA = os.environ.get('LINGUA', 'pt').lower()


def T(pt, en):
    """Texto no idioma do canal."""
    return pt if LINGUA == 'pt' else en


def milhar(n):
    s = f"{int(round(n)):,}"
    return s.replace(',', '.') if LINGUA == 'pt' else s


def decimal(x, casas=1):
    s = f"{x:.{casas}f}"
    return s.replace('.', ',') if LINGUA == 'pt' else s
