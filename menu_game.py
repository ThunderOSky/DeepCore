import pygame
import sys
import random
import math
import menu
import game, settings
from theme import *
from settings_manager import *
from ui import AnimatedButton
from music_manager import MusicManager
from effects import *

def show_continue_dialog(screen, current_width, current_height, nickname):
    theme = get_current_theme()
    
    overlay = pygame.Surface((current_width, current_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    
    dialog_width = int(current_width * 50 / 100)
    dialog_height = int(current_height * 30 / 100)
    dialog_x = (current_width - dialog_width) // 2
    dialog_y = (current_height - dialog_height) // 2
    
    dialog_bg = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
    dialog_bg.fill((*theme['card'], 240))
    pygame.draw.rect(dialog_bg, theme['accent'], (0, 0, dialog_width, dialog_height), 2, border_radius=15)
    screen.blit(dialog_bg, (dialog_x, dialog_y))
    
    font_title = pygame.font.Font('font/font.otf', int(current_height * 5 / 100))
    font_button = pygame.font.Font('font/font.otf', int(current_height * 3.5 / 100))
    
    title_text = font_title.render("Незаконченная игра", True, theme['accent'])
    title_x = dialog_x + (dialog_width - title_text.get_width()) // 2
    title_y = dialog_y + int(dialog_height * 20 / 100)
    screen.blit(title_text, (title_x, title_y))
    
    question_text = font_button.render("Хотите продолжить?", True, theme['text'])
    question_x = dialog_x + (dialog_width - question_text.get_width()) // 2
    question_y = title_y + title_text.get_height() + 20
    screen.blit(question_text, (question_x, question_y))
    
    button_width = int(dialog_width * 35 / 100)
    button_height = int(dialog_height * 25 / 100)
    button_y = dialog_y + dialog_height - button_height - 30
    
    yes_btn = AnimatedButton(dialog_x + 30, button_y, button_width, button_height,
                             'Да', font_button, theme['accent'], theme['text'])
    no_btn = AnimatedButton(dialog_x + dialog_width - button_width - 30, button_y, button_width, button_height,
                            'Нет', font_button, theme['error'], theme['text'])
    
    mwp = False; igcl = True; frm = 0
    clock = pygame.time.Clock()
    waiting = True
    while waiting:
        dt = clock.tick(60) / 1000.0
        mp = pygame.mouse.get_pos()
        mpr = pygame.mouse.get_pressed()[0]
        mrel = not mpr and mwp; mwp = mpr
        
        frm += 1
        if frm > 3: igcl = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        
        yes_btn.update(dt, mp, mpr)
        no_btn.update(dt, mp, mpr)
        
        if mrel and not igcl:
            if yes_btn.is_clicked(mp, True): return True
            if no_btn.is_clicked(mp, True):
                from db_manager import delete_save_game
                delete_save_game(nickname); return False
        
        yes_btn.draw(screen)
        no_btn.draw(screen)
        pygame.display.update()


def menu_game(nickname):
    pygame.init()
    
    difficulty = 'easy'; game_mode = 'classic'
    custom_cols = 9; custom_rows = 9; custom_mines = 10
    custom_cols_str = '9'; custom_rows_str = '9'; custom_mines_str = '10'
    
    vm = get_music(); vs = get_sound(); THEME = get_theme()
    set_theme(THEME)
    
    music_manager = MusicManager()  
    click = music_manager.load_sound('click.mp3')  
    ch = pygame.mixer.Channel(0); ch.set_volume(vs)
    
    sw, sh, sf = load_window_settings(1366, 768)
    if sf: screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else: screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
    
    pygame.display.set_caption('DeepCore - Выбор игры')
    
    is_full = sf; wsz = (sw, sh) if not sf else (1366, 768)
    
    def toggle_fs():
        nonlocal screen, is_full, wsz
        if is_full: screen = pygame.display.set_mode(wsz, pygame.RESIZABLE); is_full = False
        else: wsz = screen.get_size(); screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN); is_full = True
        save_window_settings(wsz[0], wsz[1], is_full)
        
    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)
    
    particles = [{'x': random.randint(0, sw), 'y': random.randint(0, sh), 'size': random.randint(2, 5),
                  'speed_x': random.uniform(-0.2, 0.2), 'speed_y': random.uniform(-0.2, 0.2),
                  'alpha': random.randint(30, 80), 'phase': random.uniform(0, math.pi*2)} for _ in range(40)]
    last_theme = THEME
    
    game_modes = {'classic': 'Обычный', 'chronos': 'Хронос', 'safari': 'Сафари'}
    difficulties = {'easy': 'Легкий', 'average': 'Средний', 'hard': 'Сложный', 'super': 'Экстра', 'custom': 'Своя игра'}
    
    active_input = None
    
    start_btn = None; exit_btn = None; settings_btn = None
    mode_btns = {}; diff_btns = {}
    
    mwp = False; igcl = True; frm = 0
    
    run = True; clock = pygame.time.Clock()
    
    while run:
        current_width, current_height = screen.get_size()
        cw, ch2 = screen.get_size()
        dt = clock.get_time() / 1000.0
        if current_effect != get_effect():
            current_effect = get_effect()
            effect_manager.set_effect(current_effect, current_width, current_height)
        effect_manager.update(dt, current_width, current_height)
        mp = pygame.mouse.get_pos()
        mpr = pygame.mouse.get_pressed()[0]
        mrel = not mpr and mwp; mwp = mpr
        
        frm += 1
        if frm > 3: igcl = False
        
        if last_theme != get_theme(): last_theme = get_theme(); set_theme(last_theme)
        
        theme = get_current_theme()
        TP = theme['text']; TS = theme['text_secondary']; A = theme['accent']
        AH = theme['accent_hover']; CC = theme['card']; ER = theme['error']
        
        for p in particles:
            p['x'] += p['speed_x']; p['y'] += p['speed_y']; p['phase'] += 0.01
            if p['x'] < -50: p['x'] = cw + 50
            if p['x'] > cw + 50: p['x'] = -50
            if p['y'] < -50: p['y'] = ch2 + 50
            if p['y'] > ch2 + 50: p['y'] = -50
        
        cx = cw // 2
        ty = int(ch2 * 0.08)
        
        bbw, bbh = 100, 36
        sbx, sby = 25, ch2 - bbh - 25
        
        if settings_btn is None:
            settings_btn = AnimatedButton(sbx, sby, bbw, bbh, 'Настройки', small_font, A, TP)
        else:
            settings_btn.set_position(sbx, sby)
        settings_btn.update(dt, mp, mpr)

        mby = int(ch2 * 0.2); mbw = int(cw * 0.2); mbh = int(ch2 * 0.07); msp = int(cw * 0.03)
        modes = ['classic', 'chronos', 'safari']
        tmw = len(modes) * mbw + (len(modes)-1) * msp; msx = cx - tmw // 2
        
        for i, mode in enumerate(modes):
            x = msx + i * (mbw + msp)
            if mode not in mode_btns:
                mode_btns[mode] = AnimatedButton(x, mby, mbw, mbh, game_modes[mode], button_font, CC, TS, A)
            else:
                mode_btns[mode].set_position(x, mby)
                mode_btns[mode].original_rect.width = mbw; mode_btns[mode].original_rect.height = mbh
            ia = (mode == game_mode)
            mode_btns[mode].base_color = A if ia else CC
            mode_btns[mode].text_color = TP if ia else TS
            mode_btns[mode].update(dt, mp, mpr)
        
        dby = int(ch2 * 0.35); dbw = int(cw * 0.15); dbh = int(ch2 * 0.07); dsp = int(cw * 0.02)
        row1 = ['easy', 'average']; row2 = ['hard', 'super', 'custom']
        all_diffs = row1 + row2
        
        tr1w = len(row1)*dbw + (len(row1)-1)*dsp; r1sx = cx - tr1w//2
        for i, diff in enumerate(row1):
            x = r1sx + i*(dbw+dsp)
            if diff not in diff_btns:
                diff_btns[diff] = AnimatedButton(x, dby, dbw, dbh, difficulties[diff], button_font, CC, TS, A)
            else:
                diff_btns[diff].set_position(x, dby)
                diff_btns[diff].original_rect.width = dbw; diff_btns[diff].original_rect.height = dbh
            ia = (diff == difficulty)
            diff_btns[diff].base_color = A if ia else CC
            diff_btns[diff].text_color = TP if ia else TS
            diff_btns[diff].update(dt, mp, mpr)
        
        ry = dby + dbh + int(ch2 * 0.02)
        tr2w = len(row2)*dbw + (len(row2)-1)*dsp; r2sx = cx - tr2w//2
        for i, diff in enumerate(row2):
            x = r2sx + i*(dbw+dsp)
            if diff not in diff_btns:
                diff_btns[diff] = AnimatedButton(x, ry, dbw, dbh, difficulties[diff], button_font, CC, TS, A)
            else:
                diff_btns[diff].set_position(x, ry)
                diff_btns[diff].original_rect.width = dbw; diff_btns[diff].original_rect.height = dbh
            ia = (diff == difficulty)
            diff_btns[diff].base_color = A if ia else CC
            diff_btns[diff].text_color = TP if ia else TS
            diff_btns[diff].update(dt, mp, mpr)
        
        cu_y = ry + dbh + int(ch2 * 0.05)
        cu_w = int(cw * 0.55); cu_h = int(ch2 * 0.12); cu_x = cx - cu_w // 2
        
        col_w = cu_w // 3; fw2 = int(col_w * 0.6); fh2 = int(cu_h * 0.5); fy2 = cu_y + (cu_h - fh2)//2
        
        cols_rect = pygame.Rect(cu_x + (col_w - fw2)//2, fy2, fw2, fh2)
        rows_rect = pygame.Rect(cu_x + col_w + (col_w - fw2)//2, fy2, fw2, fh2)
        mines_rect = pygame.Rect(cu_x + col_w*2 + (col_w - fw2)//2, fy2, fw2, fh2)
        
        bty = ry + dbh + int(ch2 * 0.2)
        btw = int(cw * 0.18); bth = int(ch2 * 0.07); bts = int(cw * 0.04)
        
        if start_btn is None:
            start_btn = AnimatedButton(cx - btw - bts//2, bty, btw, bth, 'НАЧАТЬ', button_font, A, CC, AH)
            exit_btn = AnimatedButton(cx + bts//2, bty, btw, bth, 'ВЕРНУТЬСЯ', button_font, ER, CC)
        else:
            start_btn.set_position(cx - btw - bts//2, bty); start_btn.original_rect.width = btw; start_btn.original_rect.height = bth
            exit_btn.set_position(cx + bts//2, bty); exit_btn.original_rect.width = btw; exit_btn.original_rect.height = bth
        
        start_btn.update(dt, mp, mpr); exit_btn.update(dt, mp, mpr)
        
        from db_manager import has_saved_game, load_game_state, delete_save_game
        
        if has_saved_game(nickname):
            sd = load_game_state(nickname)
            cg = show_continue_dialog(screen, cw, ch2, nickname)
            if cg and sd:
                game.game(nickname, sd['difficulty'], sd['game_type'], None, None, None, load_saved=True, saved_data=sd)
                return
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.VIDEORESIZE and not is_full:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                wsz = (e.w, e.h); save_window_settings(e.w, e.h, is_full); continue
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F11: toggle_fs(); pygame.display.flip(); continue
                if difficulty == 'custom' and active_input:
                    if e.key == pygame.K_BACKSPACE:
                        if active_input == 'cols': custom_cols_str = custom_cols_str[:-1]
                        elif active_input == 'rows': custom_rows_str = custom_rows_str[:-1]
                        elif active_input == 'mines': custom_mines_str = custom_mines_str[:-1]
                    elif e.key == pygame.K_RETURN:
                        if active_input == 'cols':
                            if custom_cols_str == '' or custom_cols_str == '0': custom_cols_str = '9'
                            v = int(custom_cols_str)
                            if v > 30: v = 30
                            if v < 9: v = 9
                            custom_cols = v; custom_cols_str = str(v)
                        elif active_input == 'rows':
                            if custom_rows_str == '' or custom_rows_str == '0': custom_rows_str = '9'
                            v = int(custom_rows_str)
                            if v > 30: v = 30
                            if v < 9: v = 9
                            custom_rows = v; custom_rows_str = str(v)
                        elif active_input == 'mines':
                            if custom_mines_str == '' or custom_mines_str == '0': custom_mines_str = '10'
                            v = int(custom_mines_str)
                            if v > 100: v = 100
                            if v < 10: v = 10
                            custom_mines = v; custom_mines_str = str(v)
                        active_input = None
                    elif e.unicode.isdigit():
                        n = e.unicode
                        if active_input == 'cols':
                            if custom_cols_str == '' and n == '0': pass
                            else:
                                ns = custom_cols_str + n
                                if int(ns) <= 30: custom_cols_str = ns
                        elif active_input == 'rows':
                            if custom_rows_str == '' and n == '0': pass
                            else:
                                ns = custom_rows_str + n
                                if int(ns) <= 30: custom_rows_str = ns
                        elif active_input == 'mines':
                            if custom_mines_str == '' and n == '0': pass
                            else:
                                ns = custom_mines_str + n
                                if int(ns) <= 100: custom_mines_str = ns
            if e.type == pygame.MOUSEBUTTONDOWN: ch.play(click)
        
        if mrel and not igcl:
            for mode, btn in mode_btns.items():
                if btn.is_clicked(mp, True): game_mode = mode
            for diff, btn in diff_btns.items():
                if btn.is_clicked(mp, True): difficulty = diff; active_input = None
            
            if settings_btn.is_clicked(mp, True): settings.settings(nickname, "menu_game")
            
            if difficulty == 'custom':
                if cols_rect.collidepoint(mp):
                    if active_input != 'cols': active_input = 'cols'; custom_cols_str = ''
                elif rows_rect.collidepoint(mp):
                    if active_input != 'rows': active_input = 'rows'; custom_rows_str = ''
                elif mines_rect.collidepoint(mp):
                    if active_input != 'mines': active_input = 'mines'; custom_mines_str = ''
                else: active_input = None
            
            if start_btn.is_clicked(mp, True):
                if difficulty == 'custom':
                    try:
                        cc2 = max(9, min(30, int(custom_cols if custom_cols_str == '' else custom_cols_str)))
                        cr2 = max(9, min(30, int(custom_rows if custom_rows_str == '' else custom_rows_str)))
                        cm2 = max(10, min(cc2*cr2-1, int(custom_mines if custom_mines_str == '' else custom_mines_str)))
                        game.game(nickname, difficulty, game_mode, cc2, cr2, cm2)
                    except ValueError: pass
                else:
                    game.game(nickname, difficulty, game_mode, None, None, None)
            
            if exit_btn.is_clicked(mp, True): menu.menu(nickname, 1)
        
        for y in range(ch2):
            r = int(theme['background'][0] - y/ch2*15)
            g = int(theme['background'][1] - y/ch2*15)
            b = int(theme['background'][2] - y/ch2*15)
            pygame.draw.line(screen, (max(0,r), max(0,g), max(0,b)), (0,y), (cw,y))
        
        for p in particles:
            a = max(20, min(100, int(p['alpha'] + math.sin(p['phase'])*20)))
            c = (*A, a)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, c, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']-p['size']), int(p['y']-p['size'])))
        
        fr = pygame.Rect(20, 20, cw-40, ch2-40)
        pygame.draw.rect(screen, A, fr, 2, border_radius=12)
        
        tt = title_font.render('ВЫБОР РЕЖИМА', True, A)
        screen.blit(tt, (cx - tt.get_width()//2, ty))
        
        for btn in mode_btns.values(): btn.draw(screen)
        for btn in diff_btns.values(): btn.draw(screen)
        
        if difficulty == 'custom':
            cu_rect = pygame.Rect(cu_x, cu_y, cu_w, cu_h)
            pygame.draw.rect(screen, CC, cu_rect, border_radius=12)
            pygame.draw.rect(screen, A, cu_rect, 2, border_radius=12)
            
            lfs = pygame.font.Font('font/font.otf', int(button_font.get_height()*0.7))
            for lbl, rect in [("Колонки", cols_rect), ("Строки", rows_rect), ("Мины", mines_rect)]:
                ls = lfs.render(lbl, True, TS)
                screen.blit(ls, (rect.centerx - ls.get_width()//2, rect.y - 22))
            
            ifm = pygame.font.Font('font/font.otf', int(button_font.get_height()*0.85))
            
            cd = custom_cols_str if custom_cols_str else str(custom_cols)
            rd = custom_rows_str if custom_rows_str else str(custom_rows)
            md = custom_mines_str if custom_mines_str else str(custom_mines)
            
            for rect, dv, iname in [(cols_rect, cd, 'cols'), (rows_rect, rd, 'rows'), (mines_rect, md, 'mines')]:
                ia = (active_input == iname)
                bg = AH if ia else CC
                pygame.draw.rect(screen, bg, rect, border_radius=8)
                pygame.draw.rect(screen, A, rect, 2, border_radius=8)
                vt = ifm.render(dv, True, TP)
                screen.blit(vt, vt.get_rect(center=rect.center))
        
        start_btn.draw(screen); exit_btn.draw(screen)
        settings_btn.draw(screen)
        
        effect_manager.draw(screen, current_width, current_height)
        
        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()