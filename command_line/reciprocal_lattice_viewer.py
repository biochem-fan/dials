# LIBTBX_PRE_DISPATCHER_INCLUDE_SH export PHENIX_GUI_ENVIRONMENT=1
# LIBTBX_PRE_DISPATCHER_INCLUDE_SH export BOOST_ADAPTBX_FPE_DEFAULT=1

from __future__ import division
from gltbx import wx_viewer
import copy
import wx
import wxtbx.utils
from gltbx.gl import *
import gltbx
from scitbx.math import minimum_covering_sphere
from scitbx.array_family import flex
import libtbx.phil

master_phil = libtbx.phil.parse("""
  data = None
    .type = path
    .optional = False
  reverse_phi = False
    .type = bool
    .optional = True
  beam_centre = None
    .type = floats(size=2)
    .help = "Fast, slow beam centre coordinates (mm)."
  show_rotation_axis = False
    .type = bool
  show_beam_vector = False
    .type = bool
  d_min = None
    .type = float(value_min=0.0)
  display = *all unindexed indexed
    .type = choice
  marker_size = 1
    .type = int(value_min=1)
""")

def settings () :
  return master_phil.fetch().extract()

class ReciprocalLatticeViewer(wx.Frame):
  def __init__(self, *args, **kwds):
    wx.Frame.__init__(self, *args, **kwds)
    self.parent = self.GetParent()
    self.statusbar = self.CreateStatusBar()
    self.sizer = wx.BoxSizer(wx.HORIZONTAL)
    self.detector = None
    self.beam = None
    self.scan = None
    self.goniometer = None
    self.reflections = None

    app = wx.GetApp()
    if (getattr(app, "settings", None) is not None) :
      # XXX copying the initial settings avoids awkward interactions when
      # multiple viewer windows are opened
      self.settings = copy.deepcopy(app.settings)
    else :
      self.settings = settings()

    self.create_settings_panel()
    self.sizer.Add(self.settings_panel, 0, wx.EXPAND)
    self.create_viewer_panel()
    self.sizer.Add(self.viewer, 1, wx.EXPAND|wx.ALL)
    #self.SetupToolbar()
    #self.SetupMenus()
    #self.add_view_specific_functions()
    #self.SetMenuBar(self.menubar)
    #self.toolbar.Realize()
    self.SetSizer(self.sizer)
    self.sizer.SetSizeHints(self)
    self.Bind(wx.EVT_CLOSE, self.OnClose, self)
    self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy, self)
    self.Bind(wx.EVT_ACTIVATE, self.OnActive)
    self.viewer.SetFocus()

  def OnActive (self, event) :
    if (self.IsShown()) and (type(self.viewer).__name__ != "_wxPyDeadObject") :
      self.viewer.Refresh()

  def OnClose (self, event) :
    self.Unbind(wx.EVT_ACTIVATE)
    self.Destroy()
    event.Skip()

  def OnDestroy (self, event) :
    if (self.parent is not None) :
      self.parent.viewer = None
    event.Skip()

  def create_viewer_panel (self) :
    self.viewer = MyGLWindow(settings=self.settings, parent=self, size=(800,600),
      style=wx.glcanvas.WX_GL_DOUBLEBUFFER,
      #orthographic=True
      )

  def create_settings_panel (self) :
    self.settings_panel = settings_window(self, -1, style=wx.RAISED_BORDER)

  def load_models(self, imagesets, reflections):
    self.imagesets = imagesets
    self.reflections = reflections
    if self.imagesets[0].get_goniometer() is not None:
      self.viewer.set_rotation_axis(
        self.imagesets[0].get_goniometer().get_rotation_axis())
    self.viewer.set_beam_vector(self.imagesets[0].get_beam().get_s0())

    detector = self.imagesets[0].get_detector()
    beam = self.imagesets[0].get_beam()
    if self.settings.beam_centre is None:
      try:
        panel_id, self.settings.beam_centre \
          = detector.get_ray_intersection(beam.get_s0())
      except RuntimeError:
        pass
    else:
      from dxtbx.model.detector_helpers import set_mosflm_beam_centre
      set_mosflm_beam_centre(detector, beam, tuple(reversed(
        self.settings.beam_centre)))
    if self.settings.beam_centre is not None:
      self.settings_panel.beam_fast_ctrl.SetValue(self.settings.beam_centre[0])
      self.settings_panel.beam_slow_ctrl.SetValue(self.settings.beam_centre[1])
    self.map_points_to_reciprocal_space()

  def map_points_to_reciprocal_space(self):
    goniometer = copy.deepcopy(self.goniometer)
    if goniometer is not None and self.settings.reverse_phi:
      goniometer.set_rotation_axis([-i for i in goniometer.get_rotation_axis()])
    from dials.algorithms.indexing import indexer

    reflections_input = self.reflections

    if reflections_input.has_key('miller_index'):
      indexed_sel = (reflections_input['miller_index'] != (0,0,0))
      if self.settings.display == 'indexed':
        reflections_input = reflections_input.select(indexed_sel)
      elif self.settings.display == 'unindexed':
        reflections_input = reflections_input.select(~indexed_sel)

    from dials.array_family import flex
    reflections = flex.reflection_table()
    for i, imageset in enumerate(self.imagesets):
      if 'imageset_id' in reflections_input:
        sel = (reflections_input['imageset_id'] == i)
      else:
        sel = (reflections_input['id'] == i)
      refl = indexer.indexer_base.map_spots_pixel_to_mm_rad(
        reflections_input.select(sel),
        imageset.get_detector(), imageset.get_scan())

      indexer.indexer_base.map_centroids_to_reciprocal_space(
        refl, imageset.get_detector(), imageset.get_beam(),
        imageset.get_goniometer())
      reflections.extend(refl)

    d_spacings = 1/reflections['rlp'].norms()
    if self.settings.d_min is not None:
      reflections = reflections.select(d_spacings > self.settings.d_min)
    else:
      self.settings.d_min = flex.min(d_spacings)
      self.settings_panel.d_min_ctrl.SetValue(self.settings.d_min)
    points = reflections['rlp'] * 100
    self.viewer.set_points(points)

  def update_settings(self, *args, **kwds):
    detector = self.imagesets[0].get_detector()
    beam = self.imagesets[0].get_beam()
    from dxtbx.model.detector_helpers import set_mosflm_beam_centre
    set_mosflm_beam_centre(detector, beam, tuple(reversed(
      self.settings.beam_centre)))
    self.imagesets[0].set_detector(detector)
    self.imagesets[0].set_beam(beam)
    self.map_points_to_reciprocal_space()
    self.viewer.update_settings(*args, **kwds)


class settings_window (wxtbx.utils.SettingsPanel) :
  def __init__ (self, *args, **kwds) :
    wxtbx.utils.SettingsPanel.__init__(self, *args, **kwds)
    self.Bind(wx.EVT_CHAR, self.OnChar)

  def OnChar (self, event) :
    self.GetParent().viewer.OnChar(event)

  def add_controls (self) :
    # d_min control
    from wx.lib.agw import floatspin
    self.d_min_ctrl = floatspin.FloatSpin(parent=self, increment=0.05, digits=2)
    self.d_min_ctrl.Bind(wx.EVT_SET_FOCUS, lambda evt: None)
    if (wx.VERSION >= (2,9)) : # XXX FloatSpin bug in 2.9.2/wxOSX_Cocoa
      self.d_min_ctrl.SetBackgroundColour(self.GetBackgroundColour())
    box = wx.BoxSizer(wx.HORIZONTAL)
    self.panel_sizer.Add(box)
    label = wx.StaticText(self,-1,"High resolution:")
    box.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    box.Add(self.d_min_ctrl, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    self.Bind(floatspin.EVT_FLOATSPIN, self.OnChangeSettings, self.d_min_ctrl)

    ctrls = self.create_controls(
      setting="show_rotation_axis",
      label="Show rotation axis")
    self.panel_sizer.Add(ctrls[0], 0, wx.ALL, 5)
    ctrls = self.create_controls(
      setting="show_beam_vector",
      label="Show beam vector")
    self.panel_sizer.Add(ctrls[0], 0, wx.ALL, 5)
    ctrls = self.create_controls(
      setting="reverse_phi",
      label="Reverse phi direction")
    self.panel_sizer.Add(ctrls[0], 0, wx.ALL, 5)

    self.beam_fast_ctrl = floatspin.FloatSpin(parent=self, increment=0.01, digits=2)
    self.beam_fast_ctrl.Bind(wx.EVT_SET_FOCUS, lambda evt: None)
    if (wx.VERSION >= (2,9)) : # XXX FloatSpin bug in 2.9.2/wxOSX_Cocoa
      self.beam_fast_ctrl.SetBackgroundColour(self.GetBackgroundColour())
    box = wx.BoxSizer(wx.HORIZONTAL)
    self.panel_sizer.Add(box)
    label = wx.StaticText(self,-1,"Beam fast")
    box.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    box.Add(self.beam_fast_ctrl, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    self.Bind(floatspin.EVT_FLOATSPIN, self.OnChangeSettings, self.beam_fast_ctrl)

    self.beam_slow_ctrl = floatspin.FloatSpin(parent=self, increment=0.01, digits=2)
    self.beam_slow_ctrl.Bind(wx.EVT_SET_FOCUS, lambda evt: None)
    if (wx.VERSION >= (2,9)) : # XXX FloatSpin bug in 2.9.2/wxOSX_Cocoa
      self.beam_slow_ctrl.SetBackgroundColour(self.GetBackgroundColour())
    box = wx.BoxSizer(wx.HORIZONTAL)
    self.panel_sizer.Add(box)
    label = wx.StaticText(self,-1,"Beam slow")
    box.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    box.Add(self.beam_slow_ctrl, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    self.Bind(floatspin.EVT_FLOATSPIN, self.OnChangeSettings, self.beam_slow_ctrl)

    self.marker_size_ctrl = floatspin.FloatSpin(parent=self, increment=1, digits=0,
                                          min_val=1)
    self.marker_size_ctrl.Bind(wx.EVT_SET_FOCUS, lambda evt: None)
    if (wx.VERSION >= (2,9)) : # XXX FloatSpin bug in 2.9.2/wxOSX_Cocoa
      self.marker_size_ctrl.SetBackgroundColour(self.GetBackgroundColour())
    box = wx.BoxSizer(wx.HORIZONTAL)
    self.panel_sizer.Add(box)
    label = wx.StaticText(self,-1,"Marker size:")
    box.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    box.Add(self.marker_size_ctrl, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    self.Bind(floatspin.EVT_FLOATSPIN, self.OnChangeSettings, self.marker_size_ctrl)

    from wxtbx.segmentedctrl import SegmentedRadioControl, SEGBTN_HORIZONTAL
    self.btn = SegmentedRadioControl(self, style=SEGBTN_HORIZONTAL)
    self.btn.AddSegment("all")
    self.btn.AddSegment("indexed")
    self.btn.AddSegment("unindexed")
    self.btn.SetSelection(
      ["all", "indexed", "unindexed"].index(self.settings.display))

    self.Bind(wx.EVT_RADIOBUTTON, self.OnChangeSettings, self.btn)
    self.GetSizer().Add(self.btn, 0, wx.ALL, 5)

  def add_value_widgets (self, sizer) :
    sizer.Add(wx.StaticText(self.panel, -1, "Value:"), 0,
      wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    self.value_info = wx.TextCtrl(self.panel, -1, size=(80,-1),
      style=wx.TE_READONLY)
    sizer.Add(self.value_info, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

  def OnChangeSettings(self, event):
    self.settings.d_min = self.d_min_ctrl.GetValue()
    self.settings.beam_centre = (
      self.beam_fast_ctrl.GetValue(), self.beam_slow_ctrl.GetValue())
    self.settings.marker_size = self.marker_size_ctrl.GetValue()
    for i, display in enumerate(("all", "indexed", "unindexed")):
      if self.btn.values[i]:
        self.settings.display = display
        break
    self.parent.update_settings()


class MyGLWindow(wx_viewer.show_points_and_lines_mixin):

  def __init__(self, settings, *args, **kwds):
    super(MyGLWindow, self).__init__(*args, **kwds)
    self.settings = settings
    self.points = flex.vec3_double()
    self.rotation_axis = None
    self.beam_vector = None
    self.flag_show_minimum_covering_sphere = False
    self._compute_minimum_covering_sphere()
    self.field_of_view_y = 0.001

  def set_points(self, points):
    self.points = points
    self.points_display_list = None
    #self.draw_points()
    self._compute_minimum_covering_sphere()
    #if not self.GL_uninitialised:
      #self.fit_into_viewport()

  def set_rotation_axis(self, axis):
    self.rotation_axis = axis

  def set_beam_vector(self, beam):
    self.beam_vector = beam

  #--- user input and settings
  def update_settings (self) :
    self.points_display_list = None
    #self.DrawGL()
    self._compute_minimum_covering_sphere()
    #if not self.GL_uninitialised:
      #self.fit_into_viewport()
    self.Refresh()

  def _compute_minimum_covering_sphere(self):
    n_points = min(1000, self.points.size())
    isel = flex.random_permutation(self.points.size())[:n_points]
    self.minimum_covering_sphere = minimum_covering_sphere(
      self.points.select(isel))

  def draw_cross_at(self, (x,y,z), color=(1,1,1), f=None):
    if f is None:
      f = 0.01 * self.settings.marker_size
    wx_viewer.show_points_and_lines_mixin.draw_cross_at(
      self, (x,y,z), color=color, f=f)

  def DrawGL(self):
    wx_viewer.show_points_and_lines_mixin.DrawGL(self)
    if self.rotation_axis is not None and self.settings.show_rotation_axis:
      self.draw_axis(self.rotation_axis, "phi")
    if self.beam_vector is not None and self.settings.show_beam_vector:
      self.draw_axis(self.beam_vector, "beam")

  def draw_axis(self, axis, label):
    s = self.minimum_covering_sphere
    scale = max(max(s.box_max()), abs(min(s.box_min())))
    gltbx.fonts.ucs_bitmap_8x13.setup_call_lists()
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    #if (self.settings.black_background) :
      #glColor3f(1.0, 1.0, 1.0)
    #else :
      #glColor3f(0.,0.,0.)
    glLineWidth(1.0)
    glBegin(GL_LINES)
    glVertex3f(0.,0.,0.)
    glVertex3f(axis[0]*scale, axis[1]*scale, axis[2]*scale)
    glEnd()
    glRasterPos3f(0.5+axis[0]*scale, 0.2+axis[1]*scale, 0.2+axis[2]*scale)
    gltbx.fonts.ucs_bitmap_8x13.render_string(label)
    glEnable(GL_LINE_STIPPLE)
    glLineStipple(4, 0xAAAA)
    glBegin(GL_LINES)
    glVertex3f(0.,0.,0.)
    glVertex3f(-axis[0]*scale, -axis[1]*scale, -axis[2]*scale)
    glEnd()
    glDisable(GL_LINE_STIPPLE)

  def rotate_view(self, x1, y1, x2, y2, shift_down=False, scale=0.1):
    super(MyGLWindow, self).rotate_view(
      x1, y1, x2, y2, shift_down=shift_down, scale=scale)


def run(args):

  from dials.util.options import OptionParser
  from dials.util.options import flatten_datablocks
  from dials.util.options import flatten_experiments
  from dials.util.options import flatten_reflections

  parser = OptionParser(
    phil=master_phil,
    read_datablocks=True,
    read_experiments=True,
    read_reflections=True,
    check_format=False)

  params, options = parser.parse_args(show_diff_phil=True)
  datablocks = flatten_datablocks(params.input.datablock)
  experiments = flatten_experiments(params.input.experiments)
  reflections = flatten_reflections(params.input.reflections)[0]

  if len(datablocks) == 0:
    if len(experiments) > 0:
      imagesets = experiments.imagesets()
    else:
      parser.print_help()
      return
  else:
    imagesets = []
    for datablock in datablocks:
      imagesets.extend(datablock.extract_imagesets())

  import wxtbx.app
  a = wxtbx.app.CCTBXApp(0)
  a.settings = params
  f = ReciprocalLatticeViewer(
    None, -1, "Reflection data viewer", size=(1024,768))
  f.load_models(imagesets, reflections)
  f.Show()
  a.SetTopWindow(f)
  #a.Bind(wx.EVT_WINDOW_DESTROY, lambda evt: tb_icon.Destroy(), f)
  a.MainLoop()


if __name__ == '__main__':
  import sys
  run(sys.argv[1:])
