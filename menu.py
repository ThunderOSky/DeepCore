import pygame
import sys
import math
import random
import auth, settings, top, profile, menu_game
from theme import *
from settings_manager import *
from db_manager import *
from notifications import NotificationManager
from notification_queue import get_pending
from ui import AnimatedButton
from effects import *
from music_manager import *
import admin_panel
import sqlite3

def show_daily_leaders_screen(nickname):
    import game
    pygame.init()
    
    volume_sound = get_sound()
    THEME = get_theme()
    set_theme(THEME)
    music_manager = MusicManager()
    
    click = music_manager.load_sound('click.mp3')
    channel_click = pygame.mixer.Channel(0)
    channel_click.set_volume(volume_sound)
    
    saved_width, saved_height, saved_fullscreen = load_window_settings(1366, 768)
    
    if saved_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((saved_width, saved_height), pygame.RESIZABLE)
    
    is_fullscreen = saved_fullscreen
    window_size = (saved_width, saved_height) if not saved_fullscreen else (1366, 768)
    
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
    
    particles = []
    for i in range(40):
        particles.append({
            'x': random.randint(0, saved_width),
            'y': random.randint(0, saved_height),
            'size': random.randint(2, 5),
            'speed_x': random.uniform(-0.2, 0.2),
            'speed_y': random.uniform(-0.2, 0.2),
            'alpha': random.randint(30, 80),
            'phase': random.uniform(0, math.pi * 2)
        })
    
    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)

    last_theme = THEME
    
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    is_champion = is_champion_season_active()
    
    if is_champion:
        leaders = get_champion_leaders()
        title_text_str = 'CHAMPIONS'
    else:
        leaders = get_daily_leaders(today)
        title_text_str = 'ИГРА ДНЯ'
    
    back_btn = None
    play_btn = None
    
    mouse_was_pressed = False
    ignore_clicks = True
    frames_passed = 0
    
    run = True
    clock = pygame.time.Clock()
    
    while run:
        dt = clock.get_time() / 1000.0
        current_width, current_height = screen.get_size()
        if current_effect != get_effect():
            current_effect = get_effect()
            effect_manager.set_effect(current_effect, current_width, current_height)
        effect_manager.update(dt, current_width, current_height)
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_released = not mouse_pressed and mouse_was_pressed
        mouse_was_pressed = mouse_pressed
        
        frames_passed += 1
        if frames_passed > 5:
            ignore_clicks = False
        
        current_theme_name = get_theme()
        if last_theme != current_theme_name:
            last_theme = current_theme_name
            set_theme(current_theme_name)
        
        theme = get_current_theme()
        ACCENT = theme['accent']
        ACCENT_HOVER = theme['accent_hover']
        CARD_COLOR = theme['card']
        TEXT_PRIMARY = theme['text']
        TEXT_SECONDARY = theme['text_secondary']
        
        for p in particles:
            p['x'] += p['speed_x']
            p['y'] += p['speed_y']
            p['phase'] += 0.01
            if p['x'] < -50: p['x'] = current_width + 50
            if p['x'] > current_width + 50: p['x'] = -50
            if p['y'] < -50: p['y'] = current_height + 50
            if p['y'] > current_height + 50: p['y'] = -50
        
        center_x = current_width // 2
        title_y = int(current_height * 0.08)
        
        table_y = int(current_height * 0.20)
        table_width = int(current_width * 0.7)
        table_height = int(current_height * 0.55)
        table_x = center_x - table_width // 2
        
        back_btn_w = 200
        back_btn_h = 50
        back_btn_x = center_x - back_btn_w // 2
        back_btn_y = table_y + table_height + 70
        
        play_btn_w = 250
        play_btn_h = 50
        play_btn_x = center_x - play_btn_w // 2
        play_btn_y = back_btn_y - 60
        
        if back_btn is None:
            back_btn = AnimatedButton(back_btn_x, back_btn_y, back_btn_w, back_btn_h,
                                      'НАЗАД', button_font, ACCENT, CARD_COLOR, ACCENT_HOVER)
            play_btn = AnimatedButton(play_btn_x, play_btn_y, play_btn_w, play_btn_h,
                                      'ИГРАТЬ', button_font, ACCENT, CARD_COLOR, ACCENT_HOVER)
        else:
            back_btn.set_position(back_btn_x, back_btn_y)
            back_btn.original_rect.width = back_btn_w
            back_btn.original_rect.height = back_btn_h
            play_btn.set_position(play_btn_x, play_btn_y)
            play_btn.original_rect.width = play_btn_w
            play_btn.original_rect.height = play_btn_h
        
        can_play = not has_played_daily(nickname, today)

        if can_play:
            play_btn.text = 'ИГРАТЬ'
            if is_champion:
                play_btn.base_color = get_champion_color()
            else:
                play_btn.base_color = ACCENT
            play_btn.hover_color = ACCENT_HOVER
            play_btn.text_color = CARD_COLOR
        else:
            play_btn.text = 'УЖЕ СЫГРАНО'
            play_btn.base_color = (60, 60, 60) if sum(ACCENT) < 400 else (200, 200, 200)
            play_btn.hover_color = play_btn.base_color
            play_btn.text_color = (150, 150, 150)
        
        back_btn.update(dt, mouse_pos, mouse_pressed)
        play_btn.update(dt, mouse_pos, mouse_pressed)
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            
            if e.type == pygame.VIDEORESIZE and not is_fullscreen:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                window_size = (e.w, e.h)
                save_window_settings(e.w, e.h, is_fullscreen)
                continue
            
            if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                toggle_fullscreen()
                pygame.display.flip()
                continue
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                channel_click.play(click)
        
        if mouse_released and not ignore_clicks:
            if back_btn.is_clicked(mouse_pos, True):
                menu(nickname, 1)
                return
            
            if play_btn.is_clicked(mouse_pos, True) and can_play:
                start_daily_game(nickname)
                return
        
        for y in range(current_height):
            ratio = y / current_height
            r = int(theme['background'][0] - ratio * 15)
            g = int(theme['background'][1] - ratio * 15)
            b = int(theme['background'][2] - ratio * 15)
            pygame.draw.line(screen, (max(0, r), max(0, g), max(0, b)), (0, y), (current_width, y))
        
        for p in particles:
            alpha = int(p['alpha'] + math.sin(p['phase']) * 20)
            alpha = max(20, min(100, alpha))
            color = (*ACCENT, alpha)
            temp_surf = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, color, (p['size'], p['size']), p['size'])
            screen.blit(temp_surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))
        
        frame_padding = 20
        frame_rect = pygame.Rect(frame_padding, frame_padding, current_width - frame_padding * 2, current_height - frame_padding * 2)
        pygame.draw.rect(screen, ACCENT, frame_rect, 2, border_radius=12)
        
        title_color = get_champion_color() if is_champion else ACCENT
        title_text = title_font.render(title_text_str, True, title_color)
        title_x = center_x - title_text.get_width() // 2
        screen.blit(title_text, (title_x, title_y))
        
        table_rect = pygame.Rect(table_x, table_y, table_width, table_height)
        pygame.draw.rect(screen, CARD_COLOR, table_rect, border_radius=15)
        pygame.draw.rect(screen, ACCENT, table_rect, 2, border_radius=15)
        
        headers = ["#", "Игрок", "Время"]
        col_widths = [int(table_width * 0.15), int(table_width * 0.50), int(table_width * 0.35)]
        
        header_y = table_y + 15
        x_offset = table_x + 10
        
        for i, header in enumerate(headers):
            text = small_font.render(header, True, ACCENT)
            if i == 0:
                text_x = x_offset + 5
            else:
                text_x = x_offset + sum(col_widths[:i]) + (col_widths[i] - text.get_width()) // 2
            screen.blit(text, (text_x, header_y))
        
        line_y = header_y + small_font.get_height() + 8
        pygame.draw.line(screen, ACCENT, (table_x + 10, line_y), (table_x + table_width - 10, line_y), 1)
        
        start_y = line_y + 10
        row_height = 40
        max_rows = (table_height - (start_y - table_y)) // row_height
        display_rows = min(len(leaders), max_rows)
        
        for i in range(display_rows):
            username, time_val = leaders[i]
            y = start_y + i * row_height
            
            num_text = small_font.render(str(i + 1), True, TEXT_PRIMARY)
            screen.blit(num_text, (x_offset + 5, y + 8))
            
            name_color = get_nickname_color(username)
            if name_color == 'default':
                color = TEXT_PRIMARY
            elif name_color.startswith('#'):
                color = hex_to_rgb(name_color)
            else:
                color = get_animated_color(name_color)
            
            name_text = small_font.render(username[:15], True, color)
            name_x = x_offset + col_widths[0] + (col_widths[1] - name_text.get_width()) // 2
            screen.blit(name_text, (name_x, y + 8))
            
            time_text = small_font.render(f"{time_val:.2f} сек", True, TEXT_PRIMARY)
            time_x = x_offset + col_widths[0] + col_widths[1] + (col_widths[2] - time_text.get_width()) // 2
            screen.blit(time_text, (time_x, y + 8))
        
        if not leaders:
            empty_text = button_font.render("Пока никто не победил", True, TEXT_SECONDARY)
            screen.blit(empty_text, empty_text.get_rect(center=table_rect.center))
        
        back_btn.draw(screen)
        play_btn.draw(screen)

        effect_manager.draw(screen, current_width, current_height)
        
        pygame.display.update()
        clock.tick(60)

def become_admin(nickname):
    from db_manager import get_user_data, check_admin_credentials
    
    user_data = get_user_data()
    password = None
    for i in range(len(user_data['logins'])):
        if user_data['logins'][i] == nickname:
            password = user_data['passwords'][i]
            break
    
    if not is_admin(nickname):
        if password:
            from db_manager import create_admins_table
            conn = sqlite3.connect('database/game.db')
            c = conn.cursor()
            try:
                c.execute('INSERT INTO admins (user, password) VALUES (?, ?)', (nickname, password))
                conn.commit()
            except:
                pass
            conn.close()
    
    admin_panel.admin_panel(nickname, 0)


def logout_and_clear():
    from settings_manager import clear_last_user
    clear_last_user()
    auth.auth()

def start_daily_game(nickname):
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    if is_champion_season_active():
        season = get_active_season()
        seed = season[5]
        difficulty = 'hard'
        rows, cols, mines = 16, 16, 40
    else:
        seed_data = generate_daily_game(today)
        seed = seed_data[0]
        difficulty = 'average'
        rows, cols, mines = 12, 12, 20
    
    import game
    game.game(nickname, difficulty, 'classic', None, None, None, 
              daily_mode=True, daily_date=today, daily_seed=seed)  


def menu(nickname, status):
    pygame.init()
    
    has_admin_achievement = False
    pa = get_player_achievements(nickname)
    for ach in pa:
        if ach[1] == "Администратор":
            has_admin_achievement = True
            break

    volume_music = get_music()
    volume_sound = get_sound()
    theme_name = get_theme()
    
    set_theme(theme_name)
    
    music_manager = get_music_manager()
    
    click = music_manager.load_sound('click.mp3')
    channel_click = pygame.mixer.Channel(0)
    channel_click.set_volume(volume_sound)

    notification_manager = NotificationManager(music_manager)
    
    if status != 1:
        music_manager.load_music('menu', volume_music)
        status = 1

        check_top_achievements(nickname)
        
        pending = get_pending()
        for p in pending:
            notification_manager.add_notification(p['title'], p['text'], p['type'])
    
    saved_width, saved_height, saved_fullscreen = load_window_settings(1366, 768)
    
    if saved_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((saved_width, saved_height), pygame.RESIZABLE)
    
    pygame.display.set_caption('DeepCore')

    check_time_achievements(nickname)

    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)
    
    is_fullscreen = saved_fullscreen
    window_size = (saved_width, saved_height) if not saved_fullscreen else (1366, 768)
    
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
    
    particles = []
    for i in range(40):
        particles.append({
            'x': random.randint(0, saved_width),
            'y': random.randint(0, saved_height),
            'size': random.randint(2, 5),
            'speed_x': random.uniform(-0.2, 0.2),
            'speed_y': random.uniform(-0.2, 0.2),
            'alpha': random.randint(30, 80),
            'phase': random.uniform(0, math.pi * 2)
        })
    
    last_theme = theme_name
    
    menu_btns = {}
    settings_btn = None
    exit_btn = None
    
    mouse_was_pressed = False
    ignore_clicks = True
    frames_passed = 0
    
    run = True
    clock = pygame.time.Clock()
    
    while run:
        current_width, current_height = screen.get_size()
        click_blocked = notification_manager.has_active() and notification_manager.skip_current()
        
        dt = clock.get_time() / 1000.0

        if current_effect != get_effect():
            current_effect = get_effect()
            effect_manager.set_effect(current_effect, current_width, current_height)
        effect_manager.update(dt, current_width, current_height)

        notification_manager.update(dt)

        if pygame.time.get_ticks() % 1000 < 20:
            pending = get_pending()
            for p in pending:
                notification_manager.add_notification(p['title'], p['text'], p['type'])

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mouse_released = not mouse_pressed and mouse_was_pressed
        mouse_was_pressed = mouse_pressed
        
        frames_passed += 1
        if frames_passed > 5:
            ignore_clicks = False
        
        current_theme_name = get_theme()
        if last_theme != current_theme_name:
            last_theme = current_theme_name
            set_theme(current_theme_name)
        
        theme = get_current_theme()
        BG_COLOR = theme['background']
        TEXT_PRIMARY = theme['text']
        TEXT_SECONDARY = theme['text_secondary']
        ACCENT = theme['accent']
        ACCENT_HOVER = theme['accent_hover']
        CARD_COLOR = theme['card']
        ERROR_COLOR = theme['error']
        
        for p in particles:
            p['x'] += p['speed_x']
            p['y'] += p['speed_y']
            p['phase'] += 0.01
            if p['x'] < -50: p['x'] = current_width + 50
            if p['x'] > current_width + 50: p['x'] = -50
            if p['y'] < -50: p['y'] = current_height + 50
            if p['y'] > current_height + 50: p['y'] = -50
        
        center_x = current_width // 2
        
        logo_y = int(current_height * 0.15)
        nickname_y = int(current_height * 0.25)
        
        menu_start_y = int(current_height * 0.37)
        button_width = min(int(current_width * 0.28), 260)
        button_height = int(current_height * 0.065)
        button_spacing = int(current_height * 0.013)
        
        is_champion = is_champion_season_active()
        
        button_data = [
            {'id': 'play', 'text': 'ИГРАТЬ', 'action': lambda: menu_game.menu_game(nickname), 'color': ACCENT},
            {'id': 'daily', 'text': 'CHAMPIONS' if is_champion else 'ИГРА ДНЯ', 
             'action': lambda: show_daily_leaders_screen(nickname), 
             'color': get_champion_color() if is_champion else ACCENT},
            {'id': 'profile', 'text': 'ПРОФИЛЬ', 'action': lambda: profile.profile(nickname), 'color': ACCENT},
            {'id': 'top', 'text': 'ЧЕМПИОНЫ', 'action': lambda: top.top(nickname), 'color': ACCENT},
            {'id': 'logout', 'text': 'ВЫЙТИ ИЗ АККАУНТА', 'action': lambda: logout_and_clear(), 'color': ACCENT},
        ]
        if has_admin_achievement:
            button_data.append({'id': 'become_admin', 'text': 'ВОЙТИ КАК АДМИНИСТРАТОР', 
                            'action': lambda: become_admin(nickname), 'color': ACCENT})
        
        for i, data in enumerate(button_data):
            btn_id = data['id']
            x = center_x - button_width // 2
            y = menu_start_y + i * (button_height + button_spacing)
            
            if btn_id not in menu_btns:
                menu_btns[btn_id] = AnimatedButton(
                    x, y, button_width, button_height,
                    data['text'], button_font, data['color'], CARD_COLOR, ACCENT_HOVER
                )
            else:
                menu_btns[btn_id].set_position(x, y)
                menu_btns[btn_id].original_rect.width = button_width
                menu_btns[btn_id].original_rect.height = button_height
                menu_btns[btn_id].text = data['text']
                menu_btns[btn_id].base_color = data['color']
        
        bottom_button_width = 100
        bottom_button_height = 36
        
        settings_btn_x = 25
        settings_btn_y = current_height - bottom_button_height - 25
        exit_btn_x = current_width - bottom_button_width - 25
        exit_btn_y = current_height - bottom_button_height - 25
        
        if settings_btn is None:
            settings_btn = AnimatedButton(settings_btn_x, settings_btn_y, bottom_button_width, bottom_button_height,
                                         'Настройки', small_font, ACCENT, CARD_COLOR)
            exit_btn = AnimatedButton(exit_btn_x, exit_btn_y, bottom_button_width, bottom_button_height,
                                      'Выход', small_font, ERROR_COLOR, CARD_COLOR)
        else:
            settings_btn.set_position(settings_btn_x, settings_btn_y)
            exit_btn.set_position(exit_btn_x, exit_btn_y)
        
        for btn in menu_btns.values():
            btn.update(dt, mouse_pos, mouse_pressed)
        settings_btn.update(dt, mouse_pos, mouse_pressed)
        exit_btn.update(dt, mouse_pos, mouse_pressed)
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            
            if e.type == pygame.VIDEORESIZE and not is_fullscreen:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                window_size = (e.w, e.h)
                save_window_settings(e.w, e.h, is_fullscreen)
                continue
            
            if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                toggle_fullscreen()
                pygame.display.flip()
                continue
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                if click_blocked:
                    notification_manager.update(0, skip_current=True)
                else:
                    channel_click.play(click)
        
        if mouse_released and not ignore_clicks and not click_blocked:
            for data in button_data:
                btn_id = data['id']
                if menu_btns[btn_id].is_clicked(mouse_pos, True):
                    data['action']()
                    break
            
            if settings_btn.is_clicked(mouse_pos, True):
                settings.settings(nickname, "menu")
            
            if exit_btn.is_clicked(mouse_pos, True):
                sys.exit()
        
        for y in range(current_height):
            ratio = y / current_height
            r = int(BG_COLOR[0] - ratio * 15)
            g = int(BG_COLOR[1] - ratio * 15)
            b = int(BG_COLOR[2] - ratio * 15)
            pygame.draw.line(screen, (max(0, r), max(0, g), max(0, b)), (0, y), (current_width, y))
        
        for p in particles:
            alpha = int(p['alpha'] + math.sin(p['phase']) * 20)
            alpha = max(20, min(100, alpha))
            color = (*ACCENT, alpha)
            temp_surf = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, color, (p['size'], p['size']), p['size'])
            screen.blit(temp_surf, (int(p['x'] - p['size']), int(p['y'] - p['size'])))
        
        frame_padding = 20
        frame_rect = pygame.Rect(frame_padding, frame_padding, current_width - frame_padding * 2, current_height - frame_padding * 2)
        pygame.draw.rect(screen, ACCENT, frame_rect, 2, border_radius=12)
        
        logo_text = title_font.render('DEEPCORE', True, ACCENT)
        logo_x = center_x - logo_text.get_width() // 2
        screen.blit(logo_text, (logo_x, logo_y))
        
        nickname_color = get_nickname_color(nickname)
        if nickname_color == 'default':
            color_rgb = TEXT_PRIMARY
        elif nickname_color.startswith('#'):
            color_rgb = hex_to_rgb(nickname_color)
        else:
            color_rgb = get_animated_color(nickname_color)
        
        nickname_surf = subtitle_font.render(nickname, True, color_rgb)
        nickname_x = center_x - nickname_surf.get_width() // 2
        screen.blit(nickname_surf, (nickname_x, nickname_y))
        
        line_width = 150
        line_rect = pygame.Rect(center_x - line_width // 2, nickname_y + 45, line_width, 2)
        pygame.draw.rect(screen, ACCENT, line_rect)
        
        for btn in menu_btns.values():
            btn.draw(screen)
        settings_btn.draw(screen)
        exit_btn.draw(screen)
        
        version_text = small_font.render('v0.4.3.1', True, TEXT_SECONDARY)
        screen.blit(version_text, (3, current_height - 22))
        
        notification_manager.draw(screen, current_width, theme)

        effect_manager.draw(screen, current_width, current_height)

        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()