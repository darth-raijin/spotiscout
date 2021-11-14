import os
from flask import Flask, session, request, redirect, render_template, url_for, flash
from flask_session import Session
from dotenv import load_dotenv
from datetime import date
import spotipy
import sys
import uuid
import random
import colors as colors
import json
import css_builder


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)


builder = css_builder.load_colors()
colors = colors.load_colors()

scope = "playlist-read-private user-read-recently-played user-top-read playlist-modify-public user-library-read playlist-read-private"

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
        session["user"] = {}
        auth_manager.get_access_token(request.args.get("code"))
        # TODO create get_profile data
        set_profile()
        get_total_playlists()
        get_top_artists()
        get_top_tracks()



        return redirect(url_for("index"))


    # If no token exists, user will be shown default index.html
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return render_template("index.html", auth_url = auth_url)
    
    button_text = ["View your all-time favorite tracks!", "View your most recently played tracks!", "View your all-time favorite artists!", "View your favorite genres!"]
    button_url = ["/tracks/top?range=alltime", "/recent", "/artists/top?range=alltime", "/genres"]

    dice = random.randint(0,3)
    dice_text = button_text[dice]
    dice_url = button_url[dice]

    print(dice_text)
    print(dice_url)
    return render_template("index.html", button_text = dice_text, button_url = dice_url)


def set_profile():
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    session["user"] = spotify.me()
    

@app.route('/profile')
def profile():
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    artists = []
    tracks =  []
    genres = []
    genre_count = 0

    for artist in session["user"]["long_artists"][:3]:
        artists.append(artist)

    for track in session["user"]["long_tracks"][:3]:
        tracks.append(track)

    for genre in session["user"]["genres"]:
        genre_count += 1

    iter_count = 0
    for genre in session["user"]["genres"]:
        if iter_count < 3:
            genres.append(genre.capitalize())
            iter_count += 1
        
        if iter_count >= 3:
            break
    # TODO Sort Chart.js for Genres

    return render_template("profile.html", artists = artists, tracks = tracks, genre_count = genre_count, genres = genres)


@app.route('/logout')
def logout():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect(url_for("index"))


def create_playlist(time_range: str):
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    today = date.today()

    user_id = spotify.me()['id']

    spotify.user_playlist_create(user = user_id, 
    name = f'Spotiscout Top 50 - {time_range.capitalize()}',
    description = f'Created with the help of Spotiscout | {today.strftime("%d/%m/%Y")}')

@app.route('/tracks/top', defaults = {'range': 'alltime'})
def top_tracks(range):
    valid_ranges = ["alltime", "short", "medium"]
    range = request.args.get('range')

    if check_easteregg(range):
        print(f"{session['uuid']} found the {range} easteregg!")
        return render_template('easteregg.html')

    short_button = medium_button = long_button = "is-outlined"

    tracks = None
    track_ids = []

    if range is None:
        return redirect(url_for('top_tracks'))
    
    if range not in valid_ranges:
        flash("Use the buttons instead! 😤", "error")
        range = "alltime"

    if range == "alltime":
        long_button =  ""
        tracks = pair_tracks(session["user"]["long_tracks"])
        for item in session["user"]["long_tracks"]:
            track_ids.append(item.get("id"))
    
    if range == "medium":
        medium_button =  ""
        tracks = pair_tracks(session["user"]["medium_tracks"])

        for item in session["user"]["medium_tracks"]:
            track_ids.append(item.get("id"))

    if range == "short":
        short_button = ""
        tracks = pair_tracks(session["user"]["short_tracks"])

        for item in session["user"]["short_tracks"]:
            track_ids.append(item.get("id"))

    if request.args.get('save') in valid_ranges:
        try:
            create_playlist(request.args.get('save'))
            playlist_id = get_latest_playlist()
            add_to_playlist(track_ids, playlist_id)
            flash("Successfully created playlist! Check out your Spotify", "Success")
        except: 
                flash("Something went wrong! 😱", "error")
    return render_template('tracks.html', short_button=short_button, medium_button=medium_button, long_button=long_button, tracks = tracks, current = range)

def pair_tracks(items: list):
    track_holder = items
    tracks = []
    pair = []
    counter = 0

    for track in track_holder:
        pair.append(track)
        counter += 1

        if counter == 3:
            tracks.append(pair)
            pair = []
            counter = 0
    return tracks


@app.route('/genres')
def top_genres():
    # Creates Genre profiles for 10 top tracks
    max_genres = 10
    values = []
    labels = []

    if "sort_status" not in session["user"]["genres"]:
        sorted_genres = {k: v for k, v in sorted(session["user"]["genres"].items(), reverse = True, key=lambda x: x[1])}
        session["user"]["genres"]["sort_status"] = True
    else: 
        print("Already sorted!")

    # If an equal amount of profile data is not loaded, loading will be done
    try:
        if len(session["user"]["genres"]["profiles"]) != max_genres:
            load_genreprofiles(sorted_genres)
    except:
        load_genreprofiles(sorted_genres)

    for item in session["user"]["genres"]["profiles"]:
        values.append(item.get("relative_weight"))
        labels.append(item.get("label"))

    return render_template("genres.html", values = json.dumps(values), labels = json.dumps(labels), colors = json.dumps(colors))

def load_genreprofiles(sorted_genres: dict):
    # Resetting genre profiles
    session["user"]["genres"]["profiles"] = []
    total_weight = 0
    results = []

    ten_genres = list(sorted_genres.items())[:10]

    # Iterate through all values and add to total_weight
    for item in ten_genres:
        total_weight += item[1]

    # Set index 2 to weight based on total_weight
    index = 0
    for item in ten_genres:
        current_dict = {}
        current_dict["label"] = item[0].capitalize()
        current_dict["weight"] = item[1]
        current_dict["relative_weight"] = round(item[1] / total_weight * 100, 2)
        index += 1
        results.append(current_dict)

    print(results)

    session["user"]["genres"]["profiles"] = results


@app.route('/artists/top', defaults = {'range': 'alltime'})
def top_artists(range):
    valid_ranges = ["alltime", "short", "medium"]
    range = request.args.get('range')

    if check_easteregg(range):
        print(f"{session['uuid']} found the {range} easteregg!")
        return render_template('easteregg.html')

    short_button = medium_button = long_button = "is-outlined"

    artists = None


    if range is None:
        return redirect(url_for('top_artists', variable = "alltime"))
    
    if range not in valid_ranges:
        flash("Creativity is good, but use the buttons instead! 😤", "error")
        range = "alltime"

    if range == "alltime":
        long_button =  ""
        artists = pair_tracks(session["user"]["long_artists"])
    
    if range == "medium":
        medium_button =  ""
        artists = pair_tracks(session["user"]["medium_artists"])

    if range == "short":
        short_button = ""
        artists = pair_tracks(session["user"]["short_artists"])


    return render_template('artists.html', short_button=short_button, medium_button=medium_button, long_button=long_button, artists = artists, current = range)

@app.route('/me')
def me():
    return session["user"]["genres"]

# DONE DIEGO
@app.route('/recent')
def recent():
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    recent_tracks = spotify.current_user_recently_played()
    tracks = []
    
    for item in recent_tracks["items"]:
        recent = {
            "external_url": item["track"],
            "image_url": item["track"]["album"]["images"][0]["url"],
            "name": item["track"]["name"],
            "artist": item["track"]["album"]["artists"][0]["name"],
            "artist_url": item["track"]["artists"][0]["external_urls"]["spotify"],
            "played_at": item["played_at"], # TODO FIX TIME TO MATCH USER TIMEZONE MUY IMPORTANTE
            "album_name": item["track"]["album"]["name"],
            "album_url": item["track"]["album"]["external_urls"]["spotify"]
        }
        tracks.append(recent)
    session["user"]["recent"] = recent


    return render_template("recent.html", recent = tracks)

# Functions for getting profile data

def check_easteregg(query: str):
    eastereggs = ["dbe", "deeznuts"]
    if query in eastereggs:
        return True
    
    return False

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
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    playlist_count = 0
    playlists = spotify.current_user_playlists(limit=50)

    while playlists['next']:
        playlists = spotify.next(playlists)
        for item in playlists['items']:
            playlist_count += 1

    session["user"]["playlist_count"] = playlist_count

def get_top_artists():
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    short_artists = []
    medium_artists = []
    long_artists = []
    session["user"]["genres"] = {}

    short_term = spotify.current_user_top_artists(time_range = "short_term", limit=50)
    medium_term = spotify.current_user_top_artists(time_range = "medium_term", limit=50)
    long_term = spotify.current_user_top_artists(time_range = "long_term", limit=50)

    rank = 1

    for item in short_term['items']:
        artist = {
            "external_url": item['external_urls']["spotify"],
            "image_url": item["images"][0]["url"], # TODO FIX IMAGE URL
            "name": item["name"],
            "rank": rank,
            "genres": extract_genres(item)
        }
        short_artists.append(artist)
        rank +=1
    rank = 1

    for item in medium_term['items']:
        artist = {
            "external_url": item['external_urls']["spotify"],
            "image_url": item["images"][0]["url"],
            "name": item["name"],
            "rank": rank,
            "genres": extract_genres(item)
        }
        medium_artists.append(artist)
        rank +=1
    rank = 1

    for item in long_term['items']:
        artist = {
            "external_url": item['external_urls']["spotify"],
            "image_url": item["images"][0]["url"],
            "name": item["name"],
            "rank": rank,
            "genres": extract_genres(item)
        }
        long_artists.append(artist)
        rank +=1
    rank = 1
    session["user"]["short_artists"] = short_artists
    session["user"]["medium_artists"] = medium_artists
    session["user"]["long_artists"] = long_artists

# DONE DIEGO
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

    rank = 1
    for item in short_term['items']:
        track = {
            "external_url": item['external_urls']["spotify"],
            "image_url": item["album"]["images"][0]["url"],
            "name": item["name"],
            "artist": item["album"]["artists"][0]["name"],
            "artist_url": item["artists"][0]["external_urls"]["spotify"],
            "rank": rank,
            "id": item["id"]
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
            "rank": rank,
            "id": item["id"]
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
            "rank": rank,
            "id": item["id"]
        }
        long_tracks.append(track)
        rank +=1
    rank = 1

    session["user"]["short_tracks"] = short_tracks
    session["user"]["medium_tracks"] = medium_tracks
    session["user"]["long_tracks"] = long_tracks

def extract_genres(item: dict):
    genres = []
    try: 
        for genre in item.get("genres"):
            genres.append(genre)
            if genre not in session["user"]["genres"]:
                session["user"]["genres"][genre] = 1

            if genre in session["user"]["genres"]:
                session["user"]["genres"][genre] += 1
        
        return genres
    except:
        print(f"Genre extraction failed!")
        return None



# DONE DIEGO
def add_to_playlist(tracks: list, playlist_id):
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager) 

    spotify.playlist_add_items(playlist_id, items = tracks)

# DONE DIEGO
def get_latest_playlist():
    spotify, auth_manager = confirm_authentication()
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    results = spotify.current_user_playlists(limit=1)

    return results.get("items")[0]["id"]

def confirm_authentication():
    cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope = scope,
                                                cache_handler = cache_handler, 
                                                show_dialog=True)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    return spotipy.Spotify(auth_manager=auth_manager), auth_manager

if __name__ == '__main__':
    app.run(threaded=True, port = 5000)