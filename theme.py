import pygame

pygame.init()

NUMBER_COLORS = [
    None, (0, 0, 255), (0, 128, 0), (255, 0, 0), (0, 0, 128),
    (128, 0, 0), (0, 128, 128), (0, 0, 0), (128, 128, 128)
]

COLORS = {
    "light": {
        "background": (245, 243, 238),
        "cell": (255, 255, 255),
        "cell_revealed": (240, 238, 235),
        "text": (55, 50, 45),
        "text_secondary": (140, 130, 120),
        "mine": (80, 70, 60),
        "flag": (210, 130, 120),
        "border": (225, 220, 215),
        "timer_bg": (255, 255, 255),
        "info_bg": (255, 255, 255),
        "counter_bg": (245, 243, 238),
        "win": (130, 180, 110),
        "lose": (210, 120, 110),
        "card": (255, 255, 255),
        "input_bg": (248, 246, 242),
        "accent": (180, 155, 125),
        "accent_hover": (160, 135, 105),
        "error": (210, 120, 110),
        "button_primary": (130, 180, 110),
        "button_primary_hover": (110, 160, 90),
        "button_secondary": (180, 155, 125),
        "button_secondary_hover": (160, 135, 105),
    },
    "dark": {
        "background": (28, 26, 24),
        "cell": (42, 38, 35),
        "cell_revealed": (35, 32, 30),
        "text": (225, 220, 215),
        "text_secondary": (155, 148, 140),
        "mine": (200, 180, 160),
        "flag": (220, 140, 130),
        "border": (55, 50, 47),
        "timer_bg": (35, 32, 30),
        "info_bg": (35, 32, 30),
        "counter_bg": (42, 38, 35),
        "win": (120, 160, 95),
        "lose": (210, 120, 110),
        "card": (42, 38, 35),
        "input_bg": (35, 32, 30),
        "accent": (185, 160, 130),
        "accent_hover": (165, 140, 110),
        "error": (210, 120, 110),
        "button_primary": (120, 160, 95),
        "button_primary_hover": (100, 140, 80),
        "button_secondary": (185, 160, 130),
        "button_secondary_hover": (165, 140, 110),
    },
    "pastel": {
        "background": (248, 245, 252),
        "cell": (255, 253, 250),
        "cell_revealed": (248, 245, 242),
        "text": (90, 75, 85),
        "text_secondary": (155, 140, 150),
        "mine": (110, 95, 105),
        "flag": (215, 145, 155),
        "border": (232, 225, 238),
        "timer_bg": (255, 253, 250),
        "info_bg": (255, 253, 250),
        "counter_bg": (248, 245, 252),
        "win": (160, 195, 145),
        "lose": (215, 150, 160),
        "card": (255, 253, 250),
        "input_bg": (252, 248, 255),
        "accent": (190, 160, 200),
        "accent_hover": (170, 140, 180),
        "error": (215, 145, 155),
        "button_primary": (160, 195, 145),
        "button_primary_hover": (140, 175, 125),
        "button_secondary": (190, 160, 200),
        "button_secondary_hover": (170, 140, 180),
    },
    "coffee": {
        "background": (230, 218, 202),
        "cell": (248, 240, 228),
        "cell_revealed": (238, 230, 218),
        "text": (75, 60, 48),
        "text_secondary": (135, 115, 98),
        "mine": (95, 78, 68),
        "flag": (185, 125, 105),
        "border": (210, 192, 172),
        "timer_bg": (248, 240, 228),
        "info_bg": (248, 240, 228),
        "counter_bg": (230, 218, 202),
        "win": (145, 125, 100),
        "lose": (185, 125, 105),
        "card": (248, 240, 228),
        "input_bg": (238, 230, 218),
        "accent": (165, 135, 110),
        "accent_hover": (145, 115, 90),
        "error": (185, 125, 105),
        "button_primary": (145, 125, 100),
        "button_primary_hover": (125, 105, 80),
        "button_secondary": (165, 135, 110),
        "button_secondary_hover": (145, 115, 90),
    },
    "retro": {
        "background": (242, 230, 198),
        "cell": (255, 248, 220),
        "cell_revealed": (248, 242, 210),
        "text": (85, 65, 42),
        "text_secondary": (145, 115, 82),
        "mine": (105, 80, 58),
        "flag": (205, 105, 85),
        "border": (225, 208, 170),
        "timer_bg": (255, 248, 220),
        "info_bg": (255, 248, 220),
        "counter_bg": (242, 230, 198),
        "win": (155, 135, 95),
        "lose": (205, 105, 85),
        "card": (255, 248, 220),
        "input_bg": (248, 242, 210),
        "accent": (185, 145, 105),
        "accent_hover": (165, 125, 85),
        "error": (205, 105, 85),
        "button_primary": (155, 135, 95),
        "button_primary_hover": (135, 115, 75),
        "button_secondary": (185, 145, 105),
        "button_secondary_hover": (165, 125, 85),
    },
    "retro_dark": {
        "background": (42, 38, 32),
        "cell": (65, 58, 48),
        "cell_revealed": (55, 50, 42),
        "text": (228, 210, 175),
        "text_secondary": (155, 138, 112),
        "mine": (195, 165, 128),
        "flag": (210, 130, 105),
        "border": (80, 70, 60),
        "timer_bg": (65, 58, 48),
        "info_bg": (65, 58, 48),
        "counter_bg": (55, 50, 42),
        "win": (148, 128, 95),
        "lose": (210, 130, 105),
        "card": (65, 58, 48),
        "input_bg": (55, 50, 42),
        "accent": (185, 148, 108),
        "accent_hover": (165, 128, 88),
        "error": (210, 130, 105),
        "button_primary": (148, 128, 95),
        "button_primary_hover": (128, 108, 78),
        "button_secondary": (185, 148, 108),
        "button_secondary_hover": (165, 128, 88),
    },
    "ocean": {
        "background": (218, 235, 240),
        "cell": (242, 250, 252),
        "cell_revealed": (232, 245, 248),
        "text": (35, 70, 85),
        "text_secondary": (105, 140, 155),
        "mine": (55, 100, 115),
        "flag": (200, 120, 110),
        "border": (205, 222, 228),
        "timer_bg": (242, 250, 252),
        "info_bg": (242, 250, 252),
        "counter_bg": (218, 235, 240),
        "win": (105, 165, 138),
        "lose": (200, 120, 110),
        "card": (242, 250, 252),
        "input_bg": (232, 245, 248),
        "accent": (85, 148, 165),
        "accent_hover": (65, 128, 145),
        "error": (200, 120, 110),
        "button_primary": (105, 165, 138),
        "button_primary_hover": (85, 145, 118),
        "button_secondary": (85, 148, 165),
        "button_secondary_hover": (65, 128, 145),
    },
    "forest": {
        "background": (222, 235, 218),
        "cell": (245, 252, 242),
        "cell_revealed": (235, 245, 232),
        "text": (52, 68, 48),
        "text_secondary": (112, 128, 105),
        "mine": (72, 88, 65),
        "flag": (182, 122, 102),
        "border": (202, 215, 195),
        "timer_bg": (245, 252, 242),
        "info_bg": (245, 252, 242),
        "counter_bg": (222, 235, 218),
        "win": (105, 138, 88),
        "lose": (182, 122, 102),
        "card": (245, 252, 242),
        "input_bg": (235, 245, 232),
        "accent": (112, 148, 98),
        "accent_hover": (92, 128, 78),
        "error": (182, 122, 102),
        "button_primary": (105, 138, 88),
        "button_primary_hover": (85, 118, 68),
        "button_secondary": (112, 148, 98),
        "button_secondary_hover": (92, 128, 78),
    },
    "sunset": {
        "background": (248, 222, 212),
        "cell": (255, 242, 235),
        "cell_revealed": (248, 235, 228),
        "text": (98, 62, 68),
        "text_secondary": (158, 112, 118),
        "mine": (118, 82, 88),
        "flag": (210, 102, 98),
        "border": (232, 205, 195),
        "timer_bg": (255, 242, 235),
        "info_bg": (255, 242, 235),
        "counter_bg": (248, 222, 212),
        "win": (195, 140, 112),
        "lose": (210, 102, 98),
        "card": (255, 242, 235),
        "input_bg": (248, 235, 228),
        "accent": (215, 140, 120),
        "accent_hover": (195, 120, 100),
        "error": (210, 102, 98),
        "button_primary": (195, 140, 112),
        "button_primary_hover": (175, 120, 92),
        "button_secondary": (215, 140, 120),
        "button_secondary_hover": (195, 120, 100),
    },
    "space": {
        "background": (22, 25, 42),
        "cell": (35, 38, 58),
        "cell_revealed": (30, 33, 50),
        "text": (195, 205, 240),
        "text_secondary": (128, 138, 175),
        "mine": (175, 165, 215),
        "flag": (210, 118, 148),
        "border": (52, 55, 78),
        "timer_bg": (35, 38, 58),
        "info_bg": (35, 38, 58),
        "counter_bg": (30, 33, 50),
        "win": (98, 148, 195),
        "lose": (210, 118, 148),
        "card": (35, 38, 58),
        "input_bg": (30, 33, 50),
        "accent": (98, 118, 195),
        "accent_hover": (78, 98, 175),
        "error": (210, 118, 148),
        "button_primary": (98, 148, 195),
        "button_primary_hover": (78, 128, 175),
        "button_secondary": (98, 118, 195),
        "button_secondary_hover": (78, 98, 175),
    },
    "mint": {
        "background": (218, 238, 225),
        "cell": (242, 252, 245),
        "cell_revealed": (232, 248, 238),
        "text": (52, 78, 68),
        "text_secondary": (112, 138, 125),
        "mine": (72, 98, 88),
        "flag": (198, 132, 122),
        "border": (198, 220, 208),
        "timer_bg": (242, 252, 245),
        "info_bg": (242, 252, 245),
        "counter_bg": (218, 238, 225),
        "win": (102, 158, 128),
        "lose": (198, 132, 122),
        "card": (242, 252, 245),
        "input_bg": (232, 248, 238),
        "accent": (102, 158, 128),
        "accent_hover": (82, 138, 108),
        "error": (198, 132, 122),
        "button_primary": (102, 158, 128),
        "button_primary_hover": (82, 138, 108),
        "button_secondary": (102, 158, 128),
        "button_secondary_hover": (82, 138, 108),
    },
    "cyber": {
        "background": (18, 22, 35),
        "cell": (32, 36, 52),
        "cell_revealed": (28, 32, 45),
        "text": (0, 240, 185),
        "text_secondary": (95, 190, 170),
        "mine": (240, 95, 140),
        "flag": (240, 80, 115),
        "border": (0, 190, 170),
        "timer_bg": (32, 36, 52),
        "info_bg": (32, 36, 52),
        "counter_bg": (28, 32, 45),
        "win": (0, 210, 170),
        "lose": (240, 80, 115),
        "card": (32, 36, 52),
        "input_bg": (28, 32, 45),
        "accent": (0, 210, 170),
        "accent_hover": (0, 190, 150),
        "error": (240, 80, 115),
        "button_primary": (0, 210, 170),
        "button_primary_hover": (0, 190, 150),
        "button_secondary": (0, 210, 170),
        "button_secondary_hover": (0, 190, 150),
    },
    "lavender": {
        "background": (238, 228, 248),
        "cell": (250, 245, 252),
        "cell_revealed": (245, 240, 250),
        "text": (72, 62, 98),
        "text_secondary": (140, 128, 165),
        "mine": (102, 88, 128),
        "flag": (198, 142, 178),
        "border": (218, 205, 235),
        "timer_bg": (250, 245, 252),
        "info_bg": (250, 245, 252),
        "counter_bg": (238, 228, 248),
        "win": (148, 132, 178),
        "lose": (198, 142, 178),
        "card": (250, 245, 252),
        "input_bg": (245, 240, 250),
        "accent": (158, 132, 198),
        "accent_hover": (138, 112, 178),
        "error": (198, 142, 178),
        "button_primary": (148, 132, 178),
        "button_primary_hover": (128, 112, 158),
        "button_secondary": (158, 132, 198),
        "button_secondary_hover": (138, 112, 178),
    },
}

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (255, 255, 255)

def get_animated_color(color_type, time_offset=0):
    import math
    t = pygame.time.get_ticks() / 1000.0 + time_offset
    
    if color_type == "rainbow":
        return (max(0, min(255, int((math.sin(t * 2) * 127 + 128)))),
                max(0, min(255, int((math.sin(t * 2 + 2) * 127 + 128)))),
                max(0, min(255, int((math.sin(t * 2 + 4) * 127 + 128)))))
    elif color_type == "gold":
        return (255, 
                max(0, min(255, int(215 + math.sin(t * 3) * 40))), 
                max(0, min(255, int(math.sin(t * 3) * 50))))
    elif color_type == "fire":
        return (255, 
                max(0, min(255, int(100 + math.sin(t * 5) * 55))), 
                max(0, min(255, int(math.sin(t * 5) * 20))))
    elif color_type == "neon":
        return (max(0, min(255, int(127 + math.sin(t * 4) * 127))), 
                max(0, min(255, int(127 + math.sin(t * 4 + 2) * 127))), 
                255)
    elif color_type == "space":
        return (max(0, min(255, int(50 + math.sin(t) * 30))), 
                max(0, min(255, int(50 + math.sin(t * 1.5) * 30))), 
                max(0, min(255, int(150 + math.sin(t * 2) * 105))))
    elif color_type == "legendary_purple":
        return (max(0, min(255, int(180 + math.sin(t * 2) * 75))), 
                max(0, min(255, int(math.sin(t * 2) * 50))), 
                max(0, min(255, int(200 + math.sin(t * 2) * 55))))
    elif color_type == "platinum":
        return (max(0, min(255, int(200 + math.sin(t * 2) * 55))), 
                max(0, min(255, int(200 + math.sin(t * 2) * 55))), 
                max(0, min(255, int(200 + math.sin(t * 2) * 55))))
    elif color_type == "emerald":
        return (max(0, min(255, int(math.sin(t * 2) * 30))), 
                max(0, min(255, int(200 + math.sin(t * 2) * 55))), 
                max(0, min(255, int(100 + math.sin(t * 2) * 50))))
    elif color_type == "blood":
        return (max(0, min(255, int(200 + math.sin(t * 3) * 55))), 
                max(0, min(255, int(math.sin(t * 3) * 20))), 
                max(0, min(255, int(math.sin(t * 3) * 20))))
    elif color_type == "ghost":
        return (max(0, min(255, int(200 + math.sin(t * 1.5) * 55))), 
                max(0, min(255, int(200 + math.sin(t * 1.5 + 2) * 55))), 
                255)
    elif color_type == "hacker":
        return (0, 
                max(0, min(255, int(200 + math.sin(t * 10) * 55))), 
                0)
    
    return (255, 255, 255)

def get_champion_color():
    theme = get_current_theme()
    if theme['background'][0] < 100:
        return (255, 200, 50)
    else:
        return (218, 165, 32)

EFFECTS = {
    "none": "Выкл",
    "vignette": "Виньетка",
    "chromatic": "Аберрация",
    "wave": "Волны",
    "glitch": "Глитч",
    "pixelsort": "Пиксельная сортировка",
    "snow": "Снег",
    "crystal": "Кристалл",
    "aurora": "Северное сияние",
    "nebula": "Туманность",
    "rainbow": "Радуга",
    "bubble": "Пузырьки",
    "raindrop": "Капельки"
}

AVAILABLE_EFFECTS = list(EFFECTS.keys())

THEME = "light"

WIDTH = 400
HEIGHT = 400
CELL_SIZE = 20
ROWS = HEIGHT // CELL_SIZE
COLS = WIDTH // CELL_SIZE

WHITE = (255, 255, 255)
BLACK = (40, 40, 40)
GREY = (140, 130, 120)
RED = (200, 120, 110)
GREEN = (150, 190, 120)

NUM_MINES = 35

DIFF_ACTIVE = (210, 180, 140)
DIFF_PASSIVE = (235, 230, 225)
DIFF_HOVER = (190, 160, 120)
MODE_ACTIVE = (210, 180, 140)
MODE_PASSIVE = (235, 230, 225)
MODE_HOVER = (190, 160, 120)
START_COLOR = (150, 190, 120)
START_HOVER = (130, 170, 100)
EXIT_COLOR = (200, 120, 110)
EXIT_HOVER = (180, 100, 90)
SLIDER_COLOR = (235, 230, 225)
SLIDER_ACTIVE = (210, 180, 140)
INPUT_ACTIVE = (210, 180, 140)
INPUT_PASSIVE = (235, 230, 225)
TITLE_COLOR = (80, 70, 60)
ACCENT_COLOR = (210, 180, 140)
TEXT_COLOR = (40, 40, 40)
BUTTON_HOVER = (190, 160, 120)

BUTTON_COLORS = {
    'apply': (150, 190, 120),
    'cancel': (200, 120, 110),
    'play': (150, 190, 120),
    'profile': (210, 180, 140),
    'top': (200, 120, 110),
    'exit': (235, 230, 225),
    'logout': (210, 180, 140),
    'login': (210, 180, 140),
    'register': (248, 245, 240),
    'hover': (190, 160, 120)
}

BUTTON_HOVER_COLORS = {
    'apply': (130, 170, 100),
    'cancel': (180, 100, 90),
    'play': (130, 170, 100),
    'profile': (190, 160, 120),
    'top': (180, 100, 90),
    'exit': (235, 230, 225),
    'logout': (190, 160, 120)
}

stat_font = pygame.font.Font('font/font.otf', 36)
default_font = pygame.font.Font('font/font.otf', 36)
title_font = pygame.font.Font('font/font.otf', 48)
subtitle_font = pygame.font.Font('font/font.otf', 32)
small_font = pygame.font.Font('font/font.otf', 14)
label_font = pygame.font.Font('font/font.otf', 16)
input_font = pygame.font.Font('font/font.otf', 18)
button_font = pygame.font.Font('font/font.otf', 18)
button_font_exit = pygame.font.Font('font/font.otf', 16)

def set_theme(theme_name):
    global THEME
    if theme_name in COLORS:
        THEME = theme_name

def get_current_theme():
    return COLORS[THEME]

def get_color(color_key):
    return COLORS[THEME].get(color_key, (255, 255, 255))

def get_available_themes():
    return list(COLORS.keys())


def get_available_effects():
    return AVAILABLE_EFFECTS

BACKGROUNDS = {
    "none": "Нет",
    "rain": "Дождь",
    "pulse": "Пульсация",
    "stars": "Звёзды",
    "particles": "Частицы"
}

AVAILABLE_BACKGROUNDS = list(BACKGROUNDS.keys())

def get_available_backgrounds():
    return AVAILABLE_BACKGROUNDS