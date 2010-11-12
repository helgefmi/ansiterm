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
        re_getnumber = re.compile(r'^(\d+)')
        while len(input) > 0:
            # Translate the cursor into an index into our 1-dimensional tileset.
            curidx = self.cursor['y'] * self.cols + self.cursor['x']
            if input[0] == '\x1b': # Signature of an ANSI escape code
                input = input[1:]
                # Sometimes \x1b isn't followed by [, so we check to make sure
                if input and input[0] == '[':
                    input = input[1:]
                
                # This section parses the input into the numeric arguments and
                # the type of sequence. If not numeric arguments are supplied,
                # we manually insert a 0.
                #
                # Example 1: \x1b[1;37;40m -> numbers=[1, 37, 40] char=m
                # Example 2: \x1b[m = numbers=[0] char=m

                numbers = []
                while True: # untill there's no numbers left ..
                    match = re_getnumber.match(input)
                    if match:
                        number = match.groups()[0]
                        input = input[len(number):]
                        numbers.append(int(number))

                        if input[0] == ';':
                            input = input[1:]
                    else:
                        break
                char, input = input[0], input[1:]

                if len(numbers) == 0:
                    numbers.append(0)

                # Check for known escape sequences and execute them.
                if char == 'H': # Sets cursor
                    if len(numbers) == 1: # (\x1b[H -> \x1b[1;1H)
                        assert numbers[0] == 0
                        numbers = [1, 1]
                    
                    self.cursor['y'] = numbers[0] - 1 # 1-based indexes
                    self.cursor['x'] = numbers[1] - 1 #
                elif char == 'm' or char == 'M': # Sets SGR parameters
                    for num in numbers:
                        self._parse_sgr(num)
                elif char == 'J': # Clears (parts of) the screen.
                    # From cursor to end of screen
                    if numbers[0] == 0:
                        range_ = (curidx, self.cols - self.cursor['x'] - 1)
                    # From beginning to cursor
                    elif numbers[0] == 1:
                        range_ = (0, curidx)
                    # Clears the whole screen
                    elif numbers[0] == 2:
                        range_ = (0, self.cols * self.rows - 1)
                    else:
                        raise Exception('Unknown argument for J parameter: %s (input=%r)' % (numbers, input[:20]))
                    for i in xrange(*range_):
                        self.tiles[i].reset()
                elif char == 'K': # Clears (parts of) the line
                    if numbers[0] == 0:
                        range_ = (curidx, curidx + self.cols - self.cursor['x'] - 1)
                    elif numbers[0] == 1:
                        range_ = (curidx % self.cols, curidx)
                    elif numbers[0] == 2:
                        range_ = (curidx % self.cols, curidx % self.cols + self.cols)
                    else:
                        raise Exception('Unknown argument for K parameter: %s (input=%r)' % (numbers, input[:20]))
                    for i in xrange(*range_):
                        self.tiles[i].reset()
                elif char == 'A': # Move cursor up
                    self.cursor['y'] -= 1 if not numbers else (numbers[0] + 1)
                elif char == 'B': # Move cursor down
                    self.cursor['y'] += 1 if not numbers else (numbers[0] + 1)
                elif char == 'C': # Move cursor right
                    self.cursor['x'] += 1 if not numbers else (numbers[0] + 1)
                elif char == 'D': # Move cursor left
                    self.cursor['x'] -= 1 if not numbers else (numbers[0] + 1)
                elif char == 'r' or char == 'l': # TODO
                    pass
                else:
                    raise Exception('Unknown escape code: char=%r numbers=%r input=%r' % (char, numbers, input[:20]))
            else:
                # If we end up here, the character should should just be
                # added to the current tile and the cursor should be updated.
                # Some characters such as \r, \n will only affect the cursor.
                # TODO: Find out exactly what should be accepted here
                #       i.e. only ASCII-7?
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
        self._fix_cursor()
