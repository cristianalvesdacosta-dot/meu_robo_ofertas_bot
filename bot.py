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
    return "Robô de Afiliados Oficial rodando 100% liso!"

# Inicializa o Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Descobre qual é a loja com base na variável de ambiente LOJA configurada no Render
LOJA = os.getenv("LOJA", "shopee").lower()
DOCUMENTO_CONFIG = f"{LOJA}_settings"

print(f"🤖 Robô oficial iniciado para a loja: {LOJA.upper()}!")

# ==========================================
# 🎁 CATÁLOGO DE PRODUTOS VARIADOS COM FOTOS
# ==========================================
CATALOGO_PRODUTOS = {
    "natura": [
        {
            "foto": "https://img.natura.com.br/product/1000w/114563_1.jpg",
            "texto": "🌊 *Colônia Desodorante Kayak Masculino - 100ml*\n\nO clássico que traz a sensação de liberdade e energia pura. Perfeito para o dia a dia!\n\n💰 *Valor na Loja:* R$ 149,90\n🔥 *Com o seu Cupom (10% OFF):* R$ 134,91\n🏷️ *Cupom Exclusivo:* `{cupom}`\n\n👉 [Comprar na Minha Loja]({link})"
        },
        {
            "foto": "https://img.natura.com.br/product/1000w/70123_1.jpg",
            "texto": "🌸 *Desodorante Colônia Luna Tradicional - 75ml*\n\nChipré brasileiro que une o frescor das frutas cítricas com um toque floral marcante.\n\n💰 *Valor na Loja:* R$ 159,90\n🔥 *Com o seu Cupom (10% OFF):* R$ 143,91\n🏷️ *Cupom Exclusivo:* `{cupom}`\n\n👉 [Comprar na Minha Loja]({link})"
        },
        {
            "foto": "https://img.natura.com.br/product/1000w/85412_1.jpg",
            "texto": "💧 *Creme Desodorante Nutritivo Tododia Baunilha e Macadâmia - 400ml*\n\nNutrição profunda com toque aveludado e perfume que dura o dia todo.\n\n💰 *Valor na Loja:* R$ 69,90\n🔥 *Com o seu Cupom (10% OFF):* R$ 62,91\n🏷️ *Cupom Exclusivo:* `{cupom}`\n\n👉 [Comprar na Minha Loja]({link})"
        }
    ],
    "shopee": [
        {
            "foto": "https://cf.shopee.com.br/file/sg-11134201-7rdvn-m180v362i02c7b",
            "texto": "🔥 *Fone de Ouvido Bluetooth TWS Sem Fio*\n\nExcelente qualidade de som, bateria duradoura e preço de fábrica com frete grátis!\n\n💰 *Preço Especial:* R$ 49,90\n🏷️ *Utilize seu cupom na finalização!*\n\n👉 [Aproveitar Oferta na Shopee]({link})"
        },
        {
            "foto": "https://cf.shopee.com.br/file/br-11134207-7r98o-m123456789",
            "texto": "⚡ *Suporte Veicular Magnético para Celular*\n\nPraticidade e segurança para o seu dia a dia no trânsito. Super rápido!\n\n💰 *Preço Especial:* R$ 24,90\n\n👉 [Aproveitar Oferta na Shopee]({link})"
        },
        {
            "foto": "https://cf.shopee.com.br/file/br-11134207-7r98o-m987654321",
            "texto": "🎒 *Mochila Impermeável Executiva / Viagem*\n\nCom compartimento para notebook e entrada USB integrada.\n\n💰 *Preço Especial:* R$ 89,90\n\n👉 [Aproveitar Oferta na Shopee]({link})"
        }
    ],
    "picpay": [
        {
            "foto": "https://static.picpay.com/site/icons/picpay-card.png",
            "texto": "💳 *PicPay Card com Cashback Exclusivo*\n\nPeça já o seu cartão sem anuidade e garanta dinheiro de volta em todas as suas compras!\n\n👉 [Solicitar Cartão PicPay]({link})"
        }
    ]
}

def enviar_mensagem_telegram(token, channel_id, produto):
    """Envia a foto com a legenda formatada para o canal do Telegram."""
    foto_url = produto.get("foto")
    legenda = produto.get("texto")
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {
        "chat_id": channel_id,
        "photo": foto_url,
        "caption": legenda,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Oferta enviada com sucesso para o Telegram!")
        else:
            # Fallback de segurança caso dê erro na foto: envia texto puro
            print(f"⚠️ Erro na foto, enviando texto alternativo: {response.text}")
            url_txt = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url_txt, json={"chat_id": channel_id, "text": legenda, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"⚠️ Erro de conexão com o Telegram: {e}")

# ==========================================
# ⚡ FUNÇÃO ANTI-SLEEP (Mantém o Render acordado)
# ==========================================
def manter_ativo():
    url_app = os.getenv("RENDER_EXTERNAL_URL", "https://seu-app.onrender.com")
    while True:
        try:
            time.sleep(480) # 8 minutos
            requests.get(url_app)
            print("🔄 [Anti-Sleep] Ping enviado com sucesso!")
        except Exception as e:
            print(f"⚠️ [Anti-Sleep] Erro no ping: {e}")

# ==========================================
# 🔄 LOOP DE DISPAROS (Base Estável)
# ==========================================
def loop_disparos():
    while True:
        try:
            doc_ref = db.collection("configuracoes").document(DOCUMENTO_CONFIG)
            doc = doc_ref.get()

            if doc.exists:
                config = doc.to_dict()
                token = config.get("telegram_token")
                channel_id = config.get("channel_id")
                affiliate_link = config.get("affiliate_link")
                
                status = config.get("status", "ativo").lower()
                cupom = config.get("cupom", "CLIENTEVIP")

                if status == "pausado":
                    print(f"⏸️ Robô [{DOCUMENTO_CONFIG}] está PAUSADO.")
                else:
                    print(f"🔄 Executando envio para [{DOCUMENTO_CONFIG}]...")
                    if token and channel_id and affiliate_link:
                        
                        # Pega a lista da loja correspondente e escolhe um produto diferente a cada ciclo
                        lista_produtos = CATALOGO_PRODUTOS.get(LOJA, CATALOGO_PRODUTOS["shopee"])
                        produto_sorteado = random.choice(lista_produtos).copy()
                        
                        # Insere o link e o cupom no texto
                        produto_sorteado["texto"] = produto_sorteado["texto"].format(
                            link=affiliate_link, 
                            cupom=cupom
                        )

                        enviar_mensagem_telegram(token, channel_id, produto_sorteado)
                    else:
                        print(f"⚠️ Faltam campos essenciais em '{DOCUMENTO_CONFIG}'.")
            else:
                print(f"❌ Documento '{DOCUMENTO_CONFIG}' não encontrado.")

        except Exception as e:
            print(f"⚠️ Erro no loop: {e}")

        # ⏱️ Intervalo de 60 segundos entre os disparos
        time.sleep(60)

# Inicia as rotinas em segundo plano
t_disparos = threading.Thread(target=loop_disparos)
t_disparos.daemon = True
t_disparos.start()

t_ping = threading.Thread(target=manter_ativo)
t_ping.daemon = True
t_ping.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
