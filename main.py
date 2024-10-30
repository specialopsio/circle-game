import pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

from src.game import Game

if __name__ == "__main__":
    game = Game()
    game.run() 