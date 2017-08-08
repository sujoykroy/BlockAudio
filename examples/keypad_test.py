from dawpy.editors import PianoKeypad
from dawpy import formulators
from dawpy.audio_blocks import AudioFormulaInstru, AudioFileInstru
from gi.repository import Gtk

formula_instru = AudioFormulaInstru(formulators.SineFormulator())
file_instru = AudioFileInstru("/home/sujoy/Music/amsynth-out.wav")

keypad = PianoKeypad(use_server_process=not True)

keypad.set_instru(formula_instru)
Gtk.main()
