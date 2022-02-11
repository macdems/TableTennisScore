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

import os

import kivy.utils
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.uix.screenmanager import NoTransition, WipeTransition
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineIconListItem

if kivy.utils.platform == 'android':
    import jnius
else:
    jnius = None
    window_width = Window.size[0]
    Window.size = window_width, 1.8 * window_width

from . import model
from .lang import DEFAULT as DEFAULT_LANG
from .lang import txt
from .match import Match

Config.set('kivy', 'exit_on_escape', '0')


class TableTennisScoreApp(MDApp):

    def __init__(self, **kwargs):
        self.icon = os.path.join('assets', 'icon.png')
        super().__init__(**kwargs)
        model.init_db(self)
        self.theme_cls.primary_palette = 'Indigo'
        self.theme_cls.accent_palette = 'Pink'
        self.match = None
        self._confirm_stop_dialog = None
        self._exitting = False

    def build(self):
        super().build()
        Window.bind(on_keyboard=self.on_key_press_back)
        self.root.ids.newmatch_screen.ids.newmatch_tab.setup_players()

    def _get_lang(self):
        if jnius is not None:
            try:
                Locale = jnius.autoclass('java.util.Locale')
                return Locale.getDefault().toString().split('_')[0]
            except:
                return DEFAULT_LANG
        else:
            return os.environ.get('LANG', DEFAULT_LANG).split('.')[0].split('_')[0]

    def load_kv(self, filename=None):
        self.set_lang(self.config.get('settings', 'lang'))
        if filename is None:
            kv_directory = self.kv_directory or os.path.dirname(__file__)
            filename = os.path.join(kv_directory, '__init__.kv')
        super().load_kv(filename)

    def build_config(self, config):
        config.setdefaults('settings', {'lang': 'auto', 'style': 'auto', 'rotation': 'auto', 'tts': True, 'advantages': True})
        config.setdefaults('match', {'player1': None, 'player2': None, 'serving': 1, 'sets': 3, 'points': 11})

    def set_lang(self, value):
        if value == 'auto': value = self._get_lang()
        txt.set_lang(value)

    def set_style(self, value):
        if value == 'auto': value = 'Light'  #TODO
        self.theme_cls.theme_style = value

    def _cancel_exiting(self, *args):
        self._exitting = False

    def on_key_press_back(self, window, key, *args):
        if key == 27:
            if self.root.ids.screen_manager.current == 'match':
                self.stop_match()
            else:
                if self._exitting:
                    self.stop()
                else:
                    toast(txt.confirm_exit)
                    self._exitting = Clock.schedule_once(self._cancel_exiting, 4)

    def switch_screen(self, name):
        self.root.ids.screen_manager.current = name
        self.root.ids.nav_drawer.set_state("close")

    def start_match(self, player1, player2, serving, **kwargs):
        if not isinstance(player1, model.Player):
            player1 = model.dbsession.query(model.Player).get(player1)
        if not isinstance(player2, model.Player):
            player2 = model.dbsession.query(model.Player).get(player2)

        self._matchdb = model.Match(player1=player1, player2=player2)
        self._matchdb.details = kwargs
        model.dbsession.add(self._matchdb)
        model.dbsession.commit()

        adv = self.config.get('settings', 'advantages')
        adv = adv == 'True' if isinstance(adv, str) else adv
        tts = self.config.get('settings', 'tts')
        tts = tts == 'True' if isinstance(tts, str) else tts
        self.match = Match(self, self.root.ids.match_screen, player1, player2, show_advantages=adv, tts=tts, **kwargs)

        self.root.ids.screen_manager.transition = WipeTransition()
        self.root.ids.screen_manager.current = 'match'
        self.match.start(serving)

    def game_over(self, winner, score, stats):
        self._matchdb.end_match(score, stats)
        self.root.ids.gameover_screen.winner = winner.name
        self.root.ids.screen_manager.current = 'gameover'
        self.match = None

    def stop_match(self):
        if self._confirm_stop_dialog is None:
            self._confirm_stop_dialog = MDDialog(
                text=txt.confirm_stop_match,
                buttons=[
                    MDFlatButton(text=txt.button_no, on_release=lambda *args: self._confirm_stop_dialog.dismiss()),
                    MDFlatButton(text=txt.button_yes, text_color=self.theme_cls.primary_color, on_release=self._on_stop_match),
                ],
            )
        self._confirm_stop_dialog.open()

    def _on_stop_match(self, *args):
        self._confirm_stop_dialog.dismiss()
        self._matchdb.end_match(*self.match.current_stats, finished=False)
        self.match = None
        self.root.ids.screen_manager.transition = NoTransition()
        self.root.ids.screen_manager.current = 'newmatch'
