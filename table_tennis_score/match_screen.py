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
from kivy.properties import BooleanProperty, ColorProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.utils import get_color_from_hex
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import BackgroundColorBehavior, RectangularRippleBehavior
from kivymd.uix.screen import MDScreen

from .lang import txt
from .system import set_orientation

class ScoreButton(RectangularRippleBehavior, ButtonBehavior, BackgroundColorBehavior):
    player_name = StringProperty()
    points = StringProperty('0')
    font_name = StringProperty(None)
    position = StringProperty(None)
    serving = BooleanProperty(False)
    sets = NumericProperty(0)
    foreground = ColorProperty([1.0, 1.0, 1.0, 1])

    def __init__(self, **kwargs):
        super(). __init__(**kwargs)
        self.bind(md_bg_color=self.on_bg_color)

    def on_bg_color(self, instance, value):
        lum = 0.30 * value[0] + 0.59 * value[1] + 0.11 * value[2]
        self.foreground = [1.0, 1.0, 1.0, 1] if lum < 0.7 else [0.0, 0.0, 0.0, 1]

    def on_sets(self, instance, value):
        if value > 9: value = '9-plus'
        self.ids.sets.icon = f'numeric-{value}-circle-outline'


class MatchScreen(MDScreen, ThemableBehavior):

    def _adjust_players_position(self):
        players = self.ids.players
        if self.ids.box.orientation == 'vertical':
            players.children[0].position = 'bottom'
            players.children[1].position = 'top'
        else:
            players.children[0].position = 'right'
            players.children[1].position = 'left'

    def on_enter(self, *args):
        set_orientation(App.get_running_app().config.get('settings', 'rotation'))
        super().on_enter(*args)

    def on_pre_leave(self, *args):
        super().on_pre_leave(*args)
        set_orientation('portrait')

    def on_size(self, instance, size):
        box = self.ids.box
        if size[1] > size[0]:
            box.orientation = 'vertical'
        else:
            box.orientation = 'horizontal'

    def set_players(self, *args):
        for widget, player in zip((self.ids.player_one, self.ids.player_two), args):
            try:
                widget.md_bg_color = get_color_from_hex(player.color)
            except:
                widget.md_bg_color = [0.0706, 0.0706, 0.0706, 1]
            widget.player_name = player.name

    def set_score(self, points=None, sets=None):
        players = self.ids.player_one, self.ids.player_two
        if points is not None:
            for i in 0, 1:
                players[i].points = str(points[i]).replace('+', '·')
        if sets is not None:
            for i in 0, 1:
                players[i].sets = sets[i]

    def set_serving(self, player):
        players = self.ids.player_one, self.ids.player_two
        if player is not None:
            players[player - 1].serving = True
            players[2 - player].serving = False
        else:
            players[0].serving = False
            players[1].serving = False

    @property
    def can_undo(self):
        return not self.ids.undo.disabled

    @can_undo.setter
    def can_undo(self, val):
        self.ids.undo.disabled = not val


class GameOverScreen(MDScreen, ThemableBehavior):
    winner = StringProperty()

    def on_winner(self, instance, value):
        self.ids.message.text = txt.wins_match.format(value)
