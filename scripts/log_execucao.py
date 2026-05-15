"""
log_execucao.py — Módulo central de log diário do Revamp Monitoramento.

Uso em cada script:
    from log_execucao import registrar

    registrar(
        monitoramento = "M1",
        timestamp     = TIMESTAMP,
        status        = "ok",          # "ok" ou "erro"
        qtd_contratos = len(df),
        vl_total      = float(df['VL_PRINCIPAL_VENCIDO'].sum()),
        pngs          = {"png": "grafico_q1_....png"},   # dict com os PNGs gerados
        erro          = None,          # string com traceback se status="erro"
    )
"""

import json
import os
from datetime import datetime

LOG_DIR = r"C:\Revamp Monitoramento\logs"

def _caminho_log():
    data_hoje = datetime.now().strftime('%Y%m%d')
    return os.path.join(LOG_DIR, f"monitoramento_{data_hoje}.json")

def _carregar():
    path = _caminho_log()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "data": datetime.now().strftime('%Y-%m-%d'),
        "execucoes": {}
    }

def _salvar(dados):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(_caminho_log(), 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def registrar(monitoramento, timestamp, status, qtd_contratos=None,
              vl_total=None, pngs=None, erro=None):
    """
    Registra uma execução no JSON de log do dia.

    Se o monitoramento já tiver execuções anteriores no mesmo dia,
    acumula numa lista (histórico de reexecuções).

    Parâmetros:
        monitoramento  str   Ex: "M1", "M6", "M7"
        timestamp      str   Ex: "20260515_143022"
        status         str   "ok" ou "erro"
        qtd_contratos  int   Número de linhas no CSV (contratos únicos)
        vl_total       float Soma do saldo em atraso
        pngs           dict  {"chave": "nome_arquivo.png", ...}
        erro           str   Mensagem de erro (traceback) ou None
    """
    dados = _carregar()

    entrada = {
        "timestamp":      timestamp,
        "hora":           datetime.now().strftime('%H:%M:%S'),
        "status":         status,
        "qtd_contratos":  qtd_contratos,
        "vl_total":       round(vl_total, 2) if vl_total is not None else None,
        "pngs":           pngs or {},
        "erro":           erro,
    }

    # Acumular execuções do mesmo monitoramento no mesmo dia
    if monitoramento not in dados["execucoes"]:
        dados["execucoes"][monitoramento] = []

    dados["execucoes"][monitoramento].append(entrada)

    _salvar(dados)
    print(f"[LOG] {monitoramento} registrado — status: {status} — {datetime.now().strftime('%H:%M:%S')}")
