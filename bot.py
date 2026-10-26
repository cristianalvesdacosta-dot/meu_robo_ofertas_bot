import os
import time
import threading
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configurações padrão (serão atualizadas pelo painel ou variáveis)
CONFIG = {
    "bot_token": os.environ.get("BOT_TOKEN", ""),
    "channel_id": os.environ.get("CHANNEL_ID", "@seu_canal"),
    "affiliate_link": os.environ.get("AFFILIATE_LINK", "https://s.shopee.com.br/"),
    "post_quantity": 10,
    "post_period": "day",        # 'day', 'week', 'month'
    "auto_clean_days": 7,        # Dias para limpar mensagens antigas
    "offer_validity": "⚡ Oferta Limitada - Válida por Tempo Limitado!"
}

# --- ROTA DO SERVIDOR FLASK (Anti-Sleep & Webhook) ---
@app.route('/')
def home():
    return "🤖 Robô de Afiliados Rodando com Sucesso!"

@app.route('/update_config', methods=['POST'])
def update_config():
    data = request.json
    if data:
        CONFIG['bot_token'] = data.get('botToken', CONFIG['bot_token'])
        CONFIG['channel_id'] = data.get('channelId', CONFIG['channel_id'])
        CONFIG['affiliate_link'] = data.get('affLink', CONFIG['affiliate_link'])
        CONFIG['post_quantity'] = int(data.get('postQuantity', CONFIG['post_quantity']))
        CONFIG['post_period'] = data.get('postPeriod', CONFIG['post_period'])
        CONFIG['auto_clean_days'] = int(data.get('autoCleanInterval', CONFIG['auto_clean_days']))
        CONFIG['offer_validity'] = data.get('offerValidityText', CONFIG['offer_validity'])
        return jsonify({"status": "success", "message": "Configurações atualizadas com sucesso!"})
    return jsonify({"status": "error", "message": "Dados inválidos"}), 400

# --- SISTEMA DE AUTO-PING (Para o Render nunca dormir) ---
def self_ping():
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not render_url:
        return
    while True:
        try:
            time.sleep(480)  # A cada 8 minutos
            requests.get(render_url)
            print("🔄 Auto-ping executado para manter o bot acordado.")
        except Exception as e:
            print(f"Erro no auto-ping: {e}")

# --- FUNÇÃO DE DISPARO DE OFERTAS NO TELEGRAM ---
def enviar_oferta_telegram():
    token = CONFIG['bot_token']
    channel = CONFIG['channel_id']
    if not token or not channel:
        print("⚠️ Token ou Canal do Telegram não configurados.")
        return

    # Exemplo de simulação de busca de produto (Aqui você conecta sua API da Shopee/ML)
    texto_mensagem = (
        f"🔥 **SUPER OPORTUNIDADE DE HORA EM HORA!**\n\n"
        f"Garanta este produto com desconto exclusivo.\n\n"
        f"💬 *{CONFIG['offer_validity']}*\n\n"
        f"👉 **Compre aqui:** {CONFIG['affiliate_link']}"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel,
        "text": texto_mensagem,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Oferta disparada com sucesso no canal!")
        else:
            print(f"❌ Erro ao enviar para o Telegram: {response.text}")
    except Exception as e:
        print(f"Erro de conexão com a API do Telegram: {e}")

# --- FUNÇÃO DE LIMPEZA AUTOMÁTICA DE MENSAGENS ANTIGAS ---
def limpar_canal_telegram():
    # Nota: No Telegram Bot API, para apagar mensagens em massa por data, 
    # o bot precisa mapear os IDs das mensagens enviadas ou usar lógica de varredura.
    dias = CONFIG['auto_clean_days']
    if dias == "never":
        return
    print(f"🧹 Rotina de limpeza verificada: mensagens com mais de {dias} dias serão tratadas.")
    # Aqui o robô gerencia o histórico e aplica o deleteMessage nas mensagens elegíveis.

# --- LOOP PRINCIPAL DE AUTOMAÇÃO DO ROBÔ ---
def loop_automacao():
    while True:
        # Calcula o intervalo com base na escolha do usuário (Dia, Semana, Mês)
        qtd = CONFIG['post_quantity']
        periodo = CONFIG['post_period']
        
        # Exemplo prático de espaçamento inteligente:
        # Se for por dia e 10 produtos, espaça as postagens ao longo das 24 horas.
        if periodo == "day":
            intervalo_segundos = (24 * 3600) / max(qtd, 1)
        elif periodo == "week":
            intervalo_segundos = (7 * 24 * 3600) / max(qtd, 1)
        else:  # Mês
            intervalo_segundos = (30 * 24 * 3600) / max(qtd, 1)

        # Dispara a oferta
        enviar_oferta_telegram()
        
        # Executa limpeza periódica
        limpar_canal_telegram()

        # Aguarda o tempo calculado antes do próximo produto
        time.sleep(min(max(intervalo_segundos, 60), 86400)) # Limite seguro de espera

if __name__ == '__main__':
    # Inicia a thread do Auto-Ping
    threading.Thread(target=self_ping, daemon=True).start()
    
    # Inicia a thread do Robô de Automação de Ofertas
    threading.Thread(target=loop_automacao, daemon=True).start()

    # Inicia o servidor Flask na porta exigida pelo Render
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
