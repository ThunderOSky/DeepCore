import pygame
import sys
import math
import random
from theme import *
from settings_manager import *
from db_manager import *
from ui import AnimatedButton
from datetime import datetime, timedelta
from music_manager import get_music_manager
from effects import *
import menu
from backup_dialog import *

def admin_panel(nickname, status):
    pygame.init()
    
    volume_music = get_music()
    volume_sound = get_sound()
    theme_name = get_theme()
    set_theme(theme_name)
    
    music_manager = get_music_manager()
    
    click = music_manager.load_sound('click.mp3')
    channel_click = pygame.mixer.Channel(0)
    channel_click.set_volume(volume_sound)
    
    if status == 0:
        music_manager.load_music('menu', volume_music)
        check_and_notify(nickname, 'is_admin', 1)
        status = 1
    
    saved_width, saved_height, saved_fullscreen = load_window_settings(1366, 768)
    
    if saved_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((saved_width, saved_height), pygame.RESIZABLE)
    
    pygame.display.set_caption('DeepCore - Панель администратора')
    
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

    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)

    particles = [{
        'x': random.randint(0, saved_width), 'y': random.randint(0, saved_height),
        'size': random.randint(2, 5), 'speed_x': random.uniform(-0.2, 0.2),
        'speed_y': random.uniform(-0.2, 0.2), 'alpha': random.randint(30, 80),
        'phase': random.uniform(0, math.pi * 2)
    } for _ in range(40)]
    
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
        if frames_passed > 3: ignore_clicks = False
        
        current_theme_name = get_theme()
        if last_theme != current_theme_name:
            last_theme = current_theme_name
            set_theme(current_theme_name)
        
        theme = get_current_theme()
        TEXT_PRIMARY = theme['text']
        TEXT_SECONDARY = theme['text_secondary']
        ACCENT = theme['accent']
        ACCENT_HOVER = theme['accent_hover']
        CARD_COLOR = theme['card']
        ERROR_COLOR = theme['error']
        
        copy_notification = ""
        copy_notification_timer = 0

        for p in particles:
            p['x'] += p['speed_x']
            p['y'] += p['speed_y']
            p['phase'] += 0.01
            if p['x'] < -50:
                p['x'] = current_width + 50
            if p['x'] > current_width + 50:
                p['x'] = -50
            if p['y'] < -50:
                p['y'] = current_height + 50
            if p['y'] > current_height + 50:
                p['y'] = -50
        
        center_x = current_width // 2
        title_y = int(current_height * 0.12)
        subtitle_y = int(current_height * 0.2)
        
        menu_start_y = int(current_height * 0.3)
        button_width = min(int(current_width * 0.35), 320)
        button_height = int(current_height * 0.065)
        button_spacing = int(current_height * 0.02)
        
        button_data = [
            {'id': 'edit_top', 'text': 'РЕДАКТИРОВАНИЕ ТОПА', 'action': lambda: edit_top(screen, current_width, current_height, nickname)},
            {'id': 'daily_settings', 'text': 'УПРАВЛЕНИЕ ИГРОЙ ДНЯ', 'action': lambda: daily_season_settings(screen, current_width, current_height, nickname)},
            {'id': 'change_password', 'text': 'ИЗМЕНИТЬ ПАРОЛЬ ИГРОКА', 'action': lambda: change_player_password(screen, current_width, current_height, nickname)},
            {'id': 'change_nickname', 'text': 'ИЗМЕНИТЬ НИК ИГРОКА', 'action': lambda: change_player_nickname(screen, current_width, current_height, nickname)},
            {'id': 'backup', 'text': 'РЕЗЕРВНОЕ КОПИРОВАНИЕ', 'action': lambda: show_backup_dialog(screen, nickname)},
            {'id': 'play_as_player', 'text': 'ЗАЙТИ КАК ИГРОК', 'action': lambda: play_as_player(nickname)},
            {'id': 'logout', 'text': 'ВЫЙТИ ИЗ СИСТЕМЫ', 'action': lambda: logout_and_clear()},
        ]
        
        for i, data in enumerate(button_data):
            btn_id = data['id']
            x = center_x - button_width // 2
            y = menu_start_y + i * (button_height + button_spacing)
            
            if btn_id not in menu_btns:
                menu_btns[btn_id] = AnimatedButton(x, y, button_width, button_height,
                                                   data['text'], button_font, ACCENT, CARD_COLOR, ACCENT_HOVER)
            else:
                menu_btns[btn_id].set_position(x, y)
                menu_btns[btn_id].original_rect.width = button_width
                menu_btns[btn_id].original_rect.height = button_height
                menu_btns[btn_id].text = data['text']
            menu_btns[btn_id].update(dt, mouse_pos, mouse_pressed)
        
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
                channel_click.play(click)
        
        if mouse_released and not ignore_clicks:
            for data in button_data:
                if menu_btns[data['id']].is_clicked(mouse_pos, True):
                    data['action']()
                    return
            if settings_btn.is_clicked(mouse_pos, True):
                import settings
                settings.settings(nickname, "admin_panel")
                return
            if exit_btn.is_clicked(mouse_pos, True):
                sys.exit()

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
        
        secret_key = generate_daily_secret_key()
        key_text = f"Секретный ключ: {secret_key}"

        key_shadow = small_font.render(key_text, True, (0, 0, 0, 100))
        key_surface = small_font.render(key_text, True, TEXT_SECONDARY)

        key_x = current_width - key_surface.get_width() - 20
        key_y = current_height - 25

        screen.blit(key_shadow, (key_x + 1, key_y + 1))
        screen.blit(key_surface, (key_x, key_y))
        if copy_notification_timer > 0:
            copy_notification_timer -= dt
            notif_surf = small_font.render(copy_notification, True, theme['win'])
            notif_x = current_width - notif_surf.get_width() - 20
            notif_y = key_y - 25
            if notif_x > 20:
                screen.blit(notif_surf, (notif_x, notif_y))

        title_text = title_font.render('ПАНЕЛЬ АДМИНИСТРАТОРА', True, ACCENT)
        screen.blit(title_text, (center_x - title_text.get_width() // 2, title_y))
        
        nickname_text = subtitle_font.render(nickname, True, TEXT_PRIMARY)
        screen.blit(nickname_text, (center_x - nickname_text.get_width() // 2, subtitle_y))
        
        line_width = 200
        line_rect = pygame.Rect(center_x - line_width // 2, subtitle_y + 40, line_width, 2)
        pygame.draw.rect(screen, ACCENT, line_rect)
        
        for btn in menu_btns.values():
            btn.draw(screen)
        settings_btn.draw(screen)
        exit_btn.draw(screen)
        
        effect_manager.draw(screen, current_width, current_height)

        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()


def play_as_player(admin_nickname):
    from db_manager import add_user, get_user_data, get_admin_by_user, check_and_notify
    
    if not player_exists(admin_nickname):
        admin_data = get_admin_by_user(admin_nickname)
        if admin_data:
            admin_password = admin_data[2]
            user_data = get_user_data()
            new_id = len(user_data['logins']) + 1
            add_user(new_id, admin_nickname, admin_password)

            check_and_notify(admin_nickname, 'is_admin', 1)

    menu.menu(admin_nickname, 0)


def daily_season_settings(screen, current_width, current_height, admin_nickname):
    pygame.init()
    
    volume_sound = get_sound()
    music_manager = get_music_manager()
    click = music_manager.load_sound('click.mp3')
    channel_click = pygame.mixer.Channel(0)
    channel_click.set_volume(volume_sound)
    
    clock = pygame.time.Clock()
    
    c.execute('SELECT * FROM champion_season WHERE is_active = 1 LIMIT 1')
    season = c.fetchone()
    season_active = season is not None
    end_date = season[3] if season_active and len(season) > 3 else ''
    active_field = None
    message = ''
    message_timer = 0

    action_btn = None
    save_btn = None
    back_btn = None
    
    mouse_was_pressed = False
    ignore_clicks = True
    frames_passed = 0
    
    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)

    running = True
    while running:
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
        
        theme = get_current_theme()
        ACCENT = theme['accent']
        ACCENT_HOVER = theme['accent_hover']
        CARD_COLOR = theme['card']
        TEXT_PRIMARY = theme['text']
        TEXT_SECONDARY = theme['text_secondary']
        ERROR_COLOR = theme['error']
        BG_COLOR = theme['background']
        INPUT_BG = theme['input_bg']
        BORDER_COLOR = theme['border']
        
        center_x = current_width // 2
        title_y = int(current_height * 0.06)
        
        card_w = 550
        card_h = 350
        card_x = center_x - card_w // 2
        card_y = int(current_height * 0.15)
        
        field_w = 300
        field_h = 40
        field_x = center_x - field_w // 2
        field_y = card_y + 140
        field_rect = pygame.Rect(field_x, field_y, field_w, field_h)
        
        action_w = 320
        action_h = 50
        action_rect = pygame.Rect(center_x - action_w // 2, card_y + 210, action_w, action_h)
        
        btn_w = 150
        btn_h = 40
        
        save_btn_x = center_x - btn_w - 85
        back_btn_x = center_x + 85

        if action_btn is None:
            action_color = ERROR_COLOR if season_active else get_champion_color()
            action_text = 'ЗАКОНЧИТЬ СЕЗОН ПРЯМО СЕЙЧАС' if season_active else 'НАЧАТЬ СЕЗОН CHAMPIONS'
            action_btn = AnimatedButton(action_rect.x, action_rect.y, action_w, action_h,
                                        action_text, button_font, action_color, CARD_COLOR, ACCENT_HOVER)
            save_btn = AnimatedButton(save_btn_x, card_y + card_h + 20, btn_w, btn_h,
                                      'СОХРАНИТЬ', button_font, ACCENT, CARD_COLOR, ACCENT_HOVER)
            back_btn = AnimatedButton(back_btn_x, card_y + card_h + 20, btn_w, btn_h,
                                      'НАЗАД', button_font, ACCENT, CARD_COLOR, ACCENT_HOVER)
        else:
            action_btn.set_position(action_rect.x, action_rect.y)
            action_btn.original_rect.width = action_w
            action_btn.original_rect.height = action_h
            save_btn.set_position(save_btn_x, card_y + card_h + 20)
            back_btn.set_position(back_btn_x, card_y + card_h + 20)
        
        action_btn.update(dt, mouse_pos, mouse_pressed)
        save_btn.update(dt, mouse_pos, mouse_pressed)
        back_btn.update(dt, mouse_pos, mouse_pressed)
        
        if message_timer > 0:
            message_timer -= 1
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                channel_click.play(click)
                if season_active and field_rect.collidepoint(e.pos):
                    active_field = 'date'
                else:
                    active_field = None
            if e.type == pygame.KEYDOWN and active_field == 'date':
                if e.key == pygame.K_BACKSPACE:
                    end_date = end_date[:-1]
                elif e.key == pygame.K_RETURN:
                    active_field = None
                elif len(end_date) < 10 and e.unicode.isprintable():
                    end_date += e.unicode
        
        if mouse_released and not ignore_clicks:
            if back_btn.is_clicked(mouse_pos, True):
                admin_panel(admin_nickname, 1)
                return
            
            if action_btn.is_clicked(mouse_pos, True):
                if season_active:
                    end_season_and_award()
                    c.execute('UPDATE champion_season SET is_active = 0 WHERE is_active = 1')
                    c.execute('DELETE FROM daily_results')
                    conn.commit()
                    season_active = False
                    season = None
                    end_date = ''
                    message = 'Сезон Champions завершён!'
                    message_timer = 180
                else:
                    from datetime import datetime as dt
                    today = dt.now().strftime('%Y-%m-%d')
                    start_dt = dt.now()
                    if start_dt.month == 12:
                        end_dt = start_dt.replace(year=start_dt.year + 1, month=1)
                    else:
                        end_dt = start_dt.replace(month=start_dt.month + 1)
                    end = end_dt.strftime('%Y-%m-%d')
                    
                    import hashlib
                    seed = hashlib.md5(f"champions{today}".encode()).hexdigest()[:16]
                    
                    c.execute('UPDATE champion_season SET is_active = 0')
                    c.execute('''INSERT INTO champion_season 
                               (season_name, start_date, end_date, is_active, seed, created_by)
                               VALUES (?, ?, ?, 1, ?, ?)''', 
                             ('Champions 2026', today, end, seed, admin_nickname))
                    conn.commit()
                    season_active = True
                    season = get_active_season()
                    if season:
                        end_date = season[3]
                    message = 'Сезон Champions начат!'
                    message_timer = 180
            
            if season_active and save_btn.is_clicked(mouse_pos, True):
                if end_date and len(end_date) == 10:
                    season = get_active_season()
                    if season:
                        c.execute('UPDATE champion_season SET end_date = ? WHERE id = ?', (end_date, season[0]))
                        conn.commit()
                        message = 'Дата окончания обновлена!'
                        message_timer = 180
                else:
                    message = 'Введите корректную дату (ГГГГ-ММ-ДД)'
                    message_timer = 180

        for y in range(current_height):
            ratio = y / current_height
            r = int(BG_COLOR[0] - ratio * 15)
            g = int(BG_COLOR[1] - ratio * 15)
            b = int(BG_COLOR[2] - ratio * 15)
            pygame.draw.line(screen, (max(0, r), max(0, g), max(0, b)), (0, y), (current_width, y))
        
        title_surf = title_font.render('УПРАВЛЕНИЕ ИГРОЙ ДНЯ', True, ACCENT)
        screen.blit(title_surf, (center_x - title_surf.get_width() // 2, title_y))
        
        pygame.draw.rect(screen, CARD_COLOR, (card_x, card_y, card_w, card_h), border_radius=20)
        pygame.draw.rect(screen, ACCENT, (card_x, card_y, card_w, card_h), 2, border_radius=20)
        
        status_text = "Активен: CHAMPIONS" if season_active else "Активна: Игра дня"
        status_color = get_champion_color() if season_active else ACCENT
        status_surf = subtitle_font.render(status_text, True, status_color)
        screen.blit(status_surf, (center_x - status_surf.get_width() // 2, card_y + 30))
        
        if season_active and season:
            desc = f"Сезон: {season[1]} | Начат: {season[2]} | Окончание: {season[3]}"
        else:
            desc = "Ежедневная игра меняется каждый день"
        desc_surf = small_font.render(desc, True, TEXT_SECONDARY)
        screen.blit(desc_surf, (center_x - desc_surf.get_width() // 2, card_y + 70))
        
        if season_active:
            label_surf = small_font.render('Дата окончания сезона (ГГГГ-ММ-ДД)', True, TEXT_SECONDARY)
            screen.blit(label_surf, (field_x, field_y - 22))
            
            border = ACCENT if active_field == 'date' else BORDER_COLOR
            pygame.draw.rect(screen, INPUT_BG, field_rect, border_radius=10)
            pygame.draw.rect(screen, border, field_rect, 2, border_radius=10)
            date_surf = input_font.render(end_date, True, TEXT_PRIMARY)
            screen.blit(date_surf, (field_rect.x + 10, field_rect.centery - date_surf.get_height() // 2))
        
        action_btn.draw(screen)
        if season_active:
            save_btn.draw(screen)
        back_btn.draw(screen)
        
        if message and message_timer > 0:
            msg_surf = small_font.render(message, True, theme['win'])
            screen.blit(msg_surf, (center_x - msg_surf.get_width() // 2, card_y + card_h + 60))
        
        effect_manager.draw(screen, current_width, current_height)

        pygame.display.update()
        clock.tick(60)


def logout_and_clear():
    import auth
    from settings_manager import clear_last_user
    clear_last_user()
    auth.auth()


def edit_top(screen, current_width, current_height, admin_nickname):
    import top
    top.edit_top_admin(screen, current_width, current_height, admin_nickname)


def change_player_password(screen, current_width, current_height, admin_nickname):
    pygame.init()
    
    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)

    volume_sound = get_sound()
    music_manager = get_music_manager()
    click = music_manager.load_sound('click.mp3')
    channel_click = pygame.mixer.Channel(0)
    channel_click.set_volume(volume_sound)
    
    clock = pygame.time.Clock()
    
    nickname_text = ''
    password_text = ''
    nickname_active = True
    password_active = False
    
    error_message = ''
    success_message = ''
    message_timer = 0
    
    save_btn = None
    back_btn = None
    
    mouse_was_pressed = False
    ignore_clicks = True
    frames_passed = 0
    
    running = True
    while running:
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
        
        theme = get_current_theme()
        ACCENT = theme['accent']
        ACCENT_HOVER = theme['accent_hover']
        CARD_COLOR = theme['card']
        TEXT_PRIMARY = theme['text']
        TEXT_SECONDARY = theme['text_secondary']
        ERROR_COLOR = theme['error']
        BG_COLOR = theme['background']
        INPUT_BG = theme['input_bg']
        BORDER_COLOR = theme['border']
        
        center_x = current_width // 2
        
        title_y = int(current_height * 0.12)
        
        card_width = 500
        card_height = 400
        card_x = center_x - card_width // 2
        card_y = int(current_height * 0.22)
        
        field_width = 300
        field_height = 45
        
        nickname_field_x = center_x - field_width // 2
        nickname_field_y = card_y + 80
        nickname_rect = pygame.Rect(nickname_field_x, nickname_field_y, field_width, field_height)
        
        password_field_x = center_x - field_width // 2
        password_field_y = nickname_field_y + 80
        password_rect = pygame.Rect(password_field_x, password_field_y, field_width, field_height)
        
        button_width = 150
        button_height = 45
        button_spacing = 30
        buttons_start_x = center_x - (button_width * 2 + button_spacing) // 2
        buttons_y = password_field_y + 80
        
        if save_btn is None:
            save_btn = AnimatedButton(buttons_start_x, buttons_y, button_width, button_height,
                                      'СОХРАНИТЬ', button_font, theme['win'], CARD_COLOR)
            back_btn = AnimatedButton(buttons_start_x + button_width + button_spacing, buttons_y, button_width, button_height,
                                      'ВЕРНУТЬСЯ', button_font, ACCENT, CARD_COLOR, ACCENT_HOVER)
        else:
            save_btn.set_position(buttons_start_x, buttons_y)
            back_btn.set_position(buttons_start_x + button_width + button_spacing, buttons_y)
        
        save_btn.update(dt, mouse_pos, mouse_pressed)
        back_btn.update(dt, mouse_pos, mouse_pressed)
        
        if message_timer > 0:
            message_timer -= 1
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                channel_click.play(click)
                nickname_active = nickname_rect.collidepoint(e.pos)
                password_active = password_rect.collidepoint(e.pos)
            if e.type == pygame.KEYDOWN:
                if nickname_active:
                    if e.key == pygame.K_BACKSPACE:
                        nickname_text = nickname_text[:-1]
                    elif e.key == pygame.K_TAB:
                        nickname_active = False
                        password_active = True
                    elif e.key == pygame.K_RETURN:
                        password_active = True
                        nickname_active = False
                    elif len(nickname_text) < 20:
                        nickname_text += e.unicode
                elif password_active:
                    if e.key == pygame.K_BACKSPACE:
                        password_text = password_text[:-1]
                    elif e.key == pygame.K_TAB:
                        password_active = False
                        nickname_active = True
                    elif e.key == pygame.K_RETURN:
                        if not nickname_text:
                            error_message = 'Введите никнейм игрока'
                            message_timer = 120
                        elif not password_text:
                            error_message = 'Введите новый пароль'
                            message_timer = 120
                        elif not player_exists(nickname_text):
                            error_message = 'Игрок не найден'
                            message_timer = 120
                        else:
                            if update_player_password(nickname_text, password_text):
                                success_message = 'Пароль успешно изменен'
                                error_message = ''
                                nickname_text = ''
                                password_text = ''
                            else:
                                error_message = 'Ошибка при изменении пароля'
                                success_message = ''
                            message_timer = 120
                    elif len(password_text) < 30:
                        password_text += e.unicode
        
        if mouse_released and not ignore_clicks:
            if save_btn.is_clicked(mouse_pos, True):
                if not nickname_text:
                    error_message = 'Введите никнейм игрока'
                    message_timer = 120
                elif not password_text:
                    error_message = 'Введите новый пароль'
                    message_timer = 120
                elif not player_exists(nickname_text):
                    error_message = 'Игрок не найден'
                    message_timer = 120
                else:
                    if update_player_password(nickname_text, password_text):
                        success_message = 'Пароль успешно изменен'
                        error_message = ''
                        nickname_text = ''
                        password_text = ''
                    else:
                        error_message = 'Ошибка при изменении пароля'
                        success_message = ''
                    message_timer = 120
            if back_btn.is_clicked(mouse_pos, True):
                admin_panel(admin_nickname, 1)
                return

        for y in range(current_height):
            ratio = y / current_height
            r = int(BG_COLOR[0] - ratio * 15)
            g = int(BG_COLOR[1] - ratio * 15)
            b = int(BG_COLOR[2] - ratio * 15)
            pygame.draw.line(screen, (max(0, r), max(0, g), max(0, b)), (0, y), (current_width, y))
        
        title_surf = title_font.render('ИЗМЕНЕНИЕ ПАРОЛЯ', True, ACCENT)
        screen.blit(title_surf, (center_x - title_surf.get_width() // 2, title_y))
        
        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        pygame.draw.rect(screen, CARD_COLOR, card_rect, border_radius=15)
        pygame.draw.rect(screen, ACCENT, card_rect, 2, border_radius=15)
        
        nickname_label = small_font.render('Никнейм игрока', True, TEXT_SECONDARY)
        screen.blit(nickname_label, (nickname_field_x, nickname_field_y - 22))
        
        border_color = ACCENT if nickname_active else BORDER_COLOR
        pygame.draw.rect(screen, INPUT_BG, nickname_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, nickname_rect, 2, border_radius=10)
        
        nickname_surf = input_font.render(nickname_text, True, TEXT_PRIMARY)
        screen.blit(nickname_surf, (nickname_field_x + 15, nickname_field_y + (field_height - nickname_surf.get_height()) // 2))
        
        password_label = small_font.render('Новый пароль', True, TEXT_SECONDARY)
        screen.blit(password_label, (password_field_x, password_field_y - 22))
        
        border_color = ACCENT if password_active else BORDER_COLOR
        pygame.draw.rect(screen, INPUT_BG, password_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, password_rect, 2, border_radius=10)
        
        password_display = '*' * len(password_text)
        password_surf = input_font.render(password_display, True, TEXT_PRIMARY)
        screen.blit(password_surf, (password_field_x + 15, password_field_y + (field_height - password_surf.get_height()) // 2))
        
        save_btn.draw(screen)
        back_btn.draw(screen)
        
        if error_message and message_timer > 0:
            error_surf = small_font.render(error_message, True, ERROR_COLOR)
            screen.blit(error_surf, (center_x - error_surf.get_width() // 2, buttons_y + button_height + 15))
        
        if success_message and message_timer > 0:
            success_surf = small_font.render(success_message, True, theme['win'])
            screen.blit(success_surf, (center_x - success_surf.get_width() // 2, buttons_y + button_height + 15))
        
        effect_manager.draw(screen, current_width, current_height)

        pygame.display.update()
        clock.tick(60)


def change_player_nickname(screen, current_width, current_height, admin_nickname):
    pygame.init()
    
    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)

    volume_sound = get_sound()
    music_manager = get_music_manager()
    click = music_manager.load_sound('click.mp3')
    channel_click = pygame.mixer.Channel(0)
    channel_click.set_volume(volume_sound)
    
    clock = pygame.time.Clock()
    
    old_nickname_text = ''
    new_nickname_text = ''
    old_nickname_active = True
    new_nickname_active = False
    
    error_message = ''
    success_message = ''
    message_timer = 0
    
    save_btn = None
    back_btn = None
    
    mouse_was_pressed = False
    ignore_clicks = True
    frames_passed = 0
    
    running = True
    while running:
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
        
        theme = get_current_theme()
        ACCENT = theme['accent']
        ACCENT_HOVER = theme['accent_hover']
        CARD_COLOR = theme['card']
        TEXT_PRIMARY = theme['text']
        TEXT_SECONDARY = theme['text_secondary']
        ERROR_COLOR = theme['error']
        BG_COLOR = theme['background']
        INPUT_BG = theme['input_bg']
        BORDER_COLOR = theme['border']
        
        center_x = current_width // 2
        
        title_y = int(current_height * 0.12)
        
        card_width = 500
        card_height = 400
        card_x = center_x - card_width // 2
        card_y = int(current_height * 0.22)
        
        field_width = 300
        field_height = 45
        
        old_nickname_field_x = center_x - field_width // 2
        old_nickname_field_y = card_y + 80
        old_nickname_rect = pygame.Rect(old_nickname_field_x, old_nickname_field_y, field_width, field_height)
        
        new_nickname_field_x = center_x - field_width // 2
        new_nickname_field_y = old_nickname_field_y + 80
        new_nickname_rect = pygame.Rect(new_nickname_field_x, new_nickname_field_y, field_width, field_height)
        
        button_width = 150
        button_height = 45
        button_spacing = 30
        buttons_start_x = center_x - (button_width * 2 + button_spacing) // 2
        buttons_y = new_nickname_field_y + 80
        
        if save_btn is None:
            save_btn = AnimatedButton(buttons_start_x, buttons_y, button_width, button_height,
                                      'СОХРАНИТЬ', button_font, theme['win'], CARD_COLOR)
            back_btn = AnimatedButton(buttons_start_x + button_width + button_spacing, buttons_y, button_width, button_height,
                                      'ВЕРНУТЬСЯ', button_font, ACCENT, CARD_COLOR, ACCENT_HOVER)
        else:
            save_btn.set_position(buttons_start_x, buttons_y)
            back_btn.set_position(buttons_start_x + button_width + button_spacing, buttons_y)
        
        save_btn.update(dt, mouse_pos, mouse_pressed)
        back_btn.update(dt, mouse_pos, mouse_pressed)
        
        if message_timer > 0:
            message_timer -= 1
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                channel_click.play(click)
                old_nickname_active = old_nickname_rect.collidepoint(e.pos)
                new_nickname_active = new_nickname_rect.collidepoint(e.pos)
            if e.type == pygame.KEYDOWN:
                if old_nickname_active:
                    if e.key == pygame.K_BACKSPACE:
                        old_nickname_text = old_nickname_text[:-1]
                    elif e.key == pygame.K_TAB:
                        old_nickname_active = False
                        new_nickname_active = True
                    elif e.key == pygame.K_RETURN:
                        new_nickname_active = True
                        old_nickname_active = False
                    elif len(old_nickname_text) < 20:
                        old_nickname_text += e.unicode
                elif new_nickname_active:
                    if e.key == pygame.K_BACKSPACE:
                        new_nickname_text = new_nickname_text[:-1]
                    elif e.key == pygame.K_TAB:
                        new_nickname_active = False
                        old_nickname_active = True
                    elif e.key == pygame.K_RETURN:
                        if not old_nickname_text:
                            error_message = 'Введите текущий никнейм игрока'
                            message_timer = 120
                        elif not new_nickname_text:
                            error_message = 'Введите новый никнейм'
                            message_timer = 120
                        elif not player_exists(old_nickname_text):
                            error_message = 'Игрок не найден'
                            message_timer = 120
                        elif player_exists(new_nickname_text) or is_admin(new_nickname_text):
                            error_message = 'Этот никнейм уже занят'
                            message_timer = 120
                        else:
                            if update_player_nickname(old_nickname_text, new_nickname_text):
                                success_message = 'Никнейм успешно изменен'
                                error_message = ''
                                old_nickname_text = ''
                                new_nickname_text = ''
                            else:
                                error_message = 'Ошибка при изменении никнейма'
                                success_message = ''
                            message_timer = 120
                    elif len(new_nickname_text) < 20:
                        new_nickname_text += e.unicode
        
        if mouse_released and not ignore_clicks:
            if save_btn.is_clicked(mouse_pos, True):
                if not old_nickname_text:
                    error_message = 'Введите текущий никнейм игрока'
                    message_timer = 120
                elif not new_nickname_text:
                    error_message = 'Введите новый никнейм'
                    message_timer = 120
                elif not player_exists(old_nickname_text):
                    error_message = 'Игрок не найден'
                    message_timer = 120
                elif player_exists(new_nickname_text) or is_admin(new_nickname_text):
                    error_message = 'Этот никнейм уже занят'
                    message_timer = 120
                else:
                    if update_player_nickname(old_nickname_text, new_nickname_text):
                        success_message = 'Никнейм успешно изменен'
                        error_message = ''
                        old_nickname_text = ''
                        new_nickname_text = ''
                    else:
                        error_message = 'Ошибка при изменении никнейма'
                        success_message = ''
                    message_timer = 120
            if back_btn.is_clicked(mouse_pos, True):
                admin_panel(admin_nickname, 1)
                return

        for y in range(current_height):
            ratio = y / current_height
            r = int(BG_COLOR[0] - ratio * 15)
            g = int(BG_COLOR[1] - ratio * 15)
            b = int(BG_COLOR[2] - ratio * 15)
            pygame.draw.line(screen, (max(0, r), max(0, g), max(0, b)), (0, y), (current_width, y))
        
        title_surf = title_font.render('ИЗМЕНЕНИЕ НИКНЕЙМА', True, ACCENT)
        screen.blit(title_surf, (center_x - title_surf.get_width() // 2, title_y))
        
        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        pygame.draw.rect(screen, CARD_COLOR, card_rect, border_radius=15)
        pygame.draw.rect(screen, ACCENT, card_rect, 2, border_radius=15)
        
        old_nickname_label = small_font.render('Текущий никнейм', True, TEXT_SECONDARY)
        screen.blit(old_nickname_label, (old_nickname_field_x, old_nickname_field_y - 22))
        
        border_color = ACCENT if old_nickname_active else BORDER_COLOR
        pygame.draw.rect(screen, INPUT_BG, old_nickname_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, old_nickname_rect, 2, border_radius=10)
        
        old_nickname_surf = input_font.render(old_nickname_text, True, TEXT_PRIMARY)
        screen.blit(old_nickname_surf, (old_nickname_field_x + 15, old_nickname_field_y + (field_height - old_nickname_surf.get_height()) // 2))
        
        new_nickname_label = small_font.render('Новый никнейм', True, TEXT_SECONDARY)
        screen.blit(new_nickname_label, (new_nickname_field_x, new_nickname_field_y - 22))
        
        border_color = ACCENT if new_nickname_active else BORDER_COLOR
        pygame.draw.rect(screen, INPUT_BG, new_nickname_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, new_nickname_rect, 2, border_radius=10)
        
        new_nickname_surf = input_font.render(new_nickname_text, True, TEXT_PRIMARY)
        screen.blit(new_nickname_surf, (new_nickname_field_x + 15, new_nickname_field_y + (field_height - new_nickname_surf.get_height()) // 2))
        
        save_btn.draw(screen)
        back_btn.draw(screen)
        
        if error_message and message_timer > 0:
            error_surf = small_font.render(error_message, True, ERROR_COLOR)
            screen.blit(error_surf, (center_x - error_surf.get_width() // 2, buttons_y + button_height + 15))
        
        if success_message and message_timer > 0:
            success_surf = small_font.render(success_message, True, theme['win'])
            screen.blit(success_surf, (center_x - success_surf.get_width() // 2, buttons_y + button_height + 15))
        
        effect_manager.draw(screen, current_width, current_height)

        pygame.display.update()
        clock.tick(60)