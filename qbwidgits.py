import kivy
from kivy.uix.recycleview import RecycleView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    pass
class SelectableLabel(RecycleDataViewBehavior, Label):
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    def __init__(self, **kwargs):
        super().__init__()

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(rv, index, data)
    
    def on_touch_down(self, touch):
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)
    
    def apply_selection(self, rv, index, is_selected):
        self.selected = is_selected

class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)

class SelectableText(TextInput):
    def __init__(self, **kwargs):
        super().__init__()
        self.background_normal = 'white.png'
        self.background_active = 'white.png'
        self.valign = "top"
        self.multiline = True

class BackButton(Button):
    def __init__(self, **kwargs):
        super().__init__()
        self.background_normal="Back Arrow.png"
        self.background_down="Back Arrow.png"
        self.pos_hint={"x":0.0,"y":0.0}
        self.size_hint= (0.1,0.1)

class SettingsButton(Button):
    def __init__(self, **kwargs):
        super().__init__()
        self.size_hint= (0.1, 0.13)
        self.pos_hint= {"x":0.9,"y":0.0}
        self.background_normal="Settings Icon.png"
        self.background_down="Settings Icon.png"