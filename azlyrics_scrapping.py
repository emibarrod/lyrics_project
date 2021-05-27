import os, os.path
from billboard_scrapping import get_titles_and_artists_billboard, clean_artist, clean_song
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen, ProxyHandler, build_opener
import time
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.query import Every
from whoosh.index import create_in, open_dir, exists_in
from whoosh.qparser import QueryParser
from shutil import rmtree
import re
from whoosh.query import Phrase

base_url = 'https://www.azlyrics.com/'
headers = {'User-Agent':'Mozilla/5.0'}

def get_song_data_from_url(url):
    try:
        req = Request(url, headers=headers)
        #req.set_proxy(proxy_host, 'http')
        webpage = urlopen(req).read()
        bs_webpage = BeautifulSoup(webpage,"lxml")
    except:
        print('exception at url: {}'.format(url))
        return None
        
    title = bs_webpage.find_all('b')[1].text
    artist = bs_webpage.find('h2').find('b').text
    lyrics = bs_webpage.find_all('div', attrs={'class': None})[1].text
    
    try:
        album = bs_webpage.find('div', class_='songinalbum_title').text
    except AttributeError:
        album = ""
    
    cleaning = Cleaning()
    title = cleaning.title(title)
    lyrics = cleaning.lyrics(lyrics)
    full_lyrics = cleaning.full_lyrics(lyrics)
    
    if album=="You May Also Like":
        album = ""
    if album!="":
        album = cleaning.album(album)
    
    artist = " ".join(artist.split(" ")[:-1])

    
    data = {
        'title': title,
        'artist': artist,
        'lyrics': lyrics,
        'full_lyrics': full_lyrics,
        'album': album,
        'url': url
    }
    
    return data

def create_schema():
    schema = Schema(url=ID(),
                    title=TEXT(stored=True),
                    artist=TEXT(stored=True),
                    full_lyrics=TEXT(stored=True, phrase=True),
                    lyrics=TEXT(stored=True),
                    album=TEXT(stored=True))
    return schema

def create_or_open_index(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)
    if exists_in(directory):
        index = open_dir(directory)
    else:
        schema = create_schema()
        index = create_in(directory, schema)
    return index

def index_song(index, song_data):
    writer = index.writer()
    writer.add_document(url=u'{}'.format(song_data['url']),
                        title=u'{}'.format(song_data['title']),
                        artist=u'{}'.format(song_data['artist']),
                        full_lyrics=u'{}'.format(song_data['full_lyrics']),
                        lyrics=u'{}'.format(song_data['lyrics']),
                        album=u'{}'.format(song_data['album']))
    writer.commit(optimize=True)
    
def search_song_by_title(title, index):
    results_list = list()
    qp = QueryParser('title', schema=index.schema)
    q = qp.parse(u"{}".format(title))
    with index.searcher() as searcher:
        results = searcher.search(q)
        for result in results:
            data = {
                'title': result['title'],
                'artist': result['artist'],
                'full_lyrics': result['full_lyrics'],
                'lyrics': result['lyrics'],
                'album': result['album']
            }
            results_list.append(data)
    return results_list

def search_song_by_author(author, index):
    results_list = list()
    qp = QueryParser('author', schema=index.schema)
    q = qp.parse(u"{}".format(title))
    with index.searcher() as searcher:
        results = searcher.search(q)
        for result in results:
            data = {
                'title': result['title'],
                'artist': result['artist'],
                'full_lyrics': result['full_lyrics'],
                'lyrics': result['lyrics'],
                'album': result['album']
            }
            results_list.append(data)
    return results_list

def search_song_by_lyrics(terms, index):
    results_list = list()
    qp = QueryParser('full_lyrics', schema=index.schema)
    q = qp.parse(u'"{}"'.format(terms))
    
    with index.searcher() as searcher:
        results = searcher.search(q)
        for result in results:
            data = {
                'title': result['title'],
                'artist': result['artist'],
                'full_lyrics': result['full_lyrics'],
                'lyrics': result['lyrics'],
                'album': result['album']
            }
            results_list.append(data)
    return results_list

def get_songs_urls_by_letter(letter, limit=None):

    url = base_url+'{}.html'.format(letter)
    final_url_list = list()
    
    def get_urls_by_letter(url):
        req = Request(url)
        webpage = urlopen(req).read()
        bs_webpage = BeautifulSoup(webpage,"lxml")
        divs = bs_webpage.find_all('div', class_='col-sm-6')
        a_list = [i.find_all('a') for i in divs]
        a_list = [base_url+i['href'] for j in a_list for i in j]
        return a_list
    
    urls = get_urls_by_letter(url)
    
    for u in urls[:limit]:
        req = Request(u)
        webpage = urlopen(req).read()
        bs_webpage = BeautifulSoup(webpage,"lxml")
        divs = bs_webpage.find_all('div', class_='listalbum-item')
        a_list = [i.find_all('a') for i in divs]
        final_url_list.append([base_url+i['href'][3:] for j in a_list for i in j])
        time.sleep(20)
    
    final_url_list = [i for j in final_url_list for i in j]
    
    return final_url_list

def index_songs_by_letter(letter, index, limit=None):
    urls = get_songs_urls_by_letter(letter, limit)
    for u in urls:
        song_data = get_song_data_from_url(u)
        print(song_data['title'])
        index_song(index, song_data)
        time.sleep(15)
        
def index_songs_by_artist(artist, index):
    letter = 19 if artist[:1] not in "abcdefghijklmnopqrstuvwxyz" else artist[:1]
    url = base_url+"{}/{}.html".format(letter, clean_artist(artist))
    
    req = Request(url)
    webpage = urlopen(req).read()
    bs_webpage = BeautifulSoup(webpage,"lxml")
    divs = bs_webpage.find_all('div', class_='listalbum-item')
    a_list = [i.find_all('a') for i in divs]
    final_url_list = [base_url+i['href'][3:] for j in a_list for i in j]
    time.sleep(20)
    
    for u in final_url_list:
        song_data = get_song_data_from_url(u)
        print(song_data['title'])
        index_song(index, song_data)
        time.sleep(15)
        
def index_songs_by_billboard(number, index, limit=None):
    song_artist_tuple = get_titles_and_artists_billboard(number)
    
    for song, artist in song_artist_tuple:
        song = clean_song(song)
        artist = clean_artist(artist)
        url = base_url+'lyrics/{}/{}.html'.format(artist, song)
        print(url)
        song_data = get_song_data_from_url(url)
        if song_data is None:
            continue
        print(song_data['title'])
        index_song(index, song_data)
        time.sleep(15)

class Cleaning():
    
    def full_lyrics(self, lyrics):
        lyrics = lyrics.split('\r\n')
        lyrics = [i.replace('\n', ' ')
                  for i in lyrics if i not in ['\n', '\r', '\n\r', '\r\n', '']]
        
        lyrics = ', '.join(lyrics).replace(',', '').replace('.', '').lower()
    
        return lyrics
    
    def lyrics(self, lyrics):
        lyrics = lyrics.replace('\r', '').replace('\n\n', '\n')
        lyrics = lyrics[1:][:-1]
        return lyrics
    
    def title(self, title):
        title = title.replace('"', '')
        return title
    
    def album(self, album):
        print(album)
        if (album!=""):
            album = re.findall(r'"([^"]*)"', album)[0]
        return album