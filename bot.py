import os
import time
import threading
import requests
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializa o Flask para manter a aplicação viva no Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Robô de Afiliados rodando perfeitamente!"

# Inicializa o Firebase (garante que não inicializa duas vezes)
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Descobre qual é a loja com base na variável de ambiente LOJA configurada no Render
LOJA = os.getenv("LOJA", "shopee").lower()
DOCUMENTO_CONFIG = f"{LOJA}_settings"

print(f"🤖 Robô em segundo plano iniciado para a loja: {LOJA.upper()}!")

def enviar_mensagem_telegram(token, channel_id, mensagem):
    """Função para enviar a mensagem formatada para o canal do Telegram."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Mensagem enviada com sucesso para o Telegram!")
        else:
            print(f"❌ Erro ao enviar para o Telegram: {response.text}")
    except Exception as e:
        print(f"⚠️ Erro de conexão com o Telegram: {e}")

def loop_disparos():
    """Loop principal que busca as configurações no Firestore e executa o envio."""
    while True:
        try:
            # Busca o documento correspondente na coleção 'configuracoes'
            doc_ref = db.collection("configuracoes").document(DOCUMENTO_CONFIG)
            doc = doc_ref.get()

            if doc.exists:
                config = doc.to_dict()
                token = config.get("telegram_token")
                channel_id = config.get("channel_id")
                affiliate_link = config.get("affiliate_link")

                print(f"🔄 Lendo configurações de [{DOCUMENTO_CONFIG}]...")

                # Verifica se os dados essenciais estão preenchidos
                if token and channel_id and affiliate_link:
                    mensagem = f"🔥 *Oferta Imperdível!* 🔥\n\nAproveite agora mesmo e confira o produto exclusivo:\n👉 {affiliate_link}"
                    enviar_mensagem_telegram(token, channel_id, mensagem)
                else:
                    print(f"⚠️ Atenção: Faltam campos preenchidos em '{DOCUMENTO_CONFIG}' (telegram_token, channel_id ou affiliate_link).")
            else:
                print(f"❌ Documento '{DOCUMENTO_CONFIG}' não encontrado na coleção 'configuracoes'.")

        except Exception as e:
            print(f"⚠️ Erro no ciclo de disparo: {e}")

        # Aguarda 60 segundos antes de verificar novamente (ajuste o tempo se preferir)
        time.sleep(60)

# Inicia o loop do robô em segundo plano (Thread separada para não travar o Flask)
t = threading.Thread(target=loop_disparos)
t.daemon = True
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
