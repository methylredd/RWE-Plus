import pygame as pg
import copy
from files import ui_settings, fs, path, map, allleters, loadimage
from render import gray, darkgray, color_mul, lerp  # noqa: F401

pg.font.init()

enablebuttons = True
bol = True
keybol = True
mul = ui_settings["global"]["colormul"]
black = [0, 0, 0]
white = [255, 255, 255]

def fastmts(window, text: str, x: int, y: int, col=None, fontsize=ui_settings["global"]["fontsize"], centered=False):
    if col is None:
        col = black
    fontr: pg.font.Font = fs(fontsize)[0]
    surf = fontr.render(text, True, col, None)
    textblit(window, surf, x, y, centered)


def mts(text: str = "", col=None, fontsize=ui_settings["global"]["fontsize"]):
    if col is None:
        col = black
    fontr: pg.font.Font = fs(fontsize)[0]
    sz: int = fs(fontsize)[1]
    if text == "RWE+":
        fontr: pg.font.Font = pg.font.Font(path + "/" + ui_settings["global"]["titlefont"], fontsize)
        sz: int = fontr.size(allleters)[1]
    items = text.split("\n")
    rendered = []
    w = 0
    poses = []
    for ln in items:
        render = fontr.render(ln, True, col, None)
        rendered.append(render)
        h = render.get_height()
        poses.append(h)
        if render.get_width() > w:
            w = render.get_width()

    surf = pg.Surface([w, (sz - 2) * len(poses)])
    surf = surf.convert_alpha(surf)
    surf.fill([0, 0, 0, 0])

    for i, r in enumerate(rendered):
        surf.blit(r, [0, (fontsize - 2) * i])
    return surf


def textblit(window: pg.Surface, screen_text: pg.Surface, x: int | float, y: int | float, centered: bool = False):
    if centered:
        window.blit(screen_text, [x - screen_text.get_width() / 2, y - screen_text.get_height() / 2])
    else:
        if x + screen_text.get_width() < window.get_width():
            window.blit(screen_text, [x, y])
        elif x - screen_text.get_width() > 0:
            window.blit(screen_text, [window.get_width() - screen_text.get_width(), y])
        else:
            window.blit(screen_text, [x, y])

class UIElement:
    def __init__(self, rect, surface):
        self.rect:pg.Rect = pg.Rect(rect)
        self.lastrect:pg.Rect = copy.copy(self.rect)
        self.surface:pg.Surface = surface
        self.children:[UIElement] = []

        self.active = True

        self.mouse_down = False
        self.last_mouse_down = False

    def resize(self):
        x = self.lastrect.x / 100 * self.surface.get_width()
        y = self.lastrect.y / 100 * self.surface.get_height()
        w = self.lastrect.w / 100 * self.surface.get_width() + 1
        h = self.lastrect.h / 100 * self.surface.get_height() + 1
        self.rect.update(x, y, w, h)

        for ch in self.children:
            ch.resize()

    def update(self):
        if not self.active:
            return
        
        self.mouse_down = pg.mouse.get_pressed(3)[0]

        if self.mouse_down and not self.last_mouse_down:
            self.on_click()

        self.last_mouse_down = self.mouse_down

        self.blit()

        for ch in self.children:
            ch.update()

    def blit(self):
        ...

    def on_click(self):
        ...

    @property
    def mouse_hover(self):
        return self.rect.collidepoint(pg.mouse.get_pos()) and self.active

    @property
    def topleft(self):
        return pg.Vector2(self.rect.x, self.rect.y)
    
    @property
    def bounds(self):
        return pg.Vector2(self.rect.w, self.rect.h)
    
class TextLabel(UIElement):
    def __init__(self, rect, surface, text, fontsize, fontcolor=None):
        super().__init__(rect, surface)
        self.text = text
        self.fontsize = fontsize
        self.fontcolor = fontcolor if fontcolor is not None else black

        self.text_surface = mts(text, fontcolor, fontsize)

    def blit(self):
        textblit(self.surface, self.text_surface, *self.rect.center, True)

    def resize(self):
        super().resize()
        self.set_text(self.text)

    def set_text(self, text, fontsize=None, fontcolor=None):
        self.text = text
        self.fontsize = self.fontsize if fontsize is None else fontsize
        self.fontcolor = self.fontcolor if fontcolor is None else fontcolor
        self.text_surface = mts(self.text, self.fontcolor, self.fontsize)

class ImageLabel(UIElement):
    def __init__(self, rect, surface, image:pg.Surface, imagecolor=None):
        super().__init__(rect, surface)
        self.image = image.copy()
        self.imagecolor = pg.Color(imagecolor if imagecolor is not None else white)

    def blit(self):
        imgsize = self.image.get_size()
        sfac = min(self.rect.width / imgsize[0], self.rect.height / imgsize[1])
        scaledimg = pg.transform.scale(self.image, [imgsize[0] * sfac, imgsize[1] * sfac])
        scaledimg.fill(self.imagecolor, special_flags=pg.BLEND_RGB_MULT)
        self.surface.blit(scaledimg, self.rect.center - (pg.Vector2(scaledimg.get_size()) / 2))

class GenericButton(UIElement):
    def __init__(self, rect, surface, text, hovertext, bodycolor, mdown_callback=None, fontsize=30, fontcolor=None):
        super().__init__(rect, surface)
        self.text = text
        self.hovertext = hovertext
        self.bodycolor = pg.Color(bodycolor)
        self.mdown_callback = mdown_callback

        self.children.append(TextLabel(rect, self.surface, self.text, fontsize, fontcolor))

    def blit(self):
        bgcolor = self.bodycolor

        if self.mouse_hover:
            bgcolor = color_mul(self.bodycolor, 0.8)
            pg.mouse.set_cursor(pg.Cursor(pg.SYSTEM_CURSOR_HAND))

        pg.draw.rect(self.surface, bgcolor, self.rect)

        if self.mouse_hover:
            fastmts(self.surface, self.hovertext, *pg.mouse.get_pos(), white)

    def on_click(self):
        self.mdown_callback(self)

class TextAndImageButton(UIElement):
    def __init__(self, rect, surface, text, hovertext, image, bodycolor, mdown_callback=None, fontsize=30, fontcolor=None, imagecolor=None):
        super().__init__(rect, surface)
        self.text = text
        self.hovertext = hovertext
        self.image = image.copy()
        self.bodycolor = pg.Color(bodycolor)
        self.imagecolor = pg.Color(imagecolor if imagecolor is not None else white)
        self.mdown_callback = mdown_callback

        self.children.append(TextLabel(rect, self.surface, self.text, fontsize, fontcolor))
        self.children.append(ImageLabel(rect, self.surface, self.image, self.imagecolor))

    def blit(self):
        bgcolor = self.bodycolor

        self.children[0].active = False
        self.children[1].active = True

        if self.mouse_hover:
            bgcolor = color_mul(self.bodycolor, 0.8)
            pg.mouse.set_cursor(pg.Cursor(pg.SYSTEM_CURSOR_HAND))
            self.children[0].active = True
            self.children[1].active = False

        pg.draw.rect(self.surface, bgcolor, self.rect)

        if self.mouse_hover:
            fastmts(self.surface, self.hovertext, *pg.mouse.get_pos(), white)

    def on_click(self):
        self.mdown_callback(self)

class HorizontalSlider(UIElement):
    def __init__(self, rect, surface, get_callback, set_callback, min, max, step, bodycolor=None, handlecolor=None):
        super().__init__(rect, surface)
        self.get_cb = get_callback
        self.set_cb = set_callback
        self.minvalue = min
        self.maxvalue = max
        self.step = step
        self.bodycolor = pg.Color(bodycolor if bodycolor is not None else darkgray)
        self.handlecolor = pg.Color(handlecolor if handlecolor is not None else gray)
        self.mousehold = False

    def blit(self):
        in_val = self.get_cb(self)

        in_val = max(min(in_val, self.maxvalue), self.minvalue)

        out_val = in_val

        if self.mouse_hover and self.mouse_down:
            self.mousehold = True

        if not self.mouse_down:
            self.mousehold = False
        
        rectl = self.rect.left + 10
        rectr = self.rect.right - 10

        if self.mousehold:
            mpos = pg.mouse.get_pos()
            out_val = lerp(self.minvalue, self.maxvalue, (mpos[0] - rectl) / (rectr - rectl))

        out_val = max(min(out_val, self.maxvalue), self.minvalue)

        handlecol = self.handlecolor

        if self.mouse_hover or self.mousehold:
            handlecol = color_mul(self.handlecolor, 0.8)

        handlex = lerp(rectl, rectr, (out_val - self.minvalue) / (self.maxvalue - self.minvalue))

        handlerect = [handlex - 10, self.rect.top, 20, self.rect.height]

        pg.draw.rect(self.surface, self.bodycolor, self.rect)
        pg.draw.rect(self.surface, handlecol, handlerect)

        if self.mouse_hover or self.mousehold:  
            fastmts(self.surface, f"{float(out_val):0.4}", *pg.mouse.get_pos(), white)

        self.set_cb(self, out_val)