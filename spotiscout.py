from dotenv import load_dotenv
import os
from flask import Flask, request, render_template, url_for, session, redirect
import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
from tracks import tracks
from albums import albums
from genres import genres
from recent import recent

load_dotenv()

app = Flask(__name__)
app.secret_key = NotImplemented
app.config['SESSION_COOKIE_NAME'] = NotImplemented
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

# Registering blueprints
app.register_blueprint(tracks)
app.register_blueprint(albums)
app.register_blueprint(genres)
app.register_blueprint(recent)


@app.route("/")
def root():
    return render_template("index.html" )
    # TODO Pass data, based on token validity, call confirm_auth()

@app.route("/login")
def login():
    spotify_oauth = create_spotify_oauth() 
    spotify_auth_url = spotify_oauth.get_authorize_url()
    return redirect(spotify_auth_url)

@app.route("/logout")
def logout():
    return render_template("index.html")

@app.route("/redirect")
def auth_receiver():
    print("Redirect received!")
    spotify_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = spotify_oauth.get_access_token(code)
    session["token_info"] = token_info
    return render_template("index.html")

@app.route("/settings")
def settings():
    return render_template("index.html")


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = os.getenv('CLIENT_ID'),
        client_secret = os.getenv('CLIENT_SECRET'),
        redirect_uri = url_for("auth_receiver", _external=True),
        scope="user-library-read"
)

def confirm_auth():
    session['token_info'], authorized = get_token()
    session.modified = True
    if not authorized:
        return redirect(url_for("root"))
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