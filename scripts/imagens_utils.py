"""
imagens_utils.py — Utilitários de gestão de imagens do Revamp Monitoramento.

Responsabilidades:
  - Garantir que a pasta imagens/ e imagens/expurgo/ existam
  - Mover PNGs anteriores de um monitoramento para expurgo antes de gerar novos
"""

import os
import shutil
import glob

IMG_DIR     = r"C:\Revamp Monitoramento\imagens"
EXPURGO_DIR = r"C:\Revamp Monitoramento\imagens\expurgo"


def garantir_pastas():
    """Cria imagens/ e imagens/expurgo/ se não existirem."""
    os.makedirs(IMG_DIR,     exist_ok=True)
    os.makedirs(EXPURGO_DIR, exist_ok=True)


def expurgar(prefixo: str):
    """
    Move para expurgo todos os PNGs em imagens/ cujo nome começa com `prefixo`.

    Exemplo:
        expurgar("grafico_q6_")   # move grafico_q6_*.png
        expurgar("grafico_q7_")   # move grafico_q7_*.png
    """
    garantir_pastas()
    padrao = os.path.join(IMG_DIR, f"{prefixo}*.png")
    arquivos = glob.glob(padrao)
    movidos = 0
    for arq in arquivos:
        destino = os.path.join(EXPURGO_DIR, os.path.basename(arq))
        # Se já existe no expurgo (reexecução no mesmo dia), sobrescreve
        if os.path.exists(destino):
            os.remove(destino)
        shutil.move(arq, destino)
        movidos += 1
    if movidos:
        print(f"  [expurgo] {movidos} arquivo(s) movido(s) -> imagens/expurgo/")
    return movidos
