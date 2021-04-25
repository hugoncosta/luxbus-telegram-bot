import requests
import pandas as pd
from bs4 import BeautifulSoup
from functools import lru_cache

@lru_cache(maxsize = 50)
def getDataStation(url):
    DS = requests.get(url)
    soup = BeautifulSoup(DS.text, "lxml")
    return soup.find('div',{"data-component": "Realtime"})["data-station"]

def main():
    urls = []
    lines = []
    destinations = []
    stops = []
    dataStation = []
    alphabet = list(map(chr, range(97, 123)))

    for letter in alphabet:
        response = requests.get('https://www.vdl.lu/fr/se-deplacer/en-bus/horaires-et-depart-en-temps-reel/arrets/' + letter.capitalize())
        soup = BeautifulSoup(response.text, "lxml") 
        print(letter)
        for direction in soup.find_all(class_='panel-list-item'):
            url = 'https://vdl.lu' + direction.find('div', {'role': 'article'})["data-url"]
            urls.append(url)
            stops.append(url.split("/")[-1].replace("-", " ").title())
            lines.append(direction.get_text().replace("\n", "").split("Direction")[0].strip())
            destinations.append(direction.get_text().replace("\n", "").split("Direction")[1].strip())
            dataStation.append(getDataStation(url))
    
    dict = {"stop": stops
            , "line": lines
            , "destination": destinations
            , "url": urls
            , "station_id": dataStation
            }
    
    df = pd.DataFrame(dict)
    
    df.to_csv('lux_bus.csv', index=False, encoding='latin1')

if __name__ == '__main__':
    main()