from gi.repository import Gtk, Gdk
from MotionPicture.gui_utils import *
from MotionPicture.commons import *
from MotionPicture.audio_tools import AudioRawSamples
from MotionPicture.shapes import *
from audio_player import AudioPlayer
from audio_jack import AudioJack
from audio_raw_samples import AudioRawSamples

import numpy, scipy, os, parser
from scipy import interpolate
from moviepy.audio.AudioClip import AudioArrayClip
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import dump as XmlDump
from xml.etree.ElementTree import ElementTree as XmlTree
from xml.etree.ElementTree import Element as XmlElement


import numpy, time, imp
BASE_FREQUENCY = 440.

class PianoKeyBoardKey(TextShape):
    def __init__(self, board_key_name, piano_key_name, piano_key_scale):
        border_color = "000000"
        fill_color = "FFFFFF"
        super(PianoKeyBoardKey, self).__init__(
            anchor_at=Point(0, 0), border_color=border_color,
            border_width=2, fill_color=fill_color, width=10, height=20, corner_radius=0)
        self.board_key_name = board_key_name
        self.piano_key_name = piano_key_name
        self.piano_key = PianoKey.get_key("{0}{1}".format(piano_key_name, piano_key_scale))
        text = self.board_key_name  + "\n" + self.piano_key.name
        self.set_text(text)
        self.px = 0.
        self.py = 0.
        self.font = "8"

    def set_pressed(self, pressed):
        self.pressed= pressed
        if pressed:
            fill_color = "cccccc"
        else:
            fill_color = "ffffff"
        self.fill_color = fill_color

class PianoKeyboard(Gtk.DrawingArea):
    BOARD_KEY_NAMES = ["z s x d c v g b h n j m , l. ; /".split(),
                  "q 2 w 3 e r 5 t 6 y 7 u i 9 o 0 p [ = ] \\".split()
                 ]

    BOARD_KEYS = dict()

    def __init__(self, on_piano_board_key_action):
        super(PianoKeyboard, self).__init__()
        self.set_events(
            Gdk.EventMask.POINTER_MOTION_MASK|Gdk.EventMask.BUTTON_PRESS_MASK|\
            Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.SCROLL_MASK)
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_mouse_press)
        self.connect("button-release-event", self.on_mouse_release)
        self.piano_board_keys = []
        self.on_piano_board_key_action = on_piano_board_key_action
        self.normal_key_count = 0
        self.normal_key_counts = []
        for s in range(len(self.BOARD_KEY_NAMES)):
            board_key_names=self.BOARD_KEY_NAMES[s]

            normal_key_count = 0
            for k in range(len(board_key_names)):
                piano_key_name = PianoKey.KEY_SINGLE_NAMES[k%12]
                if piano_key_name[-1] == "#":
                    continue
                normal_key_count +=1
            self.normal_key_counts.append(normal_key_count)
            if normal_key_count>self.normal_key_count:
                self.normal_key_count = normal_key_count
        self.normal_key_count += 1
        piano_scale_start = 2
        self.piano_container_box = Shape(
            anchor_at=Point(0, 0), border_color=None, border_width=0, fill_color=None,
            width=500., height=100.)

        self.piano_key_width = self.piano_container_box.width/self.normal_key_count
        self.piano_key_height = self.piano_container_box.height*.5/len(self.BOARD_KEY_NAMES)

        for s in range(len(self.BOARD_KEY_NAMES)):
            board_key_names=self.BOARD_KEY_NAMES[s]
            x = (self.normal_key_count-self.normal_key_counts[s])*.5*self.piano_key_width
            offset_y = ((len(self.BOARD_KEY_NAMES)-s)*2-1)*self.piano_key_height
            for k in range(len(board_key_names)):
                mod_k = k%12
                board_key_name = self.BOARD_KEY_NAMES[s][k]
                piano_key_scale = piano_scale_start + s + int(math.floor(k/12.))
                piano_key_name = PianoKey.KEY_SINGLE_NAMES[mod_k]
                piano_board_key = PianoKeyBoardKey(
                    board_key_name, piano_key_name, piano_key_scale)
                PianoKeyboard.BOARD_KEYS[board_key_name] = piano_board_key
                piano_board_key.width = self.piano_key_width
                piano_board_key.height = self.piano_key_height
                px = x
                py = offset_y
                self.piano_board_keys.append(piano_board_key)
                if piano_key_name[-1] == "#":
                    px  -= self.piano_key_width*.5
                    py -= self.piano_key_height
                    x -= self.piano_key_width
                x += self.piano_key_width
                piano_board_key.px = px
                piano_board_key.py = py
                piano_board_key.move_to(px, py)
                piano_board_key.parent_shape = self.piano_container_box

        self.mouse_point = Point(0, 0)
        self.pressed_piano_board_key = None

    def on_mouse_press(self, widget, event):
        self.mouse_point.copy_from(event)
        if self.pressed_piano_board_key:
            self.pressed_piano_board_key.set_pressed(False)
            self.pressed_piano_board_key = None
        point = self.piano_container_box.transform_point(self.mouse_point)
        for piano_board_key in self.piano_board_keys:
            if piano_board_key.is_within(point):
                self.pressed_piano_board_key = piano_board_key
                piano_board_key.set_pressed(True)
                self.on_piano_board_key_action(piano_board_key.piano_key)
                break
        self.queue_draw()

    def press_piano_board_key(self, board_key):
        ret = False
        if board_key in PianoKeyboard.BOARD_KEYS:
            piano_board_key = PianoKeyboard.BOARD_KEYS[board_key]
            piano_board_key.set_pressed(True)
            self.on_piano_board_key_action(piano_board_key.piano_key, pressed=True)
            ret = True
        self.queue_draw()
        return ret

    def release_piano_board_key(self, board_key):
        ret = False
        if board_key in PianoKeyboard.BOARD_KEYS:
            piano_board_key = PianoKeyboard.BOARD_KEYS[board_key]
            piano_board_key.set_pressed(False)
            self.on_piano_board_key_action(piano_board_key.piano_key, pressed=False)
            ret = True
        self.queue_draw()
        return ret

    def on_mouse_release(self, widget, event):
        if self.pressed_piano_board_key:
            self.pressed_piano_board_key.set_pressed(False)
        self.pressed_piano_board_key = None
        self.queue_draw()

    def on_draw(self, widget, ctx):
        ww = widget.get_allocated_width()
        wh = widget.get_allocated_height()

        cbxw = self.piano_container_box.width
        cbxh = self.piano_container_box.height
        scale_x = ww/cbxw
        scale_y = wh/cbxh
        #scale_x = scale_y = scale = min(scale_x, scale_y)

        self.piano_container_box.scale_x = scale_x
        self.piano_container_box.scale_y = scale_y
        self.piano_container_box.move_to((ww-cbxw*scale_x)*.5, (wh-cbxh*scale_y)*.5)

        for piano_board_key in self.piano_board_keys:
            ctx.save()
            piano_board_key.pre_draw(ctx)
            piano_board_key.draw_path(ctx)
            ctx.restore()
            piano_board_key.draw_fill(ctx)

            ctx.save()
            piano_board_key.pre_draw(ctx)
            piano_board_key.draw_text(ctx)
            ctx.restore()

            ctx.save()
            piano_board_key.pre_draw(ctx)
            piano_board_key.draw_path(ctx)
            ctx.restore()
            piano_board_key.draw_border(ctx)

class PianoKey(object):
    KEYS = OrderedDict()
    KEY_SINGLE_NAMES = "C C# D D# E F F# G G# A A# B".split(" ")

    def __init__(self, index):
        self.index = index
        self.name = self.get_key_name(index)
        self.frequency = self.get_key_frequency(index)

    @classmethod
    def get_key(cls, name):
        if PianoKey.KEYS.key_exists(name):
            return PianoKey.KEYS[name]
        return None

    def __eq__(self, other):
        return isinstance(other, PianoKey) and other.name == self.name

    @classmethod
    def get_key_name(cls, index):
        if index == 0:
            return "A0"
        if index == 1:
            return "B0"
        if index == 2:
            return "B#0"
        key_index = (index-3)%12
        scale = ((index-key_index)/12) +1
        return "{0}{1}".format(cls.KEY_SINGLE_NAMES[key_index], scale)

    @classmethod
    def get_key_frequency(cls, index):
        return 2**((index+1-49)/12.)*440

    @classmethod
    def build_keys(cls):
        PianoKey.KEYS.clear()
        for i in range(88):
            key = cls(i)
            PianoKey.KEYS.add(key.name, key)

PianoKey.build_keys()

class InterpolatorContainer(object):
    def __init__(self, doc):
        self.doc = doc

    def __getattr__(self, name):
        return self.doc.interpolators[name]

class Document(object):
    def __init__(self, filename=None):
        self.polygons = dict()
        self.filename = filename
        self.load()
        self.interpolators = dict()
        self.build_interpolators()

    def new_polygon(self, name=None):
        i = 2
        if not name:
            name = "p"
        orig_name = name
        while name in self.polygons:
            name = orig_name + "{0}".format(i)
            i += 2
        polygon = Polygon(points=[Point(0,0), Point(1,0)])
        self.polygons[name] = polygon
        return name

    def get_polygon(self, name):
        if name in self.polygons:
            return self.polygons[name]
        return None

    def get_polygon_names(self):
        return sorted(self.polygons.keys())

    def rename_polygon(self, old_name, new_name):
        polygon = self.polygon(old_name)
        if not polygon:
            return
        if not new_name in self.polygons:
            self.polygons[new_name] = polygon
            del self.polygons[old_name]

    def load(self):
        try:
            tree = ET.parse(self.filename)
        except IOError as e:
            return
        except ET.ParseError as e:
            return
        root = tree.getroot()
        doc = root.find("doc")
        for polygon_elem in doc.findall(Polygon.TAG_NAME):
            polygon = Polygon.create_from_xml_element(polygon_elem)
            polygon_name = polygon_elem.attrib["name"]
            self.polygons[polygon_name] = polygon

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        root = XmlElement("root")

        doc = XmlElement("doc")
        root.append(doc)

        for polygon_name, polygon in self.polygons.items():
            polygon_elm = polygon.get_xml_element()
            polygon_elm.attrib["name"] = polygon_name
            doc.append(polygon_elm)

        tree = XmlTree(root)
        backup_file = None
        if filename is not None:
            if os.path.isfile(filename):
                backup_file = filename + ".bk"
                os.rename(filename, backup_file)
        try:
            tree.write(filename)
        except TypeError as e:
            if backup_file:
                os.rename(backup_file, filename)
                backup_file = None
        if backup_file:
            os.remove(backup_file)

    def build_interpolators(self):
        for polygon_name, polygon in self.polygons.items():
            self.interpolators[polygon_name] = get_interpolator_for_polygon(polygon)

class DocFormula(object):
    def __init__(self, doc, formula):
        self.doc_inpt = InterpolatorContainer(doc)
        self.formula = formula

    def get_value_at(self, t, base_t):
        return self.formula(self.doc_inpt, t, base_t)

class Interpolator(object):
    def __init__(self, xs, ys):
        self.formula = interpolate.PchipInterpolator(numpy.array(xs), numpy.array(ys))

    def get_value_at(self, t, base_t):
        t %= 1
        base_t %= 1
        return self.formula(base_t)

    def __call__(self, t, base_t=None):
        if base_t is None:
            base_t = t
        return self.get_value_at(t, base_t)

def get_interpolator_for_polygon(polygon):
    xs = []
    ys = []
    for point in sorted(polygon.points, key=lambda p: p.x):
        xs.append(point.x)
        ys.append(point.y)
    return Interpolator(xs, ys)

class CurveSamples(object):
    def __init__(self):
        self.xmin =  0.
        self.xmax =  1.
        self.ymin = -1.
        self.ymax = 1.
        self.sample_rate = 44100
        self.formulas = None
        self.set_duration(0)
        self.set_cycles(1)

    def get_x_min_max(self):
        return [self.xmin, self.xmax]

    def get_y_min_max(self):
        return [self.ymin, self.ymax]

    def get_y_base(self):
        return 0.0

    def get_segment_count(self):
        if not self.formulas:
            return 1
        return len(self.formulas)

    def set_cycles(self, cycles):
        self.cycles = int(cycles)

    def set_duration(self, duration):
        self.duration = duration
        self.period_sample_count = self.sample_rate*self.duration
        if self.period_sample_count != 0:
            self.step_duration = 1.0/self.period_sample_count
            self.step_values = numpy.arange(0, 1, self.step_duration)
        else:
            self.step_values = numpy.array([1.])

    def get_sample_at_x(self, segment_index, x):
        if not self.formulas:
            return None
        if self.duration>0:
            base_x = x*self.duration*BASE_FREQUENCY
            base_x %= 1
        else:
            base_x = x
        formula = self.formulas[segment_index]
        return formula.get_value_at(x, base_x)

    def get_audio_samples(self, frequency):
        if len(self.formulas)==0:
            return None

        base_period = 1.0/frequency
        base_period_sample_count = self.sample_rate*base_period
        base_step_duration = 1.0/base_period_sample_count
        base_step_values = numpy.arange(0, 1, base_step_duration)

        if self.duration>0:
            duration_mult = int(math.ceil(self.duration*frequency))
            round_duration = duration_mult/frequency
            base_step_values = numpy.tile(base_step_values, duration_mult)
            period_sample_count = base_step_values.shape[0]
            step_duration = 1.0/period_sample_count
            step_values = numpy.arange(0, 1, step_duration)
            #print "duration_mult", duration_mult, "round_duration", round_duration, "period_sample_count ", period_sample_count
        else:
            step_values = base_step_values

        total_samples = None
        for si in range(len(self.formulas)):
            formula = self.formulas[si]
            samples = formula.get_value_at(step_values, base_step_values)

            for i in range(self.cycles):
                samples = numpy.concatenate((samples, samples[:len(step_values)]))

            if total_samples is None:
                total_samples = samples
            else:
                total_samples = numpy.stack((total_samples, samples), axis=0)
            samples = None
        if len(total_samples.shape)==1:
            total_samples = numpy.stack((total_samples, total_samples))
        return total_samples

    def build_formulas_from_text(self, text, doc):
        self.formulas = eval(parser.expr(text).compile())
        for i in range(len(self.formulas)):
            self.formulas[i] = DocFormula(doc, self.formulas[i])

    def build_formulas_from_list(self, list_data, doc):
        self.formulas = list(list_data)
        for i in range(len(self.formulas)):
            self.formulas[i] = DocFormula(doc, self.formulas[i])
        print self.formulas

    def build_formulas_from_polygons(self, polygons):
        self.formulas = []
        for pi in range(len(polygons)):
            polygon = polygons[pi]
            poly = get_interpolator_for_polygon(polygon)
            self.formulas.append(poly)

class SoundCurveViewer(ArrayViewer):
    def __init__(self, keyboard, on_play_callback=None, curve_modified_callback=None):
        super(SoundCurveViewer, self).__init__(keyboard)
        self.on_play_callback = on_play_callback
        self.curve_modified_callback = curve_modified_callback
        self.polygons = []
        self.audio_player = None
        self.selected_point = None

        self.move_control_box.remove(self.move_backward_button)
        self.move_control_box.remove(self.move_backward_button)
        self.move_control_box.remove(self.threshold_entry)
        self.move_control_box.remove(self.yvalue_apply_button)
        self.move_control_box.remove(self.threshold_entry)
        self.move_control_box.remove(self.threshold_label)
        self.move_control_box.remove(self.multiply_label)
        self.move_control_box.remove(self.threshold_entry)
        self.move_control_box.remove(self.exact_selection_button)
        self.move_control_box.remove(self.exact_selection_entry)

        self.play_start_curve_button = Gtk.Button("Play")
        self.play_start_curve_button.connect("clicked", self.play_curve_button_clicked, "start")
        self.play_stop_curve_button = Gtk.Button("Stop")
        self.play_stop_curve_button.connect("clicked", self.play_curve_button_clicked, "stop")
        self.piano_key_combo_box = NameValueComboBox()
        self.piano_key_combo_box.build_and_set_model(PianoKey.KEYS.keys)
        self.piano_key_combo_box.set_value("C4")
        self.segment_cycle_entry = Gtk.Entry()
        self.segment_cycle_entry.set_text("10")
        self.segment_cycle_entry.connect("changed", self.segment_cycle_entry_changed)
        self.segment_duration_entry = Gtk.Entry()
        self.segment_duration_entry.set_text("0")
        self.segment_duration_entry.connect("changed", self.segment_duration_entry_changed)

        self.move_control_box.pack_start(
                self.piano_key_combo_box, expand=False,  fill=False, padding=0)
        self.move_control_box.pack_start(
                self.segment_cycle_entry, expand=False,  fill=False, padding=0)
        self.move_control_box.pack_start(
                Gtk.Label("Cycles"), expand=False,  fill=False, padding=0)
        self.move_control_box.pack_start(
                self.segment_duration_entry, expand=False,  fill=False, padding=0)
        self.move_control_box.pack_start(
                Gtk.Label("Seconds"), expand=False,  fill=False, padding=0)
        self.move_control_box.pack_start(
                self.play_start_curve_button, expand=False,  fill=False, padding=0)
        self.move_control_box.pack_start(
                self.play_stop_curve_button, expand=False,  fill=False, padding=0)

        self.curve_audio_raw_segment = None
        self.sample_stroke_width = 5

    def segment_cycle_entry_changed(self, widget):
        self.samples.set_cycles(Text.parse_number(widget.get_text()))

    def segment_duration_entry_changed(self, widget):
        self.samples.set_duration(Text.parse_number(widget.get_text()))
        self.redraw()

    def set_samples(self, samples):
        super(SoundCurveViewer, self).set_samples(samples)
        self.segment_cycle_entry.set_text("{0}".format(samples.cycles))
        self.segment_duration_entry.set_text("{0}".format(samples.duration))

    def set_polygons(self, *polygons):
        del self.polygons[:]
        self.polygons.extend(polygons)
        self.samples.build_formulas_from_polygons(polygons)

    def play_curve_button_clicked(self, widget, mode):
        #if self.curve_audio_raw_segment:
        #    self.audio_player.remove_segment(self.curve_audio_raw_segment)
        #    self.curve_audio_raw_segment = None
        #self.audio_player.clear_queue()
        if mode == "seamless-start" and self.curve_audio_raw_segment is None:
            return
        if mode.find("start")>=0:
            if self.polygons:
                self.samples.build_formulas_from_polygons(self.polygons)
            piano_key = PianoKey.get_key(name=self.piano_key_combo_box.get_value())
            samples = self.samples.get_audio_samples(piano_key.frequency)
            if samples is None:
                return
            new_segment = AudioRawSamples(samples, self.audio_player.sample_rate)
            if self.on_play_callback:
                self.on_play_callback()
            if self.curve_audio_raw_segment is None:
                self.audio_player.add_segment(new_segment)
            else:
                self.audio_player.replace_segment(self.curve_audio_raw_segment, new_segment)
            self.curve_audio_raw_segment = new_segment
            self.play_stop_curve_button.show()
            self.play_start_curve_button.hide()
        else:
            self.play_start_curve_button.show()
            self.play_stop_curve_button.hide()
            if self.curve_audio_raw_segment:
                self.audio_player.remove_segment(self.curve_audio_raw_segment)
            self.curve_audio_raw_segment = None
            self.audio_player.clear_queue()

    def on_drawing_area_draw(self, widget, ctx):
        super(SoundCurveViewer, self).on_drawing_area_draw(widget, ctx)
        if self.samples is None or not self.polygons:
            return

        widget_width = widget.get_allocated_width()
        widget_height = widget.get_allocated_height()

        y_segment_count = self.samples.get_segment_count()
        for segment_index in range(y_segment_count):
            polygon = self.polygons[segment_index]
            for point in polygon.points:
                point = self.graph2screen(segment_index, point)
                ctx.new_path()
                ctx.save()
                ctx.translate(point.x, point.y)
                ctx.scale(10, 10)
                ctx.move_to(.5,0)
                ctx.arc(0,0,.5,0, 2*math.pi)
                ctx.close_path()
                ctx.restore()

                draw_stroke(ctx, 2, "0000FF")

    def on_drawing_area_mouse_press(self, widget, event):
        self.mouse_pressed = True
        self.selected_point = None

        if self.samples is None:
            return
        if self.polygons and event.button == 1:#Left mouse
            si, graph_point = self.screen2graph(self.mouse_point)
            added = False
            if event.type == Gdk.EventType._2BUTTON_PRESS:#double button click
                self.polygons[si].add_point(graph_point)
                added = True
            if not added:
                for pi in range(len(self.polygons)):
                    polygon = self.polygons[pi]
                    for point in polygon.points:
                        screen_point = self.graph2screen(pi, point)
                        if self.mouse_point.distance(screen_point)<10:
                            self.selected_point=(pi, point)
                            break
            if self.selected_point is None:
                self.selection = [graph_point.x, graph_point.x]
            self.redraw()

    def on_drawing_area_mouse_release(self, widget, event):
        self.mouse_pressed = False
        if self.selection:
            if self.selection[0] == self.selection[1]:
                self.selection = None
        self.rebuild_formulas()
        if self.polygons and self.selected_point:
            if self.curve_modified_callback:
                self.curve_modified_callback()
        self.selected_point = None

    def rebuild_formulas(self):
        if self.polygons:
            self.samples.build_formulas_from_polygons(self.polygons)
        self.redraw()

    def delete_selected_point(self):
        if self.selected_point:
            pi, point = self.selected_point
            self.polygons[pi].remove_point(point)
            self.selected_point = None
            self.rebuild_formulas()

    def on_drawing_area_mouse_move(self, widget, event):
        self.mouse_point.copy_from(event)
        if self.mouse_pressed and self.selected_point:
            pi, point = self.selected_point
            si, ms_point = self.screen2graph(self.mouse_point)
            if pi != si:
                return
            point.copy_from(ms_point)
            if self.polygons:
                self.samples.build_formulas_from_polygons(self.polygons)
            self.redraw()
        else:
            super(SoundCurveViewer, self).on_drawing_area_mouse_move(widget, event)

class SoundGeneratorEditor(Gtk.Window):
    def __init__(self, filename=None, quit_callback=None, width=100, height=200):
        Gtk.Window.__init__(self)
        self.doc = Document(filename)
        self.quit_callback = quit_callback
        self.keyboard = Keyboard()

        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_size_request(width, height)
        self.connect("delete-event", self.quit)
        self.connect("key-press-event", self.on_drawing_area_key_press)
        self.connect("key-release-event", self.on_drawing_area_key_release)

        self.topmost_box = Gtk.HBox()
        self.add(self.topmost_box)

        self.root_box = Gtk.VBox()
        self.topmost_box.pack_start(self.root_box, expand=True,  fill=True, padding=0)


        self.curve_viewer = SoundCurveViewer(self.keyboard,
            curve_modified_callback = self.on_curve_modified)
        self.curve_viewer.set_samples(CurveSamples())
        self.root_box.pack_start(
            self.curve_viewer.get_container_box(), expand=True,  fill=True, padding=0)

        self.polygon_control_box = Gtk.HBox()
        self.root_box.pack_start(self.polygon_control_box, expand=False,  fill=False, padding=0)

        self.polygon_names_combo_box = NameValueComboBox()
        self.polygon_names_combo_box.build_and_set_model(self.doc.get_polygon_names())

        self.polygon_names_combo_box.connect("changed", self.polygon_names_combo_box_changed)
        self.create_new_curve_button = Gtk.Button("New Curve")
        self.create_new_curve_button.connect("clicked", self.create_new_curve_button_clicked)

        self.polygon_control_box.pack_start(
                self.polygon_names_combo_box, expand=False,  fill=False, padding=0)
        self.polygon_control_box.pack_start(
                self.create_new_curve_button, expand=False,  fill=False, padding=0)

        self.mix_viewer = SoundCurveViewer(self.keyboard, self.on_mix_viewer_play_started)
        self.mix_viewer.set_samples(CurveSamples())
        self.mix_viewer.sample_stroke_width = 1
        self.mix_viewer.segment_duration_entry.set_text("1")
        self.root_box.pack_start(
            self.mix_viewer.get_container_box(), expand=True,  fill=True, padding=0)

        self.mix_control_box = Gtk.HBox()
        self.root_box.pack_start(self.mix_control_box, expand=False,  fill=False, padding=0)

        self.load_formula_button = Gtk.Button("Reload Formula")
        self.load_formula_button.connect("clicked", self.load_formula_button_clicked)

        self.mix_control_box.pack_start(
                self.load_formula_button, expand=False,  fill=False, padding=0)

        self.samples_viewer = ArrayViewer(self.keyboard)
        self.root_box.pack_start(
            self.samples_viewer.get_container_box(), expand=True,  fill=True, padding=0)

        self.piano_keyboard_hbox = Gtk.HBox()
        self.root_box.pack_start(
            self.piano_keyboard_hbox, expand=False, fill=False, padding=0)

        self.piano_keyboard = PianoKeyboard(self.on_piano_board_key_action)
        self.piano_keyboard_hbox.pack_start(
            self.piano_keyboard, expand=False,  fill=False, padding=0)
        self.piano_keyboard.set_size_request(500, 100)

        self.curve_audio_raw_segment = None
        self.show_all()

        self.audio_player = AudioPlayer(2)
        self.audio_player.start()

        self.live_audio_player = AudioPlayer(1)
        self.live_audio_player.set_loop(False)
        self.live_audio_player.start()

        self.curve_viewer.audio_player = self.audio_player
        self.mix_viewer.audio_player = self.audio_player
        self.piano_mode = True
        self.pressed_piano_keys = OrderedDict()
        self.piano_segments = dict()
        self.last_key_press_at = time.time()
        self.audio_raw_segment = None
        self.seamless = True
        self.last_piano_segment = None

    def on_curve_modified(self):
        self.load_formula_button_clicked(widget=None)
        self.mix_viewer.play_curve_button_clicked(widget=None, mode="seamless-start")

    def on_piano_board_key_action(self, piano_key, pressed=True):
        if pressed:
            diff_time = time.time()-self.last_key_press_at
            sensi_time = .01
            ajack = AudioJack.get_thread()
            if not ajack.record and not False:
                ajack.set_record_file("/home/sujoy/Temporary/dawpy_recor.wav")
                ajack.output_record  = True
                ajack.record = True

            if piano_key.name not in self.piano_segments:
                new_samples = self.mix_viewer.samples.get_audio_samples(piano_key.frequency)
                new_raw_segment = AudioRawSamples(new_samples, self.live_audio_player.sample_rate)
                self.piano_segments[piano_key.name] = new_raw_segment
            piano_segment = self.piano_segments[piano_key.name]
            if  not self.pressed_piano_keys.key_exists(piano_key.name):
                if self.seamless:
                    if self.last_piano_segment is None:
                        self.live_audio_player.add_segment(piano_segment, current_time_at=True)
                    else:
                        self.live_audio_player.replace_segment(self.last_piano_segment, piano_segment)
                else:
                    if diff_time<sensi_time and len(self.pressed_piano_keys)>0:
                        last_key_name = self.pressed_piano_keys.keys[-1]
                        last_piano_segment = self.piano_segments[last_key_name]
                        piano_segment.start_at_size = last_piano_segment.start_at_size
                    self.live_audio_player.add_segment(piano_segment, current_time_at=True)
                self.pressed_piano_keys.add(piano_key.name, time.time())
                self.last_key_press_at = time.time()
                self.last_piano_segment = piano_segment
        else:
            if not self.seamless and piano_key.name in self.piano_segments:
                raw_segment = self.piano_segments[piano_key.name]
                #raw_segment.start_at_size -= raw_segment.get_duration_size()*(1-.05)
                self.live_audio_player.remove_segment(raw_segment)
            if self.pressed_piano_keys.key_exists(piano_key.name):
                self.pressed_piano_keys.remove(piano_key.name)

    def load_formula_button_clicked(self, widget):
        self.doc.build_interpolators()

        formula_filename = os.path.join(os.path.dirname(__file__), "formula_sample.py")

        if False:
            formula_file = open(formula_filename, "r")
            formula_text = formula_file.read()
            formula_file.close()
            self.mix_viewer.samples.build_formulas_from_text(formula_text, self.doc)
        else:
            self.formula_machine=imp.load_source("formula_machine", formula_filename)
            self.mix_viewer.samples.build_formulas_from_list(self.formula_machine.formulas, self.doc)

        self.mix_viewer.redraw()
        self.pressed_piano_keys = OrderedDict()
        self.piano_segments = dict()
        #self.live_audio_player.remove_all_segments()

    def polygon_names_combo_box_changed(self, widget):
        polygon_name = widget.get_value()
        self.curve_viewer.set_polygons(self.doc.get_polygon(polygon_name))
        self.curve_viewer.redraw()

    def create_new_curve_button_clicked(self, widget):
        polygon_name = self.doc.new_polygon()
        self.polygon_names_combo_box.build_and_set_model(self.doc.get_polygon_names())
        self.polygon_names_combo_box.set_value(polygon_name)

    def on_mix_viewer_play_started(self):
        audio_segment = self.mix_viewer.curve_audio_raw_segment
        self.samples_viewer.set_samples(audio_segment)
        self.samples_viewer.redraw()

        if False:
            clip = AudioArrayClip(audio_segment.samples.T, fps=audio_segment.sample_rate)
            clip.write_audiofile("/home/sujoy/Temporary/mix_viewer.wav")

    def on_drawing_area_key_press(self, widget, event):
        ret = False
        self.keyboard.set_keypress(event.keyval, pressed=True)
        if self.piano_mode and not self.keyboard.is_control_shift_pressed():
            if self.piano_keyboard.press_piano_board_key(event.string):
                ret = True
        return ret

    def on_drawing_area_key_release(self, widget, event):
        ret = False
        if self.keyboard.control_key_pressed:
            if event.keyval == Gdk.KEY_s:
                self.doc.save()
            if event.keyval == Gdk.KEY_x:
                self.curve_viewer.delete_selected_point()
                self.on_curve_modified()
            if event.keyval == Gdk.KEY_p:
                self.piano_mode = not self.piano_mode
        if  self.piano_mode and not self.keyboard.is_control_shift_pressed():
            if self.piano_keyboard.release_piano_board_key(event.string):
                ret = True
        self.keyboard.set_keypress(event.keyval, pressed=False)
        return ret

    def quit(self, widget, event):
        if self.audio_player:
            self.audio_player.close()
            self.audio_player = None
        if self.live_audio_player:
            self.live_audio_player.close()
            self.live_audio_player = None
        if self.quit_callback:
            self.quit_callback()


def on_quit():
    Gtk.main_quit()
    audio_jack = AudioJack.get_thread()
    if audio_jack:
        audio_jack.close()

sound_gn_editor = SoundGeneratorEditor(quit_callback=on_quit, filename="/home/sujoy/Temporary/sd.xml")

Gtk.main()
