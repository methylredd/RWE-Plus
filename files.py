import ujson as json
import webbrowser

import pygame as pg
import os
import sys

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(__file__)

islinux = os.name == "posix"


def resolvepath(input_path):  # Thanks to someone... someone nice
    if not islinux:
        return input_path
    path = input_path.replace("\\", "/")
    if os.path.isdir(path):
        return path
    directory, filename = os.path.split(path)
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower() == filename.lower():
                return os.path.join(root, file)
    return None


def loadimage(filepath):
    resolved = resolvepath(filepath)
    if filepath is None:
        raise FileNotFoundError(f"Image by path {path} does not exist", path)
    return pg.image.load(resolved)


def get_project_display_path(filepath):
    if not os.path.exists(filepath):
        return 'Unsaved Level'
    else:
        try:
            return os.path.relpath(filepath, application_path)
        except ValueError:
            return os.path.split(filepath)[1]
    

allleters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,- =+_*()[]{}#@"

path = resolvepath(application_path + "\\files\\")
path2ui = resolvepath(path + "ui\\")
path2graphics = resolvepath(application_path + "\\drizzle\\Data\\Graphics\\")
path2cast = resolvepath(application_path + "\\drizzle\\Data\\Cast\\")
path2renderedlevels = resolvepath(application_path + "\\drizzle\\Data\\Levels\\")
path2props = resolvepath(application_path + "\\drizzle\\Data\\Props\\")
path2levels = resolvepath(application_path + "\\LevelEditorProjects\\")

path2effectPreviews = resolvepath(path + "effectPreviews\\")
path2materialPreviews = resolvepath(path + "materialPreviews\\")

pg.font.init()

graphics = json.load(open(path + "graphics.json", "r"))
settings = json.load(open(path + "settings.json", "r"))
ui_settings = json.load(open(path2ui +  settings["ui_theme"], "r"))
hotkeys = json.load(open(path + "hotkeys.json", "r"))
e = json.load(open(path + "effects.json", "r"))


tooltiles = loadimage(path + graphics["tooltiles"])
toolmenu = loadimage(path + graphics["toolmenu"])
APP_ICON = loadimage(path + "icon.png")
LOAD_SPLASH_SCREEN = loadimage(path + "load.png")

tag = "2.15.0"

ofstop = 15
ofsleft = 15

preview_cell_size = 16
render_cell_size = 20
preview_to_render_fac = float(render_cell_size) / preview_cell_size
spritesize = 16
image2sprite = spritesize / preview_cell_size
sprite2image = preview_cell_size / spritesize

camw = 70  # camera width in blocks
camh = 40  # camera height in blocks

wladd = 5.7  # addition to water level
bignum = 9999999  # just a big number

inputpromtname = "RWE+ input"

GEOMETRY_ENTRANCE_NODES = (7, 6, 21, 19, 5, 4)

fonts = {}


def fs(sz):
    if sz in fonts.keys():
        return fonts[sz]
    else:
        f = pg.font.Font(path + "/" + ui_settings["global"]["font"], sz)
        fonts[sz] = [f, f.size(allleters)[1]]
        return fonts[sz]

def jsoncopy(data):
    return json.loads(json.dumps(data))

def solveeffects(effects):
    ef = []
    for cat in effects["effects"]:
        efcat = {"nm": cat["nm"], "color": cat["color"], "efs": []}
        for effect in cat["efs"]:
            d = {**effects["defaultproperties"], **effect}
            if "options" not in d:
                d["options"] = []
            if "preview" in d:
                d["preview"] = loadimage(path2effectPreviews + d["preview"] + ".png")
            for i in effects["defaultparams"]:
                d["options"].append(i)
            for indx, option in enumerate(d["options"]):
                if option[0].lower() == "layers": # idk why, but it is what it is
                    lr = d["options"].pop(indx)
                    d["options"].insert(1, lr)
                    break
            efcat["efs"].append(d)
        ef.append(efcat)

    return ef


def plotLineLow(pointa: pg.Vector2, pointb: pg.Vector2, callback):
    if pointa.x > pointb.x:
        pointa, pointb = pointb, pointa
    dx = pointb.x - pointa.x
    dy = pointb.y - pointa.y
    yi = 1
    if dy < 0:
        yi = -1
        dy = -dy
    D = (2 * dy) - dx
    y = pointa.y

    for x in range(int(pointa.x), int(pointb.x)):
        callback(pg.Vector2(x, y), False)
        if D > 0:
            y = y + yi
            D = D + (2 * (dy - dx))
        else:
            D = D + 2 * dy
    callback(pointa, False)
    callback(pointb, False)


def plotLineHigh(pointa: pg.Vector2, pointb: pg.Vector2, callback):
    if pointa.y > pointb.y:
        pointa, pointb = pointb, pointa
    dx = pointb.x - pointa.x
    dy = pointb.y - pointa.y
    xi = 1
    if dx < 0:
        xi = -1
        dx = -dx
    D = (2 * dx) - dy
    x = pointa.x

    for y in range(int(pointa.y), int(pointb.y)):
        callback(pg.Vector2(x, y), False)
        if D > 0:
            x = x + xi
            D = D + (2 * (dx - dy))
        else:
            D = D + 2 * dx
    callback(pointa, False)
    callback(pointb, False)


def plotLine(pointa, pointb, callback):
    if abs(pointb.y - pointa.y) < abs(pointb.x - pointa.x):
        plotLineLow(pointa, pointb, callback)
    else:
        plotLineHigh(pointa, pointb, callback)


def rect2ellipse(rect: pg.Rect, hollow, callback):
    width = rect.width // 2
    height = rect.height // 2
    origin = rect.center
    hh = height * height
    ww = width * width
    hhww = hh * ww
    x0 = width
    dx = 0
    for x in range(-width, width + 1):
        if x == -width or x == width or not hollow:
            callback(pg.Vector2(origin[0] + x, origin[1]), False)
    for y in range(1, height + 1):
        x1 = x0 - (dx - 1)
        while x1 > 0:
            if x1*x1*hh + y*y*ww <= hhww:
                break
            x1 -= 1
        dx = x0 - x1
        x0 = x1
        for x in range(-x0, x0 + 1):
            if x == -x0 or x == x0 or not hollow:
                callback(pg.Vector2(origin[0] + x, origin[1] - y), False)
                callback(pg.Vector2(origin[0] + x, origin[1] + y), False)

    if not hollow:
        return

    y0 = height
    dy = 0
    for y in range(-height, height + 1):
        if y == -height or y == height or not hollow:
            callback(pg.Vector2(origin[0], origin[1] + y), False)
    for x in range(1, width + 1):
        y1 = y0 - (dy - 1)
        while y1 > 0:
            if y1*y1*ww + x*x*hh <= hhww:
                break
            y1 -= 1
        dy = y0 - y1
        y0 = y1
        for y in range(-y0, y0 + 1):
            if y == -y0 or y == y0 or not hollow:
                callback(pg.Vector2(origin[0] - x, origin[1] + y), False)
                callback(pg.Vector2(origin[0] + x, origin[1] + y), False)


def map(x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

MAX_RECENT_LEVELS = 16

def add_to_recent(filename):
    if filename not in [None, "", "\n", -1]:
        with open(path + "recent.txt", "r+") as recent:
            content = [x.replace("\n", "") for i, x in enumerate(recent.readlines()[:MAX_RECENT_LEVELS])]
            if filename in content:
                content.remove(filename)

        with open(path + "recent.txt", "w") as recent:
            recent.write(f"{str(filename)}\n")
            recent.write("\n".join(content))

def remove_wep_from_recent(filename):
    if filename not in [None, "", "\n", -1]:
        with open(path + "recent.txt", "r+") as recent:
            content = [x.replace("\n", "") for i, x in enumerate(recent.readlines()[:MAX_RECENT_LEVELS])]
            wep_filename = os.path.splitext(filename)[0] + ".wep"
            if wep_filename in content:
                content.remove(wep_filename)

        with open(path + "recent.txt", "w") as recent:
            recent.write("\n".join(content))
    ...

def report():
    webbrowser.open("https://github.com/methylredd/RWE-Plus/issues/new/choose")


def github():
    webbrowser.open("https://github.com/methylredd/RWE-Plus")
