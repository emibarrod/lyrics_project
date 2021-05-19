from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import time
import re

url1="https://www.billboard.com/charts/hot-100"
url2="https://www.billboard.com/charts/billboard-200"


def get_titles_and_artists_billboard(number):
    if number==100:
        url = url1
    if number==200:
        url = url2
        
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    bs_webpage = BeautifulSoup(webpage,"lxml")
    
    titles = list()
    for i in bs_webpage.find_all('span', class_='chart-element__information__song'):
        titles.append(i.text)

    artists = list()
    for i in bs_webpage.find_all('span', class_='chart-element__information__artist'):
        artists.append(i.text)
        
    return list(zip(titles, artists))

def clean_artist(artist):
    if "(" in artist:
        artist = re.search(r'\((.*?)\)',artist).group(1)
    artist = artist.split(" X ")[0]
    artist = artist.split(" x ")[0]
    artist = artist.split(" Featuring ")[0]
    artist = artist.split(" + ")[0]
    artist = artist.split(" & ")[0]
    artist = artist.split(" (")[0]
    aux = artist.split("The ")
    if len(aux)>1:
        artist = aux[1]
    else:
        artist = aux[0]
    artist = artist.lower().replace(" ", "")
    artist = re.sub("[^0-9a-zA-Z]+", "", artist)
    if artist=="cardib":
        artist = "cardi-b"
    return artist

def clean_song(song):
    song = song.lower()
    song = re.sub("[^0-9a-zA-Z]+", "", song)
    return song