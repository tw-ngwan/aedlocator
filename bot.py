from dotenv import load_dotenv
load_dotenv()


from locations import locations
from maps import campMaps, badURL
from buttons import campButtons
import telegram


from time import sleep
import os
import geopy.distance
from telegram import Location, KeyboardButton
import telegram.ext
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
updater = telegram.ext.Updater(API_KEY)
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
    try:
        buttons = [[telegram.KeyboardButton(text='Nearest AED',request_location=True)],\
            [telegram.KeyboardButton(text='Static Map')],[telegram.KeyboardButton(text='Restart')]]
        kb = telegram.ReplyKeyboardMarkup(keyboard=buttons,resize_keyboard = True, one_time_keyboard = True)
        welcomeString = """
        Hello, would you like to see your nearest AED or a static map?
If you click Nearest AED, the bot will request your location!
Click the RESTART button at any time to restart the commands!!
        """
        update_obj.message.reply_text(welcomeString,reply_markup=kb)
        return STATECHECKER
    except Exception as e:
        errorString = "Sorry something went wrong! Please press /start to try again!"
        print(e)
        update_obj.message.reply_text(errorString)



def state_checker(update_obj, context):
    try:
        chat_id = update_obj.message.chat_id
        #msg = update_obj.message.text
        print(f"{update_obj.message.location}")
        if update_obj.message.location: 
            current_location(update_obj, context)
            return END
        else:# msg == "Static Maps":
            return IMAGESTEP
    except Exception as e:
        cancel(update_obj, context)



def current_location(update_obj, context):
    try:
        chat_id = update_obj.message.chat_id
       
        if update_obj.location:
            aed = AED(update_obj.location)
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
                update_obj.send_chat_action("typing")
                sleep(0.5)
                update_obj.message.reply_text("The nearest AED is more than 1000m away! This probably means the camp you are in is not supported yet! Thanks for your patience!!" )
                sleep(1)
                
            update_obj.message.reply_text("The AEDs below are sorted from nearest to farthest!" )
            update_obj.send_chat_action("typing")
            sleep(0.5)
            counter = 0
            for keys in sortedDist:
                if counter > 1: # to limit to the 2 closest AEDs
                    break
                update_obj.send_location(aed.aeds[keys][0], aed.aeds[keys][1])
                sendString = "The AED at the above location is approximately " + str(round(keys)) + "m away"
                update_obj.message.reply_text(sendString )
                counter += 1
                
            finalString = "Stay Safe!"
            update_obj.message.reply_text( "If you need any more information, please type in the /start command again!")
            update_obj.message.reply_text(finalString )
            
        else:
            raise ValueError
    except ValueError:
       update_obj.message.reply_text("Could not get user location, press /start to try again!" )




def cancel(update_obj, context):
    # get the user's first name
    first_name = update_obj.message.from_user['first_name']
    update_obj.message.reply_text(
        f"Update is {update_obj}!", reply_markup=telegram.ReplyKeyboardRemove()
    )
    return telegram.ext.ConversationHandler.END

def end(update_obj, context):
    # get the user's first name
    first_name = update_obj.message.from_user['first_name']
    update_obj.message.reply_text(
        f"Thank you {first_name}, have a wonderful day. Press /start to restart the bot!", reply_markup=telegram.ReplyKeyboardRemove()
    )
    return telegram.ext.ConversationHandler.END

def main():



    handler = telegram.ext.ConversationHandler(
        entry_points=[telegram.ext.CommandHandler('start', start)],
        states={
                CURRLOCATION: [telegram.ext.MessageHandler(telegram.ext.Filters.location,current_location )],
                STATECHECKER: [telegram.ext.MessageHandler(telegram.ext.Filters.text,state_checker )],
                IMAGESTEP: [telegram.ext.MessageHandler(telegram.ext.Filters.text, end)],
                RETURNIMAGE: [telegram.ext.MessageHandler(telegram.ext.Filters.text, end)],
                CANCEL: [telegram.ext.MessageHandler(telegram.ext.Filters.text, cancel)],
                END: [telegram.ext.MessageHandler(telegram.ext.Filters.text, end)]

        },
        fallbacks=[telegram.ext.CommandHandler('end', end)],
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