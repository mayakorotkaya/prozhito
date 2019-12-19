from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

import config
from prozhito_tools import dump
dw = dump.Wrapper(csvpath=config.dumppath)

import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY = range(2)

user_subscriptions = {}

MAXLENGTH = 4096

def start(update, context):
    reply_keyboard = [['Выбрать по автору'], ['Выбрать по периоду'], ['Помочь нам']]
    context.bot.send_message(chat_id=update.effective_message.chat_id, text="Привет, я чат-бот сайта Прожито. "
                                                                                "Сайт посвящен дневниковым записям 18-20 веков."
                                                                                "Какие дневники вы бы хотели почитать? "
                                                                            "Нажми /cancel, чтобы я перестал тебе писать.",
                             reply_markup = ReplyKeyboardMarkup(reply_keyboard, True))
    return CHOOSING

def author(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(
        'Вы решили посмотреть дневники по автору. Введите имя автора в формате ИОФ')

    return AUTHOR_REPLY

def interval(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(
        'Вы решили посмотреть дневники по периоду. Введите период в формате чч.мм.гг - чч.мм.гг.')

    return INTERVAL_REPLY

def help(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(
        'Большинство дневников сайта Прожито не имеют семантической разметки. Вы могли бы помочь нам, присвоив тег одному из дневников.')

    return CHOOSING_REPLY

def received_information(update, context):
    text = update.message.text

    update.message.reply_text("{}".format(text))
    return CHOOSING

def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Пока! Надеюсь ты поговоришь со мной совсем скоро!',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

def interval1(update, context):
    text = update.message.text
    textnumb = ''.join(text)
    first_date = textnumb.split(' - ')[0].split('.')
    year1 = int(first_date[2])
    month1 = int(first_date[1])
    day1 = int(first_date[0])

    second_date = textnumb.split(' - ')[1].split('.')
    year2 = int(second_date[2])
    month2 = int(second_date[1])
    day2 = int(second_date[0])

    notes_for_period = dw.notes[(year1, month1, day1): (year2, month2, day2)]
    for note in notes_for_period:
        if len(note.text) > MAXLENGTH:
            for x in range(0, len(note.text), MAXLENGTH):
                context.bot.send_message(chat_id=update.effective_message.chat_id,
                                         text='{0}'.format(note.text[x:x + MAXLENGTH]))
        else:
            context.bot.send_message(chat_id=update.effective_message.chat_id,
                                     text='{0}'.format(note.text))
    return CHOOSING

def author1(update, context):
    author_name = update.message.text
    matched_authors = filter(lambda a: author_name in a.name, dw.authors.authors_list)
    try:
        author = next(matched_authors)
    except StopIteration:
        update.message.reply_text("Увы, мы не нашли такого автора :(")
        return CHOOSING
    for note in author.notes[:5]:
        if len(note.text) > MAXLENGTH:
            for x in range(0, len(note.text), MAXLENGTH):
                context.bot.send_message(chat_id=update.effective_message.chat_id,
                                         text='{0}'.format(note.text[x:x + MAXLENGTH]))
        else:
            context.bot.send_message(chat_id=update.effective_message.chat_id,
                                     text='{0}'.format(note.text))
    return CHOOSING

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    from telegram import Bot
    from telegram.utils.request import Request
    req = Request(proxy_url=config.proxy)
    bot = Bot(config.token, request=req)
    upd = Updater(bot=bot, use_context=True)

    dp = upd.dispatcher

    #user_subscriptions = {} #добавлять сюда chat_id, если пользователь подписывается, и подписку; создали выше
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [MessageHandler(Filters.regex('^Выбрать по автору$'),
                                      author),
                       MessageHandler(Filters.regex('^Выбрать по периоду$'), #дальше варианты выдачи (1 или 10 или файлом или регулярная подписка; Если подписка то выбрать частотность)
                                      interval),
                       MessageHandler(Filters.regex('^Помочь нам$'), #потом опять - по периоду или по автору, под сообщением кнопка добавить тэг персона, по геотэгу или по смыслу, дальше свободное текстовое поле (после этого добавить еще или следюущая запись) -
                                      help)
                       ],
            INTERVAL_REPLY: [MessageHandler(Filters.regex(r'\d\d?\.\d\d?\.\d\d\d\d - \d\d?\.\d\d?\.\d\d\d\d'),
                                            interval1)],

            AUTHOR_REPLY:  [MessageHandler(Filters.regex('[А-Яа-я]*'), author1)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    upd.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    upd.idle()


if __name__ == '__main__':
    main()

