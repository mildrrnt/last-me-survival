from game.game import Game


class GameManager(Game):
    """Backward-compatible adapter for legacy entry points."""

    def handle_event(self, event):
        self.process_events(event)

    def update(self):
        self.run_logic()

    def draw(self):
        self.display_frame(self.screen)
