import json
import os

CONFIG_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "music": 0.1,
    "sound": 0.5,
    "theme": "dark",
    "width": 1366,
    "height": 768,
    "is_fullscreen": False,
    "effect": "none",
    "music_pack": "classic"
}

def get_music_pack():
    settings = load_settings()
    return settings.get('music_pack', DEFAULT_SETTINGS['music_pack'])

def load_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                for key in DEFAULT_SETTINGS:
                    if key not in settings:
                        settings[key] = DEFAULT_SETTINGS[key]
                return settings
        except (json.JSONDecodeError, IOError):
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)


def update_settings(**kwargs):
    settings = load_settings()
    
    for key, value in kwargs.items():
        if key in settings:
            settings[key] = value
        else:
            print(f"Предупреждение: поле '{key}' не существует в настройках")
    
    save_settings(settings)

def get_effect():
    settings = load_settings()
    return settings.get('effect', DEFAULT_SETTINGS['effect'])

def get_music():
    settings = load_settings()
    return settings.get('music', DEFAULT_SETTINGS['music'])

def get_sound():
    settings = load_settings()
    return settings.get('sound', DEFAULT_SETTINGS['sound'])

def get_background():
    settings = load_settings()
    return settings.get('background', DEFAULT_SETTINGS['background'])

def get_theme():
    settings = load_settings()
    return settings.get('theme', DEFAULT_SETTINGS['theme'])


def get_window_width():
    settings = load_settings()
    return settings.get('width', DEFAULT_SETTINGS['width'])


def get_window_height():
    settings = load_settings()
    return settings.get('height', DEFAULT_SETTINGS['height'])


def get_window_size():
    settings = load_settings()
    return (
        settings.get('width', DEFAULT_SETTINGS['width']),
        settings.get('height', DEFAULT_SETTINGS['height'])
    )

def get_fullscreen():
    settings = load_settings()
    return settings.get('is_fullscreen', DEFAULT_SETTINGS['is_fullscreen'])


def get_all_settings():
    return load_settings()


def reset_settings():
    save_settings(DEFAULT_SETTINGS.copy())
    print("Настройки сброшены к значениям по умолчанию")

def save_window_settings(width, height, is_fullscreen):
    update_settings(width=width, height=height, is_fullscreen=is_fullscreen)

def load_window_settings(default_width=800, default_height=600):
    width = get_window_width()
    height = get_window_height()
    is_fullscreen = get_fullscreen()
    
    if width == DEFAULT_SETTINGS['width']:
        width = default_width
    if height == DEFAULT_SETTINGS['height']:
        height = default_height
    
    return width, height, is_fullscreen

def save_last_user(username, password):
    settings = load_settings()
    settings['last_user'] = username
    settings['last_password'] = password
    save_settings(settings)

def get_last_user():
    settings = load_settings()
    username = settings.get('last_user', None)
    password = settings.get('last_password', None)
    return username, password

def clear_last_user():
    settings = load_settings()
    if 'last_user' in settings:
        del settings['last_user']
    if 'last_password' in settings:
        del settings['last_password']
    save_settings(settings)

if __name__ == "__main__":
    print("=== Использование функций из window_settings.py ===")
    save_window_settings(1024, 768, False)
    width, height, fullscreen = load_window_settings(800, 600)
    print(f"Загружены настройки окна: {width}x{height}, fullscreen={fullscreen}")
    
    print("\n=== Использование функций из settings_manager.py ===")
    print(f"Музыка: {get_music() * 100}%")
    print(f"Звуки: {get_sound() * 100}%")
    print(f"Тема: {get_theme()}")
    print(f"Размер окна: {get_window_size()}")
    print(f"Полный экран: {get_fullscreen()}")
    
    update_settings(music=0.75, sound=0.8, theme="dark")
    
    all_settings = get_all_settings()
    print(f"\nВсе настройки: {all_settings}")
    
    reset_settings()