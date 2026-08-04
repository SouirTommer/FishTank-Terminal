import math
import os
import random
import sys
import time

try:
    import msvcrt
except ImportError:
    print('This program needs a Windows console (msvcrt)')
    raise SystemExit(1)

TICK = 0.05
MAX_FOOD = 20
MAX_BUBBLE = 40
BORDER = 240
PLANT = 34
BUBBLE = 51
FOODC = 226
SANDC = 238


class Fish:
    def __init__(self, x, y, vx, vy, size, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.size = size
        self.color = color
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
            if d < 15:
                speed = 0.6
                self.vx += (dx / d * speed - self.vx) * 0.2
                self.vy += (dy / d * speed - self.vy) * 0.2
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
        if self.y < 2.5:
            self.y = 2.5
            self.vy = abs(self.vy)
        if self.y > game.H - 3.5:
            self.y = game.H - 3.5
            self.vy = -abs(self.vy)
        self.face = 1 if self.vx > 0 else -1


class Bubble:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.phase = random.uniform(0, math.tau)

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
        self.paused = False
        self.bubbles = []
        self.foods = []
        self.fishes = []
        for i, c in enumerate((196, 51, 214, 226)):
            vx = 0.35 if i % 2 == 0 else -0.35
            self.fishes.append(Fish(random.uniform(6, W - 8),
                                    random.uniform(3, H - 5),
                                    vx, 0.0, random.randint(1, 3), c))
        self.plants = []
        xs = []
        while len(xs) < min(8, (W - 6) // 7):
            x = random.randint(3, W - 4)
            if all(abs(x - p) >= 5 for p in xs):
                xs.append(x)
        self.plants = [Plant(x, random.randint(3, 6), random.uniform(0, math.tau))
                       for x in xs]
        self.sand = [(' ', None, False)] * W
        for x in range(1, W - 1):
            self.sand[x] = ('▓', SANDC, False) if random.random() < 0.55 \
                else (' ', None, False)

    def mmss(self):
        t = int(self.gtime)
        return '%02d:%02d' % (t // 60, t % 60)

    def poll_input(self):
        while msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b'q', b'Q', b'\x1b'):
                self.running = False
                return
            if ch in (b'p', b'P'):
                self.paused = not self.paused
            elif ch == b' ':
                self.drop_food()

    def drop_food(self):
        if len(self.foods) < MAX_FOOD:
            self.foods.append(Food(random.uniform(2, self.W - 3), 2.0))

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
        if random.random() < 0.12 and len(self.bubbles) < MAX_BUBBLE:
            self.bubbles.append(Bubble(random.uniform(2, self.W - 3), self.H - 3))

        for fo in self.foods:
            fo.step(self)

        for f in self.fishes:
            for fo in self.foods:
                if abs(f.x - fo.x) < 1.6 and abs(f.y - fo.y) < 1.0:
                    self.foods.remove(fo)
                    self.score += 1
                    break

    def run(self):
        last = time.monotonic()
        acc = 0.0
        while self.running:
            now = time.monotonic()
            acc += now - last
            last = now
            self.poll_input()
            if self.paused:
                acc = 0.0
            while acc >= TICK and not self.paused:
                self.step()
                acc -= TICK
            if not self.running:
                break
            self.render()
            time.sleep(0.02)

    def render(self):
        W, H = self.W, self.H
        grid = [[(' ', None, False)] * W for _ in range(H)]

        text = 'FISH TANK | SCORE:%d | TIME:%s' % (
            self.score, self.mmss())
        hint = ' | [Q]quit [SPACE]feed [P]pause'
        if self.paused:
            text = '[ PAUSED ] ' + text
        for i, ch in enumerate((text + hint)[:W]):
            grid[0][i] = (ch, 0, True)

        for x in range(1, W - 1):
            grid[1][x] = ('═', BORDER, False)
            grid[H - 1][x] = ('═', BORDER, False)
        grid[1][0] = ('╔', BORDER, False)
        grid[1][W - 1] = ('╗', BORDER, False)
        grid[H - 1][0] = ('╚', BORDER, False)
        grid[H - 1][W - 1] = ('╝', BORDER, False)
        for y in range(2, H - 1):
            grid[y][0] = ('║', BORDER, False)
            grid[y][W - 1] = ('║', BORDER, False)

        for x in range(1, W - 1):
            grid[H - 2][x] = self.sand[x]

        for pl in self.plants:
            base = H - 2
            for h in range(1, pl.h):
                grid[base - h][pl.x] = ('|', PLANT, False)
            sway = int(round(0.6 * math.sin(self.gtime + pl.phase)))
            grid[base - pl.h][pl.x + sway] = ('~', PLANT, False)

        for b in self.bubbles:
            grid[int(round(b.y))][int(round(b.x))] = ('o', BUBBLE, False)

        for fo in self.foods:
            grid[int(round(fo.y))][int(round(fo.x))] = ('*', FOODC, False)

        for f in self.fishes:
            self.draw_fish(grid, f)

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
        if 2 <= row <= self.H - 3:
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


def main():
    os.system('')
    try:
        W, H = os.get_terminal_size()
    except OSError:
        W, H = 80, 24
    if W < 30 or H < 12:
        print('Terminal too small, need at least 30x12')
        return
    game = Game(W, H)
    sys.stdout.write('\x1b[?1049h\x1b[?25l')
    try:
        game.run()
    finally:
        sys.stdout.write('\x1b[0m\x1b[?25h\x1b[?1049l\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
