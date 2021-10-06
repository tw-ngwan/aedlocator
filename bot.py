import os
import logging
import geopy.distance
from time import sleep

import telegram
from telegram.ext import Updater, CommandHandler,ConversationHandler, MessageHandler, Filters

from locations import locations
from maps import campMaps, badURL

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# The API Key we received for our bot
TOKEN = os.environ.get('TOKEN')
PORT = int(os.environ.get('PORT', 8443))

# Create an updater object with our API Key
updater = Updater(TOKEN)
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
def help(update_obj, context):
    try:
        help_string = """
        Welcome to AED Locator Bot! Here you can find maps of 
        SAF camps with labeled AED locations or even find the
        nearest AEDs to your current location.

        /start will start the bot and allow you to choose 
        your appropriate function

        The bot will request your location if you choose to 
        find the nearest AEDs

        If you are having any issues please contact 62FMD
        at 6AMB
        
        
        """

        update_obj.message.reply_text(help_string)
        return ConversationHandler.END

    except Exception as e:
        unexpected_error(e, context)


# The entry function
def start(update_obj, context):

    try:
        # keyboard_list = ["Nearest AEDs", "Static Maps", "Restart"]
        list1 = [[telegram.KeyboardButton(text="Nearest AEDs", request_location=True)],\
                [telegram.KeyboardButton(text="Static Maps")],\
                # [telegram.KeyboardButton(text="Restart")],\
                [telegram.KeyboardButton(text="Quit")]]
        
        kb = telegram.ReplyKeyboardMarkup(keyboard=list1,resize_keyboard = True, one_time_keyboard = True)

        update_obj.message.reply_text("Hello there, how can I help you?",reply_markup=kb)
    # go to the Batallion state
        return STATECHECKER
    except Exception as e:
        unexpected_error(e, context)


def state_checker(update_obj, context):
    try:
        
        msg = update_obj.message
        logger.info(msg)
        if msg.text == "Static Maps":
            static_map(update_obj, context)
            return IMAGE 
        elif msg.location:
            return current_location(update_obj, context)
        # elif msg.text == "Restart":
        #     return start(update_obj, context)
        elif msg.text == "Quit":
            return end(update_obj, context)
        else:
            return unexpected_input(update_obj, context)
    except Exception as f:
        unexpected_error(update_obj, context)


def current_location(update_obj, context):
    try:
        chat_id = update_obj.message.chat_id
       
        aed = AED(update_obj.message.location)
        aedDict[chat_id] = aed
        minDist = 100000000000
        for coords in locations:
            dist = geopy.distance.distance((aed.latitude, aed.longitude), coords).m
            
            aed.aeds[dist] = coords
            if dist < minDist:
                minDist = dist
        sortedDist = sorted(list(aed.aeds.keys()))
        if sortedDist[0] > 1000:
            context.bot.send_chat_action(chat_id, action=telegram.ChatAction.TYPING)
            sleep(0.5)
            update_obj.message.reply_text("The nearest AED is more than 1000m away! This probably means the camp you are in is not supported yet! Thanks for your patience!!")
            sleep(1)


        update_obj.message.reply_text("The 2 Nearest AEDs are shown below", reply_markup=telegram.ReplyKeyboardRemove())
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
            
        update_obj.message.reply_text("Stay Safe!", reply_markup=telegram.ReplyKeyboardRemove())
        update_obj.message.reply_text("If you need any more information, please type in the /start command again!")

        return ConversationHandler.END
    except ValueError as e:
       update_obj.message.reply_text(f"location exception: {e}")
       unexpected_error(update_obj, context)



# #========================================================================
def static_map(update_obj, context):
    try:
        list1 = [[telegram.KeyboardButton(text=camps.upper())] for camps in sorted(list(campMaps.keys()))]
        list1.append([telegram.KeyboardButton(text="Restart")])
        list1.append([telegram.KeyboardButton(text="Quit")])

        kb = telegram.ReplyKeyboardMarkup(keyboard=list1,resize_keyboard = True, one_time_keyboard = True)
        
        update_obj.message.reply_text("Which camp would you like a map for?",reply_markup=kb )
        return IMAGE
    except Exception as e:
        update_obj.message.reply_text(f"static map exception: {e}")
        unexpected_error(update_obj, context)

def return_image(update_obj, context):
    try:

        chat_id = update_obj.message.chat.id
        msg = update_obj.message.text.lower()
        image_path = ''
        url = ""

        if update_obj.message.text == "Quit":
            return end(update_obj, context)
        elif msg in campMaps.keys():
            image_path = campMaps[msg]['image']
            url = campMaps[msg]['url']
        elif update_obj.message.text == "/start" or update_obj.message.text == "Restart":
            return start(update_obj, context)
        else:
            raise ValueError
        
        if image_path == badURL:
            errorString = "Sorry, support for this camp is not available yet! Press /start to try again!"
            context.bot.send_photo(chat_id, photo=open(image_path, 'rb'))
            update_obj.message.reply_text(errorString)
        # elif update_obj.message.text == "/start" or update_obj.message.text == "RESTART":
        #     pass
        else:
            context.bot.send_photo(chat_id, photo=open(image_path, 'rb'))
            update_obj.message.reply_text(f"You can find the map at the following link: {url}")
            update_obj.message.reply_text("If you need any more information, please type in the /start command again!",reply_markup=telegram.ReplyKeyboardRemove())
        return ConversationHandler.END
    
    except ValueError:
        errorString = "Please use the buttons provided! Press /start to try again!"
        update_obj.message.reply_text(errorString)
        return ConversationHandler.END
        # else:
        #     errorString = "This input is not recognized! Press /start to try again!"
        #     update_obj.message.reply_text(errorString)
        #     return ConversationHandler.END
    except Exception as e:
        update_obj.message.reply_text(f"image exception: {e}")
        unexpected_error(update_obj, context)



def end(update_obj, context):
    # get the user's first name
    first_name = update_obj.message.from_user['first_name']
    update_obj.message.reply_text(
        f"Thank you {first_name}. Please click /start to start again ", reply_markup=telegram.ReplyKeyboardRemove()
    )
    return ConversationHandler.END




def unexpected_error(update_obj, context):
    # get the user's first name
    first_name = update_obj.message.from_user['first_name']
    update_obj.message.reply_text(f"There was an issue, please click /start {first_name}!",\
         reply_markup=telegram.ReplyKeyboardRemove())
    return ConversationHandler.END

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)
    return ConversationHandler.END



def unexpected_input(update_obj, context):
    # get the user's first name
    update_obj.message.reply_text(f"Unexpected input, please click /start to start the bot!",\
         reply_markup=telegram.ReplyKeyboardRemove())
    return ConversationHandler.END

def main():

    handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
                IMAGE:[MessageHandler(Filters.text, return_image)],
                STATECHECKER: [MessageHandler(Filters.location, state_checker),
                MessageHandler(Filters.text, state_checker)],
                MAPSTEP: [MessageHandler(Filters.text, static_map)],
                END: [MessageHandler(Filters.text, end)],
                CANCEL: [MessageHandler(Filters.text, unexpected_error)]
        },
        fallbacks=[CommandHandler('cancel', unexpected_error)],
        )
    # add the handler to the dispatcher
    dispatcher.add_handler(handler)
    dispatcher.add_handler(MessageHandler(Filters.text | ~Filters.text, unexpected_input))
    dispatcher.add_handler(CommandHandler('help', help))

    dispatcher.add_error_handler(error)

    # start polling for updates from Telegram
    updater.start_webhook(listen="0.0.0.0",
                        port=PORT,
                        url_path=TOKEN,
                        webhook_url="https://polar-chamber-36116.herokuapp.com/" + TOKEN)
    updater.idle()


if __name__ == '__main__':
    main()