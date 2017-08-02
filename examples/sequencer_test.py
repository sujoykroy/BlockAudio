from dawpy.editors import AudioSequencer
from dawpy.audio_blocks import AudioTimedGroup, AudioFileBlock

sequencer = AudioSequencer()

files="""
/usr/share/hydrogen/data/drumkits/HipHop-2/606_tom.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/chh_1.wav
/usr/share/hydrogen/data/drumkits/HipHop-2/kick_1.wav
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
    file_block = AudioFileBlock(f)
    file_block.load_samples()
    file_block.loop = False
    group.add_block(file_block, at=t)
    group.set_block_name(file_block, os.path.basename(f))
    t += file_block.get_time_duration()
    c += 1
    if c>4:
        break

sequencer.load_block(group)

from gi.repository import Gtk
Gtk.main()
