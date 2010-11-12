A virtual terminal for parsing ANSI escape codes in python..
Call feed() with input and get back output with get_string() or get_tiles(). Supports colors, bold and reverse, and most of the escape codes.
Works with the game nethack, but i haven't tested it with anything else yet.

$ telnet nethack.alt.org | tail -n1 > input.txt
Connection closed by foreign host.
$ python
>>> input = open('input.txt', 'r').read()
>>> repr(input)
"'\\x1b[2J\\x1b(B\\x1b)0\\x1b[?1049h\\x1b[1;42r\\x1b[m\\x1b[4l\\x1b[?1h\\x1b=\\x1b[39;49m\\x1b[39;49m\\x1b[m\\x1b[H\\x1b[J\\x1b[42;1H\\x1b[?1049l\\r\\x1b[?1l\\x1b>\\x1b[2J\\x1b[?1h\\x1b=\\x1b[?1h\\x1b=\\x1b[?1049h\\x1b[1;42r\\x1b[39;49m\\x1b[m\\x1b[4l\\x1b[H\\x1b[J\\x1b[H\\x1b[J\\x1b[1B ## nethack.alt.org - http://nethack.alt.org/\\r\\x1b[1B ##\\x1b[1B\\x08\\x08## Games on this server are recorded for in-progress viewing and playback!\\x1b[6;3HNot logged in.\\x1b[8;3Hl) Login\\x1b[9;3Hr) Register new user\\x1b[10;3Hw) Watch games in progress\\x1b[12;3Hs) server info\\x1b[13;3Hm) MOTD/news (updated: 2010.09.22)\\x1b[15;3Hq) Quit\\x1b[19;3H=> '"
>>> import ansiterm
>>> term = ansiterm.Ansiterm(25, 80)
>>> term.feed(input)
>>> output = '\n'.join(term.get_string(y * 80, y * 80 + 80) for y in xrange(25))
>>> print output

 ## nethack.alt.org - http://nethack.alt.org/
 ##
 ## Games on this server are recorded for in-progress viewing and playback!

  Not logged in.

  l) Login
  r) Register new user
  w) Watch games in progress

  s) server info
  m) MOTD/news (updated: 2010.09.22)

  q) Quit



  =>







