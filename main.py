import pygame
import sys
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from game.game_manager import GameManager

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    game_manager = GameManager(screen)
    
    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game_manager.handle_event(event)

        # 2. Update
        game_manager.update()

        # 3. Draw
        # screen.fill handled in game_manager.draw()
        game_manager.draw()
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
