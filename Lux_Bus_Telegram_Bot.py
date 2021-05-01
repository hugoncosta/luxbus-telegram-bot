import os
from dotenv import load_dotenv
from datetime import datetime
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import pymongo
import dns
import getRealTime
from utils import build_menu


load_dotenv('.env')

client = pymongo.MongoClient(os.getenv("mongodb_connection"))
db = client["LuxBusBot"]
users = db["users"]
favs = db["favourites"]
stations = db["stations"]
logs = db["logs"]


main_menu_keyboard = [InlineKeyboardButton('Search by Bus Number', callback_data='searchBusNo'), InlineKeyboardButton(
    'Search by Stop', callback_data='searchStop'), InlineKeyboardButton('Favourites', callback_data='checkFavs'), InlineKeyboardButton('Help', callback_data='help')]

footer = InlineKeyboardButton('Main Menu', callback_data='startover')

def log(chat_id, data, func, level):
    # Logging function
    
    timestamp = datetime.now()
    logs.insert_one({"timestamp": timestamp, "chat_id": chat_id, "func": func, "data": data, "level": level})


def start(update, context):
    log(update.message.chat_id, "start", "start", "debug")
    start_rmarkup = InlineKeyboardMarkup(
        build_menu(main_menu_keyboard, n_cols=2))

    update.message.reply_text(
        text='Welcome to the Lux Bus Telegram Bot. Please select from the options below.', reply_markup=start_rmarkup)


def start_over(update, context):
    query = update.callback_query
    query.answer()
    log(query.message.chat_id, query.data, "start_over", "debug")
    
    start_rmarkup = InlineKeyboardMarkup(
        build_menu(main_menu_keyboard, n_cols=2))

    query.edit_message_text(
        text='Welcome back to the beginning. Please select from the options below.', reply_markup=start_rmarkup)


def searchBusNo(update, context):
    query = update.callback_query
    query.answer()
    log(query.message.chat_id, query.data, "searchBusNo", "debug")

    query.message.reply_text(
        text='What\'s the number of the bus that you want to check?')


def searchStop(update, context):
    query = update.callback_query
    query.answer()
    log(query.message.chat_id, query.data, "searchStop", "debug")

    query.message.reply_text(text='What stop do you want to check?')


def selectResults(update, context):
    msg = update.message.text.title()
    log(update.message.chat_id, msg, "selectResults", "debug")

    if len(msg) < 4:
        # If message is under 4 characters, assumes it is a number.
        # Shortest station is Bois. Fix might be required.

        unique_destinations = stations.find(
            {"line": str(msg)}).distinct("destination")
        if len(unique_destinations) == 0:
            log(update.message.chat_id, msg, "selectResults", "warning")
            update.message.reply_text(
                text="That bus doesn't exist in our database. Try with a different one.")
        else:
            busno_keyboard = []
            for destination in unique_destinations:
                busno_keyboard.append([InlineKeyboardButton(str(
                    msg) + ' towards ' + destination, callback_data=msg + '-' + destination + '-getStops')])
            busno_keyboard.append([footer])

            busno_rmarkup = InlineKeyboardMarkup(busno_keyboard)

            update.message.reply_text(
                text='Which one of these?', reply_markup=busno_rmarkup)
    else:
        unique_stations = stations.find(
            {"stop": {"$regex": ".*" + msg + ".*", "$options": "i"}}).distinct("stop")
        if len(unique_stations) == 0:
            log(update.message.chat_id, msg, "selectResults", "warning")
            update.message.reply_text(
                text='No station by that name exists in our database. Try a different one.')
        else:
            station_name_keyboard = []
            for station in unique_stations:
                station_id = stations.find_one({"stop": station})["station_id"]
                station_name_keyboard.append([InlineKeyboardButton(
                    station, callback_data='undefined-' + str(station_id) + '-getStation')])

            station_name_keyboard.append([footer])
            station_name_rmarkup = InlineKeyboardMarkup(station_name_keyboard)

            update.message.reply_text(
                text='Which one of these?', reply_markup=station_name_rmarkup)


def getStops(update, context):
    # Fetches the Stops where the selected Bus passes

    query = update.callback_query
    query.answer()
    log(query.message.chat_id, query.data, "getStops", "debug")

    line = query.data.split('-')[0]
    destination = query.data.split('-')[1]

    unique_stops = stations.find(
        {"line": str(line), "destination": destination}).distinct("stop")

    stops_keyboard = []
    for stop in unique_stops:
        station_id = stations.find_one({"stop": stop})["station_id"]
        stops_keyboard.append(InlineKeyboardButton(
            stop, callback_data=line + '-' + str(station_id) + '-getStation'))

    stops_rmarkup = InlineKeyboardMarkup(
        build_menu(stops_keyboard, n_cols=2, footer_buttons=footer))

    query.edit_message_text(
        text='Which station do you want to check?', reply_markup=stops_rmarkup)


def getStation(update, context):
    query = update.callback_query
    query.answer()
    log(query.message.chat_id, query.data, "getStation", "debug")

    chat_id = query.message.chat_id
    line = str(query.data.split('-')[0])
    station_id = query.data.split('-')[1]

    result = getRealTime.main(station_id, line)
    result = result.head(5)
    # Currently fetching the top 5 results. A higher number might be required
    # for stations like Hamilius or Gare to avoid having
    # to do a second search with only the bus the person wants
    if result.empty:
        log(query.message.chat_id, query.data, "getStops", "warning")
        text = "No bus " + line + " in the near future or the line has been deprecated."
    else:
        text = "Next Bus:\n"
        for n in range(0, result.shape[0]):
            text += "Bus " + str(result.iat[n, 0]) + " heading to " + result.iat[n, 1] + " will depart in " + str(
                result.iat[n, 3]) + " minutes at " + result.iat[n, 2] + ". \n"
        text += "Last updated at " + datetime.now().strftime("%H:%M:%S")

    if favs.find_one({"chat_id": chat_id, "station_id": int(station_id), "line": line}):
        station_keyboard = [[InlineKeyboardButton('Check Again', callback_data=line + '-' + str(station_id) + '-getStation')], [
            InlineKeyboardButton('Remove from Favourites', callback_data='rem-' + line + '-' + str(station_id) + '-changeFavs')], [footer]]
    else:
        station_keyboard = [[InlineKeyboardButton('Check Again', callback_data=line + '-' + str(station_id) + '-getStation')], [
            InlineKeyboardButton('Add to Favourites', callback_data='add-' + line + '-' + str(station_id) + '-changeFavs')], [footer]]

    station_rmarkup = InlineKeyboardMarkup(
        station_keyboard)

    query.edit_message_text(text=text, reply_markup=station_rmarkup)


def checkFavs(update, context):
    query = update.callback_query
    query.answer()
    log(query.message.chat_id, query.data, "checkFavs", "debug")

    chat_id = query.message.chat_id

    if favs.count_documents({"chat_id": chat_id}) != 0:
        favs_keyboard = []
        for fav in favs.find({"chat_id": chat_id}):
            station_id = fav['station_id']
            station_name = stations.find_one(
                {"station_id": station_id})["stop"]
            line = fav["line"]
            if line == 'undefined':
                favs_keyboard.append(InlineKeyboardButton(
                    station_name, callback_data=line + '-' + str(station_id) + '-getStation'))
            else:
                favs_keyboard.append(InlineKeyboardButton(
                    line + " out of " + station_name, callback_data=line + '-' + str(station_id) + '-getStation'))

        favs_rmarkup = InlineKeyboardMarkup(build_menu(
            favs_keyboard, n_cols=2, footer_buttons=footer), resize_keyboard=True)
        query.edit_message_text(
            text="Here are your favourites:", reply_markup=favs_rmarkup)

    else:
        noFavs_rmarkup = InlineKeyboardMarkup(
            [[footer]])
        query.edit_message_text(
            text="You don't have any favourites yet. Add them next time you search for a stop/bus.", reply_markup=noFavs_rmarkup)


def changeFavs(update, context):
    query = update.callback_query
    query.answer()
    log(query.message.chat_id, query.data, "changeFavs", "debug")

    chat_id = query.message.chat_id
    action = str(query.data.split('-')[0])
    line = str(query.data.split('-')[1])
    station_id = str(query.data.split('-')[2])

    if action == 'add':
        favs.insert_one({"chat_id": chat_id, "line": line,
                        "station_id": int(station_id)})
        station_keyboard = [[InlineKeyboardButton('Check Again', callback_data=line + '-' + str(station_id) + '-getStation')], [
            InlineKeyboardButton('Remove from Favourites', callback_data='rem-' + line + '-' + str(station_id) + '-changeFavs')], [footer]]

        station_rmarkup = InlineKeyboardMarkup(station_keyboard)

        result = getRealTime.main(station_id, line)
        result = result.head(5)
        if result.empty:
            log(query.message.chat_id, query.data, "changeFavs", "warning")
            text = "No bus " + line + " in the near future or the line has been deprecated."
        else:
            text = "Next Bus:\n"
            for n in range(0, result.shape[0]):
                text += "Bus " + str(result.iat[n, 0]) + " heading to " + result.iat[n, 1] + " will depart in " + str(
                    result.iat[n, 3]) + " minutes at " + result.iat[n, 2] + ". \n"
            text += "Last updated at " + datetime.now().strftime("%H:%M:%S")

        query.edit_message_text(
            text="The station/bus has been added.\n" + text, reply_markup=station_rmarkup)
    else:
        favs.delete_one({"chat_id": chat_id, "line": line,
                        "station_id": int(station_id)})
        station_keyboard = [[InlineKeyboardButton('Check Again', callback_data=line + '-' + str(station_id) + '-getStation')], [
            InlineKeyboardButton('Add to Favourites', callback_data='add-' + line + '-' + str(station_id) + '-changeFavs')], [footer]]

        station_rmarkup = InlineKeyboardMarkup(
            station_keyboard)

        result = getRealTime.main(station_id, line)
        result = result.head(5)
        if result.empty:
            log(query.message.chat_id, query.data, "changeFavs", "warning")
            text = "No bus " + line + " in the near future or the line has been deprecated."
        else:
            text = "Next Bus:\n"
            for n in range(0, result.shape[0]):
                text += "Bus " + str(result.iat[n, 0]) + " heading to " + result.iat[n, 1] + " will depart in " + str(
                    result.iat[n, 3]) + " minutes at " + result.iat[n, 2] + ". \n"
            text += "Last updated at " + datetime.now().strftime("%H:%M:%S")

        query.edit_message_text(
            text="The station/bus has been removed.\n" + text, reply_markup=station_rmarkup)


def help(update, context):
    query = update.callback_query
    query.answer()
    log(query.message.chat_id, query.data, "help", "debug")

    help_keyboard = [[InlineKeyboardButton(
        'GitHub Link', url='https://github.com/hugoncosta/luxbus-telegram-bot/')], [footer]]

    help_rmarkup = InlineKeyboardMarkup(help_keyboard)

    query.edit_message_text(
        text="Simple bot to check Real Time data from public busses and trams in Luxembourg. For more info, check the GitHub repo.", reply_markup=help_rmarkup)


def main():
    updater = Updater(token=os.getenv('bot_api'), use_context=True)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(
        searchBusNo, pattern='^searchBusNo$'))
    dispatcher.add_handler(CallbackQueryHandler(
        searchStop, pattern='^searchStop$'))
    dispatcher.add_handler(CallbackQueryHandler(
        getStops, pattern='^(.|\n)*?-getStops$'))
    dispatcher.add_handler(CallbackQueryHandler(
        getStation, pattern='^(.|\n)*?-getStation$'))
    dispatcher.add_handler(CallbackQueryHandler(
        changeFavs, pattern='^(.|\n)*?-changeFavs$'))
    dispatcher.add_handler(CallbackQueryHandler(
        checkFavs, pattern='^checkFavs$'))
    dispatcher.add_handler(MessageHandler(Filters.text, selectResults))
    dispatcher.add_handler(CallbackQueryHandler(
        start_over, pattern='^startover$'))
    dispatcher.add_handler(CallbackQueryHandler(
        help, pattern='^' + 'help' + '$'))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
