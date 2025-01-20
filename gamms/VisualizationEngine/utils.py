from gamms.VisualizationEngine import Color


def string_to_color(color_string: str) -> Color:
    if color_string == "red":
        return Color.Red
    elif color_string == "blue":
        return Color.Blue
    elif color_string == "green":
        return Color.Green
    elif color_string == "yellow":
        return Color.Yellow
    elif color_string == "orange":
        return Color.Orange
    elif color_string == "purple":
        return Color.Purple
    elif color_string == "black":
        return Color.Black
    elif color_string == "white":
        return Color.White
    else:
        raise ValueError(f"Color {color_string} not recognized")