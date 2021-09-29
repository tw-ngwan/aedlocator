from dotenv import load_dotenv
load_dotenv()


from locations import locations
from maps import campMaps, badURL
from buttons import campButtons
import telegram


from time import sleep
import os
import geopy.distance
from telegram import Location, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import MessageFilter, MessageHandler, ConversationHandler, Filters, CommandHandler, Updater
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# The API Key we received for our bot
API_KEY = os.environ.get('TOKEN')
PORT = int(os.environ.get('PORT', 8443))

# Create an updater object with our API Key
updater = Updater(API_KEY)
# Retrieve the dispatcher, which will be used to add handlers
dispatcher = updater.dispatcher
# Our states, as integers

STATECHECKER, CURRLOCATION, IMAGESTEP, RETURNIMAGE, CANCEL, END = range(6)

####################################################################################
#Global Variables
aedDict = {}


class AED:
    def __init__(self, location): #initialized with the coordinates of a location
        self.latitude = location.latitude
        self.longitude = location.longitude
        self.aeds = {}


####################################################################################
       


def start(update_obj, context):
    """Send a message when the command /start is issued."""


    buttons = [[KeyboardButton(text='Nearest AED',request_location=True)],\
        [KeyboardButton(text='Static Map')],[KeyboardButton(text='Restart')]]

    kb = ReplyKeyboardMarkup(keyboard=buttons,resize_keyboard = True, one_time_keyboard = True)

    welcomeString = """
    Hello, would you like to see your nearest AED or a static map?
If you click Nearest AED, the bot will request your location!
Click the RESTART button at any time to restart the commands!!
    """

    update_obj.message.reply_text(welcomeString,reply_markup=kb)
    return STATECHECKER
    
def state_checker(update_obj, context):
    print("SC func")
    return ConversationHandler.END




def cancel(update_obj, context):
    # get the user's first name
    first_name = update_obj.message.from_user['first_name']
    update_obj.message.reply_text(
        f"Update is {update_obj}!", reply_markup=telegram.ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def end(update_obj, context):
    # get the user's first name
    first_name = update_obj.message.from_user['first_name']
    update_obj.message.reply_text(
        f"Thank you {first_name}, have a wonderful day. Press /start to restart the bot!", reply_markup=telegram.ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():



    handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
                STATECHECKER: [MessageHandler(Filters.text('Nearest AED' or 'Static Map') or Filters.location  , state_checker)],
                CANCEL: [MessageHandler(Filters.text, cancel)],
                END: [MessageHandler(Filters.text, end)]

        },
        fallbacks=[CommandHandler('end', end)],
        )
    # add the handler to the dispatcher
    dispatcher.add_handler(handler)
    # add handlers
    updater.start_webhook(listen="0.0.0.0",
                        port=PORT,
                        url_path=API_KEY,
                        webhook_url="https://polar-chamber-36116.herokuapp.com/" + API_KEY)
    updater.idle()


if __name__ == '__main__':
    main()