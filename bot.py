import os
import time
import threading
import requests
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializa o Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

LOJA = os.getenv("LOJA", "shopee").lower()
DOCUMENTO_CONFIG = f"{LOJA}_settings"

print(f"🤖 Robô infalível iniciado para a loja: {LOJA.upper()}!")

# ==========================================
# 🎁 CATÁLOGO OFICIAL COM FOTOS REAIS E DIFERENTES
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

indice_atual = 0

def enviar_mensagem_telegram(token, channel_id, produto):
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
            print("✅ Oferta com foto disparada com sucesso no automático!")
        else:
            print(f"❌ Erro do Telegram: {response.text}")
    except Exception as e:
        print(f"⚠️ Erro de conexão: {e}")

def loop_disparos():
    global indice_atual
    print("🚀 Loop de disparos automáticos iniciado em segundo plano!")
    
    while True:
        try:
            print(f"🔍 [Loop] Buscando documento '{DOCUMENTO_CONFIG}' no Firebase...")
            doc_ref = db.collection("configuracoes").document(DOCUMENTO_CONFIG)
            doc = doc_ref.get()

            if doc.exists:
                config = doc.to_dict()
                token = config.get("telegram_token")
                channel_id = config.get("channel_id")
                affiliate_link = config.get("affiliate_link")
                cupom = config.get("cupom", "CLIENTEVIP")

                if token and channel_id and affiliate_link:
                    lista_produtos = CATALOGO_PRODUTOS.get(LOJA, CATALOGO_PRODUTOS["shopee"])
                    
                    produto_selecionado = lista_produtos[indice_atual].copy()
                    indice_atual = (indice_atual + 1) % len(lista_produtos)
                    
                    produto_selecionado["texto"] = produto_selecionado["texto"].format(
                        link=affiliate_link, 
                        cupom=cupom
                    )

                    print(f"📤 [Loop] Enviando produto índice {indice_atual} para o canal {channel_id}...")
                    enviar_mensagem_telegram(token, channel_id, produto_selecionado)
                else:
                    print("⚠️ [Loop] Faltam campos (token, channel_id ou affiliate_link) no Firebase.")
            else:
                print(f"❌ [Loop] Documento '{DOCUMENTO_CONFIG}' não encontrado no Firebase.")

        except Exception as e:
            print(f"⚠️ [Loop] Erro crítico no ciclo: {e}")

        # Aguarda 60 segundos (1 minuto) exatos para o próximo envio
        time.sleep(60)

# Inicia o loop de disparos imediatamente antes de qualquer coisa
t = threading.Thread(target=loop_disparos)
t.daemon = True
t.start()

# Mantém um servidor HTTP leve rodando só para o Render não reclamar de porta fechada
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Robô de Afiliados Rodando no Automático!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
