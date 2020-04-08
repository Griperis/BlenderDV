import bpy
import math

from mathutils import Vector
from data_vis.data_manager import DataManager, DataType
from data_vis.utils.data_utils import find_axis_range
from data_vis.colors import ColorType


class DV_AxisPropertyGroup(bpy.types.PropertyGroup):
    def range_updated(self, context):
        if self.x_range[0] == self.x_range[1]:
            self.x_range[1] += 1.0
        if self.y_range[0] == self.y_range[1]:
            self.y_range[1] += 1.0
        if self.z_range[0] == self.z_range[1]:
            self.z_range += 1.0

    create: bpy.props.BoolProperty(
        name='Create Axis Object',
        default=True,
    )

    auto_steps: bpy.props.BoolProperty(
        name='Automatic Steps',
        default=True,
        description='Automatically calculates stepsize to display 10 marks'
    )

    x_step: bpy.props.FloatProperty(
        name='Step of x axis',
        default=1.0,
    )

    x_range: bpy.props.FloatVectorProperty(
        name='Range of x axis',
        size=2,
        update=range_updated,
        default=DataManager().get_range('x')
    )

    y_step: bpy.props.FloatProperty(
        name='Step of y axis',
        default=1.0,
    )

    y_range: bpy.props.FloatVectorProperty(
        name='Range of y axis',
        size=2,
        update=range_updated,
        default=DataManager().get_range('y')
    )

    z_range: bpy.props.FloatVectorProperty(
        name='Range of y axis',
        size=2,
        update=range_updated,
        default=DataManager().get_range('z'),
    )

    z_step: bpy.props.FloatProperty(
        name='Step of z axis',
        default=1.0,
    )

    thickness: bpy.props.FloatProperty(
        name='Thickness',
        min=0.001,
        max=0.02,
        default=0.005,
        description='How thick is the axis object'
    )

    tick_mark_height: bpy.props.FloatProperty(
        name='Tick Mark Height',
        default=0.015,
        min=0.001,
        max=0.02,
        description='Thickness of axis mark objects'
    )

    padding: bpy.props.FloatProperty(
        name='Padding',
        default=0.1,
        min=0,
        description='Axis distance from chart origin'
    )

    text_size: bpy.props.FloatProperty(
        name='Text size',
        default=0.05
    )

    number_format: bpy.props.EnumProperty(
        name='Num format',
        items=(
            ('0', 'Decimal', '123.456'),
            ('1', 'Scientific', '1.23e+05')
        )
    )

    decimal_places: bpy.props.IntProperty(
        name='Decimal places',
        default=2,
        min=0
    )


class DV_LabelPropertyGroup(bpy.types.PropertyGroup):
    create: bpy.props.BoolProperty(
        name='Create labels',
        default=True
    )

    from_data: bpy.props.BoolProperty(
        name='From data',
        default=True
    )

    x_label: bpy.props.StringProperty(
        name='X',
        default='X Label'
    )

    y_label: bpy.props.StringProperty(
        name='Y',
        default='Y Label'
    )

    z_label: bpy.props.StringProperty(
        name='Z',
        default='Z Label'
    )


class DV_ColorPropertyGroup(bpy.types.PropertyGroup):
    use_shader: bpy.props.BoolProperty(
        name='Use Nodes',
        default=True,
        description='Uses Node Shading to color created objects. Not using this option may create material for every chart object when not using constant color type'
    )

    color_type: bpy.props.EnumProperty(
        name='Color Type',
        items=(
            ('0', 'Gradient', 'Gradient based on value'),
            ('1', 'Constant', 'One color'),
            ('2', 'Random', 'Random colors'),
        ),
        default='0',
        description='Type of coloring for chart'
    )

    color_shade: bpy.props.FloatVectorProperty(
        name='Base Color',
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        description='Base color shade to work with'
    )


class OBJECT_OT_GenericChart(bpy.types.Operator):
    '''Creates chart'''
    bl_idname = 'object.create_chart'
    bl_label = 'Generic chart operator'
    bl_options = {'REGISTER', 'UNDO'}

    data = None
    axis_mat = None

    def __init__(self):
        self.container_object = None
        self.labels = []
        self.dm = DataManager()
        if hasattr(self, 'dimensions'):
            self.dimensions = str(self.dm.dimensions)

        if hasattr(self, 'data_type'):
            self.data_type = '0' if self.dm.predicted_data_type == DataType.Numerical else '1'

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(icon='WORLD_DATA', text='Chart settings:')
        if hasattr(self, 'data_type'):
            row = box.row()
            row.prop(self, 'data_type')

        only_2d = hasattr(self, 'dimensions')
        numerical = True
        if hasattr(self, 'data_type'):
            if self.data_type == '1':
                numerical = False

        only_2d = only_2d or not numerical

        if hasattr(self, 'dimensions') and self.dm.predicted_data_type != DataType.Categorical:
            if numerical:
                row = box.row()
                row.prop(self, 'dimensions')
            else:
                self.dimensions = '2'

        self.draw_axis_settings(layout, numerical)
        self.draw_color_settings(layout)

    def draw_label_settings(self, box):
        if hasattr(self, 'label_settings'):
            row = box.row()
            row.label(icon='FILE_FONT', text='Label Settings:')
            row.prop(self.label_settings, 'create')
            if self.label_settings.create:
                box.prop(self.label_settings, 'from_data')
                if not self.label_settings.from_data:
                    row = box.row()
                    row.prop(self.label_settings, 'x_label')
                    if self.dm.dimensions == 3:
                        row.prop(self.label_settings, 'y_label')
                    row.prop(self.label_settings, 'z_label')

    def draw_color_settings(self, layout):
        if hasattr(self, 'color_settings'):
            box = layout.box()
            box.label(icon='COLOR', text='Color settings')
            box.prop(self.color_settings, 'use_shader')
            box.prop(self.color_settings, 'color_type')
            if not ColorType.str_to_type(self.color_settings.color_type) == ColorType.Random:
                box.prop(self.color_settings, 'color_shade')
 
    def draw_axis_settings(self, layout, numerical):
        if not hasattr(self, 'axis_settings'):
            return

        box = layout.box()
        box.label(icon='ORIENTATION_VIEW', text='Axis Settings:')

        row = box.row()
        row.label(text='Range settings:')
        row = box.row()
        row.prop(self.axis_settings, 'x_range', text='X')
        if hasattr(self, 'dimensions') and self.dimensions == '3':
            row = box.row()
            row.prop(self.axis_settings, 'y_range', text='Y')
        row = box.row()
        row.prop(self.axis_settings, 'z_range', text='Z')
        box.prop(self.axis_settings, 'auto_steps')

        if not self.axis_settings.auto_steps:
            row = box.row()
            if numerical:
                row.prop(self.axis_settings, 'x_step', text='X')
            if hasattr(self, 'dimensions') and self.dimensions == '3':
                row.prop(self.axis_settings, 'y_step', text='Y')
            row.prop(self.axis_settings, 'z_step', text='Z')

        row = box.row()
        row.prop(self.axis_settings, 'create')
        if not self.axis_settings.create:
            return
        row = box.row()
        row.prop(self.axis_settings, 'padding')
        row.prop(self.axis_settings, 'thickness')
        row.prop(self.axis_settings, 'tick_mark_height')
        box.separator()
        row = box.row()
        row.label(text='Text settings', icon='FONT_DATA')
        box.prop(self.axis_settings, 'number_format')
        row = box.row()
        row.prop(self.axis_settings, 'text_size')
        row.prop(self.axis_settings, 'decimal_places')
        box.separator()
        self.draw_label_settings(box)

    @classmethod
    def poll(cls, context):
        '''Default behavior for every chart poll method (when data is not available, cannot create chart)'''
        return self.dm.parsed_data is not None

    def execute(self, context):
        raise NotImplementedError('Execute method should be implemented in every chart operator!')

    def init_ranges(self):
        self.axis_settings.x_range = self.dm.get_range('x')
        self.axis_settings.y_range = self.dm.get_range('y')
        self.axis_settings.z_range = self.dm.get_range('z')

    def invoke(self, context, event):
        if hasattr(self, 'axis_settings'):
            self.init_ranges()

        return context.window_manager.invoke_props_dialog(self)

    def create_container(self):
        bpy.ops.object.empty_add()
        self.container_object = bpy.context.object
        self.container_object.empty_display_type = 'PLAIN_AXES'
        self.container_object.name = 'Chart_Container'
        self.container_object.location = bpy.context.scene.cursor.location

    def data_type_as_enum(self):
        if not hasattr(self, 'data_type'):
            return DataType.Numerical

        if self.data_type == '0':
            return DataType.Numerical
        elif self.data_type == '1':
            return DataType.Categorical

    def new_mat(self, color, alpha, name='Mat'):
        mat = bpy.data.materials.new(name=name)
        mat.diffuse_color = (*color, alpha)
        return mat

    def init_data(self):
        if hasattr(self, 'label_settings'):
            self.init_labels()
        data = self.dm.get_parsed_data()

        self.data = data
        return True

    def init_labels(self):
        if not self.label_settings.create:
            self.labels = (None, None, None)
            return
        if self.dm.has_labels and self.label_settings.from_data:
            first_line = self.dm.get_labels()
            length = len(first_line)
            if length == 2:
                self.labels = (first_line[0], '', first_line[1])
            elif length == 3:
                self.labels = (first_line[0], first_line[1], first_line[2])
            else:
                self.report({'ERROR'}, 'Unsupported number of labels on first line')
        else:
            self.labels = [self.label_settings.x_label, self.label_settings.y_label, self.label_settings.z_label]

    def init_range(self, data):
        self.axis_settings.x_range = find_axis_range(data, 0)
        self.axis_settings.y_range = find_axis_range(data, 1)

    def in_axis_range_bounds(self, entry):
        '''
        Checks whether the entry point defined as [x, y, z] is within user selected axis range
        returns False if not in range, else True
        '''
        entry_dims = len(entry)
        if entry_dims == 2 or entry_dims == 3:
            if hasattr(self, 'data_type') and self.data_type != '0':
                return True

            if entry[0] < self.x_axis_range[0] or entry[0] > self.x_axis_range[1]:
                return False

        if entry_dims == 3:
            if entry[1] < self.y_axis_range[0] or entry[1] > self.y_axis_range[1]:
                return False

        return True

    def in_axis_range_bounds_new(self, entry):
        '''
        Checks whether the entry point defined as [x, y, z] is within user selected axis range
        returns False if not in range, else True
        '''
        entry_dims = len(entry)
        if entry_dims == 2 or entry_dims == 3:
            if hasattr(self, 'data_type') and self.data_type != '0':
                return True

            if entry[0] < self.axis_settings.x_range[0] or entry[0] > self.axis_settings.x_range[1]:
                return False

        if entry_dims == 3:
            if entry[1] < self.axis_settings.y_range[0] or entry[1] > self.axis_settings.y_range[1]:
                return False

        return True

    def select_container(self):
        '''Makes container object active and selects it'''
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = self.container_object
        self.container_object.select_set(True)
