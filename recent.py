from flask import Blueprint, render_template

recent = Blueprint('recent', __name__,
                        template_folder='templates')
