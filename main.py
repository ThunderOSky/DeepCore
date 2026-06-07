import pygame
from db_manager import init_db
from auth import auth as auth_main
from splash import SplashScreen
from theme import set_theme
from settings_manager import load_settings
from db_manager import check_and_auto_backup

def main():
    pygame.init()
    
    settings = load_settings()
    theme_name = settings.get('theme', 'light')
    set_theme(theme_name)
    
    width = settings.get('width', 1366)
    height = settings.get('height', 768)
    fullscreen = settings.get('is_fullscreen', False)
     
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    
    pygame.display.set_caption('DeepCore')
    
    splash = SplashScreen(screen)
    clock = pygame.time.Clock()
    
    running = True
    while running and not splash.is_done():
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        splash.update(dt)
        splash.draw()
        pygame.display.flip()
    
    if running:
        init_db()
        auth_main()
        check_and_auto_backup()

if __name__ == "__main__":
    main()