"""Minimal example of a non-agent dynamic artist moving between two fixed points."""

import gamms
from gamms.VisualizationEngine import Color, Shape
from gamms.VisualizationEngine.artist import Artist
from gamms.typing import ArtistType, IContext


START_POINT = (-8.0, 0.0)
END_POINT = (8.0, 0.0)
VIS_KWARGS = {}


def draw_moving_dot(ctx: IContext, data: dict):
    start_x, start_y = data["start"]
    end_x, end_y = data["end"]
    alpha = data.get("_alpha")

    x = (1.0 - alpha) * start_x + alpha * end_x
    y = (1.0 - alpha) * start_y + alpha * end_y

    ctx.visual.render_circle(
        x,
        y,
        data.get("radius", 0.9),
        data.get("color", Color.Red),
    )


def draw_path_line(ctx: IContext, data: dict):
    start_x, start_y = data["start"]
    end_x, end_y = data["end"]
    ctx.visual.render_line(
        start_x,
        start_y,
        end_x,
        end_y,
        data.get("path_color", Color.LightGray),
        width=data.get("width", 2),
    )


def add_anchor(ctx: IContext, name: str, x: float, y: float, color):
    anchor = Artist(ctx, Shape.Circle, 5)
    anchor.data["x"] = x
    anchor.data["y"] = y
    anchor.data["radius"] = 0.6
    anchor.data["color"] = color
    anchor.set_artist_type(ArtistType.STATIC)
    ctx.visual.add_artist(name, anchor)
    return anchor


def add_path_line(ctx: IContext, name: str, start: tuple[float, float], end: tuple[float, float]):
    path = Artist(ctx, draw_path_line, 15)
    path.data["start"] = start
    path.data["end"] = end
    path.data["path_color"] = Color.LightGray
    path.data["width"] = 2
    path.set_artist_type(ArtistType.STATIC)
    ctx.visual.add_artist(name, path)
    return path


def main() -> None:
    ctx = gamms.create_context(
        vis_engine=gamms.visual.Engine.PYGAME,
        vis_kwargs=VIS_KWARGS,
    )

    add_anchor(ctx, "start_anchor", START_POINT[0], START_POINT[1], Color.Blue)
    add_anchor(ctx, "end_anchor", END_POINT[0], END_POINT[1], Color.Green)
    add_path_line(ctx, "moving_dot_path", START_POINT, END_POINT)

    moving_dot = Artist(ctx, draw_moving_dot, 20)
    moving_dot.set_artist_type(ArtistType.DYNAMIC)
    moving_dot.data["start"] = START_POINT
    moving_dot.data["end"] = END_POINT
    moving_dot.data["radius"] = 0.9
    moving_dot.data["color"] = Color.Red
    moving_dot.data["path_color"] = Color.LightGray
    ctx.visual.add_artist("moving_dot", moving_dot)

    while not ctx.is_terminated():
        ctx.visual.simulate()
        moving_dot.data["start"], moving_dot.data["end"] = moving_dot.data["end"], moving_dot.data["start"]

    ctx.terminate()


if __name__ == "__main__":
    main()
    
