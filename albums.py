from flask import Blueprint, render_template

albums = Blueprint('albums', __name__,
                        template_folder='templates')

@albums.route('/top', defaults = {'range': 'all_time'})
def top_albums():
    return NotImplemented