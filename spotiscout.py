import os
from flask import Flask, session, request, redirect, render_template, url_for
from flask_session import Session
from dotenv import load_dotenv
import spotipy
import uuid
import asyncio

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

scope = "playlist-read-private playlist-read-collaborative user-top-read user-library-read"

# Set SpotiPy values in environment
app.config.update(
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID"),
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET"),
    SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid')

@app.route('/')
def index():
    if not session.get('user'):
        session.clear()
   
    if not session.get("uuid"):
        # Visitor gets assigned a random UUID if they don't have one.
        session['uuid'] = str(uuid.uuid4())
    



    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope = scope,
                                                cache_handler = cache_handler, 
                                                show_dialog=True)


    # If user gets redirected from Spotify, they will have "code" in payload
    if request.args.get("code"):
        
        auth_manager.get_access_token(request.args.get("code"))
        # await asyncio.gather(        get_artist_background(),
        # get_total_playlists(),
        # get_total_tracks())

        get_artist_background()
        get_total_playlists()
        get_total_tracks()
        get_top_artists()
        get_top_tracks()

        return render_template("index.html")


    # If no token exists, user will be shown default index.html
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return render_template("index.html", auth_url = auth_url)

    # User is signed in, and view with user details will be displayed - All user data in session gets updated
    print("yessirski")
    return render_template("index.html")

@app.route('/profile')
def profile():
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    artists = []
    tracks =  []

    for artist in session["user"]["long_artists"][:3]:
        artists.append(artist)

    for track in session["user"]["long_tracks"][:3]:
        tracks.append(track)

    # TODO Sort Chart.js for Genres

    return render_template("profile.html", artists = artists, tracks = tracks)


@app.route('/logout')
def logout():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))
    return redirect(url_for("index"))


@app.route('/playlists')
def playlists():
    spotify, auth_manager = confirm_authentication()

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user_playlists()

@app.route('/tracks/top', defaults = {'range': 'all_time'})
def top_tracks(range):
    confirm_authentication()

@app.route('/genres/top', defaults = {'range': 'all_time'})
def top_genres(range):
    confirm_authentication()

@app.route('/albums/top', defaults = {'range': 'all_time'})
def top_albums(range):
    confirm_authentication()

@app.route('/artists/top', defaults = {'range': 'all_time'})
def top_artists(range):
    confirm_authentication()

@app.route('/recent', defaults = {'item': 'tracks'})
def recent(item):
    confirm_authentication()

# Functions for getting profile data

def top_artist_background(item: dict):
    """Gets the URL for the artist image

    Args:
        item (dict): Received from Spotify API with data about user's single top artist

    Returns:
        String: URL for top artist's background image
    """
    return item.get("items")[0]["images"][0]["url"]

def get_artist_background():
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    session["user"] = spotify.me()

    # Set top artist image, to use for background in profile
    session["user"]["top_artist_background"] = top_artist_background(spotify.current_user_top_artists(time_range="long_term", limit=1))


def get_total_tracks():
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    track_count = 0
    saved_tracks = spotify.current_user_saved_tracks(limit = 50)

    while saved_tracks['next']:
        saved_tracks = spotify.next(saved_tracks)
        for item in saved_tracks['items']:
            track_count += 1

    session["user"]["track_count"] = track_count


def get_total_playlists():
    print("Get playlists stated")
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    playlist_count = 0
    playlists = spotify.current_user_playlists(limit=50)

    while playlists['next']:
        playlists = spotify.next(playlists)
        for item in playlists['items']:
            playlist_count += 1

    session["user"]["playlist_count"] = playlist_count
    print("get playlists finish")

def get_top_artists():
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)



    short_artists = []
    medium_artists = []
    long_artists = []

    short_term = spotify.current_user_top_artists(time_range = "short_term", limit=50)
    medium_term = spotify.current_user_top_artists(time_range = "medium_term", limit=50)
    long_term = spotify.current_user_top_artists(time_range = "long_term", limit=50)

    rank = 1

    for item in short_term['items']:
        artist = {
            "external_url": item['external_urls']["spotify"],
            "image_url": item["images"][0]["url"], # TODO FIX IMAGE URL
            "name": item["name"],
            "rank": rank
        }
        short_artists.append(artist)
        rank +=1
    rank = 1

    for item in medium_term['items']:
        artist = {
            "external_url": item['external_urls']["spotify"],
            "image_url": item["images"][0]["url"],
            "name": item["name"],
            "rank": rank
        }
        medium_artists.append(artist)
        rank +=1
    rank = 1

    for item in long_term['items']:
        artist = {
            "external_url": item['external_urls']["spotify"],
            "image_url": item["images"][0]["url"],
            "name": item["name"],
            "rank": rank
        }
        long_artists.append(artist)
        rank +=1
    rank = 1

    session["user"]["short_artists"] = short_artists
    session["user"]["medium_artists"] = medium_artists
    session["user"]["long_artists"] = long_artists

def get_top_tracks():
    #TODO POLISH AND FINISH
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    short_tracks = []
    medium_tracks = []
    long_tracks = []

    short_term = spotify.current_user_top_tracks(time_range = "short_term", limit=50)
    medium_term = spotify.current_user_top_tracks(time_range = "medium_term", limit=50)
    long_term = spotify.current_user_top_tracks(time_range = "long_term", limit=50)

    session["user"]["genres"] = {}

    rank = 1
    for item in short_term['items']:
        track = {
            "external_url": item['external_urls']["spotify"],
            "image_url": item["album"]["images"][0]["url"],
            "name": item["name"],
            "artist": item["album"]["artists"][0]["name"],
            "artist_url": item["artists"][0]["external_urls"]["spotify"],
            "rank": rank
        }
        short_tracks.append(track)
        rank +=1
    
    rank = 1
    for item in medium_term['items']:
        track = {
            "external_url": item['external_urls']["spotify"],
            "image_url": item["album"]["images"][0]["url"],
            "name": item["name"],
            "artist": item["album"]["artists"][0]["name"],
            "artist_url": item["artists"][0]["external_urls"]["spotify"],
            "rank": rank
        }
        medium_tracks.append(track)
        rank +=1
    
    rank = 1
    for item in long_term['items']:
        track = {
            "external_url": item['external_urls']["spotify"],
            "image_url": item["album"]["images"][0]["url"],
            "name": item["name"],
            "artist": item["album"]["artists"][0]["name"],
            "artist_url": item["artists"][0]["external_urls"]["spotify"],
            "rank": rank
        }
        long_tracks.append(track)
        rank +=1
    rank = 1

    session["user"]["short_tracks"] = short_tracks
    session["user"]["medium_tracks"] = medium_tracks
    session["user"]["long_tracks"] = long_tracks

def extract_genres(item: dict):
    genres = []

    for genre in item.get("genres"):
        genres.append(genre)
        if genre not in session["user"]["genres"]:
            session["user"]["genres"][genre] = 1

        if genre in session["user"]["genres"]:
            session["user"]["genres"][genre] += 1


    return genres

def calculate_genres(genres: list):
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    genres = {}

    #TODO Loop over top 50 artists, fetch

def confirm_authentication():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope = scope,
                                                cache_handler = cache_handler, 
                                                show_dialog=True)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    return spotipy.Spotify(auth_manager=auth_manager), auth_manager

if __name__ == '__main__':
    app.run(threaded=True)