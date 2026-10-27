import os
import time
import threading
import random
import requests
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializa o Flask para manter a aplicação viva no Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Robô de Afiliados Oficial com Cupom Fixo e Sistema de Pausa rodando!"

# Inicializa o Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Descobre qual é a loja com base na variável de ambiente LOJA configurada no Render
LOJA = os.getenv("LOJA", "shopee").lower()
DOCUMENTO_CONFIG = f"{LOJA}_settings"

print(f"🤖 Robô oficial iniciado para a loja: {LOJA.upper()}!")

# Cupom fixo da sua loja
CUPOM_FIXO = "CLIENTEVIP"

# Vitrine de produtos estruturados com cálculo automático e aviso do cupom fixo
PRODUTOS_VITRINE = {
    "natura": [
        "🌊 *Colônia Desodorante Kayak Masculino - 100ml*\n\nO clássico que traz a sensação de liberdade e energia pura. Perfeito para o dia a dia e momentos de aventura!\n\n💰 *Valor na Loja:* R$ 149,90\n🔥 *Com o seu Cupom (10% OFF):* R$ 134,91\n🏷️ *Cupom Exclusivo:* `{cupom}` *(Copie e cole no carrinho!)*\n\n👉 [Comprar Agora na Minha Loja]({link})"
    ],
    "shopee": [
        "🔥 *Achadinho da Shopee: Fone de Ouvido Bluetooth TWS*\n\nExcelente qualidade de som, bateria duradoura e preço de fábrica com frete grátis!\n\n💰 *Preço Especial:* R$ 59,90\n🏷️ *Utilize seu cupom na finalização!*\n\n👉 [Aproveitar Oferta na Shopee]({link})"
    ],
    "picpay": [
        "💳 *PicPay Card com Cashback Exclusivo*\n\nPeça já o seu cartão sem anuidade e garanta dinheiro de volta em todas as suas compras!\n\n👉 [Solicitar Cartão PicPay]({link})"
    ]
}

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
            print("✅ Oferta com cupom enviada com sucesso para o Telegram!")
        else:
            print(f"❌ Erro ao enviar para o Telegram: {response.text}")
    except Exception as e:
        print(f"⚠️ Erro de conexão com o Telegram: {e}")

def loop_disparos():
    """Loop principal que gerencia o status (pausado/ativo) e envia as ofertas com o cupom fixo."""
    while True:
        try:
            doc_ref = db.collection("configuracoes").document(DOCUMENTO_CONFIG)
            doc = doc_ref.get()

            if doc.exists:
                config = doc.to_dict()
                token = config.get("telegram_token")
                channel_id = config.get("channel_id")
                affiliate_link = config.get("affiliate_link")
                
                # 🛑 SISTEMA DE PAUSA: Lê o campo 'status' (ativo ou pausado)
                status = config.get("status", "ativo").lower()

                if status == "pausado":
                    print(f"⏸️ Robô [{DOCUMENTO_CONFIG}] está PAUSADO pelo painel do Firebase.")
                else:
                    print(f"🔄 Executando ciclo de envio para [{DOCUMENTO_CONFIG}]...")
                    if token and channel_id and affiliate_link:
                        # Pega a lista da loja correspondente
                        lista = PRODUTOS_VITRINE.get(LOJA, PRODUTOS_VITRINE["shopee"])
                        
                        # Seleciona o texto base do produto
                        texto_produto = random.choice(lista)
                        
                        # Insere o link de afiliado e o cupom fixo na mensagem
                        mensagem_final = texto_produto.format(link=affiliate_link, cupom=CUPOM_FIXO)

                        enviar_mensagem_telegram(token, channel_id, mensagem_final)
                    else:
                        print(f"⚠️ Faltam campos essenciais (token, channel_id ou affiliate_link) em '{DOCUMENTO_CONFIG}'.")
            else:
                print(f"❌ Documento '{DOCUMENTO_CONFIG}' não encontrado.")

        except Exception as e:
            print(f"⚠️ Erro no ciclo de disparo: {e}")

        # ⏱️ Intervalo entre os disparos (3600 segundos = 1 hora)
        time.sleep(3600)

# Inicia o loop em segundo plano
t = threading.Thread(target=loop_disparos)
t.daemon = True
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
