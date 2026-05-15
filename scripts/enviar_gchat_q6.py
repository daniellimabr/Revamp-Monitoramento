import os
import base64
import requests
from datetime import datetime
from config import GITHUB_TOKEN, WEBHOOK_URL

# ── Configurações ──────────────────────────────────────────────────────────────
REPO        = "daniellimabr/Revamp-Monitoramento"
BRANCH      = "main"
PASTA       = "imagens"
TS_FILE     = r"C:\Revamp Monitoramento\ultimo_timestamp_q6.txt"
IMG_DIR     = r"C:\Revamp Monitoramento\imagens"

# ── Leitura do timestamp e localização do PNG ──────────────────────────────────
with open(TS_FILE, 'r') as f:
    timestamp = f.read().strip()

png_nome  = f"grafico_q6_{timestamp}.png"
png_path  = os.path.join(IMG_DIR, png_nome)

# ── Upload para o GitHub ───────────────────────────────────────────────────────
with open(png_path, 'rb') as f:
    conteudo_b64 = base64.b64encode(f.read()).decode('utf-8')

url_api = f"https://api.github.com/repos/{REPO}/contents/{PASTA}/{png_nome}"
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Verificar se arquivo já existe (para obter SHA em caso de update)
resp_check = requests.get(url_api, headers=headers)
sha = resp_check.json().get('sha') if resp_check.status_code == 200 else None

payload = {
    "message": f"M6 grafico {timestamp}",
    "content": conteudo_b64,
    "branch": BRANCH,
}
if sha:
    payload["sha"] = sha

resp_upload = requests.put(url_api, headers=headers, json=payload)
resp_upload.raise_for_status()
print(f"Upload GitHub: {resp_upload.status_code}")

# ── Montar URL raw (com timestamp para evitar cache) ──────────────────────────
raw_url = (
    f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
    f"/{PASTA}/{png_nome}?ts={timestamp}"
)

# ── Envio para o Google Chat ───────────────────────────────────────────────────
thread_name = os.environ.get("GCHAT_THREAD_NAME", "")
data_hoje   = datetime.now().strftime('%d/%m/%Y')

card = {
    "cardsV2": [{
        "cardId": "m6-card",
        "card": {
            "header": {
                "title": "M6 · Distribuição para Assessorias",
                "subtitle": f"Foto Atual — {data_hoje}"
            },
            "sections": [{
                "widgets": [{
                    "image": {
                        "imageUrl": raw_url,
                        "altText": "M6 Distribuição para Assessorias",
                        "onClick": {
                            "openLink": {
                                "url": raw_url
                            }
                        }
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

resp_chat = requests.post(webhook, json=card)
resp_chat.raise_for_status()
print(f"Google Chat: {resp_chat.status_code}")
print("M6 enviado com sucesso.")
