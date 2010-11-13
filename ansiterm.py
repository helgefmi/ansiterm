import re

class Tile:
    """Represents a single tile in the terminal"""
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
    escape_parser = re.compile(r'^\x1b\[?([\d;]*)(\w)')
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
        """Handles <escape code>n[;k]m, which changes the graphic rendition"""
        if param >= 30 and param <= 37:
            self.color['fg'] = param
        elif param >= 40 and param <= 47:
            self.color['bg'] = param
        elif param == 1:
            self.color['bold'] = True
        elif param == 7:
            self.color['reverse'] = True
        elif param == 0:
            self.color['fg'] = 37
            self.color['bg'] = 40
            self.color['bold'] = False
            self.color['reverse'] = False
        else:
            return False
        return True

    def _fix_cursor(self):
        """Makes sure the cursor are within the boundaries of the current terminal size"""
        while self.cursor['x'] >= self.cols:
            self.cursor['y'] += 1
            self.cursor['x'] = self.cursor['x'] - self.cols

        if self.cursor['y'] >= self.rows:
            self.cursor['y'] = self.rows - 1

    def feed(self, input):
        """Feeds the terminal with input."""
        while len(input) > 0:
            # Translate the cursor into an index into our 1-dimensional tileset.
            curidx = self.cursor['y'] * self.cols + self.cursor['x']
            if input[0] == '\x1b': # Signature of an ANSI escape code
                # This section parses the input into the numeric arguments and
                # the type of sequence. If no numeric arguments are supplied,
                # we manually insert a 0 or a 1 depending on the sequence type,
                # because different types has different default values.
                #
                # Example 1: \x1b[1;37;40m -> numbers=[1, 37, 40] char=m
                # Example 2: \x1b[m = numbers=[0] char=m
                match = Ansiterm.escape_parser.match(input)
                if not match:
                    raise Exception('Invalid escape sequence, input[:20]=%r' % input[:20])
                input = input[match.end():]
                args, char = match.groups()
                # If arguments are omitted, add the default argument for this sequence.
                if len(args) == 0:
                    if char in 'ABCDEFSTf':
                        numbers = [1]
                    elif char == 'H':
                        numbers = [1, 1]
                    else:
                        numbers = [0]
                else:
                    numbers = map(int, args.split(';'))

                # Check for known escape sequences and execute them.
                if char == 'H': # Sets cursor
                    self.cursor['y'] = numbers[0] - 1 # 1-based indexes
                    self.cursor['x'] = numbers[1] - 1 #
                elif char == 'm' or char == 'M': # Sets color/boldness
                    for num in numbers:
                        self._parse_sgr(num)
                elif char == 'J': # Clears (parts of) the screen.
                    # From cursor to end of screen
                    if numbers[0] == 0:
                        range_ = (curidx, self.cols - self.cursor['x'] - 1)
                    # From beginning to cursor
                    elif numbers[0] == 1:
                        range_ = (0, curidx)
                    # The whole screen
                    elif numbers[0] == 2:
                        range_ = (0, self.cols * self.rows - 1)
                    else:
                        raise Exception('Unknown argument for J parameter: %s (input=%r)' % (numbers, input[:20]))
                    for i in xrange(*range_):
                        self.tiles[i].reset()
                elif char == 'K': # Clears (parts of) the line
                    # From cursor to end of line
                    if numbers[0] == 0:
                        range_ = (curidx, curidx + self.cols - self.cursor['x'] - 1)
                    # From beginning of line to cursor
                    elif numbers[0] == 1:
                        range_ = (curidx % self.cols, curidx)
                    # The whole line
                    elif numbers[0] == 2:
                        range_ = (curidx % self.cols, curidx % self.cols + self.cols)
                    else:
                        raise Exception('Unknown argument for K parameter: %s (input=%r)' % (numbers, input[:20]))
                    for i in xrange(*range_):
                        self.tiles[i].reset()
                elif char == 'A': # Move cursor up
                    self.cursor['y'] -= 1 if not numbers else (numbers[0])
                elif char == 'B': # Move cursor down
                    self.cursor['y'] += 1 if not numbers else (numbers[0])
                elif char == 'C': # Move cursor right
                    self.cursor['x'] += 1 if not numbers else (numbers[0])
                elif char == 'D': # Move cursor left
                    self.cursor['x'] -= 1 if not numbers else (numbers[0])
                elif char == 'r' or char == 'l': # TODO
                    pass
                else:
                    raise Exception('Unknown escape code: char=%r numbers=%r input=%r' % (char, numbers, input[:20]))
            else:
                # If we end up here, the character should should just be
                # added to the current tile and the cursor should be updated.
                # Some characters such as \r, \n will only affect the cursor.
                # TODO: Find out exactly what should be accepted here.
                #       Only ASCII-7 perhaps?
                a = input[0]
                if a == '\r':
                    self.cursor['x'] = 0
                elif a == '\b':
                    self.cursor['x'] -= 1
                elif a == '\n':
                    self.cursor['y'] += 1
                elif a == '\x0f' or a == '\x00':
                    pass
                else:
                    self.tiles[self.cursor['y'] * self.cols + self.cursor['x']].set(a, self.color)
                    self.cursor['x'] += 1

                input = input[1:]
        self._fix_cursor()
