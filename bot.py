import os
import time
import json
import requests
from datetime import datetime
from threading import Thread
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask

# Inicialização do Flask para manter o Render acordado
app = Flask(__name__)

@app.route("/")
def home():
    return f"🤖 Robô Multimarcas Pro ({LOJA_ALVO.upper()}) está rodando 100% automatizado!"

# Identifica qual loja este bot Render deve gerenciar (shopee ou natura)
# Você pode definir a variável de ambiente LOJA no Render, ou ele assume 'natura' por padrão
LOJA_ALVO = os.environ.get("LOJA", "natura").lower()

# Inicialização Segura do Firebase
db = None
try:
    if not firebase_admin._apps:
        cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
        if cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            cred = credentials.Certificate("firebase_credentials.json")
            firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("🔥 Firebase conectado com sucesso!")
except Exception as e:
    print(f"⚠️ Aviso na inicialização do Firebase: {e}")

def carregar_configuracoes():
    """Lê dinamicamente as configurações da loja correta no Firebase."""
    if not db:
        return None
    try:
        # Puxa 'shopee_settings' ou 'natura_settings' dependendo da instância
        doc_name = "shopee_settings" if LOJA_ALVO == "shopee" else "natura_settings"
        doc_ref = db.collection("configuracoes").doc(doc_name)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            print(f"⚠️ Documento {doc_name} não encontrado no Firebase. Verifique o painel web.")
    except Exception as e:
        print(f"Erro ao ler configurações do Firebase: {e}")
    return None

def calcular_intervalo_segundos(frequencia, detalhe):
    """Converte a frequência escolhida no painel em segundos."""
    detalhe_lower = detalhe.lower() if detalhe else ""
    try:
        import re
        nums = re.findall(r'\d+', detalhe_lower)
        valor = int(nums[0]) if nums else 1
    except:
        valor = 1

    if "minuto" in frequencia.lower() or "minuto" in detalhe_lower:
        return max(60, valor * 60)
    elif "hora" in frequencia.lower() or "hora" in detalhe_lower:
        return max(300, valor * 3600)
    elif "dia" in frequencia.lower():
        return 86400
    
    return 60

def enviar_telegram(token, channel_id, mensagem, foto_url=None):
    """Envia a oferta formatada para o canal do Telegram."""
    if not token or not channel_id:
        print("⚠️ Token ou Channel ID do Telegram não configurados.")
        return {"ok": False}
        
    if foto_url:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {
            "chat_id": channel_id,
            "photo": foto_url,
            "caption": mensagem,
            "parse_mode": "Markdown"
        }
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": channel_id,
            "text": mensagem,
            "parse_mode": "Markdown"
        }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar para o Telegram: {e}")
        return {"ok": False}

def salvar_produto_na_loja(produto_data):
    """Salva o produto na coleção 'products' da vitrine do GitHub Pages."""
    if not db:
        return
    try:
        db.collection("products").add(produto_data)
        print("✅ Produto sincronizado com sucesso na Loja Digital!")
    except Exception as e:
        print(f"❌ Erro ao salvar produto na loja: {e}")

def loop_automatico_robo():
    """Loop contínuo que roda em segundo plano de forma autônoma."""
    print(f"🚀 Robô em segundo plano iniciado para a loja: {LOJA_ALVO.upper()}!")
    time.sleep(15) # Aguarda o sistema estabilizar
    
    while True:
        try:
            config = carregar_configuracoes()
            if not config:
                print(f"⚠️ Configurações da {LOJA_ALVO} não encontradas no Firebase. Tentando novamente em 60s...")
                time.sleep(60)
                continue

            token = config.get("telegram_token")
            channel_id = config.get("channel_id")
            
            if LOJA_ALVO == "shopee":
                aff_link = config.get("affiliate_link", "https://s.shopee.com.br/6VOwp1jg5L")
                nome_produto = "Achadinho Imperdível da Shopee"
                preco_original = 199.00
                desconto_percentual = 15
                preco_com_desconto = preco_original - (preco_original * (desconto_percentual / 100))
                cupom = "OFERTASHOPEE"
                categoria = "Achadinhos"
                foto_url = "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=800&q=80"
                descricao_curta = "Produto selecionado com super desconto e frete grátis."
                
                mensagem_telegram = (
                    f"🔥 *OFERTA EXCLUSIVA SHOPEE*\n\n"
                    f"📱 *{nome_produto}*\n\n"
                    f"❌ De: R$ {preco_original:.2f}".replace('.', ',') + f"\n"
                    f"💰 *Por apenas: R$ {preco_com_desconto:.2f}* `(-{desconto_percentual}% OFF)`\n"
                    f"🏷️ *Cupom:* `{cupom}`\n\n"
                    f"📝 *Detalhes:* {descricao_curta}\n\n"
                    f"🔗 *Compre aqui:*\n{aff_link}"
                )
            else:
                aff_link = config.get("affiliate_link", "https://www.minhaloja.natura.com/consultoria/ora_et_labora")
                nome_produto = "Deo Parfum Essencial Exclusivo Masculino 100ml"
                preco_original = 180.00
                desconto_percentual = 10
                preco_com_desconto = preco_original - (preco_original * (desconto_percentual / 100))
                cupom = "CLIENTEVIP"
                categoria = "Perfumaria"
                foto_url = "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=800&q=80"
                descricao_curta = "Fragrância marcante com notas amadeiradas e especiadas."
                
                mensagem_telegram = (
                    f"🌸 *LANÇAMENTO / OFERTA NATURA*\n\n"
                    f"✨ *{nome_produto}*\n\n"
                    f"❌ De: R$ {preco_original:.2f}".replace('.', ',') + f"\n"
                    f"💰 *Por apenas: R$ {preco_com_desconto:.2f}* `(-{desconto_percentual}% OFF)`\n"
                    f"🏷️ *Cupom:* `{cupom}`\n\n"
                    f"📝 *Detalhes:* {descricao_curta}\n\n"
                    f"🔗 *Compre no meu Espaço Natura:*\n{aff_link}"
                )
            
            freq = config.get("frequencia", "Por Minuto")
            detalhe = config.get("detalhe_frequencia", "1 minuto")
            intervalo_segundos = calcular_intervalo_segundos(freq, detalhe)
            
            print(f"🔄 Executando ciclo {LOJA_ALVO}... Próximo disparo em {intervalo_segundos}s.")

            # Envia para o Telegram
            res_tg = enviar_telegram(token, channel_id, mensagem_telegram, foto_url)
            if res_tg.get("ok"):
                print(f"✅ Oferta da {LOJA_ALVO} enviada para o Telegram com sucesso!")
            else:
                print(f"⚠️ Falha ao enviar no Telegram: {res_tg}")
            
            # Salva na Loja Digital (Firebase)
            produto_para_loja = {
                "name": nome_produto,
                "category": categoria,
                "isFeatured": True,
                "image": foto_url,
                "images": [foto_url],
                "price": str(preco_original),
                "discountPercent": str(desconto_percentual),
                "description": f"✨ Desconto especial garantido!\n\n{descricao_curta}",
                "link": aff_link,
                "code": cupom,
                "validityDays": 30,
                "totalUses": 30,
                "usedCount": 0,
                "createdAt": datetime.utcnow().isoformat()
            }
            salvar_produto_na_loja(produto_para_loja)

            time.sleep(intervalo_segundos)

        except Exception as e:
            print(f"❌ Erro no loop do robô ({LOJA_ALVO}): {e}")
            time.sleep(60)

if __name__ == "__main__":
    # Inicia o robô em uma Thread separada rodando em segundo plano
    t = Thread(target=loop_automatico_robo)
    t.daemon = True
    t.start()
    
    # Inicia o servidor Flask na porta exigida pelo Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
