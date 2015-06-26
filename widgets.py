#! /usr/bin/python
# vim: set et ts=4 sw=4 fdm=marker
import curses
import curses.ascii
import sys
import time
import signal

CURSES_ERR=-1
curses.KEY_SDOWN=-2
curses.KEY_SUP=-3
curses.KEY_CRIGHT=-4
curses.KEY_CLEFT=-5
curses.KEY_CTRL_C=-6
curses.KEY_CTRL_V=-7
curses.KEY_CDOWN=-8
curses.KEY_CUP=-9

def db():
    curses.echo()
    curses.nocbreak()
    curses.endwin()
    if 0:
        from pydbgr.api import debug
        debug()
def ps2str(ps):
    """ method unction to return a string
    representation of a sequence of pane
    objs. it is assumed that value() method
    returns a string. """
    ret=''
    for p in ps: ret+=p.value();
    return ret
        

class scr:
    class scr_impl:
        def __init__(self):	
            signal.signal(signal.SIGINT, self.hint)
            self.stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            self.stdscr.keypad(1)
            try:
                curses.start_color()
            except:
                pass
                    
            self._cps = {}
            self._cpid = 0
            self._reg=reg([], '')

        def reg(self, v=None):
            if v!=None: 
                self._reg=v
            return self._reg
        def raiseevent(self, src, event, eargs=None):
            if eargs == None: eargs = eventargs()
            for eventhandler in event:
                eventhandler(src, eargs)

        def hint(self, sig, frame):
            """ handle SIGINT (ctrl-c)
            and push a representation 
            of it into the getch()
            buffer with ungetch() """
            curses.ungetch(curses.KEY_CTRL_C)

        def getexistingcp(self, cfg, cbg):
            # get existing color pair
            for k, v in self._cps.iteritems():
                if v[0] == cfg and v[1] == cbg:
                    return v[2]
            return None

        def cpid(self, v=None):
            if v != None:
                self._cpid = v
            return self._cpid
            
        def colorpair(self,fg,bg):
            cfg = self.curses_color_const(fg)
            cbg = self.curses_color_const(bg)
            cp = self.getexistingcp(cfg, cbg)
            if cp == None:
                id = self.cpid()
                id+=1
                if id <= 8: 
                    curses.init_pair(id, cfg, cbg)
                    cp = curses.color_pair(id)
                    self.cpid(id)
                    self._cps[str(id)] = [cfg, cbg, cp]
                else:
                    pass
                    # todo exception (exceeded cp count)
            return cp

        def curses_color_const(self,c):
            if c == 'black':
                return curses.COLOR_BLACK
            elif c == 'blue':
                return curses.COLOR_BLUE
            elif c == 'cyan':
                return curses.COLOR_CYAN
            elif c == 'green':
                return curses.COLOR_GREEN
            elif c == 'magenta':
                return curses.COLOR_MAGENTA
            elif c == 'red':
                return curses.COLOR_RED
            elif c == 'white':
                return curses.COLOR_WHITE
            elif c == 'yellow':
                return curses.COLOR_YELLOW
            else:
                pass # todo exception
                   

        def destroy(self):
            curses.nocbreak()
            self.stdscr.keypad(0)
            curses.echo()
            curses.endwin()

    _inst=None
    def __init__(self):
        if not scr._inst:
            scr._inst = scr.scr_impl()
        self.__dict__['inst']=self._inst

    def __getattr__(self, attr):
        return getattr(self._inst, attr)

    def __setattr__(self, attr):
        return setattr(self._inst, attr)
        

class eventargs:
    def __init__(self,data=None):
        self._data = data
        self._cancel=False
    def data(self):
        return self._data
    def cancel(self, v=None):
        if v!=None: self._cancel=v
        return self._cancel

class panerow:
    def __init__(self, panematrix):
        self._panes = []
        self._panematrix = panematrix
        self._height = 1

    def hl(self, v=None):
        """ pm(w): sets highlight for all 
        panes in this row """
        if v!=None:
            for p in self._panes:
                p.hl(v)
    def isnull(self):
        # does row have 1 null pane?
        return self.len() == 1

    def height(self, v=None):
        if v!=None:
            self._height=v
        return self._height

    def delete(self):
        self._panematrix.deleterow(self)
    
    def delpane(self, p, ifempty_delrow=False): 
        if p is self._panematrix.curpane():
            self._panematrix.curpane(None)
        del self._panes[p.x()]

        if ifempty_delrow and self.isempty(True):
            self.delete()

    def isempty(self, nullisempty=True):
        if nullisempty:
            return self.len() == 1 and \
                self.bol().isnull()
        else:
            return self.len()==0

    def newpane(self, v):
        p = pane(self, v)
        self._panematrix.append(self, p)

        # append using panematrix (class panes:)
        # because certain things are encapsulated
        # there
        #self._panes.append(p)
        return p

    def str(self):
        r=''
        for pane in self._panes:
            v = pane.value()
            if instanceof(v, str):
                if v == None:
                    v = '<None>'
                r+=v
        return r

    def below(self):
        ix = self.y()+1
        if ix > 0:
            try:
                r = self._panematrix.rows()[ix]
            except:
                return None
        else:
            r=None
        return r
    def above(self):
        ix = self.y()-1
        if ix >= 0:
            r = self._panematrix.rows()[ix]
        else:
            r=None
        return r

    def len(self):
        return len(self._panes)

    def y(self):
        return self._panematrix.rows().index(self)

    def appendnull(self):
        # add a null pane to eol
        p=pane(self,None)
        self.append(p)
        return p

    def append(self, p, updrow=True):
        # append a pane obj (p)
        # to the row's panes list
        if updrow: p.row(self)
        self._panematrix.append(self, p)
        # append using panematrix (class panes:)
        # because certain things are encapsulated
        # there
        #self._panes.append(p)
        return p

    def insert(self, i, v):
        return self._panes.insert(i, v)

    def insertrow(self):
        return self._panematrix.insertrow(self.y())

    def appendrow(self):
        return self._panematrix.appendrow()

    def curpane(self, v=0):
        return self._panematrix.curpane(v)

    def panes(self, withNull=True):
        if withNull:
            return self._panes
        else:
            ret=[]
            for p in self._panes:
                if p.value()!=None:
                    ret.append(p)
            return ret

    def getpane(self, x):
        for pane in self._panes:
            if pane.x() == x:
                return pane
        return None

    def getpanes(self, x, x0=None):
        ret=[]
        if x0 == None: x0=x+1
        for pane in self._panes:
            if pane.x() in range(x,x0):
               ret.append(pane)
        return ret

    def eol(self): return self._panes[-1]
    def bol(self): return self._panes[0]

    def isfirst(self):
        return (self is\
                self._panematrix.rows()[1])

    def islast(self):
        return (self is\
                self._panematrix.rows()[-1])

class col:
    def __init__(self):
        self._len=0

    def len(self, v=None):
        if v!=None:
            self._len=v
        return self._len
class reg:
    """ a simple register/clipboard 
    class for the panes class """
    def __init__(self, data, type):
        self.type(type)
        self.data(data)

    def type(self, v=None):
        if v!=None: self._type=v
        return self._type

    def isempty(self):
        return (len(self.data())==0)

    def data(self, v=None):
        """ pm: a [] of pane objs
        representing the registry's
        contents """
        if v!=None:
            self._data=[]
            for p in v:
                # TODO p.value() will need to be
                # cloned some how for real objects
                p=pane(None, p.value())
                self._data.append(p)
        return self._data


class panes:
    def __init__(self, owner):
        self.clear()
        self._sealdim = [0,0]
        self._owner=owner
        self._hlstartpane=None;
        self.onadd=[]
        self.onchgcurpane=[]
        self.onchgsealoffsets=[]
        self.onparse=[]

    def clear(self):
        self._panerows=[]
        self._curpane=None
        self._sealoffset = [0,0]
        self._cols=[]

    def append(self, r, p):
        r._panes.append(p)
        scr().raiseevent(self, self.onadd, eventargs(p))

    def cols(self):
        return self._cols
    def getcol(self, x):
        collens=len(self._cols)
        if x > collens-1:
            self._cols.insert(x, col())
        return self._cols[x]

    def crsize(self, collens=None, rowheights=None):
        # TODO the last lenght determines the lenght
        # for the rest of the rows
        # TODO Validation
        # TODO Currently, this must be called
        # after rows have been set
        x=y=0
        if collens!=None: 
            if isinstance(collens, int):
                collens=[collens]
            for l in collens:
                col=self.getcol(x)
                col.len(l)
                x+=1

        if rowheights!=None: 
            lenpanerows=len(self._panerows)
            if isinstance(rowheights, int):
                rowheights=[rowheights]
            for height in rowheights:
                if y<lenpanerows:
                    r=self._panerows[y]
                    r.height(height)
                else:
                    break
                y+=1

        collens=[]
        rowheights=[]
        for col in self.cols():
            collens.append(col.len())

        for row in self._panerows:
            rowheights.append(row.height())

        return [collens, rowheights]

    def isempty(self):
        return len(self._panerows) == 0

    def hled(self, withNLs=True):
        """ returns a [] of pane obj's
        that are highlighted """
        ret=[]
        started=False
        for r in self._panerows:
            for p in r.panes():
                if p.hl(): 
                    if withNLs and p.isbol() and started:
                        ret.append(pane(None, '\n'))
                    ret.append(p)
                    started=True
        return ret

    def hl(self, v):
        """ set the highlight boolean
        for all panes to v """
        # TODO This should be optimized
        for r in self._panerows:
            for p in r.panes():
                p.hl(v)
            
    def hlmode(self, v=None, type='p'):
        """ a bool pm
        that reflects whether hlstartpane==None.
        hlstartpane will be set to curpane if 
        this property method is set to True """
        if v != None:
            if v:
                if self.hlstartpane()==None:
                    # if type is pane (p) then
                    # higlight curpane
                    if   type=='p': 
                        self.hlstartpane(self.curpane())
                    # if type is row (r) then
                    # higlight currow
                    elif type=='r':
                        self.hlstartpane(self.currow())
            else:
                self.hlstartpane(None)
                self.hl(False)

        return (self.hlstartpane() != None)

    def hlstartpane(self, v=0):
        """ pm: sets hlstartpane.
            if v is a pane or panerow then
            v is set to highlighted for convinience.
            v defaults to 0 instead of None because
            we may want to set the hlstartpane to None """
        if v!=0:
            if v!=None:
                v.hl(True)
            if isinstance(v, panerow):
                v=v.bol()
            self._hlstartpane = v
        return self._hlstartpane
                
    def getpane(self, x, y):
        for i in range(0, len(self._panerows)):
            if i == y:
                return self._panerows[i].getpane(x)
        return None

    def deleterow(self, row):
        ry = row.y()
        del self._panerows[ry]

    def str(self):
        r=''
        for row in self._panerows:
            r+=row.str()
            r+="\n"
        return r

    def sealdim(self, w=None, h=None):
        if w != None:
            self._sealdim[0]=w
        if h != None:
            self._sealdim[1]=h

        return self._sealdim


    def seal(self):
        # ret a panes obj that
        # is a subset of the main
        # panes obj based on seal
        # offsets and dimentions
        # to represent the view-
        # able part of the win obj
        ret = panes(self._owner)
        x,y = self._sealoffset
        w,h = self.sealdim()
        
        rows = self._panerows[y:(h+y)]
        for row in rows:
            r = panerow(ret)
            r.height(row.height())
            for p in row.getpanes(x,w+x):
                # dont updrow so pane
                # sees itself as part of
                # the superset panes col
                r.append(p, updrow=False)
            ret._panerows.append(r) 
        return ret

    def rows(self):
        return self._panerows
    
    def toprow(self):
        return self._panerows[0]
        
    def bottomrow(self):
        ix=len(self._panerows)-1
        return self._panerows[ix]

    def currow(self):
        return self._panerows[self._curpane.y()]

    def parse(self, v):
        # assume v is a str
        self.clear()
        r = self.insertrow()
        for c in v:
            if c == "\n":
                r.append(pane(r,None))
                r = self.appendrow()
            elif c == "\r":
                continue
            else:
                r.append(pane(r,c))
        r.append(pane(r,None))

        scr().raiseevent(self, \
                            self.onparse, \
                            eventargs())
        return r
                
    def insertrow(self, y=0, null=False):
        """ insert a row at y. if (null)
            then append a null pane to end
            of row """
        r = panerow(self)
        self._panerows.insert(y, r)
        if null:
            r.appendnull()
        return r

    def appendrow(self):
        r = panerow(self)
        self._panerows.append(r)
        return r
        
    def curpane(self, v=0):
        if v != 0: 
            if not (self._curpane is v):
                eargs=eventargs((self._curpane, v))
                scr().raiseevent(self, \
                                 self.onchgcurpane, \
                                 eargs)
                self._curpane = v
        return self._curpane
    def makehl(self):
        """ highlight from orgpane
            to curpane """

        if not self.hlmode(): return
        startpane=self.hlstartpane()

        # clear highlights on all panes
        # to get a fresh start
        self.hl(False)

        startpane.hl(True)
        curpane=self.curpane()
        d='l'
        if ( startpane.y() == curpane.y() and \
             startpane.x() < curpane.x() ) or \
             startpane.y() < curpane.y():
            d='r'

        p=startpane;done=False
        while p!= None and p is not curpane:
            if   d=='l': p=p.left()
            elif d=='r': p=p.right()
            if p!=None:
                p.hl(True)

    def yank(self, cmd):
        """ copy to register. puts panes on
        the register given a 'vi-*' cmd """
        if   cmd in ('vi-y', 'ctrl-c'):
            hled=self.hled()
            if len(hled) > 0:
                scr().reg(reg(hled,'c'))

                # only de-highlight if in vimode
                if cmd == 'vi-y':
                    self.hlmode(False)
            
        elif cmd in ('vi-yy', 'vi-dd'):
            scr().reg(reg(self.currow().panes(), 'l'))
        elif cmd in ('vi-s', 'vi-x'):
            scr().reg(reg([self.curpane()], 'c'))
        elif cmd in ('vi-Y', 'vi-D'):
            scr().reg(reg ([self.curpane()] + self.curpane().rightchars(), 'c'))
    def mv(self,cmd, passnl=True):
        currow = self.currow()
        curpane = currow.curpane()
        w,h=self.sealdim()
        asc=curses.ascii
        if cmd == 'l':
            p = curpane.left(passnl)
            if p != None:
                currow.curpane(p)
                self.mvseal('curpane', 'mid', 'top')
        elif cmd == 'r':
            p = curpane.right(passnl)
            if p != None:
                currow.curpane(p)
                self.mvseal('curpane', 'mid', 'bottom')
        elif cmd == 'd':
            p = curpane.below()
            if p != None:
                currow.curpane(p)
            else:
                r = currow.below()
                if r != None:
                    self.curpane(r.eol())
        elif cmd == 'u':
            p = curpane.above()
            if p != None:
                currow.curpane(p)
        elif cmd == 'pgup':
            ny=curpane.y()-h
            if ny<0:ny=0
            npane = self.getpane(0,ny)
            if npane==None: return
            while npane.right() != None:
                if npane.value() == ' ':
                    npane=npane.right()
                else:
                    break
            self.curpane(npane)
            self.mvseal('curpane', 'left', 'bottom')
        elif cmd == 'pgdown':
            npane = self.getpane(0,curpane.y()+h)
            if npane==None: return
            while npane.right() != None:
                if npane.value() == ' ':
                    npane=npane.right()
                else:
                    break
            self.curpane(npane)
            self.mvseal('curpane', 'left', 'top')
            
        elif cmd == 'home':
            for p in currow.panes():
                v = p.value()
                if not (v in (' ', "\t")):
                    self.curpane(p)
                    break
            self.mvseal('curpane', 'left')
        elif cmd == 'end':
            currow.curpane(currow.eol())
            self.mvseal('curpane', 'mid')
        elif cmd == 'vi-B':
            sp=False
            lchars=curpane.leftchars()
            lchars.reverse()
            for p in lchars:
                if p.left() == None or \
                    curses.ascii.isspace(p.left().value()):
                    self.curpane(p)
                    self.mvseal('curpane', 'mid')
                    break;

        elif cmd == 'vi-b':
            sp=False
            v=curpane.value()
            startpunct=asc.ispunct(v)
            startsp   =asc.isspace(v)
            startbow  =curpane.bow()
            lchars=curpane.leftchars()
            lchars.reverse()
            found=False
            for p in lchars:
                v=p.value()
                ispunct=asc.ispunct(v)
                if asc.isspace(v):
                    sp=True
                elif ispunct and p.left() != None\
                        and (asc.isalnum(p.left().value()) or \
                                asc.isspace(p.left().value())):
                            found=True
                elif startbow and sp and p.bow():
                    found=True
                elif not startbow and p.bow():
                    found=True

                if found:
                    self.curpane(p)
                    self.mvseal('curpane', 'mid')
                    break;

        elif cmd == 'vi-I':
            for p in currow.panes():
                if asc.isalnum(p.value()):
                    break;
            self.curpane(p)
            self.mvseal('curpane', 'left')
            self._owner.vimode='ins'
            
        elif cmd == 'vi-W':
            p=self.vi_W_chars(curpane)[-1]
            self.curpane(p)
            self.mvseal('curpane', 'mid')

        elif cmd == 'vi-w':
            p=self.vi_w_chars(curpane)[-1]
            self.curpane(p)
            self.mvseal('curpane', 'mid')
        elif cmd == 'vi-gg':
            tr=self.toprow()
            if tr!=None:
                self.curpane(tr.bol())
                self.mvseal('curpane', 'left', 'top')
        elif cmd == 'vi-G':
            tr=self.bottomrow()
            if tr!=None:
                self.curpane(tr.bol())
                self.mvseal('curpane', 'left', 'bottom')
        self.makehl()

        if cmd in ('r','u','d', 'l'):
            self.mvseal(cmd)

    def mvseal(self, cmd, halign=None, valign=None, chgSealOffset=True):
        # chg the seal offsets
        # after the curpane has been changed
        # by mv()
        currow = self.currow() 
        curpane = currow.curpane()
        w,h=self.sealdim()
        x,y = self._sealoffset
        rowlen = currow.len()

        if cmd == 'end':
            # adjust seal to make the last char
            # on the line visible
            if rowlen > w:
                if not self.inseal(curpane.x()):
                    x=rowlen - w
            else:
                x=0
        elif cmd == 'r':
            # if cur pane is at end
            # of seal
            if w + x == curpane.x():
                x+=1
        elif cmd == 'fl': # far left
            x=0
        elif cmd == 'l': # TODO rm
            pass
            #if curpane.x()+1 == x:
            #    x-=1
        elif cmd == 'd':
            if currow.y() == (h + y):
                y+=1
            x=self.mvseal('end', chgSealOffset=False)[0]

        elif cmd == 'u':
            if currow.y()+1 == y:
                y-=1
            x=self.mvseal('end', chgSealOffset=False)[0]
        elif cmd == 'curpane':
            # adjust seal to include curpane
            if (halign != None) and \
                    (not self.inseal(x=curpane.x())):
                if   halign == 'left' :hx=0
                elif halign == 'right':hx=w
                elif halign == 'mid'  :hx=w//2 
                x = curpane.x()-hx
                if x<0:x=0

            if (valign != None) and \
                   (not self.inseal(y=curpane.y())):
                if   valign == 'top'    :hy=0
                elif valign == 'bottom':hy=h-1
                elif valign == 'mid'   :hy=h//2 
                y = curpane.y()-hy
                if y<0:y=0

        if chgSealOffset and self._sealoffset != [x,y]:
            self._sealoffset = [x,y]
            scr().raiseevent(self, self.onchgsealoffsets)
        return self._sealoffset

    def vi_W_chars(self, pane):
        ret=[pane]
        sp=False
        for p in pane.rightchars():
            if sp and p.value()!=' ':
                ret.append(p)
                break
            else:
                if p.value() == ' ':
                    sp=True
            ret.append(p)
        return ret

    def vi_w_chars(self, pane):
        ret=[pane]
        v=pane.value()
        startpunct=\
            curses.ascii.ispunct(v) or \
            (v == ' ')
        sp=False
        for p in pane.rightchars():
            v=p.value()
            if v==' ': 
                sp=True; 
            else:
                if startpunct:
                    if sp or curses.ascii.isalnum(v):
                        ret.append(p)
                        break
                else:
                    if sp or curses.ascii.ispunct(v):
                        ret.append(p)
                        break
            ret.append(p)
        return ret

                
    def inseal(self,x=None, y=None):
        # are x and y inside the 
        # current seal offsets?
        sx,sy = self._sealoffset
        w,h = self.sealdim()
        if x != None:
            if x >= sx and x < sx+w:
                return True
        if y != None:
            if y >= sy and y < sy+h:
                return True
        return False

                
class pane:
    def __init__(self, row, v):
        self._row=row
        self._v=v
        self._hl=False

    def clone(self):
        r = pane(None, self.value())
        r.hl(self.hl())
        return r

    def iscurrent(self):
        return self is self._row._panematrix.curpane()

    def hl(self, v=None):
        """ boolean pm: is pane (self) 
        highlighted """
        if v!=None:
            self._hl=v
        # null panes can't be hled
        return ((not self.isnull()) and self._hl)

    def col(self):
        return self._row.\
            _panematrix.\
                getcol(self.x())
        
    def dbg(self):
        r=''
        r += "x: %s\n" % self.x()
        r += "y: %s\n" % self.y()
        r += "val: %s\n" % self.value()
        print r

    def delete(self, ifempty_delrow=False):
        r=self.row()
        if r:
            r.delpane(self, ifempty_delrow)

    def row(self, v=None):
        if v!= None:
             self._row = v
        return self._row

    def value(self, v=None):
        if v != None:
            self._v=v
        return self._v

    def x(self, v=None):
        x=0
        for pane in self.row().panes():
            if pane is self:
                return x
            x+=1

    def y(self, v=None):
        return self.row().y()

    def left(self, passnl=True):
        """ return the char to the left of self.
        if (passnl) then pass newlines.
        in other words, if (passnl) and self is bol
        then the char to the 'left' will
        be the last char on the above row """

        # todo consider a linked
        # list to optimize
        p=self._row.getpane(self.x()-1)
        if passnl and p==None:
            p=self.above()
            if p != None:
                p=p.row().eol()
        return p

    def leftchars(self):
        """
        return chars left of self on the currow
        """
        ret=[]
        for p in self.row().panes():
            if p.x()<self.x():
                ret.append(p)
            else: break
        return ret
    def rightchars(self):
        """ return a [] of chars to the 
        right of self """
        ret=[]
        for p in self.row().panes():
            if p.x()>self.x():
                ret.append(p)
        return ret
    def right(self, passnl=True):
        """ return the char to the right of self.
        if (passnl) then the algorithm will pass
        newlines. so if self is eol
        then the char to the 'right' will
        be the first char on the below row """
        p=self._row.getpane(self.x()+1)
        if passnl and p==None:
            r=self.row().below()
            if r != None:
                p=r.bol()
        return p

    def above(self):
        row = self._row.above()
        if row != None:
            p = row.getpane(self.x())
            if p != None:
                return p
            else:
                return row.eol()
        return None

    def below(self):
        row = self._row.below()
        if row != None:
            return row.getpane(self.x())
        return None

    def isnull(self): 
        return (self.value() == None)

    def isbol(self):
        """ is self the first pane 
        on it's row """
        return (self.x() == 0)

    def iseol(self):
        """ is self the last pane 
        on it's row """
        return (self.row().eol() is self)

    def bow(self):
        asc=curses.ascii
        if asc.isalpha(self.value()):
            l=self.left()
            if l!=None:
                v=l.value()
                return (asc.isspace(v) or \
                            asc.ispunct(v))
            else: 
                return True
        return False

class window:
    def __init__(self):
        self._h = self._w = 1
        self._container=None
        self._fg=None
        self._bg=None
        self._visible=True
        self._x=None
        self._y=None
        self._btop=None
        self._bright=None
        self._bbottom=None
        self._bleft=None
        self._ptop=0
        self._pright=None  
        self._pbottom=None 
        self._pleft=None  
        self._trcorner=None
        self._tlcorner=None
        self._brcorner=None
        self._blcorner=None
        self._paintable=False
	
    def clear(self):
        x,y=self.xy()
        w,h=self.wh()
        for i in range(x, x+w):
            for j in range(y, y+h):
                scr().stdscr.addstr(j,i, ' ')

    def editmode(self, v=None):
        if v!=None:
            v=v.lower()
            if v in ('win', 'windows'):
                self._editmode='win'
            elif v in ('vi', 'vim'):
                self._editmode='vi'
            elif v == 'emacs':
                # TODO throw not implemented exception
                pass
            else:
                # TODO throw unsupported exception
                pass
        else:
            if self._editmode==None:
                return self.container().editmode()
            else:
                return self._editmode


    def container(self, wid=None):
        if wid!=None:
            self._container = wid
        return self._container

    def visible(self, v=None):
        if v!=None: self._visible=v
        return self._visible
    
    def ispaintable(self):
        return  self._x != None and\
                self._y != None and\
                self._w != None and\
                self._h != None and\
                self._paintable and\
                self.visible()
            
    def paint(self, clear=True):
        if not self.ispaintable(): return
        if clear: self.clear()
        stdscr=scr().stdscr
        #y,x=stdscr.getmaxyx()
        cp=self.cp()
        x,y=self.xy()
        w,h=self.wh()
        bt,br,bb,bl=self.border()
        ctl,ctr,cbr,cbl=self.corner()

        bt = ctl + bt * (w - len(ctl) - len(ctr))  + ctr
        bb = cbl + bb * (w - len(cbl) - len(cbr))  + cbr

        for i in range(y, h+y):
            if  i==y:
                stdscr.addstr(i,x, bt, cp)
            elif i==h+y-1:
                stdscr.addstr(i,x, bb, cp)
            else:
                stdscr.addstr(i,x, bl, cp)
                stdscr.addstr(i,x+w-1, br, cp)
            i+=1
        return

    def contentwh(self):
        """ the width and hight of the block of
        content without the border or the padding
        """

        # dont use self.wh() here or an infinit loop
        # will occur
        w,h=self._w, self._h
        pt,pr,pb,pl=self.pad()
        bt,br,bb,bl=[len(b) for b in self.border()]

        w = w - (pr+pl+br+bl)
        h = h - (pt+pb+bt+bb)
        return w,h

    def contentxy(self):
        """ the coordinates of the top-left portion
        of the window where the content starts; i.e.
        without the border and padding """
        x,y=self.xy()
        pt,pr,pb,pl=self.pad()
        bt,br,bb,bl=[len(b) for b in self.border()]
        x = x+pl+bl
        y = y+pt+bt
        return x,y
        
    def pad(self, top=None, right=None, bottom=None, left=None):
        if top   != None: self._ptop=    top
        if right != None: self._pright=  right
        if bottom!= None: self._pbottom= bottom
        if left  != None: self._pleft=   left

        if self._pright == None: self._pright=  self._ptop
        if self._pbottom== None: self._pbottom= self._ptop
        if self._pleft  == None: self._pleft=   self._pright

        return self._ptop, self._pright, self._pbottom, self._pleft

    def border(self, top=None, right=None, bottom=None, left=None):
        if top   != None: self._btop=    top
        if right != None: self._bright=  right
        if bottom!= None: self._bbottom= bottom
        if left  != None: self._bleft=   left

        if self._bright == None: self._bright=  self._btop
        if self._bbottom== None: self._bbottom= self._btop
        if self._bleft  == None: self._bleft=   self._bright

        repl=lambda s: '' if s==None else s
        return [repl(b) for b in [self._btop, self._bright,\
                                    self._bbottom, self._bleft] ]

    def corner(self, tl=None, tr=None, br=None, bl=None):
        if tl   != None: self._tlcorner=tl
        if tr   != None: self._trcorner=tr
        if br   != None: self._brcorner=br
        if bl   != None: self._blcorner=bl

        if self._trcorner  == None: self._trcorner= self._tlcorner
        if self._brcorner  == None: self._brcorner= self._tlcorner
        if self._blcorner  == None: self._blcorner= self._brcorner

        repl=lambda s: '' if s==None else s
        return [repl(b) for b in [self._tlcorner, self._trcorner,\
                                    self._brcorner, self._blcorner] ]
        
    def xy(self, x=None, y=None):
        if x != None: self._x = x
        if y != None: self._y = y
        return self._x, self._y

    def wh(self, w=None, h=None):
        if w != None: 
            self._w = w
            # TODO: sealdim isn't w/h unless
            # pane.value is a char
            # self._panes.sealdim(w=w)

        if h != None: 
            self._h = h
            # TODO: sealdim isn't w/h unless
            # pane.value is a char
            # self._panes.sealdim(h=h)

        return self._w, self._h

    def xyxy(self):
        x,y = self.xy()
        wh = self.wh()
        x0 = x+w
        y0 = y+h
        return x,y,x0,y0
        

    def fgbg(self, fg=None, bg=None):
        if fg != None: self._fg=fg
        if bg != None: self._bg=bg

        # Inherit containters
        # properties if not specified
        cont=self.container()
        if cont:
            if self._fg == None:
                self._fg = \
                    cont.fgbg()[0]
            if self._bg == None:
                self._bg = \
                    cont.fgbg()[1]

        return self._fg, self._bg
    

class widgets:
    def __init__(self):
        self._widgets=[]
        self.TAB='\t'
        self._curwidget=None

    def mkpaintable(self):
        for w in self._widgets:
            w._paintable=True
    def paint(self):
        for w in self._widgets:
            w.paint()

    def firstwidget(self):
        for w in self._widgets:
            if w.tabord == 0:
                return w

    def lastwidget(self):
        maxwidget = self.firstwidget()
        for w in self._widgets:
            if w.tabord > maxwidget.tabord:
                maxwidget = w
        return maxwidget.tabord

    def curwidget(self, v=None):
        if v!=None:
            self._curwidget=v
        if self._curwidget == None:
            self._curwidget = self.firstwidget()
        return self._curwidget
                
    def len(self):
        return len(self._widgets)
    
    def show(self):
        if self.len() == 0: return

        self.mkpaintable()
        self.paint()
        while 1:
            w=self.curwidget()
            r = w.setfocus()
            if r == ord("\t"):
                w = self.curwidget(self.next())
            # FIXME
            if r == "":
                w = self.curwidget(self.prev())

                
    def prev(self):
        curtab = self.curwidget().tabord
        for w in self._widgets:
            if curtab - 1 == w.tabord:
                return w
        return self.lastwidget()

    def next(self):
        curtab = self.curwidget().tabord
        for w in self._widgets:
            if curtab + 1 == w.tabord:
                return w
        return self.firstwidget()


    def append(self, w):
        # todo: ensure .name is uniq
        # todo: ensure .xy is uniq
        if w.tabord == None:
            w.tabord = self.maxtab() + 1
        w.widgets(self)
        self._widgets.append(w)

    def maxtab(self):
        max=-1
        for w in self._widgets:
            if max < w.tabord:
                max = w.tabord
        return max


class widget(window):
    # TODO are widgets and windows the
    # same thing
    def __init__(self):
        window.__init__(self)
        self.tabord=None

    def widgets(self, v=None):
        if v != None:
            self._widgets = v
        return self._widgets

    def name(self, v=None):
        if v != None:
            self._name = v

    def cp(self):
        fg,bg=self.fgbg()
        return scr().colorpair(fg, bg)
        
class frm(window):
    def __init__(self):
        window.__init__(self)
        self._widgets = widgets()
        self._focusfg=None
        self._focusbg=None

    def widgets(self, v=None):
        if v != None:
            self._widgets = v
        return self._widgets
    def append(self, widget):
        self.widgets().append(widget)

    def show(self):
        self.paint()
        self.widgets().show()

    def paint(self):
        stdscr=scr().stdscr
        y,x=stdscr.getmaxyx()
        for i in range(y-1):
            stdscr.addstr(i,0, ' '*x, self.cp())
        window.paint(self)

    def cp(self):
        fg,bg=self.fgbg()
        return scr().colorpair(fg, bg)
            
class tbl(widget):
    def __init__(self):
        widget.__init__(self)
        self._panes=panes(self)
        self._panefocus=False
        self._panes.onadd.append(self.panes_onadd)
        self._editmode='win'

    def panes_onadd(self, src, eargs):
        wid=eargs.data().value()
        wid.onkeypress.append(self.curpane_onkeypress)

        # make wid have no edit mode so it 
        # obtains it from it's containter 
        # which in this case would be (self)
        wid.editmode(None)

    def setsealdim(self):	
        crsize = self.panes().crsize()
        
        if  len(crsize[0]) == 0 or\
            len(crsize[1]) == 0 or\
            self.wh() == (None, None):
            return

        w, h=self.contentwh()
        i=0
        for lengths in crsize:
            j=0; sum=0 
            if i==0: dim=w
            else:    dim=h
            for length in lengths:
                sum+=length
                # TODO this line is for cells
                # that have 0 width between them.
                # this should be parameterized
                sum-=1
                if sum > dim:
                    if i==0: sdw=j
                    else:    sdh=j-1
                    break
                else:
                    j+=1
            i+=1
        self._panes.sealdim(sdw, sdh)
    def pad(self, top=None, right=None, bottom=None, left=None):
        r=window.pad(self, top, right, bottom, left)
        self.setsealdim()
        return r

    def wh(self, w=None, h=None):
        """ pm: overriden from 'window'.
        sets width and height.
        overriden to set sealdim """
        rw,rh=window.wh(self, w, h)
        self.setsealdim()
        return rw, rh

    def crsize(self, collens=None, rowheights=None):
        self.panes().crsize(collens, rowheights)
        self.setsealdim()

    def cells(self):
        """ pm(r); returns the 
        cell collection; a subset
        of the panes cls """
        return self._cells

    def setfocus(self):
        panes = self._panes
        curpane=panes.curpane()
        if not curpane:
            curpane= \
                panes.curpane( \
                    self._panes.getpane(0,0))
        while 1:
            fg,bg=self.focusfgbg()
            wid=self.panes().curpane().value()
            wid.fgbg(fg,bg)
            wid.paint()

            wid.setfocus()

            fg,bg=self.fgbg()
            wid.fgbg(fg,bg)
            wid.paint()

    def curpane_onkeypress(self, src, eargs):
        """ catch event from curpane 
        indicating which key was pressed
        to control navigation """
        key=eargs.data()
        if key==curses.KEY_F2:
            # allow pane (i.e. txt box) to
            # control nav keys (left, right, etc..)
            self.panefocus(True)
        #elif key==curses.ESC:
        elif key==27:
            # allow tbl (self) to control nav
            self.panefocus(False)
        elif key in (curses.KEY_LEFT,
                     curses.KEY_RIGHT,
                     curses.KEY_DOWN,
                     curses.KEY_UP):
            # if tbl controls navigation then...
            # navigate
            if not self.panefocus():
                eargs.cancel(True)
                self.mv(key)


    def panefocus(self, v=None):
        if v!=None: self._panefocus=v
        return self._panefocus

    def mv(self, cmd):
        if   cmd==curses.KEY_LEFT:  cmd='l'
        elif cmd==curses.KEY_RIGHT: cmd='r'
        elif cmd==curses.KEY_DOWN:  cmd='d'
        elif cmd==curses.KEY_UP:    cmd='u'
        self._panes.mv(cmd)
        self.paint()

    def focusfgbg(self, fg=None, bg=None):
        if fg != None: self._focusfg=fg
        if bg != None: self._focusbg=bg

        if self._focusfg==None: 
            self._focusfg = self.fgbg()[0]
        if self._focusbg==None: 
            self._focusbg = self.fgbg()[1]

        return self._focusfg, self._focusbg

    def paint(self):
        x,y=self.contentxy()
        wy=y
        self.clear()
        window.paint(self)
        for row in self.panes().seal().rows():
            wx=x
            for pane in row.panes(): 
                wid=pane.value()
                wid.blankchar('.')
                pt,pr,pb,pl=wid.pad(0,1)
                ctl,ctr,cbr,cbl=wid.corner('+')
                bt,br,bb,bl=\
                   wid.border("-", "|", "-", "|")
                wid.container(self)
                wid.xy(wx, wy)

                clen = pane.col().len()
                rheight=row.height()

                wid.wh(clen, rheight)
                wid.visible(True)
                wid.paint()
                wx+=clen-1
            wy+=rheight-1

    def panes(self):
        return self._panes

class txt(widget):
    def __init__(self):
        widget.__init__(self)
        self._text=[]
        self._panes = panes(self)
        self.onchg = []
        self.onedit = []
        self.onmv = []
        self.onkeypress = []
        self._blankchar='_'
        self._editmode='win'
        self.vimode='ins'
        self.vicmd=''
        self._lastedit=[]
        self._dirtysealoffsets=True
        self._dirtytext=True
        self._seal=None

        ps=self._panes;

        ps.onchgsealoffsets.\
            append(self.panes_onchgsealoffsets)

        ps.onparse.append(self.panes_onparse)
        self.onedit.append(self.self_onedit)
        self.onmv.append(self.self_onmv)

        # start txt off with a null pane
        r = ps.insertrow()
        p = r.newpane(None)
        ps.curpane(p)

    def self_onmv(self, src, eargs):
        self._dirtytext=True
        self.paint()

    def self_onedit(self, src, eargs):
        self._dirtytext=True
        self.paint()

    def panes_onchgsealoffsets(self, src, eargs):
        self._dirtysealoffsets=True
        self.paint()

    def panes_onparse(self, src, eargs):
        self._dirtytext=True
        self.paint()

    def blankchar(self, v=None):
        if v!=None:
            self._blankchar = v
        return self._blankchar

    def panes(self):
        return self._panes

    def wh(self, w=None, h=None):
        """ pm: overriden from 'window'.
        sets width and height.
        overriden to set sealdim as well
        because the dimentions of the txt box
        eq the dimentions of the seal """

        # set window.wh() before calling
        # self.contentwh()
        w,h=window.wh(self, w, h)
        if w != None and h != None:
            pw, ph = self.contentwh()
            self._panes.sealdim(pw,ph)
        return w,h

        #return self._panes.sealdim(w,h)


    def getchs(self,y,x):
        esc=[]; ret=[]
        curses_err=-1; open_bracket=91
        esckey=27; dollar=36
        ctrl=False
        while True:
            if len(esc)>0: curses.halfdelay(1)
            #if len(esc)>0: scr().stdscr.timeout(0)
            c = scr().stdscr.getch(y,x)
            if c==-1 or c == esckey or c == open_bracket:
                esc.append(c)
                continue
            else:
                lenesc=len(esc)
                if lenesc > 0:
                    if lenesc == 1 and c == -1:
                        # <ESC> was pressed
                        ret = [esckey]
                    elif c == curses.KEY_CTRL_C:
                        if lenesc != 1:
                            break;
                        # the next call to getch
                        # returns -1 so we go ahead
                        # and get that over with here
                        # to prevent having to hit the 
                        # next key twice
                        # TODO (see above) This may have
                        # to do with a prob entering cmd 
                        # mode in vi mode
                        z=scr().stdscr.getch(y,x)
                        ret = [c]
                    elif c == curses_err:
                        ret = esc
                    elif c == 55:
                        ret=[curses.KEY_HOME]
                        continue
                    elif ret==[curses.KEY_HOME]:
                        if c == dollar:
                            ret=[curses.KEY_SHOME]
                    elif c == 56:
                        ret=[curses.KEY_END]
                        continue
                    elif ret==[curses.KEY_END]:
                        if c == dollar:
                            ret=[curses.KEY_SEND]
                    elif ctrl:
                        # cleft seq: 27, 79, 100
                        if c==100:
                            ret=[curses.KEY_CLEFT]
                        elif c==99:
                            ret=[curses.KEY_CRIGHT]
                        elif c==98:
                            ret=[curses.KEY_CDOWN]
                        elif c==97:
                            ret=[curses.KEY_CUP]
                    elif c == 100:
                            # cleft seq: 27, open_bracket, 100
                        ret=[curses.KEY_SLEFT]
                    elif c == 79:
                        ctrl=True
                        continue
                    elif c == 99:
                        ret=[curses.KEY_SRIGHT]
                    elif c == 98:
                        ret=[curses.KEY_SDOWN]
                    elif c == 97:
                        ret=[curses.KEY_SUP]
                    else:
                        esc.append(c)
                        ret=esc
                    if len(ret) == 0: ret = [ord('?')]
                    curses.cbreak()
                    return ret
                else:
                    if c == 22:
                        ret=curses.KEY_CTRL_V
                    else:
                        ret=c
                        
                    return [ret]
        
    def trchar(self, ch):
        """ 
        translate char (c) into ctrl 
        cmd based on editmode (vi, win, emacs)
        """
        mv=edit=data=None
        if ch in range(0,256): chstr=chr(ch)
        mode=self.editmode()

        if   ch==curses.KEY_LEFT:    mv='l'
        elif ch==curses.KEY_RIGHT:   mv='r'
        elif ch==curses.KEY_DOWN:    mv='d'
        elif ch==curses.KEY_UP:      mv='u'
        elif ch==curses.KEY_NPAGE:   mv='pgdown'
        elif ch==curses.KEY_PPAGE:   mv='pgup'
        elif ch==263:                edit='bs'
        elif ch==10:                 edit='nl'
        else:
            if mode == 'vi':
                if self.vicmd=='r':
                    self.vicmd=''; edit='vi-r'
                    data=curses.unctrl(ch)
                elif self.vicmd=='s':
                    self.vicmd=''; edit='vi-r'
                    edit='add'
                    data=curses.unctrl(ch)
                    self.vimode='ins'
                elif self.vicmd=='d':
                    if chstr=='d':
                        edit='vi-dd'
                    if chstr=='w':
                        edit='vi-dw'
                    if chstr=='W':
                        edit='vi-dW'
                    self.vicmd=''
                elif self.vicmd=='f':
                    self.vicmd=''
                    mv='vi-f'
                    data=curses.unctrl(ch)
                elif self.vicmd=='g':
                    if chstr=='g':
                        mv='vi-gg'
                    self.vicmd=''
                elif self.vicmd=='c':
                    if chstr=='c':
                        edit='vi-cc'
                    if chstr=='w':
                        edit='vi-cw'
                    if chstr=='W':
                        edit='vi-cW'
                    self.vicmd=''
                elif self.vicmd=='y':
                    if chstr=='y':
                        edit='vi-yy'
                    self.vicmd=''
                else:
                    if self.vimode=='ins' and ch == 27:  # <esc>
                        self.vimode='cmd'
                        if not self._panes.curpane().isbol(): mv='l'
                    elif ch == 27 and self._panes.hlmode():
                        self._panes.hlmode(False)
                        self._panes.hl(False)
                        # TODO: Shouldn't this be a raiseevent? 
                        self.refresh()
                    elif self.vimode=='cmd':
                        if   chstr=='i': self.vimode='ins'
                        elif chstr=='~': edit='vi-~'
                        elif chstr=='$': mv='end'
                        elif chstr=='^': mv='home'
                        elif chstr=='w': mv='vi-w'
                        elif chstr=='W': mv='vi-W'
                        elif chstr=='I': mv='vi-I'
                        elif chstr=='r': self.vicmd='r'
                        elif chstr=='y': 
                            self.vicmd='y'; edit='vi-y'
                        elif chstr=='o': edit='vi-o'
                        elif chstr=='O': edit='vi-O'
                        elif chstr=='p': edit='vi-p'
                        elif chstr=='P': edit='vi-P'
                        elif chstr=='a': 
                            mv='r'; self.vimode='ins'
                        elif chstr=='A': 
                            mv='end'; self.vimode='ins'
                        elif chstr=='s': self.vicmd='s'; edit='vi-s'
                        elif chstr=='d': self.vicmd='d'
                        elif chstr=='D': edit='vi-D'
                        elif chstr=='f': self.vicmd='f'
                        elif chstr=='g': self.vicmd='g'
                        elif chstr=='G': mv='vi-G'
                        elif chstr=='h': mv='l'
                        elif chstr=='j': mv='d'
                        elif chstr=='J': edit='join'
                        elif chstr=='k': mv='u'
                        elif chstr=='l': mv='r'
                        elif chstr=='x': edit='vi-x'
                        elif chstr=='X': edit='bs'
                        elif chstr=='c': self.vicmd='c'
                        elif chstr=='C': edit='vi-C'
                        elif chstr=='v': self._panes.hlmode(True)
                        elif chstr=='V': 
                            self._panes.hlmode(True, 'r')
                            # TODO: Shouldn't this be a raiseevent? 
                            self.refresh()
                            
                        elif chstr=='b': mv='vi-b'
                        elif chstr=='B': mv='vi-B'
                        elif chstr=='.': edit='vi-.'

                    elif self.vimode=='ins':
                        if self.isprintable(ch):
                            #mv='r'; 
                            edit='add'; 
                            data=curses.unctrl(ch)
            elif mode == 'win':
                if   ch==curses.KEY_HOME: mv='home'
                elif ch==curses.KEY_SHOME: mv='home'
                elif ch==curses.KEY_END:  mv='end'
                elif ch==curses.KEY_SEND:  mv='end'
                elif ch==curses.KEY_SLEFT: mv='l'
                elif ch==curses.KEY_SRIGHT: mv='r'
                elif ch==curses.KEY_SDOWN: mv='d'
                elif ch==curses.KEY_SUP: mv='u'
                elif ch==curses.KEY_CDOWN: mv='d'
                elif ch==curses.KEY_CUP: mv='u'
                elif ch==curses.KEY_DC: edit='del'
                elif ch==curses.KEY_CRIGHT: mv='vi-W'
                elif ch==curses.KEY_CLEFT: mv='vi-B'
                elif ch==curses.KEY_CTRL_C: 
                    edit='ctrl-c'
                elif ch==curses.KEY_CTRL_V: edit='ctrl-v'
                elif self.isprintable(ch):
                    edit='add'; 
                    data=curses.unctrl(ch)
        if mode=='win':
            if ch in (curses.KEY_LEFT, curses.KEY_RIGHT,
                      curses.KEY_DOWN, curses.KEY_UP,  
                      curses.KEY_HOME, curses.KEY_END,
                      curses.KEY_NPAGE, curses.KEY_PPAGE):
                self._panes.hlmode(False)
            elif ch in (curses.KEY_SLEFT, curses.KEY_SRIGHT,
                        curses.KEY_SDOWN, curses.KEY_SUP,
                        curses.KEY_SHOME, curses.KEY_SEND):
                self._panes.hlmode(True)

        return mv,edit,data

    def isprintable(self, ch):
        return (ch in range(32, 125))

    def setfocus(self):
        panes = self._panes
        chs=None
        while 1:
            x,y = self.curxy()
            chs = self.getchs(y,x)
            ch = chs[0]
            if ch==ord("\t"): return ch

            e = eventargs(ch) 
            scr().raiseevent(self, self.onkeypress, e)
            if e.cancel(): return
            mv,edit,data=self.trchar(ch)
                
            if edit != None: 
                if edit != 'vi-.':
                    self._lastedit=mv,edit,data
                self.edit(edit,data)
            if mv   != None: 
                e = eventargs(mv) 
                scr().raiseevent(self, self.onmv, e)
                if e.cancel(): return
                self.mv(mv, data)
            
    def mv(self, cmd, data=None, passnl=True):
        panes=self._panes
        curpane=panes.curpane()
        if cmd=='vi-f':
            for p in curpane.rightchars():
                if p.value()==data:
                    panes.curpane(p)
                    break
        
        self._panes.mv(cmd, passnl)

    def edit(self, cmd, data=None):
        panes = self._panes
        asc=curses.ascii
        panes.yank(cmd)
        cancel=False

        # if hlmode then delete highlighted
        # chars for certain conditions. 
        if panes.hlmode():
            # use 'del' instead of 'vi-x'
            # to prevent copying chars to 
            # register
            if cmd not in ('join', 'del', 'vi-s', 'vi-x', 'ctrl-c'):
                self.edit('del')
                if cmd in ('bs'):
                    cancel=True
                       

        # these two lines need to come after the call
        # to self.edit('del') because, if called, it
        # will chg these
        curpane = panes.curpane()
        currow = panes.currow() 

        if not cancel:
            # if new line (e.g. <enter>)
            if cmd == 'nl':
                newrow = panes.insertrow(currow.y()+1)
                p = curpane
                while p != None and p.value() != None:
                    newpane = pane(newrow, p.value())
                    newrow.append(newpane)
                    tmppane=p
                    p = p.right()
                    tmppane.delete()
                p = newrow.newpane(None)
                newrow.curpane(newrow.bol())
                panes.mvseal('d') 
            elif cmd == 'bs':
                if currow.isnull():
                    if currow.y() == 0:
                        return
                    aboverow = currow.above()
                    currow.delete()
                    if aboverow != None:
                        curpane.delete()
                        panes.curpane(aboverow.eol())
                        panes.mvseal('curpane', 'mid')
                else:
                    left=curpane.left(False)
                    # just del and mv left
                    if left != None:
                        left.delete()
                        panes.mvseal('curpane', 'mid', 'mid')
                    else:
                        # we are at the bol and
                        # and the line isn't empty so
                        # join line above with currow
                        aboverow = currow.above()
                        if aboverow != None:
                            panes.curpane(aboverow.eol())
                            self.edit('join')
                            panes.mvseal('curpane', 'mid', 'mid')
            elif cmd == 'vi-r':
                # TODO When hlmode, replace all highlighted
                # with replacement char
                if not curpane.isnull():
                    curpane.value(data)
            elif cmd == 'add':
                if currow.eol() is curpane:
                    curpane.value(data)
                    p=currow.newpane(None)
                    currow.curpane(p)
                else:
                    p = pane(currow, data)
                    currow.insert(curpane.x(), p)
                panes.mvseal('curpane', 'mid')
            elif cmd in('del', 'vi-s', 'vi-x'):
                # get currently hl'ed panes
                # and delete them
                hled = panes.hled(); 
                lenhled=len(hled)
                ins=False
                if lenhled>0:
                    # curpane will be one of these
                    # hled panes so we need to 
                    # set the curpane to something
                    # else
                            
                    if hled[0].isbol() and\
                        (hled[-1].right().iseol() or\
                            hled[-1].y() > hled[0].y()):
                            cp=hled[0]
                            ins=True
                            y=cp.y()
                    else:
                        cp=hled[-1].right()
                    hled.reverse()
                    for p in hled:
                        p.delete(True)

                    if ins:
                        r=panes.insertrow(y, True)
                        curpane=panes.curpane(r.bol())
                    else:
                        curpane=panes.curpane(cp)
                    # turn hlmode off now that we've  
                    # deleted the hled
                    panes.hlmode(False)
                    panes.mvseal('curpane', 'left')
                else:
                    if not curpane.isnull():
                        right = curpane.right()
                        if right != None:
                            self.panes().curpane(right)
                        curpane.delete()
                    else: #curpane is null
                        self.edit('join')

            elif cmd == 'join':
                # TODO Make sure that when
                # in hlmode, the join is done
                # the way vi does it
                # join currow with currow.bottom
                # NOTE: vi ready
                below=currow.below()
                if below != None:
                    currow.eol().delete()
                    # if curpane.isnull then set:
                    # curpane to the first of 
                    # the appended chars
                    # else, leave as is 
                    beenhere=not curpane.isnull()
                    for p in below.panes():
                        if p.isnull(): break
                        if not beenhere:
                            panes.curpane(p)
                            beenhere=True
                        currow.append(p)
                    nullpane=currow.appendnull()
                    if panes.curpane() == None:
                        panes.curpane(currow.eol())
                    below.delete()
            elif cmd == 'vi-o':
                # TODO if hlmode, do nothing (i think)
                newrow = panes.insertrow(currow.y()+1, True)
                panes.curpane(newrow.bol())
                panes.mvseal('curpane',valign='bottom')
                self.vimode='ins'
            elif cmd == 'vi-O':
                # TODO if hlmode, do nothing (i think)
                newrow = panes.insertrow(currow.y(), True)
                panes.curpane(newrow.bol())
                self.vimode='ins'
            elif cmd == 'vi-dd':
                if   currow.below() != None:
                    self.mv('d')
                elif currow.above() != None:
                    self.mv('u')
                else:
                    newrow = panes.insertrow(currow.y(), True)
                    panes.curpane(newrow.bol())
                    self.mv('u')
                currow.delete()
            elif cmd == 'vi-D':
                if not curpane.isnull():
                    for p in curpane.rightchars():
                        if p.isnull(): continue
                        p.delete()
                    curpane.delete()
                    panes.curpane(currow.eol())
            elif cmd == 'vi-cc':
                foundblack=False
                ps=currow.panes()
                for i in range(len(ps)):
                    p=ps[i]
                    if asc.isspace(p.value()):
                        continue
                    else:
                        falnum=i
                        break

                for i in range(len(ps)-1,falnum-1,-1):
                    p=ps[i]
                    if not p.isnull():  
                        p.delete()
                panes.curpane(currow.eol())
                panes.mvseal('curpane', 'mid')
                self.vimode='ins'
            elif cmd in ('vi-dw', 'vi-dW'):
                if cmd == 'vi-dw':
                    ps = panes.vi_w_chars(curpane)
                else:
                    ps = panes.vi_W_chars(curpane)

                p=ps.pop()
                if p!=None:
                    panes.curpane(p)
                # add deleted to register
                scr().reg(reg(ps, 'c'))
                ps.reverse()
                for p in ps:
                    p.delete()
            elif cmd == 'vi-cw':
                # FIXME: These recursive calls
                # will cause the event(s) at 
                # the bottom to fire more than once
                self.edit('vi-dw')
                self.vimode='ins'
            elif cmd == 'vi-cW':
                self.edit('vi-dW')
                self.vimode='ins'
            elif cmd == 'vi-C':
                self.edit('vi-D')
                self.vimode='ins'

            elif cmd == 'vi-.':
                mv,edit,data=self._lastedit
                self.edit(edit,data)
                self.mv(mv)
            elif cmd == 'vi-~':
                v = curpane.value() 
                if v!= None and v.isalpha():
                    if v.isupper(): 
                        curpane.value(v.lower())
                    else:
                        curpane.value(v.upper())
                self.mv('r')
            elif cmd in ('vi-p', 'vi-P', 'ctrl-v'):
                # get register
                r=scr().reg()
                if r.isempty(): return


                # if a line was copied (i.e. vi-yy)
                # then 'put' as new line
                if r.type() == 'l':
                    if cmd=='vi-p':
                        self.edit('vi-o')
                    elif cmd=='vi-P':
                        self.edit('vi-O')
                    
                # add chars from register into 
                # panes collection
                for p in r.data():
                    v=p.value()
                    if v=='\n':
                        self.edit('nl')
                    else:
                        self.edit('add', p.value())

                if r.type() == 'l':
                    # vi-o/vi-O would have set vimode to 'ins' so:
                    self.vimode='cmd'

                    # set curpane to bol 
                    panes.curpane( \
                        panes.currow().bol())

                # adjust seal to show curpane
                # at left of seal
                panes.mvseal('curpane', 'left')

        
        e = eventargs({'cmd':cmd, 'data':data})
        scr().raiseevent(self, self.onedit, e)
            
    def curxy(self):
        x,y = self.contentxy()
        sx,sy = self._panes._sealoffset
        currow = self._panes.currow()
        curpane = currow.curpane()
        if curpane != None:
            rx = x + (curpane.x() - sx)
            ry = y + (currow.y() - sy)
        else:
            rx = x; ry = y
               
        return rx,ry

    def text(self, v=None):
        if v != None: 
            self._panes.parse(v)
            p=self._panes.getpane(0,0)
            if p != None:
                self._panes.curpane(p)
            r=v
            if p != None:
                self._panes.curpane(p)
        else:
            r=''
            for row in self._panes.rows():
                for pane in row.panes():
                    r += pane.value()
        return r

    def paint(self):
        self.refresh()

    def refresh(self):
        if not self.ispaintable(): return
        window.paint(self, clear=False)
        screen = scr()
        if screen == None: return
        stdscr=screen.stdscr
        cx,cy=self.contentxy(); w,h=self.contentwh()
        cp=self.cp()
        if self._dirtytext or self._dirtysealoffsets:
            bc = self.blankchar()
            bcs = bc*w
            blankpane = pane(None, bc)
            seal=self.panes().seal()
            self._prevseal=seal

            # create self._seal
            if not self._seal:
                self._seal=[]
                for y in range(h):
                    self._seal.append([])
                    for x in range(w):
                        self._seal[y].append(None)

            rowlen=len(seal.rows())
            for y in range(h):
                if y+1<=rowlen: row=seal.rows()[y]
                else:           row=None
                if row:
                    panelen=len(row.panes())
                    for x in range(w):
                        if x+1<=panelen: p=row.panes()[x]
                        else:            p=None
                        if p:
                            prevpane=self._seal[y][x]

                            if prevpane:
                                prev_v=prevpane.value()
                                prev_hl = prevpane.hl()
                            else:
                                prev_hl=False
                                prev_v=None

                            v=p.value()

                            if v!= None and not self.isprintable(ord(v)):
                                v='?'

                            if v     ==None: v=' '
                            if prev_v==None: prev_v=' '
                            
                            if ( (p.hl() != prev_hl or v != prev_v)):
                                self._seal[y][x]=p.clone()
                                if p.hl() and not p.iscurrent():
                                    stdscr.addch(y+cy, x+cx, v, \
                                        curses.A_REVERSE)
                                else:
                                    stdscr.addch(y+cy, x+cx, v, cp)
                        else:
                            for i in range(x, w-x):
                                self._seal[y][x+i] = blankpane
                            remain=bc*(w-x)
                            stdscr.addstr(y+cy, x+cx, remain, cp)
                            break
                else:
                    for i in range(0, w):
                        self._seal[y][i] = blankpane
                    stdscr.addstr(y+cy, cx, bcs, cp)

            self._dirtysealoffsets=False
            self._dirtytext=       False

