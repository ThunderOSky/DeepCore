import pygame
import math
import random

class AnimatedButton:
    def __init__(self, x, y, width, height, text, font, base_color, text_color, 
                 hover_color=None, border_radius=12, animation_speed=12.0):
        self.rect = pygame.Rect(x, y, width, height)
        self.original_rect = self.rect.copy()
        self.text = text
        self.font = font
        self.base_color = base_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.animation_speed = animation_speed
        
        if hover_color is None:
            is_dark = sum(base_color) < 380
            if is_dark:
                self.hover_color = tuple(min(255, c + 50) for c in base_color)
            else:
                self.hover_color = tuple(max(0, c - 50) for c in base_color)
        else:
            self.hover_color = hover_color
        
        self.hover_progress = 0.0
        self.press_progress = 0.0
        self.scale = 1.0
        
        self.float_offset_y = 0.0
        self.float_phase = random.uniform(0, math.pi * 2)
        
        self.alpha = 255
        self.was_hovered = False
        
    def is_released(self, mouse_pos, mouse_released):
        if not mouse_released:
            return False
        return self.rect.collidepoint(mouse_pos)

    def update(self, dt, mouse_pos, mouse_pressed=False):
        hovered = self.rect.collidepoint(mouse_pos)
        
        if hovered:
            self.hover_progress = min(1.0, self.hover_progress + dt * self.animation_speed)
        else:
            self.hover_progress = max(0.0, self.hover_progress - dt * self.animation_speed)
        
        if hovered and mouse_pressed:
            self.press_progress = min(1.0, self.press_progress + dt * self.animation_speed * 2)
        else:
            self.press_progress = max(0.0, self.press_progress - dt * self.animation_speed * 3)
        
        if hovered and mouse_pressed:
            target_scale = 0.94
        elif hovered:
            target_scale = 1.04
        else:
            target_scale = 1.0
        self.scale += (target_scale - self.scale) * min(1.0, dt * 10)
        
        if hovered and not mouse_pressed:
            self.float_phase += dt * 5.0
            self.float_offset_y = math.sin(self.float_phase) * 1.5
        else:
            self.float_offset_y *= 0.85
        
        scaled_w = int(self.original_rect.width * self.scale)
        scaled_h = int(self.original_rect.height * self.scale)
        self.rect.width = scaled_w
        self.rect.height = scaled_h
        self.rect.center = (self.original_rect.centerx, 
                           self.original_rect.centery + self.float_offset_y)
    
    def draw(self, screen):
        current_color = self._lerp_color(self.base_color, self.hover_color, self.hover_progress)
        if self.press_progress > 0:
            current_color = self._lerp_color(current_color, self._darken(current_color, 0.8), self.press_progress)
        
        pygame.draw.rect(screen, current_color, self.rect, border_radius=self.border_radius)

        if self.hover_progress > 0.3:
            border_alpha = int(255 * self.hover_progress)
            from theme import get_current_theme
            theme = get_current_theme()
            if sum(theme['background']) < 200:  
                border_color = (0, 0, 0, border_alpha // 2)  
            else:  
                border_color = (255, 255, 255, border_alpha) 
            border_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, border_color, (0, 0, self.rect.width, self.rect.height), 
                        2, border_radius=self.border_radius)
            screen.blit(border_surf, (self.rect.x, self.rect.y))
        
        if self.hover_progress > 0.5:
            hover_text = (255, 255, 255) if sum(self.base_color) < 380 else (0, 0, 0)
            text_color = self._lerp_color(self.text_color, hover_text, (self.hover_progress - 0.5) * 2)
        else:
            text_color = self.text_color
        
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def draw_on(self, target_surface):
        if self.alpha < 10:
            return
        
        current_color = self._lerp_color(self.base_color, self.hover_color, self.hover_progress)
        if self.press_progress > 0:
            current_color = self._lerp_color(current_color, self._darken(current_color, 0.8), self.press_progress)
        
        pygame.draw.rect(target_surface, current_color, self.rect, border_radius=self.border_radius)
        
        if self.hover_progress > 0.3:
            border_alpha = int(255 * self.hover_progress)
            if sum(self.base_color) < 400:
                border_color = (0, 0, 0, border_alpha // 2)
            else:
                border_color = (255, 255, 255, border_alpha)
            border_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, border_color, (0, 0, self.rect.width, self.rect.height), 
                           2, border_radius=self.border_radius)
            target_surface.blit(border_surf, (self.rect.x, self.rect.y))
        
        if self.hover_progress > 0.5:
            hover_text = (255, 255, 255) if sum(self.base_color) < 380 else (0, 0, 0)
            text_color = self._lerp_color(self.text_color, hover_text, (self.hover_progress - 0.5) * 2)
        else:
            text_color = self.text_color
        
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        target_surface.blit(text_surf, text_rect)
    
    def is_clicked(self, mouse_pos, mouse_clicked):
        if not mouse_clicked:
            return False
        return self.rect.collidepoint(mouse_pos)
    
    def set_position(self, x, y):
        self.original_rect.x = x
        self.original_rect.y = y
        self.rect.center = self.original_rect.center
    
    def _lerp_color(self, c1, c2, t):
        t = max(0, min(1, t))
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    
    def _darken(self, color, factor):
        return tuple(max(0, int(c * factor)) for c in color)


class AnimatedInput:
    def __init__(self, x, y, width, height, font, base_color, text_color, 
                 border_color, active_border_color, border_radius=10):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.base_color = base_color
        self.text_color = text_color
        self.border_color = border_color
        self.active_border_color = active_border_color
        self.border_radius = border_radius
        self.text = ''
        self.active = False
        self.anim_progress = 0.0
        self.cursor_visible = True
        self.cursor_timer = 0
        
    def update(self, dt):
        target = 1.0 if self.active else 0.0
        self.anim_progress += (target - self.anim_progress) * min(1.0, dt * 10)
        self.cursor_timer += dt
        if self.cursor_timer > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, screen):
        current_border = self._lerp_color(self.border_color, self.active_border_color, self.anim_progress)
        pygame.draw.rect(screen, self.base_color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(screen, current_border, self.rect, 2, border_radius=self.border_radius)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_y = self.rect.centery - text_surf.get_height() // 2
        screen.blit(text_surf, (self.rect.x + 12, text_y))
        
        if self.active and self.cursor_visible:
            cursor_x = self.rect.x + 12 + text_surf.get_width() + 2
            pygame.draw.line(screen, self.text_color, 
                           (cursor_x, self.rect.y + 10),
                           (cursor_x, self.rect.y + self.rect.height - 10), 2)
    
    def _lerp_color(self, c1, c2, t):
        t = max(0, min(1, t))
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    
