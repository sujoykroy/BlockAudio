from audio_server import AudioServer
from audio_file_track import AudioFileTrack
from audio_samples_track import AudioSamplesTrack

import numpy
import Queue

import moviepy.editor as movie_editor
from gi.repository import GObject
GObject.threads_init()


from gi.repository import Gtk
class Win(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)
        self.connect("delete-event", self.quit)
        button = Gtk.Button("Play")
        button.connect("clicked", self.button_clicked)
        self.add(button)
        self.audio_server = AudioServer()

    def button_clicked(self, widget):
        self.play()

    def play(self):
        filename1 = "/home/sujoy/Music/KabhiJo.mp3"
        filename1 = "/home/sujoy/Music/clip1.wav"
        self.audio_server.master_track.add_track(AudioFileTrack(filename1))
        return
        filename2 = "/home/sujoy/Music/FromShreya/_my_music/David Guetta feat. Nicki Minaj - Turn Me On  [WWE  WrestleMa.mp3"
        audioclip2 = movie_editor.AudioFileClip(filename2)
        samples = audioclip2.to_soundarray(buffersize=1000).astype(numpy.float32)
        self.audio_server.master_track.add_track(AudioSamplesTrack(samples))
        #self.audio_server.master_track.play()
        #self.server2.push_data(samples)

    def quit(self, widget, event):
        if self.audio_server:
            self.audio_server.close()
        Gtk.main_quit()

win = Win()
win.set_size_request(200, 100)
win.show_all()
Gtk.main()


