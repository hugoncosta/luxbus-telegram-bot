# Luxembourg Bus Telegram Bot

The Luxembourg Bus Telegram Bot is a simple Telegram Bot to get the most accurate data regarding next bus/tram within a specific station.
Uses the (un)official vdl RealTime API to get the data and then transforms it into a standard output.
Originated from my frustration that buses never follow the schedule and the fact the website randomly selects to give either minutes left
or "bus will leave at xx:yy", which leads to unnecessary math.

## Features

- Search by Bus Number or by Station name
- Get the latest schedules in a consistent output
- Quickly access your favourite stations/lines.

## Installation

Clone the repo, create a .env file with bot_api = 'your_bot_token' and mongodb_connection = 'your_mongodb_connection' and run the Lux Bus Telegram Bot file. 

In case the stations have changed, run the scrape_db.py to update the db.

## Future Ideas for Development/Backlog

- [x] Create a db to save the user's favourite stations or station/bus combinations
    - [ ] Alert the user when his normal bus (e.g. the 18 that leaves Station X at 8:30am) is running early/late - very hard to scale properly
- [x] Create a proper db system that isn't based out of csv files (keep in mind that the bot runs continously, functions need to open/insert/save in the same step)
- [ ] Introduce limitations to avoid overburdening the API, as this bot hasn't been blessed by the Grand Duke yet
- [ ] Consider using the ConversationHandler instead of one MessageHandler to seperate both workflows (Search by Bus No and by Station)
- [ ] Create a proper logger to gather usage data for statistics/debug
- [ ] Allow the user to select more than one bus when searching
    - [ ] I want to know when the next bus that passes on my stop will come 
    (from Hamilius I can take bus X and Y thus I only want to see those)
    - [ ] If a certain flag is activated, I will only see the busses that
    pass by my destination (not necessarily my stop but one nearby that I don't mind to walk from)
- [ ] Create user preferences
    - [ ] Allow users to choose how many busses they want to be shown (currently only 5 are given)

## License

MIT
