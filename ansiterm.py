import re

class Tile:
    """Represent a single tile in the terminal"""
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Resets the tile to a white space on black background"""
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
        """Initializes the ansiterm with rows*cols white-on-black spaces"""
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
        """Returns the character used on a section of the screen"""
        return ''.join([tile.glyph for tile in self.get_tiles(from_, to)])

    def get_tiles(self, from_, to):
        """Returns a tileset for a section of the screen"""
        return [tile for tile in self.tiles[from_:to]]

    def get_cursor(self):
        """Returns the current position of the curser"""
        return self.cursor.copy()

    def _parse_sgr(self, param):
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
        """
            Feed the terminal with input.
            This is where ANSI escape codes are parsed.
        """
        while len(input) > 0:
            # TODO: We must put this somewhere else, because this will not reset the
            #       cursor if the last input element will leave the cursor in an
            #       invalid position.
            while self.cursor['x'] >= self.cols:
                self.cursor['y'] += 1
                self.cursor['x'] = self.cursor['x'] - self.cols

            if self.cursor['y'] >= self.rows:
                self.cursor['y'] = self.rows - 1

            # Translate the cursor into an index into our 1-dimensional tileset.
            curidx = self.cursor['y'] * self.cols + self.cursor['x']
            if input.startswith('\x1b['): # Signature of an ANSI escape code
                input = input[2:]

                # Check against serveral ANSI escape codes, and make sure
                # that any successfully parsed input will be followed by a
                # `continue`.
                match = re.compile('^(\d+);(\d+)(\w)').match(input)
                if match:
                    a, b, c = match.groups()
                    c = c.lower()
                    if c == 'h':
                        self.cursor['y'] = int(a) - 1
                        self.cursor['x'] = int(b) - 1
                    elif c == 'r':
                        pass
                    elif c == 'm':
                        self._parse_sgr(int(a))
                        self._parse_sgr(int(b))
                    else:
                        raise Exception('Unknown escape code: \\x1b[' + a + ';' + b + c)

                    input = input[len(a + b + c) + 1:]
                    continue

                match = re.compile('^(\d+)(\w)').match(input)
                if match:
                    a, b = match.groups()
                    a = int(a)
                    b = b.lower()
                    if b == 'j':
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
                    elif b == 'b':
                        self.cursor['y'] += a
                    elif b == 'm':
                        if not self._parse_sgr(a):
                            raise Exception('Unknown color')
                    elif b == 'l':
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
                # If we end up here, the character should should just be
                # added to the current tile and the cursor should be updated.
                # Some characters such as \r, \n will only affect the cursor.
                # TODO: Find out exactly what should be accepted here
                #       i.e. \xff should probably be ignored.
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
