from flask import Blueprint, render_template

genres = Blueprint('genres', __name__, url_prefix='/genres',
                        template_folder='templates')

@genres.route('/top', defaults = {'range': 'all_time'})
def top_genres(range):
    return NotImplemented