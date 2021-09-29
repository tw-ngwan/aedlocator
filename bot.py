from dotenv import load_dotenv
from telegram import replykeyboardmarkup
load_dotenv()


from locations import locations
from maps import campMaps, badURL
from buttons import campButtons
import telegram


from time import sleep
import os
import geopy.distance
from telegram import Location, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import MessageFilter, MessageHandler, ConversationHandler, Filters, CommandHandler, Updater, RegexHandler
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# The API Key we received for our bot
API_KEY = os.environ.get('TOKEN')
PORT = int(os.environ.get('PORT', 8443))

GENDER, PHOTO, LOCATION, BIO = range(4)
 
 
def start(bot, update):
    reply_keyboard = [['Boy', 'Girl', 'Other']]
 
    bot.message.reply_text(
        'Hi! My name is Professor Bot. I will hold a conversation with you. '
        'Send /cancel to stop talking to me.\n\n'
        'Are you a boy or a girl?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
 
    return GENDER
 
 
def gender(bot, update):
    user = bot.message.from_user
    logger.info("Gender of %s: %s" % (user.first_name, bot.message.text))
    bot.message.reply_text('I see! Please send me a photo of yourself, '
                              'so I know what you look like, or send /skip if you don\'t want to.')
 
    return PHOTO
 
 
def photo(bot, update):
    user = update.message.from_user
    photo_file = bot.getFile(update.message.photo[-1].file_id)
    photo_file.download('user_photo.jpg')
    logger.info("Photo of %s: %s" % (user.first_name, 'user_photo.jpg'))
    update.message.reply_text('Gorgeous! Now, send me your location please, '
                              'or send /skip if you don\'t want to.')
 
    return LOCATION
 
 
def skip_photo(bot, update):
    user = bot.message.from_user
    logger.info("User %s did not send a photo." % user.first_name)
    kb = [[KeyboardButton(text = "send location", request_location=True)] ]
    bot.message.reply_text('I bet you look great! Now, send me your location please, '
                              'or send /skip.', reply_markup = kb)
 
    return LOCATION
 
 
def location(bot, update):
    user = bot.message.from_user
    user_location = bot.message.location
    logger.info("Location of %s: %f / %f"
                % (user.first_name, user_location.latitude, user_location.longitude))
    update.message.reply_text('Maybe I can visit you sometime! '
                              'At last, tell me something about yourself.')
 
    return BIO
 
 
def skip_location(bot, update):
    user = update.message.from_user
    logger.info("User %s did not send a location." % user.first_name)
    update.message.reply_text('You seem a bit paranoid! '
                              'At last, tell me something about yourself.')
 
    return BIO
 
 
def bio(bot, update):
    user = update.message.from_user
    logger.info("Bio of %s: %s" % (user.first_name, update.message.text))
    update.message.reply_text('Thank you! I hope we can talk again some day.')
 
    return ConversationHandler.END
 
 
def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation." % user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.')
 
    return ConversationHandler.END
 
 
def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))
 
 
def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(API_KEY)
 
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
 
    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
 
        states={
            GENDER: [RegexHandler('^(Boy|Girl|Other)$', gender)],
 
            PHOTO: [MessageHandler(Filters.photo, photo),
                    CommandHandler('skip', skip_photo)],
 
            LOCATION: [MessageHandler(Filters.location, location),
                       CommandHandler('skip', skip_location)],
 
            BIO: [MessageHandler(Filters.text, bio)]
        },
 
        fallbacks=[CommandHandler('cancel', cancel)]
    )
 
    dp.add_handler(conv_handler)
 
    # log all errors
    dp.add_error_handler(error)
    # add handlers
    updater.start_webhook(listen="0.0.0.0",
                        port=PORT,
                        url_path=API_KEY,
                        webhook_url="https://polar-chamber-36116.herokuapp.com/" + API_KEY)
    updater.idle()


if __name__ == '__main__':
    main()