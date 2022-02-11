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
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ColorProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex, get_hex_from_color
# from kivymd.uix.pickers import MDColorPicker
from kivymd.color_definitions import colors as COLORS
from kivymd.uix.behaviors import TouchBehavior
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.screen import MDScreen

from .lang import txt
from .model import Player, dbsession
from .widgets import MenuBehavior

PLAYER_ICONS = [
    'face',
    'face-outline',
    'face-woman',
    'face-woman-outline',
    'face-profile',
    'face-profile-woman',
    'baby-face',
    'baby-face-outline',
    'face-mask',
    'face-mask-outline',
]

PLAYER_COLORS = [c['A700'] for c in COLORS.values() if isinstance(c, dict) and 'A700' in c and c['A700'] != '000000']


class PlayerItem(OneLineIconListItem):
    data = ObjectProperty()
    icon = StringProperty()
    icon_color = ColorProperty([0, 0, 0, 0])

    def on_data(self, instance, value):
        if value is not None:
            self.text = value.name
            self.icon = value.icon or 'face'
            try:
                self.icon_color = get_color_from_hex(value.color)
            except:
                pass


class PlayerItemInteractive(PlayerItem, TouchBehavior, MenuBehavior):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._menu = None
        self._dialog = None

    def get_menu(self):
        return [{'text': txt.menu_edit, 'callback': self._edit}, {'text': txt.menu_delete, 'callback': self._delete}]

    def on_long_touch(self, touch, *args):
        self.menu_open()

    def _delete(self, *args):
        self.menu_close()
        if self._dialog is None:
            self._dialog = MDDialog(
                text=txt.confirm_player_delete.format(self.data.name),
                buttons=[
                    MDFlatButton(text=txt.button_cancel, on_release=lambda *args: self._dialog.dismiss()),
                    MDFlatButton(
                        text=txt.button_delete,
                        text_color=App.get_running_app().theme_cls.primary_color,
                        on_release=self._do_delete
                    ),
                ],
            )
        self._dialog.open()

    def _do_delete(self, *args):
        self._dialog.dismiss()
        app = App.get_running_app()
        save_config = False
        for i in 1, 2:
            field = f'player{i}'
            if app.config.get('match', field) == str(self.data.id):
                app.config.set('match', field, None)
                save_config = True
        if save_config:
            app.config.write()
        self.data.delete()
        app.root.ids.players_screen.populate_player_list()

    def _edit(self):
        self._menu.dismiss()
        App.get_running_app().root.ids.players_screen.show_dialog(self.data)


class PlayerEditBox(BoxLayout):
    pass


class PlayersScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dialog = None
        Clock.schedule_once(lambda *args: self.populate_player_list())

    def populate_player_list(self):
        player_list = self.ids.player_list
        player_list.clear_widgets()
        for player in Player.get_all():
            player_list.add_widget(PlayerItemInteractive(data=player))

    def show_dialog(self, player=None):
        app = App.get_running_app()
        if self._dialog is None:
            self._dialog = MDDialog(
                type='custom',
                content_cls=PlayerEditBox(),
                buttons=[
                    MDFlatButton(text=txt.button_cancel, on_release=lambda *args: self._dialog.dismiss()),
                    MDFlatButton(text=txt.button_ok, text_color=app.theme_cls.primary_color, on_release=self._on_dialog_ok),
                ],
            )
            self._dialog.md_bg_color = app.theme_cls.bg_dark
            self._dialog_player_name = self._dialog.content_cls.ids.player_name
            self._dialog_player_color = self._dialog.content_cls.ids.player_color
            self._dialog_player_icon = self._dialog.content_cls.ids.player_icon
            self._dialog_player_color.bind(on_release=self._on_select_color)
            self._dialog_player_icon.bind(on_release=self._on_select_icon)
        if player is None:
            self._dialog.title = txt.new_player
            self._dialog_player_name.text = ''
            self._dialog_player_icon.icon = PLAYER_ICONS[0]
            self._dialog_player_color.md_bg_color = get_color_from_hex(PLAYER_COLORS[0])
        else:
            self._dialog.title = txt.edit_player
            self._dialog_player_name.text = player.name
            self._dialog_player_icon.icon = player.icon
            try:
                self._dialog_player_color.md_bg_color = get_color_from_hex(player.color)
            except:
                self._dialog_player_color.md_bg_color = get_color_from_hex(PLAYER_COLORS[0])
        self._dialog.player = player
        self._dialog.open()

    def _on_dialog_ok(self, *args):
        try:
            player_name = str(self._dialog_player_name.text)[:50]
            player_color = get_hex_from_color(self._dialog_player_color.md_bg_color)[:7]
            player_icon = str(self._dialog_player_icon.icon)[:25]
            if self._dialog.player is None:
                player = Player(name=player_name, icon=player_icon, color=player_color)
                dbsession.add(player)
            else:
                player = self._dialog.player
                player.name = player_name
                player.color = player_color
                player.icon = player_icon
            dbsession.commit()
            self.populate_player_list()
        finally:
            self._dialog.dismiss()

    def _on_select_icon(self, *args):
        try:
            idx = (PLAYER_ICONS.index(self._dialog_player_icon.icon) + 1) % len(PLAYER_ICONS)
        except ValueError:
            idx = 0
        self._dialog_player_icon.icon = PLAYER_ICONS[idx]

    def _on_select_color(self, *args):
        # color_picker = MDColorPicker(size_hint=(0.45, 0.85))
        # color_picker.bind(
        #     on_select_color=self.on_select_color,
        # )
        # color_picker.open()
        try:
            color = get_hex_from_color(self._dialog_player_color.md_bg_color)[1:7].upper()
            idx = (PLAYER_COLORS.index(color) + 1) % len(PLAYER_COLORS)
        except ValueError:
            idx = 0
        self._dialog_player_color.md_bg_color = get_color_from_hex(PLAYER_COLORS[idx])

    def new_player(self):
        self.show_dialog()
