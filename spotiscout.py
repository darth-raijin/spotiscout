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
    if not session.get("uuid"):
        # Visitor gets assigned a random UUID if they don't have one.
        session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope = scope,
                                                cache_handler = cache_handler, 
                                                show_dialog=True)

    # If user gets redirected from Spotify, they will have "code" in payload
    if request.args.get("code"):
        print("i am here")
        auth_manager.get_access_token(request.args.get("code"))
        # await asyncio.gather(        get_artist_background(),
        # get_total_playlists(),
        # get_total_tracks())
        get_artist_background()
        get_total_playlists()
        get_total_tracks()

        return render_template("index.html")


    # If no token exists, user will be shown default index.html
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return render_template("index.html", auth_url = auth_url)

    # User is signed in, and view with user details will be displayed - All user data in session gets updated
    print("yessirski")
    return render_template("index.html")

def get_artist_background():
    print("Get background stated")
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    session["user"] = spotify.me()

    # Set top artist image, to use for background in profile
    session["user"]["top_artist_background"] = top_artist_background(spotify.current_user_top_artists(time_range="long_term", limit=1))
    print("Get background finished")


def get_total_tracks():
    print("Get tracks stated")
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    track_count = 0
    saved_tracks = spotify.current_user_saved_tracks(limit = 50)

    while saved_tracks['next']:
        saved_tracks = spotify.next(saved_tracks)
        for item in saved_tracks['items']:
            track_count += 1

    session["user"]["track_count"] = track_count
    print("Get track finish")


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



@app.route('/profile')
def profile():
    spotify = confirm_authentication()
    return render_template("profile.html")


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

def top_artist_background(item: dict):
    """Gets the URL for the artist image

    Args:
        item (dict): Received from Spotify API with data about user's single top artist

    Returns:
        String: URL for top artist's background image
    """
    return item.get("items")[0]["images"][0]["url"]


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