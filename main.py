import pygame
import sys
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from game.game import Game


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    game = Game(screen)

    running = True
    while running:
        # 1. Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.process_events(event)

        # 2. Update logic
        game.run_logic()

        # 3. Draw
        game.display_frame(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
