import requests
from bs4 import BeautifulSoup
import arrow
import pandas as pd


def main(station_id, busno='undefined'):
    today = arrow.utcnow().to('Europe/Paris').format('YYYY-MM-DD ')

    params = (
        ('station', station_id),
        ('line', ''),
        ('line_id', busno),
    )

    response = requests.get(
        'https://www.vdl.lu/fr/bus/realtime', params=params)
    soup = BeautifulSoup(str(response.json()), "lxml")

    bus_number = []
    destination = []
    time_left = []
    departure = []

    for line in soup.find_all('div', {'class': 'block-layout-content block-station-next-departure-content'})[0].find_all('article'):
        bus_number.append(line.find('div').attrs['class'][1].split("-")[1])
        destination.append(line.find_all('span')[1].get_text().strip())

        time = line.find_all('span')[2].get_text()
        
        if len(time) == 2: # When the time is given in minutes
            if time[0] == '0':
                time = time[1]
            time_left.append(int(time))
            departure.append(arrow.utcnow().to(
                'Europe/Paris').shift(minutes=int(time)).format('HH:mm'))
        else: # When the time is given in hours
            departure.append(time)
            if time[0] == '0' and arrow.now().format('HH')[0] != '0': # To account for overnight searches
                time = arrow.now().shift(days=1).to(
                    'Europe/Paris').format('YYYY-MM-DD ') + time + ' Europe/Paris'
            else:
                time = today + time + ' Europe/Paris'
            diff_min = int((arrow.get(time, 'YYYY-MM-DD HH:mm ZZZ').timestamp() -
                           arrow.now('Europe/Paris').timestamp())/60)
            time_left.append(diff_min)

        dict = {"Bus Number": bus_number, "Destination": destination,
                "Departure": departure, "Time Left": time_left}

    df = pd.DataFrame(dict)
    if busno != 'undefined': # If the search is for a specific bus number. Currently not needed, failsafe if the API decides to change.
        df = df[df["Bus Number"] == busno]
    df = df.drop_duplicates()
    return df


if __name__ == "__main__":
    pass
