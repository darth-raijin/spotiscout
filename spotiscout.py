from dotenv import load_dotenv
import os
from flask import Flask, request, render_template, url_for, session, redirect
import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth


load_dotenv()

app = Flask(__name__)
app.secret_key =  "Doflamingo"
app.config['SESSION_COOKIE_NAME'] = "Quijote"

@app.route("/")
def root():
    return render_template("index.html")
    # TODO Pass data, based on token validity, call confirm_auth()

@app.route("/login")
def login():
    spotify_oauth = create_spotify_oauth() 
    spotify_auth_url = spotify_oauth.get_authorize_url()
    return redirect(spotify_auth_url)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("root"))

@app.route("/profile")
def user_profile():
    return render_template("profile.html")

@app.context_processor
def is_authenticated():
    return dict(is_auth = confirm_auth())

@app.route("/session")
def get_session():
    print(session)
    return "hell"

@app.route("/me")
def get_user_profile():
    confirm_auth()
    sp = spotipy.Spotify(auth = session.get("token_info").get("access_token"))
    # TODO Create profile, based on current_user()
    # Pass External URL (Spotify), image URL, and Display Name to Template
    
    spotify_profile = sp.current_user()
    profile_dict = {
        "display_name": spotify_profile["display_name"],
        "spotify_url": spotify_profile["external_urls"]["spotify"],
        "follower_total": spotify_profile["followers"]["total"],
        "image_url": spotify_profile["images"][0]["url"],
        "top_artist": None
    }

    session["user_info"] = profile_dict
    return session["user_info"]

@app.route("/redirect")
def auth_receiver():
    print("Redirect received!")
    spotify_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = spotify_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect(url_for("root"))

@app.route("/settings")
def settings():
    return render_template("index.html")


# TRACKS API
@app.route('/tracks/top', defaults = {'range': 'all_time'})
def top_tracks(range):
    confirm_auth()
    spotify = spotipy.Spotify(auth = session.get("token_info").get("access_token"))

    results = []
    iter = 0
    while True:
        offset = iter * 50
        iter += 1
        curGroup = spotify.current_user_saved_tracks(limit=50, offset=offset)['items']
        for idx, item in enumerate(curGroup):
            track = item['track']
            val = track['name'] + " - " + track['artists'][0]['name']
            results += [val]
        if (len(curGroup) < 50):
            break


    return spotify.current_user_saved_tracks(limit=50, offset=offset)['items']

# GENRES API
@app.route('/genres/top', defaults = {'range': 'all_time'})
def top_genres(range):
    return render_template("genres.html")

# RECENT API
@app.route('/recent/', defaults = {'item': 'tracks'})
def recent(item):
    return render_template("recent.html")

# ALBUMS API
@app.route('/albums/top', defaults = {'range': 'alltime'})
def top_albums(range):
    return render_template("album.html")


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = os.getenv('CLIENT_ID'),
        client_secret = os.getenv('CLIENT_SECRET'),
        redirect_uri = url_for("auth_receiver", _external=True),
        scope="user-library-read user-read-recently-played user-top-read playlist-modify-public"
)

def confirm_auth():
    session['token_info'], authorized = get_token()
    session.modified = True
    if not authorized:
        return False
    return True

def get_token():
    token_valid = False
    token_info = session.get("token_info", {})

    if not (session.get('token_info', False)):
        token_valid = False
        return token_info, token_valid

    # Check if session token has expired
    now = int(time.time())
    is_token_expired = session.get('token_info').get('expires_at') - now < 60

    if (is_token_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)