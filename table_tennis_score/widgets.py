# Copyright (c) 2022 Maciej Dems
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from kivy.app import App
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ColorProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivymd.theming import ThemableBehavior
from kivymd.uix.list import OneLineIconListItem, TwoLineIconListItem, TwoLineListItem, OneLineRightIconListItem
from kivymd.uix.menu import MDDropdownMenu

from .lang import txt


class IconMenuItem(OneLineIconListItem):
    icon = StringProperty()
    icon_color = ColorProperty()


class MenuBehavior:
    menu_item_class = StringProperty('OneLineListItem')
    menu_item_height = NumericProperty(dp(48))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._menu = None
        txt.fbind(None, self.on_lang, ())

    def get_menu(self):
        return []

    #yapf: disable
    def _make_callback(self, item):
        callback = item['callback']
        def action():
            self._menu.dismiss()
            callback()
        return action
    #yapf: enable

    def menu_open(self, caller=None):
        if caller is None:
            caller = self
        menu_items = [
            dict(viewclass=self.menu_item_class, height=self.menu_item_height, on_release=self._make_callback(item), **item)
            for item in self.get_menu()
        ]
        if self._menu is None:
            self._menu = MDDropdownMenu(caller=caller, items=menu_items, width_mult=4)
        self._menu.open()

    def menu_close(self):
        self._menu.dismiss()

    def on_lang(self, *args, **kwargs):
        self._menu = None


class SettingsBehavior:
    section = StringProperty()
    name = StringProperty()
    value = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_value()

    def on_parent(self, instance, parent):
        parent.bind(on_kv_post=self._init_value)

    def _init_value(self, *args, **kwargs):
        if self.section and self.name:
            self.value = App.get_running_app().config.get(self.section, self.name)

    def save_value(self, value):
        if self.value != value:
            self.value = value
            if self.section and self.name:
                config = App.get_running_app().config
                config.set(self.section, self.name, value)
                config.write()


class ComboBehavior(MenuBehavior, SettingsBehavior):
    items = ListProperty()
    textid = StringProperty()
    text_prop = StringProperty('text')

    def _get_text(self, value):
        if self.textid:
            return getattr(txt, self.textid)[value]
        else:
            return str(value)

    def on_value(self, instance, value):
        setattr(self, self.text_prop, self._get_text(value))

    def _get_item_callback(self, item):
        return lambda: self.save_value(item)

    def get_menu(self):
        return [{'text': self._get_text(item), 'callback': self._get_item_callback(item)} for item in self.items]

    def on_lang(self, *args, **kwargs):
        super().on_lang(*args, **kwargs)
        setattr(self, self.text_prop, self._get_text(self.value))


class ComboListItem(TwoLineListItem, ComboBehavior):

    def on_release(self):
        self.menu_open()


class IconComboListItem(TwoLineIconListItem, ComboBehavior):
    icon = StringProperty()
    icon_color = ColorProperty()

    def on_release(self):
        self.menu_open(caller=self.ids.left_icon)


class BooleanListItem(OneLineRightIconListItem, SettingsBehavior):
    value = BooleanProperty()

    def _init_value(self, *args, **kwargs):
        if self.section and self.name:
            value = App.get_running_app().config.get(self.section, self.name)
            self.value = value == 'True' if isinstance(value, str) else value
            self.ids.checkbox.state = 'down' if self.value else 'normal'
