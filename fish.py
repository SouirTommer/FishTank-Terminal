import math
import os
import random
import sys
import time

try:
    import msvcrt
    IS_WIN = True
except ImportError:
    import select
    import termios
    import tty
    IS_WIN = False

TICK = 0.05
MAX_FOOD = 20
MAX_BUBBLE = 40
BORDER = 240
PLANT = 34
BUBBLE = 51
FOODC = 226
SANDC = 238
FISH_COLORS = (196, 51, 214, 226, 45, 208)
FISH_NAMES = ('Bubbles', 'Fin', 'Nemo', 'Coral', 'Pearl', 'Marlin',
              'Dory', 'Flipper', 'Splash', 'Wanda', 'Sushi', 'Jaws',
              'Goldie', 'Poseidon', 'Neptune', 'Kraken', 'Salmon',
              'Triton', 'Caspian', 'Gill')
PALETTES = (
    (BORDER, SANDC, PLANT, BUBBLE, FOODC),
    (24, 110, 29, 81, 220),
    (214, 222, 100, 209, 208),
    (237, 246, 28, 81, 226),
)
HUNGRY_MAX = 100
HUNGRY_DRAIN = 0.06
HUNGRY_FEED = 15


class Fish:
    def __init__(self, x, y, vx, vy, size, color, name):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.size = size
        self.color = color
        self.name = name
        self.eaten = 0
        self.speed = random.uniform(0.8, 1.3)
        self.greed = random.uniform(0.5, 1.0)
        self.hist = []
        self.face = 1 if vx >= 0 else -1

    def sprite(self):
        n = 2 + self.size
        if self.face > 0:
            return '><' + '(' * n + "'" + '>'
        return '<' + ')' * n + "'" + '<'

    def ai_step(self, game):
        target = game.nearest_food(self)
        if target is not None:
            dx = target.x - self.x
            dy = target.y - self.y
            d = math.hypot(dx, dy)
            if d < 15 / self.greed:
                speed = 0.6 * self.speed
                self.vx += (dx / d * speed - self.vx) * 0.2 * self.greed
                self.vy += (dy / d * speed - self.vy) * 0.2 * self.greed
        else:
            if random.random() < 0.01:
                self.vx = -self.vx
            if random.random() < 0.03:
                self.vy += (random.uniform(-0.12, 0.12) - self.vy) * 0.05
        self.x += self.vx
        self.y += self.vy
        half = len(self.sprite()) // 2
        if self.x < 1 + half:
            self.x = 1 + half
            self.vx = abs(self.vx)
        if self.x > game.W - 2 - half:
            self.x = game.W - 2 - half
            self.vx = -abs(self.vx)
        if self.y < 4.0:
            self.y = 4.0
            self.vy = abs(self.vy)
        if self.y > game.H - 3.5:
            self.y = game.H - 3.5
            self.vy = -abs(self.vy)
        self.face = 1 if self.vx > 0 else -1
        self.hist.append((self.x, self.y))
        self.hist = self.hist[-3:]


class Bubble:
    def __init__(self, x, y, splash=False):
        self.x, self.y = x, y
        self.phase = random.uniform(0, math.tau)
        self.splash = splash

    def step(self, game):
        self.y -= 0.3
        self.x += 0.2 * math.sin(self.phase + game.gtime * 4)
        return self.y >= 1.6


class Food:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.rest = False

    def step(self, game):
        if not self.rest:
            self.y += 0.25
            self.x += 0.05 * math.sin(self.x * 0.5)
            self.x = max(1.0, min(game.W - 2, self.x))
            if self.y >= game.H - 3.2:
                self.y = game.H - 3.2
                self.rest = True


class Plant:
    def __init__(self, x, h, phase):
        self.x, self.h, self.phase = x, h, phase


class Game:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.gtime = 0.0
        self.score = 0
        self.running = True
        self.show_bubbles = True
        self.show_names = True
        self.auto = False
        self.pal = 0
        self.hungry = HUNGRY_MAX
        self.death_msg = 0.0
        self.bubbles = []
        self.foods = []
        self.fishes = []
        for i, c in enumerate(FISH_COLORS):
            vx = 0.35 if i % 2 == 0 else -0.35
            self.fishes.append(Fish(random.uniform(6, W - 8),
                                    random.uniform(3, H - 5),
                                    vx, 0.0, random.randint(1, 3), c,
                                    FISH_NAMES[i % len(FISH_NAMES)]))
        self.plants = []
        xs = []
        while len(xs) < min(8, (W - 6) // 7):
            x = random.randint(3, W - 4)
            if all(abs(x - p) >= 5 for p in xs):
                xs.append(x)
        self.plants = [Plant(x, random.randint(3, 6), random.uniform(0, math.tau))
                       for x in xs]
        self.sand = [' '] * W
        for x in range(1, W - 1):
            self.sand[x] = '▓' if random.random() < 0.55 else ' '

    def mmss(self):
        t = int(self.gtime)
        return '%02d:%02d' % (t // 60, t % 60)

    def poll_input(self):
        for ch in read_keys():
            if ch == b'\x1b':
                self.running = False
                return
            if ch in (b'c', b'C'):
                self.show_bubbles = not self.show_bubbles
            elif ch in (b'n', b'N'):
                self.show_names = not self.show_names
            elif ch in (b't', b'T'):
                self.pal = (self.pal + 1) % len(PALETTES)
            elif ch in (b'v', b'V'):
                self.auto = not self.auto
            elif ch == b' ':
                self.drop_food()
            elif ch in (b'+', b'='):
                self.add_fish()
            elif ch == b'-':
                self.remove_fish()

    def drop_food(self):
        if len(self.foods) < MAX_FOOD:
            self.foods.append(Food(random.uniform(2, self.W - 3), 3.0))

    def add_fish(self):
        i = len(self.fishes)
        vx = 0.35 if i % 2 == 0 else -0.35
        self.fishes.append(Fish(random.uniform(6, self.W - 8),
                                random.uniform(3, self.H - 5),
                                vx, 0.0, random.randint(1, 3),
                                FISH_COLORS[i % len(FISH_COLORS)],
                                FISH_NAMES[i % len(FISH_NAMES)]))

    def remove_fish(self):
        if self.fishes:
            self.fishes.pop()

    def nearest_food(self, fish):
        best = None
        best_d = 1e9
        for fo in self.foods:
            d = (fo.x - fish.x) ** 2 + (fo.y - fish.y) ** 2
            if d < best_d:
                best_d = d
                best = fo
        return best

    def step(self):
        self.gtime += TICK
        for f in self.fishes:
            f.ai_step(self)

        self.bubbles = [b for b in self.bubbles if b.step(self)]
        if self.show_bubbles and random.random() < 0.12 and len(self.bubbles) < MAX_BUBBLE:
            self.bubbles.append(Bubble(random.uniform(2, self.W - 3), self.H - 3))

        for fo in self.foods:
            fo.step(self)

        for f in self.fishes:
            for fo in self.foods:
                if abs(f.x - fo.x) < 1.6 and abs(f.y - fo.y) < 1.0:
                    self.foods.remove(fo)
                    self.score += 1
                    f.eaten += 1
                    self.hungry = min(HUNGRY_MAX, self.hungry + HUNGRY_FEED)
                    self.bubbles += [Bubble(fo.x, fo.y, True) for _ in range(3)]
                    self.bubbles = self.bubbles[-MAX_BUBBLE:]
                    break

        if self.auto:
            if len(self.foods) < 4:
                self.drop_food()
        else:
            self.hungry -= HUNGRY_DRAIN
            if self.hungry <= 0:
                if self.fishes:
                    self.fishes.pop()
                    self.death_msg = 3.0
                self.hungry = HUNGRY_MAX
        if self.death_msg > 0:
            self.death_msg -= TICK

    def run(self):
        last = time.monotonic()
        acc = 0.0
        while self.running:
            now = time.monotonic()
            acc += now - last
            last = now
            self.poll_input()
            while acc >= TICK:
                self.step()
                acc -= TICK
            if not self.running:
                break
            self.render()
            time.sleep(0.02)

    def render(self):
        W, H = self.W, self.H
        bcol, scol, pcol, bucol, fcol = PALETTES[self.pal]
        grid = [[(' ', None, False)] * W for _ in range(H)]

        text = 'FISH TANK | SCORE:%d | TIME:%s' % (self.score, self.mmss())
        if self.auto:
            text = 'WATCH | ' + text
        if self.death_msg > 0:
            text += ' | A fish died!'
        for i, ch in enumerate(text[:W]):
            grid[0][i] = (ch, 0, True)

        for x in range(1, W - 1):
            grid[1][x] = ('═', bcol, False)
            grid[H - 1][x] = ('═', bcol, False)
        grid[1][0] = ('╔', bcol, False)
        grid[1][W - 1] = ('╗', bcol, False)
        grid[H - 1][0] = ('╚', bcol, False)
        grid[H - 1][W - 1] = ('╝', bcol, False)
        for y in range(2, H - 1):
            grid[y][0] = ('║', bcol, False)
            grid[y][W - 1] = ('║', bcol, False)

        for x in range(1, W - 1):
            grid[H - 2][x] = (self.sand[x], scol, False)

        for pl in self.plants:
            base = H - 2
            for h in range(1, pl.h):
                grid[base - h][pl.x] = ('|', pcol, False)
            sway = int(round(0.6 * math.sin(self.gtime + pl.phase)))
            grid[base - pl.h][pl.x + sway] = ('~', pcol, False)

        for b in self.bubbles:
            if self.show_bubbles or b.splash:
                grid[int(round(b.y))][int(round(b.x))] = ('o', bucol, False)

        for fo in self.foods:
            grid[int(round(fo.y))][int(round(fo.x))] = ('*', fcol, False)

        for f in self.fishes:
            for k, (hx, hy) in enumerate(f.hist[:-1]):
                row = int(round(hy))
                gx = int(round(hx))
                if 3 <= row <= self.H - 3 and 1 <= gx <= self.W - 2:
                    grid[row][gx] = ('.', 232 + k * 3, False)
        for f in self.fishes:
            self.draw_fish(grid, f)

        if self.show_names:
            for f in self.fishes:
                name = f.name
                row = int(round(f.y)) - 1
                left = int(round(f.x)) - len(name) // 2
                if 3 <= row <= self.H - 3:
                    for i, ch in enumerate(name):
                        gx = left + i
                        if 1 <= gx <= self.W - 2:
                            grid[row][gx] = (ch, 250, False)

        n = int(self.hungry / HUNGRY_MAX * 10)
        controls = '[SPC]feed [+]/-fish [N]names [C]bub [T]theme [V]watch  HUNGRY:%s' % (
            '#' * n + '-' * (10 - n))
        for i, ch in enumerate(controls[:W]):
            grid[2][i] = (ch, 250, False)

        out = ['\x1b[H']
        for y in range(H):
            out.append(self.row_str(grid[y]) + '\x1b[0m')
        sys.stdout.write('\r\n'.join(out))
        sys.stdout.flush()

    def draw_fish(self, grid, f):
        s = f.sprite()
        L = len(s)
        row = int(round(f.y))
        left = int(round(f.x)) - L // 2
        if 3 <= row <= self.H - 3:
            for i, ch in enumerate(s):
                gx = left + i
                if 1 <= gx <= self.W - 2:
                    grid[row][gx] = (ch, f.color, False)

    def row_str(self, cells):
        parts = []
        cur = None
        for ch, fg, rev in cells:
            sig = (fg, rev)
            if sig != cur:
                parts.append('\x1b[0m')
                if fg is not None:
                    parts.append('\x1b[38;5;%dm' % fg)
                if rev:
                    parts.append('\x1b[7m')
                cur = sig
            parts.append(ch)
        return ''.join(parts)


def setup_input():
    if IS_WIN:
        return None
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    return old


def restore_input(old):
    if old is not None:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)


def read_keys():
    keys = []
    if IS_WIN:
        while msvcrt.kbhit():
            keys.append(msvcrt.getch())
    else:
        while select.select([sys.stdin], [], [], 0)[0]:
            b = sys.stdin.buffer.read(1)
            if b == b'\x1b':
                if select.select([sys.stdin], [], [], 0)[0]:
                    continue
                keys.append(b)
            elif b in (b'c', b'C', b'n', b'N', b't', b'T', b' ', b'+', b'=', b'-'):
                keys.append(b)
    return keys


def main():
    if IS_WIN:
        os.system('')
    try:
        W, H = os.get_terminal_size()
    except OSError:
        W, H = 80, 24
    if W < 30 or H < 12:
        print('Terminal too small, need at least 30x12')
        return
    game = Game(W, H)
    old = setup_input()
    sys.stdout.write('\x1b[?1049h\x1b[?25l')
    try:
        game.run()
    finally:
        sys.stdout.write('\x1b[0m\x1b[?25h\x1b[?1049l\n')
        sys.stdout.flush()
        restore_input(old)


if __name__ == '__main__':
    main()
