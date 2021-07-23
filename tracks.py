from flask import Blueprint, render_template

tracks = Blueprint('tracks', __name__,
                        template_folder='templates')
