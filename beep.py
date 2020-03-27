import tkinter as tk
from tkinter import tkSnack

root = tk.Tk()
tkSnack.initializeSnack(root)

snd = tkSnack.Sound()
snd.read('basso.aiff')
snd.play(blocking=1)

def bell(loops):
    snd = tkSnack.Sound()
    snd.read('basso.aiff')
    

    #duration = 1000  # milliseconds
    #freq = 440  # Hz
    #winsound.Beep(freq, duration)
    #freq = 400  # Hz
    #winsound.Beep(freq, duration)
    i = 0
    for i in range(loops):
        snd.play(blocking=1)


    
bell(10)
