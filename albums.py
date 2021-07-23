from flask import Blueprint, render_template

albums = Blueprint('albums', __name__,
                        template_folder='templates')
