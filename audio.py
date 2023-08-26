import pyaudio
import wave
import threading


def stop(name):
    """Stops the music, removes it from the memory, and joins its thread"""
    sound = audio.playing.pop(name)
    sound.playing = False
    sound.stream.close()
    sound.thread.join()


def pause(name):
    """Pauses the music and join's its thread"""
    sound = audio.playing[name]
    sound.playing = False
    sound.thread.join()


def unpause(name):
    """Un-does everything that the pause function does"""
    sound = audio.playing[name]
    sound.playing = True
    if sound.loop:
        sound.thread = threading.Thread(target=sound.play, daemon=True)
    else:
        sound.thread = threading.Thread(target=sound.playOnce, daemon=True)
    sound.thread.start()


def stopAll():
    for name in audio.playing.copy():
        stop(name)


class audio:
    # Instantiate PyAudio and initialize PortAudio system resources
    p = pyaudio.PyAudio()
    # Save sounds by name
    playing = {}
    # Size of the chunks of the wavefile to be read
    chunk = 1024

    def __init__(self, name, loop=True):
        audio.playing[name] = self
        self.playing = True
        self.loop = loop
        self.wf = wave.open(f'{name}.wav', 'rb')
        self.stream = audio.p.open(format=audio.p.get_format_from_width(self.wf.getsampwidth()),
                                   channels=self.wf.getnchannels(),
                                   rate=self.wf.getframerate(),
                                   output=True)
        if loop:
            self.thread = threading.Thread(target=self.play, daemon=True)
        else:
            self.thread = threading.Thread(target=self.playOnce, daemon=True)
        self.thread.start()

    def play(self):
        """Endless function meant to be played in its own thread. Continuously reads and loops the music in chunks"""
        while self.playing:
            data = self.wf.readframes(self.chunk)
            self.stream.write(data)
            if not len(data):
                self.wf.rewind()

    def playOnce(self):
        """Endless function meant to be played in its own thread. Continuously reads the music in chunks"""
        while self.playing and len(data := self.wf.readframes(self.chunk)):
            self.stream.write(data)
