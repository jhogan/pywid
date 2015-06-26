#! /usr/bin/python
# vim: set et ts=4 sw=4 fdm=marker
from widgets import *
class mainform(frm):
    def __init__(self):
        frm.__init__(self)
        self.initwidgets()
        self.fgbg('white', 'black')

        
    def txtfname_onchg(self, src, eargs):
        curpane = src.panes().curpane()
        currow = src.panes().currow()
        v = curpane.value()
        if v == ' ': v='<sp>'
        py = curpane.y()
        px = curpane.x()
        ry = currow.y()
        msg = "v: %s; px: %s; py: %s; ry: %s \n" % (v,px,py,ry)
        msg += "soff: %s " % str(src.panes()._sealoffset) 
        msg += "hl: %s\n" % curpane.hl()
        self._txtdbg.text(msg)


    def initwidgets(self):

        # pad
        w=txt()
        w.name='pad'
        w.xy(3,15)
        w.border('-', '|')
        w.corner('+')
        w.fgbg('black', 'white')
        w.pad(0,1)
        w.wh(65, 5)
        w.blankchar('_')
        w.editmode('win')
        #w.text('test\njesse james hogan\njesse james\ndelia maria hogan')
        #w.text('o\ntwo\nthree\nfour')
        if True:
            t=''
            f=open('/tmp/services')
            for l in f:
                t+=l
            w.text(t)

        w.onchg.append(self.txtfname_onchg)
        #w.onupdpos.append(self.txtfname_onchg)
        self._txtfname = w
        self.append(w)

        #dbg
        w = txt()
        w.name='dbg'
        w.xy(3,10)
        w.fgbg('black', 'white')
        w.wh(50,3)
        self._txtdbg = w
        w.editmode('win')
        
        self.append(w)

    

frm=mainform()
frm.border("","")
frm.fgbg('black', 'white')
frm.show()
scr().destroy()
