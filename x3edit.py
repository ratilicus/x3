import Tkinter

root = Tkinter.Tk()
root.title("Keysym Logger")

def reportEvent(event):
    print 'keysym=%s, keysym_num=%s' % (event.keysym, event.keysym_num)

def selectEvent(event):
    print event.widget.nearest(event.y)
    return False

shiplist  = Tkinter.Listbox(root, highlightthickness=2)
shiplist.grid(row=0,column=0,rowspan=2, sticky=Tkinter.W+Tkinter.N+Tkinter.S)
for i in xrange(64):
    shiplist.insert(Tkinter.END, 'Key %d' % i)
shiplist.bind('<Button-1>', selectEvent)
shiplist.bind('<B1-Motion>', selectEvent)


Tkinter.Label(root, text='Field 1').grid(row=0, column=1)
text  = Tkinter.Text(root, width=20, height=5, highlightthickness=2)
text.grid(row=0, column=2)
text.bind('<KeyPress>', reportEvent)

Tkinter.Label(root, text='Field 2').grid(row=1, column=1)
text2  = Tkinter.Text(root, width=20, height=5, highlightthickness=2)
text2.grid(row=1, column=2)


root.mainloop()
