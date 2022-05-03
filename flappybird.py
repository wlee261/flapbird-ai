import random
import sys
import pygame
from pygame.locals import *
import os
import neat
import time
import pickle

pygame.font.init()

window_width = 600
window_height = 800

window = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)     
max_vel = 16
FLOOR = 730
MENU_FONT = pygame.font.SysFont("comicsans", 25)
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)


MODE = 0
WIN = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Flappy Bird")

gen = 0
OBSTACLE_VEL = 5

tpipe_image = pygame.transform.scale2x(pygame.image.load(os.path.join("images","topPipe.png")).convert_alpha())
bpipe_image = pygame.transform.scale2x(pygame.image.load(os.path.join("images","bottomPipe.png")).convert_alpha())
bg_image = pygame.transform.scale(pygame.image.load(os.path.join("images","bg.png")).convert_alpha(), (600, 900))
bird_image = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird1.png")).convert_alpha())
base_image = pygame.transform.scale2x(pygame.image.load(os.path.join("images","base.png")).convert_alpha())

class Bird:
    def __init__ (self, x, y):
        self.x = x
        self.y = y
        self.vel = 0
        self.height = self.y
        self.t = 0
        self.birdSprite = bird_image

    def draw(self, win):
        win.blit(self.birdSprite, (self.x, self.y))
    
    def draw2P(self, win):
        win.blit(self.birdSprite, (self.x+window_width, self.y))
    
    def jump(self):
        self.vel = -10.5
        self.height = self.y
        self.t = 0

    def get_mask(self):
        return pygame.mask.from_surface(self.birdSprite)

    def move(self):
        self.t += 1

        displacement = self.vel*self.t + 1.5*(self.t)**2


        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16

        self.y = self.y + displacement


class Pipe:
    GAP = 200
    def __init__(self, x):
        self.x = x
        self.height = self.setHeight()
        self.topPipe = tpipe_image
        self.bottomPipe = bpipe_image
        self.top = self.height - self.topPipe.get_height()
        self.bottom = self.height + self.GAP
        self.passed = False

    def setHeight(self):
        return random.randrange(50, 450)

    def move(self):
        self.x -= OBSTACLE_VEL

    def draw(self, win):
        win.blit(self.topPipe, (self.x, self.top))
        win.blit(self.bottomPipe, (self.x, self.bottom))
    
    def draw2P(self, win):
        win.blit(self.topPipe, (self.x+window_width, self.top))
        win.blit(self.bottomPipe, (self.x+window_width, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.topPipe)
        bottom_mask = pygame.mask.from_surface(self.bottomPipe)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask,top_offset)

        if b_point or t_point:
            return True

        return False

class Base:
    WIDTH = base_image.get_width()
    IMG = base_image

    def __init__(self, y):
        self.y = y
        self.x1 = 0 
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= OBSTACLE_VEL
        self.x2 -= OBSTACLE_VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

    def draw2P(self, win):
        win.blit(self.IMG, (self.x1+window_width, self.y))
        win.blit(self.IMG, (self.x2+window_width, self.y))

def draw_window(win, birds, pipes, base, score, gen, pipe_ind, player=None):
    if gen == 0:
        gen = 1
    win.blit(bg_image, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        bird.draw(win)
    if player:
        player.draw(win)

    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (window_width - score_label.get_width() - 15, 10))

    score_label = STAT_FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))

    score_label = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50))

    pygame.display.update()

def draw_window2P(win, birds, pipes, base, score, gen, pipe_ind, player):
    win.blit(bg_image, (0,0))
    win.blit(bg_image, (window_width, 0))

    pygame.draw.line(WIN, (0, 0, 0), (window_width, 0), (window_width, window_height), width=10) 

    for pipe in pipes:
        pipe.draw(win)
        pipe.draw2P(win)

    base.draw(win)
    base.draw2P(win)

    for bird in birds:
        bird.draw2P(win)

    if player:
        player.draw(win)

    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (window_width - score_label.get_width() - 15, 10))

    pygame.display.update()


def eval_genomes(genomes, config):
    global WIN, gen, OBSTACLE_VEL
    global window_width, window_height
    win = WIN
    gen += 1

    nets = []
    birds = []
    if MODE:
        player = Bird(230, 350)
        window_width_2P = window_width*2
        WIN = pygame.display.set_mode((window_width_2P, window_height), pygame.RESIZABLE) 
        
    ge = []
    if MODE == 1:
        nets.append(pickle.load(open("medium.pickle", "rb")))
        birds.append(Bird(230, 350))
    if MODE == 2:
        nets.append(pickle.load(open("hard.pickle", "rb")))
        birds.append(Bird(230, 350))
    if MODE == 3:
        nets.append(pickle.load(open("best.pickle", "rb")))
        birds.append(Bird(230, 350))
    if not MODE:
        for _, genome in genomes:
            genome.fitness = 0
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            nets.append(net)
            birds.append(Bird(230,350))
            ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and (len(birds) > 0 or MODE):
        clock.tick(50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                player.jump()
                

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].topPipe.get_width():
                pipe_ind = 1

        for x, bird in enumerate(birds):
            if not MODE:
                ge[x].fitness += 0.1
            bird.move()

            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        base.move()
        if MODE:
            player.move()


        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            if MODE:
                if pipe.collide(player):
                    quit()
            for bird in birds:
                if pipe.collide(bird):
                    if not MODE:
                        ge[birds.index(bird)].fitness -= 1
                        if genome.fitness > 120 and genome.fitness < 160:
                            pickle.dump(nets[birds.index(bird)], open("medium.pickle", "wb"))
                        if genome.fitness > 160 and genome.fitness < 300:
                            pickle.dump(nets[birds.index(bird)], open("hard.pickle", "wb")) 
                        ge.pop(birds.index(bird))
                    nets.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            if pipe.x + pipe.topPipe.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        if add_pipe:
            score += 1
            if OBSTACLE_VEL < 20:
                OBSTACLE_VEL += 0.1
            if not MODE:
                for genome in ge:
                    genome.fitness += 5

            pipes.append(Pipe(window_width))

        for r in rem:
            pipes.remove(r)
        if MODE:
            if player.y + player.birdSprite.get_height() - 10 >= FLOOR or player.y < -50:
                quit()
        for bird in birds:
            if bird.y + bird.birdSprite.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                if not MODE:
                    ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))
        if MODE:
            draw_window2P(WIN, birds, pipes, base, score, gen, pipe_ind, player)
        else:
            draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)
        
        if not MODE:
            if score > 30:
                pickle.dump(nets[0],open("best.pickle", "wb"))


def run(config_file):
    global WIN, MODE
    win = WIN

    runMenu = True
    x = 200
    y_coord = [200, 300, 400, 500]
    offset = [35, 35, 55, 15]
    w = 200
    h = 40
    text = ['Train Birds', 'Medium AI', 'Hard AI', 'Impossible AI']
    win.blit(bg_image, (0,0))

    for i, y in enumerate(y_coord):
        pygame.draw.rect(win, (255,255,255), (x, y, w, h))
        win.blit(MENU_FONT.render(text[i], True, (0,0,0)), (x+offset[i], y))

    while runMenu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            pygame.display.update()
            pos = pygame.mouse.get_pos()
            click = pygame.mouse.get_pressed()
        for i, y in enumerate(y_coord):
            if pos[0] > x and pos[0] < x + w and pos[1] > y and pos[1] < y + h:
                if click[0] == 1:
                    runMenu = False
                    MODE = i
       
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                        neat.DefaultSpeciesSet, neat.DefaultStagnation,
                        config_file)


    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(eval_genomes, 50)

    print('\nBest genome:\n{!s}'.format(winner))
    


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
