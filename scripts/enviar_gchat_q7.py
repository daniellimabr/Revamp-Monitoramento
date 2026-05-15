import os
import base64
import json
import requests
from datetime import datetime
from config import GITHUB_TOKEN, WEBHOOK_URL

# ── Configurações ──────────────────────────────────────────────────────────────
REPO    = "daniellimabr/Revamp-Monitoramento"
BRANCH  = "main"
PASTA   = "imagens"
TS_FILE = r"C:\Revamp Monitoramento\ultimo_timestamp_q7.txt"
IMG_DIR = r"C:\Revamp Monitoramento\imagens"

# Títulos legíveis para cada grupo no card do Chat
TITULOS_CHAT = {
    'act-fpd':    'Ativos — FPD',
    'act-new':    'Ativos — Novos',
    'act-stock':  'Ativos — Stock',
    'evictions':  'Evictions',
    'end-new':    'Encerrados — Novos',
    'end-31-90':  'Encerrados — 31 a 90 dias',
    'end-91-180': 'Encerrados — 91 a 180 dias',
    'end-181-360':'Encerrados — 181 a 360 dias',
    'end-360+':   'Encerrados — 360+ dias',
    'outros':     'Audiencias Residuais',
}

def upload_github(png_path, png_nome):
    with open(png_path,'rb') as f:
        conteudo_b64=base64.b64encode(f.read()).decode('utf-8')
    url_api=f"https://api.github.com/repos/{REPO}/contents/{PASTA}/{png_nome}"
    headers={"Authorization":f"token {GITHUB_TOKEN}","Accept":"application/vnd.github.v3+json"}
    resp=requests.get(url_api,headers=headers)
    sha=resp.json().get('sha') if resp.status_code==200 else None
    payload={"message":f"M7 {png_nome}","content":conteudo_b64,"branch":BRANCH}
    if sha: payload["sha"]=sha
    resp=requests.put(url_api,headers=headers,json=payload)
    resp.raise_for_status()
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{PASTA}/{png_nome}"

def enviar_card(raw_url, subtitulo, thread_name, data_hoje):
    card = {
        "cardsV2": [{
            "cardId": f"m7-{subtitulo}",
            "card": {
                "header": {
                    "title": f"M7 · Distribuição por Audiência — {subtitulo}",
                    "subtitle": f"Foto Atual — {data_hoje}"
                },
                "sections": [{
                    "widgets": [{
                        "image": {
                            "imageUrl": raw_url,
                            "altText": f"M7 {subtitulo}",
                            "onClick": {"openLink": {"url": raw_url}}
                        }
                    }]
                }]
            }
        }]
    }
    if thread_name:
        card["thread"] = {"name": thread_name}

    webhook = WEBHOOK_URL
    if thread_name:
        webhook += "&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"

    resp = requests.post(webhook, json=card)
    resp.raise_for_status()
    return resp.status_code

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with open(TS_FILE,'r') as f:
        meta = json.load(f)

    timestamp   = meta['timestamp']
    pngs        = meta['pngs']
    thread_name = os.environ.get("GCHAT_THREAD_NAME","")
    data_hoje   = datetime.now().strftime('%d/%m/%Y')

    print(f"Enviando {len(pngs)} PNGs do M7...")

    for sub, fname in pngs.items():
        png_path = os.path.join(IMG_DIR, fname)
        subtitulo = TITULOS_CHAT.get(sub, sub)

        print(f"  Uploading {fname}...")
        raw_url = upload_github(png_path, fname)

        print(f"  Enviando card: {subtitulo}...")
        status = enviar_card(raw_url, subtitulo, thread_name, data_hoje)
        print(f"  OK ({status})")

    print("\nM7 enviado com sucesso.")
