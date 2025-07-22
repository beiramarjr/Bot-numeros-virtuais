import telebot
import requests
import json
import time
import threading
import schedule
from telebot import types
from datetime import datetime

TOKEN = '7686670285:AAE3WSKt8HoqYnm6m6aXmGMb6-Hue8VShX0'
ADMIN_ID = 6782574931
SMS_ACTIVATE_API = 'd93d557720A61172d34d946Ac610e7f3'
SIM5_API_KEY = 'SUA_CHAVE_5SIM_AQUI'

bot = telebot.TeleBot(TOKEN)

usuarios = {}
saldos = {}
compras = {}
geracoes = {}
bloqueios = {}
recargas_pendentes = {}
ultima_requisicao = {}

facebook_prontos = {
    "D - Diogo hortega (R$20)": {"login": "17982307535", "senha": "22setembro95@"},
    "H - Higor kalleb (R$20)": {"login": "12981783300", "senha": "22setembro95"},
    "M - Piu Santana (R$20)": {"login": "11980991935", "senha": "22setembro95."},
}

apps_disponiveis = ['Facebook', 'WhatsApp', 'Telegram', 'TikTok', 'OLX']
operadoras_fixas = {
    'facebook': {
        'vivo': 1.30,
        'tim': 1.30,
        'claro': 1.20,
        'oi': 1.20
    }
}

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda m: m.text == 'Start 🔄')
def start(m):
    usuarios[m.from_user.id] = {'nome': m.from_user.first_name}
    if m.from_user.id == ADMIN_ID:
        saldos[m.from_user.id] = 999
    elif m.from_user.id not in saldos:
        saldos[m.from_user.id] = 0
    if m.from_user.id not in compras:
        compras[m.from_user.id] = 0
    menu_principal(m)

def menu_principal(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Comprar Número', 'Facebook Pronto')
    markup.add('Saldo / Recarga', f'Seu Saldo: R${saldos.get(m.from_user.id, 0):.2f}')
    markup.add('Dúvidas', 'Start 🔄')
    msg = "Escolha uma opção abaixo:\n\n🎁 Promoção: Compre 7 Facebooks Prontos e ganhe o 8º grátis!\n💸 Recarga mínima: R$20"
    bot.send_message(m.chat.id, msg, reply_markup=markup)
@bot.message_handler(func=lambda m: m.text == 'Facebook Pronto')
def facebook_pronto(m):
    total = compras.get(m.from_user.id, 0)
    markup = types.InlineKeyboardMarkup()
    for nome in facebook_prontos:
        markup.add(types.InlineKeyboardButton(text=nome, callback_data=f"selecionar_{nome}"))
    msg = f"*Contas disponíveis:*\n\n"
    msg += "\n".join([f"• {nome}" for nome in facebook_prontos])
    msg += f"\n\n🎁 Promoção: Compre 7 e leve a 8ª grátis!\n🛒 Clique em uma conta para ver os dados e confirmar a compra.\n\n📊 Você já comprou {total} Facebook(s)."
    bot.send_message(m.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirmar_recarga_"))
def confirmar_recarga(call):
    user_id = int(call.data.split("_")[-1])
    valor = recargas_pendentes.get(user_id)
    if valor:
        saldos[user_id] = saldos.get(user_id, 0) + valor

        # Cria o botão "Start 🔄"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Start 🔄')

        # Envia para o usuário
        bot.send_message(
            user_id,
            f"✅ Recarga de R${valor:.2f} confirmada!\n\nClique no botão abaixo para acessar o menu principal:",
            reply_markup=markup
        )

        # Notifica o ADM
        bot.send_message(ADMIN_ID, f"✅ Saldo liberado para ID {user_id}.")
        del recargas_pendentes[user_id]
    else:
        bot.send_message(call.message.chat.id, "⚠️ Recarga já foi confirmada ou não existe.")
@bot.callback_query_handler(func=lambda call: call.data.startswith("comprar_"))
def realizar_compra(call):
    user_id = call.from_user.id
    nome_conta = call.data.replace("comprar_", "")
    if saldos.get(user_id, 0) < 20:
        bot.answer_callback_query(call.id, "❌ Saldo insuficiente. Recarga mínima: R$20.")
        bot.send_message(call.message.chat.id, "💳 Faça uma recarga. Valor mínimo: *R$20*", parse_mode="Markdown")
        return

    saldos[user_id] -= 20
    dados = facebook_prontos.pop(nome_conta)
    compras[user_id] += 1

    # Envia pro usuário
    bot.send_message(call.message.chat.id, f"✅ Compra realizada!\n\n🔐 Login: `{dados['login']}`\n🔑 Senha: `{dados['senha']}`", parse_mode="Markdown")

    # ✅ Notifica o ADM
    bot.send_message(ADMIN_ID,
        f"📦 Nova compra de Facebook pronto!\n\n👤 Usuário: {call.from_user.first_name} (ID: {user_id})\n📘 Conta: {nome_conta}\n🔐 Login: `{dados['login']}`\n🔑 Senha: `{dados['senha']}`",
        parse_mode="Markdown")

    # Promoção da 8ª conta grátis
    if compras[user_id] == 7:
        bot.send_message(user_id, "🎁 Você ganhou um Facebook pronto GRÁTIS!")
        bot.send_message(ADMIN_ID, f"🎉 {call.from_user.first_name} completou 7 compras e ganhou uma conta grátis!")

@bot.message_handler(func=lambda m: m.text == 'Saldo / Recarga')
def menu_recarga(m):
    markup = types.InlineKeyboardMarkup()
    for valor in [20, 30, 40, 50, 75, 100]:
        markup.add(types.InlineKeyboardButton(f"R${valor}", callback_data=f"valor_{valor}"))
    bot.send_message(m.chat.id, "💸 Escolha o valor da recarga (mínimo R$20):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("valor_"))
def solicitar_dados_pagador(call):
    valor = call.data.split("_")[1]
    bot.send_message(call.message.chat.id,
        f"📝 Preencha com o *Nome do pagador Pix* e *Banco* para facilitar o reconhecimento e liberação de saldo.\n\n📌 Exemplo:\nJoão Marcos\nBanco do Brasil",
        parse_mode="Markdown")
    bot.register_next_step_handler(call.message, lambda m: processar_dados_pagador(m, valor))

def processar_dados_pagador(m, valor):
    linhas = m.text.split("\n")
    if len(linhas) != 2 or len(linhas[0]) < 4 or len(linhas[1]) < 3:
        bot.send_message(m.chat.id, "❌ Dados inválidos. Digite o nome + banco corretamente (em linhas separadas).")
        return menu_recarga(m)

    nome, banco = linhas
    try:
        with open("qrcode_universal.png", "rb") as qr:
            bot.send_photo(m.chat.id, qr, caption=f"💳 Pague R${valor} com o QR Code acima.")
    except:
        bot.send_message(m.chat.id, "⚠️ QR Code não encontrado.")

    pix_code = "00020101021126400014br.gov.bcb.pix0118ntvasbot@gmail.com5204000053039865802BR5925ANDREIA BENEDITA ALMEIDA 6013VARZEA GRANDE610878152100622905254702432f713e44ba82520b8e96304C000"
    bot.send_message(m.chat.id, f"📎 Copia e Cola:\n`{pix_code}`", parse_mode="Markdown")

    user_id = m.from_user.id
    recargas_pendentes[user_id] = float(valor)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Confirmar Recarga", callback_data=f"confirmar_recarga_{user_id}"))
    bot.send_message(ADMIN_ID,
        f"🧾 Nova recarga aguardando confirmação:\n👤 Nome: {nome}\n🏦 Banco: {banco}\n💰 Valor: R${valor}\n🆔 ID: {user_id}",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirmar_recarga_"))
def confirmar_recarga(call):
    user_id = int(call.data.split("_")[-1])
    valor = recargas_pendentes.get(user_id)
    if valor:
        saldos[user_id] = saldos.get(user_id, 0) + valor
        bot.send_message(user_id, f"✅ Recarga de R${valor:.2f} confirmada! Saldo atualizado.")
        bot.send_message(ADMIN_ID, f"✅ Saldo liberado para ID {user_id}.")
        del recargas_pendentes[user_id]
    else:
        bot.send_message(call.message.chat.id, "⚠️ Recarga já foi confirmada ou não existe.")
@bot.message_handler(func=lambda m: m.text == 'Comprar Número')
def escolher_app(m):
    markup = types.InlineKeyboardMarkup()
    for app in apps_disponiveis:
        markup.add(types.InlineKeyboardButton(app, callback_data=f"app_{app.lower()}"))
    markup.add(types.InlineKeyboardButton("Voltar 🔙", callback_data="voltar_menu"))
    bot.send_message(m.chat.id, "📲 Para qual app você quer o número?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("app_"))
def escolher_operadora(call):
    app = call.data.split("_")[1]
    markup = types.InlineKeyboardMarkup()
    for op in ['vivo', 'claro', 'tim', 'oi']:
        preco = operadoras_fixas['facebook'][op] if app == "facebook" else 2.00
        markup.add(types.InlineKeyboardButton(f"{op.capitalize()} (R${preco:.2f})", callback_data=f"gerar_{app}_{op}_{preco}"))
    markup.add(types.InlineKeyboardButton("Voltar 🔙", callback_data="voltar_menu"))
    bot.send_message(call.message.chat.id, "📡 Escolha a operadora:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("gerar_"))
def gerar_numero_handler(call):
    user_id = call.from_user.id
    _, app, operadora, preco = call.data.split("_")
    preco = float(preco)

    if saldos.get(user_id, 0) < preco:
        bot.send_message(call.message.chat.id, "❌ Saldo insuficiente. Recarga mínima R$20.")
        return

    if user_id in bloqueios and time.time() < bloqueios[user_id]:
        restante = int((bloqueios[user_id] - time.time()) // 60)
        bot.send_message(call.message.chat.id, f"🚫 Limite de uso atingido.\n⏳ Tente novamente em {restante} minutos.")
        return

    geracoes[user_id] = geracoes.get(user_id, 0) + 1
    if geracoes[user_id] >= 14:
        bloqueios[user_id] = time.time() + (15 * 60)
        geracoes[user_id] = 0
        bot.send_message(call.message.chat.id, "🚫 Limite atingido. Aguarde 15 minutos para gerar mais números.")
        return

    ultima_requisicao[user_id] = {'app': app, 'operadora': operadora, 'preco': preco}
    numero = gerar_numero(user_id, app, operadora)
    if numero:
        saldos[user_id] -= preco
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Cancelar Número", callback_data="cancelar_numero"))
        markup.add(types.InlineKeyboardButton("Voltar 🔙", callback_data="voltar_menu"))
        bot.send_message(call.message.chat.id, f"📱 Número gerado para *{app.capitalize()}* via *{operadora.capitalize()}*:\n`{numero}`\n\n⏳ Aguarde o código de verificação...", parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "❌ Não foi possível gerar número no momento.")

@bot.callback_query_handler(func=lambda call: call.data == "voltar_menu")
def voltar_menu(call):
    m = call.message
    m.from_user = call.from_user
    menu_principal(m)

@bot.callback_query_handler(func=lambda call: call.data == "cancelar_numero")
def cancelar_numero(call):
    user_id = call.from_user.id
    preco = ultima_requisicao.get(user_id, {}).get('preco', 1.20)
    saldos[user_id] += preco
    bot.send_message(call.message.chat.id, "❌ Número cancelado com sucesso. Saldo devolvido.")
    menu_principal(call.message)

def gerar_numero(user_id, app, operadora):
    try:
        # SMS-Activate
        r = requests.get(f"https://api.sms-activate.org/stubs/handler_api.php?api_key={SMS_ACTIVATE_API}&action=getNumber&service=fb&country=73")
        if "ACCESS_NUMBER" in r.text:
            id_ativ, numero = r.text.split(":")[1:3]
            threading.Thread(target=aguardar_sms_activate, args=(user_id, id_ativ)).start()
            return numero
    except:
        pass
    try:
        # 5SIM
        headers = {"Authorization": f"Bearer {SIM5_API_KEY}"}
        r = requests.get("https://5sim.net/v1/user/buy/activation/any/brazil/facebook", headers=headers)
        data = r.json()
        numero = data["phone"]
        id_5sim = data["id"]
        threading.Thread(target=aguardar_sms_5sim, args=(user_id, id_5sim)).start()
        return numero
    except:
        return None

def aguardar_sms_activate(user_id, ativ_id):
    for _ in range(72):
        time.sleep(10)
        r = requests.get(f"https://api.sms-activate.org/stubs/handler_api.php?api_key={SMS_ACTIVATE_API}&action=getStatus&id={ativ_id}")
        if "STATUS_OK" in r.text:
            codigo = r.text.split(":")[1]
            bot.send_message(user_id, f"✅ Código recebido: `{codigo}`", parse_mode="Markdown")
            return
    requests.get(f"https://api.sms-activate.org/stubs/handler_api.php?api_key={SMS_ACTIVATE_API}&action=setStatus&status=8&id={ativ_id}")
    bot.send_message(user_id, "⏰ Tempo esgotado. Nenhum código recebido. Saldo devolvido.")
    saldos[user_id] += 1.20

def aguardar_sms_5sim(user_id, ativ_id):
    headers = {"Authorization": f"Bearer {SIM5_API_KEY}"}
    for _ in range(72):
        time.sleep(10)
        r = requests.get(f"https://5sim.net/v1/user/check/{ativ_id}", headers=headers)
        sms = r.json().get("sms", [])
        if sms:
            codigo = sms[0]['code']
            bot.send_message(user_id, f"✅ Código recebido: `{codigo}`", parse_mode="Markdown")
            return
    requests.post(f"https://5sim.net/v1/user/cancel/{ativ_id}", headers=headers)
    bot.send_message(user_id, "⏰ Tempo esgotado. Nenhum código recebido. Saldo devolvido.")
    saldos[user_id] += 1.20

def agendar_mensagens():
    def bom_dia():
        for uid in usuarios:
            nome = usuarios[uid].get('nome', 'amigo')
            try:
                bot.send_message(uid, f"☀️ Bom dia {nome}! Vamos pra mais um dia de batalha com Deus! 🙏")
            except: continue
    def boa_tarde():
        for uid in usuarios:
            nome = usuarios[uid].get('nome', 'amigo')
            try:
                bot.send_message(uid, f"🌤️ Boa tarde {nome}! Continue focado, sua vitória vem! 💪")
            except: continue
    def boa_noite():
        for uid in usuarios:
            nome = usuarios[uid].get('nome', 'amigo')
            try:
                bot.send_message(uid, f"🌙 Boa noite {nome}! Descanse bem, amanhã é um novo dia! ✨")
            except: continue

    schedule.every().day.at("07:00").do(bom_dia)
    schedule.every().day.at("14:00").do(boa_tarde)
    schedule.every().day.at("20:00").do(boa_noite)
    while True:
        schedule.run_pending()
        time.sleep(30)

# Iniciar agendamentos
threading.Thread(target=agendar_mensagens).start()

# Avisar o ADM
bot.send_message(ADMIN_ID, "✅ BOT INICIADO COM SUCESSO!")
print("Bot rodando no Termux...")

# Iniciar polling
bot.polling()
