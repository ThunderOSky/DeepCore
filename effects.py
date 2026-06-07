import pygame
import math
import random

class VignetteEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
        self._cache = None
        self._cache_size = (0, 0)
    
    def update(self, dt):
        self.time += dt
    
    def draw(self, screen, width, height):
        if self._cache is None or self._cache_size != (width, height):
            self._cache = pygame.Surface((width, height), pygame.SRCALPHA)
            cx, cy = width / 2, height / 2
            for y in range(0, height, 4):
                for x in range(0, width, 4):
                    dist = ((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2
                    a = int(min(1.0, dist * 1.5) * 140)
                    if a > 0:
                        pulse = 0.8 + math.sin(self.time * 2) * 0.2
                        a = int(a * pulse)
                        pygame.draw.rect(self._cache, (0, 0, 0, a), (x, y, 4, 4))
            self._cache_size = (width, height)
        
        screen.blit(self._cache, (0, 0))


class ChromaticEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
    
    def update(self, dt):
        self.time += dt
    
    def draw(self, screen, width, height):
        o = int(2 + math.sin(self.time * 1.2) * 2)
        t = screen.copy()
        
        r = pygame.Surface((width, height), pygame.SRCALPHA)
        r.blit(t, (o, 0))
        r.fill((255, 30, 30, 25), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(r, (0, 0))
        
        b = pygame.Surface((width, height), pygame.SRCALPHA)
        b.blit(t, (-o, 0))
        b.fill((30, 30, 255, 25), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(b, (0, 0))
        
        g = pygame.Surface((width, height), pygame.SRCALPHA)
        g.blit(t, (o//2, o//2))
        g.fill((30, 255, 30, 15), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(g, (0, 0))


class WaveEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
    
    def update(self, dt):
        self.time += dt
    
    def draw(self, screen, width, height):
        temp = screen.copy()
        screen.fill((0, 0, 0, 0))
        for y in range(0, height, 4):
            offset_x = int(math.sin(self.time * 3 + y * 0.02) * 8)
            offset_y = int(math.cos(self.time * 2.5 + y * 0.015) * 4)
            screen.blit(temp, (offset_x, y + offset_y), (0, y, width, 4))
        
        wave_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        for y in range(0, height, 20):
            alpha = int(30 * (0.5 + math.sin(self.time * 5 + y * 0.05) * 0.5))
            pygame.draw.line(wave_surf, (200, 220, 255, alpha), (0, y), (width, y), 2)
        screen.blit(wave_surf, (0, 0))


class GlitchEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
        self.glitch_timer = 0
    
    def update(self, dt):
        self.time += dt
        if self.glitch_timer > 0:
            self.glitch_timer -= dt
        if random.random() < 0.02 and self.glitch_timer <= 0:
            self.glitch_timer = 0.1
    
    def draw(self, screen, width, height):
        temp = screen.copy()
        if self.glitch_timer > 0:
            for _ in range(random.randint(5, 15)):
                y = random.randint(0, height - 20)
                h = random.randint(5, 30)
                shift = random.randint(-15, 15)
                screen.blit(temp, (shift, y), (0, y, width, h))
            glitch_surf = pygame.Surface((width, height), pygame.SRCALPHA)
            for _ in range(random.randint(3, 8)):
                y = random.randint(0, height - 10)
                h = random.randint(3, 15)
                color = random.choice([(255, 0, 0, 80), (0, 255, 0, 80), (0, 0, 255, 80)])
                pygame.draw.rect(glitch_surf, color, (0, y, width, h))
            screen.blit(glitch_surf, (0, 0))
        
        r_shift = pygame.Surface((width, height), pygame.SRCALPHA)
        r_shift.blit(temp, (2, 0))
        r_shift.fill((255, 0, 0, 20), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(r_shift, (0, 0))
        
        b_shift = pygame.Surface((width, height), pygame.SRCALPHA)
        b_shift.blit(temp, (-2, 0))
        b_shift.fill((0, 0, 255, 20), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(b_shift, (0, 0))


class PixelSortEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
        self.sort_timer = 0
    
    def update(self, dt):
        self.time += dt
        if self.sort_timer > 0:
            self.sort_timer -= dt
        if random.random() < 0.02 and self.sort_timer <= 0:
            self.sort_timer = 0.15
    
    def draw(self, screen, width, height):
        if self.sort_timer > 0:
            temp = screen.copy()
            for _ in range(random.randint(3, 8)):
                y = random.randint(0, height - 20)
                h = random.randint(10, 40)
                strip = pygame.Surface((width, h))
                strip.blit(temp, (0, 0), (0, y, width, h))
                
                pixels = []
                for x in range(0, width, 4):
                    px_strip = pygame.Surface((4, h))
                    px_strip.blit(strip, (0, 0), (x, 0, 4, h))
                    pixels.append(px_strip)
                random.shuffle(pixels)
                
                for i, px in enumerate(pixels):
                    screen.blit(px, (i * 4, y))
        
        r = pygame.Surface((width, height), pygame.SRCALPHA)
        r.blit(screen, (3, 0))
        r.fill((255, 0, 0, 15), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(r, (0, 0))
        
        b = pygame.Surface((width, height), pygame.SRCALPHA)
        b.blit(screen, (-3, 0))
        b.fill((0, 0, 255, 15), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(b, (0, 0))


class SnowEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.snowflakes = []
        self.time = 0
        for _ in range(150):
            self.snowflakes.append({
                'x': random.randint(0, width),
                'y': random.randint(0, height),
                'size': random.randint(2, 6),
                'speed': random.uniform(30, 80),
                'sway': random.uniform(0, math.pi * 2),
                'sway_speed': random.uniform(1, 3)
            })
    
    def update(self, dt):
        self.time += dt
        for s in self.snowflakes:
            s['y'] += s['speed'] * dt
            s['sway'] += dt * s['sway_speed']
            s['x'] += math.sin(s['sway']) * 20 * dt
            
            if s['y'] > self.height:
                s['y'] = -10
                s['x'] = random.randint(0, self.width)
            if s['x'] < -10:
                s['x'] = self.width + 10
            if s['x'] > self.width + 10:
                s['x'] = -10
    
    def draw(self, screen, width, height):
        snow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        for s in self.snowflakes:
            alpha = int(150 * (0.5 + math.sin(self.time * 2 + s['x'] * 0.01) * 0.3))
            pygame.draw.circle(snow_surf, (255, 255, 255, alpha), (int(s['x']), int(s['y'])), s['size'])
            pygame.draw.circle(snow_surf, (200, 220, 255, alpha // 2), (int(s['x']), int(s['y'])), s['size'] + 1, 1)
        screen.blit(snow_surf, (0, 0))


class CrystalEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
        self.sparks = []
    
    def update(self, dt):
        self.time += dt
        
        if random.random() < 0.2: 
            for _ in range(random.randint(2, 4)): 
                self.sparks.append({
                    'x': random.randint(0, self.width),
                    'y': random.randint(0, self.height),
                    'vx': random.uniform(-40, 40),
                    'vy': random.uniform(-80, -20),
                    'life': 1.0,
                    'size': random.uniform(2, 4),
                    'color': random.choice([(200, 200, 255), (170, 170, 255), (140, 140, 255), (220, 220, 255)])
                })
        
        for s in self.sparks[:]:
            s['x'] += s['vx'] * dt
            s['y'] += s['vy'] * dt
            s['vy'] += 180 * dt
            s['life'] -= dt * 2.5
            if s['life'] <= 0 or s['y'] > self.height:
                self.sparks.remove(s)
    
    def draw(self, screen, width, height):
        crystal = pygame.Surface((width, height), pygame.SRCALPHA)
        cx, cy = width // 2, height // 2
        
        pulse = 0.6 + math.sin(self.time * 6) * 0.4
        for r in range(80, 5, -8):
            alpha = int(12 * (1 - r/80) * pulse)
            pygame.draw.circle(crystal, (120, 160, 255, alpha), (cx, cy), r)
        
        for i in range(3):
            angle = self.time * 0.8 + i * math.pi * 2 / 3
            x = cx + math.cos(angle) * 140
            y = cy + math.sin(angle) * 90
            for r in range(50, 5, -6):
                alpha = int(10 * (1 - r/50) * (0.5 + math.sin(self.time * 4 + i) * 0.5))
                pygame.draw.circle(crystal, (100, 140, 255, alpha), (int(x), int(y)), r)
        
        screen.blit(crystal, (0, 0))
        
        for s in self.sparks:
            alpha = int(255 * s['life'])
            size = int(s['size'] * s['life'])
            if size > 0:
                pygame.draw.circle(screen, (*s['color'], alpha), (int(s['x']), int(s['y'])), size)

class AuroraEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
    
    def update(self, dt):
        self.time += dt
    
    def draw(self, screen, width, height):
        aurora = pygame.Surface((width, height), pygame.SRCALPHA)
        
        zones = [
            {'y_offset': height * 0.15, 'speed': 0.4, 'colors': [(0, 200, 100), (0, 150, 150), (0, 100, 200)], 'alpha': 55},
            {'y_offset': height * 0.45, 'speed': 0.5, 'colors': [(50, 200, 100), (100, 150, 150), (50, 100, 200)], 'alpha': 50},
            {'y_offset': height * 0.75, 'speed': 0.6, 'colors': [(100, 200, 50), (50, 150, 100), (0, 100, 150)], 'alpha': 45},
        ]
        
        for zone in zones:
            for i in range(6): 
                offset = i * 1.2
                y_shift = zone['y_offset'] + i * 15
                color = zone['colors'][i % len(zone['colors'])]
                alpha = zone['alpha'] - i * 6
                if alpha < 5:
                    continue
                
                points = []
                for x in range(0, width + 30, 15):
                    y = y_shift + math.sin(x * 0.007 + self.time * zone['speed'] + offset) * 40
                    y += math.cos(x * 0.012 + self.time * 0.4 + offset) * 20
                    points.append((x, y))
                
                for j in range(len(points) - 1):
                    pygame.draw.line(aurora, (*color, alpha), points[j], points[j+1], 7 - i)
                    for k in range(3):
                        glow_alpha = max(1, alpha // (k + 2))
                        pygame.draw.line(aurora, (*color, glow_alpha), 
                                       (points[j][0], points[j][1] + k * 3),
                                       (points[j+1][0], points[j+1][1] + k * 3), 5 - k)
                        pygame.draw.line(aurora, (*color, glow_alpha), 
                                       (points[j][0], points[j][1] - k * 3),
                                       (points[j+1][0], points[j+1][1] - k * 3), 5 - k)
        
        screen.blit(aurora, (0, 0))


class NebulaEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
        self.nebulas = []
        for _ in range(12):
            self.nebulas.append({
                'x': random.randint(0, width),
                'y': random.randint(0, height),
                'radius': random.randint(180, 350),
                'vx': random.uniform(5, 15),
                'vy': random.uniform(3, 10),
                'color': random.choice([(200, 100, 200), (100, 150, 200), (200, 100, 150), (100, 200, 150), (200, 150, 100)]),
                'phase': random.uniform(0, math.pi * 2),
                'brightness': random.uniform(0.7, 1.0)
            })
    
    def update(self, dt):
        self.time += dt
        for n in self.nebulas:
            n['x'] += n['vx'] * dt
            n['y'] += n['vy'] * dt
            n['phase'] += dt
            if n['x'] > self.width + n['radius']:
                n['x'] = -n['radius']
            if n['x'] < -n['radius']:
                n['x'] = self.width + n['radius']
            if n['y'] > self.height + n['radius']:
                n['y'] = -n['radius']
            if n['y'] < -n['radius']:
                n['y'] = self.height + n['radius']
    
    def draw(self, screen, width, height):
        nebula_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        for n in self.nebulas:
            pulse = 0.6 + math.sin(n['phase'] * 2) * 0.4
            for r in range(int(n['radius'] * pulse), 0, -12):
                alpha = int(45 * (1 - r / (n['radius'] * pulse)) * (0.8 + math.sin(n['phase'] * 3) * 0.2) * n['brightness'])
                pygame.draw.circle(nebula_surf, (*n['color'], alpha), (int(n['x']), int(n['y'])), r)
        screen.blit(nebula_surf, (0, 0))


class RainbowEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
    
    def update(self, dt):
        self.time += dt
    
    def draw(self, screen, width, height):
        rainbow = pygame.Surface((width, height), pygame.SRCALPHA)
        for y in range(height):
            hue = (y * 0.5 + self.time * 50) % 360
            r = int((math.sin(hue * math.pi / 180) * 127 + 128))
            g = int((math.sin((hue + 120) * math.pi / 180) * 127 + 128))
            b = int((math.sin((hue + 240) * math.pi / 180) * 127 + 128))
            alpha = 35
            pygame.draw.line(rainbow, (r, g, b, alpha), (0, y), (width, y))
        screen.blit(rainbow, (0, 0))


class BubbleEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.bubbles = []
        self.theme_color = None
    
    def update(self, dt):
        from theme import get_current_theme
        theme = get_current_theme()
        self.theme_color = theme['accent']
        
        if random.random() < 0.08 and len(self.bubbles) < 60:
            self.bubbles.append({
                'x': random.randint(0, self.width),
                'y': self.height + random.randint(0, 50),
                'radius': random.randint(8, 20),
                'speed': random.uniform(40, 80),
                'phase': random.uniform(0, math.pi * 2),
                'wobble': random.uniform(0, math.pi * 2)
            })
        
        for b in self.bubbles[:]:
            b['y'] -= b['speed'] * dt
            b['phase'] += dt * 4
            b['wobble'] += dt * 3
            if b['y'] + b['radius'] < 0:
                self.bubbles.remove(b)
    
    def draw(self, screen, width, height):
        bubble_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        for b in self.bubbles:
            color = self.theme_color if self.theme_color else (100, 150, 200)
            alpha = int(120 * (0.6 + math.sin(b['phase']) * 0.4))
            wobble_x = int(math.sin(b['wobble']) * 3)
            
            pygame.draw.circle(bubble_surf, (*color, alpha), 
                             (int(b['x'] + wobble_x), int(b['y'])), b['radius'])
            pygame.draw.circle(bubble_surf, (255, 255, 255, alpha // 2), 
                             (int(b['x'] + wobble_x), int(b['y'])), b['radius'], 2)
            light_x = b['x'] + wobble_x - b['radius'] // 3
            light_y = b['y'] - b['radius'] // 3
            pygame.draw.circle(bubble_surf, (255, 255, 255, alpha // 2), 
                             (int(light_x), int(light_y)), b['radius'] // 4)
        screen.blit(bubble_surf, (0, 0))

class RaindropEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.droplets = []
        self.streams = []
        self.time = 0
    
    def update(self, dt):
        self.time += dt
        
        if random.random() < 0.1 and len(self.droplets) < 80:
            self.droplets.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'radius': random.randint(3, 8),
                'life': 1.0,
                'phase': random.uniform(0, math.pi * 2)
            })
        
        for d in self.droplets[:]:
            d['life'] -= dt * 0.5
            d['phase'] += dt * 5
            if d['life'] <= 0:
                self.streams.append({
                    'x': d['x'],
                    'y': d['y'],
                    'length': 5,
                    'life': 0.8,
                    'angle': random.uniform(-0.3, 0.3)
                })
                self.droplets.remove(d)
        
        for s in self.streams[:]:
            s['life'] -= dt * 1.5
            s['length'] += dt * 30
            s['y'] += dt * 25
            if s['life'] <= 0 or s['y'] > self.height:
                self.streams.remove(s)
    
    def draw(self, screen, width, height):
        from theme import get_current_theme
        theme = get_current_theme()
        theme_color = theme['accent']
        is_dark = theme['background'][0] < 100
        
        drop_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        for d in self.droplets:
            alpha = int(150 * d['life'])
            if is_dark:
                color = (*theme_color, alpha)
            else:
                dark_color = (max(0, theme_color[0] - 100), max(0, theme_color[1] - 100), max(0, theme_color[2] - 100))
                color = (*dark_color, alpha)
            
            pygame.draw.circle(drop_surf, color, (int(d['x']), int(d['y'])), d['radius'])
            light_alpha = alpha // 2
            light_x = d['x'] - d['radius'] // 2
            light_y = d['y'] - d['radius'] // 2
            pygame.draw.circle(drop_surf, (255, 255, 255, light_alpha), 
                             (int(light_x), int(light_y)), d['radius'] // 3)
        
        for s in self.streams:
            alpha = int(100 * s['life'])
            if is_dark:
                color = (*theme_color, alpha)
            else:
                dark_color = (max(0, theme_color[0] - 100), max(0, theme_color[1] - 100), max(0, theme_color[2] - 100))
                color = (*dark_color, alpha)
            
            end_x = s['x'] + s['angle'] * s['length']
            end_y = s['y'] + s['length']
            pygame.draw.line(drop_surf, color, (s['x'], s['y']), (end_x, end_y), 2)
        
        screen.blit(drop_surf, (0, 0))

class EffectManager:
    def __init__(self):
        self.effect = None
        self.instance = None
    
    def set_effect(self, name, width, height):
        self.effect = name
        effects = {
            "vignette": VignetteEffect,
            "chromatic": ChromaticEffect,
            "wave": WaveEffect,
            "glitch": GlitchEffect,
            "pixelsort": PixelSortEffect,
            "snow": SnowEffect,
            "crystal": CrystalEffect,
            "aurora": AuroraEffect,
            "nebula": NebulaEffect,
            "rainbow": RainbowEffect,
            "bubble": BubbleEffect,
            "raindrop": RaindropEffect,
        }
        self.instance = effects.get(name, lambda w, h: None)(width, height) if name in effects else None
    
    def update(self, dt, width, height):
        if self.instance:
            self.instance.update(min(dt, 0.05))
    
    def draw(self, screen, width, height):
        if self.instance:
            self.instance.draw(screen, width, height)