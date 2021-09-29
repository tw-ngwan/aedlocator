import telegram
import telebot
import telegram.ext
import re
from random import randint
import os
import logging
from locations import locations
from maps import campMaps, badURL
from buttons import campButtons
import geopy.distance
from time import sleep


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

STATECHECKER, LOCATIONSTEP, MAPSTEP,IMAGE, END, CANCEL = range(6)


####################################################################################
#Global Variables
aedDict = {}


class AED:
    def __init__(self, location): #initialized with the coordinates of a location
        self.latitude = location.latitude
        self.longitude = location.longitude
        self.aeds = {}


####################################################################################

# The entry function
def start(update_obj, context):
    # send the question, and show the keyboard markup (suggested answers)
    # list1 = [unitbuttons['Armour'], unitbuttons['Artillery']]
    # list2 = [unitbuttons['Engineers'], unitbuttons['Commandos'], unitbuttons['Guards']]
    # list3 = [unitbuttons['Infantry'], unitbuttons['Signals']]
    try:
        # keyboard_list = ["Nearest AEDs", "Static Maps", "Restart"]
        list1 = [[telegram.KeyboardButton(text="Nearest AEDs", request_location=True)],\
                [telegram.KeyboardButton(text="Static Maps")],\
                 [telegram.KeyboardButton(text="Restart")]]
        kb = telegram.ReplyKeyboardMarkup(keyboard=list1,resize_keyboard = True, one_time_keyboard = True)
        chat_id = update_obj.message.chat_id

        update_obj.message.reply_text("Hello there, what do you want?",reply_markup=kb)
    # go to the Batallion state
        return STATECHECKER
    except Exception as e:
        cancel(e, context)


def state_checker(update_obj, context):
    try:
        chat_id = update_obj.message.chat_id        
        
        msg = update_obj.message
        print(msg)
        if msg.location:
            currentLocation(update_obj, context)
            return END
        elif msg.text == "Static Maps":
            
            return MAPSTEP
        elif msg.text == "Restart":
            return END
        else:
            return CANCEL
    except Exception as e:
        cancel(update_obj, context)


def currentLocation(update_obj, context):
    try:
        chat_id = update_obj.message.chat_id
       
        aed = AED(update_obj.message.location)
        aedDict[chat_id] = aed
        minDist = 100000000000
        for coords in locations:
            dist = geopy.distance.distance((aed.latitude, aed.longitude), coords).m
            
            #dist = geopy.distance.distance((1.405854, 103.818543), coords).m if need to show POV for NSDC
            aed.aeds[dist] = coords
            if dist < minDist:
                minDist = dist
        sortedDist = sorted(list(aed.aeds.keys()))
        if sortedDist[0] > 1000:
            context.bot.send_chat_action(chat_id, action=telegram.ChatAction.TYPING)
            sleep(0.5)
            update_obj.message.reply_text("The nearest AED is more than 1000m away! This probably means the camp you are in is not supported yet! Thanks for your patience!!")
            sleep(1)


        update_obj.message.reply_text("The AEDs below are sorted from nearest to farthest!", reply_markup=telegram.ReplyKeyboardRemove())
        context.bot.send_chat_action(chat_id, action=telegram.ChatAction.TYPING)
        sleep(0.5)
        counter = 0
        for keys in sortedDist:

            if counter > 1: # to limit to the 2 closest AEDs
                break
            context.bot.send_location(chat_id, aed.aeds[keys][0], aed.aeds[keys][1])
            curr_dist = str(round(keys))
            sendString = f"The AED at the above location is approximately {curr_dist} m away"
            update_obj.message.reply_text(sendString)
            counter += 1
            
        finalString = "Stay Safe!"
        update_obj.message.reply_text("If you need any more information, please type in the /start command again!")
        update_obj.message.reply_text(finalString)
    except ValueError:
       update_obj.message.reply_text("lol")




# #========================================================================
def static_map(update_obj, context):
    try:

        list1 = [[telegram.KeyboardButton(text=camps)] for camps in list(campButtons.keys())]
        kb = telegram.ReplyKeyboardMarkup(keyboard=list1,resize_keyboard = True, one_time_keyboard = True)
        
        update_obj.message.reply_text("Which camp would you like a map for?",reply_markup=kb )
        return IMAGE
        #bot.register_next_step_handler(msg, returnImage)
    except Exception as e:
        update_obj.message.reply_text("lol")

def return_image(update_obj, context):
    try:

        chat_id = update_obj.message.chat.id
        msg = update_obj.effective_message.text.lower()
        image_path = ''
        url = ""

        if update_obj.message.text == "QUIT":
            raise Exception
        elif update_obj.message.text in campButtons.keys():
            image_path = campMaps[msg]['image']
            url = campMaps[msg]['url']
        elif update_obj.message.text == "/start" or update_obj.message.text == "RESTART":
            start(update_obj.effective_message)
        else:
            raise ValueError
        
        if image_path == badURL:
            errorString = "Sorry, support for this camp is not available yet! Press /start to try again!"
            context.bot.send_photo(chat_id=chat_id, photo=image_path)
            update_obj.message.reply_text(errorString)
        elif update_obj.effective_message.text == "/start" or update_obj.effective_message.text == "RESTART":
            pass
        else:
            context.bot.send_photo(chat_id, photo=open(image_path, 'rb'))
            update_obj.message.reply_text(f"You can find the map at the following link: {url}")
            update_obj.message.reply_text("If you need any more information, please type in the /start command again!")
        return END
    except ValueError:
        if msg.isalpha():
            errorString = "Please use the buttons provided! Press /start to try again!"
            update_obj.message.reply_text(errorString)
        else:
            errorString = "This input is not recognized! Press /start to try again!"
            update_obj.message.reply_text(errorString)
    except Exception:
        update_obj.message.reply_text("lol")




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
        f"There was an issue, please click /start {first_name}!", reply_markup=telegram.ReplyKeyboardRemove()
    )
    return telegram.ext.ConversationHandler.END



def main():

    handler = telegram.ext.ConversationHandler(
        entry_points=[telegram.ext.CommandHandler('start', start)],
        states={
                STATECHECKER: [telegram.ext.MessageHandler(telegram.ext.Filters.location or telegram.ext.Filters.text, state_checker)],
                MAPSTEP: [telegram.ext.MessageHandler(telegram.ext.Filters.text, static_map)],
                IMAGE:[telegram.ext.MessageHandler(telegram.ext.Filters.text, return_image)],
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