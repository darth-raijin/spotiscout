from dotenv import load_dotenv
import os
from flask import Flask, request, render_template, url_for, session, redirect
import spotipy
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
    return render_template("index.html")

@app.route("/login")
def login():
    spotify_oauth = create_spotify_oauth() 
    spotify_auth_url = spotify_oauth.get_authorize_url()
    return redirect(spotify_auth_url)

@app.route("/logout")
def logout():
    return render_template("index.html")

@app.route("/redirect")
def redirect():
    print("Redirect received!")
    return render_template("index.html")

@app.route("/settings")
def settings():
    return render_template("index.html")


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = os.getenv('CLIENT_ID'),
        client_secret = os.getenv('CLIENT_SECRET'),
        redirect_uri = url_for("redirect", _external=True),
        scope="user-library-read"
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)