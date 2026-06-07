import pygame
import sys
import menu, menu_game, game, admin_panel
from theme import *
from settings_manager import *
from db_manager import *
from ui import AnimatedButton
from music_manager import *
import math
import settings_manager
from effects import *

class Slider:
    def __init__(self, x, y, width, height, value, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.value = value
        self.color = color
        self.hover_color = hover_color
        self.dragging = False
        self.knob_radius = height * 2
        
    def update(self, mouse_pos, mouse_pressed):
        if self.rect.collidepoint(mouse_pos) and mouse_pressed:
            self.dragging = True
        if self.dragging:
            if not mouse_pressed: self.dragging = False
            else:
                rel = max(0, min(mouse_pos[0] - self.rect.x, self.rect.width))
                self.value = rel / self.rect.width
        return self.value
    
    def draw(self, screen, accent_color):
        pygame.draw.rect(screen, (100, 100, 100, 50), self.rect, border_radius=self.rect.height//2)
        fw = int(self.rect.width * self.value)
        pygame.draw.rect(screen, accent_color, (self.rect.x, self.rect.y, fw, self.rect.height), border_radius=self.rect.height//2)
        kx = self.rect.x + fw
        pygame.draw.circle(screen, accent_color, (kx, self.rect.centery), self.knob_radius)
        pygame.draw.circle(screen, (255, 255, 255), (kx, self.rect.centery), self.knob_radius, 2)


class ThemeCarousel:
    def __init__(self, x, y, width, height, items_list, current_item, display_names=None):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.items = items_list
        self.display_names = display_names or {item: item.upper() for item in items_list}
        self.current_index = items_list.index(current_item) if current_item in items_list else 0
        
    def next_item(self):
        self.current_index = (self.current_index + 1) % len(self.items)
        return self.items[self.current_index]
    
    def prev_item(self):
        self.current_index = (self.current_index - 1) % len(self.items)
        return self.items[self.current_index]
    
    def draw(self, screen, theme_colors):
        bg_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, theme_colors['card'], bg_rect, border_radius=15)
        pygame.draw.rect(screen, theme_colors['accent'], bg_rect, 2, border_radius=15)
        
        item = self.items[self.current_index]
        name = self.display_names.get(item, item.upper())
        
        fs = min(24, self.height // 3)
        tf = pygame.font.Font('font/font.otf', fs)
        ts = tf.render(name, True, theme_colors['text'])
        screen.blit(ts, (self.x + (self.width - ts.get_width())//2, self.y + (self.height - ts.get_height())//2))


class MusicPackCarousel:
    def __init__(self, x, y, width, height, items_list, current_item, display_names=None):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.items = items_list
        self.display_names = display_names or {}
        self.current_index = items_list.index(current_item) if current_item in items_list else 0
        self.glow_phase = 0
        
    def next_item(self):
        self.current_index = (self.current_index + 1) % len(self.items)
        return self.items[self.current_index]
    
    def prev_item(self):
        self.current_index = (self.current_index - 1) % len(self.items)
        return self.items[self.current_index]
    
    def update(self, dt):
        self.glow_phase += dt * 3
        
    def draw(self, screen, theme_colors):
        bg_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        shadow_surf = pygame.Surface((self.width + 4, self.height + 4), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 40), (2, 2, self.width, self.height), border_radius=15)
        screen.blit(shadow_surf, (self.x - 2, self.y - 2))
        
        pygame.draw.rect(screen, theme_colors['card'], bg_rect, border_radius=15)
        pygame.draw.rect(screen, theme_colors['accent'], bg_rect, 2, border_radius=15)
        
        glow = abs(math.sin(self.glow_phase)) * 20
        inner_rect = pygame.Rect(self.x + 2, self.y + 2, self.width - 4, self.height - 4)
        pygame.draw.rect(screen, (*theme_colors['accent'], int(glow)), inner_rect, 1, border_radius=13)
        
        item = self.items[self.current_index]
        name = self.display_names.get(item, item.upper())
        
        fs = min(24, self.height // 3)
        tf = pygame.font.Font('font/font.otf', fs)
        ts = tf.render(name, True, theme_colors['text'])
        screen.blit(ts, (self.x + (self.width - ts.get_width())//2, self.y + (self.height - ts.get_height())//2))


def settings(nickname, place):
    global volume_music, volume_sound, THEME
    pygame.init()
    
    sw = get_window_width(); sh = get_window_height(); sf = get_fullscreen()
    
    if sf: screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else: screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
    
    pygame.display.set_caption('DeepCore - Настройки')
    
    is_full = sf
    wsz = (sw, sh) if not sf else (1366, 768)
    
    def toggle_fs():
        nonlocal screen, is_full, wsz
        if is_full: screen = pygame.display.set_mode(wsz, pygame.RESIZABLE); is_full = False
        else: wsz = screen.get_size(); screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN); is_full = True
        update_settings(is_fullscreen=is_full, width=wsz[0], height=wsz[1])
    
    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)
    
    vm = get_music(); vs = get_sound(); THEME = get_theme()
    set_theme(THEME)
    
    music_manager = MusicManager()
    av_music_packs = music_manager.get_available_packs()
    music_pack_display = {
        "classic": "Стандартный",
        "minecraft": "Майнкрафт",
        "custom": "Пользовательский",
        "city": "Современный"
    }
    
    av_themes = get_available_themes()
    av_effects = get_available_effects()
    
    orig_theme = THEME
    orig_eff = get_effect()
    orig_music_pack = get_music_pack()
    orig_vm = vm
    orig_vs = vs
    
    current_theme = THEME
    current_eff = orig_eff
    current_music_pack = orig_music_pack
    current_vm = vm
    current_vs = vs
    
    original_saved_pack = get_music_pack()
    
    click_sound = None
    click_channel = pygame.mixer.Channel(0)
    click_channel.set_volume(current_vs)
    
    def update_click_sound():
        nonlocal click_sound
        settings_manager.update_settings(music_pack=current_music_pack)
        click_sound = music_manager.load_sound('click.mp3')
        if click_sound is None:
            click_sound = pygame.mixer.Sound("sounds/classic/click.mp3")
    
    def preview_music():
        old_pack = get_music_pack()
        from settings_manager import update_settings
        update_settings(music_pack=current_music_pack)
        music_manager.load_music('menu', current_vm, force=True)
        update_settings(music_pack=old_pack)
    
    update_click_sound()
    
    music_manager.load_music('menu.mp3', current_vm)
    
    cur_pass = ''; new_pass = ''; conf_pass = ''
    pass_msg = ''; pass_msg_timer = 0; pass_msg_col = (255,255,255)
    cp_active = False; np_active = False; cf_active = False
    
    mwp = False; igcl = True; frm = 0
    sliders = {}
    theme_car = None; eff_car = None; music_pack_car = None
    
    apply_btn = None; reset_btn = None; cancel_btn = None; change_pass_btn = None
    th_left_btn = None; th_right_btn = None
    eff_left_btn = None; eff_right_btn = None
    music_pack_left_btn = None; music_pack_right_btn = None
    
    run = True; clock = pygame.time.Clock()
    last_theme = THEME
    
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
        
        if last_theme != current_theme:
            last_theme = current_theme
            set_theme(current_theme)
        
        theme = get_current_theme()
        A = theme['accent']; AH = theme['accent_hover']; CC = theme['card']
        TP = theme['text']; TS = theme['text_secondary']; ER = theme['error']
        IB = theme['input_bg']; BR = theme['border']

        if th_left_btn is not None:
            th_left_btn.base_color = A
            th_left_btn.hover_color = AH
            th_left_btn.text_color = TP
            
            th_right_btn.base_color = A
            th_right_btn.hover_color = AH
            th_right_btn.text_color = TP
            
            eff_left_btn.base_color = A
            eff_left_btn.hover_color = AH
            eff_left_btn.text_color = TP
            
            eff_right_btn.base_color = A
            eff_right_btn.hover_color = AH
            eff_right_btn.text_color = TP
            
            music_pack_left_btn.base_color = A
            music_pack_left_btn.hover_color = AH
            music_pack_left_btn.text_color = TP
            
            music_pack_right_btn.base_color = A
            music_pack_right_btn.hover_color = AH
            music_pack_right_btn.text_color = TP
            
            apply_btn.base_color = A
            apply_btn.hover_color = AH
            apply_btn.text_color = CC
            
            reset_btn.base_color = ER
            reset_btn.hover_color = AH
            reset_btn.text_color = CC
            
            cancel_btn.base_color = A
            cancel_btn.hover_color = AH
            cancel_btn.text_color = CC
            
            change_pass_btn.base_color = A
            change_pass_btn.hover_color = AH
            change_pass_btn.text_color = CC
        
        cx = cw // 2
        
        ty = int(ch2 * 0.04)
        sl_w = int(cw * 0.35); sl_h = 8; sl_x = cx - sl_w // 2
        music_y = int(ch2 * 0.14); sound_y = int(ch2 * 0.22)
        
        theme_y = int(ch2 * 0.32); th_cw = int(cw * 0.25); th_ch = 40
        th_cx = cx - th_cw // 2; th_cy = theme_y + 35
        
        eff_y = int(ch2 * 0.44); eff_cw = int(cw * 0.18); eff_ch = 35
        eff_cx = cx - eff_cw // 2; eff_cy = eff_y + 35
        
        music_pack_y = int(ch2 * 0.56); music_pack_cw = int(cw * 0.22); music_pack_ch = 40
        music_pack_cx = cx - music_pack_cw // 2; music_pack_cy = music_pack_y + 35
        
        pass_y = int(ch2 * 0.68); pf_w = int(cw * 0.13); pf_h = 35
        pf_sx = cx - int(cw * 0.28); pb_w = 110; pb_h = 35
        
        btns_y = int(ch2 * 0.85); btn_w = 120; btn_h = 35; btn_s = 20
        
        if not sliders:
            sliders['music'] = Slider(sl_x, music_y+25, sl_w, sl_h, current_vm, (0,0,0), (0,0,0))
            sliders['sound'] = Slider(sl_x, sound_y+25, sl_w, sl_h, current_vs, (0,0,0), (0,0,0))
        sliders['music'].rect = pygame.Rect(sl_x, music_y+25, sl_w, sl_h)
        sliders['sound'].rect = pygame.Rect(sl_x, sound_y+25, sl_w, sl_h)
        sliders['music'].color = A; sliders['music'].hover_color = AH
        sliders['sound'].color = A; sliders['sound'].hover_color = AH
        
        current_vm = sliders['music'].update(mp, mpr)
        current_vs = sliders['sound'].update(mp, mpr)
        
        pygame.mixer.music.set_volume(current_vm)
        click_channel.set_volume(current_vs)
        
        if not theme_car: 
            theme_car = ThemeCarousel(th_cx, th_cy, th_cw, th_ch, av_themes, current_theme)
        else:
            theme_car.x, theme_car.y, theme_car.width, theme_car.height = th_cx, th_cy, th_cw, th_ch
            
        if not eff_car: 
            eff_car = ThemeCarousel(eff_cx, eff_cy, eff_cw, eff_ch, av_effects, current_eff, EFFECTS)
        else:
            eff_car.x, eff_car.y, eff_car.width, eff_car.height = eff_cx, eff_cy, eff_cw, eff_ch
        
        if music_pack_car is None:
            music_pack_car = MusicPackCarousel(music_pack_cx, music_pack_cy, music_pack_cw, music_pack_ch, 
                                               av_music_packs, current_music_pack, music_pack_display)
        else:
            music_pack_car.x, music_pack_car.y = music_pack_cx, music_pack_cy
            music_pack_car.width, music_pack_car.height = music_pack_cw, music_pack_ch
        
        music_pack_car.update(dt)
        
        if apply_btn is None:
            apply_btn = AnimatedButton(cx - btn_w*1.5 - btn_s, btns_y, btn_w, btn_h, 'ПРИМЕНИТЬ', button_font, A, CC, AH)
            reset_btn = AnimatedButton(cx - btn_w//2, btns_y, btn_w, btn_h, 'СБРОС', button_font, ER, CC)
            cancel_btn = AnimatedButton(cx + btn_w//2 + btn_s, btns_y, btn_w, btn_h, 'ОТМЕНА', button_font, A, CC, AH)
            change_pass_btn = AnimatedButton(pf_sx + (pf_w+20)*3 + 10, pass_y+30, pb_w, pb_h, 'Изменить', button_font, A, CC, AH)
        else:
            apply_btn.set_position(cx - btn_w*1.5 - btn_s, btns_y)
            reset_btn.set_position(cx - btn_w//2, btns_y)
            cancel_btn.set_position(cx + btn_w//2 + btn_s, btns_y)
            change_pass_btn.set_position(pf_sx + (pf_w+20)*3 + 10, pass_y+30)
        
        apply_btn.update(dt, mp, mpr); reset_btn.update(dt, mp, mpr)
        cancel_btn.update(dt, mp, mpr); change_pass_btn.update(dt, mp, mpr)
        
        if th_left_btn is None:
            th_left_btn = AnimatedButton(th_cx-35, th_cy+th_ch//2-15, 30, 30, '<', button_font, A, TP, AH, border_radius=15)
            th_right_btn = AnimatedButton(th_cx+th_cw+5, th_cy+th_ch//2-15, 30, 30, '>', button_font, A, TP, AH, border_radius=15)
        else:
            th_left_btn.set_position(th_cx-35, th_cy+th_ch//2-15)
            th_right_btn.set_position(th_cx+th_cw+5, th_cy+th_ch//2-15)
        th_left_btn.update(dt, mp, mpr); th_right_btn.update(dt, mp, mpr)
        
        if eff_left_btn is None:
            eff_left_btn = AnimatedButton(eff_cx-35, eff_cy+eff_ch//2-15, 30, 30, '<', button_font, A, TP, AH, border_radius=15)
            eff_right_btn = AnimatedButton(eff_cx+eff_cw+5, eff_cy+eff_ch//2-15, 30, 30, '>', button_font, A, TP, AH, border_radius=15)
        else:
            eff_left_btn.set_position(eff_cx-35, eff_cy+eff_ch//2-15)
            eff_right_btn.set_position(eff_cx+eff_cw+5, eff_cy+eff_ch//2-15)
        eff_left_btn.update(dt, mp, mpr); eff_right_btn.update(dt, mp, mpr)
        
        if music_pack_left_btn is None:
            music_pack_left_btn = AnimatedButton(music_pack_cx-35, music_pack_cy+music_pack_ch//2-15, 30, 30, '<', button_font, A, TP, AH, border_radius=15)
            music_pack_right_btn = AnimatedButton(music_pack_cx+music_pack_cw+5, music_pack_cy+music_pack_ch//2-15, 30, 30, '>', button_font, A, TP, AH, border_radius=15)
        else:
            music_pack_left_btn.set_position(music_pack_cx-35, music_pack_cy+music_pack_ch//2-15)
            music_pack_right_btn.set_position(music_pack_cx+music_pack_cw+5, music_pack_cy+music_pack_ch//2-15)
        music_pack_left_btn.update(dt, mp, mpr); music_pack_right_btn.update(dt, mp, mpr)
        
        if pass_msg_timer > 0: pass_msg_timer -= 1
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.VIDEORESIZE and not is_full:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                wsz = (e.w, e.h); update_settings(width=e.w, height=e.h); continue
            if e.type == pygame.KEYDOWN and e.key == pygame.K_F11: toggle_fs(); pygame.display.flip(); continue
            if e.type == pygame.MOUSEBUTTONDOWN:
                if click_sound:
                    click_channel.play(click_sound)
                cp_active = pygame.Rect(pf_sx, pass_y+30, pf_w, pf_h).collidepoint(e.pos)
                np_active = pygame.Rect(pf_sx+pf_w+20, pass_y+30, pf_w, pf_h).collidepoint(e.pos)
                cf_active = pygame.Rect(pf_sx+(pf_w+20)*2, pass_y+30, pf_w, pf_h).collidepoint(e.pos)
                if not (cp_active or np_active or cf_active):
                    if not change_pass_btn.rect.collidepoint(e.pos):
                        cp_active = np_active = cf_active = False
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_LALT, pygame.K_RALT, 
                            pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LMETA, pygame.K_RMETA]: continue
                if cp_active:
                    if e.key == pygame.K_BACKSPACE: cur_pass = cur_pass[:-1]
                    elif e.key == pygame.K_TAB: cp_active = False; np_active = True
                    elif e.key == pygame.K_RETURN: np_active = True; cp_active = False
                    elif len(cur_pass) < 30 and e.unicode.isprintable(): cur_pass += e.unicode
                elif np_active:
                    if e.key == pygame.K_BACKSPACE: new_pass = new_pass[:-1]
                    elif e.key == pygame.K_TAB: np_active = False; cf_active = True
                    elif e.key == pygame.K_RETURN: cf_active = True; np_active = False
                    elif len(new_pass) < 30 and e.unicode.isprintable(): new_pass += e.unicode
                elif cf_active:
                    if e.key == pygame.K_BACKSPACE: conf_pass = conf_pass[:-1]
                    elif e.key == pygame.K_TAB: cf_active = False; cp_active = True
                    elif e.key == pygame.K_RETURN:
                        if not cur_pass: pass_msg = 'Введите текущий пароль'; pass_msg_col = ER; pass_msg_timer = 180
                        elif not new_pass: pass_msg = 'Введите новый пароль'; pass_msg_col = ER; pass_msg_timer = 180
                        elif new_pass != conf_pass: pass_msg = 'Новые пароли не совпадают'; pass_msg_col = ER; pass_msg_timer = 180
                        elif cur_pass == new_pass: pass_msg = 'Новый пароль не должен быть таким же, как старый'; pass_msg_col = ER; pass_msg_timer = 180
                        else:
                            from db_manager import get_user_data
                            ud = get_user_data(); ok = False
                            for i in range(len(ud['logins'])):
                                if ud['logins'][i] == nickname and ud['passwords'][i] == cur_pass: ok = True; break
                            if ok:
                                if update_player_password(nickname, new_pass):
                                    pass_msg = 'Пароль успешно сменён'; pass_msg_col = theme['win']; pass_msg_timer = 180
                                    cur_pass = new_pass = conf_pass = ''
                                    cp_active = np_active = cf_active = False
                            else: pass_msg = 'Неверно введён старый пароль'; pass_msg_col = ER; pass_msg_timer = 180
                    elif len(conf_pass) < 30 and e.unicode.isprintable(): conf_pass += e.unicode
        
        if mrel and not igcl:
            if th_left_btn.is_clicked(mp, True):
                current_theme = theme_car.prev_item()
                set_theme(current_theme)
            if th_right_btn.is_clicked(mp, True):
                current_theme = theme_car.next_item()
                set_theme(current_theme)
            
            if eff_left_btn.is_clicked(mp, True):
                current_eff = eff_car.prev_item()
                update_settings(effect=current_eff)
            if eff_right_btn.is_clicked(mp, True):
                current_eff = eff_car.next_item()
                update_settings(effect=current_eff)
            
            if music_pack_left_btn.is_clicked(mp, True):
                current_music_pack = music_pack_car.prev_item()
                preview_music()
                update_click_sound()
            if music_pack_right_btn.is_clicked(mp, True):
                current_music_pack = music_pack_car.next_item()
                preview_music()
                update_click_sound()
            
            if change_pass_btn.is_clicked(mp, True):
                if not cur_pass: pass_msg = 'Введите текущий пароль'; pass_msg_col = ER; pass_msg_timer = 180
                elif not new_pass: pass_msg = 'Введите новый пароль'; pass_msg_col = ER; pass_msg_timer = 180
                elif new_pass != conf_pass: pass_msg = 'Новые пароли не совпадают'; pass_msg_col = ER; pass_msg_timer = 180
                elif cur_pass == new_pass: pass_msg = 'Новый пароль не должен быть таким же, как старый'; pass_msg_col = ER; pass_msg_timer = 180
                else:
                    from db_manager import get_user_data
                    ud = get_user_data(); ok = False
                    for i in range(len(ud['logins'])):
                        if ud['logins'][i] == nickname and ud['passwords'][i] == cur_pass: ok = True; break
                    if ok:
                        if update_player_password(nickname, new_pass):
                            pass_msg = 'Пароль успешно сменён'; pass_msg_col = theme['win']; pass_msg_timer = 180
                            cur_pass = new_pass = conf_pass = ''
                    else: pass_msg = 'Неверно введён старый пароль'; pass_msg_col = ER; pass_msg_timer = 180
            
            if apply_btn.is_clicked(mp, True):
                update_settings(music=current_vm, sound=current_vs, theme=current_theme, 
                            effect=current_eff, music_pack=current_music_pack)
                
                orig_theme = current_theme
                orig_eff = current_eff
                orig_music_pack = current_music_pack
                orig_vm = current_vm
                orig_vs = current_vs
                
                if place == "game":
                    music_manager.load_music('game', current_vm, force=True)
                
                if place == "menu":
                    menu.menu(nickname, 1)
                elif place == "admin_panel":
                    admin_panel.admin_panel(nickname, 1)
                elif place == "menu_game":
                    menu_game.menu_game(nickname)
                elif place == "game":
                    sd = load_game_state(nickname)
                    if sd:
                        game.game(nickname, sd['difficulty'], sd['game_type'], None, None, None, load_saved=True, saved_data=sd)
                    else:
                        menu_game.menu_game(nickname)
            
            if reset_btn.is_clicked(mp, True):
                from settings_manager import DEFAULT_SETTINGS
                reset_settings()
                
                current_vm = DEFAULT_SETTINGS['music']
                current_vs = DEFAULT_SETTINGS['sound']
                current_theme = DEFAULT_SETTINGS['theme']
                current_eff = DEFAULT_SETTINGS['effect']
                current_music_pack = DEFAULT_SETTINGS['music_pack']
                
                orig_theme = current_theme
                orig_eff = current_eff
                orig_music_pack = current_music_pack
                orig_vm = current_vm
                orig_vs = current_vs
                
                set_theme(current_theme)
                pygame.mixer.music.set_volume(current_vm)
                click_channel.set_volume(current_vs)
                
                sliders['music'].value = current_vm
                sliders['sound'].value = current_vs
                theme_car.current_index = av_themes.index(current_theme) if current_theme in av_themes else 0
                eff_car.current_index = av_effects.index(current_eff) if current_eff in av_effects else 0
                music_pack_car.current_index = av_music_packs.index(current_music_pack) if current_music_pack in av_music_packs else 0
                
                settings_manager.update_settings(music_pack=current_music_pack)
                music_manager.load_music('menu.mp3', current_vm)
                update_click_sound()
                
                is_full = DEFAULT_SETTINGS['is_fullscreen']
                ww = DEFAULT_SETTINGS['width']; wh = DEFAULT_SETTINGS['height']
                if is_full: screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else: screen = pygame.display.set_mode((ww, wh), pygame.RESIZABLE)
                wsz = (ww, wh) if not is_full else (1366, 768)
                update_settings(music=current_vm, sound=current_vs, theme=current_theme, 
                              is_fullscreen=is_full, width=ww, height=wh, effect=current_eff, 
                              music_pack=current_music_pack)
            
            if cancel_btn.is_clicked(mp, True):
                current_theme = orig_theme
                current_eff = orig_eff
                current_music_pack = orig_music_pack
                current_vm = orig_vm
                current_vs = orig_vs
                
                set_theme(current_theme)
                pygame.mixer.music.set_volume(current_vm)
                click_channel.set_volume(current_vs)
                
                sliders['music'].value = current_vm
                sliders['sound'].value = current_vs
                theme_car.current_index = av_themes.index(current_theme) if current_theme in av_themes else 0
                eff_car.current_index = av_effects.index(current_eff) if current_eff in av_effects else 0
                music_pack_car.current_index = av_music_packs.index(current_music_pack) if current_music_pack in av_music_packs else 0
                
                settings_manager.update_settings(music_pack=current_music_pack)
                music_manager.load_music('menu.mp3', current_vm)
                update_click_sound()
                update_settings(effect=current_eff)
                
                if place == "game":
                    music_manager.load_music('game', current_vm, force=True)
                
                if place == "menu":
                    menu.menu(nickname, 1)
                elif place == "admin_panel":
                    admin_panel.admin_panel(nickname, 1)
                elif place == "menu_game":
                    menu_game.menu_game(nickname)
                elif place == "game":
                    sd = load_game_state(nickname)
                    if sd:
                        game.game(nickname, sd['difficulty'], sd['game_type'], None, None, None, load_saved=True, saved_data=sd)
                    else:
                        menu_game.menu_game(nickname)
        
        for y in range(ch2):
            r = int(theme['background'][0] - y/ch2*15)
            g = int(theme['background'][1] - y/ch2*15)
            b = int(theme['background'][2] - y/ch2*15)
            pygame.draw.line(screen, (max(0,r), max(0,g), max(0,b)), (0,y), (cw,y))
        
        fr = pygame.Rect(20, 20, cw-40, ch2-40)
        pygame.draw.rect(screen, A, fr, 2, border_radius=12)
        
        tt = title_font.render('НАСТРОЙКИ', True, A)
        screen.blit(tt, (cx - tt.get_width()//2, ty))
        
        screen.blit(subtitle_font.render('Музыка', True, TS), (sl_x, music_y-20))
        mv = button_font.render(f'{int(current_vm*100)}%', True, TP)
        screen.blit(mv, (sl_x+sl_w-mv.get_width(), music_y-20))
        sliders['music'].draw(screen, A)
        
        screen.blit(subtitle_font.render('Звуковые эффекты', True, TS), (sl_x, sound_y-20))
        sv = button_font.render(f'{int(current_vs*100)}%', True, TP)
        screen.blit(sv, (sl_x+sl_w-sv.get_width(), sound_y-20))
        sliders['sound'].draw(screen, A)
        
        screen.blit(subtitle_font.render('Тема интерфейса', True, TS), (cx - subtitle_font.size('Тема интерфейса')[0]//2, theme_y-20))
        th_left_btn.draw(screen); th_right_btn.draw(screen)
        theme_car.draw(screen, theme)
        
        screen.blit(subtitle_font.render('Эффекты', True, TS), (cx - subtitle_font.size('Эффекты')[0]//2, eff_y-20))
        eff_left_btn.draw(screen); eff_right_btn.draw(screen)
        eff_car.draw(screen, theme)
        
        screen.blit(subtitle_font.render('Музыкальный пак', True, TS), (cx - subtitle_font.size('Музыкальный пак')[0]//2, music_pack_y-20))
        music_pack_left_btn.draw(screen); music_pack_right_btn.draw(screen)
        music_pack_car.draw(screen, theme)
        
        screen.blit(subtitle_font.render('Изменение пароля', True, TS), (cx - subtitle_font.size('Изменение пароля')[0]//2, pass_y-20))
        ff = pygame.font.Font('font/font.otf', 16)
        
        for lbl, rx, val in [('Текущий', pf_sx, '*'*len(cur_pass)),
                              ('Новый', pf_sx+pf_w+20, '*'*len(new_pass)),
                              ('Повтор', pf_sx+(pf_w+20)*2, '*'*len(conf_pass))]:
            screen.blit(small_font.render(lbl, True, TS), (rx, pass_y+10))
            rct = pygame.Rect(rx, pass_y+30, pf_w, pf_h)
            pygame.draw.rect(screen, IB, rct, border_radius=8)
            pygame.draw.rect(screen, BR, rct, 2, border_radius=8)
            vs2 = ff.render(val, True, TP)
            screen.blit(vs2, (rx+10, pass_y+30+(pf_h-vs2.get_height())//2))
        
        change_pass_btn.draw(screen)
        
        if pass_msg and pass_msg_timer > 0:
            ms = small_font.render(pass_msg, True, pass_msg_col)
            screen.blit(ms, (cx - ms.get_width()//2, pass_y+75))
        
        apply_btn.draw(screen); reset_btn.draw(screen); cancel_btn.draw(screen)
        
        effect_manager.draw(screen, current_width, current_height)

        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()