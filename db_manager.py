import sqlite3
import json
import shutil
import os
from datetime import datetime
from hash_utils import *
import random
import string
import sys, subprocess

conn = sqlite3.connect('database/game.db')
c = conn.cursor()

def init_db():
    create_tables()
    create_settings_table()
    create_admins_table()
    migrate_saved_games_table()
    add_experience_column()
    add_nickname_color_column()
    create_achievements_tables()
    create_unlocked_colors_table()
    create_showcase_table()
    init_achievements()
    add_win_streak_column()
    create_daily_tables()
    create_difficulty_tables()
    migrate_passwords()
    create_default_admin()

def create_difficulty_tables():
    c.execute(f'''CREATE TABLE IF NOT EXISTS complete_games
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    time REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    print("Difficulty tables created successfully")

def create_tables():
    c.execute('''CREATE TABLE IF NOT EXISTS user
                 (id INTEGER PRIMARY KEY, 
                  name TEXT UNIQUE, 
                  pass TEXT, 
                  games INTEGER DEFAULT 0, 
                  wins INTEGER DEFAULT 0, 
                  lvl INTEGER DEFAULT 1,
                  experience INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings
                 (user TEXT PRIMARY KEY,
                  music REAL DEFAULT 0.5,
                  sound REAL DEFAULT 0.5,
                  theme TEXT DEFAULT 'light',
                  FOREIGN KEY (user) REFERENCES user(name) ON DELETE CASCADE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS saved_games
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user TEXT NOT NULL,
                  game_type TEXT NOT NULL,
                  difficulty TEXT NOT NULL,
                  rows INTEGER NOT NULL,
                  cols INTEGER NOT NULL,
                  mines INTEGER NOT NULL,
                  board TEXT NOT NULL,
                  revealed TEXT NOT NULL,
                  flagged TEXT NOT NULL,
                  elapsed_time REAL DEFAULT 0,
                  start_time REAL,
                  total_pause_time REAL DEFAULT 0,
                  first_click INTEGER DEFAULT 1,
                  mines_left INTEGER,
                  last_move_time REAL DEFAULT 0,
                  moving_mines INTEGER DEFAULT 0,
                  move_direction TEXT,
                  move_progress REAL DEFAULT 0,
                  move_start_positions TEXT,
                  move_end_positions TEXT,
                  time_limit REAL,
                  time_penalty REAL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user) REFERENCES user(name) ON DELETE CASCADE)''')
    
    conn.commit()

def create_default_admin():
    from hash_utils import hash_password

    c.execute('SELECT COUNT(*) FROM admins')
    count = c.fetchone()[0]
    
    if count == 0:
        hashed_password = hash_password("admin")
        c.execute('INSERT INTO admins (user, password) VALUES (?, ?)', ("admin", hashed_password))
        conn.commit()
        print("Default admin account created: admin / admin")

        c.execute('SELECT COUNT(*) FROM user WHERE name = ?', ("admin",))
        user_exists = c.fetchone()[0]
        if not user_exists:
            c.execute('INSERT INTO user (id, name, pass, games, wins, lvl) VALUES (?, ?, ?, 0, 0, 1)', 
                     (1, "admin", hashed_password))
            conn.commit()

def migrate_saved_games_table():
    try:
        c.execute('ALTER TABLE saved_games ADD COLUMN game_over INTEGER DEFAULT 0')
        print("Added column game_over")
    except sqlite3.OperationalError:
        pass
    
    try:
        c.execute('ALTER TABLE saved_games ADD COLUMN game_won INTEGER DEFAULT 0')
        print("Added column game_won")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()

def create_settings_table():
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (user TEXT PRIMARY KEY,
                  music REAL DEFAULT 0.5,
                  sound REAL DEFAULT 0.5,
                  theme TEXT DEFAULT 'light')''')
    conn.commit()

def save_game_state(user, game):
    board_json = json.dumps(game.board)
    revealed_json = json.dumps(game.revealed)
    flagged_json = json.dumps(game.flagged)
    
    current_elapsed_time = game.get_elapsed_time()
    
    move_start_positions_json = json.dumps(game.move_start_positions) if hasattr(game, 'move_start_positions') else None
    move_end_positions_json = json.dumps(game.move_end_positions) if hasattr(game, 'move_end_positions') else None
    move_direction_json = json.dumps(game.move_direction) if hasattr(game, 'move_direction') and game.move_direction else None
    
    delete_save_game(user)
    
    c.execute('''INSERT INTO saved_games 
                 (user, game_type, difficulty, rows, cols, mines, 
                  board, revealed, flagged, elapsed_time, start_time, 
                  total_pause_time, first_click, mines_left,
                  last_move_time, moving_mines, move_direction, 
                  move_progress, move_start_positions, move_end_positions,
                  time_limit, time_penalty, game_over, game_won)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (user, game.game_type, game.difficulty if hasattr(game, 'difficulty') else 'custom',
               game.rows, game.cols, game.mines,
               board_json, revealed_json, flagged_json,
               current_elapsed_time, game.start_time,
               game.total_pause_time, int(game.first_click), game.mines_left,
               getattr(game, 'last_move_time', 0), int(getattr(game, 'moving_mines', False)),
               move_direction_json, getattr(game, 'move_progress', 0),
               move_start_positions_json, move_end_positions_json,
               getattr(game, 'time_limit', None), getattr(game, 'time_penalty', None),
               int(game.game_over), int(game.game_won)))
    
    conn.commit()
    return True

def load_game_state(user):
    c.execute('''SELECT game_type, difficulty, rows, cols, mines,
                        board, revealed, flagged, elapsed_time, start_time,
                        total_pause_time, first_click, mines_left,
                        last_move_time, moving_mines, move_direction,
                        move_progress, move_start_positions, move_end_positions,
                        time_limit, time_penalty, game_over, game_won
                 FROM saved_games 
                 WHERE user = ? 
                 ORDER BY created_at DESC LIMIT 1''', (user,))
    
    result = c.fetchone()
    if not result:
        return None
    
    has_game_over = len(result) > 21
    
    return {
        'game_type': result[0],
        'difficulty': result[1],
        'rows': result[2],
        'cols': result[3],
        'mines': result[4],
        'board': json.loads(result[5]),
        'revealed': json.loads(result[6]),
        'flagged': json.loads(result[7]),
        'elapsed_time': result[8],
        'start_time': result[9],
        'total_pause_time': result[10],
        'first_click': bool(result[11]),
        'mines_left': result[12],
        'last_move_time': result[13] or 0,
        'moving_mines': bool(result[14]),
        'move_direction': json.loads(result[15]) if result[15] else None,
        'move_progress': result[16] or 0,
        'move_start_positions': json.loads(result[17]) if result[17] else [],
        'move_end_positions': json.loads(result[18]) if result[18] else [],
        'time_limit': result[19],
        'time_penalty': result[20],
        'game_over': bool(result[21]) if has_game_over and len(result) > 21 else False,
        'game_won': bool(result[22]) if has_game_over and len(result) > 22 else False
    }

def has_saved_game(user):
    c.execute('SELECT COUNT(*) FROM saved_games WHERE user = ?', (user,))
    count = c.fetchone()[0]
    return count > 0

def delete_save_game(user):
    c.execute('DELETE FROM saved_games WHERE user = ?', (user,))
    conn.commit()

def get_user_data():
    c.execute("SELECT * FROM user")
    new = c.fetchall()
    return {
        'logins': [i[1] for i in new],
        'passwords': [i[2] for i in new],
        'games': [i[3] for i in new],
        'wins': [i[4] for i in new],
        'lvls': [i[5] for i in new]
    }

def add_user(user_id, name, password):
    hashed_password = hash_password(password)
    c.execute("INSERT INTO user (id, name, pass, games, wins, lvl) VALUES (?, ?, ?, 0, 0, 1)", 
             (user_id, name, hashed_password))
    conn.commit()

def update_user_games(name, games):
    c.execute("UPDATE user SET games = ? WHERE name = ?", (games, name))
    conn.commit()

def update_user_wins(name, wins):
    c.execute("UPDATE user SET wins = ? WHERE name = ?", (wins, name))
    conn.commit()

def save_game_result(difficulty, name, game_type, elapsed_time):
    c.execute("INSERT INTO complete_games (name, type, difficulty, time) VALUES (?, ?, ?, ?)",
             (name, game_type, difficulty, elapsed_time))
    conn.commit()

def get_leaders(difficulty, mode='all'):
    if difficulty == 'all':
        if mode == 'all':
            c.execute("SELECT name, difficulty, type, time FROM complete_games ORDER BY time ASC LIMIT 9")
        else:
            c.execute("SELECT name, difficulty, type, time FROM complete_games WHERE type = ? ORDER BY time ASC LIMIT 9", (mode,))
    else:
        if mode == 'all':
            c.execute("SELECT name, difficulty, type, time FROM complete_games WHERE difficulty = ? ORDER BY time ASC LIMIT 9", (difficulty,))
        else:
            c.execute("SELECT name, difficulty, type, time FROM complete_games WHERE difficulty = ? AND type = ? ORDER BY time ASC LIMIT 9", (difficulty, mode))
    
    return [(row[0], row[1], row[2], row[3]) for row in c.fetchall()]

def create_admins_table():
    c.execute('''CREATE TABLE IF NOT EXISTS admins
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
    conn.commit()

create_admins_table()

def is_admin(user):
    c.execute('SELECT COUNT(*) FROM admins WHERE user = ?', (user,))
    return c.fetchone()[0] > 0

def add_admin(user, password):
    hashed_password = hash_password(password)
    try:
        c.execute('INSERT INTO admins (user, password) VALUES (?, ?)', (user, hashed_password))
        conn.commit()
        return True
    except:
        return False

def check_admin_credentials(user, password):
    c.execute('SELECT password FROM admins WHERE user = ?', (user,))
    result = c.fetchone()
    if result:
        stored_hash = result[0]
        return verify_password(password, stored_hash)
    return False

def get_admin_by_user(user):
    c.execute('SELECT * FROM admins WHERE user = ?', (user,))
    return c.fetchone()

def update_player_password(nickname, new_password):
    hashed_password = hash_password(new_password)
    c.execute('UPDATE user SET pass = ? WHERE name = ?', (hashed_password, nickname))
    conn.commit()
    return c.rowcount > 0

def check_user_credentials(username, password):
    c.execute('SELECT pass FROM user WHERE name = ?', (username,))
    result = c.fetchone()
    if result:
        stored_hash = result[0]
        return verify_password(password, stored_hash)
    return False

def update_player_nickname(old_nickname, new_nickname):
    try:
        c.execute('UPDATE user SET name = ? WHERE name = ?', (new_nickname, old_nickname))
        c.execute('UPDATE user_settings SET user = ? WHERE user = ?', (new_nickname, old_nickname))
        c.execute('UPDATE saved_games SET user = ? WHERE user = ?', (new_nickname, old_nickname))
        
        for diff in ['easy', 'average', 'hard', 'super']:
            try:
                c.execute(f'UPDATE {diff} SET name = ? WHERE name = ?', (new_nickname, old_nickname))
            except:
                pass
        conn.commit()
        return True
    except:
        return False

def delete_top_record(difficulty, name, time, game_type):
    c.execute('''DELETE FROM complete_games 
                 WHERE name = ? AND difficulty = ? AND time = ? AND type = ?''',
              (name, difficulty, time, game_type))
    conn.commit()
    return c.rowcount > 0

def update_top_record(difficulty, old_name, old_time, old_type, new_name, new_time, new_type):
    c.execute('''UPDATE complete_games 
                 SET name = ?, time = ?, type = ? 
                 WHERE name = ? AND difficulty = ? AND time = ? AND type = ?''',
              (new_name, new_time, new_type, old_name, difficulty, old_time, old_type))
    conn.commit()
    return c.rowcount > 0

def player_exists(nickname):
    c.execute('SELECT COUNT(*) FROM user WHERE name = ?', (nickname,))
    return c.fetchone()[0] > 0

def add_experience_column():
    try:
        c.execute('ALTER TABLE user ADD COLUMN experience INTEGER DEFAULT 0')
        print("Added column experience")
    except sqlite3.OperationalError:
        pass
    conn.commit()

def add_win_streak_column():
    try:
        c.execute('ALTER TABLE user ADD COLUMN win_streak INTEGER DEFAULT 0')
        print("Added column win_streak")
    except sqlite3.OperationalError:
        pass
    conn.commit()

def get_level_threshold(level):
    return 50 * level * level

def add_experience(username, amount):
    c.execute('SELECT lvl, experience FROM user WHERE name = ?', (username,))
    result = c.fetchone()
    if not result:
        return False
    
    current_level, current_exp = result
    new_exp = current_exp + amount
    new_level = current_level
    
    while new_exp >= get_level_threshold(new_level):
        new_exp -= get_level_threshold(new_level)
        new_level += 1
    
    c.execute('UPDATE user SET lvl = ?, experience = ? WHERE name = ?',
              (new_level, new_exp, username))
    conn.commit()
    
    return new_level > current_level

def get_player_level(username):
    c.execute('SELECT lvl, experience FROM user WHERE name = ?', (username,))
    result = c.fetchone()
    if result:
        return {
            'level': result[0],
            'experience': result[1],
            'next_level_exp': get_level_threshold(result[0])
        }
    return None

def add_game_experience(username, game_won, difficulty, game_type, time_elapsed):
    if difficulty == 'custom':
        return False
    
    if not game_won:
        base_exp = 5
        return add_experience(username, base_exp)
    
    difficulty_exp = {
        'easy': 10,
        'average': 25,
        'hard': 75,
        'super': 215
    }
    
    base_exp = difficulty_exp.get(difficulty, 10)
    
    mode_multiplier = {
        'classic': 1.0,
        'chronos': 1.5,
        'safari': 2.0
    }
    
    multiplier = mode_multiplier.get(game_type, 1.0)
    
    if time_elapsed > 0:
        if difficulty == 'easy':
            base_time = 60
        elif difficulty == 'average':
            base_time = 180
        elif difficulty == 'hard':
            base_time = 360
        elif difficulty == 'super':
            base_time = 600
        else:
            base_time = 180
        
        speed_bonus = max(0.5, min(3.0, base_time / time_elapsed))
        multiplier *= speed_bonus
    
    final_exp = int(base_exp * multiplier)
    
    return add_experience(username, final_exp)

def migrate_passwords():
    from hash_utils import hash_password
    
    c.execute('SELECT id, name, pass FROM user')
    users = c.fetchall()
    
    for user_id, name, password in users:
        if len(password) != 64 or not all(c in '0123456789abcdef' for c in password):
            hashed = hash_password(password)
            c.execute('UPDATE user SET pass = ? WHERE id = ?', (hashed, user_id))
    
    c.execute('SELECT id, user, password FROM admins')
    admins = c.fetchall()
    
    for admin_id, user, password in admins:
        if len(password) != 64 or not all(c in '0123456789abcdef' for c in password):
            hashed = hash_password(password)
            c.execute('UPDATE admins SET password = ? WHERE id = ?', (hashed, admin_id))
    
    conn.commit()
    print("Passwords migrated successfully")

def create_achievements_tables():
    c.execute('''CREATE TABLE IF NOT EXISTS achievements_list
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  description TEXT NOT NULL,
                  rarity TEXT NOT NULL,
                  secret INTEGER DEFAULT 0,
                  condition_type TEXT NOT NULL,
                  condition_value INTEGER DEFAULT 1,
                  exp_reward INTEGER DEFAULT 0,
                  color_reward TEXT DEFAULT NULL,
                  date_available TEXT,
                  date_expiry TEXT,
                  icon TEXT DEFAULT 'default')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS player_achievements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL,
                  achievement_id INTEGER NOT NULL,
                  unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (username) REFERENCES user(name) ON DELETE CASCADE,
                  FOREIGN KEY (achievement_id) REFERENCES achievements_list(id) ON DELETE CASCADE,
                  UNIQUE(username, achievement_id))''')
    
    conn.commit()

def create_unlocked_colors_table():
    c.execute('''CREATE TABLE IF NOT EXISTS unlocked_colors
                 (username TEXT NOT NULL,
                  color_name TEXT NOT NULL,
                  unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (username, color_name))''')
    conn.commit()

def init_achievements():
    c.execute('SELECT COUNT(*) FROM achievements_list')
    count = c.fetchone()[0]
    if count > 0:
        return
    
    achievements = [
        ('Первая игра', 'Завершите первую игру', 'common', 0, 'games_played', 1, 50, '#FF4444', None, None, 'gamepad'),
        ('Первая победа', 'Выиграйте первую игру', 'common', 0, 'games_won', 1, 75, '#4444FF', None, None, 'trophy'),
        ('Новичок', 'Сыграйте 10 игр', 'common', 0, 'games_played', 10, 60, '#44FF44', None, None, 'gamepad'),
        ('Любитель', 'Сыграйте 50 игр', 'common', 0, 'games_played', 50, 80, '#FFFF44', None, None, 'gamepad'),
        ('Победитель', 'Выиграйте 5 игр', 'common', 0, 'games_won', 5, 90, '#FF8844', None, None, 'trophy'),
        ('Сапёр-любитель', 'Выиграйте на лёгкой сложности', 'common', 0, 'win_easy', 1, 55, '#FF44FF', None, None, 'star'),
        ('Пять побед подряд', 'Выиграйте 5 игр подряд', 'common', 0, 'win_streak', 5, 100, '#44FFFF', None, None, 'fire'),
        ('Быстрый ум', 'Выиграйте игру быстрее чем за 30 секунд', 'common', 0, 'win_under_time', 30, 85, '#FF88CC', None, None, 'bolt'),
        ('Флагоносец', 'Поставьте 100 флагов', 'common', 0, 'flags_placed', 100, 70, '#CCCCCC', None, None, 'flag'),
        
        ('Охотник за рекордами', 'Попадите в топ-10 таблицы лидеров', 'rare', 0, 'top_10', 1, 400, '#CC0000', None, None, 'top'),
        ('Специалист по сложному', 'Выиграйте на сложном уровне', 'rare', 0, 'win_hard', 1, 500, '#0000CC', None, None, 'star'),
        ('Мастер сложности', 'Выиграйте на уровне Экстра', 'rare', 0, 'win_super', 1, 650, '#00CC00', None, None, 'star'),
        ('Хронос-мастер', 'Выиграйте в режиме Хронос', 'rare', 0, 'win_chronos', 1, 450, '#CCAA00', None, None, 'clock'),
        ('Сафари-мастер', 'Выиграйте в режиме Сафари', 'rare', 0, 'win_safari', 1, 550, '#C0C0C0', None, None, 'paw'),
        ('Стахановец', 'Сыграйте 200 игр', 'rare', 0, 'games_played', 200, 380, '#FF7F50', None, None, 'gamepad'),
        ('Коллекционер', 'Выиграйте на всех сложностях', 'rare', 0, 'win_all_difficulties', 4, 750, '#98FF98', None, None, 'medal'),
        ('Скоростной гонщик', 'Выиграйте игру быстрее чем за 15 секунд', 'rare', 0, 'win_under_time', 15, 600, '#E6E6FA', None, None, 'bolt'),
        ('Тактик', 'Выиграйте игру не поставив ни одного флага', 'rare', 0, 'win_no_flags', 1, 500, '#FFDAB9', None, None, 'brain'),
        
        ('Непобедимый', 'Выиграйте 100 игр', 'epic', 0, 'games_won', 100, 2000, 'emerald', None, None, 'trophy'),
        ('Ветеран', 'Сыграйте 500 игр', 'epic', 0, 'games_played', 500, 1800, '#87CEEB', None, None, 'gamepad'),
        ('Скоростной бегун', 'Выиграйте игру быстрее чем за 10 секунд', 'epic', 0, 'win_under_time', 10, 2500, 'neon', None, None, 'bolt'),
        ('Мастер всех режимов', 'Выиграйте во всех режимах на всех сложностях', 'epic', 0, 'win_all_modes_all_difficulties', 1, 3500, 'rainbow', None, None, 'crown'),
        ('Топ-3', 'Займите место в тройке лидеров', 'epic', 0, 'top_3', 1, 3000, 'gold', None, None, 'top'),
        ('Сапёр-маньяк', 'Сыграйте 1000 игр', 'epic', 0, 'games_played', 1000, 2800, 'fire', None, None, 'gamepad'),
        ('Идеальная игра', 'Выиграйте игру открыв всё поле кроме мин первым кликом', 'epic', 0, 'perfect_game', 1, 3200, None, None, None, 'magic'),
        ('Закладчик', 'Закройте всё поле флагами в сложности Экстра', 'epic', 0, 'all_flagged_super', 1, 3000, None, None, None, 'flag'),
        
        ('Бог сапёра', 'Выиграйте 500 игр', 'legendary', 0, 'games_won', 500, 8000, 'legendary_purple', None, None, 'trophy'),
        ('Топ-1', 'Займите первое место в таблице лидеров', 'legendary', 0, 'top_1', 1, 12000, 'gold', None, None, 'top'),
        ('Бессмертный', 'Выиграйте 1000 игр', 'legendary', 0, 'games_won', 1000, 15000, 'platinum', None, None, 'trophy'),
        ('Легенда', 'Наберите 100000 очков опыта', 'legendary', 0, 'total_exp', 100000, 10000, None, None, None, 'gem'),
        ('Мировой рекордсмен', 'Установите мировой рекорд на всех сложностях', 'legendary', 0, 'world_record_all', 1, 15000, 'space', None, None, 'globe'),
        
        ('Администратор', 'Получите права администратора', 'secret', 1, 'is_admin', 1, 0, 'hacker', None, None, 'shield'),
        ('Полуночник', 'Играйте в 3:00 ночи', 'secret', 1, 'play_at_night', 1, 0, 'ghost', None, None, 'moon'),
        
        ('Шутовской наряд', 'Играйте 1 апреля', 'limited', 1, 'play_april_fools', 1, 0, 'rainbow', '2025-04-01', '2025-04-02', 'jester'),
        ('Новогоднее чудо', 'Играйте 31 декабря', 'limited', 1, 'play_new_year', 1, 0, 'space', '2024-12-31', '2025-01-01', 'snowflake'),
        ('Хэллоуинский страх', 'Играйте 31 октября', 'limited', 1, 'play_halloween', 1, 0, 'fire', '2024-10-31', '2024-11-01', 'ghost'),
        ('День рождения игры', 'Играйте в день рождения игры', 'limited', 1, 'play_birthday', 1, 0, 'gold', '2025-06-15', '2025-06-16', 'cake'),
        ('Участник Champions 2026', 'Победите в Уровне-чемпионе во время Champions 2026', 'limited', 1, 'champions_2026_participant', 1, 0, 'neon', '2026-08-05', '2026-08-25', 'user2026'),
        ('Победитель Champions 2026', 'Наберите самое быстрое время в Уровне-чемпионе', 'limited', 1, 'champions_2026_winner', 1, 0, 'legendary_purple', '2026-08-05', '2026-08-25', 'winner2026'),
    ]
    
    for ach in achievements:
        try:
            c.execute('''INSERT INTO achievements_list 
                        (name, description, rarity, secret, condition_type, condition_value, 
                         exp_reward, color_reward, date_available, date_expiry, icon)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', ach)
        except Exception as e:
            print(f"Error adding achievement {ach[0]}: {e}")
    
    conn.commit()
    print("Achievements initialized successfully")

def check_achievement(username, condition_type, value=1):
    c.execute('''SELECT id, name, description, condition_value, exp_reward, color_reward, condition_type
                 FROM achievements_list 
                 WHERE condition_type = ? 
                 AND id NOT IN (
                     SELECT achievement_id FROM player_achievements WHERE username = ?
                 )''', (condition_type, username))
    
    available = c.fetchall()
    earned = []
    
    for achievement in available:
        ach_id, name, desc, cond_value, exp_reward, color_reward, cond_type = achievement
        should_award = False
        
        if cond_type in ['games_played', 'games_won', 'win_streak', 'flags_placed']:
            if value >= cond_value:
                should_award = True
        
        elif cond_type == 'win_under_time':
            if value <= cond_value:
                should_award = True
        
        elif cond_type in ['win_easy', 'win_hard', 'win_super', 'win_chronos', 'win_safari', 
                          'top_10', 'top_3', 'top_1', 'win_no_flags', 'perfect_game', 
                          'all_flagged_super', 'is_admin', 'champions_2026_participant', 
                          'champions_2026_winner', 'play_at_night', 'play_april_fools',
                          'play_new_year', 'play_halloween', 'play_birthday']:
            if value >= 1:
                should_award = True
        
        elif cond_type == 'win_all_difficulties':
            if value >= 4:
                should_award = True
        
        elif cond_type == 'win_all_modes_all_difficulties':
            c.execute('''SELECT COUNT(DISTINCT difficulty || "_" || type) FROM complete_games 
                        WHERE name = ?''', (username,))
            unique_combos = c.fetchone()[0]
            if unique_combos >= 12:
                should_award = True
        
        elif cond_type == 'world_record_all':
            world_records = 0
            for diff in ['easy', 'average', 'hard', 'super']:
                c.execute('''SELECT name FROM complete_games 
                            WHERE difficulty = ? 
                            ORDER BY time ASC LIMIT 1''', (diff,))
                first = c.fetchone()
                if first and first[0] == username:
                    world_records += 1
            if world_records >= 4:
                should_award = True
        
        elif cond_type == 'total_exp':
            if value >= cond_value:
                should_award = True
        
        if should_award:
            c.execute('INSERT OR IGNORE INTO player_achievements (username, achievement_id) VALUES (?, ?)',
                     (username, ach_id))
            conn.commit()
            
            if color_reward:
                c.execute('INSERT OR IGNORE INTO unlocked_colors (username, color_name) VALUES (?, ?)',
                         (username, color_reward))
                conn.commit()
            
            if exp_reward and exp_reward > 0:
                add_experience(username, exp_reward)
            
            earned.append({'name': name, 'description': desc, 'exp': exp_reward, 'color': color_reward})
    
    return earned

def get_player_achievements(username):
    c.execute('''SELECT a.id, a.name, a.description, a.rarity, a.secret, a.icon, p.unlocked_at
                 FROM achievements_list a
                 INNER JOIN player_achievements p ON a.id = p.achievement_id
                 WHERE p.username = ?
                 ORDER BY p.unlocked_at DESC''', (username,))
    return c.fetchall()

def get_all_achievements():
    c.execute('''SELECT id, name, description, rarity, secret, condition_type, condition_value, 
                 exp_reward, color_reward, date_available, date_expiry, icon 
                 FROM achievements_list ORDER BY 
              CASE rarity 
                  WHEN "common" THEN 1 
                  WHEN "rare" THEN 2 
                  WHEN "epic" THEN 3 
                  WHEN "legendary" THEN 4 
                  WHEN "secret" THEN 5 
                  WHEN "limited" THEN 6
              END''')
    return c.fetchall()

def add_nickname_color_column():
    try:
        c.execute('ALTER TABLE user ADD COLUMN nickname_color TEXT DEFAULT "default"')
        print("Added column nickname_color")
    except sqlite3.OperationalError:
        pass
    conn.commit()

def set_nickname_color(username, color):
    c.execute('UPDATE user SET nickname_color = ? WHERE name = ?', (color, username))
    conn.commit()

def get_nickname_color(username):
    c.execute('SELECT nickname_color FROM user WHERE name = ?', (username,))
    result = c.fetchone()
    if result and result[0]:
        return result[0]
    return "default"

def get_available_nickname_colors():
    return {
        "basic": {
            "Стандартный": "default",
            "Красный": "#FF4444",
            "Синий": "#4444FF",
            "Зелёный": "#44FF44",
            "Жёлтый": "#FFFF44",
            "Оранжевый": "#FF8844",
            "Фиолетовый": "#FF44FF",
            "Бирюзовый": "#44FFFF",
            "Розовый": "#FF88CC",
            "Серый": "#CCCCCC",
            "Тёмно-красный": "#CC0000",
            "Тёмно-синий": "#0000CC",
            "Тёмно-зелёный": "#00CC00",
            "Золотистый": "#CCAA00",
            "Серебряный": "#C0C0C0",
            "Коралловый": "#FF7F50",
            "Мятный": "#98FF98",
            "Лавандовый": "#E6E6FA",
            "Персиковый": "#FFDAB9",
            "Небесно-голубой": "#87CEEB"
        },
        "animated": {
            "Радужный": "rainbow",
            "Золотой": "gold",
            "Огненный": "fire",
            "Неоновый": "neon",
            "Космический": "space"
        },
        "achievement": {
            "Легендарный пурпур": "legendary_purple",
            "Платиновый": "platinum",
            "Изумрудный": "emerald",
            "Кровавый": "blood",
            "Призрачный": "ghost",
            "Хакерский": "hacker"
        }
    }

def get_unlocked_colors(username):
    unlocked = {
        "basic": ["Стандартный"],
        "animated": [],
        "achievement": []
    }
    
    c.execute('SELECT color_name FROM unlocked_colors WHERE username = ?', (username,))
    db_colors = c.fetchall()
    
    available_colors = get_available_nickname_colors()
    
    for color_row in db_colors:
        color_name = color_row[0]
        
        found = False
        
        for name, val in available_colors["basic"].items():
            if val == color_name or name == color_name:
                if name not in unlocked["basic"]:
                    unlocked["basic"].append(name)
                found = True
                break
        
        if found:
            continue
        
        for name, val in available_colors["animated"].items():
            if val == color_name or name == color_name:
                if name not in unlocked["animated"]:
                    unlocked["animated"].append(name)
                found = True
                break
        
        if found:
            continue
        
        for name, val in available_colors["achievement"].items():
            if val == color_name or name == color_name:
                if name not in unlocked["achievement"]:
                    unlocked["achievement"].append(name)
                found = True
                break
    
    return unlocked

def create_showcase_table():
    c.execute('''CREATE TABLE IF NOT EXISTS achievement_showcase
                 (username TEXT NOT NULL,
                  achievement_id INTEGER NOT NULL,
                  position INTEGER DEFAULT 0,
                  FOREIGN KEY (username) REFERENCES user(name) ON DELETE CASCADE,
                  FOREIGN KEY (achievement_id) REFERENCES achievements_list(id) ON DELETE CASCADE,
                  PRIMARY KEY (username, achievement_id))''')
    conn.commit()

def get_showcased_achievements(username):
    c.execute('SELECT achievement_id FROM achievement_showcase WHERE username = ? ORDER BY position', (username,))
    return [row[0] for row in c.fetchall()]

def toggle_showcased_achievement(username, achievement_id):
    showcased = get_showcased_achievements(username)
    
    if achievement_id in showcased:
        c.execute('DELETE FROM achievement_showcase WHERE username = ? AND achievement_id = ?', 
                 (username, achievement_id))
        remaining = get_showcased_achievements(username)
        for i, ach_id in enumerate(remaining):
            c.execute('UPDATE achievement_showcase SET position = ? WHERE username = ? AND achievement_id = ?',
                     (i, username, ach_id))
    else:
        if len(showcased) >= 5:
            return False
        c.execute('INSERT INTO achievement_showcase (username, achievement_id, position) VALUES (?, ?, ?)',
                 (username, achievement_id, len(showcased)))
    
    conn.commit()
    return True

def check_top_achievements(username):
    modes = ['classic', 'chronos', 'safari']
    
    for difficulty in ['easy', 'average', 'hard', 'super']:
        for mode in modes:
            c.execute('''SELECT name, time FROM complete_games 
                         WHERE difficulty = ? AND type = ? 
                         ORDER BY time ASC LIMIT 10''', (difficulty, mode))
            leaders = c.fetchall()
            
            for position, (name, time) in enumerate(leaders):
                if name == username:
                    position += 1
                    if position <= 10:
                        check_achievement(username, 'top_10', position)
                    if position <= 3:
                        check_achievement(username, 'top_3', position)
                    if position == 1:
                        check_achievement(username, 'top_1', position)
                    break
   
    conn.commit()
    print(f"Unlocked all achievements and colors for {username}")

def check_and_notify(username, condition_type, value=1):
    earned = check_achievement(username, condition_type, value)
    if earned:
        try:
            from notification_queue import add_pending
            for ach in earned:
                add_pending("Достижение", f'Вы получили достижение "{ach["name"]}"', "achievement")
        except:
            pass
    return earned

def get_win_streak(username):
    c.execute('SELECT win_streak FROM user WHERE name = ?', (username,))
    result = c.fetchone()
    if result:
        return result[0]
    return 0

def increment_win_streak(username):
    c.execute('UPDATE user SET win_streak = win_streak + 1 WHERE name = ?', (username,))
    conn.commit()
    streak = get_win_streak(username)
    check_and_notify(username, 'win_streak', streak)
    return streak

def reset_win_streak(username):
    c.execute('UPDATE user SET win_streak = 0 WHERE name = ?', (username,))
    conn.commit()


def create_daily_tables():
    
    c.execute('''CREATE TABLE IF NOT EXISTS daily_game
                 (date TEXT PRIMARY KEY,
                  seed TEXT NOT NULL,
                  rows INTEGER DEFAULT 12,
                  cols INTEGER DEFAULT 12,
                  mines INTEGER DEFAULT 20)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS daily_results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT NOT NULL,
                  username TEXT NOT NULL,
                  time REAL NOT NULL,
                  won INTEGER DEFAULT 0,
                  played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  UNIQUE(date, username))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS champion_season
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  season_name TEXT NOT NULL,
                  start_date TEXT NOT NULL,
                  end_date TEXT NOT NULL,
                  is_active INTEGER DEFAULT 0,
                  seed TEXT NOT NULL,
                  created_by TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()


def get_daily_game_seed(date_str=None):
    if date_str is None:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    c.execute('SELECT seed, rows, cols, mines FROM daily_game WHERE date = ?', (date_str,))
    return c.fetchone()


def generate_daily_game(date_str=None):
    if date_str is None:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    existing = get_daily_game_seed(date_str)
    if existing:
        return existing
    
    import hashlib
    seed = hashlib.md5(date_str.encode()).hexdigest()[:16]
    rows, cols, mines = 12, 12, 20
    
    c.execute('INSERT OR REPLACE INTO daily_game (date, seed, rows, cols, mines) VALUES (?, ?, ?, ?, ?)',
              (date_str, seed, rows, cols, mines))
    conn.commit()
    
    return (seed, rows, cols, mines)


def save_daily_result(username, date_str, time_elapsed, won):
    try:
        c.execute('''INSERT OR IGNORE INTO daily_results (date, username, time, won) 
                     VALUES (?, ?, ?, ?)''', (date_str, username, time_elapsed, int(won)))
        conn.commit()
        return True
    except:
        return False


def has_played_daily(username, date_str=None):
    if date_str is None:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    c.execute('SELECT COUNT(*) FROM daily_results WHERE date = ? AND username = ?', (date_str, username))
    return c.fetchone()[0] > 0


def get_daily_leaders(date_str=None):
    if date_str is None:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    c.execute('''SELECT username, time FROM daily_results 
                 WHERE date = ? AND won = 1 
                 ORDER BY time ASC LIMIT 100''', (date_str,))
    return c.fetchall()

def get_champion_leaders():
    season = get_active_season()
    if not season:
        return []
    
    c.execute('''SELECT username, time FROM daily_results 
                 WHERE date >= ? AND date <= ? AND won = 1 
                 ORDER BY time ASC LIMIT 100''', (season[2], season[3]))
    return c.fetchall()


def create_champion_season(season_name, start_date, end_date, created_by):
    import hashlib
    seed = hashlib.md5(f"{season_name}{start_date}{end_date}".encode()).hexdigest()[:16]
    
    c.execute('UPDATE champion_season SET is_active = 0')
    
    c.execute('''INSERT INTO champion_season (season_name, start_date, end_date, is_active, seed, created_by)
                 VALUES (?, ?, ?, 1, ?, ?)''', (season_name, start_date, end_date, seed, created_by))
    conn.commit()


def get_active_season():
    c.execute('SELECT * FROM champion_season WHERE is_active = 1 LIMIT 1')
    return c.fetchone()


def is_champion_season_active():
    season = get_active_season()
    if not season:
        return False

    return season[4] == 1

def end_season_and_award():
    season = get_active_season()
    if not season:
        return None
    
    c.execute('''SELECT username, time FROM daily_results 
                 WHERE date >= ? AND date <= ? AND won = 1 
                 ORDER BY time ASC LIMIT 1''', (season[2], season[3]))
    winner = c.fetchone()
    
    if winner:
        check_achievement(winner[0], 'champions_2026_winner', 1)
    
    c.execute('UPDATE champion_season SET is_active = 0 WHERE id = ?', (season[0],))
    
    c.execute('DELETE FROM daily_results WHERE date >= ? AND date <= ?', (season[2], season[3]))
    
    conn.commit()
    return winner

def force_refresh_daily():
    from datetime import datetime
    import hashlib
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if is_champion_season_active():
        season = get_active_season()
        if season:
            new_seed = hashlib.md5(f"{season[1]}_refresh_{today}".encode()).hexdigest()[:16]
            c.execute('UPDATE champion_season SET seed = ? WHERE id = ?', (new_seed, season[0]))
            c.execute('DELETE FROM daily_results')
    else:
        new_seed = hashlib.md5(f"refresh_{today}".encode()).hexdigest()[:16]
        c.execute('UPDATE daily_game SET seed = ? WHERE date = ?', (new_seed, today))
        c.execute('DELETE FROM daily_results WHERE date = ?', (today,))
    
    conn.commit()
    print("Daily game refreshed")

def check_time_achievements(username):
    now = datetime.now()
    
    if now.hour == 3 and now.minute == 0:
        check_and_notify(username, 'play_at_night', 1)
    
    if now.month == 4 and now.day == 1:
        check_and_notify(username, 'play_april_fools', 1)
    
    if now.month == 12 and now.day == 31:
        check_and_notify(username, 'play_new_year', 1)
    
    if now.month == 10 and now.day == 31:
        check_and_notify(username, 'play_halloween', 1)
    
    if now.month == 6 and now.day == 15:
        check_and_notify(username, 'play_birthday', 1)

def backup_database():
    backup_dir = "database/backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_dir}/game_backup_{timestamp}.db"
    
    try:
        shutil.copy2("database/game.db", backup_path)

        settings = {}
        settings_file = "database/backup_settings.json"
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        
        settings['last_backup'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        settings['last_backup_path'] = backup_path
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        
        return True, backup_path
    except Exception as e:
        print(f"Backup error: {e}")
        return False, None

def get_last_backup_info():
    settings_file = "database/backup_settings.json"
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get('last_backup', 'Никогда'), settings.get('last_backup_path', '')
    return 'Никогда', ''

def save_backup_settings(interval_days):
    settings_file = "database/backup_settings.json"
    settings = {}
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    
    settings['backup_interval'] = interval_days
    settings['last_backup_check'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def get_backup_interval():
    settings_file = "database/backup_settings.json"
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get('backup_interval', 7)
    return 7

def check_and_auto_backup():
    interval = get_backup_interval()
    if interval == 0 or interval == "Выкл":
        return
    
    settings_file = "database/backup_settings.json"
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            last_check = settings.get('last_backup_check')
            if last_check:
                last_date = datetime.strptime(last_check, "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                days_diff = (now - last_date).days
                if days_diff >= interval:
                    backup_database()
                    save_backup_settings(interval)

def generate_daily_secret_key():
    import random
    import string
    from datetime import datetime
    
    today = datetime.now().strftime("%Y-%m-%d")

    random.seed(today)

    chars = string.ascii_uppercase + string.digits
    key = ''.join(random.choice(chars) for _ in range(10))

    random.seed()

    return key

def verify_secret_key(key):
    valid = key == generate_daily_secret_key()
    print(f"DEBUG: verify_secret_key('{key}') = {valid}") 
    return valid