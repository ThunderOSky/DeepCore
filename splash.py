import pygame
import random
import math
from theme import *
from settings_manager import get_music
from music_manager import get_music_manager

def safe_color(c, alpha=255):
    try:
        r = max(0, min(255, int(c[0])))
        g = max(0, min(255, int(c[1])))
        b = max(0, min(255, int(c[2])))
        a = max(0, min(255, int(alpha)))
        return (r, g, b, a)
    except:
        return (128, 128, 128, 255)

class SplashScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.state = "dark"
        self.timer = 0
        self.done = False
        
        self.dark_alpha = 255
        self.field_bg_alpha = 0
        self.field_border_alpha = 0
        self.title_alpha = 0
        self.glow_alpha = 0
        
        self.field_scale = 1.0
        
        self.reveal_duration = 2.0
        self.show_duration = 3.0
        self.fade_duration = 1.5
        
        self.cell_appear_time = {}
        self.cell_appear_duration = 0.6
        self.cells_start_time = 0
        
        self.particles = []
        for _ in range(80):
            self.particles.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(2, 7),
                'speed_y': random.uniform(0.4, 1.0),
                'speed_x': random.uniform(-0.3, 0.3),
                'alpha': random.randint(20, 70),
                'phase': random.uniform(0, math.pi * 2),
                'color_shift': random.uniform(0, 1)
            })
        
        rows, cols = 8, 8
        self.rows = rows
        self.cols = cols
        self.field = [[0]*cols for _ in range(rows)]
        mines = set()
        while len(mines) < 10:
            mines.add((random.randint(0, rows-1), random.randint(0, cols-1)))
        for r, c in mines:
            self.field[r][c] = -1
        for r in range(rows):
            for c in range(cols):
                if self.field[r][c] == -1: continue
                cnt = 0
                for dr in [-1,0,1]:
                    for dc in [-1,0,1]:
                        nr, nc = r+dr, c+dc
                        if 0<=nr<rows and 0<=nc<cols and self.field[nr][nc]==-1:
                            cnt += 1
                self.field[r][c] = cnt
        
        self.cell_order = []
        for diag in range(rows + cols - 1):
            for r in range(max(0, diag - cols + 1), min(rows, diag + 1)):
                c = diag - r
                self.cell_order.append((r, c))
        
        total_cells = rows * cols
        for i, (r, c) in enumerate(self.cell_order):
            delay = i / total_cells * 1.2
            self.cell_appear_time[(r, c)] = delay
        
        self.title_font = pygame.font.Font('font/font.otf', 90)
        self.subtitle_font = pygame.font.Font('font/font.otf', 22)
        
        try:
            music_volume = get_music()
            music_manager = get_music_manager()
            music_manager.load_music('start.mp3', music_volume)
        except:
            pass
    
    def update(self, dt):
        self.timer += dt
        
        for p in self.particles:
            p['y'] -= p['speed_y']
            p['x'] += p['speed_x']
            p['phase'] += dt * 1.5
            if p['y'] < -30:
                p['y'] = self.height + 30
                p['x'] = random.randint(0, self.width)
        
        if self.state == "dark":
            self.dark_alpha = 255
            if self.timer > 0.2:
                self.state = "revealing"
                self.timer = 0
                self.cells_start_time = 0
        
        elif self.state == "revealing":
            progress = min(1.0, self.timer / self.reveal_duration)
            self.cells_start_time = self.timer
            
            theme = get_current_theme()
            is_light = theme['background'][0] > 150
            if is_light:
                self.dark_alpha = int(255 * (1.0 - self._ease_out(progress) * 0.85))
            else:
                self.dark_alpha = int(255 * (1.0 - self._ease_out(progress) * 0.75))
            
            self.field_bg_alpha = int(255 * self._ease_out(min(1.0, progress * 2)))
            self.field_border_alpha = int(255 * self._ease_out(min(1.0, progress * 1.5)))
            
            if progress < 0.6:
                self.field_scale = 0.85 + 0.25 * self._ease_out(progress / 0.6)
            else:
                overshoot = (progress - 0.6) / 0.4
                self.field_scale = 1.1 - 0.1 * self._ease_out(overshoot)
            
            if progress >= 1.0:
                self.state = "showing"
                self.timer = 0
                self.field_scale = 1.0
        
        elif self.state == "showing":
            theme = get_current_theme()
            is_light = theme['background'][0] > 150
            self.dark_alpha = 80 if is_light else 60
            self.field_bg_alpha = 255
            self.field_border_alpha = 255
            self.field_scale = 1.0 + 0.005 * math.sin(self.timer * 2.5)
            self.glow_alpha = int(50 + 25 * math.sin(self.timer * 1.8))
            
            if self.timer > 0.5:
                tp = min(1.0, (self.timer - 0.5) / 1.2)
                self.title_alpha = int(255 * self._ease_out(tp))
            
            if self.timer >= self.show_duration:
                self.state = "fading"
                self.timer = 0
        
        elif self.state == "fading":
            progress = min(1.0, self.timer / self.fade_duration)
            theme = get_current_theme()
            is_light = theme['background'][0] > 150
            if is_light:
                self.dark_alpha = int(80 + 175 * self._ease_in(progress))
            else:
                self.dark_alpha = int(60 + 195 * self._ease_in(progress))
            self.field_bg_alpha = int(255 * (1.0 - self._ease_in(progress)))
            self.field_border_alpha = int(255 * (1.0 - self._ease_in(progress)))
            self.title_alpha = max(0, int(255 * (1.0 - self._ease_in(progress * 1.5))))
            self.glow_alpha = max(0, self.glow_alpha - int(80 * dt))
            
            if progress >= 1.0:
                self.done = True
    
    def _ease_out(self, t):
        return 1 - (1 - t) ** 4
    
    def _ease_in(self, t):
        return t ** 3
    
    def _get_cell_alpha(self, row, col):
        if self.state == "dark":
            return 0
        if self.state == "fading":
            return self.field_bg_alpha
        
        cell_start = self.cell_appear_time.get((row, col), 0)
        if self.cells_start_time < cell_start:
            return 0
        
        cell_progress = min(1.0, (self.cells_start_time - cell_start) / self.cell_appear_duration)
        
        if cell_progress < 0.7:
            return int(255 * self._ease_out(cell_progress / 0.7))
        else:
            overshoot = (cell_progress - 0.7) / 0.3
            scale = 1.0 + 0.15 * (1 - overshoot)
            return int(255 * scale)
    
    def draw(self):
        theme = get_current_theme()
        accent = safe_color(theme['accent'], 255)
        bg_color = safe_color(theme['background'], 255)
        is_light = theme['background'][0] > 150
        
        if is_light:
            self.screen.fill((bg_color[0]//3, bg_color[1]//3, bg_color[2]//3))
        else:
            self.screen.fill((5, 5, 8))
        
        if self.field_bg_alpha > 20:
            for p in self.particles:
                a = int((30 + 40 * math.sin(p['phase'])) * (self.field_bg_alpha / 255))
                a = max(5, min(150, a))
                
                shift = p['color_shift']
                glow_col = (
                    min(255, accent[0] + int(40 * shift)),
                    min(255, accent[1] + int(30 * shift)),
                    min(255, accent[2] + int(20 * shift)),
                    a
                )
                
                s = pygame.Surface((p['size']*5, p['size']*5), pygame.SRCALPHA)
                for r in range(p['size']*2, 0, -3):
                    alpha = int(a * (1 - r/(p['size']*2)) * 0.6)
                    if alpha > 0:
                        pygame.draw.circle(s, (glow_col[0], glow_col[1], glow_col[2], alpha), 
                                         (p['size']*5//2, p['size']*5//2), r)
                self.screen.blit(s, (int(p['x']-p['size']*2.5), int(p['y']-p['size']*2.5)))
        
        rows, cols = self.rows, self.cols
        base_cell = 58
        cell_size = int(base_cell * self.field_scale)
        if cell_size < 5:
            cell_size = 5
        fw = cols * cell_size
        fh = rows * cell_size
        fx = self.width // 2 - fw // 2
        fy = self.height // 2 - fh // 2 - 35
        
        if self.field_bg_alpha > 5:
            frame = pygame.Rect(fx - 8, fy - 8, fw + 16, fh + 16)
            border_color = safe_color(theme['accent'], self.field_border_alpha)
            pygame.draw.rect(self.screen, border_color, frame, 2, border_radius=10)
            
            for r in range(rows):
                for c in range(cols):
                    cell_alpha = self._get_cell_alpha(r, c)
                    if cell_alpha < 5:
                        continue
                    
                    x = fx + c * cell_size
                    y = fy + r * cell_size
                    
                    cell_progress = 0
                    if self.state == "revealing":
                        cell_start = self.cell_appear_time.get((r, c), 0)
                        if self.cells_start_time > cell_start:
                            cell_progress = min(1.0, (self.cells_start_time - cell_start) / self.cell_appear_duration)
                    
                    offset_y = 0
                    if cell_progress > 0.7:
                        overshoot = (cell_progress - 0.7) / 0.3
                        offset_y = int((1 - overshoot) * 8 * math.sin(overshoot * math.pi))
                    
                    cw = max(1, cell_size - 2)
                    ch = max(1, cell_size - 2)
                    cx = x + 1
                    cy = y + 1 + offset_y
                    
                    cell_surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
                    bg = safe_color(theme['card'], cell_alpha)
                    pygame.draw.rect(cell_surf, bg, (0, 0, cw, ch), border_radius=4)
                    self.screen.blit(cell_surf, (cx, cy))
                    
                    brd = safe_color(theme['border'], cell_alpha)
                    pygame.draw.rect(self.screen, brd, (cx, cy, cw, ch), 1, border_radius=4)
                    
                    value = self.field[r][c]
                    if value == -1:
                        r2 = max(1, int(cell_size * 0.25))
                        mc = safe_color(theme['mine'], cell_alpha)
                        pygame.draw.circle(self.screen, mc,
                                         (x + cell_size//2, y + cell_size//2 + offset_y), r2)
                    elif value > 0:
                        fs = max(10, int(cell_size * 0.5))
                        nf = pygame.font.Font('font/font.otf', fs)
                        num_color = NUMBER_COLORS[value] if value < len(NUMBER_COLORS) else (255, 255, 255)
                        ns = nf.render(str(value), True, num_color)
                        ns.set_alpha(cell_alpha)
                        nr = ns.get_rect(center=(x + cell_size//2, y + cell_size//2 + offset_y))
                        self.screen.blit(ns, nr)
        
        if self.title_alpha > 10:
            if self.glow_alpha > 0:
                glow_surf = pygame.Surface((self.width, 150), pygame.SRCALPHA)
                for i in range(3):
                    a = self.glow_alpha // (i + 2)
                    gc = safe_color(theme['accent'], a)
                    pygame.draw.rect(glow_surf, gc, (i*10, i*10, self.width - i*20, 150 - i*20), border_radius=30)
                self.screen.blit(glow_surf, (0, fy + fh + 30))
            
            title = self.title_font.render('DEEPCORE', True, accent[:3])
            title.set_alpha(self.title_alpha)
            tr = title.get_rect(center=(self.width//2, fy + fh + 90))
            self.screen.blit(title, tr)
            
            ver = self.subtitle_font.render('v0.4.3.1', True, safe_color(theme['text'], 255)[:3])
            ver.set_alpha(self.title_alpha)
            vr = ver.get_rect(center=(self.width//2, fy + fh + 145))
            self.screen.blit(ver, vr)
        
        if self.dark_alpha > 0:
            dark = pygame.Surface((self.width, self.height))
            if is_light:
                dark.fill((bg_color[0]//3, bg_color[1]//3, bg_color[2]//3))
            else:
                dark.fill((5, 5, 8))
            dark.set_alpha(self.dark_alpha)
            self.screen.blit(dark, (0, 0))
    
    def is_done(self):
        return self.done