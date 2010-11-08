import re

class Tile:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.color = {
            'fg': 37, 'bg': 40,
            'reverse': False,
            'bold': False,
        }
        self.glyph = ' '

    def set(self, glyph, color):
        self.glyph = glyph
        self.color['fg'] = color['fg']
        self.color['bg'] = color['bg']
        self.color['reverse'] = color['reverse']
        self.color['bold'] = color['bold']

class Ansiterm:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.tiles = [Tile() for _ in xrange(rows * cols)]
        self.cursor = {
            'x': 0,
            'y': 0,
        }
        self.color = {
            'fg': 37, 'bg': 40,
            'bold': False,
            'reverse': False,
        }

    def get_string(self, from_, to):
        return ''.join([tile.glyph for tile in self.get_tiles(from_, to)])

    def get_tiles(self, from_, to):
        return [tile for tile in self.tiles[from_:to]]

    def get_cursor(self):
        return self.cursor.copy()

    def parse_sgr(self, param):
        if param >= 30 and param <= 37:
            self.color['fg'] = param
        elif param >= 40 and param <= 47:
            self.color['bg'] = param
        elif param == 1:
            self.color['bold'] = True
        elif param == 7:
            self.color['reverse'] = True
        else:
            return False
        return True

    def feed(self, input):
        while len(input) > 0:
            if self.cursor['x'] >= self.cols:
                self.cursor['y'] += 1
                self.cursor['x'] = 0

            if self.cursor['y'] >= self.rows:
                self.cursor['y'] = self.rows - 1

            curidx = self.cursor['y'] * self.cols + self.cursor['x']
            if input.startswith('\x1b['):
                input = input[2:]
                match = re.compile('^(\d+);(\d+)(\w)').match(input)
                if match:
                    a, b, c = match.groups()
                    if c.lower() == 'h':
                        self.cursor['y'] = int(a) - 1
                        self.cursor['x'] = int(b) - 1
                    elif c.lower() == 'r':
                        pass
                    elif c.lower() == 'm':
                        self.parse_sgr(int(a))
                        self.parse_sgr(int(b))
                    else:
                        raise Exception('Unknown escape code: \\x1b[' + a + ';' + b + c)

                    input = input[len(a + b + c) + 1:]
                    continue

                match = re.compile('^(\d+)(\w)').match(input)
                if match:
                    a, b = match.groups()
                    a = int(a)
                    if b.lower() == 'j':
                        if a == 0:
                            for i in xrange(curidx, self.cols - self.cursor['x'] - 1):
                                self.tiles[i].reset()
                        elif a == 1:
                            for i in xrange(curidx):
                                self.tiles[i].reset()
                        elif a == 2:
                            for i in xrange(self.cols * self.rows - 1):
                                self.tiles[i].reset()
                        else:
                            raise Exception('Unknown escape code: \\x1b[' + str(a) +  b)
                    elif b.lower() == 'b':
                        self.cursor['y'] += a
                    elif b.lower() == 'm':
                        if not self.parse_sgr(a):
                            raise Exception('Unknown color')
                    elif b.lower() == 'l':
                        pass
                    else:
                        raise Exception('Unknown escape code: \\x1b[' + str(a) + b)

                    input = input[len(str(a) + b):]
                    continue

                match = re.compile('^(\w)').match(input)
                if match:
                    a = match.groups()[0].lower()
                    if a == 'h':
                        self.cursor['y'] = 0
                        self.cursor['x'] = 0
                    elif a == 'k':
                        for i in xrange(curidx, curidx + self.cols - self.cursor['x'] - 1):
                            self.tiles[i].reset()
                    elif a == 'j':
                        for i in xrange(curidx, self.cols * self.rows - 1):
                            self.tiles[i].reset()
                    elif a == 'm':
                        self.color['fg'] = 37
                        self.color['bg'] = 40
                        self.color['bold'] = False
                        self.color['reverse'] = False
                    elif a == 'a':
                        self.cursor['y'] = self.cursor['y'] - 1
                    elif a == 'b':
                        self.cursor['y'] = self.cursor['y'] + 1
                    elif a == 'c':
                        self.cursor['x'] = self.cursor['x'] + 1
                    elif a == 'd':
                        self.cursor['x'] = self.cursor['x'] - 1
                    else:
                        raise Exception('Unknown escape code: \\x1b[' + a)

                    input = input[1:]
                    continue
            else:
                a = input[0]
                if a == '\r':
                    self.cursor['x'] = 0
                elif a == '\b':
                    self.cursor['x'] = self.cursor['x'] - 1
                elif a == '\n':
                    self.cursor['y'] = self.cursor['y'] + 1
                elif a == '\x0f' or a == '\x00':
                    pass
                else:
                    self.tiles[self.cursor['y'] * self.cols + self.cursor['x']].set(a, self.color)
                    self.cursor['x'] += 1

                input = input[1:]
                continue
