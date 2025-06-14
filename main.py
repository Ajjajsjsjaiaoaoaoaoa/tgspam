from telethon.sync import TelegramClient, events
import asyncio
import datetime
from flask import Flask
from threading import Thread
import os

# CONFIGURACIÓN
api_id = 23720875  # tu API ID
api_hash = 'a52aa051d3e737afb9e21fe6b80cc765'  # tu API HASH
session_name = 'mi_session'  # el archivo .session (debe estar en tu repo)
ARCHIVO_GRUPOS = 'grupos.txt'
grupo_logs = '@logsdelbotspammm'
inicio = datetime.datetime.now()

client = TelegramClient(session_name, api_id, api_hash)

def cargar_grupos():
    with open(ARCHIVO_GRUPOS, 'r') as f:
        return [line.strip() for line in f if line.strip()]

@client.on(events.NewMessage(from_users='me', pattern='/estado'))
async def estado(event):
    grupos = cargar_grupos()
    await event.reply(f"📦 {len(grupos)} grupos en grupos.txt\n🤖 Bot activo y esperando órdenes.")

@client.on(events.NewMessage(from_users='me', pattern='/spam'))
async def activar_spam(event):
    async for msg in client.iter_messages('me', limit=5):
        if msg.fwd_from:
            mensaje_origen = msg
            break
    else:
        await event.reply("⚠️ No encontré mensaje reenviado tuyo.")
        return

    grupos = cargar_grupos()
    if not grupos:
        await event.reply("⚠️ No hay grupos en grupos.txt.")
        return

    enviados_ok, enviados_fail = [], []
    await event.reply(f"🚀 Enviando mensaje a {len(grupos)} grupos...")

    for grupo in grupos:
        try:
            await client.send_message(grupo, mensaje_origen)
            enviados_ok.append(grupo)
            await asyncio.sleep(0.5)
        except Exception as e:
            enviados_fail.append(f"{grupo} → {str(e)}")

    log_text = f"✅ Enviados: {len(enviados_ok)}\n❌ Fallos: {len(enviados_fail)}"
    await event.reply(log_text)

    try:
        await client.send_message(grupo_logs, log_text)
    except Exception as e:
        print("No se pudo enviar log:", e)

@client.on(events.NewMessage(from_users='me', pattern='/comandos'))
async def mostrar_comandos(event):
    await event.reply(
        "📜 *Comandos disponibles:*\n\n"
        "🔹 /spam → Reenvía el último mensaje reenviado a todos los grupos\n"
        "🔹 /estado → Verifica si el bot está activo\n"
        "🔹 /comandos → Muestra este menú",
        parse_mode='Markdown'
    )

# 🌐 FLASK para Render
app = Flask('')

@app.route('/')
def home():
    return "✅ El bot está activo."

def iniciar_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def iniciar_telegram():
    with client:
        client.loop.run_until_complete(client.send_message('me', "🤖 Bot iniciado correctamente."))
        client.run_until_disconnected()

# 🚀 ARRANQUE
if __name__ == '__main__':
    Thread(target=iniciar_web).start()
    Thread(target=iniciar_telegram).start()
