#!/usr/bin/python3
"""
Records a tone.
"""

import sounddevice as sd
import scipy.signal as sp
import scipy.fftpack as sf
import numpy as np
import matplotlib.pyplot as plt
import pygame
import queue

# sounddevice docs: https://python-sounddevice.readthedocs.io/en/0.3.12/usage.html#recording
# scipy.signal docs: https://docs.scipy.org/doc/scipy/reference/signal.html

# design for 8 kHz
fs = 40000 # sampling rate (Hz)
duration = .05 # block time (s)
freqs = [880, 500, 600, 700] # frequencies of interest (Hz)

def design_bandpass(low, high, fs, order):
    nyq = fs * 0.5
    return sp.butter(order, [low/nyq, high/nyq], btype='bandpass')
def apply_bandpass(signal):
    b, a = design_bandpass(390, 410, fs, order=3)
    print(b,a)
    return scipy.signal.lfilter(b, a, signal, axis=0)

class Recorder:
    def __init__(self):
        self.phases = np.zeros((10,len(freqs)))

    def callback(self, data, frames, time, status):
        n = data.shape[0]
        window = np.reshape(sp.windows.hamming(n), (n,1))
        signal = data[:] * window
        amplitudes = np.abs(np.real(sf.fft(signal, axis=0)[0:n//2]))
        phases = np.imag(sf.fft(signal, axis=0)[0:n//2])
        self.phases = np.roll(self.phases, 0)
        for index, freq in enumerate(freqs):
            location = int(freq*n/fs)
            amplitude = amplitudes[location,0]
            if amplitude > 1:
                print('freq {} on'.format(freq))
            self.phases[0,index] = phases[location,0] - phases[location, 1]
        print('{: >#016.4f}{: >#016.4f}{: >#016.4f}{: >#016.4f}'.format(self.phases[0,0], self.phases[0,1], self.phases[0,2], self.phases[0,3]))

pygame.init()
screen = pygame.display.set_mode((500,500))
r = Recorder()
stream = sd.InputStream(channels=2, samplerate=fs, callback=r.callback, blocksize=int(duration*fs))
with stream:
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
        phase = np.average(r.phases[:,0])
        if phase < -20:
            phase = -20
        if phase > 20:
            phase = 20
        screen.fill((0,0,0))
        pygame.draw.rect(screen, ((phase+20)*255/40, 0, 255 - (phase+20)*255/40), pygame.Rect(int((phase+20)*10), 0, 100, 500))
        pygame.display.flip()
