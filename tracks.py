from flask import Blueprint, render_template

tracks = Blueprint('tracks', __name__,
                        template_folder='templates')

@tracks.route('/top', defaults = {'range': 'all_time'})
def top_tracks():
    return NotImplemented