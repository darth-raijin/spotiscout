from flask import Blueprint, render_template


albums = Blueprint('albums', __name__, url_prefix='/albums',
                        template_folder='templates')

@albums.route('/top', defaults = {'range': 'alltime'})
def top_albums(range):
    return NotImplemented