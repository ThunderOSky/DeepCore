import pygame
import os
import random
from settings_manager import get_music_pack

class MusicManager:
    def __init__(self):
        self.current_pack = None
        self.current_music_type = None
        self.current_volume = None
        self.tracks_cache = {}
        self.packs = {
            "classic": "Стандартный",
            "city": "Современный",
            "minecraft": "Майнкрафт",
            "custom": "Пользовательский"
        }
    
    def get_available_packs(self):
        return list(self.packs.keys())
    
    def get_pack_name(self, pack_id):
        return self.packs.get(pack_id, pack_id)
    
    def get_music_tracks(self, music_type, pack=None):
        if pack is None:
            pack = get_music_pack()
        
        cache_key = f"{pack}_{music_type}"
        if cache_key in self.tracks_cache:
            return self.tracks_cache[cache_key]
        
        tracks = []
        
        main_path = f"sounds/{pack}/{music_type}.mp3"
        if os.path.exists(main_path):
            tracks.append(main_path)
        
        i = 1
        while i <= 10:
            numbered_path = f"sounds/{pack}/{music_type}{i}.mp3"
            if os.path.exists(numbered_path):
                tracks.append(numbered_path)
                i += 1
            else:
                break
        
        if not tracks:
            main_path = f"sounds/classic/{music_type}.mp3"
            if os.path.exists(main_path):
                tracks.append(main_path)
            
            i = 1
            while i <= 10:
                numbered_path = f"sounds/classic/{music_type}{i}.mp3"
                if os.path.exists(numbered_path):
                    tracks.append(numbered_path)
                    i += 1
                else:
                    break
        
        self.tracks_cache[cache_key] = tracks
        return tracks
    
    def get_random_track(self, music_type, pack=None):
        tracks = self.get_music_tracks(music_type, pack)
        if tracks:
            return random.choice(tracks)
        return None
    
    def get_sound_path(self, filename):
        pack = get_music_pack()
        
        pack_path = f"sounds/{pack}/{filename}"
        if os.path.exists(pack_path):
            return pack_path
        
        classic_path = f"sounds/classic/{filename}"
        return classic_path
    
    def load_music(self, music_type, volume=None, force=False):
        if music_type.endswith('.mp3'):
            music_type = music_type[:-4]

        if not force and self.current_music_type == music_type and pygame.mixer.music.get_busy():
            if volume is not None and self.current_volume != volume:
                pygame.mixer.music.set_volume(volume)
                self.current_volume = volume
            return True
        
        self.current_music_type = music_type
        if volume is not None:
            self.current_volume = volume
        
        track_path = self.get_random_track(music_type)
        
        if track_path and os.path.exists(track_path):
            try:
                pygame.mixer.music.load(track_path)
                if volume is not None:
                    pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)
                return True
            except Exception as e:
                print(f"ERROR loading music: {e}")
        
        return False
    
    def change_pack_and_reload(self, new_pack, music_type, volume=None):
        old_pack = get_music_pack()
        from settings_manager import update_settings
        update_settings(music_pack=new_pack)
        
        self.load_music(music_type, volume, force=True)
        
        return old_pack
    
    def load_sound(self, filename):
        path = self.get_sound_path(filename)
        try:
            if os.path.exists(path):
                return pygame.mixer.Sound(path)
            else:
                return self._create_dummy_sound()
        except Exception as e:
            print(f"ERROR loading sound {path}: {e}")
            return self._create_dummy_sound()
    
    def _create_dummy_sound(self):
        try:
            dummy = pygame.mixer.Sound(buffer=bytes(100))
            dummy.set_volume(0)
            return dummy
        except:
            return None

_global_music_manager = None

def get_music_manager():
    global _global_music_manager
    if _global_music_manager is None:
        _global_music_manager = MusicManager()
    return _global_music_manager