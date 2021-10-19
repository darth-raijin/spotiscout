import sass


def load_colors():
    compiled_css_from_file = sass.compile(dirname=('static/sass', 'static/css'), output_style='compressed')
    print("Build successfull!")
