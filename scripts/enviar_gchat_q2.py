import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import GITHUB_TOKEN, GITHUB_USER, GITHUB_REPO, GITHUB_BRANCH, GITHUB_PASTA, WEBHOOK_URL

import requests
import base64
import json
from datetime import datetime

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
TIMESTAMP_FILE = os.path.join(BASE_DIR, "ultimo_timestamp_q2.txt")
IMG_DIR        = os.path.join(BASE_DIR, "imagens")

TITULOS_GRUPO = {
    'grupo_a': 'Grupo A — ATFX / ATEQ / ATPJ / AONB / XONB / OV15',
    'grupo_b': 'Grupo B — EVIC',
    'grupo_c': 'Grupo C — FINA',
    'grupo_d': 'Grupo D — Outros Segmentos',
}

def upload_github(png_path, nome_arquivo):
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_PASTA}/{nome_arquivo}"
    with open(png_path, "rb") as f:
        conteudo_b64 = base64.b64encode(f.read()).decode("utf-8")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    resp_check = requests.get(api_url, headers=headers)
    sha = resp_check.json().get('sha') if resp_check.status_code == 200 else None
    payload = {"message": f"M2 {nome_arquivo}", "content": conteudo_b64, "branch": GITHUB_BRANCH}
    if sha:
        payload["sha"] = sha
    resp = requests.put(api_url, headers=headers, json=payload)
    resp.raise_for_status()
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_PASTA}/{nome_arquivo}"
    print(f"  Upload OK: {nome_arquivo}")
    return raw_url

def enviar_gchat(image_url, titulo, subtitulo, thread_name=None):
    url = WEBHOOK_URL
    if thread_name:
        url += "&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
    card = {
        "cards": [{
            "header": {"title": titulo, "subtitle": subtitulo},
            "sections": [{"widgets": [{"image": {
                "imageUrl": image_url,
                "onClick": {"openLink": {"url": image_url}}
            }}]}]
        }]
    }
    if thread_name:
        card["thread"] = {"name": thread_name}
    resp = requests.post(url, json=card)
    resp.raise_for_status()
    print(f"  Chat OK: {titulo}")

if __name__ == "__main__":
    hoje        = datetime.now().strftime("%d/%m/%Y %H:%M")
    thread_name = os.environ.get("GCHAT_THREAD_NAME")

    if not os.path.exists(TIMESTAMP_FILE):
        raise FileNotFoundError(f"Timestamp não encontrado: {TIMESTAMP_FILE}\nExecute primeiro: python gerar_grafico_q2.py")

    with open(TIMESTAMP_FILE) as f:
        meta = json.load(f)

    timestamp = meta['timestamp']
    pngs      = meta['pngs']

    print(f"Enviando {len(pngs)} PNGs do M2...")

    for grp_key, fname in pngs.items():
        png_path = os.path.join(IMG_DIR, fname)
        if not os.path.exists(png_path):
            print(f"  AVISO: PNG não encontrado, pulando: {fname}")
            continue

        subtitulo_grp = TITULOS_GRUPO.get(grp_key, grp_key)
        print(f"\n  {subtitulo_grp}")

        raw_url = upload_github(png_path, fname)
        enviar_gchat(
            image_url   = raw_url,
            titulo      = f"M2 — Entradas por Segmento  |  {subtitulo_grp}",
            subtitulo   = f"Foto atual · {hoje}",
            thread_name = thread_name,
        )

    print("\nM2 enviado com sucesso.")
