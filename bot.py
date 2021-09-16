from dotenv import load_dotenv
load_dotenv()


from locations import locations
from maps import campMaps, badURL
from buttons import campButtons


from time import sleep
import os
import telebot
import geopy.distance
from telegram import Location, KeyboardButton
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from flask import Flask, request
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


"""
Issues to solve for
1. If for some reason the input is not one of the two buttons
    a. Static Map:
        1. exception handling for input is not robust
    b. Nearest AED:
        2. exception handling for input is not robust



"""

# API_key = os.environ.get('aedAPI_KEY')
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
PORT = int(os.environ.get('PORT', 8443))


####################################################################################
#Global Variables
aedDict = {}


class AED:
    def __init__(self, location): #initialized with the coordinates of a location
        self.latitude = location.latitude
        self.longitude = location.longitude
        self.aeds = {}


####################################################################################
def start(update, context):
    """Send a message when the command /start is issued."""
    try:
        loc = telebot.types.KeyboardButton(text='Nearest AED', request_location=True)
        not_loc = telebot.types.KeyboardButton(text='Static Map')
        quit = campButtons["Quit"]

        start = telebot.types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
        start.add(loc, not_loc, quit)
        welcomeString = """
        Hello, would you like to see your nearest AED or a static map?
If you click Nearest AED, the bot will request your location!
Click the RESTART button at any time to restart the commands!!
        """
        bot.send_message(update.effective_message.chat_id,text= welcomeString, reply_markup=start)
    except Exception:
        errorString = "Sorry something went wrong! Please press /start to try again!"
        bot.send_message(update.effective_message.chat_id,errorString)


def help(update, context):
    """Send a message when the command /help is issued."""
    bot.send_message(update.effective_message.chat_id, """ 
Welcome to AED Bot!
If you need to find the nearest AED or get a map of the AEDs at a certain camp use the /start command

If you haven't used the bot in a while, just type in /start and the bot will restart

If you have any issues please contact 62FMD at 6AMB!
    
     """)
    
    
# #if location is not handled correctly, exception is now raised
@bot.message_handler(content_types=['location'])
def currentLocation(update, context):
    try:
        chat_id = update.effective_message.chat_id
       
        if update.effective_message.location:
            aed = AED(update.effective_message.location)
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
                bot.send_chat_action(update.effective_message.chat.id, "typing")
                sleep(0.5)
                bot.send_message(update.effective_message.chat.id,"The nearest AED is more than 1000m away! This probably means the camp you are in is not supported yet! Thanks for your patience!!" )
                sleep(1)
                
            bot.send_message(update.effective_message.chat.id,"The AEDs below are sorted from nearest to farthest!" )
            bot.send_chat_action(update.effective_message.chat.id, "typing")
            sleep(0.5)
            counter = 0
            for keys in sortedDist:
                if counter > 1: # to limit to the 2 closest AEDs
                    break
                bot.send_location(update.effective_message.chat.id, aed.aeds[keys][0], aed.aeds[keys][1])
                sendString = "The AED at the above location is approximately " + str(round(keys)) + "m away"
                bot.send_message(update.effective_message.chat.id,sendString )
                counter += 1
                
            finalString = "Stay Safe!"
            bot.send_message(chat_id, "If you need any more information, please type in the /start command again!")
            bot.send_message(update.effective_message.chat.id, finalString )
            
        else:
            raise ValueError
    except ValueError:
       bot.send_message(update.effective_message.chat.id,"Could not get user location, press /start to try again!" )



# #========================================================================
def staticMap(update, context):
    try:
        locs = telebot.types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
   
        locs.add(campButtons["NSDC"], campButtons["NSC"], campButtons["Mandai Hill"],campButtons["KC2"],\
                campButtons["KC3"],campButtons["Mowbray"],campButtons["Hendon"],\
                campButtons["Clementi"],campButtons["Maju"],campButtons["ALB"],campButtons["Gedong"], campButtons["Quit"])

        msg = bot.reply_to(update.effective_message, """\
        Which camp would you like a map for?
        """, reply_markup=locs)
        #bot.register_next_step_handler(msg, returnImage)
    except Exception as e:
        bot.reply_to(update.effective_message, 'oooops')

def returnImage(update, context):
    try:

        chat_id = update.effective_message.chat.id
        msg = update.effective_message.text.lower()
        url = ""

        if update.effective_message.text == "QUIT":
            raise Exception
        elif update.effective_message.text in campButtons.keys():
            url = campMaps[msg]
        elif update.effective_message.text == "/start" or update.effective_message.text == "RESTART":
            start(update.effective_message)
        else:
            raise ValueError
        
        if url == badURL:
            errorString = "Sorry, support for this camp is not available yet! Press /start to try again!"
            bot.send_photo(chat_id=chat_id, photo=url)
            bot.send_message(update.effective_message.chat.id,errorString )
        elif update.effective_message.text == "/start" or update.effective_message.text == "RESTART":
            pass
        else:
            bot.send_photo(chat_id=chat_id, photo=url)
            bot.send_message(chat_id, "If you need any more information, please type in the /start command again!")
    except ValueError:
        if msg.isalpha():
            errorString = "Please use the buttons provided! Press /start to try again!"
            bot.send_message(update.effective_message.chat.id,errorString)
        else:
            errorString = "This input is not recognized! Press /start to try again!"
            bot.send_message(update.effective_message.chat.id,errorString)
    except Exception:
        st = update.effective_message.text.replace(" ", "").lower()
        bot.send_message(update.effective_message.chat.id,st)

# @bot.message_handler(regexp="Quit")    
def qFunc(update, context):
    try:
        bot.send_message(update.effective_message.chat.id,"Unrecognized Input! Please press /start to try again!")
    except Exception:
        errorString = "Sorry something went wrong! Please press /start to try again!"
        bot.send_message(update.effective_message.chat.id,errorString)


#####################################################################################

#bot.polling()




def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    
    startList = ["/start", "RESTART"]
    #message handling
    dp.add_handler(MessageHandler(Filters.location, currentLocation))
    dp.add_handler(MessageHandler(Filters.text("Static Map"), staticMap))
    dp.add_handler(MessageHandler(Filters.text(startList), start)) 
    dp.add_handler(MessageHandler(Filters.text(campButtons.keys()), returnImage)) #does keys have to be a list?
    dp.add_handler(MessageHandler(Filters.text, qFunc)) #does keys have to be a list?

    # add handlers
    updater.start_webhook(listen="0.0.0.0",
                        port=PORT,
                        url_path=TOKEN,
                        webhook_url="https://polar-chamber-36116.herokuapp.com/" + TOKEN)
    updater.idle()


if __name__ == '__main__':
    main()