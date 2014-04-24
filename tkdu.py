#!/usr/bin/env python

#    This is tkdu.py, an interactive program to display disk usage
#    Copyright 2004 Jeff Epler <jepler@unpythonic.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import math, Tkinter, sys, os, stat, string, time, gzip, FileDialog
from tkFileDialog import askdirectory

MIN_PSZ = 1000
MIN_IPSZ = 240
MIN_W = 50
MIN_H = 15
VERTICAL = "vertical"
HORIZONTAL = "horizontal"
NUM_QUEUE = 25
FONT_FACE = ("helvetica", 12)
BORDER = 2
FONT_HEIGHT = 12
FONT_HEIGHT2 = 20

dircolors = ['#ff7070', '#70ff70', '#7070ff']
leafcolors = ['#bf5454', '#54bf54', '#5454bf']

def allocate(path, files, canvas, x, y, w, h, first, depth):
    tk_call = canvas.tk.call
    if w < MIN_W or h < MIN_H: return
    psz = w*h
    if psz < MIN_PSZ: return
    if path and path[-1] == "/":
        basename_idx = len(path)
        nslashes = string.count(path, os.sep) - 1
    else:
        basename_idx = len(path) + 1
        nslashes = string.count(path, os.sep)
    dircolor = dircolors[nslashes % len(dircolors)]
    leafcolor = leafcolors[nslashes % len(dircolors)]
    colors = (leafcolor, dircolor)
    totsz = 0
    ff = getkids(files, path)
    if not ff: return
    if ff[0][1] == '/': del ff[0]
    ff = ff[first:]
    for item in ff:
        totsz = totsz + item[0]
        item[2] = None

    if totsz == 0: return

    i = 0
    ratio = psz*1./totsz

    while i < len(ff) and w>2*BORDER and h>2*BORDER:
        if w > h:
            orient = VERTICAL
            usew = w - h*2./3
            if usew < 50: usew = 50
            if usew > 200: usew = 200
            first_height = ff[i][0]/usew*ratio
            while first_height < .65 * usew:
                usew = usew / 1.5
                first_height = ff[i][0]/usew*ratio
            want = usew * h / ratio
            maxcnt = h/30
        else:
            orient = HORIZONTAL
            useh = h - w*2./3
            if useh < 50: useh = 50
            if useh > 100: useh = 100
            first_width = ff[i][0]/useh*ratio
            while first_width < .65 * useh:
                useh = useh / 1.5
                first_width = ff[i][0]/useh*ratio
            want = useh * w / ratio
            maxcnt = w/30


        j = i+1
        use = ff[i][0]
        while j < len(ff) and use < want: #and j < i + maxcnt:
            use = use + ff[j][0]
            j=j+1

        if orient is VERTICAL:
            usew = use * ratio / h
            if usew <= 2*BORDER: break
            y0 = y
            for item in ff[i:j]:
                dy = item[0]/usew*ratio
                item[2] = (x, y0, usew, dy)
                y0 = y0 + dy
            x = x + usew
            w = w - usew
        else:
            useh = use * ratio / w
            if useh <= 2*BORDER: break
            x0 = x
            for item in ff[i:j]:
                dx = item[0]/useh*ratio
                item[2] = (x0, y, dx, useh)
                x0 = x0 + dx
            y = y + useh
            h = h - useh
        i = j

    for item in ff:
        sz = item[0]
        name = item[1]
        haskids = bool(getkids(files, name))
        color = colors[haskids]
        if item[2] is None: continue
        x, y, w, h = pos = item[2]
        if w > 3*BORDER and h > 3*BORDER:
            tk_call(canvas._w,
                "create", "rectangle",
                x+BORDER+2, y+BORDER+2, x+w-BORDER+1, y+h-BORDER+1,
                "-fill", "#3f3f3f",
                "-outline", "#3f3f3f")

        i = tk_call(canvas._w,
            "create", "rectangle",
            x+BORDER, y+BORDER, x+w-BORDER, y+h-BORDER,
            "-fill", color)
        canvas.map[int(i)] = name

        if h > FONT_HEIGHT+2*BORDER:
            w1 = w - 2*BORDER
            stem = name[basename_idx:]
            ssz = size(sz)
            text = "%s %s" % (name[basename_idx:], ssz)
            tw = int(tk_call("font", "measure", FONT_FACE, text))
            if tw > w1:
                if h > FONT_HEIGHT2 + 2*BORDER:
                    tw = max(
                        int(tk_call("font", "measure", FONT_FACE, stem)),
                        int(tk_call("font", "measure", FONT_FACE, ssz)))
                    if tw < w1:
                        text = "%s\n%s" % (stem, ssz)
                        i = tk_call(canvas._w, "create", "text",
                            x+BORDER+2, y+BORDER,
                            "-text", text,
                            "-font", FONT_FACE, "-anchor", "nw")
                        canvas.map[int(i)] = name
                        y = y + FONT_HEIGHT2
                        h = h - FONT_HEIGHT2
                        if w*h > MIN_PSZ and haskids and depth != 1:
                            queue(canvas, allocate, name, files, canvas,
                                x+2*BORDER, y+2*BORDER,
                                w-4*BORDER, h-4*BORDER, 0, depth-1)
                        continue
                text = stem
                tw = int(tk_call("font", "measure", FONT_FACE, text))
            if tw < w1:
                i = tk_call(canvas._w, "create", "text",
                        x+BORDER+2, y+BORDER,
                        "-text", text,
                        "-font", FONT_FACE, "-anchor", "nw")
                canvas.map[int(i)] = name
                y = y + FONT_HEIGHT
                h = h - FONT_HEIGHT
        if w*h > MIN_PSZ and haskids and depth != 1:
            queue(canvas, allocate, name, files, canvas,
                x+2*BORDER, y+2*BORDER,
                w-4*BORDER, h-4*BORDER, 0, depth-1)

def queue(c, *args):
    if c.aid is None:
        c.aid = c.after_idle(run_queue, c)
        c.configure(cursor="watch")
    c.queue.append(args)

def run_queue(c):
    queue = c.queue
    end = time.time() + .5
    while 1:
        if not queue:
            c.aid = None
            c.configure(cursor="")
            break
        if time.time() > end: break
        item = queue[0]
        del queue[0]
        apply(item[0], item[1:])
    if queue:
        c.aid = c.after_idle(run_queue, c)

def chroot(e, r):
    c = e.widget
    if not getkids(c.files, r):
        r = os.path.dirname(r)
        if r == c.cur: return
    if r is None:
        return
    if not r.startswith(c.root):
        c.bell()
        return
    c.cur = r
    c.first = 0
    e.width = c.winfo_width()
    e.height = c.winfo_height()
    reconfigure(e)

def item_under_cursor(e):
    c = e.widget
    try:
        item = c.find_overlapping(e.x, e.y, e.x, e.y)[-1]
    except IndexError:
        return None
    return  c.map.get(item, None)

def descend(e):
    c = e.widget
    item = item_under_cursor(e)
    chroot(e, item)

def ascend(e):
    c = e.widget
    parent = os.path.dirname(c.cur)
    chroot(e, parent)

def size(n):
    if n > 1024*1024*1024:
        return "%.1fGB" % (n/1024./1024/1024)
    elif n > 1024*1024:
        return "%.1fMB" % (n/1024./1024)
    elif n > 1024:
        return "%.1fKB" % (n/1024.)
    return "%d" % n

def scroll(e, dir):
    c = e.widget
    offset = c.first + 5*dir
    l = len(getkids(c.files, c.cur))
    if offset + 5 > l: offset = l-5
    if offset < 0: offset = 0
    if offset != c.first:
        c.first = offset
        e.width = c.winfo_width()
        e.height = c.winfo_height()
        reconfigure(e)

def schedule_tip(e):
    c = e.widget
    s = item_under_cursor(e)
    if not s: return
    sz = getname(c.files, s)
    s = "%s (%s)" % (s, size(sz))
    c.tipa = c.after(500, make_tip, e, s)

def make_tip(e, s):
    c = e.widget
    c.tipa = None
    c.tipl.configure(text=s)
    c.tip.wm_geometry("+%d+%d" % (e.x_root+5, e.y_root+5))
    c.tip.wm_deiconify()

def cancel_tip(e, c=None):
    if c is None:
        c = e.widget
    if c.tipa:
        c.after_cancel(c.tipa)
        c.tipa = None
    else:
        c.tip.wm_withdraw()

def reconfigure(e):
    c = e.widget
    w = e.width
    h = e.height
    c.t.wm_title("%s (%s)" % (c.cur, size(getname(c.files, c.cur))))
    c.delete("all")
    for cb in c.cb:
        c.after_cancel(cb)
    c.cb = []
    c.aid = None
    c.queue = []
    c.map = {}
    c.tipa = None
    if c.cur == "/":
        nslashes = -1
    else:
        nslashes = string.count(c.cur, os.sep) - 1
    parent = os.path.dirname(c.cur)
    color = dircolors[nslashes % len(dircolors)]
    c.configure(background=color)
    c.queue = [(allocate, c.cur, c.files, c, 0, 0, w, h, c.first, c.depth)]
    run_queue(c)
    
def putname_base(dict, name, base, size):
    try:
        dict[base][name] = size
    except:
        dict[base] = {name: size}

def putname(dict, name, size):
    base = os.path.dirname(name)
    try:
        dict[base][name] = size
    except:
        dict[base] = {name: size}

def getname(dict, name):
    base = os.path.dirname(name)
    return dict[base][0][name]

def getkids(dict, path):
    return dict.get(path, ((), {}))[1]
        
def doit(dir, files):
    sorted_files = {}
    for k, v in files.items():
        sv = map(lambda (k, v): [v, k, None], v.items())
        sv.sort()
        sv.reverse()
        sorted_files[k] = (v, sv)

    t = Tkinter.Tk()
    c = Tkinter.Canvas(t, width=1024, height=768)
    c.tip = Tkinter.Toplevel(t)
    c.tip.wm_overrideredirect(1)
    c.tipl = Tkinter.Label(c.tip)
    c.tipl.pack()
    c.pack(expand="yes", fill="both")
    c.files = sorted_files
    c.cur = c.root = dir
    c.t = t
    c.cb = []
    c.aid = None
    c.queue = []
    c.depth = 0
    c.first = 0
    c.bind("<Configure>", reconfigure)
    t.bind("<Unmap>", lambda e, c=c: cancel_tip(e, c))
    t.bind("<q>", lambda e, t=t: t.destroy())
    for i in range(10):
        t.bind("<Key-%d>" % i, lambda e, c=c, i=i: setdepth(e, c, i))
    c.bind("<Button-4>", lambda e: scroll(e, -1))
    c.bind("<Button-5>", lambda e: scroll(e, 1))
    if os.name == 'nt':
        c.bind("<Button-3>", ascend)
    else:
        c.bind("<Button-2>", ascend)
    c.tag_bind("all", "<Button-1>", descend)
    c.tag_bind("all", "<Enter>", schedule_tip)
    c.tag_bind("all", "<Leave>", cancel_tip)
    c.mainloop()

def setdepth(e, c, i):
    e.widget = c
    e.width = c.winfo_width()
    e.height = c.winfo_height()
    c.depth = i
    reconfigure(e)

def main(f = sys.stdin):
    files = {}
    firstfile = None
    for line in f.readlines():
        sz, name = string.split(line[:-1], None, 1)
#       name = name.split("/")
        sz = long(sz)*1024
        putname(files, name, sz)
    doit(name, files)

def du(dir, files, fs=0, ST_MODE=stat.ST_MODE, ST_SIZE = stat.ST_SIZE, S_IFMT = 0170000, S_IFDIR = 0040000, lstat = os.lstat, putname_base = putname_base, fmt="%%s%s%%s" % os.sep):
    tsz = 0

    try: fns = os.listdir(dir)
    except: return 0

    if not files.has_key(dir): files[dir] = {}
    d = files[dir]

    for fn in fns:
        fn = fmt % (dir, fn)

        try:
            info = lstat(fn)
        except:
            continue

        if info[ST_MODE] & S_IFMT == S_IFDIR:
            sz = du(fn, files) + long(info[ST_SIZE])
        else:
            sz = info[ST_SIZE]
        d[fn] = sz
        tsz = tsz + sz
    return tsz

def abspath(p):
    return os.path.normpath(os.path.join(os.getcwd(), p))

class DirDialog(FileDialog.LoadFileDialog):
    def __init__(self, master, title=None):
        FileDialog.LoadFileDialog.__init__(self, master, title)
        self.files.destroy()
        self.filesbar.destroy()

    def ok_command(self):
        file = self.get_selection()
        if not os.path.isdir(file):
            self.master.bell()
        else:
            self.quit(file)

    def filter_command(self, event=None):
        END="end"
        dir, pat = self.get_filter()
        try:
            names = os.listdir(dir)
        except os.error:
            self.master.bell()
            return
        self.directory = dir
        self.set_filter(dir, pat)
        names.sort()
        subdirs = [os.pardir]
        matchingfiles = []
        for name in names:
            fullname = os.path.join(dir, name)
            if os.path.isdir(fullname):
                subdirs.append(name)
        self.dirs.delete(0, END)
        for name in subdirs:
            self.dirs.insert(END, name)
        head, tail = os.path.split(self.get_selection())
        if tail == os.curdir: tail = ''
        self.set_selection(tail)

def main_builtin_du(args):
    import sys
    if len(args) > 1:
        p = args[1]
    else:
        t = Tkinter.Tk()
        t.wm_withdraw()
        p = askdirectory()
        if Tkinter._default_root is t:
            Tkinter._default_root = None
        t.destroy()
        if p is None:
            return
    files = {}

    if p == '-h' or p == '--help' or p == '-?':
        base = os.path.basename(args[0])
        print 'Usage:'
        print ' ', base, '<file.gz>     interpret file as gzipped du -ak output and visualize it'
        print ' ', base, '<file>        interpret file as du -ak output and visualize it'
        print ' ', base, '<folder>      analyze disk usage in that folder'
        print ' ', base, '-             interpret stdin input as du -ak output and visualize it'
        print ' ', base, '              ask for folder to analyze'
        print
        print 'Controls:'
        print '  * Press `q` to quit'
        print '  * LMB: zoom in to item'
        print '  * RMB: zoom out one level'
        print '  * Press `1`..`9`: Show that many nested levels'
        print '  * Press `0`: Show man nested levels'
        return

    if p == "-":
        main()
    else:
        p = abspath(p)
        if os.path.isfile(p):
            if p.endswith('.gz'):
                # gzipped file
                main(gzip.open(p, 'r'))
            else:
                main(open(p, 'r'))
        else:
            putname(files, p, du(p, files))
            doit(p, files)

if __name__ == '__main__':
    import sys
    main_builtin_du(sys.argv)

# vim:sts=4:sw=4:
