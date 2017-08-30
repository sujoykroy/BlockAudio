from blockaudio.editors import AudioSequencer
from blockaudio.audio_blocks import AudioTimedGroup, AudioFileBlock
from blockaudio.audio_blocks import AudioFileInstru, AudioFormulaInstru
from blockaudio import formulators

instru_list = AudioFileInstru.load("/usr/share/hydrogen/data/drumkits/")
instru_list = None
sequencer = AudioSequencer(instru_list=instru_list)
sequencer.start()
