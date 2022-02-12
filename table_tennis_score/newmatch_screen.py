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
from kivy.properties import ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularRippleBehavior, SpecificBackgroundColorBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import TwoLineIconListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.tab import MDTabsBase

from .lang import txt
from .model import Player, dbsession
from .widgets import MenuBehavior


class StartMatchButton(MDLabel, RectangularRippleBehavior, ButtonBehavior, ThemableBehavior, SpecificBackgroundColorBehavior):
    pass


class PlayerCombo(TwoLineIconListItem, MenuBehavior):
    data = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.data is None:
            self.theme_text_color = 'Custom'

    def _player_selected_callback(self, player):
        return lambda: self.on_player_selected(player)

    def get_menu(self):
        return [{
            'text': player.name,
            'icon': player.icon,
            'icon_color': player.color,
            'callback': self._player_selected_callback(player=player)
        } for player in Player.get_all()]

    def on_release(self, *args):
        self.menu_open(caller=self.ids.left_icon)

    def setup(self, currentid):
        self._menu = None
        if currentid is not None:
            self._select_player(dbsession.query(Player).get(currentid))
        else:
            self._select_player(None)

    def on_player_selected(self, player):
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

    def setup_players(self, *args, **kwargs):
        config = App.get_running_app().config
        self.ids.player_one.setup(config.get('match', 'player1'))
        self.ids.player_two.setup(config.get('match', 'player2'))


class NewMatchScreen(MDScreen, ThemableBehavior):

    def start_match(self):
        newmatch_tab = self.ids.newmatch_tab
        player1 = newmatch_tab.ids.player_one.data
        player2 = newmatch_tab.ids.player_two.data
        serving = int(newmatch_tab.ids.serving.value)
        newmatchdetails_tab = self.ids.newmatchdetails_tab
        sets = int(newmatchdetails_tab.ids.sets.value)
        points = int(newmatchdetails_tab.ids.points.value)
        App.get_running_app().start_match(player1, player2, serving, sets=sets, set_points=points)
