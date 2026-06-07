import pygame
import sys
import math
import random
import re
from db_manager import *
import auth, menu, admin_panel
from theme import *
from settings_manager import *
from ui import AnimatedButton, AnimatedInput
from music_manager import get_music_manager
from effects import *

ALLOWED_CHARS = re.compile(r'^[a-zA-Zа-яА-Я0-9!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~ ]+$')

def filter_input(text, max_len=30):
    filtered = ''
    for char in text:
        if ALLOWED_CHARS.match(char) and len(filtered) < max_len:
            filtered += char
    return filtered


class LavaLamp:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.blobs = []
        self.create_blobs()
    
    def create_blobs(self):
        theme = get_current_theme()
        
        accent = theme['accent']
        accent_hover = theme['accent_hover']
        
        LAVA_COLORS = [
            (*accent, 85),
            (*accent_hover, 80),
            (min(accent[0] + 30, 255), min(accent[1] + 20, 255), min(accent[2] + 10, 255), 80),
            (max(accent[0] - 30, 0), max(accent[1] - 20, 0), max(accent[2] - 10, 0), 90),
            (min(accent[0] + 50, 255), min(accent[1] + 30, 255), min(accent[2] + 20, 255), 75),
            (min(accent[0] + 15, 255), min(accent[1] + 10, 255), accent[2], 85),
            (accent[0], min(accent[1] + 25, 255), min(accent[2] + 25, 255), 80),
            (min(accent[0] + 40, 255), max(accent[1] - 10, 0), min(accent[2] + 15, 255), 85),
        ]
        
        if theme['background'][0] < 100 and theme['background'][1] < 100 and theme['background'][2] < 100:
            LAVA_COLORS = [(min(c[0] + 30, 255), min(c[1] + 30, 255), min(c[2] + 30, 255), c[3]) for c in LAVA_COLORS]
        elif theme['background'][0] > 200 and theme['background'][1] > 200 and theme['background'][2] > 200:
            LAVA_COLORS = [(max(c[0] - 40, 100), max(c[1] - 40, 100), max(c[2] - 40, 100), c[3]) for c in LAVA_COLORS]
        
        self.blobs = []
        for i in range(8):
            self.blobs.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'radius': random.randint(120, 280),
                'speed_x': random.uniform(0.3, 0.7),
                'speed_y': random.uniform(0.25, 0.6),
                'angle_x': random.uniform(0, math.pi * 2),
                'angle_y': random.uniform(0, math.pi * 2),
                'color': random.choice(LAVA_COLORS),
                'pulse': random.uniform(0, math.pi * 2),
                'pulse_speed': random.uniform(0.015, 0.04)
            })
    
    def update_theme_colors(self):
        theme = get_current_theme()
        
        accent = theme['accent']
        accent_hover = theme['accent_hover']
        
        LAVA_COLORS = [
            (*accent, 85),
            (*accent_hover, 80),
            (min(accent[0] + 30, 255), min(accent[1] + 20, 255), min(accent[2] + 10, 255), 80),
            (max(accent[0] - 30, 0), max(accent[1] - 20, 0), max(accent[2] - 10, 0), 90),
            (min(accent[0] + 50, 255), min(accent[1] + 30, 255), min(accent[2] + 20, 255), 75),
            (min(accent[0] + 15, 255), min(accent[1] + 10, 255), accent[2], 85),
            (accent[0], min(accent[1] + 25, 255), min(accent[2] + 25, 255), 80),
            (min(accent[0] + 40, 255), max(accent[1] - 10, 0), min(accent[2] + 15, 255), 85),
        ]
        
        if theme['background'][0] < 100 and theme['background'][1] < 100 and theme['background'][2] < 100:
            LAVA_COLORS = [(min(c[0] + 30, 255), min(c[1] + 30, 255), min(c[2] + 30, 255), c[3]) for c in LAVA_COLORS]
        elif theme['background'][0] > 200 and theme['background'][1] > 200 and theme['background'][2] > 200:
            LAVA_COLORS = [(max(c[0] - 40, 100), max(c[1] - 40, 100), max(c[2] - 40, 100), c[3]) for c in LAVA_COLORS]
        
        for blob in self.blobs:
            blob['color'] = random.choice(LAVA_COLORS)
    
    def update(self, width, height):
        self.width = width
        self.height = height
        
        for blob in self.blobs:
            blob['angle_x'] += 0.006
            blob['angle_y'] += 0.005
            
            blob['pulse'] += blob['pulse_speed']
            pulse_factor = 0.7 + math.sin(blob['pulse']) * 0.3
            
            blob['x'] += math.sin(blob['angle_x']) * blob['speed_x']
            blob['y'] += math.cos(blob['angle_y']) * blob['speed_y']
            blob['current_radius'] = blob['radius'] * pulse_factor
            
            if blob['x'] < -blob['radius']:
                blob['x'] = width + blob['radius']
            if blob['x'] > width + blob['radius']:
                blob['x'] = -blob['radius']
            if blob['y'] < -blob['radius']:
                blob['y'] = height + blob['radius']
            if blob['y'] > height + blob['radius']:
                blob['y'] = -blob['radius']
    
    def draw(self, screen):
        theme = get_current_theme()
        
        bg_color = theme['background']
        for y in range(self.height):
            ratio = y / self.height
            r = int(bg_color[0] - ratio * 15)
            g = int(bg_color[1] - ratio * 15)
            b = int(bg_color[2] - ratio * 15)
            pygame.draw.line(screen, (max(0, r), max(0, g), max(0, b)), (0, y), (self.width, y))
        
        for blob in self.blobs:
            radius = int(blob.get('current_radius', blob['radius']))
            
            temp_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            center = (radius, radius)
            
            for r in range(radius, 0, -3):
                alpha = int(blob['color'][3] * (1 - (r / radius) ** 1.6))
                color = (blob['color'][0], blob['color'][1], blob['color'][2], alpha)
                pygame.draw.circle(temp_surf, color, center, r)
            
            screen.blit(temp_surf, (int(blob['x'] - radius), int(blob['y'] - radius)))
        
        fog = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        fog_color = (*bg_color, 15)
        fog.fill(fog_color)
        screen.blit(fog, (0, 0))


def reg():
    pygame.init()
    
    volume_music = get_music()
    volume_sound = get_sound()
    theme_name = get_theme()
    
    set_theme(theme_name)
    
    music_manager = get_music_manager()
    
    click = music_manager.load_sound('click.mp3')
    channel_click = pygame.mixer.Channel(0)
    channel_click.set_volume(volume_sound)

    music_manager.load_music('auth', volume_music)

    saved_width, saved_height, saved_fullscreen = load_window_settings(1366, 768)
    
    if saved_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((saved_width, saved_height), pygame.RESIZABLE)
    
    pygame.display.set_caption('DeepCore')
    
    is_fullscreen = saved_fullscreen
    window_size = (saved_width, saved_height) if not saved_fullscreen else (1366, 768)
    
    current_width, current_height = screen.get_size()
    lava_lamp = LavaLamp(current_width, current_height)
    
    def toggle_fullscreen():
        nonlocal screen, is_fullscreen, window_size
        if is_fullscreen:
            screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
            is_fullscreen = False
        else:
            window_size = screen.get_size()
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            is_fullscreen = True
        save_window_settings(window_size[0], window_size[1], is_fullscreen)

    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)
    admin_creation_mode = False
    
    login_text = ''
    pass_text = ''
    pass2_text = ''
    
    admin_login_text = ''
    admin_pass_text = ''
    admin_pass2_text = ''
    
    login_active = False
    pass_active = False
    pass2_active = False
    
    admin_login_active = False
    admin_pass_active = False
    admin_pass2_active = False
    
    reg_error = False
    error_message = ''
    error_timer = 0
    
    last_theme = theme_name
    
    register_btn = None
    login_btn = None
    admin_register_btn = None
    admin_back_btn = None
    
    mouse_was_pressed = False
    ignore_clicks = True
    frames_passed = 0
    
    run = True
    clock = pygame.time.Clock()
    
    while run:
        current_width, current_height = screen.get_size()
        dt = clock.get_time() / 1000.0
        
        if current_effect != get_effect():
            current_effect = get_effect()
            effect_manager.set_effect(current_effect, current_width, current_height)
        effect_manager.update(dt, current_width, current_height)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_released = not mouse_pressed and mouse_was_pressed
        mouse_was_pressed = mouse_pressed
        
        frames_passed += 1
        if frames_passed > 3:
            ignore_clicks = False
        
        current_theme_name = get_theme()
        if last_theme != current_theme_name:
            last_theme = current_theme_name
            set_theme(current_theme_name)
            lava_lamp.update_theme_colors()
        
        lava_lamp.update(current_width, current_height)
        
        theme = get_current_theme()
        CARD_COLOR = theme['card']
        TEXT_PRIMARY = theme['text']
        TEXT_SECONDARY = theme['text_secondary']
        ACCENT = theme['accent']
        ACCENT_HOVER = theme['accent_hover']
        BORDER_COLOR = theme['border']
        ERROR_COLOR = theme['error']
        INPUT_BG = theme['input_bg']
        
        card_width = 480
        card_height = 620
        card_x = (current_width - card_width) // 2
        card_y = (current_height - card_height) // 2
        
        padding = 40
        content_x = card_x + padding
        content_width = card_width - padding * 2
        
        title_y = card_y + 55
        login_label_y = card_y + 150
        login_field_y = login_label_y + 28
        login_field_height = 50
        
        pass_label_y = login_field_y + 70
        pass_field_y = pass_label_y + 28
        pass_field_height = 50
        
        pass2_label_y = pass_field_y + 70
        pass2_field_y = pass2_label_y + 28
        pass2_field_height = 50
        
        register_btn_y = pass2_field_y + 85
        login_btn_y = register_btn_y + 65
        button_height = 48
        
        login_rect = pygame.Rect(content_x, login_field_y, content_width, login_field_height)
        pass_rect = pygame.Rect(content_x, pass_field_y, content_width, pass_field_height)
        pass2_rect = pygame.Rect(content_x, pass2_field_y, content_width, pass2_field_height)
        
        admin_login_rect = pygame.Rect(content_x, login_field_y, content_width, login_field_height)
        admin_pass_rect = pygame.Rect(content_x, pass_field_y, content_width, pass_field_height)
        admin_pass2_rect = pygame.Rect(content_x, pass2_field_y, content_width, pass2_field_height)
        
        if not admin_creation_mode:
            if register_btn is None:
                register_btn = AnimatedButton(
                    content_x, register_btn_y, content_width, button_height,
                    'СОЗДАТЬ АККАУНТ', button_font, ACCENT, CARD_COLOR, ACCENT_HOVER
                )
                login_btn = AnimatedButton(
                    content_x, login_btn_y, content_width, button_height,
                    'ВОЙТИ', button_font, ACCENT, CARD_COLOR, ACCENT_HOVER
                )
            else:
                register_btn.set_position(content_x, register_btn_y)
                register_btn.original_rect.width = content_width
                register_btn.original_rect.height = button_height
                login_btn.set_position(content_x, login_btn_y)
                login_btn.original_rect.width = content_width
                login_btn.original_rect.height = button_height
            
            register_btn.update(dt, mouse_pos, mouse_pressed)
            login_btn.update(dt, mouse_pos, mouse_pressed)
        else:
            if admin_register_btn is None:
                admin_register_btn = AnimatedButton(
                    content_x, register_btn_y, content_width, button_height,
                    'СОЗДАТЬ АДМИНИСТРАТОРА', button_font, ACCENT, CARD_COLOR, ACCENT_HOVER
                )
                admin_back_btn = AnimatedButton(
                    content_x, login_btn_y, content_width, button_height,
                    'НАЗАД', button_font, ERROR_COLOR, CARD_COLOR
                )
            else:
                admin_register_btn.set_position(content_x, register_btn_y)
                admin_register_btn.original_rect.width = content_width
                admin_register_btn.original_rect.height = button_height
                admin_back_btn.set_position(content_x, login_btn_y)
                admin_back_btn.original_rect.width = content_width
                admin_back_btn.original_rect.height = button_height
            
            admin_register_btn.update(dt, mouse_pos, mouse_pressed)
            admin_back_btn.update(dt, mouse_pos, mouse_pressed)
        
        user_data = get_user_data()
        
        if error_timer > 0:
            error_timer -= 1
        else:
            reg_error = False
            error_message = ''
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            
            if e.type == pygame.VIDEORESIZE and not is_fullscreen:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                window_size = (e.w, e.h)
                save_window_settings(e.w, e.h, is_fullscreen)
                lava_lamp = LavaLamp(e.w, e.h)
                continue
            
            if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                toggle_fullscreen()
                pygame.display.flip()
                new_width, new_height = screen.get_size()
                lava_lamp = LavaLamp(new_width, new_height)
                continue
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                channel_click.play(click)
                
                if not admin_creation_mode:
                    login_active = login_rect.collidepoint(e.pos)
                    pass_active = pass_rect.collidepoint(e.pos)
                    pass2_active = pass2_rect.collidepoint(e.pos)
                    admin_login_active = False
                    admin_pass_active = False
                    admin_pass2_active = False
                else:
                    admin_login_active = admin_login_rect.collidepoint(e.pos)
                    admin_pass_active = admin_pass_rect.collidepoint(e.pos)
                    admin_pass2_active = admin_pass2_rect.collidepoint(e.pos)
                    login_active = False
                    pass_active = False
                    pass2_active = False
            
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_LALT, pygame.K_RALT, 
                             pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LMETA, pygame.K_RMETA]:
                    continue
                
                if not admin_creation_mode:
                    if login_active:
                        if e.key == pygame.K_BACKSPACE:
                            login_text = login_text[:-1]
                        elif e.key == pygame.K_TAB:
                            login_active = False
                            pass_active = True
                        elif e.key == pygame.K_RETURN:
                            pass_active = True
                            login_active = False
                        else:
                            filtered = filter_input(e.unicode, 30 - len(login_text))
                            login_text += filtered
                            
                    elif pass_active:
                        if e.key == pygame.K_BACKSPACE:
                            pass_text = pass_text[:-1]
                        elif e.key == pygame.K_TAB:
                            pass_active = False
                            pass2_active = True
                        elif e.key == pygame.K_RETURN:
                            pass2_active = True
                            pass_active = False
                        else:
                            filtered = filter_input(e.unicode, 30 - len(pass_text))
                            pass_text += filtered
                            
                    elif pass2_active:
                        if e.key == pygame.K_BACKSPACE:
                            pass2_text = pass2_text[:-1]
                        elif e.key == pygame.K_TAB:
                            pass2_active = False
                            login_active = True
                        elif e.key == pygame.K_RETURN:
                            auth.auth()
                            return
                        else:
                            filtered = filter_input(e.unicode, 30 - len(pass2_text))
                            pass2_text += filtered
                else:
                    if admin_login_active:
                        if e.key == pygame.K_BACKSPACE:
                            admin_login_text = admin_login_text[:-1]
                        elif e.key == pygame.K_TAB:
                            admin_login_active = False
                            admin_pass_active = True
                        elif e.key == pygame.K_RETURN:
                            admin_pass_active = True
                            admin_login_active = False
                        else:
                            filtered = filter_input(e.unicode, 30 - len(admin_login_text))
                            admin_login_text += filtered
                            
                    elif admin_pass_active:
                        if e.key == pygame.K_BACKSPACE:
                            admin_pass_text = admin_pass_text[:-1]
                        elif e.key == pygame.K_TAB:
                            admin_pass_active = False
                            admin_pass2_active = True
                        elif e.key == pygame.K_RETURN:
                            admin_pass2_active = True
                            admin_pass_active = False
                        else:
                            filtered = filter_input(e.unicode, 30 - len(admin_pass_text))
                            admin_pass_text += filtered
                            
                    elif admin_pass2_active:
                        if e.key == pygame.K_BACKSPACE:
                            admin_pass2_text = admin_pass2_text[:-1]
                        elif e.key == pygame.K_TAB:
                            admin_pass2_active = False
                            admin_login_active = True
                        elif e.key == pygame.K_RETURN:
                            auth.auth()
                            return
                        else:
                            filtered = filter_input(e.unicode, 30 - len(admin_pass2_text))
                            admin_pass2_text += filtered
        
        if mouse_released and not ignore_clicks:
            if not admin_creation_mode:
                if register_btn and register_btn.is_clicked(mouse_pos, True):
                    from db_manager import verify_secret_key, generate_daily_secret_key
                    
                    current_key = generate_daily_secret_key()
                    print(f"DEBUG: Current secret key = '{current_key}'")
                    print(f"DEBUG: Entered login = '{login_text}'")
                    print(f"DEBUG: Pass empty = {not pass_text}, Pass2 empty = {not pass2_text}")
                    print(f"DEBUG: Verify result = {verify_secret_key(login_text)}")
                    
                    if login_text and not pass_text and not pass2_text and verify_secret_key(login_text):
                        print("DEBUG: SECRET KEY MATCHED! Entering admin creation mode")
                        admin_creation_mode = True
                        login_text = ''
                        pass_text = ''
                        pass2_text = ''
                        admin_login_text = ''
                        admin_pass_text = ''
                        admin_pass2_text = ''
                        reg_error = False
                        error_message = ''
                        continue
                    elif not login_text:
                        reg_error = True
                        error_message = 'Введите логин'
                        error_timer = 120
                    elif not pass_text:
                        reg_error = True
                        error_message = 'Введите пароль'
                        error_timer = 120
                    elif pass_text != pass2_text:
                        reg_error = True
                        error_message = 'Пароли не совпадают'
                        error_timer = 120
                    elif login_text in user_data['logins'] or is_admin(login_text):
                        reg_error = True
                        error_message = 'Логин уже существует'
                        error_timer = 120
                    else:
                        login_id = len(user_data['logins'])
                        new_id = login_id + 1
                        add_user(new_id, login_text, pass_text)
                        menu.menu(login_text, 0)
                
                if login_btn and login_btn.is_clicked(mouse_pos, True):
                    auth.auth()
            else:
                if admin_register_btn and admin_register_btn.is_clicked(mouse_pos, True):
                    if not admin_login_text:
                        reg_error = True
                        error_message = 'Введите логин администратора'
                        error_timer = 120
                    elif not admin_pass_text:
                        reg_error = True
                        error_message = 'Введите пароль администратора'
                        error_timer = 120
                    elif admin_pass_text != admin_pass2_text:
                        reg_error = True
                        error_message = 'Пароли не совпадают'
                        error_timer = 120
                    elif admin_login_text in user_data['logins'] or is_admin(admin_login_text):
                        reg_error = True
                        error_message = 'Логин уже существует'
                        error_timer = 120
                    else:
                        from db_manager import add_admin
                        if add_admin(admin_login_text, admin_pass_text):
                            login_id = len(user_data['logins'])
                            new_id = login_id + 1
                            add_user(new_id, admin_login_text, admin_pass_text)
                            admin_panel.admin_panel(admin_login_text, 0)
                            return
                        else:
                            reg_error = True
                            error_message = 'Ошибка создания администратора'
                            error_timer = 120
                
                if admin_back_btn and admin_back_btn.is_clicked(mouse_pos, True):
                    admin_creation_mode = False
                    login_text = ''
                    pass_text = ''
                    pass2_text = ''
                    admin_login_text = ''
                    admin_pass_text = ''
                    admin_pass2_text = ''
                    reg_error = False
                    error_message = ''
                    continue
        
        lava_lamp.draw(screen)
        
        shadow_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 30), (0, 0, card_width, card_height), border_radius=24)
        screen.blit(shadow_surf, (card_x + 2, card_y + 4))
        
        card_surf = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (*CARD_COLOR, 245), (0, 0, card_width, card_height), border_radius=24)
        screen.blit(card_surf, (card_x, card_y))
        
        title_text = title_font.render('DeepCore', True, TEXT_PRIMARY)
        title_x = card_x + (card_width - title_text.get_width()) // 2
        screen.blit(title_text, (title_x, title_y))
        
        if not admin_creation_mode:
            subtitle_text = small_font.render('Создание аккаунта', True, TEXT_SECONDARY)
            subtitle_x = card_x + (card_width - subtitle_text.get_width()) // 2
            screen.blit(subtitle_text, (subtitle_x, title_y + 55))
            
            login_label = small_font.render('Логин', True, TEXT_SECONDARY)
            screen.blit(login_label, (content_x, login_label_y))
            
            border_color = ACCENT if login_active else BORDER_COLOR
            pygame.draw.rect(screen, INPUT_BG, login_rect, border_radius=12)
            pygame.draw.rect(screen, border_color, login_rect, 2, border_radius=12)
            
            login_surface = input_font.render(login_text, True, TEXT_PRIMARY)
            if login_surface.get_width() > content_width - 30:
                login_surface = input_font.render(login_text[:25] + '...', True, TEXT_PRIMARY)
            login_text_y = login_field_y + (login_field_height - login_surface.get_height()) // 2
            screen.blit(login_surface, (content_x + 15, login_text_y))
            
            pass_label = small_font.render('Пароль', True, TEXT_SECONDARY)
            screen.blit(pass_label, (content_x, pass_label_y))
            
            border_color = ACCENT if pass_active else BORDER_COLOR
            pygame.draw.rect(screen, INPUT_BG, pass_rect, border_radius=12)
            pygame.draw.rect(screen, border_color, pass_rect, 2, border_radius=12)
            
            pass_display = '*' * len(pass_text)
            pass_surface = input_font.render(pass_display, True, TEXT_PRIMARY)
            pass_text_y = pass_field_y + (pass_field_height - pass_surface.get_height()) // 2
            screen.blit(pass_surface, (content_x + 15, pass_text_y))
            
            pass2_label = small_font.render('Подтверждение пароля', True, TEXT_SECONDARY)
            screen.blit(pass2_label, (content_x, pass2_label_y))
            
            border_color = ACCENT if pass2_active else BORDER_COLOR
            pygame.draw.rect(screen, INPUT_BG, pass2_rect, border_radius=12)
            pygame.draw.rect(screen, border_color, pass2_rect, 2, border_radius=12)
            
            pass2_display = '*' * len(pass2_text)
            pass2_surface = input_font.render(pass2_display, True, TEXT_PRIMARY)
            pass2_text_y = pass2_field_y + (pass2_field_height - pass2_surface.get_height()) // 2
            screen.blit(pass2_surface, (content_x + 15, pass2_text_y))
            
            if register_btn:
                register_btn.draw(screen)
            if login_btn:
                login_btn.draw(screen)
            
        else:
            subtitle_text = small_font.render('Создание аккаунта администратора', True, ACCENT)
            subtitle_x = card_x + (card_width - subtitle_text.get_width()) // 2
            screen.blit(subtitle_text, (subtitle_x, title_y + 55))
            
            login_label = small_font.render('Логин администратора', True, TEXT_SECONDARY)
            screen.blit(login_label, (content_x, login_label_y))
            
            border_color = ACCENT if admin_login_active else BORDER_COLOR
            pygame.draw.rect(screen, INPUT_BG, admin_login_rect, border_radius=12)
            pygame.draw.rect(screen, border_color, admin_login_rect, 2, border_radius=12)
            
            login_surface = input_font.render(admin_login_text, True, TEXT_PRIMARY)
            if login_surface.get_width() > content_width - 30:
                login_surface = input_font.render(admin_login_text[:25] + '...', True, TEXT_PRIMARY)
            login_text_y = login_field_y + (login_field_height - login_surface.get_height()) // 2
            screen.blit(login_surface, (content_x + 15, login_text_y))
            
            pass_label = small_font.render('Пароль администратора', True, TEXT_SECONDARY)
            screen.blit(pass_label, (content_x, pass_label_y))
            
            border_color = ACCENT if admin_pass_active else BORDER_COLOR
            pygame.draw.rect(screen, INPUT_BG, admin_pass_rect, border_radius=12)
            pygame.draw.rect(screen, border_color, admin_pass_rect, 2, border_radius=12)
            
            pass_display = '*' * len(admin_pass_text)
            pass_surface = input_font.render(pass_display, True, TEXT_PRIMARY)
            pass_text_y = pass_field_y + (pass_field_height - pass_surface.get_height()) // 2
            screen.blit(pass_surface, (content_x + 15, pass_text_y))
            
            pass2_label = small_font.render('Подтверждение пароля', True, TEXT_SECONDARY)
            screen.blit(pass2_label, (content_x, pass2_label_y))
            
            border_color = ACCENT if admin_pass2_active else BORDER_COLOR
            pygame.draw.rect(screen, INPUT_BG, admin_pass2_rect, border_radius=12)
            pygame.draw.rect(screen, border_color, admin_pass2_rect, 2, border_radius=12)
            
            pass2_display = '*' * len(admin_pass2_text)
            pass2_surface = input_font.render(pass2_display, True, TEXT_PRIMARY)
            pass2_text_y = pass2_field_y + (pass2_field_height - pass2_surface.get_height()) // 2
            screen.blit(pass2_surface, (content_x + 15, pass2_text_y))
            
            if admin_register_btn:
                admin_register_btn.draw(screen)
            if admin_back_btn:
                admin_back_btn.draw(screen)
        
        if reg_error:
            error_text = small_font.render(error_message, True, ERROR_COLOR)
            error_x = card_x + (card_width - error_text.get_width()) // 2
            error_y = register_btn_y + button_height + 5
            screen.blit(error_text, (error_x, error_y))
        
        effect_manager.draw(screen, current_width, current_height)

        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()