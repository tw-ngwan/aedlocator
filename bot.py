from dotenv import load_dotenv
load_dotenv()

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
TOKEN = '1925685631:AAHWdFKf07_NjwHa3dbnlGp4i42a00ikt_8'
bot = telebot.TeleBot(TOKEN)

PORT = int(os.environ.get('PORT', 8443))


####################################################################################
#Global Variables
aedDict = {}
campButtons = {
        "NSDC":telebot.types.KeyboardButton(text='NSDC'),
        "NSC" : telebot.types.KeyboardButton(text='NSC'),
        "Mandai Hill" : telebot.types.KeyboardButton(text='Mandai Hill'),
        "KC2" : telebot.types.KeyboardButton(text='KC2'),
        "KC3" :telebot.types.KeyboardButton(text='KC3'),
        "Mowbray" :telebot.types.KeyboardButton(text='Mowbray'),
        "Hendon" :telebot.types.KeyboardButton(text='Hendon'),
        "Clementi" :telebot.types.KeyboardButton(text='Clementi'),
        "Maju" :telebot.types.KeyboardButton(text='Maju'),
        "Gombak" :telebot.types.KeyboardButton(text='Gombak'),
        "Gedong" :telebot.types.KeyboardButton(text='Gedong'),
        "Quit" :telebot.types.KeyboardButton(text="RESTART")
}

class AED:
    def __init__(self, location): #initialized with the coordinates of a location
        self.latitude = location.latitude
        self.longitude = location.longitude
        self.aeds = {}

locations = {

    1: (1.4055524, 103.8182829), #NSDC
    2: (1.4067986, 103.8192924), #NSDC
    3: (1.4091958,103.8186530) #NSDC

}

       

# locations = {
#     "nsdc": {
#         1: (1.4055524, 103.8182829),
#         2: (1.4067986, 103.8192924),
#         3: (1.4091958,103.8186530)

#     }
#     #add the rest of the coordinates of other camps in this format
#     # "campName": {
#     # num: (lat, lon),
#     # num: (lat,lon)
#     # }

#     #campName must match the script as shows in campMaps
# }

#using badURL as a way of showing that a map is not available
badURL = "https://lh3.googleusercontent.com/m61vTtkjihiwIJ_PEnVPEKfd8Yx1FsoGcCzcrx0A5SJjZtnpu7h61HB-viz0K4JpBnK2QAf0KRfN8AA-spL_C6SIf-tMu4o3x5W6RMuG37RXP4X4COk6QRrE0ylLQJYVPLJ3-G3wQC5MQkwCcksHJfTq2UCYxKdPlSdy5pzb6m5g7Z2pot_z8_uxssfM0FjPmQ9EpprG_g_3wZ1hwp1-iEr3_RYnZUt7YzfaDDFWMlElGVCwfJ6dbzqD2NCNTGlHn_webljEdtswpUQx-2H2EHxBtlU03_ey4fKz0rGCUhN2ryyauTfdTzfvsiw6WB2Bz5uency7qEqA8EiooqZwVgRvDFOpPp8tTEZLI7JnErd_dqwrDr-3nJLdTyEntpGSlKlKBdbl4o6R1-JysFom6VcjAPW9Y1o-ZKOwoWhvVkOFHLad87PyU6_N8cBY_5WiaTbFs5Nrjl_sY84ViBp_lx4MOaW6xpjS9evotqJ2HJcen5rPGTEz3o89v2evb8nKVfqnI-M2cnTSd9qN6M8aqvz8K1XtI_ts61wVbVNCM4S1UoohWTQB0MYHkAeljkzK7unLavErhZSajtRKgfHhfIfbPK-eHHyXFxbqQ_qFCAki9FCfUT79zd80TFURjb8DlcT0dBOtyIG75D8_cCkwG2JV4_Y3M1N77K0EOfDi80m51aHxfW6znaHBob_1em6qZxBLBQadGBTQvCj_jOWEVcgOsg=w800-h399-no?authuser=1"
campMaps = {
    "nsdc": "https://lh3.googleusercontent.com/jz7l8taMGnOPqRTafzGq_3Uflb92HE54IkQ4AwD1Za_e2W5ywkfP-fqYV2V_aQ91z7tKvBAbpGV2w9F5uB6zNXp2YOEuaXV3cOnA5WSQeiAmE-cMCW-K4GMSjSEozIqZ2pxt2Nz1aF_dWwHhczezH3nUWo1cK85IFD8HPd4Ct1qq-YlP84q0MN9JQAKTtnsowsuPe8IiXyq33UuHhzluOkkc2_pQdBBWZxgA7Sit767DkZO30GBrGSNkWI9GPk2G6PEWM5edoRgWqtxaFKXeYsPV4kd9eCud4SykFGlRHJuxk5c_CXA2FSZH7ZFQk1ikTyBkvMgAY9UycxNPO8lUxFb6FLwLqKBKoXcP7uIG0BfFtT9YLVh135NSuRBvl538qQG-zhkv1tYi-w03LgRdo9zk5790QrEszkkKFL8fcGoqkmuGrtIzGQ5mEgXPqhh4hZoiSkaDTMZHDLgTBl6IitaIrWtmnzs9f8OFNQGSGuB_4qAFavOgCvKITX4WiimtWQaD7WGky8RVKFiB7dlLc2uhu_BUeVVtUaD2EzWelye0lKr1dpob7LK6qd30Br2qf_7LDVUzjbMbRjE5LDn1UWsYXAT8oKWRn213sEwArF56lUDb8kYdpIkHQApqyjDuykVjPRrRRhXtNTjtOJdP4ZdIqZ15ks9eqU1F0P2dcTiZbWSqAO-esahf0zXS7I1XTFZiH6wXX6Plw2PGG9eGmoK0zw=w596-h792-no?authuser=1",
    "nsc": badURL,
    "mandai hill":badURL,
    "kc2":badURL,
    "kc3" :badURL,
    "mowbray": badURL,
    "hendon":badURL,
    "clementi":badURL,
    "maju":badURL,
    "gombak":badURL,
    "gedong":badURL
}

#mappingMapDict was needed in previous implementation, keep for now

# mappingMapDict = {1:"nsdc", 2:"nsc", 3:"mandai hill", 4:"kc2", 5:"kc3", \
#     6:"mowbray", 7: "hendon", 8:"clementi", 9:"maju", 10:"gombak", 11:"gedong"}


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
#     Welcome to AED Bot!
#     If you need to find the nearest AED or get a map of the AEDs at a certain camp use the /start command

# If you haven't used the bot in a while, just type in /start and the bot will restart

# If you have any issues please contact 62FMD at 6AMB!
    
#     """)
    
    
# #if location is not handled correctly, exception is now raised
@bot.message_handler(content_types=['location'])
def currentLocation(update, context):
    try:
        chat_id = update.effective_message.chat_id
       
        if update.effective_message.location:
            aed = AED(update.effective_message.location)
            aedDict[chat_id] = aed
            
            minDist = 100000000000
            for coords in locations.values():
                dist = geopy.distance.distance((aed.latitude, aed.longitude), coords).m
                
                #dist = geopy.distance.distance((1.405854, 103.818543), coords).m
                aed.aeds[dist] = coords
                if dist < minDist:
                    minDist = dist
            sortedDist = sorted(list(aed.aeds.keys()))
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


# #exception handling added for out of scope input
def distanceCalculator(update, context):
    try:
        chat_id = update.effective_message.chat.id
        aed = aedDict[chat_id]

        camp =  update.effective_message.text.lower()
        if update.effective_message.text == "QUIT":
            raise Exception
        elif update.effective_message.text == "/start" or update.effective_message.text == "RESTART":
            start(update.effective_message)
        elif camp not in campMaps.keys():
            raise ValueError
        
        
        if camp in locations.keys():
            minDist = 100000000000
            for coords in locations[camp].values():
                dist = geopy.distance.distance((aed.latitude, aed.longitude), coords).m
                
                #dist = geopy.distance.distance((1.405854, 103.818543), coords).m
                aed.aeds[dist] = coords
                if dist < minDist:
                    minDist = dist
            sortedDist = sorted(list(aed.aeds.keys()))
            bot.send_message(update.effective_message.chat.id,"The AEDs below are sorted from nearest to farthest!" )
            bot.send_chat_action(update.effective_message.chat.id, "typing")
            sleep(1)
            counter = 0
            for keys in sortedDist:
                if counter > 1: # to limit to the 2 closest AEDs
                    break
                bot.send_location(update.effective_message.chat.id, aed.aeds[keys][0], aed.aeds[keys][1])
                sendString = "The AED at the above location is approximately " + str(round(keys)) + "m away"
                bot.send_message(update.effective_message.chat.id,sendString )
                counter += 1
                
                sleep(0.5)
            finalString = "Stay Safe!"
            bot.send_message(chat_id, "If you need any more information, please type in the /start command again!")
            bot.send_message(update.effective_message.chat.id, finalString )
        elif camp == "/start" or update.effective_message.text == "RESTART":
            pass
        else:
            bot.send_message(update.effective_message.chat.id,"Sorry, we currently don't have the coordinates of the AEDs in this camp! Press /start to try again!" )
    
    #introducing exception handling if the input is not from the buttons
    except ValueError:
        if camp.isalpha():
            errorString = "Please use the buttons provided! Press /start to try again!"
            bot.send_message(update.effective_message.chat.id,errorString)
        else:
            errorString = "This input is not recognized! Press /start to try again!"
            bot.send_message(update.effective_message.chat.id,errorString)
    except Exception:
        bot.send_message(update.effective_message.chat.id,"Have a wonderful day! Please press /start to try again!!!")




# #========================================================================

# @bot.message_handler(func=checker)
def staticMap(update, context):
    try:
       
        locs = telebot.types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
   
        locs.add(campButtons["NSDC"], campButtons["NSC"], campButtons["Mandai Hill"],campButtons["KC2"],\
                campButtons["KC3"],campButtons["Mowbray"],campButtons["Hendon"],\
                campButtons["Clementi"],campButtons["Maju"],campButtons["Gombak"],campButtons["Gedong"], campButtons["Quit"])

        msg = bot.reply_to(update.effective_message, """\
        Which camp would you like a map for?
        """, reply_markup=locs)
        #bot.register_next_step_handler(msg, returnImage)
    except Exception as e:
        bot.reply_to(update.effective_message, 'oooops')

def returnImage(update, context):
    try:
        #bot.send_message(update.effective_message.chat.id,"I am in returnImage" )

        chat_id = update.effective_message.chat.id
        msg = update.effective_message.text.replace(" ", "")
        msg = msg.lower()
        url = ""
        #stri = "This is msg.lower(): " + msg
        #bot.send_message(update.effective_message.chat.id,stri )

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
# def qFunc(message, context):
#     try:
#         bot.send_message(message.chat.id,"Have a wonderful day! Please press /start to try again!")
#     except Exception:
#         errorString = "Sorry something went wrong! Please press /start to try again!"
#         bot.send_message(message.chat.id,errorString)


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
    #dp.add_handler(MessageHandler(Filters.text(campButtons.keys()), distanceCalculator)) #does keys have to be a list?
    dp.add_handler(MessageHandler(Filters.text(startList), start)) 
    dp.add_handler(MessageHandler(Filters.text(campButtons.keys()), returnImage)) #does keys have to be a list?

    # add handlers
    updater.start_webhook(listen="0.0.0.0",
                        port=PORT,
                        url_path=TOKEN,
                        webhook_url="https://polar-chamber-36116.herokuapp.com/" + TOKEN)
    updater.idle()


if __name__ == '__main__':
    main()