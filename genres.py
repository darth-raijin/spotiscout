from flask import Blueprint, render_template

genres = Blueprint('genres', __name__,
                        template_folder='templates')
