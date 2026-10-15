#!/usr/bin/env python3
"""Paletas próprias das cenas NO RITMO (mesma convenção de índices do
pixelengine: 0 fundo, 11 branco, 9 destaque...). Registradas aqui, num lugar
só, porque uma cena pode usar a paleta de outra — e a paleta só existia se a
outra cena tivesse sido importada antes."""
import pixelengine as PX


def nova_paleta(nome, cores):
    assert len(cores) == 16, nome
    PX.PALETAS[nome] = cores


nova_paleta('rota', ['#0e0b16', '#2d6a3e', '#58a84a', '#8fd16a', '#d9b27c', '#a8794d',
                     '#3a7fd5', '#86c5f2', '#f5c9a0', '#ffd23f', '#ff8a3d', '#ffffff',
                     '#41e0d0', '#c2433d', '#8a8fa3', '#ff3d6e'])
nova_paleta('rota_noite', ['#070512', '#1b2a4a', '#25365e', '#3a4f86', '#5d5a8a', '#3d3a66',
                           '#1d2d6b', '#4b6fd1', '#e0b090', '#ffe066', '#ff5ea8', '#ffffff',
                           '#3df5ff', '#a83279', '#6b6f8a', '#ff2d55'])
nova_paleta('rota_outono', ['#140b08', '#6b3a1f', '#b0602a', '#e09a45', '#e8cf9a', '#9c6b43',
                            '#2f6f8f', '#7fc0d8', '#f5c9a0', '#ffd23f', '#ff6a3d', '#ffffff',
                            '#5ad1b0', '#8a2b2b', '#8f8a80', '#e8364f'])
nova_paleta('por_do_sol', ['#120422', '#2a0845', '#4b0f5c', '#6e1a6b', '#8c2a74', '#3b2b5f',
                           '#ff6c8f', '#ffa45c', '#ffd56b', '#ffe94d', '#ff3fa4', '#ffffff',
                           '#29e7ff', '#1a0f2e', '#45305e', '#ff2b4a'])
nova_paleta('deserto', ['#1a0f0a', '#5b3a29', '#8a5a3c', '#c2824a', '#e0a96a', '#3d6e9e',
                        '#7fb2e5', '#b8dcf5', '#f2d9a0', '#ffd23f', '#ff7a2f', '#ffffff',
                        '#2de0c8', '#2b1c14', '#6d6a66', '#e8364f'])
nova_paleta('noite_cidade', ['#04040c', '#0b0b1f', '#141433', '#1e1e4a', '#2a2a5e', '#3a3a75',
                             '#5a5ab0', '#8b8bff', '#c2c2ff', '#ffe066', '#ff4fd8', '#ffffff',
                             '#3df5ff', '#08081a', '#2b2b44', '#ff2d55'])
