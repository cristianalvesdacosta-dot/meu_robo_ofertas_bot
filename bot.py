import os
import time
import threading
import requests
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

@app.route('/')
def home():
    return "Robô de Afiliados Rodando 100% Estável!"

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

LOJA = os.getenv("LOJA", "shopee").lower()
DOCUMENTO_CONFIG = f"{LOJA}_settings"

print(f"🤖 Robô iniciado para a loja: {LOJA.upper()}!")

# ==========================================
# 🎁 CATÁLOGO COM ROTAÇÃO SEQUENCIAL (SEM REPETIÇÃO)
# ==========================================
CATALOGO_PRODUTOS = {
    "natura": [
        {
            "foto": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800",
            "texto": "🌊 *Colônia Desodorante Kayak Masculino - 100ml*\n\nO clássico que traz a sensação de liberdade e energia pura. Perfeito para o dia a dia!\n\n💰 *Valor na Loja:* R$ 149,90\n🔥 *Com o seu Cupom (10% OFF):* R$ 134,91\n🏷️ *Cupom Exclusivo:* `{cupom}`\n\n👉 [Comprar na Minha Loja]({link})"
        },
        {
            "foto": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800",
            "texto": "🌸 *Desodorante Colônia Luna Tradicional - 75ml*\n\nChipré brasileiro que une o frescor das frutas cítricas com um toque floral marcante.\n\n💰 *Valor na Loja:* R$ 159,90\n🔥 *Com o seu Cupom (10% OFF):* R$ 143,91\n🏷️ *Cupom Exclusivo:* `{cupom}`\n\n👉 [Comprar na Minha Loja]({link})"
        },
        {
            "foto": "https://images.unsplash.com/photo-1608248597359-9d74b075b2a2?w=800",
            "texto": "💧 *Creme Desodorante Nutritivo Tododia Baunilha e Macadâmia - 400ml*\n\nNutrição profunda com toque aveludado e perfume que dura o dia todo.\n\n💰 *Valor na Loja:* R$ 69,90\n🔥 *Com o seu Cupom (10% OFF):* R$ 62,91\n🏷️ *Cupom Exclusivo:* `{cupom}`\n\n👉 [Comprar na Minha Loja]({link})"
        }
    ],
    "shopee": [
        {
            "foto": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800",
            "texto": "🔥 *Fone de Ouvido Bluetooth TWS Sem Fio*\n\nExcelente qualidade de som, bateria duradoura e preço de fábrica com frete grátis!\n\n💰 *Preço Especial:* R$ 49,90\n🏷️ *Utilize seu cupom na finalização!*\n\n👉 [Aproveitar Oferta na Shopee]({link})"
        },
        {
            "foto": "https://images.unsplash.com/photo-1584438784894-089d6a62b8fa?w=800",
            "texto": "⚡ *Suporte Veicular Magnético para Celular*\n\nPraticidade e segurança para o seu dia a dia no trânsito. Super rápido!\n\n💰 *Preço Especial:* R$ 24,90\n\n👉 [Aproveitar Oferta na Shopee]({link})"
        },
        {
            "foto": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800",
            "texto": "🎒 *Mochila Impermeável Executiva / Viagem*\n\nCom compartimento para notebook e entrada USB integrada.\n\n💰 *Preço Especial:* R$ 89,90\n\n👉 [Aproveitar Oferta na Shopee]({link})"
        }
    ],
    "picpay": [
        {
            "foto": "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=800",
            "texto": "💳 *PicPay Card com Cashback Exclusivo*\n\nPeça já o seu cartão sem anuidade e garanta dinheiro de volta em todas as suas compras!\n\n👉 [Solicitar Cartão PicPay]({link})"
        }
    ]
}

# Índice global para controlar a ordem exata dos produtos (sem repetir)
indice_atual = 0

def enviar_mensagem_telegram(token, channel_id, produto):
    """Envia a foto perfeitamente integrada no topo com a legenda limpa."""
    foto_url = produto.get("foto")
    legenda = produto.get("texto")
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {
        "chat_id": channel_id,
        "photo": foto_url,
        "caption": legenda,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Oferta com foto enviada com sucesso!")
        else:
            print(f"❌ Erro ao enviar foto: {response.text}")
    except Exception as e:
        print(f"⚠️ Erro de conexão: {e}")

def manter_ativo():
    url_app = os.getenv("RENDER_EXTERNAL_URL", "https://seu-app.onrender.com")
    while True:
        try:
            time.sleep(480)
            requests.get(url_app)
            print("🔄 [Anti-Sleep] Ping enviado!")
        except Exception as e:
            print(f"⚠️ [Anti-Sleep] Erro no ping: {e}")

def loop_disparos():
    global indice_atual
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
                    print(f"⏸️ Robô [{DOCUMENTO_CONFIG}] está pausado.")
                else:
                    if token and channel_id and affiliate_link:
                        lista_produtos = CATALOGO_PRODUTOS.get(LOJA, CATALOGO_PRODUTOS["shopee"])
                        
                        # Pega o produto da vez de forma sequencial (evita repetição)
                        produto_selecionado = lista_produtos[indice_atual].copy()
                        
                        # Avança para o próximo produto na próxima execução
                        indice_atual = (indice_atual + 1) % len(lista_produtos)
                        
                        produto_selecionado["texto"] = produto_selecionado["texto"].format(
                            link=affiliate_link, 
                            cupom=cupom
                        )

                        enviar_mensagem_telegram(token, channel_id, produto_selecionado)
                    else:
                        print("⚠️ Faltam campos essenciais no Firebase.")
            else:
                print("❌ Documento não encontrado no Firebase.")
        except Exception as e:
            print(f"⚠️ Erro no loop: {e}")

        # Intervalo de 1 minuto entre os disparos
        time.sleep(60)

t_disparos = threading.Thread(target=loop_disparos)
t_disparos.daemon = True
t_disparos.start()

t_ping = threading.Thread(target=manter_ativo)
t_ping.daemon = True
t_ping.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
