import pygame
import math

class Notification:
    def __init__(self, title, text, notification_type="achievement"):
        self.title = title
        self.text = text
        self.type = notification_type
        self.alpha = 0
        self.y_offset = -100
        self.state = "appearing"
        self.timer = 0
        self.appear_duration = 0.5
        self.show_duration = 5.0
        self.disappear_duration = 0.5
        
    def update(self, dt, skipped=False):
        if self.state == "appearing":
            self.timer += dt
            progress = min(1.0, self.timer / self.appear_duration)
            self.alpha = int(255 * progress)
            self.y_offset = int(-100 + 100 * progress)
            if progress >= 1.0:
                self.state = "showing"
                self.timer = 0
                
        elif self.state == "showing":
            if skipped:
                self.state = "disappearing"
                self.timer = 0
            else:
                self.timer += dt
                if self.timer >= self.show_duration:
                    self.state = "disappearing"
                    self.timer = 0
                    
        elif self.state == "disappearing":
            self.timer += dt
            progress = min(1.0, self.timer / self.disappear_duration)
            self.alpha = int(255 * (1.0 - progress))
            self.y_offset = int(-100 * progress)
            if progress >= 1.0:
                self.state = "done"
                
        return self.state == "done"
    
    def draw(self, screen, width, theme):
        if self.alpha <= 0:
            return
            
        accent = theme['accent']
        card = theme['card']
        text_color = theme['text']
        
        notif_width = int(width * 0.5)
        notif_height = 80
        notif_x = width // 2 - notif_width // 2
        notif_y = 20 + self.y_offset
        
        shadow_surf = pygame.Surface((notif_width, notif_height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, self.alpha // 3), (0, 0, notif_width, notif_height), border_radius=15)
        screen.blit(shadow_surf, (notif_x + 2, notif_y + 2))
        
        bg_surf = pygame.Surface((notif_width, notif_height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (*card, self.alpha), (0, 0, notif_width, notif_height), border_radius=15)
        pygame.draw.rect(bg_surf, (*accent, self.alpha), (0, 0, notif_width, notif_height), 2, border_radius=15)
        screen.blit(bg_surf, (notif_x, notif_y))
        
        font_title = pygame.font.Font('font/font.otf', 22)
        title_surf = font_title.render(self.title, True, accent)
        title_surf.set_alpha(self.alpha)
        screen.blit(title_surf, (notif_x + 20, notif_y + 10))
        
        font_text = pygame.font.Font('font/font.otf', 18)
        text_surf = font_text.render(self.text, True, text_color)
        text_surf.set_alpha(self.alpha)
        screen.blit(text_surf, (notif_x + 20, notif_y + 45))


class NotificationManager:
    def __init__(self, music_manager=None, sound_volume=0.5):
        self.queue = []
        self.current_notification = None
        self.music_manager = music_manager
        self.sound_volume = sound_volume
        self.notification_sound = None
        self.notification_channel = None
        self._load_sound()
        
    def _load_sound(self):
        try:
            if self.music_manager:
                self.notification_sound = self.music_manager.load_sound('notification.mp3')
            else:
                self.notification_sound = pygame.mixer.Sound("sounds/classic/notification.mp3")
            
            self.notification_channel = pygame.mixer.Channel(6) 
            if self.notification_channel:
                self.notification_channel.set_volume(self.sound_volume)
        except Exception as e:
            print(f"ERROR loading notification sound: {e}")
            self.notification_sound = None
            self.notification_channel = None
    
    def update_volume(self, volume):
        self.sound_volume = volume
        if self.notification_channel:
            self.notification_channel.set_volume(volume)
        
    def add_notification(self, title, text, notification_type="achievement"):
        self.queue.append(Notification(title, text, notification_type))
        
    def update(self, dt, skip_current=False):
        if self.current_notification is None and self.queue:
            self.current_notification = self.queue.pop(0)
            if self.notification_sound and self.notification_channel:
                try:
                    self.notification_channel.stop()
                    self.notification_channel.play(self.notification_sound)
                except:
                    pass
                
        if self.current_notification:
            done = self.current_notification.update(dt, skip_current)
            if done:
                self.current_notification = None
                        
    def draw(self, screen, width, theme):
        if self.current_notification:
            self.current_notification.draw(screen, width, theme)
            
    def has_active(self):
        return self.current_notification is not None or len(self.queue) > 0
    
    def skip_current(self):
        return self.current_notification is not None and self.current_notification.state == "showing"