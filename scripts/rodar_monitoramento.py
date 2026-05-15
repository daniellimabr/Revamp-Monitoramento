import subprocess
import requests
import os
from datetime import datetime
from config import WEBHOOK_URL
from log_execucao import registrar

# ── Sequência de monitoramentos ────────────────────────────────────────────────
MONITORAMENTOS = [
    ("M1",  "gerar_grafico_q1.py",  "enviar_gchat_q1.py"),
    ("M2",  "gerar_grafico_q2.py",  "enviar_gchat_q2.py"),
    ("M3",  "gerar_grafico_q3.py",  "enviar_gchat_q3.py"),
    ("M4",  "gerar_grafico_q4.py",  "enviar_gchat_q4.py"),
    ("M5",  "gerar_grafico_q5.py",  "enviar_gchat_q5.py"),
    ("M6",  "gerar_grafico_q6.py",  "enviar_gchat_q6.py"),
    ("M7",  "gerar_grafico_q7.py",  "enviar_gchat_q7.py"),
]

BASE_DIR = r"C:\Revamp Monitoramento"
DATA_HOJE = datetime.now().strftime('%d/%m/%Y %H:%M')

# ── Abre thread no Google Chat ─────────────────────────────────────────────────
def abrir_thread():
    payload = {
        "text": f"🤖 *Monitoramento Diário — Cyber/QuintoAndar*\n{DATA_HOJE}\nIniciando envio dos relatórios..."
    }
    resp = requests.post(WEBHOOK_URL, json=payload)
    resp.raise_for_status()
    thread_name = resp.json().get("thread", {}).get("name", "")
    print(f"Thread aberta: {thread_name}")
    return thread_name

def fechar_thread(thread_name, sucessos, falhas):
    total = len(MONITORAMENTOS)
    texto = (
        f"✅ *Monitoramento concluído* — {DATA_HOJE}\n"
        f"Enviados: {sucessos}/{total}"
    )
    if falhas:
        texto += f"\n⚠️ Falhas: {', '.join(falhas)}"

    payload = {"text": texto}
    if thread_name:
        payload["thread"] = {"name": thread_name}

    webhook = WEBHOOK_URL
    if thread_name:
        webhook += "&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"

    requests.post(webhook, json=payload)

# ── Executa cada monitoramento ─────────────────────────────────────────────────
def rodar(script, thread_name, nome_monitoramento=None):
    env = os.environ.copy()
    if thread_name:
        env["GCHAT_THREAD_NAME"] = thread_name
    result = subprocess.run(
        ["python", os.path.join(BASE_DIR, script)],
        capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        print(f"  ERRO em {script}:\n{result.stderr}")
        # Registrar falha no log se for script de geração (envio já registra no próprio script)
        if nome_monitoramento and 'gerar' in script:
            registrar(
                monitoramento = nome_monitoramento,
                timestamp     = datetime.now().strftime("%Y%m%d_%H%M%S"),
                status        = "erro",
                erro          = result.stderr,
            )
        return False
    print(f"  OK: {script}")
    return True

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"Revamp Monitoramento — {DATA_HOJE}")
    print(f"{'='*50}\n")

    thread_name = abrir_thread()
    sucessos = 0
    falhas   = []

    for nome, script_gerar, script_enviar in MONITORAMENTOS:
        print(f"\n── {nome} ──────────────────────────")
        ok_gerar  = rodar(script_gerar,  thread_name="",          nome_monitoramento=nome)
        ok_enviar = rodar(script_enviar, thread_name=thread_name, nome_monitoramento=None) if ok_gerar else False

        if ok_gerar and ok_enviar:
            sucessos += 1
        else:
            falhas.append(nome)

    fechar_thread(thread_name, sucessos, falhas)
    print(f"\nConcluído. {sucessos}/{len(MONITORAMENTOS)} monitoramentos enviados.")
