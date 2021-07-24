from flask import Blueprint, render_template

recent = Blueprint('recent', __name__,
                        template_folder='templates')

@recent.route('/albums')
def recent_albums():
    return NotImplemented

@recent.route('/tracks')
def recent_tracks():
    return NotImplemented

@recent.route('/genres')
def recent_genres():
    return NotImplemented