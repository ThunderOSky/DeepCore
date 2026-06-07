import pygame
import sys
import math
import random
import menu
from theme import *
from db_manager import *
from settings_manager import *
from ui import AnimatedButton
from music_manager import MusicManager
from effects import *

def get_rarity_color(rarity, time_offset=0):
    t = pygame.time.get_ticks() / 1000.0 + time_offset
    
    if rarity == 'common': return (100, 180, 255)
    elif rarity == 'rare': return (100, 255, 100)
    elif rarity == 'epic': return (180, 100, 255)
    elif rarity == 'legendary':
        r = 255; g = int(215 + math.sin(t * 2) * 40); b = int(50 + math.sin(t * 2) * 30)
        return (r, g, b)
    elif rarity == 'secret':
        r = int(200 + math.sin(t * 2) * 55); g = int(50 + math.sin(t * 2) * 30); b = int(50 + math.sin(t * 2) * 30)
        return (r, g, b)
    elif rarity == 'limited':
        r = int((math.sin(t * 2) * 127 + 128)); g = int((math.sin(t * 2 + 2) * 127 + 128)); b = int((math.sin(t * 2 + 4) * 127 + 128))
        return (r, g, b)
    return (255, 255, 255)


def get_level_color(level):
    if level < 10: return (255, 255, 255)
    elif level < 20: return (100, 255, 100)
    elif level < 30: return (100, 100, 255)
    elif level < 40: return (255, 255, 100)
    elif level < 50: return (255, 165, 0)
    elif level < 60: return (255, 100, 100)
    elif level < 70: return (180, 100, 255)
    elif level < 80:
        t = pygame.time.get_ticks() / 1000.0
        return (255, int(100 + math.sin(t * 2) * 155), int(math.sin(t * 2) * 100))
    elif level < 90:
        t = pygame.time.get_ticks() / 1000.0
        return (int(100 + math.sin(t * 2) * 100), int(100 + math.sin(t * 2 + 1) * 155), int(200 + math.sin(t * 2 + 2) * 55))
    else:
        t = pygame.time.get_ticks() / 1000.0
        return (int((math.sin(t * 2) * 127 + 128)), int((math.sin(t * 2 + 2) * 127 + 128)), int((math.sin(t * 2 + 4) * 127 + 128)))


def load_tinted_icon(icon_name, color, size=40):
    try:
        icon = pygame.image.load(f"icons/{icon_name}.png").convert_alpha()
        icon = pygame.transform.smoothscale(icon, (size, size))
        tinted = pygame.Surface((size, size), pygame.SRCALPHA)
        for x in range(size):
            for y in range(size):
                r, g, b, a = icon.get_at((x, y))
                if a > 0: tinted.set_at((x, y), (*color, min(a, 200)))
        return tinted
    except: return None


def draw_stat_card(screen, rect, title, value, theme, accent_color, animation_progress=1.0):
    CARD_COLOR = theme['card']; TEXT_PRIMARY = theme['text']; TEXT_SECONDARY = theme['text_secondary']
    ca = int(230 * animation_progress); ba = int(255 * animation_progress)
    
    cs = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(cs, (*CARD_COLOR, ca), (0, 0, rect.width, rect.height), border_radius=20)
    pygame.draw.rect(cs, (*accent_color, ba), (0, 0, rect.width, rect.height), 2, border_radius=20)
    screen.blit(cs, (rect.x, rect.y))
    
    vf = pygame.font.Font('font/font.otf', int(rect.height * 0.3))
    vs = vf.render(str(value), True, TEXT_PRIMARY)
    vs.set_alpha(int(255 * animation_progress))
    screen.blit(vs, (rect.centerx - vs.get_width()//2, rect.centery - vs.get_height()//2 - 5))
    
    tf = pygame.font.Font('font/font.otf', int(rect.height * 0.15))
    ts = tf.render(title, True, TEXT_SECONDARY)
    ts.set_alpha(int(255 * animation_progress))
    screen.blit(ts, (rect.centerx - ts.get_width()//2, rect.centery + 10))


def profile(nickname, viewing_own=True, viewer_nickname=None):
    pygame.init()
    
    vm = get_music(); vs = get_sound(); THEME = get_theme()
    set_theme(THEME)
    
    music_manager = MusicManager()

    click = music_manager.load_sound('click.mp3')
    ch = pygame.mixer.Channel(0); ch.set_volume(vs)
    
    sw, sh, sf = load_window_settings(1366, 768)
    if sf: screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else: screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
    
    pygame.display.set_caption(f'DeepCore - Профиль {nickname}')
    
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
    
    ud = get_user_data(); games = wins = 0
    for i in range(len(ud['logins'])):
        if nickname == ud['logins'][i]: games, wins = ud['games'][i], ud['wins'][i]; break
    win_rate = (wins / games * 100) if games > 0 else 0
    
    ld = get_player_level(nickname)
    pl = ld['level'] if ld else 1; pe = ld['experience'] if ld else 0; nle = ld['next_level_exp'] if ld else 50
    
    pa = get_player_achievements(nickname); aa = get_all_achievements()
    sa = get_showcased_achievements(nickname) or [a[0] for a in pa[:5]]
    
    ap = 0; animating = True
    showing_ach = False; cur_page = 0; selecting_sc = False
    showing_color = False; cp_page = 0
    
    ach_btn = None; color_btn = None; back_btn = None
    ach_back_btn = None; close_btn = None
    ach_left_btn = None; ach_right_btn = None
    col_left_btn = None; col_right_btn = None
    showcase_btn = None
    
    mwp = False; igcl = True; frm = 0; acd = 0
    
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
        
        if acd > 0: acd -= dt
        frm += 1
        if frm > 3: igcl = False
        
        if animating:
            ap = min(1.0, ap + 0.03)
            if ap >= 1.0: animating = False
        
        if last_theme != get_theme():
            last_theme = get_theme(); set_theme(last_theme)
        
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
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.VIDEORESIZE and not is_full:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                wsz = (e.w, e.h); save_window_settings(e.w, e.h, is_full); continue
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F11: toggle_fs(); pygame.display.flip(); continue
                if e.key == pygame.K_ESCAPE and viewing_own: menu.menu(nickname, 1); return
            if e.type == pygame.MOUSEBUTTONDOWN: ch.play(click)
        
        if showing_ach:
            ty = int(ch2 * 0.05)
            cdw, cdh = int(cw * 0.8), int(ch2 * 0.7)
            cdx, cdy = cx - cdw // 2, int(ch2 * 0.12)
            
            ipp = 8; ih = 55
            
            if viewing_own: da = [a for a in aa if not (a[4] == 1 and a[0] not in [p[0] for p in pa])]
            else: da = [a for a in aa if a[0] in [p[0] for p in pa]]
            da = [a for a in da if not (a[3] == 'limited' and a[0] not in [p[0] for p in pa])]
            
            tp = max(1, (len(da) + ipp - 1) // ipp)
            if cur_page >= tp: cur_page = tp - 1
            
            if ach_back_btn is None:
                ach_back_btn = AnimatedButton(cx - 90, cdy + cdh + 60, 180, 45, 'НАЗАД', button_font, A, CC, AH)
            else:
                ach_back_btn.set_position(cx - 90, cdy + cdh + 60)
            ach_back_btn.update(dt, mp, mpr)
            
            tt2 = title_font.render('ДОСТИЖЕНИЯ', True, A)
            screen.blit(tt2, (cx - tt2.get_width()//2, ty))
            
            lr = pygame.Rect(cdx, cdy, cdw, cdh)
            pygame.draw.rect(screen, CC, lr, border_radius=15)
            pygame.draw.rect(screen, A, lr, 2, border_radius=15)
            
            if viewing_own:
                if showcase_btn is None:
                    showcase_btn = AnimatedButton(cx - 125, cdy + cdh - 50, 250, 35, 'Выбрать для витрины', small_font, A, CC, AH)
                else:
                    showcase_btn.set_position(cx - 125, cdy + cdh - 50)
                showcase_btn.text = 'Готово' if selecting_sc else 'Выбрать для витрины'
                showcase_btn.update(dt, mp, mpr)
                showcase_btn.draw(screen)
            
            si = cur_page * ipp; ei = min(si + ipp, len(da))
            for i in range(si, ei):
                ach = da[i]
                ach_id, name, desc, rarity, secret, _, _, _, _, _, _, icon = ach
                owned = ach_id in [p[0] for p in pa]
                y = cdy + 50 + (i - si) * ih
                ir = pygame.Rect(cdx + 20, y, cdw - 40, ih - 2)
                
                if owned:
                    if ach_id in sa: pygame.draw.rect(screen, (*A, 80), ir, border_radius=8); pygame.draw.rect(screen, A, ir, 2, border_radius=8)
                    else: pygame.draw.rect(screen, (*CC, 200), ir, border_radius=8)
                    screen.blit(subtitle_font.render(name, True, get_rarity_color(rarity, i*0.5)), (cdx+35, y+5))
                    screen.blit(small_font.render(desc[:50]+('...' if len(desc)>50 else ''), True, TS), (cdx+35, y+30))
                    if selecting_sc and ach_id in sa:
                        screen.blit(small_font.render('✓', True, A), (cdx+cdw-50, y+10))
                else:
                    if secret:
                        pygame.draw.rect(screen, (50,50,50,100), ir, border_radius=8)
                        screen.blit(subtitle_font.render('???', True, (120,120,120)), (cdx+35, y+5))
                        screen.blit(small_font.render('Скрытое достижение', True, (100,100,100)), (cdx+35, y+30))
                    else:
                        pygame.draw.rect(screen, (50,50,50,80), ir, border_radius=8)
                        screen.blit(subtitle_font.render(name, True, (120,120,120)), (cdx+35, y+5))
                        screen.blit(small_font.render(desc[:50]+('...' if len(desc)>50 else ''), True, (100,100,100)), (cdx+35, y+30))
            
            if tp > 1:
                ay = cdy + cdh + 10
                if ach_left_btn is None:
                    ach_left_btn = AnimatedButton(cdx+10, ay, 40, 40, '<', button_font, A, TP, AH, border_radius=20)
                    ach_right_btn = AnimatedButton(cdx+cdw-50, ay, 40, 40, '>', button_font, A, TP, AH, border_radius=20)
                else:
                    ach_left_btn.set_position(cdx+10, ay); ach_right_btn.set_position(cdx+cdw-50, ay)
                if cur_page > 0: ach_left_btn.update(dt, mp, mpr); ach_left_btn.draw(screen)
                if cur_page < tp-1: ach_right_btn.update(dt, mp, mpr); ach_right_btn.draw(screen)
                pt = small_font.render(f'{cur_page+1}/{tp}', True, TS)
                screen.blit(pt, (cx - pt.get_width()//2, ay+10))
            
            ach_back_btn.draw(screen)
            
            if mrel and not igcl:
                if ach_back_btn.is_clicked(mp, True): showing_ach = False; cur_page = 0
                if viewing_own and showcase_btn.is_clicked(mp, True): selecting_sc = not selecting_sc
                if tp > 1 and acd <= 0:
                    if ach_left_btn and ach_left_btn.is_clicked(mp, True) and cur_page > 0: cur_page -= 1; acd = 0.15
                    if ach_right_btn and ach_right_btn.is_clicked(mp, True) and cur_page < tp-1: cur_page += 1; acd = 0.15
                if viewing_own and selecting_sc:
                    for i in range(si, ei):
                        ach = da[i]; ach_id = ach[0]; y = cdy+50+(i-si)*ih
                        if pygame.Rect(cdx+20, y, cdw-40, ih-2).collidepoint(mp) and ach_id in [p[0] for p in pa]:
                            toggle_showcased_achievement(nickname, ach_id); sa = get_showcased_achievements(nickname)
        else:
            ty = int(ch2 * 0.06); sy = int(ch2 * 0.13)
            avs = int(ch2 * 0.15); avy = int(ch2 * 0.20)
            
            st_y = avy + avs + int(ch2 * 0.04)
            cw2, ch3 = int(cw * 0.20), int(ch2 * 0.10)
            cs2 = int(cw * 0.02)
            csx = cx - (cw2*3 + cs2*2)//2
            
            sh_y = st_y + ch3 + int(ch2 * 0.04)
            sw2, sh2 = int(cw * 0.6), int(ch2 * 0.20)
            sh_x = cx - sw2 // 2
            
            bw2, bh2 = int(cw * 0.15), int(ch2 * 0.06)
            bs2 = int(cw * 0.02)
            btx = cx - (bw2*3 + bs2*2)//2
            bty = sh_y + sh2 + 15
            
            if ach_btn is None:
                ach_btn = AnimatedButton(btx, bty, bw2, bh2, 'ДОСТИЖЕНИЯ', button_font, A, CC, AH)
                color_btn = AnimatedButton(btx+bw2+bs2, bty, bw2, bh2, 'ЦВЕТ', button_font, A, CC, AH)
                back_btn = AnimatedButton(btx+(bw2+bs2)*2, bty, bw2, bh2, 'НАЗАД', button_font, A, CC, AH)
            else:
                ach_btn.set_position(btx, bty); ach_btn.original_rect.width = bw2; ach_btn.original_rect.height = bh2
                color_btn.set_position(btx+bw2+bs2, bty); color_btn.original_rect.width = bw2; color_btn.original_rect.height = bh2
                back_btn.set_position(btx+(bw2+bs2)*2, bty); back_btn.original_rect.width = bw2; back_btn.original_rect.height = bh2
            
            ach_btn.update(dt, mp, mpr); color_btn.update(dt, mp, mpr); back_btn.update(dt, mp, mpr)
            
            tt3 = title_font.render('ПРОФИЛЬ', True, A); tt3.set_alpha(int(255*ap))
            screen.blit(tt3, (cx - tt3.get_width()//2, ty))
            
            nc = get_nickname_color(nickname)
            if nc == "default": cr = TP
            elif nc.startswith('#'): cr = hex_to_rgb(nc)
            else: cr = get_animated_color(nc)
            ns = subtitle_font.render(nickname, True, cr); ns.set_alpha(int(255*ap))
            screen.blit(ns, (cx - ns.get_width()//2, sy))
            
            cav = int(avs * ap)
            if cav > 0:
                cax, cay = cx - cav//2, avy
                lc = get_level_color(pl)
                avs2 = pygame.Surface((cav, cav), pygame.SRCALPHA)
                pygame.draw.circle(avs2, (*CC, int(230*ap)), (cav//2, cav//2), cav//2)
                pygame.draw.circle(avs2, (*lc, int(255*ap)), (cav//2, cav//2), cav//2, 4)
                screen.blit(avs2, (cax, cay))
                lnf = pygame.font.Font('font/font.otf', int(cav*0.5))
                lnt = lnf.render(str(pl), True, lc); lnt.set_alpha(int(255*ap))
                screen.blit(lnt, lnt.get_rect(center=(cx, cay+cav//2)))
            
            ebw = int(cw * 0.15); ebx = cx - ebw//2; eby = avy + avs + 10
            pygame.draw.rect(screen, (*CC, 150), (ebx, eby, ebw, 6), border_radius=3)
            if nle > 0:
                fw = int(ebw * (pe/nle))
                if fw > 0: pygame.draw.rect(screen, A, (ebx, eby, fw, 6), border_radius=3)
            pygame.draw.rect(screen, A, (ebx, eby, ebw, 6), 1, border_radius=3)
            et = small_font.render(f'{pe}/{nle} XP', True, TS); et.set_alpha(int(150*ap))
            screen.blit(et, (cx - et.get_width()//2, eby+8))
            
            if ap > 0.3:
                ca = min(1.0, (ap-0.3)/0.7)
                draw_stat_card(screen, pygame.Rect(csx, st_y, cw2, ch3), "Игр сыграно", games, theme, A, ca)
                draw_stat_card(screen, pygame.Rect(csx+cw2+cs2, st_y, cw2, ch3), "Побед", wins, theme, A, ca)
                draw_stat_card(screen, pygame.Rect(csx+(cw2+cs2)*2, st_y, cw2, ch3), "Процент побед", f"{win_rate:.1f}%", theme, A, ca)
            
            if ap > 0.5:
                sa2 = int(200*ap)
                pygame.draw.rect(screen, (*CC, sa2), (sh_x, sh_y, sw2, sh2), border_radius=15)
                pygame.draw.rect(screen, (*A, int(150*ap)), (sh_x, sh_y, sw2, sh2), 2, border_radius=15)
                screen.blit(small_font.render('Витрина достижений', True, TS), (sh_x+15, sh_y+8))
                
                sach = [a for a in pa if a[0] in sa][:5]
                if not sach:
                    screen.blit(small_font.render('Выберите достижения для витрины', True, TS), (cx-100, sh_y+sh2//2))
                else:
                    iw = (sw2-60)//5
                    for i, ach in enumerate(sach):
                        ach_id, name, desc, rarity, secret, icon, _ = ach
                        x = sh_x+20+i*iw
                        color = get_rarity_color(rarity, i*1.0)
                        icon_img = load_tinted_icon(icon, color, 36)
                        if icon_img: screen.blit(icon_img, (x+iw//2-18, sh_y+46))
                        else: pygame.draw.circle(screen, color, (x+iw//2, sh_y+65), 20, 2)
                        
                        words = name.split(); lines, cl = [], ""
                        for w in words:
                            if small_font.size(cl+" "+w)[0] <= iw: cl += (" " if cl else "") + w
                            else: lines.append(cl); cl = w
                        if cl: lines.append(cl)
                        for j, line in enumerate(lines[:2]):
                            ls = small_font.render(line, True, TP)
                            screen.blit(ls, (x+(iw-ls.get_width())//2, sh_y+85+j*20))
            
            ach_btn.draw(screen)
            if viewing_own: color_btn.draw(screen)
            back_btn.draw(screen)
            
            if mrel and not igcl:
                if ach_btn.is_clicked(mp, True): showing_ach = True; cur_page = 0; selecting_sc = False
                if color_btn.is_clicked(mp, True) and viewing_own: showing_color = True; cp_page = 0
                if back_btn.is_clicked(mp, True):
                    if viewing_own: menu.menu(nickname, 1)
                    else: import top; top.top(viewer_nickname)
                    return
        
        if showing_color and viewing_own:
            overlay = pygame.Surface((cw, ch2), pygame.SRCALPHA); overlay.fill((0,0,0,180)); screen.blit(overlay, (0,0))
            
            pw, ph = int(cw*0.7), int(ch2*0.6); px, py = cx-pw//2, int(ch2*0.15)
            pygame.draw.rect(screen, CC, (px, py, pw, ph), border_radius=20)
            pygame.draw.rect(screen, A, (px, py, pw, ph), 2, border_radius=20)
            screen.blit(subtitle_font.render('Выбор цвета', True, A), (cx-60, py+15))
            
            ac = get_available_nickname_colors(); ul = get_unlocked_colors(nickname)
            all_colors = []
            for name in ul["basic"]:
                if name in ac["basic"]: all_colors.append(("basic", name, ac["basic"][name]))
            for name in ul["animated"]:
                if name in ac["animated"]: all_colors.append(("animated", name, ac["animated"][name]))
            for name in ul["achievement"]:
                if name in ac["achievement"]: all_colors.append(("achievement", name, ac["achievement"][name]))
            
            cpp = 7; tpc = max(1, (len(all_colors)+cpp-1)//cpp)
            if cp_page >= tpc: cp_page = tpc-1
            
            si2 = cp_page*cpp; ei2 = min(si2+cpp, len(all_colors))
            for i in range(si2, ei2):
                cat, name, value = all_colors[i]; y = py+55+(i-si2)*55
                ir = pygame.Rect(px+30, y, pw-60, 50)
                ih2 = ir.collidepoint(mp)
                pygame.draw.rect(screen, (*(AH if ih2 else CC), 200), ir, border_radius=10)
                pygame.draw.rect(screen, A, ir, 1, border_radius=10)
                
                try:
                    if value == "default": dc = TP
                    elif value.startswith('#'): dc = hex_to_rgb(value)
                    else: dc = get_animated_color(value, i*0.3)
                except: dc = TP
                screen.blit(subtitle_font.render(name, True, dc), (px+50, y+10))
                
                if mrel and ih2 and not igcl: set_nickname_color(nickname, value); showing_color = False
            
            if tpc > 1:
                ay = py+ph-40
                if col_left_btn is None:
                    col_left_btn = AnimatedButton(px+10, ay, 40, 40, '<', button_font, A, TP, AH, border_radius=20)
                    col_right_btn = AnimatedButton(px+pw-50, ay, 40, 40, '>', button_font, A, TP, AH, border_radius=20)
                else: col_left_btn.set_position(px+10, ay); col_right_btn.set_position(px+pw-50, ay)
                if cp_page > 0: col_left_btn.update(dt, mp, mpr); col_left_btn.draw(screen)
                if cp_page < tpc-1: col_right_btn.update(dt, mp, mpr); col_right_btn.draw(screen)
                pt = small_font.render(f'{cp_page+1}/{tpc}', True, TS)
                screen.blit(pt, (cx-pt.get_width()//2, ay+10))
            
            if close_btn is None:
                close_btn = AnimatedButton(cx-60, py+ph-40, 120, 35, 'Закрыть', small_font, ER, TP)
            else: close_btn.set_position(cx-60, py+ph-40)
            close_btn.update(dt, mp, mpr); close_btn.draw(screen)
            
            if mrel and not igcl:
                if close_btn.is_clicked(mp, True): showing_color = False
                if tpc > 1 and acd <= 0:
                    if col_left_btn and col_left_btn.is_clicked(mp, True) and cp_page > 0: cp_page -= 1; acd = 0.15
                    if col_right_btn and col_right_btn.is_clicked(mp, True) and cp_page < tpc-1: cp_page += 1; acd = 0.15
        
        effect_manager.draw(screen, current_width, current_height)
        
        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()