#!/usr/bin/python
import curses

def f(stdscr, args, kwds):
    x=0
    while True:
        c=stdscr.getch(0,x)
        s=str(c)
        for c in s:
            stdscr.addch(0,x,c)
            x+=1
        x+=1
        stdscr.addch(0,x,' ')

curses.wrapper(f, None, None)
