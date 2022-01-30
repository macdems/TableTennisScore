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

from random import choices
from kivy.app import App
from kivy.metrics import dp
from kivy.properties import ColorProperty, ListProperty, ObjectProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularRippleBehavior, SpecificBackgroundColorBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import TwoLineIconListItem, TwoLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.tab import MDTabsBase

from .lang import txt
from .model import dbsession, Player

SERVING_TEXT = [txt.play_for_serve, txt.first_player, txt.second_player]


class StartMatchButton(MDLabel, RectangularRippleBehavior, ButtonBehavior, ThemableBehavior, SpecificBackgroundColorBehavior):
    pass


class ComboButton(TwoLineListItem):
    name = StringProperty()
    items = ListProperty()
    value = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._menu = None

    def _item_callback(self, item):
        self._menu.dismiss()
        self.text = str(item)
        self.value = item
        if self.name:
            config = App.get_running_app().config
            config.set('match', self.name, item)
            config.write()

    def _get_item_callback(self, item):
        return lambda: self._item_callback(item)

    def open_menu(self):
        if self._menu is None:
            menu_items = [{
                'text': str(item),
                'viewclass': 'OneLineListItem',
                "height": dp(48),
                'on_release': self._get_item_callback(item)
            } for item in self.items]
            self._menu = MDDropdownMenu(caller=self, items=menu_items, width_mult=4)
        self._menu.open()


class IconInputButton(TwoLineIconListItem):
    icon = StringProperty()
    icon_color = ColorProperty()


class PlayerButton(IconInputButton):
    data = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._menu = None
        if self.data is None:
            self.theme_text_color = 'Custom'

    def _player_selected_callback(self, player):
        return lambda: self.on_player_selected(player)

    def make_menu(self, currentid):
        menu_items = [{
            'text': player.name,
            'icon': player.icon,
            'viewclass': 'IconMenuItem',
            'data': player,
            "height": dp(48),
            'on_release': self._player_selected_callback(player=player)
        } for player in Player.get_all()]
        self._menu = MDDropdownMenu(caller=self.ids.left_icon, items=menu_items, width_mult=4)
        if currentid is not None:
            self._select_player(dbsession.query(Player).get(currentid))
        else:
            self._select_player(None)

    def on_player_selected(self, player):
        self._menu.dismiss()
        self._select_player(player)
        config = App.get_running_app().config
        config.set('match', self.name, player.id)
        config.write()

    def _select_player(self, player):
        app = App.get_running_app()
        self.data = player
        if player is not None:
            self.text = player.name
            self.icon = player.icon
            self.icon_color = player.color
            player1 = self.parent.ids.player_one.data
            player2 = self.parent.ids.player_two.data
            if player1 is not None and player2 is not None and player1 != player2:
                app.root.ids.newmatch_screen.ids.start_button.disabled = False
            else:
                app.root.ids.newmatch_screen.ids.start_button.disabled = True
        else:
            self.icon = 'face'
            self.icon_color = app.theme_cls.disabled_hint_text_color
            self.text = txt.select_

    def on_data(self, instance, value):
        self.theme_text_color = 'Primary' if value is not None else 'Custom'


class NewMatchTab(MDBoxLayout, MDTabsBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serving_player = 1
        self._serving_menu = None

    def make_player_menus(self, config):
        self.ids.player_one.make_menu(config.get('match', 'player1'))
        self.ids.player_two.make_menu(config.get('match', 'player2'))

    def select_serving(self):
        if self._serving_menu is None:
            menu_items = [
                {
                    'text': txt.first_player,
                    'viewclass': 'OneLineListItem',
                    "height": dp(48),
                    'on_release': lambda: self.on_serving_selected(1)
                },
                {
                    'text': txt.second_player,
                    'viewclass': 'OneLineListItem',
                    "height": dp(48),
                    'on_release': lambda: self.on_serving_selected(2)
                },
                {
                    'text': txt.play_for_serve,
                    'viewclass': 'OneLineListItem',
                    "height": dp(48),
                    'on_release': lambda: self.on_serving_selected(0)
                },
            ]
            self._serving_menu = MDDropdownMenu(caller=self.ids.serving.ids.left_icon, items=menu_items, width_mult=4)
        self._serving_menu.open()

    def on_serving_selected(self, option):
        self._serving_menu.dismiss()
        self.serving_player = option
        self.ids.serving.text = SERVING_TEXT[option]
        config = App.get_running_app().config
        config.set('match', 'serving', option)
        config.write()


class NewMatchDetailsTab(MDBoxLayout, MDTabsBase):
    sets = NumericProperty(3)
    points = NumericProperty(11)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sets = 3
        self.points = 11
        self._sets_menu = None
        self._points_menu = None


class NewMatchScreen(MDScreen, ThemableBehavior):

    def setup(self, config):
        basic_tab = self.ids.newmatch_tab
        basic_tab.make_player_menus(config)
        serving = int(config.get('match', 'serving'))
        basic_tab.serving_player = serving
        basic_tab.ids.serving.text = SERVING_TEXT[serving]

        details_tab = self.ids.newmatchdetails_tab
        details_tab.sets = int(config.get('match', 'sets'))
        details_tab.points = int(config.get('match', 'points'))

    def start_match(self):
        player1 = self.ids.newmatch_tab.ids.player_one.data
        player2 = self.ids.newmatch_tab.ids.player_two.data
        sets = self.ids.newmatchdetails_tab.sets
        points = self.ids.newmatchdetails_tab.points
        App.get_running_app().start_match(player1, player2, self.ids.newmatch_tab.serving_player, sets=sets, set_points=points)
