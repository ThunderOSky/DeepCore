import pygame
import sqlite3
import sys
import menu
import random
import math
import admin_panel
from theme import *
from settings_manager import *
from db_manager import *
from profile import profile
from ui import AnimatedButton
from music_manager import *
from effects import *

conn = sqlite3.connect('database/game.db')
c = conn.cursor()

def top(nickname):
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
    
    pygame.display.set_caption('DeepCore - Таблица лидеров')
    
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
    
    particles = [{'x': random.randint(0, saved_width), 'y': random.randint(0, saved_height),
                  'size': random.randint(2, 5), 'speed_x': random.uniform(-0.2, 0.2),
                  'speed_y': random.uniform(-0.2, 0.2), 'alpha': random.randint(30, 80),
                  'phase': random.uniform(0, math.pi * 2)} for _ in range(40)]
    
    last_theme = THEME
    current_difficulty = 'all'
    current_mode = 'all'
    
    search_text = ''
    search_active = False
    search_error = ''
    search_error_timer = 0
    
    mode_btns = {}
    diff_btns = {}
    search_btn = None
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
            last_theme = current_theme_name; set_theme(current_theme_name)
        
        theme = get_current_theme()
        ACCENT = theme['accent']; ACCENT_HOVER = theme['accent_hover']
        CARD_COLOR = theme['card']; TEXT_PRIMARY = theme['text']
        TEXT_SECONDARY = theme['text_secondary']; ERROR_COLOR = theme['error']
        INPUT_BG = theme['input_bg']; BORDER_COLOR = theme['border']
        
        for p in particles:
            p['x'] += p['speed_x']; p['y'] += p['speed_y']; p['phase'] += 0.01
            if p['x'] < -50: p['x'] = current_width + 50
            if p['x'] > current_width + 50: p['x'] = -50
            if p['y'] < -50: p['y'] = current_height + 50
            if p['y'] > current_height + 50: p['y'] = -50
        
        center_x = current_width // 2
        
        title_y = int(current_height * 0.04)
        
        sw = int(current_width * 0.22); sh = 38
        sx = center_x - sw // 2; sy = int(current_height * 0.12)
        search_rect = pygame.Rect(sx, sy, sw, sh)
        
        sbw, sbh = 80, 38
        sbx = sx + sw + 8; sby = sy
        
        if search_btn is None:
            search_btn = AnimatedButton(sbx, sby, sbw, sbh, 'Поиск', button_font, ACCENT, TEXT_PRIMARY, ACCENT_HOVER)
        else:
            search_btn.set_position(sbx, sby)
            search_btn.original_rect.width = sbw; search_btn.original_rect.height = sbh
        search_btn.update(dt, mouse_pos, mouse_pressed)
        
        mby = int(current_height * 0.20); mbw = int(current_width * 0.18)
        mbh = int(current_height * 0.06); msp = int(current_width * 0.02)
        
        modes = ['all', 'classic', 'chronos', 'safari']
        mode_names = {'all': 'Все режимы', 'classic': 'Обычный', 'chronos': 'Хронос', 'safari': 'Сафари'}
        
        for i, mode in enumerate(modes):
            x = center_x - (len(modes) * mbw + (len(modes)-1) * msp) // 2 + i * (mbw + msp)
            if mode not in mode_btns:
                mode_btns[mode] = AnimatedButton(x, mby, mbw, mbh, mode_names[mode], button_font, CARD_COLOR, TEXT_SECONDARY, ACCENT)
            else:
                mode_btns[mode].set_position(x, mby)
                mode_btns[mode].original_rect.width = mbw; mode_btns[mode].original_rect.height = mbh
            is_active = (mode == current_mode)
            mode_btns[mode].base_color = ACCENT if is_active else CARD_COLOR
            mode_btns[mode].text_color = TEXT_PRIMARY if is_active else TEXT_SECONDARY
            mode_btns[mode].update(dt, mouse_pos, mouse_pressed)
        
        dby = int(current_height * 0.28); dbw = int(current_width * 0.12)
        dbh = int(current_height * 0.06); dsp = int(current_width * 0.015)
        
        difficulties = ['all', 'easy', 'average', 'hard', 'super']
        diff_names = {'all': 'Все уровни', 'easy': 'Легкий', 'average': 'Средний', 'hard': 'Сложный', 'super': 'Экстра'}
        
        for i, diff in enumerate(difficulties):
            x = center_x - (len(difficulties) * dbw + (len(difficulties)-1) * dsp) // 2 + i * (dbw + dsp)
            if diff not in diff_btns:
                diff_btns[diff] = AnimatedButton(x, dby, dbw, dbh, diff_names[diff], button_font, CARD_COLOR, TEXT_SECONDARY, ACCENT)
            else:
                diff_btns[diff].set_position(x, dby)
                diff_btns[diff].original_rect.width = dbw; diff_btns[diff].original_rect.height = dbh
            is_active = (diff == current_difficulty)
            diff_btns[diff].base_color = ACCENT if is_active else CARD_COLOR
            diff_btns[diff].text_color = TEXT_PRIMARY if is_active else TEXT_SECONDARY
            diff_btns[diff].update(dt, mouse_pos, mouse_pressed)
        
        ty = int(current_height * 0.38); tw = int(current_width * 0.8); th = int(current_height * 0.50)
        tx = center_x - tw // 2
        
        ebw = int(current_width * 0.15); ebh = int(current_height * 0.06)
        ebx = center_x - ebw // 2; eby = ty + th + int(current_height * 0.02)
        
        if exit_btn is None:
            exit_btn = AnimatedButton(ebx, eby, ebw, ebh, 'ВЕРНУТЬСЯ', button_font, ACCENT, CARD_COLOR, ACCENT_HOVER)
        else:
            exit_btn.set_position(ebx, eby)
            exit_btn.original_rect.width = ebw; exit_btn.original_rect.height = ebh
        exit_btn.update(dt, mouse_pos, mouse_pressed)
        
        if search_error_timer > 0: search_error_timer -= 1
        else: search_error = ''
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.VIDEORESIZE and not is_fullscreen:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                window_size = (e.w, e.h); save_window_settings(e.w, e.h, is_fullscreen); continue
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F11: toggle_fullscreen(); pygame.display.flip(); continue
                if search_active:
                    if e.key == pygame.K_BACKSPACE: search_text = search_text[:-1]
                    elif e.key == pygame.K_RETURN:
                        search_active = False
                        if search_text.strip():
                            if player_exists(search_text.strip()):
                                profile(search_text.strip(), viewing_own=False, viewer_nickname=nickname); return
                            else: search_error = 'Такого игрока нет'; search_error_timer = 180
                    elif e.unicode.isprintable() and len(search_text) < 20: search_text += e.unicode
            if e.type == pygame.MOUSEBUTTONDOWN:
                channel_click.play(click)
                search_active = search_rect.collidepoint(e.pos)
        
        if mouse_released and not ignore_clicks:
            if search_btn.is_clicked(mouse_pos, True) and search_text.strip():
                if player_exists(search_text.strip()):
                    profile(search_text.strip(), viewing_own=False, viewer_nickname=nickname); return
                else: search_error = 'Такого игрока нет'; search_error_timer = 180
            for mode, btn in mode_btns.items():
                if btn.is_clicked(mouse_pos, True): current_mode = mode
            for diff, btn in diff_btns.items():
                if btn.is_clicked(mouse_pos, True): current_difficulty = diff
            if exit_btn.is_clicked(mouse_pos, True): menu.menu(nickname, 1); return
        
        for y in range(current_height):
            r = int(theme['background'][0] - y/current_height * 15)
            g = int(theme['background'][1] - y/current_height * 15)
            b = int(theme['background'][2] - y/current_height * 15)
            pygame.draw.line(screen, (max(0,r), max(0,g), max(0,b)), (0,y), (current_width,y))
        
        for p in particles:
            a = max(20, min(100, int(p['alpha'] + math.sin(p['phase'])*20)))
            col = (*ACCENT, a)
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, col, (p['size'], p['size']), p['size'])
            screen.blit(s, (int(p['x']-p['size']), int(p['y']-p['size'])))
        
        fr = pygame.Rect(20, 20, current_width-40, current_height-40)
        pygame.draw.rect(screen, ACCENT, fr, 2, border_radius=12)
        
        tt = title_font.render('ТАБЛИЦА ЛИДЕРОВ', True, ACCENT)
        screen.blit(tt, (center_x - tt.get_width()//2, title_y))
        
        pygame.draw.rect(screen, INPUT_BG, search_rect, border_radius=10)
        pygame.draw.rect(screen, ACCENT if search_active else BORDER_COLOR, search_rect, 2, border_radius=10)
        st = input_font.render(search_text or 'Поиск игрока...', True, TEXT_PRIMARY if search_text else TEXT_SECONDARY)
        screen.blit(st, (sx+12, sy+(sh-st.get_height())//2))
        search_btn.draw(screen)
        
        if search_error and search_error_timer > 0:
            es = small_font.render(search_error, True, ERROR_COLOR)
            screen.blit(es, (sbx+sbw+12, sy+(sbh-es.get_height())//2))
        
        for btn in mode_btns.values(): btn.draw(screen)
        for btn in diff_btns.values(): btn.draw(screen)
        
        leaders = []
        RPM = 10
        if current_difficulty == 'all':
            if current_mode == 'all':
                c.execute("SELECT name, difficulty, type, time FROM complete_games ORDER BY time ASC LIMIT 100")
            else:
                c.execute("SELECT name, difficulty, type, time FROM complete_games WHERE type = ? ORDER BY time ASC LIMIT 100", (current_mode,))
        else:
            if current_mode == 'all':
                c.execute("SELECT name, difficulty, type, time FROM complete_games WHERE difficulty = ? ORDER BY time ASC LIMIT 100", (current_difficulty,))
            else:
                c.execute("SELECT name, difficulty, type, time FROM complete_games WHERE difficulty = ? AND type = ? ORDER BY time ASC LIMIT 100", (current_difficulty, current_mode))

        leaders = [(row[0], row[1], row[2], row[3]) for row in c.fetchall()]
        
        if current_mode != 'all': leaders = [r for r in leaders if r[2] == current_mode]
        leaders.sort(key=lambda x: x[3])
        
        tr = pygame.Rect(tx, ty, tw, th)
        pygame.draw.rect(screen, CARD_COLOR, tr, border_radius=15)
        pygame.draw.rect(screen, ACCENT, tr, 2, border_radius=15)
        
        headers = ["#", "Игрок", "Сложность", "Режим", "Время"]
        cw = [int(tw*.08), int(tw*.32), int(tw*.20), int(tw*.20), int(tw*.20)]
        hy = ty + 15; xo = tx + 10
        
        for i, h in enumerate(headers):
            ht = small_font.render(h, True, ACCENT)
            screen.blit(ht, (xo+5 if i==0 else xo+sum(cw[:i])+(cw[i]-ht.get_width())//2, hy))
        
        ly = hy + small_font.get_height() + 8
        pygame.draw.line(screen, ACCENT, (tx+10, ly), (tx+tw-10, ly), 1)
        
        sy2 = ly + 10; rh = int(th*.07)
        mr = (th - (sy2 - ty)) // rh
        dr = min(len(leaders), mr)
        
        for i in range(dr):
            name, diff, mode, time = leaders[i]
            y = sy2 + i*rh
            frr = pygame.Rect(tx+5, y, tw-10, rh-2)
            if frr.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (*ACCENT, 50), frr, border_radius=8)
                pygame.draw.rect(screen, ACCENT, frr, 1, border_radius=8)
            
            screen.blit(small_font.render(str(i+1), True, TEXT_PRIMARY), (xo+5, y+8))
            
            nc = get_nickname_color(name)
            if nc.startswith('#'): nrgb = hex_to_rgb(nc)
            elif nc == 'default': nrgb = TEXT_PRIMARY
            else: nrgb = get_animated_color(nc)
            nt = small_font.render(name[:15], True, nrgb)
            screen.blit(nt, (xo+cw[0]+(cw[1]-nt.get_width())//2, y+8))
            
            dt2 = {'easy':'Легкий','average':'Средний','hard':'Сложный','super':'Экстра'}[diff]
            screen.blit(small_font.render(dt2, True, TEXT_PRIMARY), (xo+sum(cw[:2])+(cw[2]-small_font.size(dt2)[0])//2, y+8))
            
            mt2 = {'classic':'Обычный','chronos':'Хронос','safari':'Сафари'}.get(mode, mode)
            screen.blit(small_font.render(mt2, True, TEXT_PRIMARY), (xo+sum(cw[:3])+(cw[3]-small_font.size(mt2)[0])//2, y+8))
            
            tmt = small_font.render(f"{time:.2f} сек", True, TEXT_PRIMARY)
            screen.blit(tmt, (xo+sum(cw[:4])+(cw[4]-tmt.get_width())//2, y+8))
            
            if mouse_released and not ignore_clicks and frr.collidepoint(mouse_pos):
                profile(name, viewing_own=(name==nickname), viewer_nickname=None if name==nickname else nickname)
                return
        
        if not leaders:
            et = button_font.render("Нет данных", True, TEXT_SECONDARY)
            screen.blit(et, et.get_rect(center=tr.center))
        
        effect_manager.draw(screen, current_width, current_height)
        
        exit_btn.draw(screen)
        pygame.display.update()
        clock.tick(60)


def edit_top_admin(screen, current_width, current_height, admin_nickname):
    pygame.init()
    vs = get_sound()
    music_manager = get_music_manager()
    click = music_manager.load_sound('click.mp3')
    ch = pygame.mixer.Channel(0)
    ch.set_volume(vs)
    clock = pygame.time.Clock()
    
    cur_diff = 'all'
    cur_mode = 'all'
    sel_rec = None
    click_tmr = 0
    edit_mode = False
    edit_rec = None
    cur_page = 0
    rpp = 8
    
    edit_name = ''
    edit_time = ''
    edit_mtype = 'classic'
    edit_af = None  
    
    edit_name_rect = None
    edit_time_rect = None
    edit_mode_rects = []
    
    records = []
    
    def load_recs():
        nonlocal records, cur_page
        records = []
        
        if cur_diff == 'all':
            if cur_mode == 'all':
                c.execute("SELECT name, difficulty, type, time FROM complete_games ORDER BY time ASC LIMIT 100")
            else:
                c.execute("SELECT name, difficulty, type, time FROM complete_games WHERE type = ? ORDER BY time ASC LIMIT 100", (cur_mode,))
        else:
            if cur_mode == 'all':
                c.execute("SELECT name, difficulty, type, time FROM complete_games WHERE difficulty = ? ORDER BY time ASC LIMIT 100", (cur_diff,))
            else:
                c.execute("SELECT name, difficulty, type, time FROM complete_games WHERE difficulty = ? AND type = ? ORDER BY time ASC LIMIT 100", (cur_diff, cur_mode))
        
        records = [(row[0], row[1], row[2], row[3]) for row in c.fetchall()]
        records.sort(key=lambda x: x[3])
        cur_page = 0
    
    load_recs()
    tp = max(1, (len(records)+rpp-1)//rpp)
    
    mbtns = {}
    dbtns = {}
    back_btn = None
    del_btn = None
    save_btn = None
    eback_btn = None
    larr = None
    rarr = None
    
    mwp = False
    igcl = True
    frm = 0
    acd = 0

    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)
    
    run = True
    while run:
        current_width, current_height = screen.get_size()
        dt = clock.get_time() / 1000.0
        if current_effect != get_effect():
            current_effect = get_effect()
            effect_manager.set_effect(current_effect, current_width, current_height)
        effect_manager.update(dt, current_width, current_height)
        mp = pygame.mouse.get_pos()
        mpr = pygame.mouse.get_pressed()[0]
        mrel = not mpr and mwp
        mwp = mpr
        
        if acd > 0: 
            acd -= dt
        if click_tmr > 0: 
            click_tmr -= dt
        frm += 1
        if frm > 3: 
            igcl = False
        
        theme = get_current_theme()
        A = theme['accent']
        AH = theme['accent_hover']
        CC = theme['card']
        TP = theme['text']
        TS = theme['text_secondary']
        ER = theme['error']
        BG = theme['background']
        IB = theme['input_bg']
        BR = theme['border']
        
        cx = current_width // 2
        
        mby2 = int(current_height * 0.14)
        mbw2 = int(current_width * 0.15)
        mbh2 = int(current_height * 0.05)
        msp2 = int(current_width * 0.015)
        modes2 = ['all', 'classic', 'chronos', 'safari']
        mnames2 = {'all': 'Все режимы', 'classic': 'Обычный', 'chronos': 'Хронос', 'safari': 'Сафари'}
        
        for i, mode in enumerate(modes2):
            x = cx - (len(modes2) * mbw2 + (len(modes2) - 1) * msp2) // 2 + i * (mbw2 + msp2)
            if mode not in mbtns:
                mbtns[mode] = AnimatedButton(x, mby2, mbw2, mbh2, mnames2[mode], button_font, CC, TS, A)
            else:
                mbtns[mode].set_position(x, mby2)
                mbtns[mode].original_rect.width = mbw2
                mbtns[mode].original_rect.height = mbh2
            ia = (mode == cur_mode)
            mbtns[mode].base_color = A if ia else CC
            mbtns[mode].text_color = TP if ia else TS
            mbtns[mode].update(dt, mp, mpr)
        
        dby2 = int(current_height * 0.21)
        dbw2 = int(current_width * 0.11)
        dbh2 = int(current_height * 0.05)
        dsp2 = int(current_width * 0.012)
        diffs2 = ['all', 'easy', 'average', 'hard', 'super']
        dnames2 = {'all': 'Все', 'easy': 'Легкий', 'average': 'Средний', 'hard': 'Сложный', 'super': 'Экстра'}
        
        for i, diff in enumerate(diffs2):
            x = cx - (len(diffs2) * dbw2 + (len(diffs2) - 1) * dsp2) // 2 + i * (dbw2 + dsp2)
            if diff not in dbtns:
                dbtns[diff] = AnimatedButton(x, dby2, dbw2, dbh2, dnames2[diff], button_font, CC, TS, A)
            else:
                dbtns[diff].set_position(x, dby2)
                dbtns[diff].original_rect.width = dbw2
                dbtns[diff].original_rect.height = dbh2
            ia = (diff == cur_diff)
            dbtns[diff].base_color = A if ia else CC
            dbtns[diff].text_color = TP if ia else TS
            dbtns[diff].update(dt, mp, mpr)
        
        ty2 = int(current_height * 0.30)
        tw2 = int(current_width * 0.8)
        th2 = int(current_height * 0.45)
        tx2 = cx - tw2 // 2
        py2 = ty2 + th2 + 5
        
        bww, bhh, bss = 150, 45, 30
        bty = py2 + 55  
        
        if not edit_mode:
            if back_btn is None:
                back_btn = AnimatedButton(cx + bss // 2, bty, bww, bhh, 'ВЕРНУТЬСЯ', button_font, A, CC, AH)
                del_btn = AnimatedButton(cx - bww - bss // 2, bty, bww, bhh, 'УДАЛИТЬ', button_font, ER, CC)
            else:
                back_btn.set_position(cx + bss // 2, bty)
                del_btn.set_position(cx - bww - bss // 2, bty)
            back_btn.update(dt, mp, mpr)
            if sel_rec and not edit_mode:
                del_btn.update(dt, mp, mpr)
        else:
            back_btn = None
            del_btn = None
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                ch.play(click)
            
            if e.type == pygame.KEYDOWN and edit_mode:
                if edit_af == 'nickname':
                    if e.key == pygame.K_BACKSPACE:
                        edit_name = edit_name[:-1]
                    elif e.key == pygame.K_TAB:
                        edit_af = 'time'
                    elif len(edit_name) < 20 and e.unicode.isprintable():
                        edit_name += e.unicode
                elif edit_af == 'time':
                    if e.key == pygame.K_BACKSPACE:
                        edit_time = edit_time[:-1]
                    elif e.key == pygame.K_TAB:
                        edit_af = 'nickname'
                    elif e.unicode in '0123456789.' and len(edit_time) < 10:
                        edit_time += e.unicode
        
        if mrel and not igcl:
            for mode, btn in mbtns.items():
                if btn.is_clicked(mp, True):
                    cur_mode = mode
                    load_recs()
                    sel_rec = None
                    edit_mode = False
                    cur_page = 0
                    tp = max(1, (len(records) + rpp - 1) // rpp)
            for diff, btn in dbtns.items():
                if btn.is_clicked(mp, True):
                    cur_diff = diff
                    load_recs()
                    sel_rec = None
                    edit_mode = False
                    cur_page = 0
                    tp = max(1, (len(records) + rpp - 1) // rpp)
            
            if not edit_mode and back_btn and back_btn.is_clicked(mp, True):
                admin_panel.admin_panel(admin_nickname, 1)
                return
            
            if not edit_mode and sel_rec and not edit_mode and del_btn and del_btn.is_clicked(mp, True):
                n, d, mt, tv = sel_rec
                if delete_top_record(d, n, tv, mt):
                    load_recs()
                    sel_rec = None
                    tp = max(1, (len(records) + rpp - 1) // rpp)
                if cur_page >= tp:
                    cur_page = max(0, tp - 1)
            
            if not edit_mode and tp > 1 and acd <= 0:
                if larr and larr.is_clicked(mp, True):
                    cur_page = cur_page - 1 if cur_page > 0 else tp - 1
                    sel_rec = None
                    acd = 0.15
                if rarr and rarr.is_clicked(mp, True):
                    cur_page = cur_page + 1 if cur_page < tp - 1 else 0
                    sel_rec = None
                    acd = 0.15
            
            if not edit_mode:
                si = cur_page * rpp
                ei = min(si + rpp, len(records))
                for i in range(si, ei):
                    n, d, mt, tv = records[i]
                    y = sy3 + (i - si) * rh2
                    rr = pygame.Rect(tx2, y, tw2, rh2)
                    if rr.collidepoint(mp):
                        if sel_rec == records[i] and click_tmr > 0:
                            edit_mode = True
                            edit_rec = records[i]
                            edit_name = n
                            edit_time = str(tv)
                            edit_mtype = mt
                            sel_rec = None
                            edit_af = 'nickname'
                        else:
                            sel_rec = records[i]
                            click_tmr = 0.3
                        break
            
            if edit_mode:
                if save_btn and save_btn.is_clicked(mp, True):
                    if edit_rec and edit_name and edit_time:
                        try:
                            tv2 = float(edit_time.replace(',', '.'))
                            if update_top_record(edit_rec[1], edit_rec[0], edit_rec[3], edit_rec[2], edit_name, tv2, edit_mtype):
                                load_recs()
                                edit_mode = False
                                edit_rec = None
                                sel_rec = None
                                edit_af = None
                                tp = max(1, (len(records) + rpp - 1) // rpp)
                        except:
                            pass
                if eback_btn and eback_btn.is_clicked(mp, True):
                    edit_mode = False
                    edit_rec = None
                    edit_af = None
        
        for y in range(current_height):
            r = int(BG[0] - y / current_height * 15)
            g = int(BG[1] - y / current_height * 15)
            b = int(BG[2] - y / current_height * 15)
            pygame.draw.line(screen, (max(0, r), max(0, g), max(0, b)), (0, y), (current_width, y))
        
        ts2 = title_font.render('РЕДАКТИРОВАНИЕ ТОПА', True, A)
        screen.blit(ts2, (cx - ts2.get_width() // 2, int(current_height * 0.06)))
        
        for btn in mbtns.values():
            btn.draw(screen)
        for btn in dbtns.values():
            btn.draw(screen)
        
        if edit_mode:
            ecw, ech = 550, 420
            ecx = cx - ecw // 2
            ecy = int(current_height * 0.32)
            
            overlay = pygame.Surface((current_width, current_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            pygame.draw.rect(screen, CC, (ecx, ecy, ecw, ech), border_radius=20)
            pygame.draw.rect(screen, A, (ecx, ecy, ecw, ech), 2, border_radius=20)
            
            et2 = subtitle_font.render('Редактирование записи', True, A)
            screen.blit(et2, (cx - et2.get_width() // 2, ecy + 20))
            
            label_y = ecy + 70
            field_w = 300
            field_h = 40
            
            name_label = small_font.render('Никнейм', True, TS)
            screen.blit(name_label, (cx - field_w // 2, label_y))
            
            name_field_x = cx - field_w // 2
            name_field_y = label_y + 22
            edit_name_rect = pygame.Rect(name_field_x, name_field_y, field_w, field_h)
            
            border_color = A if edit_af == 'nickname' else BR
            pygame.draw.rect(screen, IB, edit_name_rect, border_radius=10)
            pygame.draw.rect(screen, border_color, edit_name_rect, 2, border_radius=10)
            
            name_surf = input_font.render(edit_name, True, TP)
            screen.blit(name_surf, (name_field_x + 15, name_field_y + (field_h - name_surf.get_height()) // 2))
            
            time_label_y = label_y + 80
            time_label = small_font.render('Время (сек)', True, TS)
            screen.blit(time_label, (cx - field_w // 2, time_label_y))
            
            time_field_x = cx - field_w // 2
            time_field_y = time_label_y + 22
            edit_time_rect = pygame.Rect(time_field_x, time_field_y, field_w, field_h)
            
            border_color = A if edit_af == 'time' else BR
            pygame.draw.rect(screen, IB, edit_time_rect, border_radius=10)
            pygame.draw.rect(screen, border_color, edit_time_rect, 2, border_radius=10)
            
            time_surf = input_font.render(edit_time, True, TP)
            screen.blit(time_surf, (time_field_x + 15, time_field_y + (field_h - time_surf.get_height()) // 2))
            
            mode_label_y = time_label_y + 80
            mode_label = small_font.render('Режим', True, TS)
            screen.blit(mode_label, (cx - field_w // 2, mode_label_y))
            
            mode_options = ['classic', 'chronos', 'safari']
            mode_names = {'classic': 'Обычный', 'chronos': 'Хронос', 'safari': 'Сафари'}
            btn_w = 100
            btn_h = 35
            spacing = 15
            total_w = btn_w * 3 + spacing * 2
            start_x = cx - total_w // 2
            mode_y = mode_label_y + 25
            
            edit_mode_rects = []
            for i, opt in enumerate(mode_options):
                rect = pygame.Rect(start_x + i * (btn_w + spacing), mode_y, btn_w, btn_h)
                edit_mode_rects.append((rect, opt))
                
                is_selected = (opt == edit_mtype)
                is_hover = rect.collidepoint(mp)
                
                color = AH if is_hover else (A if is_selected else CC)
                pygame.draw.rect(screen, color, rect, border_radius=8)
                if is_selected:
                    pygame.draw.rect(screen, A, rect, 2, border_radius=8)
                
                text_color = TP if (is_selected or is_hover) else TS
                text_surf = small_font.render(mode_names[opt], True, text_color)
                screen.blit(text_surf, text_surf.get_rect(center=rect.center))
                
                if mrel and not igcl and rect.collidepoint(mp):
                    edit_mtype = opt
            
            btn_y = ecy + ech - 55
            if save_btn is None:
                save_btn = AnimatedButton(cx - bww - bss // 2, btn_y, bww, bhh, 'СОХРАНИТЬ', button_font, theme['win'], CC)
                eback_btn = AnimatedButton(cx + bss // 2, btn_y, bww, bhh, 'ОТМЕНА', button_font, A, CC, AH)
            else:
                save_btn.set_position(cx - bww - bss // 2, btn_y)
                eback_btn.set_position(cx + bss // 2, btn_y)
            
            save_btn.update(dt, mp, mpr)
            eback_btn.update(dt, mp, mpr)
            save_btn.draw(screen)
            eback_btn.draw(screen)
            
            if mrel and not igcl and edit_mode:
                if edit_name_rect and edit_name_rect.collidepoint(mp):
                    edit_af = 'nickname'
                elif edit_time_rect and edit_time_rect.collidepoint(mp):
                    edit_af = 'time'
                else:
                    clicked_on_mode = False
                    for rect, opt in edit_mode_rects:
                        if rect.collidepoint(mp):
                            clicked_on_mode = True
                            break
                    if not clicked_on_mode and not save_btn.rect.collidepoint(mp) and not eback_btn.rect.collidepoint(mp):
                        edit_af = None
        
        else:
            tr3 = pygame.Rect(tx2, ty2, tw2, th2)
            pygame.draw.rect(screen, CC, tr3, border_radius=15)
            pygame.draw.rect(screen, A, tr3, 2, border_radius=15)
            
            headers2 = ["#", "Игрок", "Сложность", "Режим", "Время"]
            cw2 = [int(tw2 * 0.1), int(tw2 * 0.35), int(tw2 * 0.2), int(tw2 * 0.2), int(tw2 * 0.15)]
            hy3 = ty2 + 15
            xo2 = tx2 + 10
            
            for i, h in enumerate(headers2):
                ht2 = small_font.render(h, True, A)
                if i == 0:
                    screen.blit(ht2, (xo2 + 5, hy3))
                else:
                    screen.blit(ht2, (xo2 + sum(cw2[:i]) + (cw2[i] - ht2.get_width()) // 2, hy3))
            
            ly3 = hy3 + small_font.get_height() + 5
            pygame.draw.line(screen, A, (tx2 + 5, ly3), (tx2 + tw2 - 5, ly3), 1)
            
            sy3 = ly3 + 10
            rh2 = 40
            si = cur_page * rpp
            ei = min(si + rpp, len(records))
            
            for i in range(si, ei):
                n, d, mt, tv = records[i]
                y = sy3 + (i - si) * rh2
                ir2 = pygame.Rect(tx2, y, tw2, rh2)
                
                if (n, d, mt, tv) == sel_rec:
                    pygame.draw.rect(screen, (*A, 50), ir2, border_radius=5)
                    pygame.draw.rect(screen, A, ir2, 2, border_radius=5)
                
                screen.blit(small_font.render(str(i + 1), True, TP), (xo2 + 5, y + 8))
                screen.blit(small_font.render(n[:15], True, TP), (xo2 + cw2[0] + (cw2[1] - small_font.size(n[:15])[0]) // 2, y + 8))
                
                dt3 = {'easy': 'Легкий', 'average': 'Средний', 'hard': 'Сложный', 'super': 'Экстра'}[d]
                dr2 = small_font.render(dt3, True, TP)
                screen.blit(dr2, (xo2 + sum(cw2[:2]) + (cw2[2] - dr2.get_width()) // 2, y + 8))
                
                mt3 = {'classic': 'Обычный', 'chronos': 'Хронос', 'safari': 'Сафари'}.get(mt, mt)
                mr2 = small_font.render(mt3, True, TP)
                screen.blit(mr2, (xo2 + sum(cw2[:3]) + (cw2[3] - mr2.get_width()) // 2, y + 8))
                
                tmt2 = small_font.render(f"{tv:.2f}", True, TP)
                screen.blit(tmt2, (xo2 + sum(cw2[:4]) + (cw2[4] - tmt2.get_width()) // 2, y + 8))
            
            if tp > 1:
                ay2 = py2
                if larr is None:
                    larr = AnimatedButton(tx2 + 10, ay2, 40, 40, '<', button_font, A, TP, AH, border_radius=20)
                    rarr = AnimatedButton(tx2 + tw2 - 50, ay2, 40, 40, '>', button_font, A, TP, AH, border_radius=20)
                else:
                    larr.set_position(tx2 + 10, ay2)
                    rarr.set_position(tx2 + tw2 - 50, ay2)
                
                if cur_page > 0:
                    larr.update(dt, mp, mpr)
                    larr.draw(screen)
                if cur_page < tp - 1:
                    rarr.update(dt, mp, mpr)
                    rarr.draw(screen)
                
                pt2 = small_font.render(f'{cur_page + 1}/{tp}', True, TS)
                screen.blit(pt2, (cx - pt2.get_width() // 2, ay2 + 10))
            
            if not edit_mode and back_btn:
                back_btn.draw(screen)
            if not edit_mode and sel_rec and not edit_mode and del_btn:
                del_btn.draw(screen)
        
        effect_manager.draw(screen, current_width, current_height)
        
        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()