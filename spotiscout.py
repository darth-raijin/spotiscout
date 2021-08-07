import os
from flask import Flask, session, request, redirect, render_template
from flask_session import Session
from dotenv import load_dotenv
import spotipy
import uuid

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

# Set SpotiPy values in environment
app.config.update(
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID"),
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET"),
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid')

@app.route('/')
def index():
    if not session.get('uuid'):
        # Visitor gets assigned a random UUID if they don't have one.
        session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing playlist-modify-private',
                                                cache_handler =cache_handler, 
                                                show_dialog=True)

    # If user gets redirected from Spotify, they will have "code" in payload
    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    # If no token exists, user will be shown default index.html
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return render_template("index.html")

    # User is signed in, and view with user details will be displayed
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    session["user"] = spotify.me()

    return render_template("index.html")

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
    return redirect('/')


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
def top_albums(range):
    confirm_authentication()

@app.route('/recent', defaults = {'item': 'tracks'})
def recent(item):
    confirm_authentication()

# USED FOR TESTING PURPOSES TODO DELETE AFTER
@app.route('/me')
def current_user():
    spotify = confirm_authentication()

    return spotify.current_user()

def confirm_authentication():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    return spotipy.Spotify(auth_manager=auth_manager), auth_manager

if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT",
                                                   os.environ.get("SPOTIPY_REDIRECT_URI", 5000).split(":")[-1])))