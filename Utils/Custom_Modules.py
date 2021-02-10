from difflib import SequenceMatcher
import requests
from bs4 import BeautifulSoup
import re
import Settings


class Modules:
    def __init__(self):
        self.__settings = Settings

    def get_app_settings(self, key_word):
        return self.__settings.parameters[key_word.upper()]

    def set_default_param_as_user(self):
        self.__settings.user_parameters = self.__settings.parameters

    def similarity(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def process_downloaded_song_name(self, song_string, search_text):
        print(f'processing song name')
        s = song_string.replace('_', ' ')
        s = s.replace('-', ' ')
        s = ' '.join(s.split()).split()
        search_str_words_len = len(search_text.split())
        for i in range(len(s) - search_str_words_len):
            extracted_string = ' '.join(s[i:i + search_str_words_len]).lower()
            sim = str(self.similarity(extracted_string, search_text))
            match_val = float(sim.split('.')[0] + '.' + sim.split('.')[-1][:2])
            if match_val > 0.6:
                return extracted_string
        return None

    def words_in_Title_Case(self, s):
        s = s.split()
        s = [x.title() for x in s]
        s = ' '.join(s)
        return s

    def get_song_info(self, song_name):  # Do google search with the "song name" and get the song info
        search = f"song {song_name} artist name"
        url = f"https://www.google.com/search?&q={search}"
        req = requests.get(url)
        page = BeautifulSoup(req.text, "html.parser")
        song_artist = page.find("div", class_='BNeawe').text
        if self.similarity(song_artist, song_name) > 0.7:
            try:
                song_artist = page.find("div", class_='am3QBf').text
                print(f'1: {song_artist}')
            except:
                song_artist = page.find("div", class_='BNeawe').text
                print(f'2: {song_artist}')
            if len(song_artist) > 20:
                song_artist = page.find("div", class_='rlc__slider-page').text
                print(f'3: {song_artist}')
        regex = re.compile('[^a-zA-Z]')
        song_artist = regex.sub('-', song_artist)
        song_info = (song_name.split('.')[0], song_artist)
        return song_info

    def has_any(self, sentence, list_of_words, case_sensitive=False):
        """
        if any of 'list_of_words' is present in 'sentence'
        """
        for word in list_of_words:
            if case_sensitive:
                if word in sentence:
                    return True
            else:
                if word.lower() in sentence.lower():
                    return True
        return False
