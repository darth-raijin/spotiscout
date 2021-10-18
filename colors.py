def load_colors():
    with open('colors.txt') as f:
        colors = []
        for line in f:
            colors.append(line.replace("\n",""))

    return colors