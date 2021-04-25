import os
from dotenv import load_dotenv
import pandas as pd
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from emoji import emojize
import getRealTime

lux_bus = pd.read_csv("lux_bus.csv", encoding='latin1')

main_menu_keyboard = [[InlineKeyboardButton('Search by Bus Number', callback_data='searchBusNo')], [InlineKeyboardButton(
    'Search by Stop', callback_data='searchStop')], [InlineKeyboardButton('Help', callback_data='help')]]


def start(update, context):
    start_rmarkup = InlineKeyboardMarkup(
        main_menu_keyboard, resize_keyboard=True)

    update.message.reply_text(
        text='Welcome to the Lux Bus Telegram Bot. Please select from the options below.', reply_markup=start_rmarkup)


def start_over(update, context):
    query = update.callback_query
    query.answer()

    start_rmarkup = InlineKeyboardMarkup(
        main_menu_keyboard, resize_keyboard=True)

    query.edit_message_text(
        text='Welcome back to the beginning. Please select from the options below.', reply_markup=start_rmarkup)


def searchBusNo(update, context):
    query = update.callback_query
    query.answer()

    query.message.reply_text(
        text='What\'s the number of the bus that you want to check?')


def searchStop(update, context):
    query = update.callback_query
    query.answer()

    query.message.reply_text(text='What stop do you want to check?')


def selectResults(update, context):
    msg = update.message.text.title()

    if len(msg) < 4:
        # If message is under 4 characters, assumes it is a number.
        # Shortest station is Bois. Fix might be required.

        results = lux_bus[lux_bus.line == msg][[
            "line", "destination"]].drop_duplicates()
        if results.empty:
            update.message.reply_text(
                text='That bus doesn\'t exist in our database. Try with a different one.')
        else:
            pairs = list(results.itertuples(index=False, name=None))

            busno_keyboard = []
            for pair in pairs:
                busno_keyboard.append([InlineKeyboardButton(str(
                    pair[0]) + ' towards ' + str(pair[1]), callback_data=str(pair) + '-getStops')])
            busno_keyboard.append([InlineKeyboardButton(
                'Main Menu', callback_data='startover')])

            busno_rmarkup = InlineKeyboardMarkup(
                busno_keyboard, resize_keyboard=False)

            update.message.reply_text(
                text='Which one of these?', reply_markup=busno_rmarkup)
    else:
        results = lux_bus[lux_bus.stop.str.contains(
            msg)]['stop'].unique().tolist()
        if len(results) == 0:
            update.message.reply_text(
                text='No station by that name exists in our database. Try a different one.')
        else:
            station_name_keyboard = []
            for station in results:
                station_name_keyboard.append([InlineKeyboardButton(
                    station, callback_data='undefined-' + station + '-getStation')])
            station_name_keyboard.append(
                [InlineKeyboardButton('Main Menu', callback_data='startover')])

            station_name_keyboard = InlineKeyboardMarkup(
                station_name_keyboard, resize_keyboard=False)

            update.message.reply_text(
                text='Which one of these?', reply_markup=station_name_keyboard)


def getStops(update, context):
    # Fetches the Stops where the selected Bus stops
    # Current UI causes a good amount of scrolling
    # If possible, making them into 2 collumns would be ideal

    query = update.callback_query
    query.answer()

    line = query.data.split('\'')[1]
    destination = query.data.split('\'')[3]

    stops = lux_bus[(lux_bus.line == line) & (
        lux_bus.destination == destination)]["stop"].to_list()

    stops_keyboard = []
    for stop in stops:
        stops_keyboard.append([InlineKeyboardButton(
            stop, callback_data=line + '-' + stop + '-getStation')])
    stops_keyboard.append([InlineKeyboardButton(
        'Main Menu', callback_data='startover')])

    stops_rmarkup = InlineKeyboardMarkup(stops_keyboard, resize_keyboard=False)

    query.edit_message_text(
        text='Which station do you want to check?', reply_markup=stops_rmarkup)


def getStation(update, context):
    query = update.callback_query
    query.answer()

    line = str(query.data.split('-')[0])
    station_name = query.data.split('-')[1]
    station_id = str(lux_bus[lux_bus.stop == station_name]
                     ['station_id'].to_list()[0])

    station_keyboard = []
    station_keyboard.append([InlineKeyboardButton(
        'Check Again', callback_data=line + '-' + station_name + '-getStation')])
    station_keyboard.append([InlineKeyboardButton(
        'Main Menu', callback_data='startover')])

    station_rmarkup = InlineKeyboardMarkup(
        station_keyboard, resize_keyboard=False)

    result = getRealTime.main(station_id, line)
    result = result.head(5)
    # Currently fetching the top 5 results. A higher number might be required
    # for stations like Hamilius or Gare to avoid having
    # to do a second search with only the bus the person wants
    if result.empty:
        text = "No bus " + line + " in the near future or the line has been deprecated."
    else:
        text = "Next Bus:\n"
        for n in range(0, result.shape[0]):
            text += "Bus " + str(result.iat[n, 0]) + " heading to " + result.iat[n, 1] + " will depart in " + str(
                result.iat[n, 3]) + " minutes at " + result.iat[n, 2] + ". \n"

    query.edit_message_text(text=text, reply_markup=station_rmarkup)


def help(update, context):
    query = update.callback_query
    query.answer()

    help_keyboard = [[InlineKeyboardButton('GitHub Link', url='https://github.com/hugoncosta/luxbus-telegram-bot/')], [
        InlineKeyboardButton('Main Menu', callback_data='startover')]]

    help_rmarkup = InlineKeyboardMarkup(help_keyboard, resize_keyboard=True)

    query.edit_message_text(
        text="Simple bot to check Real Time data from public busses and trams in Luxembourg.", reply_markup=help_rmarkup)


def main():
    load_dotenv('.env')
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
    dispatcher.add_handler(MessageHandler(Filters.text, selectResults))
    dispatcher.add_handler(CallbackQueryHandler(
        start_over, pattern='^startover$'))
    dispatcher.add_handler(CallbackQueryHandler(
        help, pattern='^' + 'help' + '$'))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
