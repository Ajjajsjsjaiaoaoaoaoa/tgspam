import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configurar logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Token del bot (usa variable de entorno en Render)
TOKEN = os.getenv("8310011197:AAF0WQnYAAvP3IVF5MO_sqYpmoO9WIE55p0")  # En Render, configura esto en env vars

# Lista de administradores verificados
ADMINISTRADORES_VERIFICADOS = {
    7296719664: "@admin_ejemplo"
}

# Diccionario para tratos
tratos = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensaje_bienvenida = "¡Hola! Soy el bot de tratos seguros.\nUsa /menu para ver los administradores disponibles y comenzar un trato."
    await update.message.reply_text(mensaje_bienvenida)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = []
    for admin_id, admin_username in ADMINISTRADORES_VERIFICADOS.items():
        keyboard.append([InlineKeyboardButton(admin_username, callback_data=str(admin_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Elige un administrador para tu trato:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    admin_id = int(query.data)
    usuario_a_id = query.from_user.id

    if usuario_a_id in tratos:
        await query.edit_message_text(text="Ya tienes un trato pendiente. Debes finalizarlo antes de iniciar otro.")
        return

    try:
        usuario_a = await context.bot.get_chat(chat_id=usuario_a_id)
        admin_username = ADMINISTRADORES_VERIFICADOS[admin_id]
        nombre_grupo = f'Trato seguro entre @{usuario_a.username or "Usuario"} y {admin_username}'
    except Exception as e:
        await query.edit_message_text(text=f"Error al obtener información del usuario: {e}")
        return

    try:
        grupo = await context.bot.create_supergroup_chat(title=nombre_grupo)
        grupo_id = grupo.id
    except Exception as e:
        await query.edit_message_text(text=f"No se pudo crear el supergroup: {e}")
        return

    try:
        await context.bot.add_chat_member(chat_id=grupo_id, user_id=usuario_a_id)
        await context.bot.add_chat_member(chat_id=grupo_id, user_id=admin_id)
    except Exception as e:
        await query.edit_message_text(text=f"No se pudo agregar a los usuarios al supergroup: {e}")
        try:
            await context.bot.delete_chat(chat_id=grupo_id)
        except:
            pass
        return

    tratos[usuario_a_id] = {'grupo_id': grupo_id}

    mensaje_confirmacion = f"Se ha creado el supergroup {nombre_grupo}.\nEste supergroup se eliminará automáticamente en 24 horas."
    await query.edit_message_text(text=mensaje_confirmacion)

    context.job_queue.run_once(enviar_aviso_eliminacion, 79200, data={'chat_id': grupo_id})
    context.job_queue.run_once(eliminar_grupo, 82800, data={'chat_id': grupo_id})

async def enviar_aviso_eliminacion(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data['chat_id']
    try:
        await context.bot.send_message(chat_id=chat_id, text="Aviso: Este supergroup se eliminará automáticamente en 1 hora.")
    except Exception as e:
        logging.error(f"No se pudo enviar el aviso: {e}")

async def eliminar_grupo(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data['chat_id']
    try:
        await context.bot.delete_chat(chat_id=chat_id)
        logging.info(f'Supergroup {chat_id} eliminado.')
    except Exception as e:
        logging.error(f'No se pudo eliminar el supergroup {chat_id}: {e}')
    
    for usuario_id, trato in list(tratos.items()):
        if trato['grupo_id'] == chat_id:
            del tratos[usuario_id]
            break

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()