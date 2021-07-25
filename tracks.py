from flask import Blueprint, render_template, session


tracks = Blueprint('tracks', __name__, url_prefix='/tracks',
                        template_folder='templates')

@tracks.route('/top', defaults = {'range': 'all_time'})
def top_tracks(range):
    return render_template("tracks.html")