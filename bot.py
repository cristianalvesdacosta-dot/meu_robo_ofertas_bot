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
    return "🤖 Robô Multimarcas Pro está rodando 100% automatizado!"

# Inicialização do Firebase
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

def carregar_configuracoes_natura():
    """Lê as configurações da Natura salvas no Firebase."""
    try:
        doc_ref = db.collection("configuracoes").doc("natura_settings")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        print(f"Erro ao ler configurações da Natura: {e}")
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
    try:
        db.collection("products").add(produto_data)
        print("✅ Produto sincronizado com sucesso na Loja Digital!")
    except Exception as e:
        print(f"❌ Erro ao salvar produto na loja: {e}")

def loop_automatico_robô():
    """Loop contínuo que roda em segundo plano de forma autônoma."""
    print("🚀 Robô em segundo plano iniciado com sucesso!")
    time.sleep(10) # Aguarda o sistema estabilizar
    
    while True:
        try:
            config = carregar_configuracoes_natura()
            if not config:
                print("⚠️ Configurações da Natura não encontradas. Aguardando...")
                time.sleep(60)
                continue

            token = config.get("telegram_token")
            channel_id = config.get("channel_id")
            aff_link = config.get("affiliate_link", "https://www.minhaloja.natura.com/consultoria/ora_et_labora")
            
            freq = config.get("frequencia", "Por Minuto")
            detalhe = config.get("detalhe_frequencia", "1 minuto")
            intervalo_segundos = calcular_intervalo_segundos(freq, detalhe)
            
            print(f"🔄 Executando ciclo Natura... Próximo em {intervalo_segundos}s.")
            
            # Dados simulados do produto com o cálculo do cupom CLIENTEVIP (10% OFF)
            nome_produto = "Deo Parfum Essencial Exclusivo Masculino 100ml"
            preco_original = 180.00
            desconto_percentual = 10
            preco_com_desconto = preco_original - (preco_original * (desconto_percentual / 100))
            cupom = "CLIENTEVIP"
            categoria = "Perfumaria"
            foto_url = "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=800&q=80"
            descricao_curta = "Fragrância marcante com notas amadeiradas e especiadas."
            
            # Mensagem detalhada para o Telegram
            mensagem_telegram = (
                f"🌸 *LANÇAMENTO / OFERTA NATURA*\n\n"
                f"✨ *{nome_produto}*\n\n"
                f"❌ De: R$ {preco_original:.2f}".replace('.', ',') + f"\n"
                f"💰 *Por apenas: R$ {preco_com_desconto:.2f}* `(-{desconto_percentual}% OFF)`\n"
                f"🏷️ *Cupom:* `{cupom}`\n\n"
                f"📝 *Detalhes:* {descricao_curta}\n\n"
                f"🔗 *Compre no meu Espaço Natura (com o cupom aplicado):*\n"
                f"{aff_link}"
            )

            # Envia para o Telegram
            res_tg = enviar_telegram(token, channel_id, mensagem_telegram, foto_url)
            if res_tg.get("ok"):
                print("✅ Oferta enviada para o Telegram com sucesso!")
            
            # Salva na Loja Digital (Firebase)
            produto_para_loja = {
                "name": nome_produto,
                "category": categoria,
                "isFeatured": True,
                "image": foto_url,
                "images": [foto_url],
                "price": str(preco_original),
                "discountPercent": str(desconto_percentual),
                "description": f"✨ 10% de OFF garantido! Copie o cupom CLIENTEVIP e use em qualquer produto da loja.\n\n{descricao_curta}",
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
            print(f"❌ Erro no loop do robô: {e}")
            time.sleep(60)

if __name__ == "__main__":
    # Inicia o robô em uma Thread separada rodando em segundo plano
    t = Thread(target=loop_automatico_robô)
    t.daemon = True
    t.start()
    
    # Inicia o servidor Flask na porta exigida pelo Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
