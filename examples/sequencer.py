from blockaudio.editors import AudioSequencer
from blockaudio.audio_blocks import AudioTimedGroup, AudioFileBlock
from blockaudio.audio_blocks import AudioFileInstru, AudioFormulaInstru
from blockaudio import formulators

instru_list = AudioFileInstru.load("/usr/share/hydrogen/data/drumkits/")

instru_list.insert(0, AudioFormulaInstru(filepath="/home/sujoy/Devel/BlockAudio/src/formulators/tomtom.py"))
instru_list1 = AudioFileInstru.load("/home/sujoy/Music/clip1.wav")
sequencer = AudioSequencer(
    instru_list=instru_list)
beat = sequencer.beat

files="""
/usr/share/hydrogen/data/drumkits/HipHop-2/kick_1.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/606_tom.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/chh_1.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/sn_1.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/rim_1.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/chh_2.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/chh_3.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/chh_4.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/funk_clap_1.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/fx_kick.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/kick_2.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/kick_3.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/kick_4.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/sn_2.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/sn_3.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/sn_4.wav
"""

group = AudioTimedGroup()

t = 0
c = 0
import os

for f in files.split("\n"):
    if not f:
        continue
    file_block = AudioFileBlock(f, sample_count=1*sequencer.beat.get_div_sample(1))
    file_block.load_samples()
    #file_block.set_inclusive_duration(sequencer.beat.get_div_sample(1))

    group.add_block(file_block, at=t, unit="sec", beat=beat)
    group.set_block_name(file_block, os.path.basename(f))
    t += sequencer.beat.get_div_time(1) # file_block.get_time_duration()
    file_block.loop = None
    if c== 0:
        file_block.loop = file_block.LOOP_STRETCH
        #file_block.loop = file_block.LOOP_INFINITE
    if True:
        if c==0:
            file_block.set_midi_channel(1)
        if c==10:
            file_block.set_midi_channel(1)
            file_block.set_note("D5")
        if c==20:
            file_block.set_midi_channel(1)
            file_block.set_note("E5")
    c += 1
    if c>2:
        break
#group.set_duration(sequencer.beat.get_div_time(3))

group2 = AudioTimedGroup()
file_instru = AudioFileInstru("/home/sujoy/Music/amsynth-out.wav")
t = 0
for nn in ["C5", "C3", "E5", "F5"]:
    group2.add_block(file_instru.create_note_block(nn), t, "sec", beat)
    t += sequencer.beat.get_div_time(1)

group3 = AudioTimedGroup()
formula_instru = AudioFormulaInstru(formulators.TomTomFormulator)
formula_instru.set_duration(sequencer.beat.get_div_time(1), sequencer.beat)
t = 0
for nn in ["C4", "C5", "E5", "F5"]:
    group3.add_block(formula_instru.create_note_block(nn), t, "sec", beat)
    t += sequencer.beat.get_div_time(1)

sequencer.load_block(group)
sequencer.start()
