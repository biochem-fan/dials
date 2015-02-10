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
  show_rotation_axis = False
    .type = bool
  show_beam_vector = False
    .type = bool
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

  def load_models(self, imageset, reflections):
    self.detector = imageset.get_detector()
    self.beam = imageset.get_beam()
    self.scan = imageset.get_scan()
    self.goniometer = imageset.get_goniometer()
    self.reflections = reflections
    self.parameterise_models()
    self.viewer.set_rotation_axis(self.goniometer.get_rotation_axis())
    self.viewer.set_beam_vector(self.beam.get_s0())
    self.map_points_to_reciprocal_space()

  def parameterise_models(self):
    from dials.algorithms.refinement.parameterisation import \
      DetectorParameterisationSinglePanel, DetectorParameterisationHierarchical, \
      DetectorParameterisationMultiPanel
    if len(self.detector) > 1:
      try:
        h = self.detector.hierarchy()
        self.dp = DetectorParameterisationHierarchical(self.detector,
            experiment_ids=[0], level=0)
      except AttributeError:
        self.dp = DetectorParameterisationMultiPanel(self.detector, self.beam,
                                                    experiment_ids=[0])
    else:
      self.dp = DetectorParameterisationSinglePanel(self.detector,
                                                    experiment_ids=[0])

    from dials.algorithms.refinement.parameterisation import BeamParameterisation
    self.bp = BeamParameterisation(self.beam, self.goniometer, experiment_ids=[0])

    # keep parameter names
    self.detector_parameter_names = self.dp.get_param_names()
    self.beam_parameter_names = self.bp.get_param_names()

    # keep parameter values (modify these and update_models to make changes)
    self.detector_parameters = self.dp.get_param_vals()
    self.beam_parameters = self.bp.get_param_vals()

  def map_points_to_reciprocal_space(self):
    goniometer = copy.deepcopy(self.goniometer)
    if self.settings.reverse_phi:
      goniometer.set_rotation_axis([-i for i in goniometer.get_rotation_axis()])
    from dials.algorithms.indexing import indexer

    # set parameters to latest values
    self.dp.set_param_vals(self.detector_parameters)
    self.bp.set_param_vals(self.beam_parameters)

    reflections = indexer.indexer_base.map_spots_pixel_to_mm_rad(
      self.reflections, self.detector, self.scan)
    indexer.indexer_base.map_centroids_to_reciprocal_space(
      reflections, self.detector, self.beam, goniometer)
    points = reflections['rlp'] * 100
    self.viewer.set_points(points)

  def update_settings(self, *args, **kwds):
    self.map_points_to_reciprocal_space()
    self.viewer.update_settings(*args, **kwds)
    #self.draw_rotation_axis()


class settings_window (wxtbx.utils.SettingsPanel) :
  def __init__ (self, *args, **kwds) :
    wxtbx.utils.SettingsPanel.__init__(self, *args, **kwds)
    self.Bind(wx.EVT_CHAR, self.OnChar)

  def OnChar (self, event) :
    self.GetParent().viewer.OnChar(event)

  def add_controls (self) :
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

  def add_value_widgets (self, sizer) :
    sizer.Add(wx.StaticText(self.panel, -1, "Value:"), 0,
      wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
    self.value_info = wx.TextCtrl(self.panel, -1, size=(80,-1),
      style=wx.TE_READONLY)
    sizer.Add(self.value_info, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

  def OnChangeColor (self, event) :
    self.settings.color_scheme = str(self.color_ctrl.GetStringSelection())
    self.parent.update_settings()

  def OnSetScale (self, event) :
    self.settings.scale = (self.scale_ctrl.GetValue() + 4) / 4
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
    if not self.GL_uninitialised:
      self.fit_into_viewport()

  def set_rotation_axis(self, axis):
    self.rotation_axis = axis

  def set_beam_vector(self, beam):
    self.beam_vector = beam

  #--- user input and settings
  def update_settings (self) :
    self.points_display_list = None
    #self.DrawGL()
    self._compute_minimum_covering_sphere()
    if not self.GL_uninitialised:
      self.fit_into_viewport()
    self.Refresh()

  def _compute_minimum_covering_sphere(self):
    n_points = min(1000, self.points.size())
    isel = flex.random_permutation(self.points.size())[:n_points]
    self.minimum_covering_sphere = minimum_covering_sphere(
      self.points.select(isel))

  def draw_cross_at(self, (x,y,z), color=(1,1,1), f=None):
    if f is None:
      f = 0.01
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

  def rotate_view(self, x1, y1, x2, y2, shift_down=False, scale=0.25):
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
  elif len(datablocks) > 1:
    raise Sorry("Only one DataBlock can be processed at a time")
  else:
    imagesets = datablocks[0].extract_imagesets()

  if len(imagesets) > 1:
    raise Sorry("Only one ImageSet can be processed at a time")
  imageset = imagesets[0]

  import wxtbx.app
  a = wxtbx.app.CCTBXApp(0)
  a.settings = params
  f = ReciprocalLatticeViewer(
    None, -1, "Reflection data viewer", size=(1024,768))
  f.load_models(imageset, reflections)
  f.Show()
  a.SetTopWindow(f)
  #a.Bind(wx.EVT_WINDOW_DESTROY, lambda evt: tb_icon.Destroy(), f)
  a.MainLoop()


if __name__ == '__main__':
  import sys
  run(sys.argv[1:])