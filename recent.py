from flask import Blueprint, render_template


recent = Blueprint('recent', __name__, url_prefix='/recent',
                        template_folder='templates')

@recent.route('/', defaults = {'item': 'tracks'})
def recent_albums(item):
    return item

