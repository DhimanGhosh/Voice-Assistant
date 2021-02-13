import numpy as np
import pandas as pd
import speech_recognition as sr
import pyttsx3
import wikipedia
import webbrowser
import requests
import json
import string
import os
import sys
import shutil
import platform
import subprocess
import re
import pygame
import time
import urllib
import urllib.request as request
from urllib.request import urlopen
from urllib.parse import quote
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from playsound import playsound
from gtts import gTTS
from random import randint
from datetime import datetime
from glob import glob
from time import sleep
from mutagen.mp3 import MP3
from Levenshtein import ratio
from difflib import SequenceMatcher
from youtube_search import YoutubeSearch
from .Custom_Modules import Modules
#from tempfile import TemporaryFile


if platform.system() == 'Linux':
    pass
elif platform.system() == 'Windows':
    from Utils.Stream import Gaana
    from winsound import Beep

root_dir = os.path.realpath('Voice-Assistant')
if root_dir.split(os.sep)[-2] == 'Voice-Assistant':
    root_dir = os.sep.join(root_dir.split(os.sep)[:-1])
utils_dir = root_dir + os.sep + 'Utils' + os.sep
assets_dir = root_dir + os.sep + 'assets' + os.sep
datasets_dir = assets_dir + 'datasets' + os.sep
cache_dir = assets_dir + 'cache' + os.sep
tmp_dir = cache_dir + 'tmp_dir' + os.sep

class VA:
    def __init__(self):
        self.VA_NAME = 'ji'
        self._mod = Modules()

        try:
            os.mkdir(cache_dir)
            # print('Cache folder created')
        except FileExistsError:
            pass
            # print('Cache folder already present')

        try:
            os.mkdir(tmp_dir)
            # print('tmp folder created')
        except FileExistsError:
            pass
            # print('tmp folder already present')

        try:
            for f in glob(assets_dir + '*.exe'):
                print(f'Copying "{f}" to {tmp_dir}')
                shutil.copy(f, tmp_dir)
        except Exception:
            pass
            # print(f'EXE already copied to {tmp_dir}')

    def _speak(self, text):
        #os.system(f'espeak {text}')
        tts = gTTS(text=text, lang='en')  # TODO: Taking too much time saving to a file and reading out
        #f = TemporaryFile()
        #tts.write_to_fp(f)
        #f.close()
        filename = 'voice.mp3'
        tts.save(filename)
        playsound(filename)
        os.remove(filename)

    def __wish_me(self):
        hour = int(datetime.now().hour)
        if 0 <= hour < 12:
            self._speak('Good Morning!')
        elif 12 <= hour < 18:
            self._speak('Good Afternoon!')
        else:
            self._speak('Good Evening!')
        self._speak('How may I help You?')

    def _take_command(self, waiting_for_query=''):  ## TODO: Execution Stopped (hanged)
        """
        NOTE: <To Solve HANG issue>
        Create 2 threads: for handling the mic voice commands
        1. if retries exceed a THRESHOLD_VALUE=5 ======= kill it
        2. it waits for thread 1 to be killed ======= then it will start
        <Cycle interchangeably REPEATS>
        """

        ## TODO: Create 2 threads (one for handling the mic voice commands) && (amother will wait for its expire)
        r = sr.Recognizer()
        with sr.Microphone() as source:
            #r.adjust_for_ambient_noise(source)  # Ambient Noise Cancellation; use only when in a noisy background
            '''
            Intended to calibrate the energy threshold with the ambient energy level. Should be used on periods of audio without speech - will stop early if any speech is detected.
            '''
            ## TODO: Add what the mic is waiting to hear from you
            print(f'Waiting for: {waiting_for_query}\nListening...')  # TODO: execute in seperate threads; if one gets hanged (overloaded) kill that; start new ['DEBUGGING' purpose only] <--> comment it when 'using'
            r.pause_threshold = 1  # let it be as '1'
            r.energy_threshold = 100  # Default: 300 (now less energy required while speaking)
            audio = r.listen(source)
        try:
            print('Recognizing...')
            query = r.recognize_google(audio, language='en-in')
            print(f'User Said: {query}\n')
        except Exception:
            print('Say that again please...')
            return 'none'
        return query.lower()

    def start_VA(self):  # Entry point of this 'Voice Assistant'
        self.__wish_me()
        __abilities = _Abilities()

        while True:
            query = self._take_command('Waiting for commands in main thread').lower()
            print(f'query: {query}')

            # Logic for executing tasks based on query ; TODO: use "self.__global_commands" / "self.__music_commands"
            # Call each abilities based on query

            if self._mod.has_any(sentence=query, list_of_words=__abilities.global_commands):
                if 'play ' in query:
                    _Media_Player().pause()
                    player = __abilities.download_and_play_song(query)
                    if player:
                        song, artist = player.get_song_info()
                        self._speak(f'{song} by {artist}. Starting now')
                        player.play()
                    else:
                        self._speak('Sorry Sir! Did not get you!')
                        player.resume()
                        continue
            elif self._mod.has_any(sentence=query, list_of_words=list(__abilities.music_commands.keys())):
                # TODO: Take query for Media Controls ; if not controls but any other information - STOP media and respond to that ; start in separate thread
                pass
            elif self.VA_NAME.lower() in query:
                _Media_Player().pause()

    def _quit_VA(self, query):
        os.chdir(cache_dir)
        shutil.rmtree(tmp_dir, cache_dir)
        hour = int(datetime.now().hour)
        if 0 <= hour <= 18:
            self._speak('Good Bye Sir, Thanks for your time! Have a nice day')
        else:
            if 'good night' in query:
                self._speak('Good Bye Sir, Thanks for your time! Good Night!')
            else:
                self._speak('Good Bye Sir, Thanks for your time!')


class _Media_Player(VA):  # Supports only mp3
    """
    TODO:
        1. Cross playing multiple songs in playlist (total time of prev song -5 before end FADE OUT; total time of next song -5 before start FADE IN)
        2. Show live timer
        3. seek bar
        4. Stop playing music / in Music player control mode after song ends
    """
    REPLAY = False

    def __init__(self, audio_file=assets_dir + 'welcome.mp3'):  # If nothing is found; for the time being; just play the initialised value
        """
        Play, Pause, Stop, Resume, Restart(Stop + Play), Replay <A MODE to restart the song once it finishes>

        forward (+10 seconds), backward (-10 seconds) ---- 'pygame.mixer.music.get_pos' && 'pygame.mixer.music.set_pos'

        volume-up (), volume-down () ---- 'pygame.mixer.music.get_volume()' && 'pygame.mixer.music.set_volume()'

        next, prev -- for playlist playing (for single audio ---- SAY: "That was the last song" <resume_playing>)
        """
        super().__init__()
        self.__audio_file = audio_file
        self.__audio = MP3(self.__audio_file)
        self.__audio_sample_rate = self.__audio.info.sample_rate
        self.__audio_channels = self.__audio.info.channels
        self.__audio_length = self.__audio.info.length
        self.__song_name = audio_file.split('\\')[-1]
        self.__volume = 0.5
        self.__songtracks = os.listdir()
        self.__playlist = []
        for track in self.__songtracks:
            self.__playlist.append(track)

    def play(self):
        if pygame.mixer.get_init():
            pygame.mixer.quit()  # quit it, to make sure it is reinitialized
        pygame.mixer.pre_init(frequency=self.__audio_sample_rate, size=-16, channels=self.__audio_channels,
                              buffer=4096)
        pygame.mixer.init()
        pygame.mixer.music.load(self.__audio_file)
        pygame.mixer.music.play()
        print(self.__song_name + " ---- Playing")

    def pause(self):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
        print("Playback Paused")

    def resume(self):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.unpause()
        print(self.__song_name + " ---- Resumed")

    def stop(self):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            # pygame.mixer.music.fadeout(5)
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        print("Stopped")

    def replay(self):
        self.REPLAY = not self.REPLAY
        if self.REPLAY:
            print(f'{self.__audio_file} ---- is set to REPLAY')
        else:
            print(f'{self.__audio_file} ---- is set NOT to REPLAY')
        return self.REPLAY

    def restart(self):
        self.stop()
        self.play()
        print(self.__song_name + " ---- Restarting")

    def volume(self, mode):
        if mode == 'up':
            self.__volume += 0.1
        elif mode == 'down':
            self.__volume -= 0.1
        elif mode == 'max':
            self.__volume = 1.0
        elif mode == 'min':
            self.__volume = 0.1
        elif mode == 'mute':
            self.__volume = 0.0
        pygame.mixer.music.set_volume(self.__volume)

    def current_time(self):
        timer = 0
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            timer = pygame.mixer.music.get_pos()
            timer = int(timer // 1000)
        return timer

    def get_song_info(self):  # Do google search with the "song name" and get the song info
        return self._mod.get_song_info(self.__song_name)

    def __un_used_functions(self):
        pygame.mixer.music.rewind()  # restart music
        # pygame.mixer.music.queue  # queue a sound file to follow the current


class _Youtube_mp3(VA):  # Download songs from youtube and create a mp3 file of that
    def __init__(self):
        """
        Overview:
            Throw me a song query... I will play it for you!

        Description:
            That also with the help of YouTube. Now guess my library size. LOL!
        """
        super().__init__()
        self.__player = _Media_Player
        self.playlist = []

    def get_media(self, song_search, number=0):  # number = song_number to play in the list of search results
        max_search = 1
        valid_song = False
        song_name_recv = ''
        player = self.__player()

        if number == 0:  # direct play; doesn't involve user
            self._speak('Searching Song...')
            cache_search = self.__play_media_from_cache(song_search)
            if not cache_search:
                songs_list = self.__url_search(song_search, max_search)  ##NOTE: add 'search_more' parameter in 'url_search()' that will hold an integer of 'self.__retry_list'
                print(f'songs_url_list: {songs_list}')
                if songs_list:
                    for sl_no, url in songs_list.items():
                        os.chdir(tmp_dir)
                        song_name_recv = self.__download_mp3(song_search, url)  # TODO: {song_name: saved_name} ; need to store this dict as json file for cache search
                        os.chdir(cache_dir)
                        if song_name_recv and [self.__play_media_from_cache(song_name_recv.split('.')[0])]:  # valid song found
                            valid_song = True
                            break
                        else:
                            continue
                    if valid_song:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                        player = self.__play_media(song_name_recv)
                    else:  # list of 5 searches exhausted
                        pass  # self.__retry_list += 1 (----if the first 5 searches doesn't contain any media file; then go for next 5 searches----)
                else:
                    player = None
                    pass  # Say Again
            else:  # Play from cache
                self._speak('Playing from your cache')
                shutil.rmtree(tmp_dir, ignore_errors=True)
                player = self.__play_media(cache_search)

        return player

    def __url_search(self, search_string, max_search):  # search youtube and returns list of 5 links
        dict = {}
        results = YoutubeSearch(search_string + ' full audio lyrics', max_results=max_search).to_dict()
        for i in range(len(results)):
            dict[i] = 'https://www.youtube.com' + results[i]['url_suffix']
        return dict

    def __clean_file_name(self, name, song_search):  # TODO: match the song search name from the downloaded name ; pass song search term for matching
        print(f'downloaded song name before cleanup: {name}')
        artist_album_name = ''
        if 'by' in song_search:
            artist_album_name = song_search.split('by')[-1].strip()
            song_search = song_search.split('by')[0].strip()
        elif 'from' in song_search:
            artist_album_name = song_search.split('from')[-1].strip()
            song_search = song_search.split('from')[0].strip()

        if not artist_album_name:
            artist_album_name = self._mod.get_song_info(song_search)[-1]
        artist_album_name = '-'.join(artist_album_name.split())
        cleaned_name = self._mod.words_in_Title_Case(self._mod.process_downloaded_song_name(name, song_search))
        cleaned_name = '-'.join(cleaned_name.split()) + '_' + artist_album_name + '.' + name.split('.')[-1]
        print(f'Song name after similarity check and cleaned: {cleaned_name}')
        return cleaned_name

    def __download_mp3(self, song_search, url):  # (in folder 'assets\cache')
        # TODO: - Create a 'config.py' file... from there get the value of cache size
        #  1. Restrict Cache storage total size ; replace the oldest (first) saved file with the latest search if cache full ; FIFO (queue)
        os.chdir(tmp_dir)
        try:
            subprocess.call(f'python -m youtube_dl --restrict-filenames --ignore-errors -x --audio-format mp3 {url}')
            sleep(2)
            if glob('*.mp3') or glob('*.webm') or glob('*.m4a'):  # song found
                print('Song Downloaded!')
                song_name = ''
                if glob('*.webm'):
                    downloaded_song_name = glob('*.webm')[0]
                    cleaned_name = self.__clean_file_name(downloaded_song_name, song_search)
                    os.rename(downloaded_song_name, cleaned_name)
                    downloaded_song_name = glob('*.webm')[0]
                    song_name = downloaded_song_name.split('.')[0] + '.mp3'
                    command = f"ffmpeg -i {downloaded_song_name} -vn -ar 44100 -ac 2 -b:a 192k -y {song_name}"
                    subprocess.call(command)
                elif glob('*.m4a'):
                    downloaded_song_name = glob('*.m4a')[0]
                    cleaned_name = self.__clean_file_name(downloaded_song_name, song_search)
                    os.rename(downloaded_song_name, cleaned_name)
                    downloaded_song_name = glob('*.m4a')[0]
                    song_name = downloaded_song_name.split('.')[0] + '.mp3'
                    command = f'ffmpeg -i {downloaded_song_name} -codec:v copy -codec:a libmp3lame -q:a 2 -y {song_name}'
                    subprocess.call(command)
                elif glob('*.mp3'):
                    downloaded_song_name = glob('*.mp3')[0]
                    cleaned_name = self.__clean_file_name(downloaded_song_name, song_search)
                    os.rename(downloaded_song_name, cleaned_name)
                    song_name = glob('*.mp3')[0]
                    shutil.copy(song_name, cache_dir)
                    os.chdir(cache_dir)
                os.chdir(tmp_dir)
                return song_name
            else:
                print('Song not downloaded!')
                return None
        except Exception:  # (HTTPError) # url is not a song
            print('exception in song processing!')
            return None

    def __play_media(self, song_name):  # Play media based on url; since .mp3 will already be downloaded in 'test_url()'; no need to download it again; ---- Just Returns '_Media_Player' object with loaded song----
        os.chdir(cache_dir)
        player = self.__player(audio_file=cache_dir + song_name)
        return player

    def __play_media_from_cache(self, query):  # String Similarity using SequenceMatcher
        """
        For Cache storing:
        1. Check if the name of the song is there in cache folder or not.
        2. If it is there play from cache or download it and play

        TODO: 'store' them && 'encrypt' them --------- 'decrypt' while using
        """
        os.chdir(cache_dir)
        artist_album_name = ''
        cache_songs = glob('*.mp3')
        if cache_songs:
            if 'by' in query:
                artist_album_name = query.split('by')[-1]
                query = query.split('by')[0]
            elif 'from' in query:
                artist_album_name = query.split('from')[-1]
                query = query.split('from')[0]

            # TODO:
            #  1. if multiple song occurance is present and artist/album name not asked ; play any of available songs from cache ; do not download
            #  2. if single song is present but artist/album not asked ; play that. If artist/album matched with google search Play that ; Else download

            if not artist_album_name:
                artist_album_name = self._mod.get_song_info(query)[-1]
            artist_album_name = '-'.join(artist_album_name.split())
            query = '-'.join(query.strip().split())
            query = query + '_' + artist_album_name.lower()
            for i in range(len(cache_songs)):
                song = cache_songs[i]
                song = song.split('.')[0].lower()
                sim = str(self._mod.similarity(song, query))
                match_val = float(sim.split('.')[0] + '.' + sim.split('.')[-1][:1])
                if match_val > 0.8:
                    print('Matched!')
                    return cache_songs[i]

        print('No Match!')
        return None

    def __add_playlist(self, search_query):
        url = self.__url_search(search_query, max_search=1)
        self.playlist.append(url)


class _Vocabulary(VA):  # Reads data from datasets; Store personalised data
    def __init__(self):
        super().__init__()
        self.SYNONYMS = {
            'PLAY': ['play', 'begin'],  # This will act as 'Replay' (when called while playing a song)
            'PAUSE': ['pause', 'hold', 'break', 'suspend', 'interrupt'],
            'RESUME': ['resume'],
            'REPLAY': ['replay', 'repeat', 'reply'],
            # 'reply' is added since 'speech_recognition' sometimes hear 'reply' when I say 'replay'... LOL!
            'RESTART': ['restart', 'beginning', 'starting', 'start from ', 'play from '],
            'STOP': ['stop', 'close', 'finish', 'end', 'terminate', 'wind up', 'windup'],
            'VOLUME UP': ['up', 'volume up', 'increase volume', 'increase'],
            'VOLUME DOWN': ['down', 'volume down', 'decrease volume', 'decrease'],
            'MAX VOLUME': ['max', 'max volume', 'full volume', 'loud volume'],
            'MIN VOLUME': ['min', 'min volume', 'low volume', 'whisper'],
            'MUTE': ['mute', 'no volume', 'no sound', 'silent']
        }


class _Abilities(VA):
        """
            Overview:
                The 'Abilities' that I have to perform various tasks.

            Myself:
                My 'Abilities' are very limited.

            NOTE: A task for you... "Please train me with new 'Abilities' so that I can stand in the real world"

            NOTE: Add support for wikipedia extract for information like ('Bollywood movies releasing next month')

            NOTE: If 'another / again' joke is asked; SAY it;; or else pass this 'query' to main 'Thread' so that ita can execute any of its tasks
                {Don't use this approach;; or else it has to be implemented on every sub-tasks}

            Instead:
                1. Go back to main thread
                2. If 'another / again' is asked
                3. It will check what was the last thing asked <stored in a list[]>
                4. Based on that; it will call the respective function

            NOTE: It can conflict with the feature 'Abilities.play_song_from_last_search(<webpage>)'. Make the commands unique [SMARTer recognision]
        """

        def __init__(self):
            super().__init__()
            self.__youtube = _Youtube_mp3()
            self._vocabulary = _Vocabulary()
            self._global_commands = [
                'play ', 'open ', 'bye'
            ]  # This will have global thread commands
            self._music_commands = {
                'play': self._vocabulary.SYNONYMS['PLAY'],
                'pause': self._vocabulary.SYNONYMS['PAUSE'],
                'resume': self._vocabulary.SYNONYMS['RESUME'],
                'replay': self._vocabulary.SYNONYMS['REPLAY'],
                'restart': self._vocabulary.SYNONYMS['RESTART'],
                'stop': self._vocabulary.SYNONYMS['STOP'],
                'volume up': self._vocabulary.SYNONYMS['VOLUME UP'],
                'volume down': self._vocabulary.SYNONYMS['VOLUME DOWN'],
                'max volume': self._vocabulary.SYNONYMS['MAX VOLUME'],
                'min volume': self._vocabulary.SYNONYMS['MIN VOLUME'],
                'mute': self._vocabulary.SYNONYMS['MUTE']
            }  # This will have music thread commands

        def stream_song(self, query):
            music_name = ' '.join(query.split()[1:])  # Play <song_name_query>
            query_string = urllib.parse.urlencode({"search_query": music_name})
            formatUrl = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)

            search_results = re.findall(r"watch\?v=(\S{11})", formatUrl.read().decode())
            clip = requests.get("https://www.youtube.com/watch?v=" + "{}".format(search_results[0]))
            clip1 = "https://www.youtube.com/watch?v=" + "{}".format(search_results[0])

            inspect = BeautifulSoup(clip.content, "html.parser")
            yt_title = inspect.find_all("meta", property="og:title")

            print(f'Playing: {yt_title}')
            os.system(f"mpv --no-video {clip1} > output.txt")

        def download_and_play_song(self, query):
            music_name = ' '.join(query.split()[1:])  # play <song_name>
            music_player = self.__youtube.get_media(music_name)

            if music_player:
                return music_player
            else:
                return None

        def control_media_playback(self):  # Start in separate thread
            pass

        @property
        def global_commands(self):
            return self._global_commands

        @property
        def music_commands(self):
            return self._music_commands


