import os
import time
import requests
import schedule
import threading
from flask import Flask

# Inicializa o mini servidor web interno para manter o Render 100% acordado
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Robô de Afiliados Pro rodando 24h na nuvem com sucesso!"

def iniciar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=porta)

def keep_alive_interno():
    """Auto-ping interno a cada 8 minutos para evitar o modo sleep do Render."""
    time.sleep(30)
    url_local = "http://127.0.0.1:" + str(os.environ.get("PORT", 10000)) + "/"
    while True:
        try:
            time.sleep(480) # 8 minutos
            requests.get(url_local, timeout=5)
            print("🔄 [Anti-Sleep] Auto-ping executado com sucesso!")
        except Exception as e:
            print(f"⚠️ [Anti-Sleep] Erro: {e}")

def rotina_postagem():
    print("🚀 [Robô] Disparando ofertas diárias...")

def rotina_limpeza():
    print("🧹 [Robô] Limpando mensagens antigas da semana...")

schedule.every().day.at("09:00").do(rotina_postagem)
schedule.every().monday.at("00:00").do(rotina_limpeza)

def executar_agendamentos():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    print("🤖 Iniciando Robô de Afiliados...")
    threading.Thread(target=keep_alive_interno, daemon=True).start()
    threading.Thread(target=executar_agendamentos, daemon=True).start()
    iniciar_servidor_web()
