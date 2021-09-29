import telegram
import telebot
import telegram.ext
import re
from random import randint
import os
from buttons import unitbuttons, battalionButtons,companyButtons

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import gspread_dataframe
import pytz
import datetime as dt


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# The API Key we received for our bot
TOKEN = os.environ.get('TOKEN')
PORT = int(os.environ.get('PORT', 8443))

# Create an updater object with our API Key
updater = telegram.ext.Updater(TOKEN)
# Retrieve the dispatcher, which will be used to add handlers
dispatcher = updater.dispatcher
# Our states, as integers

BATSTEP, COYSTEP, WPNSTEP,BUTTSTEP, DEFECTSTEP, DEFECTIDSTEP, RMKCHKSTEP, YESORNO, RMKSTEP, END, CANCEL = range(11)


#=================================================================================================================

oddDict = {}

class ODD:
    def __init__(self, chatID):
        self.chatID = chatID
        self.unit = ""
        self.battalion = ""        
        self.datetime = ""
        self.coy = ""
        self.wpn = ""
        self.butt = 0
        self.defPart = ""
        self.defect = ""
        self.rmk = "N/A"
       


# The entry function
def start(update_obj, context):
    # send the question, and show the keyboard markup (suggested answers)
    # list1 = [unitbuttons['Armour'], unitbuttons['Artillery']]
    # list2 = [unitbuttons['Engineers'], unitbuttons['Commandos'], unitbuttons['Guards']]
    # list3 = [unitbuttons['Infantry'], unitbuttons['Signals']]
    try:
        keyboard_list = ["Nearest AEDs", "Static Maps", "Restart"]
        list1 = [[telegram.KeyboardButton(text=word, request_location=True)] for word in keyboard_list]
        kb = telegram.ReplyKeyboardMarkup(keyboard=list1,resize_keyboard = True, one_time_keyboard = True)
        chat_id = update_obj.message.chat_id

        update_obj.message.reply_text("Hello there, which unit are you from?",reply_markup=kb)
    # go to the Batallion state
        return BATSTEP
    except Exception as e:
        cancel(e, context)


def batStep(update_obj, context):
    try:
        chat_id = update_obj.message.chat_id
        msg = update_obj.message
        print(msg)
        return END
    except Exception as e:
        cancel(update_obj, context)



def end(update_obj, context):

    chat_id = update_obj.message.chat_id
    msg = update_obj.message.text

    # get the user's first name
    first_name = update_obj.message.from_user['first_name']
    update_obj.message.reply_text(
        f"Thank you {first_name} for your report!", reply_markup=telegram.ReplyKeyboardRemove()
    )
    return telegram.ext.ConversationHandler.END




def cancel(update_obj, context):
    # get the user's first name
    first_name = update_obj.message.from_user['first_name']
    update_obj.message.reply_text(
        f"Okay, no question for you then, take care, {first_name}!", reply_markup=telegram.ReplyKeyboardRemove()
    )
    return telegram.ext.ConversationHandler.END



def main():
    # a regular expression that matches yes or no
    yes_no_regex = re.compile(r'^(yes|no|y|n)$', re.IGNORECASE)
    # Create our ConversationHandler, with only one state


    handler = telegram.ext.ConversationHandler(
        entry_points=[telegram.ext.CommandHandler('start', start)],
        states={
                BATSTEP: [telegram.ext.MessageHandler(telegram.ext.Filters.location or telegram.ext.Filters.text, batStep)],
                COYSTEP: [telegram.ext.MessageHandler(telegram.ext.Filters.text, coyStep)],
                WPNSTEP: [telegram.ext.MessageHandler(telegram.ext.Filters.text, wpnStep)],
                BUTTSTEP: [telegram.ext.MessageHandler(telegram.ext.Filters.text, buttStep)],
                DEFECTSTEP: [telegram.ext.MessageHandler(telegram.ext.Filters.text, defectStep)],
                DEFECTIDSTEP: [telegram.ext.MessageHandler(telegram.ext.Filters.text, defectIDStep)],
                RMKCHKSTEP: [telegram.ext.MessageHandler(telegram.ext.Filters.text, rmkchkStep)],
                YESORNO: [telegram.ext.MessageHandler(telegram.ext.Filters.text, check_yes_or_no)],
                END: [telegram.ext.MessageHandler(telegram.ext.Filters.text, end)],
                CANCEL: [telegram.ext.MessageHandler(telegram.ext.Filters.text, cancel)]
        },
        fallbacks=[telegram.ext.CommandHandler('cancel', cancel)],
        )
    # add the handler to the dispatcher
    dispatcher.add_handler(handler)
    # start polling for updates from Telegram
    updater.start_webhook(listen="0.0.0.0",
                        port=PORT,
                        url_path=TOKEN,
                        webhook_url="https://polar-chamber-36116.herokuapp.com/" + TOKEN)
    updater.idle()


if __name__ == '__main__':
    main()