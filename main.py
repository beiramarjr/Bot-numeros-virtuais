import telebot
import requests
import json
import time
import threading
import schedule
from telebot import types
from datetime import datetime
from flask import Flask

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
    markup.add('Seu Saldo', 'Start 🔄')
    msg = "✅ Bot ativo! Use os botões abaixo."
    bot.send_message(m.chat.id, msg, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Seu Saldo')
def ver_saldo(m):
    saldo = saldos.get(m.from_user.id, 0)
    bot.send_message(m.chat.id, f"💰 Seu saldo é R${saldo:.2f}")

# Função para manter o bot ativo com Flask (Render exige isso)
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot está online!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Iniciar bot e Flask juntos
def start_bot():
    bot.infinity_polling()

# Iniciar ambos em paralelo
threading.Thread(target=start_bot).start()
threading.Thread(target=run_flask).start()
