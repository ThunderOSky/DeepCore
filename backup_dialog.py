import pygame
import sys
import math
from theme import *
import admin_panel
from ui import AnimatedButton
from db_manager import backup_database, get_last_backup_info, save_backup_settings, get_backup_interval
from effects import EffectManager
from settings_manager import get_effect, get_sound

class BackupCarousel:
    def __init__(self, x, y, width, height, items, current_item):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.items = items
        self.current_index = items.index(current_item) if current_item in items else 0
        self.glow_phase = 0
    
    def next_item(self):
        self.current_index = (self.current_index + 1) % len(self.items)
        return self.items[self.current_index]
    
    def prev_item(self):
        self.current_index = (self.current_index - 1) % len(self.items)
        return self.items[self.current_index]
    
    def get_current_value(self):
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
        if item == 0:
            name = "Выкл"
        elif item == 1:
            name = "1 день"
        elif item == 3:
            name = "3 дня"
        elif item == 5:
            name = "5 дней"
        elif item == 7:
            name = "7 дней"
        elif item == 15:
            name = "15 дней"
        elif item == 30:
            name = "30 дней"
        else:
            name = f"{item} дней"
        
        fs = min(24, self.height // 3)
        tf = pygame.font.Font('font/font.otf', fs)
        ts = tf.render(name, True, theme_colors['text'])
        screen.blit(ts, (self.x + (self.width - ts.get_width())//2, self.y + (self.height - ts.get_height())//2))

def show_backup_dialog(screen, nickname):
    from music_manager import get_music_manager
    
    volume_sound = get_sound()
    music_manager = get_music_manager()
    click = music_manager.load_sound('click.mp3')
    channel_click = pygame.mixer.Channel(0)
    channel_click.set_volume(volume_sound)
    
    effect_manager = EffectManager()
    current_effect = get_effect()
    tw, th = screen.get_size()
    effect_manager.set_effect(current_effect, tw, th)
    
    clock = pygame.time.Clock()

    last_backup, _ = get_last_backup_info()
    current_interval = get_backup_interval()

    intervals = [0, 1, 3, 5, 7, 15, 30]
    carousel = BackupCarousel(0, 0, 250, 40, intervals, current_interval)
    
    save_btn = None
    backup_now_btn = None
    cancel_btn = None
    left_btn = None
    right_btn = None
    
    message = ""
    message_timer = 0
    
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
        
        if message_timer > 0:
            message_timer -= dt
        
        theme = get_current_theme()
        A = theme['accent']
        AH = theme['accent_hover']
        CC = theme['card']
        TP = theme['text']
        TS = theme['text_secondary']
        
        cx = current_width // 2
        cy = current_height // 2
        
        dialog_w = 500
        dialog_h = 350
        dialog_x = cx - dialog_w // 2
        dialog_y = cy - dialog_h // 2

        overlay = pygame.Surface((current_width, current_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, CC, (dialog_x, dialog_y, dialog_w, dialog_h), border_radius=20)
        pygame.draw.rect(screen, A, (dialog_x, dialog_y, dialog_w, dialog_h), 2, border_radius=20)

        title = title_font.render("Резервное копирование", True, A)
        screen.blit(title, (cx - title.get_width() // 2, dialog_y + 25))

        backup_text = small_font.render(f"Последнее резервное копирование: {last_backup}", True, TS)
        screen.blit(backup_text, (dialog_x + 30, dialog_y + 90))

        carousel.x = dialog_x + (dialog_w - 250) // 2
        carousel.y = dialog_y + 140
        carousel.update(dt)
        carousel.draw(screen, theme)

        if left_btn is None:
            left_btn = AnimatedButton(carousel.x - 35, carousel.y + carousel.height//2 - 15, 30, 30, '<', button_font, A, TP, AH, border_radius=15)
            right_btn = AnimatedButton(carousel.x + carousel.width + 5, carousel.y + carousel.height//2 - 15, 30, 30, '>', button_font, A, TP, AH, border_radius=15)
        else:
            left_btn.set_position(carousel.x - 35, carousel.y + carousel.height//2 - 15)
            right_btn.set_position(carousel.x + carousel.width + 5, carousel.y + carousel.height//2 - 15)
        
        left_btn.update(dt, mouse_pos, mouse_pressed)
        right_btn.update(dt, mouse_pos, mouse_pressed)
        left_btn.draw(screen)
        right_btn.draw(screen)

        freq_text = small_font.render("Частота автоматического создания резервных копий", True, TS)
        screen.blit(freq_text, (cx - freq_text.get_width() // 2, carousel.y + carousel.height + 10))

        btn_w = 140
        btn_h = 40
        btn_spacing = 15
        total_w = btn_w * 3 + btn_spacing * 2
        btn_start_x = cx - total_w // 2
        btn_y = dialog_y + dialog_h - 60
        
        if save_btn is None:
            save_btn = AnimatedButton(btn_start_x, btn_y, btn_w, btn_h, 'СОХРАНИТЬ', button_font, A, CC, AH)
            backup_now_btn = AnimatedButton(btn_start_x + btn_w + btn_spacing, btn_y, btn_w, btn_h, 'СОЗДАТЬ КОПИЮ', button_font, theme['win'], CC)
            cancel_btn = AnimatedButton(btn_start_x + (btn_w + btn_spacing) * 2, btn_y, btn_w, btn_h, 'ОТМЕНА', button_font, theme['error'], CC)
        else:
            save_btn.set_position(btn_start_x, btn_y)
            backup_now_btn.set_position(btn_start_x + btn_w + btn_spacing, btn_y)
            cancel_btn.set_position(btn_start_x + (btn_w + btn_spacing) * 2, btn_y)
        
        save_btn.update(dt, mouse_pos, mouse_pressed)
        backup_now_btn.update(dt, mouse_pos, mouse_pressed)
        cancel_btn.update(dt, mouse_pos, mouse_pressed)
        
        save_btn.draw(screen)
        backup_now_btn.draw(screen)
        cancel_btn.draw(screen)

        if message and message_timer > 0:
            msg_surf = small_font.render(message, True, theme['win'] if "успешно" in message else theme['error'])
            screen.blit(msg_surf, (cx - msg_surf.get_width() // 2, btn_y - 30))

        if mouse_released and not ignore_clicks:
            if left_btn.is_clicked(mouse_pos, True):
                carousel.prev_item()
            elif right_btn.is_clicked(mouse_pos, True):
                carousel.next_item()
            elif save_btn.is_clicked(mouse_pos, True):
                new_interval = carousel.get_current_value()
                save_backup_settings(new_interval)
                message = "Настройки сохранены!"
                message_timer = 180
            elif backup_now_btn.is_clicked(mouse_pos, True):
                success, path = backup_database()
                if success:
                    message = f"Резервная копия создана успешно!"
                    last_backup, _ = get_last_backup_info()
                else:
                    message = "Ошибка при создании резервной копии!"
                message_timer = 180
            elif cancel_btn.is_clicked(mouse_pos, True):
                running = False
                admin_panel.admin_panel(nickname, 1)
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                channel_click.play(click)
        
        effect_manager.draw(screen, current_width, current_height)
        
        pygame.display.update()
        clock.tick(60)