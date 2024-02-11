import bpy
from .bar_chart import DV_GN_BarChart
from .data import DV_DataProperties
from .components import DV_AddNumericAxis, DV_AddHeading, DV_AddAxisLabel, DV_AddDataLabels, DV_AxisPanel, DV_DataLabelsPanel
from .modifier_utils import DV_RemoveModifier

CLASSES = [
    DV_DataProperties,
    DV_RemoveModifier,
    DV_GN_BarChart,
    DV_AddNumericAxis,
    DV_AddHeading,
    DV_AddAxisLabel,
    DV_AddDataLabels,
    DV_AxisPanel,
    DV_DataLabelsPanel
]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)