import pygame
import random
import time
import sys
import math
import menu, menu_game, settings
from theme import *
from db_manager import *
from settings_manager import *
from effects import EffectManager
from settings_manager import get_effect
from notification_queue import add_pending
from ui import AnimatedButton
from effects import *

class RainEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.droplets = []
        self.ripples = []
        self.create_droplets()
    
    def create_droplets(self):
        self.droplets = []
        for i in range(100):
            self.droplets.append({
                'x': random.randint(0, self.width),
                'y': random.randint(-self.height, 0),
                'speed': random.uniform(3, 7),
                'length': random.randint(15, 30),
                'alpha': random.randint(80, 150),
                'phase': random.uniform(0, math.pi * 2)
            })
    
    def update(self, width, height):
        self.width = width
        self.height = height
        
        for d in self.droplets:
            d['y'] += d['speed']
            d['phase'] += 0.05
            d['alpha'] = 100 + int(math.sin(d['phase']) * 50)
            
            if d['y'] > self.height:
                d['y'] = -random.randint(10, 50)
                d['x'] = random.randint(0, self.width)
                if random.random() < 0.2:
                    self.ripples.append({
                        'x': d['x'],
                        'y': self.height - random.randint(0, 30),
                        'radius': 5,
                        'alpha': 80,
                        'phase': 0
                    })
        
        for r in self.ripples[:]:
            r['radius'] += 2
            r['alpha'] -= 5
            r['phase'] += 0.1
            if r['alpha'] <= 0 or r['radius'] > 70:
                self.ripples.remove(r)

    def draw(self, screen, accent_color, is_dark_theme):
        theme = get_current_theme()
        bg_color = theme['background']
        
        for y in range(self.height):
            ratio = y / self.height
            r = int(bg_color[0] - ratio * 15)
            g = int(bg_color[1] - ratio * 12)
            b = int(bg_color[2] - ratio * 18)
            pygame.draw.line(screen, (max(0, r), max(0, g), max(0, b)), (0, y), (self.width, y))
        
        for d in self.droplets:
            if is_dark_theme:
                color = (*accent_color, min(180, d['alpha']))
            else:
                dark_accent = (max(0, accent_color[0] - 80), max(0, accent_color[1] - 80), max(0, accent_color[2] - 80))
                color = (*dark_accent, min(150, d['alpha']))
            
            temp_surf = pygame.Surface((4, d['length'] + 4), pygame.SRCALPHA)
            for i in range(d['length']):
                alpha = int(d['alpha'] * (1 - i / d['length']))
                if is_dark_theme:
                    line_color = (*accent_color, alpha)
                else:
                    line_color = (*dark_accent, alpha)
                pygame.draw.line(temp_surf, line_color, (2, i), (2, i + 1))
            screen.blit(temp_surf, (d['x'] - 2, d['y']))
        
        for r in self.ripples:
            alpha = max(0, min(100, r['alpha']))
            temp_surf = pygame.Surface((r['radius'] * 2, r['radius'] * 2), pygame.SRCALPHA)
            for i in range(1, 4):
                rad = r['radius'] - i * 3
                if rad > 0:
                    alpha_layer = alpha // (i + 1)
                    if is_dark_theme:
                        ripple_color = (*accent_color, alpha_layer)
                    else:
                        ripple_color = (*dark_accent, alpha_layer)
                    pygame.draw.circle(temp_surf, ripple_color, (r['radius'], r['radius']), rad, 1)
            screen.blit(temp_surf, (r['x'] - r['radius'], r['y'] - r['radius']))
        
        fog = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        fog_color = (*bg_color, 40)
        fog.fill(fog_color)
        screen.blit(fog, (0, 0))


class Minesweeper:
    def __init__(self, rows, cols, mines, game_type='classic', difficulty='easy', seed=None):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.game_type = game_type
        self.difficulty = difficulty
        self.seed = seed
        self.reset()
        self.click_count = 0
        
    def reset(self):
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.revealed = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.flagged = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.game_over = False
        self.game_won = False
        self.first_click = True
        self.mines_left = self.mines
        self.start_time = 0
        self.elapsed_time = 0
        self.paused = False
        self.pause_time = 0
        self.total_pause_time = 0
        self._processing_adjacent = False
        self.win_delay_active = False
        self.win_delay_timer = 0
        self.time_out = False
        self._flags_to_transfer = {}
        
        if self.game_type == 'safari':
            self.last_move_time = 0
            self.move_interval = 30
            self.moving_mines = False
            self.move_direction = None
            self.move_progress = 0
            self.move_start_positions = []
            self.move_end_positions = []
            self.flash_alpha = 0
            self._mines_moved = False
            self._flagged_mines = {}

        if self.game_type == 'chronos':
            if self.difficulty == 'easy': self.time_limit = 35; self.time_penalty = 1
            elif self.difficulty == 'average': self.time_limit = 120; self.time_penalty = 2
            elif self.difficulty == 'hard': self.time_limit = 300; self.time_penalty = 5
            elif self.difficulty == 'super': self.time_limit = 600; self.time_penalty = 10
            else: self.time_limit = 180; self.time_penalty = 10
    
    def load_from_save(self, save_data):
        self.board = save_data['board']
        self.revealed = save_data['revealed']
        self.flagged = save_data['flagged']
        self.elapsed_time = save_data['elapsed_time']
        self.total_pause_time = save_data['total_pause_time']
        self.first_click = save_data['first_click']
        self.mines_left = save_data['mines_left']
        self.game_over = save_data.get('game_over', False)
        self.game_won = save_data.get('game_won', False)
        self.time_out = False
        if not self.first_click and not self.game_over:
            self.start_time = time.time() - self.elapsed_time
        else:
            self.start_time = 0
        if self.game_type == 'safari':
            self.last_move_time = save_data.get('last_move_time', 0)
            self.moving_mines = save_data.get('moving_mines', False)
            self.move_progress = save_data.get('move_progress', 0)
            self.move_start_positions = save_data.get('move_start_positions', [])
            self.move_end_positions = save_data.get('move_end_positions', [])
            self.flash_alpha = 0
            self._mines_moved = False
            self._flagged_mines = {}
        if self.game_type == 'chronos':
            self.time_limit = save_data.get('time_limit')
            self.time_penalty = save_data.get('time_penalty')
        if not self.game_over:
            self.check_win()
        return not self.game_over

    def place_mines(self, first_click_row, first_click_col):
        safe_zone = [(first_click_row + i, first_click_col + j) 
                    for i in [-1, 0, 1] for j in [-1, 0, 1]
                    if 0 <= first_click_row + i < self.rows and 0 <= first_click_col + j < self.cols]
        if self.seed: random.seed(self.seed)
        mines_placed = 0
        while mines_placed < self.mines:
            row = random.randint(0, self.rows - 1)
            col = random.randint(0, self.cols - 1)
            if (row, col) not in safe_zone and self.board[row][col] != -1:
                self.board[row][col] = -1
                mines_placed += 1
        if self.seed: random.seed()
        self.update_numbers()
        
    def update_numbers(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] != -1:
                    count = 0
                    for i in [-1, 0, 1]:
                        for j in [-1, 0, 1]:
                            if (i != 0 or j != 0) and 0 <= row + i < self.rows and 0 <= col + j < self.cols:
                                if self.board[row + i][col + j] == -1:
                                    count += 1
                    self.board[row][col] = count



    def move_mines_safari(self):
        if self.game_type != 'safari' or self.moving_mines:
            return False
        
        current_time = self.get_elapsed_time()
        if current_time - self.last_move_time < self.move_interval:
            return False
        
        self.moving_mines = True
        self.move_progress = 0
        self._mines_moved = False
        self.flash_alpha = 1.0
        
        mines = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.board[r][c] == -1]
        self.move_start_positions = []
        self.move_end_positions = []

        flags_on_mines = {}
        for (r, c) in mines:
            if self.flagged[r][c]:
                flags_on_mines[(r, c)] = True

        occupied = set()

        random.shuffle(mines)
        
        for (r, c) in mines:
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            
            moved = False
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.board[nr][nc] == -1:
                        continue
                    if (nr, nc) in occupied:
                        continue
                    
                    self.move_start_positions.append((r, c))
                    self.move_end_positions.append((nr, nc))
                    occupied.add((nr, nc))
                    moved = True
                    break
            
            if not moved:
                if (r, c) not in occupied:
                    self.move_start_positions.append((r, c))
                    self.move_end_positions.append((r, c))
                    occupied.add((r, c))

        self._flags_to_transfer = flags_on_mines
        
        self.last_move_time = self.get_elapsed_time()
        return True

    def update_mines_position(self, progress):
        if not self.moving_mines:
            return
        
        self.move_progress = progress
        
        if progress < 0.1:
            self.flash_alpha = 1.0
        elif progress < 0.8:
            self.flash_alpha = 1.0
            if progress >= 0.4 and not self._mines_moved:
                target_states = {}
                for (r, c) in self.move_end_positions:
                    target_states[(r, c)] = {
                        'revealed': self.revealed[r][c],
                        'flagged': self.flagged[r][c]
                    }
                
                for (r, c) in self.move_start_positions:
                    self.board[r][c] = 0

                for (r, c) in self.move_end_positions:
                    self.board[r][c] = -1

                for i in range(len(self.move_start_positions)):
                    old_r, old_c = self.move_start_positions[i]
                    new_r, new_c = self.move_end_positions[i]

                    if (old_r, old_c) != (new_r, new_c):
                        self.revealed[old_r][old_c] = target_states.get((new_r, new_c), {}).get('revealed', False)

                        if target_states.get((new_r, new_c), {}).get('flagged', False):
                            self.flagged[old_r][old_c] = True
                            self.flagged[new_r][new_c] = False
                        else:
                            self.flagged[old_r][old_c] = False

                    self.revealed[new_r][new_c] = False

                    if (old_r, old_c) in self._flags_to_transfer:
                        self.flagged[new_r][new_c] = True
                        self.flagged[old_r][old_c] = False
                    else:
                        self.flagged[new_r][new_c] = False

                self.mines_left = self.mines
                for row in range(self.rows):
                    for col in range(self.cols):
                        if self.flagged[row][col]:
                            self.mines_left -= 1

                self.update_numbers()
                self._mines_moved = True
        else:
            self.flash_alpha = max(0, (1.0 - progress) * 5)
        
        if progress >= 1.0:
            self.moving_mines = False
            self.flash_alpha = 0
            self._mines_moved = False
            self.move_start_positions = []
            self.move_end_positions = []
            self._flags_to_transfer = {}
            if not self.game_over:
                self.check_win()

    def get_flash_alpha(self):
        if hasattr(self, 'flash_alpha') and self.flash_alpha > 0:
            return int(self.flash_alpha * 255)
        return 0

    def toggle_flag(self, row, col):
        if not (0 <= row < self.rows and 0 <= col < self.cols): return False
        if self.game_over or self.paused or self.revealed[row][col]: return False
        if self.game_type == 'safari' and self.moving_mines: return False
        self.flagged[row][col] = not self.flagged[row][col]
        if self.flagged[row][col]:
            self.mines_left -= 1
            if self.game_type == 'chronos': self.total_pause_time -= self.time_penalty
        else: self.mines_left += 1
        self.check_win()
        return True
    
    def reveal(self, row, col):
        self.click_count += 1
        if not (0 <= row < self.rows and 0 <= col < self.cols): return False
        if self.game_over or self.paused or self.revealed[row][col] or self.flagged[row][col]: return False
        if self.game_type == 'safari' and self.moving_mines: return False
        
        if self.first_click:
            self.first_click = False
            self.place_mines(row, col)
            self.start_time = time.time()
            if self.game_type == 'safari': self.last_move_time = 0
        
        if self.board[row][col] == -1:
            self.revealed[row][col] = True
            self.game_over = True
            self.game_won = False
            self.elapsed_time = time.time() - self.start_time - self.total_pause_time
            return True
            
        queue = [(row, col)]; visited = set()
        while queue and not self.game_over:
            r, c = queue.pop(0)
            if (r, c) in visited: continue
            if self.revealed[r][c]: continue
            if self.flagged[r][c]: continue
            visited.add((r, c)); self.revealed[r][c] = True
            if self.board[r][c] == 0:
                for i in [-1, 0, 1]:
                    for j in [-1, 0, 1]:
                        if i == 0 and j == 0: continue
                        nr, nc = r + i, c + j
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if not self.revealed[nr][nc] and not self.flagged[nr][nc] and self.board[nr][nc] != -1:
                                queue.append((nr, nc))
        if not self.game_over: 
            self.check_win()
        return False
    
    def reveal_adjacent(self, row, col):
        if self._processing_adjacent: 
            return False
        self._processing_adjacent = True
        try:
            if self.game_over or self.paused or not self.revealed[row][col] or self.board[row][col] <= 0: 
                return False
            
            flag_count = 0
            adjacent = []
            for i in [-1, 0, 1]:
                for j in [-1, 0, 1]:
                    if i == 0 and j == 0: 
                        continue
                    r, c = row + i, col + j
                    if 0 <= r < self.rows and 0 <= c < self.cols:
                        adjacent.append((r, c))
                        if self.flagged[r][c]: 
                            flag_count += 1
            
            if flag_count == self.board[row][col]:
                for r, c in adjacent:
                    if self.game_over: 
                        return True
                    if not self.flagged[r][c] and not self.revealed[r][c]:
                        if self.board[r][c] == -1:
                            self.revealed[r][c] = True
                            self.game_over = True
                            self.game_won = False
                            self.elapsed_time = time.time() - self.start_time - self.total_pause_time
                            return True
                        elif self.board[r][c] > 0:
                            self.revealed[r][c] = True
                        else:
                            queue = [(r, c)]
                            visited = set()
                            while queue and not self.game_over:
                                rr, cc = queue.pop(0)
                                if (rr, cc) in visited: 
                                    continue
                                if self.revealed[rr][cc]: 
                                    continue
                                if self.flagged[rr][cc]: 
                                    continue
                                visited.add((rr, cc))
                                self.revealed[rr][cc] = True
                                
                                if self.board[rr][cc] == 0:
                                    for ii in [-1, 0, 1]:
                                        for jj in [-1, 0, 1]:
                                            if ii == 0 and jj == 0: 
                                                continue
                                            nrr, ncc = rr + ii, cc + jj
                                            if 0 <= nrr < self.rows and 0 <= ncc < self.cols:
                                                if not self.revealed[nrr][ncc] and not self.flagged[nrr][ncc] and self.board[nrr][ncc] != -1:
                                                    queue.append((nrr, ncc))
                
                if not self.game_over:
                    self.check_win()
                return True
            
            return False
        finally:
            self._processing_adjacent = False
    
    def check_win(self):
        if self.game_over:
            return
        if self.game_type == 'safari' and self.moving_mines:
            return
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] != -1 and not self.revealed[row][col]:
                    return
        
        self.game_over = True
        self.game_won = True
        self.elapsed_time = time.time() - self.start_time - self.total_pause_time
        self.win_delay_active = True
        self.win_delay_timer = 0

    def update_win_delay(self, dt):
        if self.win_delay_active:
            self.win_delay_timer += dt
            if self.win_delay_timer >= 1.0:
                self.win_delay_active = False
                return True
        return False

    def toggle_pause(self):
        if self.game_over or self.first_click: return False
        self.paused = not self.paused
        if self.paused: self.pause_time = time.time()
        else: self.total_pause_time += time.time() - self.pause_time
        return True
            
    def get_elapsed_time(self):
        if self.first_click: 
            return 0
        elif self.game_over: 
            return self.elapsed_time
        elif self.paused: 
            return self.pause_time - self.start_time - self.total_pause_time
        else:
            current_time = time.time() - self.start_time - self.total_pause_time
            if self.game_type == 'chronos' and current_time >= self.time_limit:
                self.game_over = True
                self.game_won = False
                self.elapsed_time = self.time_limit
                self.time_out = True 
                return self.time_limit
            return current_time

    def get_move_progress(self): return self.move_progress if self.moving_mines else 0
    def get_move_direction(self): return self.move_direction if self.moving_mines else None
    def get_time_left(self):
        if self.game_type != 'chronos': return None
        return max(0, self.time_limit - self.get_elapsed_time())
    def get_flash_alpha(self):
        if hasattr(self, 'flash_alpha') and self.flash_alpha > 0:
            return int(self.flash_alpha * 255)
        return 0

def create_massive_explosion(field_x, field_y, field_width, field_height, rows, cols, CELL_SIZE):
    particles = []
    
    center_x = field_x + field_width // 2
    center_y = field_y + field_height // 2
    
    for _ in range(300):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(200, 600)
        particles.append({
            'x': center_x, 'y': center_y,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed - random.uniform(100, 300),
            'gravity': random.uniform(300, 800),
            'life': 1.0,
            'decay': random.uniform(0.3, 0.8),
            'color': random.choice([
                (255, 60, 20), (255, 160, 30), (255, 220, 60),
                (255, 140, 40), (255, 200, 50), (255, 80, 10),
                (220, 40, 10), (255, 100, 30), (255, 180, 20),
                (255, 50, 50), (255, 200, 0), (255, 100, 0)
            ]),
            'size': random.uniform(3, 8)
        })
    
    for row in range(rows):
        for col in range(cols):
            x = field_x + col * CELL_SIZE + CELL_SIZE // 2
            y = field_y + row * CELL_SIZE + CELL_SIZE // 2
            
            for _ in range(random.randint(3, 6)):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(100, 350)
                particles.append({
                    'x': x, 'y': y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed - random.uniform(80, 250),
                    'gravity': random.uniform(200, 600),
                    'life': 1.0,
                    'decay': random.uniform(0.4, 0.9),
                    'color': random.choice([
                        (255, 80, 30), (255, 180, 40), (255, 220, 70),
                        (200, 60, 20), (255, 120, 30), (255, 160, 40),
                        (255, 200, 60), (180, 50, 15), (255, 140, 35)
                    ]),
                    'size': random.uniform(2, 6)
                })
    
    for _ in range(400):
        x = random.randint(field_x, field_x + field_width)
        y = random.randint(field_y, field_y + field_height)
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(150, 500)
        particles.append({
            'x': x, 'y': y,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed - random.uniform(100, 350),
            'gravity': random.uniform(250, 700),
            'life': 1.0,
            'decay': random.uniform(0.5, 1.0),
            'color': random.choice([
                (255, 200, 100), (255, 150, 50), (255, 100, 30),
                (255, 220, 80), (255, 180, 60), (200, 100, 30),
                (255, 255, 100), (255, 200, 80)
            ]),
            'size': random.uniform(1, 3)
        })
    
    return particles

def get_difficulty_name(diff):
    return {'easy':'Легкая','average':'Средняя','hard':'Сложная','super':'Экстра','custom':'Своя игра'}.get(diff, diff)

def get_mode_name(mode):
    return {'classic':'Классический','chronos':'Хронос','safari':'Сафари'}.get(mode, mode)

def draw_neon_border(screen, rect, accent_color, is_dark_theme):
    if is_dark_theme:
        neon_main = accent_color
        neon_glow1 = tuple(min(255, c+80) for c in accent_color)
        neon_glow2 = tuple(max(0, c-40) for c in accent_color)
    else:
        neon_main = tuple(max(0, c-30) for c in accent_color)
        neon_glow1 = accent_color
        neon_glow2 = tuple(min(255, c+40) for c in accent_color)
    
    bp = 15
    bs = pygame.Surface((rect.width+bp*2, rect.height+bp*2), pygame.SRCALPHA)
    
    for i in range(12, 0, -2):
        a = int(25*(1-i/15))
        pygame.draw.rect(bs, (*neon_glow1, a), (bp-i//2, bp-i//2, rect.width+i, rect.height+i), 2, border_radius=12)
    for i in range(8, 0, -1):
        a = int(45*(1-i/10))
        pygame.draw.rect(bs, (*neon_main, a), (bp-i//2, bp-i//2, rect.width+i, rect.height+i), 2, border_radius=12)
    
    pygame.draw.rect(bs, neon_main, (bp, bp, rect.width, rect.height), 3, border_radius=12)
    pygame.draw.rect(bs, neon_glow2, (bp+1, bp+1, rect.width-2, rect.height-2), 1, border_radius=10)
    
    blink = abs(math.sin(pygame.time.get_ticks()/500))
    if blink > 0.5:
        gs = pygame.Surface((bs.get_width(), bs.get_height()), pygame.SRCALPHA)
        pygame.draw.rect(gs, (*neon_glow1, int(30*(blink-0.5)*2)), (bp-2, bp-2, rect.width+4, rect.height+4), 4, border_radius=14)
        bs.blit(gs, (0,0))
    
    screen.blit(bs, (rect.x-bp, rect.y-bp))

def draw_result_border(screen, rect, color, is_dark_theme):
    if is_dark_theme:
        main_color = color
        glow1 = tuple(min(255, c+80) for c in color)
        glow2 = tuple(max(0, c-40) for c in color)
    else:
        main_color = color
        glow1 = tuple(min(255, c+60) for c in color)
        glow2 = tuple(max(0, c-30) for c in color)
    
    bp = 15
    bs = pygame.Surface((rect.width+bp*2, rect.height+bp*2), pygame.SRCALPHA)
    
    for i in range(12, 0, -2):
        a = int(35*(1-i/15))
        pygame.draw.rect(bs, (*glow1, a), (bp-i//2, bp-i//2, rect.width+i, rect.height+i), 3, border_radius=12)
    for i in range(8, 0, -1):
        a = int(60*(1-i/10))
        pygame.draw.rect(bs, (*main_color, a), (bp-i//2, bp-i//2, rect.width+i, rect.height+i), 2, border_radius=12)
    
    pygame.draw.rect(bs, main_color, (bp, bp, rect.width, rect.height), 4, border_radius=12)
    
    inner_rect = pygame.Rect(bp+2, bp+2, rect.width-4, rect.height-4)
    pygame.draw.rect(bs, (*glow2, 100), inner_rect, 2, border_radius=10)
    
    if color == (100, 200, 100) or (len(color) == 3 and color[0] < 150 and color[1] > 150):
        blink = abs(math.sin(pygame.time.get_ticks() / 300))
        if blink > 0.3:
            gs = pygame.Surface((bs.get_width(), bs.get_height()), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*glow1, int(40*(blink-0.3)/0.7)), (bp-2, bp-2, rect.width+4, rect.height+4), 5, border_radius=14)
            bs.blit(gs, (0,0))
    
    screen.blit(bs, (rect.x-bp, rect.y-bp))

def draw_field_inner_glow(screen, rect, accent_color, is_dark_theme):
    gs = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    colors = [(*accent_color, a) for a in ([15,10,5,2] if is_dark_theme else [12,8,4,1])]
    for i, col in enumerate(colors):
        p = i*3
        if p*2 < rect.width and p*2 < rect.height:
            pygame.draw.rect(gs, col, (p, p, rect.width-p*2, rect.height-p*2), 2, border_radius=10)
    screen.blit(gs, (rect.x, rect.y))


def check_all_achievements(setting_name, game_obj, games, wins, difficulty, global_type):
    
    check_and_notify(setting_name, 'games_played', games + 1)
    
    flags_count = sum(sum(row) for row in game_obj.flagged)
    check_and_notify(setting_name, 'flags_placed', flags_count)
    
    if game_obj.game_won:
        check_and_notify(setting_name, 'games_won', wins + 1)
        
        if difficulty == 'easy':
            check_and_notify(setting_name, 'win_easy', 1)
        elif difficulty == 'hard':
            check_and_notify(setting_name, 'win_hard', 1)
        elif difficulty == 'super':
            check_and_notify(setting_name, 'win_super', 1)
        
        if global_type == 'chronos':
            check_and_notify(setting_name, 'win_chronos', 1)
        elif global_type == 'safari':
            check_and_notify(setting_name, 'win_safari', 1)
        
        check_and_notify(setting_name, 'win_under_time', int(game_obj.elapsed_time))
        
        if flags_count == 0:
            check_and_notify(setting_name, 'win_no_flags', 1)
        
        streak = increment_win_streak(setting_name)
        check_and_notify(setting_name, 'win_streak', streak)
        
        if game_obj.click_count == 1:
            check_and_notify(setting_name, 'perfect_game', 1)
        
        total_cells = game_obj.rows * game_obj.cols
        if difficulty == 'super' and flags_count == total_cells - game_obj.mines:
            check_and_notify(setting_name, 'all_flagged_super', 1)
        
        difficulties_won = 0
        for d in ['easy', 'average', 'hard', 'super']:
            c.execute('SELECT COUNT(*) FROM complete_games WHERE name = ? AND difficulty = ? AND type = ?', 
                    (setting_name, d, global_type))
            if c.fetchone()[0] > 0:
                difficulties_won += 1
        check_and_notify(setting_name, 'win_all_difficulties', difficulties_won)

        modes_won = set()
        c.execute('SELECT DISTINCT difficulty, type FROM complete_games WHERE name = ?', (setting_name,))
        for diff, mode in c.fetchall():
            modes_won.add(f"{diff}_{mode}")
        if len(modes_won) >= 12:
            check_and_notify(setting_name, 'win_all_modes_all_difficulties', 1)

        world_records = 0
        for d in ['easy', 'average', 'hard', 'super']:
            c.execute('SELECT name FROM complete_games WHERE difficulty = ? ORDER BY time ASC LIMIT 1', (d,))
            first = c.fetchone()
            if first and first[0] == setting_name:
                world_records += 1
        check_and_notify(setting_name, 'world_record_all', world_records)
        
        c.execute('SELECT experience, lvl FROM user WHERE name = ?', (setting_name,))
        result = c.fetchone()
        if result:
            total_exp = sum(50 * i * i for i in range(1, result[1])) + result[0]
            check_and_notify(setting_name, 'total_exp', total_exp)
    
    else:
        reset_win_streak(setting_name)


def game(setting_name, diff, type, custom_cols, custom_rows, custom_mines, load_saved=False, saved_data=None, daily_mode=False, daily_date=None, daily_seed=None):
    global global_type, difficulty
    difficulty = diff
    global_type = type
    
    volume_music = get_music()
    volume_sound = get_sound()
    theme_name = get_theme()
    set_theme(theme_name)
    
    from music_manager import get_music_manager
    music_manager = get_music_manager()
    
    lclick_sound = music_manager.load_sound('lclick.mp3')
    rclick_sound = music_manager.load_sound('rclick.mp3')
    win_sound = music_manager.load_sound('win.mp3')
    lose_sound = music_manager.load_sound('lose.mp3')
    wow_sound = music_manager.load_sound('wow.mp3')
    boom_sound = music_manager.load_sound('boom.mp3')
    
    ch_l = pygame.mixer.Channel(1)
    ch_r = pygame.mixer.Channel(2)
    ch_f = pygame.mixer.Channel(3)
    ch_b = pygame.mixer.Channel(4)
    ch_w = pygame.mixer.Channel(5)
    
    for ch, vol in [(ch_l, volume_sound), (ch_r, volume_sound), (ch_f, volume_music), 
                    (ch_b, volume_sound), (ch_w, volume_sound)]:
        ch.set_volume(vol)
    
    music_manager.load_music('game', volume_music)

    user_data = get_user_data()
    games = 0
    wins = 0
    for i in range(len(user_data['logins'])):
        if setting_name == user_data['logins'][i]:
            games = user_data['games'][i]
            wins = user_data['wins'][i]
            break
    
    if load_saved and saved_data:
        rows, cols, mines = saved_data['rows'], saved_data['cols'], saved_data['mines']
        game_obj = Minesweeper(rows, cols, mines, saved_data['game_type'], saved_data['difficulty'])
        game_obj.load_from_save(saved_data)
    else:
        if difficulty == 'easy':
            rows, cols, mines = 8, 8, 10
        elif difficulty == 'average':
            rows, cols, mines = 12, 12, 20
        elif difficulty == 'hard':
            rows, cols, mines = 16, 16, 40
        elif difficulty == 'super':
            rows, cols, mines = 20, 20, 80
        else:
            rows, cols, mines = custom_rows, custom_cols, custom_mines
        game_obj = Minesweeper(rows, cols, mines, global_type, difficulty, seed=daily_seed)
    
    saved_width, saved_height, saved_fullscreen = load_window_settings(1366, 768)
    if saved_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((saved_width, saved_height), pygame.RESIZABLE)
    
    pygame.display.set_caption(f"DeepCore - Сапёр ({get_mode_name(global_type)})")
    
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
    
    rain_effect = RainEffect(saved_width, saved_height)
    clock = pygame.time.Clock()
    last_save_time = time.time()
    SAVE_INTERVAL = 30
    
    sound_played = False
    game_over_display = False
    win_sound_played = False
    
    daily_exit_dialog = False
    force_quit = False
    
    explosion_particles = []
    explosion_active = False
    explosion_timer = 0
    EXPLOSION_DURATION = 0.8
    shake_offset = [0, 0]
    shake_intensity = 5
    game_lost = False
    
    init_theme = get_current_theme()
    temp_font = pygame.font.Font('font/font.otf', 16)
    init_A = init_theme['accent']
    init_AH = init_theme['accent_hover']
    init_CC = init_theme['card']
    init_ER = init_theme['error']
    
    pause_btn = AnimatedButton(0, 0, 120, 36, 'Пауза', temp_font, init_A, init_CC, init_AH)
    pause_continue_btn = AnimatedButton(0, 0, 120, 40, 'Продолжить', temp_font, init_A, init_CC, init_AH)
    pause_settings_btn = AnimatedButton(0, 0, 120, 40, 'Настройки', temp_font, init_A, init_CC, init_AH)
    pause_menu_btn = AnimatedButton(0, 0, 120, 40, 'В меню', temp_font, init_ER, init_CC)
    result_new_btn = AnimatedButton(0, 0, 120, 40, 'Новая игра', temp_font, init_A, init_CC, init_AH)
    result_again_btn = AnimatedButton(0, 0, 120, 40, 'Ещё раз', temp_font, init_A, init_CC, init_AH)
    result_menu_btn = AnimatedButton(0, 0, 120, 40, 'В меню', temp_font, init_ER, init_CC)
    result_daily_btn = AnimatedButton(0, 0, 180, 40, 'В МЕНЮ', temp_font, init_A, init_CC, init_AH)
    dialog_stay_btn = AnimatedButton(0, 0, 130, 38, 'Вернуться', temp_font, init_A, init_CC, init_AH)
    dialog_exit_btn = AnimatedButton(0, 0, 130, 38, 'Выйти', temp_font, init_ER, init_CC)
    
    pressed_cell = None
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
        mouse_left = pygame.mouse.get_pressed()[0]
        mouse_right = pygame.mouse.get_pressed()[2]
        mouse_released = not mouse_left and not mouse_right and mouse_was_pressed
        mouse_was_pressed = mouse_left or mouse_right
        
        frames_passed += 1
        if frames_passed > 3:
            ignore_clicks = False
        
        if game_obj.game_type == 'chronos' and hasattr(game_obj, 'time_out') and game_obj.time_out and not explosion_active and not game_obj.game_won:
            explosion_active = True
            explosion_timer = 0
            shake_intensity = 15
            game_lost = True
            game_obj.time_out = False
            
            explosion_particles = create_massive_explosion(
                field_x, field_y, field_width, field_height, 
                game_obj.rows, game_obj.cols, CELL_SIZE
            )
            ch_b.play(boom_sound)

        if game_obj.win_delay_active:
            delay_complete = game_obj.update_win_delay(dt)
            if delay_complete:
                game_over_display = True
                if not sound_played and not win_sound_played:
                    ch_w.play(wow_sound)
                    sound_played = True
                    win_sound_played = True
        
        theme = get_current_theme()
        is_dark_theme = theme['background'][0] < 100
        
        pause_btn.base_color = theme['accent']
        pause_btn.hover_color = theme['accent_hover']
        pause_btn.text_color = theme['card']
        
        pause_continue_btn.base_color = theme['accent']
        pause_continue_btn.hover_color = theme['accent_hover']
        pause_continue_btn.text_color = theme['card']
        
        pause_settings_btn.base_color = theme['accent']
        pause_settings_btn.hover_color = theme['accent_hover']
        pause_settings_btn.text_color = theme['card']
        
        pause_menu_btn.base_color = theme['error']
        pause_menu_btn.text_color = theme['card']
        
        result_new_btn.base_color = theme['accent']
        result_new_btn.hover_color = theme['accent_hover']
        result_new_btn.text_color = theme['card']
        
        result_again_btn.base_color = theme['accent']
        result_again_btn.hover_color = theme['accent_hover']
        result_again_btn.text_color = theme['card']
        
        result_menu_btn.base_color = theme['error']
        result_menu_btn.text_color = theme['card']
        
        result_daily_btn.base_color = theme['accent']
        result_daily_btn.hover_color = theme['accent_hover']
        result_daily_btn.text_color = theme['card']
        
        dialog_stay_btn.base_color = theme['accent']
        dialog_stay_btn.hover_color = theme['accent_hover']
        dialog_stay_btn.text_color = theme['card']
        
        dialog_exit_btn.base_color = theme['error']
        dialog_exit_btn.text_color = theme['card']
        
        rain_effect.update(current_width, current_height)
        
        if explosion_active:
            explosion_timer += dt
            
            for p in explosion_particles[:]:
                p['x'] += p['vx'] * dt
                p['y'] += p['vy'] * dt
                p['vy'] += p['gravity'] * dt
                p['life'] -= dt * p['decay']
                if p['life'] <= 0:
                    explosion_particles.remove(p)
            
            t = explosion_timer
            intensity = shake_intensity * (1 - t/EXPLOSION_DURATION)
            shake_offset[0] = math.sin(t * 60) * intensity + random.uniform(-3, 3)
            shake_offset[1] = math.cos(t * 55) * intensity + random.uniform(-3, 3)
            
            if explosion_timer >= 1.2:
                explosion_active = False
                game_over_display = True
                ch_f.play(lose_sound)
        
        current_time = time.time()
        if not game_obj.game_over and not game_obj.paused and not game_obj.first_click:
            if current_time - last_save_time >= SAVE_INTERVAL:
                save_game_state(setting_name, game_obj)
                last_save_time = current_time
        
        max_cell_size = 40
        min_cell_size = 20
        available_width = current_width - 100
        available_height = current_height - 200
        CELL_SIZE = max(min_cell_size, min(max_cell_size, 
                        min(available_width // game_obj.cols if game_obj.cols > 0 else 30,
                            available_height // game_obj.rows if game_obj.rows > 0 else 30)))
        
        font_number_size = max(12, int(CELL_SIZE * 0.5))
        font_small_size = max(12, int(20 * current_width / 900))
        font_medium_size = max(14, int(24 * current_width / 900))
        font_large_size = max(20, int(32 * current_width / 900))
        
        font_small = pygame.font.Font('font/font.otf', font_small_size)
        font_medium = pygame.font.Font('font/font.otf', font_medium_size)
        font_large = pygame.font.Font('font/font.otf', font_large_size)
        font_number = pygame.font.Font('font/font.otf', font_number_size)
        
        CARD_COLOR = theme['card']
        TEXT_PRIMARY = theme['text']
        TEXT_SECONDARY = theme['text_secondary']
        ACCENT = theme['accent']
        ACCENT_HOVER = theme['accent_hover']
        BORDER_COLOR = theme['border']
        ERROR_COLOR = theme['error']
        INPUT_BG = theme['input_bg']
        
        field_width = game_obj.cols * CELL_SIZE
        field_height = game_obj.rows * CELL_SIZE
        field_x = (current_width - field_width) // 2
        field_y = (current_height - field_height) // 2 + 40
        
        panel_height = 50
        panel_y = 15
        
        pause_btn_w = 120
        pause_btn_h = 36
        pause_btn_x = current_width - pause_btn_w - 20
        pause_btn_y = panel_y + panel_height + 10
        
        pause_btn.text = "Пауза" if not game_obj.paused else "Игра"
        pause_btn.font = small_font
        pause_btn.set_position(pause_btn_x, pause_btn_y)
        pause_btn.original_rect.width = pause_btn_w
        pause_btn.original_rect.height = pause_btn_h
        pause_btn.update(dt, mouse_pos, mouse_left)
        
        mouse_col = (mouse_pos[0] - field_x) // CELL_SIZE if field_x <= mouse_pos[0] < field_x + field_width else -1
        mouse_row = (mouse_pos[1] - field_y) // CELL_SIZE if field_y <= mouse_pos[1] < field_y + field_height else -1
        hover_cell = (mouse_row, mouse_col) if 0 <= mouse_row < game_obj.rows and 0 <= mouse_col < game_obj.cols else None
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if daily_mode and not game_obj.game_over:
                    daily_exit_dialog = True
                    force_quit = True
                else:
                    if not game_obj.game_over and not game_obj.first_click and not daily_mode:
                        save_game_state(setting_name, game_obj)
                    update_user_games(setting_name, games + 1)
                    if daily_mode and daily_date and not game_obj.game_over:
                        save_daily_result(setting_name, daily_date, 0, False)
                    sys.exit()
            
            if event.type == pygame.VIDEORESIZE and not is_fullscreen:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                window_size = (event.w, event.h)
                save_window_settings(event.w, event.h, is_fullscreen)
                rain_effect = RainEffect(event.w, event.h)
                continue
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                    pygame.display.flip()
                    continue
                if event.key == pygame.K_p and not game_obj.game_over and not game_obj.first_click and not explosion_active:
                    game_obj.toggle_pause()
                if event.key == pygame.K_ESCAPE and not game_obj.game_over and not game_obj.first_click and not explosion_active:
                    game_obj.toggle_pause()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_obj.game_over and not explosion_active:
                    continue
                if game_obj.paused:
                    continue
                if explosion_active:
                    continue
                if hover_cell:
                    pressed_cell = (hover_cell, event.button)
        
        if mouse_released and not ignore_clicks:
            if pause_btn.is_clicked(mouse_pos, True) and not game_obj.game_over and not game_obj.first_click and not explosion_active:
                game_obj.toggle_pause()
            
            if pressed_cell and not explosion_active:
                (p_row, p_col), p_btn = pressed_cell
                if hover_cell and hover_cell == (p_row, p_col):
                    if p_btn == 1:
                        if global_type == 'safari' and game_obj.moving_mines:
                            pass
                        else:
                            ch_l.play(lclick_sound)
                            game_obj.reveal_adjacent(p_row, p_col)
                            
                            if game_obj.game_over and not game_obj.game_won and not explosion_active:
                                explosion_active = True
                                explosion_timer = 0
                                shake_offset = [0, 0]
                                game_lost = True
                                
                                cx = field_x + p_col * CELL_SIZE + CELL_SIZE//2
                                cy = field_y + p_row * CELL_SIZE + CELL_SIZE//2
                                for _ in range(100):
                                    angle = random.uniform(0, math.pi * 2)
                                    speed = random.uniform(150, 500)
                                    explosion_particles.append({
                                        'x': cx, 'y': cy,
                                        'vx': math.cos(angle) * speed,
                                        'vy': math.sin(angle) * speed - random.uniform(200, 400),
                                        'gravity': random.uniform(400, 900),
                                        'life': 1.0,
                                        'decay': random.uniform(0.4, 0.9),
                                        'color': random.choice([
                                            (255, 60, 20), (255, 160, 30), (255, 220, 60),
                                            (255, 140, 40), (255, 200, 50), (255, 80, 10),
                                            (220, 40, 10), (255, 100, 30), (255, 180, 20)
                                        ]),
                                        'size': random.uniform(2, 7)
                                    })
                                ch_b.play(boom_sound)
                            else:
                                was_mine = game_obj.board[p_row][p_col] == -1 and not game_obj.flagged[p_row][p_col]
                                game_obj.reveal(p_row, p_col)
                                if game_obj.game_over and not game_obj.game_won and not explosion_active:
                                    explosion_active = True
                                    explosion_timer = 0
                                    shake_offset = [0, 0]
                                    game_lost = True
                                    
                                    cx = field_x + p_col * CELL_SIZE + CELL_SIZE//2
                                    cy = field_y + p_row * CELL_SIZE + CELL_SIZE//2
                                    for _ in range(100):
                                        angle = random.uniform(0, math.pi * 2)
                                        speed = random.uniform(150, 500)
                                        explosion_particles.append({
                                            'x': cx, 'y': cy,
                                            'vx': math.cos(angle) * speed,
                                            'vy': math.sin(angle) * speed - random.uniform(200, 400),
                                            'gravity': random.uniform(400, 900),
                                            'life': 1.0,
                                            'decay': random.uniform(0.4, 0.9),
                                            'color': random.choice([
                                                (255, 60, 20), (255, 160, 30), (255, 220, 60),
                                                (255, 140, 40), (255, 200, 50), (255, 80, 10),
                                                (220, 40, 10), (255, 100, 30), (255, 180, 20)
                                            ]),
                                            'size': random.uniform(2, 7)
                                        })
                                    ch_b.play(boom_sound)
                    
                    elif p_btn == 3:
                        if global_type == 'safari' and game_obj.moving_mines:
                            pass
                        else:
                            ch_r.play(rclick_sound)
                            game_obj.toggle_flag(p_row, p_col)
                pressed_cell = None
        
        if explosion_active:
            shake_surface = pygame.Surface((current_width, current_height))
            shake_surface.fill(theme['background'])
            
            rain_effect.draw(shake_surface, ACCENT, is_dark_theme)
            
            frame_padding = 15
            frame_rect = pygame.Rect(frame_padding, frame_padding, current_width - frame_padding * 2, current_height - frame_padding * 2)
            pygame.draw.rect(shake_surface, ACCENT, frame_rect, 2, border_radius=12)
            
            panel_rect = pygame.Rect(20, panel_y, current_width - 40, panel_height)
            panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (*CARD_COLOR, 230), (0, 0, panel_rect.width, panel_rect.height), border_radius=12)
            pygame.draw.rect(panel_surf, ACCENT, (0, 0, panel_rect.width, panel_rect.height), 1, border_radius=12)
            shake_surface.blit(panel_surf, (panel_rect.x, panel_rect.y))
            
            time_elapsed = max(0, int(game_obj.get_elapsed_time()))
            time_text = font_medium.render(f"Время: {time_elapsed}с", True, TEXT_PRIMARY)
            shake_surface.blit(time_text, (panel_rect.x + 20, panel_rect.centery - time_text.get_height() // 2))
            
            flags_count = sum(sum(row) for row in game_obj.flagged)
            flags_text = font_medium.render(f"Флаги: {flags_count}", True, TEXT_PRIMARY)
            flags_x = panel_rect.x + panel_rect.width // 2 - flags_text.get_width() // 2
            shake_surface.blit(flags_text, (flags_x, panel_rect.centery - flags_text.get_height() // 2))
            
            mines_text = font_medium.render(f"Мины: {game_obj.mines_left}", True, TEXT_PRIMARY)
            mines_x = panel_rect.x + panel_rect.width - mines_text.get_width() - 20
            shake_surface.blit(mines_text, (mines_x, panel_rect.centery - mines_text.get_height() // 2))
            
            pause_btn.draw_on(shake_surface)
            
            field_rect = pygame.Rect(field_x, field_y, field_width, field_height)
            draw_neon_border(shake_surface, field_rect, ACCENT, is_dark_theme)
            
            shadow_surf = pygame.Surface((field_width + 10, field_height + 10), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 60), (5, 5, field_width, field_height), border_radius=10)
            shake_surface.blit(shadow_surf, (field_x - 5, field_y - 5))
            
            pygame.draw.rect(shake_surface, INPUT_BG, field_rect, border_radius=8)
            pygame.draw.rect(shake_surface, ACCENT, field_rect, 2, border_radius=8)
            
            for row in range(game_obj.rows):
                for col in range(game_obj.cols):
                    x = field_x + col * CELL_SIZE
                    y = field_y + row * CELL_SIZE
                    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                    
                    if game_obj.revealed[row][col]:
                        if game_obj.board[row][col] == -1:
                            pulse = 1 + math.sin(explosion_timer * 20) * 0.4
                            pygame.draw.rect(shake_surface, (*ERROR_COLOR, 80), rect)
                            pygame.draw.circle(shake_surface, ERROR_COLOR, rect.center, int(CELL_SIZE//3 * pulse))
                            if random.random() < 0.3:
                                spark_x = rect.centerx + random.uniform(-10, 10)
                                spark_y = rect.centery + random.uniform(-10, 10)
                                explosion_particles.append({
                                    'x': spark_x, 'y': spark_y,
                                    'vx': random.uniform(-50, 50),
                                    'vy': random.uniform(-100, -30),
                                    'gravity': 200,
                                    'life': 0.5,
                                    'decay': 2.0,
                                    'color': (255, 200, 100),
                                    'size': 1.5
                                })
                        else:
                            pygame.draw.rect(shake_surface, CARD_COLOR, rect)
                            pygame.draw.rect(shake_surface, BORDER_COLOR, rect, 1)
                            if game_obj.board[row][col] > 0:
                                color = NUMBER_COLORS[game_obj.board[row][col]] if game_obj.board[row][col] < len(NUMBER_COLORS) else TEXT_PRIMARY
                                text = font_number.render(str(game_obj.board[row][col]), True, color)
                                shake_surface.blit(text, text.get_rect(center=rect.center))
                    else:
                        pygame.draw.rect(shake_surface, INPUT_BG, rect)
                        pygame.draw.rect(shake_surface, BORDER_COLOR, rect, 1)
                        if game_obj.flagged[row][col]:
                            fx, fy = rect.centerx, rect.centery
                            fp = [
                                (fx - CELL_SIZE//4, fy - CELL_SIZE//4),
                                (fx + CELL_SIZE//4, fy),
                                (fx - CELL_SIZE//4, fy + CELL_SIZE//4)
                            ]
                            pygame.draw.polygon(shake_surface, theme['flag'], fp)
            
            for p in explosion_particles:
                alpha = int(255 * p['life'])
                size = int(p['size'] * p['life'] * 2)
                if size > 0:
                    ps = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                    pygame.draw.circle(ps, (*p['color'], alpha), (size, size), size)
                    shake_surface.blit(ps, (int(p['x'] - size), int(p['y'] - size)))
            
            draw_field_inner_glow(shake_surface, field_rect, ERROR_COLOR, is_dark_theme)
            
            screen.blit(shake_surface, (shake_offset[0], shake_offset[1]))
            
            if shake_offset[0] > 0:
                pygame.draw.rect(screen, (0,0,0), (0, 0, shake_offset[0], current_height))
            if shake_offset[0] < 0:
                pygame.draw.rect(screen, (0,0,0), (current_width + shake_offset[0], 0, -shake_offset[0], current_height))
            if shake_offset[1] > 0:
                pygame.draw.rect(screen, (0,0,0), (0, 0, current_width, shake_offset[1]))
            if shake_offset[1] < 0:
                pygame.draw.rect(screen, (0,0,0), (0, current_height + shake_offset[1], current_width, -shake_offset[1]))
        else:
            rain_effect.draw(screen, ACCENT, is_dark_theme)
            
            frame_padding = 15
            frame_rect = pygame.Rect(frame_padding, frame_padding, current_width - frame_padding * 2, current_height - frame_padding * 2)
            pygame.draw.rect(screen, ACCENT, frame_rect, 2, border_radius=12)
            
            panel_rect = pygame.Rect(20, panel_y, current_width - 40, panel_height)
            panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (*CARD_COLOR, 230), (0, 0, panel_rect.width, panel_rect.height), border_radius=12)
            pygame.draw.rect(panel_surf, ACCENT, (0, 0, panel_rect.width, panel_rect.height), 1, border_radius=12)
            screen.blit(panel_surf, (panel_rect.x, panel_rect.y))
            
            time_elapsed = max(0, int(game_obj.get_elapsed_time()))
            time_text = font_medium.render(f"Время: {time_elapsed}с", True, TEXT_PRIMARY)
            screen.blit(time_text, (panel_rect.x + 20, panel_rect.centery - time_text.get_height() // 2))
            
            flags_count = sum(sum(row) for row in game_obj.flagged)
            flags_text = font_medium.render(f"Флаги: {flags_count}", True, TEXT_PRIMARY)
            flags_x = panel_rect.x + panel_rect.width // 2 - flags_text.get_width() // 2
            screen.blit(flags_text, (flags_x, panel_rect.centery - flags_text.get_height() // 2))
            
            mines_text = font_medium.render(f"Мины: {game_obj.mines_left}", True, TEXT_PRIMARY)
            mines_x = panel_rect.x + panel_rect.width - mines_text.get_width() - 20
            screen.blit(mines_text, (mines_x, panel_rect.centery - mines_text.get_height() // 2))
            
            if game_obj.game_type == 'chronos':
                time_left = max(0, int(game_obj.get_time_left()))
                tl_color = ERROR_COLOR if time_left < 30 else TEXT_SECONDARY
                time_left_text = font_small.render(f"Осталось: {time_left}с", True, tl_color)
                screen.blit(time_left_text, (panel_rect.x + 20, panel_rect.y + panel_height + 5))
            
            if game_obj.game_type == 'safari' and not game_obj.moving_mines and not game_obj.first_click:
                time_to_move = max(0, game_obj.move_interval - (time_elapsed - game_obj.last_move_time))
                safari_text = font_small.render(f"Перемещение мин через: {int(time_to_move)}с", True, (255, 150, 50))
                screen.blit(safari_text, (panel_rect.x + 20, panel_rect.y + panel_height + 5))
            
            pause_btn.draw(screen)
            
            field_rect = pygame.Rect(field_x, field_y, field_width, field_height)
            
            if game_obj.game_over and game_over_display and not explosion_active and not game_obj.win_delay_active:
                border_color = theme['win'] if game_obj.game_won else theme['error']
                draw_result_border(screen, field_rect, border_color, is_dark_theme)
            else:
                draw_neon_border(screen, field_rect, ACCENT, is_dark_theme)
            
            shadow_surf = pygame.Surface((field_width + 10, field_height + 10), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 60), (5, 5, field_width, field_height), border_radius=10)
            screen.blit(shadow_surf, (field_x - 5, field_y - 5))
            
            pygame.draw.rect(screen, INPUT_BG, field_rect, border_radius=8)
            pygame.draw.rect(screen, ACCENT, field_rect, 2, border_radius=8)
            
            for row in range(game_obj.rows):
                for col in range(game_obj.cols):
                    x = field_x + col * CELL_SIZE
                    y = field_y + row * CELL_SIZE
                    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                    
                    is_hovered = hover_cell and hover_cell == (row, col)
                    
                    if game_obj.game_type == 'safari' and game_obj.moving_mines:
                        move_offset = (0, 0)
                        for i, (start_r, start_c) in enumerate(game_obj.move_start_positions):
                            if (row, col) == (start_r, start_c):
                                end_r, end_c = game_obj.move_end_positions[i]
                                move_offset = ((end_c - start_c) * game_obj.move_progress * CELL_SIZE,
                                              (end_r - start_r) * game_obj.move_progress * CELL_SIZE)
                                break
                        if move_offset != (0, 0):
                            rect = pygame.Rect(x + move_offset[0], y + move_offset[1], CELL_SIZE, CELL_SIZE)
                    
                    is_pressed = pressed_cell and (pressed_cell[0] == (row, col))
                    if is_pressed:
                        cx, cy = rect.centerx, rect.centery
                        w = int(CELL_SIZE * 0.85)
                        h = int(CELL_SIZE * 0.85)
                        rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
                    
                    if game_obj.revealed[row][col]:
                        if game_obj.board[row][col] == -1 and game_lost:
                            pygame.draw.rect(screen, (*ERROR_COLOR, 80), rect)
                            pygame.draw.circle(screen, ERROR_COLOR, rect.center, CELL_SIZE // 3)
                        else:
                            pygame.draw.rect(screen, CARD_COLOR, rect)
                            pygame.draw.rect(screen, BORDER_COLOR, rect, 1)
                            if game_obj.board[row][col] == -1:
                                pygame.draw.circle(screen, ERROR_COLOR, rect.center, CELL_SIZE // 3)
                            elif game_obj.board[row][col] > 0:
                                color = NUMBER_COLORS[game_obj.board[row][col]] if game_obj.board[row][col] < len(NUMBER_COLORS) else TEXT_PRIMARY
                                text = font_number.render(str(game_obj.board[row][col]), True, color)
                                screen.blit(text, text.get_rect(center=rect.center))
                    else:
                        pygame.draw.rect(screen, INPUT_BG, rect)
                        if is_hovered and not game_obj.game_over:
                            pygame.draw.rect(screen, ACCENT_HOVER, rect, 2)
                        else:
                            pygame.draw.rect(screen, BORDER_COLOR, rect, 1)
                        
                        if game_obj.flagged[row][col]:
                            flag_scale = 0.8 if is_pressed else 1.0
                            fx, fy = rect.centerx, rect.centery
                            fp = [
                                (fx - int(CELL_SIZE//4 * flag_scale), fy - int(CELL_SIZE//4 * flag_scale)),
                                (fx + int(CELL_SIZE//4 * flag_scale), fy),
                                (fx - int(CELL_SIZE//4 * flag_scale), fy + int(CELL_SIZE//4 * flag_scale))
                            ]
                            pygame.draw.polygon(screen, theme['flag'], fp)
            
            draw_field_inner_glow(screen, field_rect, ERROR_COLOR if game_lost else ACCENT, is_dark_theme)
        
        if game_obj.paused and not game_obj.game_over and not explosion_active:
            overlay = pygame.Surface((current_width, current_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            pcw, pch = 450, 250
            pcx = (current_width - pcw)//2
            pcy = (current_height - pch)//2
            pygame.draw.rect(screen, (*CARD_COLOR, 250), (pcx, pcy, pcw, pch), border_radius=20)
            pygame.draw.rect(screen, ACCENT, (pcx, pcy, pcw, pch), 2, border_radius=20)
            
            pause_title = font_large.render("Пауза", True, ACCENT)
            screen.blit(pause_title, pause_title.get_rect(center=(current_width//2, pcy+45)))
            
            btn_w, btn_h, btn_s = 120, 40, 20
            bsx = (current_width - (btn_w*3 + btn_s*2))//2
            by = pcy + pch - 75
            
            for i, btn in enumerate([pause_continue_btn, pause_settings_btn, pause_menu_btn]):
                btn.font = small_font
                btn.set_position(bsx + i*(btn_w+btn_s), by)
                btn.original_rect.width = btn_w
                btn.original_rect.height = btn_h
                btn.update(dt, mouse_pos, mouse_left)
                btn.draw(screen)
            
            if mouse_released and not ignore_clicks:
                if pause_continue_btn.is_clicked(mouse_pos, True):
                    game_obj.toggle_pause()
                elif pause_settings_btn.is_clicked(mouse_pos, True):
                    if not game_obj.game_over and not game_obj.first_click:
                        save_game_state(setting_name, game_obj)
                    settings.settings(setting_name, "game")
                elif pause_menu_btn.is_clicked(mouse_pos, True):
                    if daily_mode and not game_obj.game_over:
                        daily_exit_dialog = True
                    else:
                        if not game_obj.game_over and not game_obj.first_click and not daily_mode:
                            save_game_state(setting_name, game_obj)
                        update_user_games(setting_name, games + 1)
                        music_manager.load_music('menu', volume_music, force=True)
                        return menu.menu(setting_name, 1)
        
        elif game_obj.game_over and game_over_display and not explosion_active and not game_obj.win_delay_active:
            overlay = pygame.Surface((current_width, current_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            rcw, rch = 450, 350
            rcx = (current_width - rcw)//2
            rcy = (current_height - rch)//2
            border_color = theme['win'] if game_obj.game_won else theme['error']
            pygame.draw.rect(screen, (*CARD_COLOR, 250), (rcx, rcy, rcw, rch), border_radius=20)
            pygame.draw.rect(screen, border_color, (rcx, rcy, rcw, rch), 2, border_radius=20)
            
            result_text = font_large.render("Победа!" if game_obj.game_won else "Поражение!", True, border_color)
            screen.blit(result_text, result_text.get_rect(center=(current_width//2, rcy+45)))
            
            time_result = font_medium.render(f"Время: {int(game_obj.elapsed_time)} сек", True, TEXT_PRIMARY)
            screen.blit(time_result, time_result.get_rect(center=(current_width//2, rcy+95)))
            
            difficulty_result = font_medium.render(f"Сложность: {get_difficulty_name(difficulty)}", True, TEXT_PRIMARY)
            screen.blit(difficulty_result, difficulty_result.get_rect(center=(current_width//2, rcy+135)))
            
            mode_result = font_medium.render(f"Режим: {get_mode_name(global_type)}", True, TEXT_PRIMARY)
            screen.blit(mode_result, mode_result.get_rect(center=(current_width//2, rcy+175)))
            
            if daily_mode:
                btn_w = 180
                btn_h = 40
                result_daily_btn.font = small_font
                result_daily_btn.set_position(current_width//2 - btn_w//2, rcy + rch - 65)
                result_daily_btn.original_rect.width = btn_w
                result_daily_btn.original_rect.height = btn_h
                result_daily_btn.update(dt, mouse_pos, mouse_left)
                result_daily_btn.draw(screen)
                
                if mouse_released and not ignore_clicks and result_daily_btn.is_clicked(mouse_pos, True):
                    check_all_achievements(setting_name, game_obj, games, wins, difficulty, global_type)
                    
                    if game_obj.game_won and is_champion_season_active():
                        check_achievement(setting_name, 'champions_2026_participant', 1)
                    
                    delete_save_game(setting_name)
                    update_user_games(setting_name, games + 1)
                    
                    if difficulty != 'custom':
                        add_game_experience(setting_name, game_obj.game_won, difficulty, global_type, game_obj.elapsed_time)
                    
                    if daily_date:
                        save_daily_result(setting_name, daily_date, game_obj.elapsed_time, game_obj.game_won)
                    
                    music_manager.load_music('menu', volume_music, force=True)
                    return menu.menu(setting_name, 1)
            else:
                btn_w, btn_h, btn_s = 120, 40, 15
                bsx = (current_width - (btn_w*3 + btn_s*2))//2
                by = rcy + rch - 65
                
                for i, btn in enumerate([result_new_btn, result_again_btn, result_menu_btn]):
                    btn.font = small_font
                    btn.set_position(bsx + i*(btn_w+btn_s), by)
                    btn.original_rect.width = btn_w
                    btn.original_rect.height = btn_h
                    btn.update(dt, mouse_pos, mouse_left)
                    btn.draw(screen)
                
                if mouse_released and not ignore_clicks:
                    if result_new_btn.is_clicked(mouse_pos, True):
                        check_all_achievements(setting_name, game_obj, games, wins, difficulty, global_type)
                        
                        if difficulty != 'custom':
                            add_game_experience(setting_name, game_obj.game_won, difficulty, global_type, game_obj.elapsed_time)
                        
                        delete_save_game(setting_name)
                        update_user_games(setting_name, games + 1)
                        
                        if game_obj.game_won and difficulty != 'custom':
                            save_game_result(difficulty, setting_name, global_type, game_obj.elapsed_time)
                            update_user_wins(setting_name, wins + 1)
                            check_top_achievements(setting_name)
                        
                        music_manager.load_music('menu', volume_music, force=True)
                        return menu_game.menu_game(setting_name)
                    
                    if result_again_btn.is_clicked(mouse_pos, True):
                        check_all_achievements(setting_name, game_obj, games, wins, difficulty, global_type)
                        
                        if difficulty != 'custom':
                            add_game_experience(setting_name, game_obj.game_won, difficulty, global_type, game_obj.elapsed_time)
                        
                        delete_save_game(setting_name)
                        update_user_games(setting_name, games + 1)
                        
                        if game_obj.game_won and difficulty != 'custom':
                            save_game_result(difficulty, setting_name, global_type, game_obj.elapsed_time)
                            update_user_wins(setting_name, wins + 1)
                            check_top_achievements(setting_name)
                        
                        game(setting_name, diff, type, custom_cols, custom_rows, custom_mines)
                        return
                    
                    if result_menu_btn.is_clicked(mouse_pos, True):
                        check_all_achievements(setting_name, game_obj, games, wins, difficulty, global_type)
                        
                        if difficulty != 'custom':
                            add_game_experience(setting_name, game_obj.game_won, difficulty, global_type, game_obj.elapsed_time)
                        
                        delete_save_game(setting_name)
                        update_user_games(setting_name, games + 1)
                        
                        if game_obj.game_won and difficulty != 'custom':
                            save_game_result(difficulty, setting_name, global_type, game_obj.elapsed_time)
                            update_user_wins(setting_name, wins + 1)
                            check_top_achievements(setting_name)
                        
                        pygame.mixer.music.stop()
                        music_manager.load_music('menu', volume_music, force=True)
                        return menu.menu(setting_name, 1)
        
        if game_obj.game_type == 'safari' and not game_obj.paused and not game_obj.game_over and not game_obj.first_click and not explosion_active:
            if not game_obj.moving_mines:
                game_obj.move_mines_safari()
            else:
                game_obj.update_mines_position(min(1.0, game_obj.get_move_progress() + 0.05))
        
        if daily_exit_dialog:
            overlay = pygame.Surface((current_width, current_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            dw, dh = 420, 200
            dx = current_width//2 - dw//2
            dy = (current_height - dh)//2
            pygame.draw.rect(screen, CARD_COLOR, (dx, dy, dw, dh), border_radius=20)
            pygame.draw.rect(screen, ACCENT, (dx, dy, dw, dh), 2, border_radius=20)
            
            for i, txt in enumerate(["Выходя из уровня, вы не сможете", "пройти его сегодня ещё раз.", "Точно выйти?"]):
                ws = font_small.render(txt, True, TEXT_PRIMARY)
                screen.blit(ws, (current_width//2 - ws.get_width()//2, dy + 25 + i*30))
            
            btn_w, btn_h = 130, 38
            by2 = dy + dh - 55
            for i, btn in enumerate([dialog_stay_btn, dialog_exit_btn]):
                btn.font = small_font
                btn.set_position([current_width//2 - btn_w - 15, current_width//2 + 15][i], by2)
                btn.original_rect.width = btn_w
                btn.original_rect.height = btn_h
                btn.update(dt, mouse_pos, mouse_left)
                btn.draw(screen)
            
            if mouse_released and not ignore_clicks:
                if dialog_stay_btn.is_clicked(mouse_pos, True):
                    daily_exit_dialog = False
                    force_quit = False
                elif dialog_exit_btn.is_clicked(mouse_pos, True):
                    if daily_date:
                        save_daily_result(setting_name, daily_date, 0, False)
                    update_user_games(setting_name, games + 1)
                    if force_quit:
                        sys.exit()
                    music_manager.load_music('menu', volume_music, force=True)
                    return menu.menu(setting_name, 1)
        
        flash_alpha = game_obj.get_flash_alpha()
        if flash_alpha > 0:
            flash_surf = pygame.Surface((current_width, current_height))
            flash_surf.fill((0, 0, 0))
            flash_surf.set_alpha(flash_alpha)
            screen.blit(flash_surf, (0, 0))
        
        effect_manager.draw(screen, current_width, current_height)
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()