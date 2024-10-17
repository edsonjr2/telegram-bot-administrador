from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from collections import defaultdict
import logging
import time
import random

TOKEN = 'YOUR_TOKEN'

# Configuração de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Estruturas de dados
banned_users = set()
warnings = defaultdict(list)
filtered_words = {'palavra1', 'palavra2'}
log_messages = []
rules = "Regras do grupo: 1. Respeitar todos. 2. Sem ofensas. 3. Sem spam."
welcome_message = "Bem-vindo ao grupo! Leia as regras e divirta-se!"
feedbacks = []
links_uteis = []
anuncios = []
scheduled_messages = []

# Funções do Bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Olá! Eu sou o seu bot administrador.')

def warn(update: Update, context: CallbackContext) -> None:
    if is_admin(update, context):
        if context.args:
            user_id = int(context.args[0])
            message = ' '.join(context.args[1:])
            warnings[user_id].append(message)
            update.message.reply_text(f'Usuário {user_id} recebeu um aviso: {message}')
        else:
            update.message.reply_text('Por favor, forneça o ID do usuário e a mensagem do aviso.')

def ban(update: Update, context: CallbackContext) -> None:
    if is_admin(update, context):
        if context.args:
            user_id = int(context.args[0])
            context.bot.kick_chat_member(update.message.chat.id, user_id)
            banned_users.add(user_id)
            update.message.reply_text(f'Usuário {user_id} banido.')

def unban(update: Update, context: CallbackContext) -> None:
    if is_admin(update, context):
        if context.args:
            user_id = int(context.args[0])
            context.bot.unban_chat_member(update.message.chat.id, user_id)
            banned_users.discard(user_id)
            update.message.reply_text(f'Usuário {user_id} desbanido.')

def banned_list(update: Update, context: CallbackContext) -> None:
    if banned_users:
        update.message.reply_text('Usuários banidos: ' + ', '.join(map(str, banned_users)))
    else:
        update.message.reply_text('Nenhum usuário banido.')

def feedback(update: Update, context: CallbackContext) -> None:
    feedback_message = ' '.join(context.args)
    feedbacks.append(feedback_message)
    update.message.reply_text('Obrigado pelo seu feedback!')

def regras(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(rules)

def boas_vindas(update: Update, context: CallbackContext) -> None:
    if update.message.new_chat_members:
        for member in update.message.new_chat_members:
            context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)

def ajuda(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Comandos disponíveis:\n/start - Iniciar\n/warn user_id mensagem - Avisar usuário\n/ban user_id - Banir usuário\n/unban user_id - Desbanir usuário\n/banned - Listar banidos\n/feedback mensagem - Enviar feedback\n/regras - Exibir regras do grupo\n/ajuda - Mostrar esta mensagem.\n/log mensagem - Registrar mensagem.\n/filtered_words - Listar palavras filtradas.\n/poll pergunta opção1 opção2 - Criar uma enquete.\n/info - Informações do grupo.\n/mute user_id tempo - Silenciar usuário.\n/promote user_id - Promover usuário.\n/demote user_id - Remover admin.\n/lembrete mensagem tempo - Definir lembrete.\n/anuncio mensagem - Fazer um anúncio.\n/links adicionar link - Adicionar um link útil.\n/sorteio - Realizar um sorteio.\n/banir_temporariamente user_id tempo - Banir temporariamente um usuário.')

def log(update: Update, context: CallbackContext) -> None:
    if is_admin(update, context):
        message = ' '.join(context.args)
        log_messages.append(message)
        update.message.reply_text(f'Mensagem registrada: {message}')

def filtered_words_list(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Palavras filtradas: ' + ', '.join(filtered_words))

def poll(update: Update, context: CallbackContext) -> None:
    if is_admin(update, context):
        if len(context.args) < 3:
            update.message.reply_text('Uso: /poll pergunta opção1 opção2')
            return
        question = ' '.join(context.args[:-2])
        options = context.args[-2:]
        update.message.reply_poll(question, options)

def info(update: Update, context: CallbackContext) -> None:
    chat = update.message.chat
    info_message = f'Nome do grupo: {chat.title}\nNúmero de membros: {chat.get_members_count()}'
    update.message.reply_text(info_message)

def mute(update: Update, context: CallbackContext) -> None:
    if is_admin(update, context):
        if len(context.args) < 2:
            update.message.reply_text('Uso: /mute user_id tempo')
            return
        user_id = int(context.args[0])
        time_limit = int(context.args[1])
        context.bot.restrict_chat_member(update.message.chat.id, user_id, until_date=time.time() + time_limit)
        update.message.reply_text(f'Usuário {user_id} silenciado por {time_limit} segundos.')

def promote(update: Update, context: CallbackContext) -> None:
    if is_admin(update, context):
        if context.args:
            user_id = int(context.args[0])
            context.bot.promote_chat_member(update.message.chat.id, user_id)
            update.message.reply_text(f'Usuário {user_id} promovido a administrador.')

def demote(update: Update, context: CallbackContext) -> None:
    if is_admin(update, context):
        if context.args:
            user_id = int(context.args[0])
            context.bot.promote_chat_member(update.message.chat.id, user_id, can_change_info=False, can_post_messages=False, can_edit_messages=False, can_delete_messages=False, can_invite_to_chat=False, can_restrict_members=False, can_pin_messages=False, can_promote_members=False)
            update.message.reply_text(f'Usuário {user_id} removido de administrador.')

def lembrete(update: Update, context: CallbackContext) -> None:
    if context.args and len(context.args) >= 2:
        message = ' '.join(context.args[:-1])
        time_delay = int(context.args[-1])
        update.message.reply_text(f'Lembrete definido para "{message}" em {time_delay} segundos.')
        time.sleep(time_delay)
        update.message.reply_text(f'Lembrete: {message}')
    else:
        update.message.reply_text('Uso: /lembrete mensagem tempo')

def anuncio(update: Update, context: CallbackContext) -> None:
    if is_admin(update, context):
        if context.args:
            message = ' '.join(context.args)
            anuncios.append(message)
            update.message.reply_text(f'Anúncio feito: {message}')
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'🚨 Anúncio: {message}')

def adicionar_link(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 1:
        update.message.reply_text('Uso: /links adicionar link')
        return
    link = ' '.join(context.args[1:])
    links_uteis.append(link)
    update.message.reply_text(f'Link adicionado: {link}')

def sorteio(update: Update, context: CallbackContext) -> None:
    if context.args:
        participants = context.args
        winner = random.choice(participants)
        update.message.reply_text(f'O vencedor do sorteio é: {winner}')
    else:
        update.message.reply_text('Uso: /sorteio usuário1 usuário2 ...')

def banir_temporariamente(update: Update, context: CallbackContext) -> None:
    if is_admin(update, context):
        if len(context.args) < 2:
            update.message.reply_text('Uso: /banir_temporariamente user_id tempo')
            return
        user_id = int(context.args[0])
        time_limit = int(context.args[1])
        context.bot.kick_chat_member(update.message.chat.id, user_id)
        banned_users.add(user_id)
        update.message.reply_text(f'Usuário {user_id} banido temporariamente por {time_limit} segundos.')
        time.sleep(time_limit)
        context.bot.unban_chat_member(update.message.chat.id, user_id)
        banned_users.discard(user_id)

def is_admin(update: Update, context: CallbackContext) -> bool:
    admins = context.bot.get_chat_administrators(update.message.chat.id)
    return update.message.from_user.id in [admin.user.id for admin in admins]

def main() -> None:
    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('warn', warn))
    updater.dispatcher.add_handler(CommandHandler('ban', ban))
    updater.dispatcher.add_handler(CommandHandler('unban', unban))
    updater.dispatcher.add_handler(CommandHandler('banned', banned_list))
    updater.dispatcher.add_handler(CommandHandler('feedback', feedback))
    updater.dispatcher.add_handler(CommandHandler('regras', regras))
    updater.dispatcher.add_handler(CommandHandler('ajuda', ajuda))
    updater.dispatcher.add_handler(CommandHandler('log', log))
    updater.dispatcher.add_handler(CommandHandler('filtered_words', filtered_words_list))
    updater.dispatcher.add_handler(CommandHandler('poll', poll))
    updater.dispatcher.add_handler(CommandHandler('info', info))
    updater.dispatcher.add_handler(CommandHandler('mute', mute))
    updater.dispatcher.add_handler(CommandHandler('promote', promote))
    updater.dispatcher.add_handler(CommandHandler('demote', demote))
    updater.dispatcher.add_handler(CommandHandler('lembrete', lembrete))
    updater.dispatcher.add_handler(CommandHandler('anuncio', anuncio))
    updater.dispatcher.add_handler(CommandHandler('links', adicionar_link))
    updater.dispatcher.add_handler(CommandHandler('sorteio', sorteio))
    updater.dispatcher.add_handler(CommandHandler('banir_temporariamente', banir_temporariamente))
    updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, boas_vindas))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
