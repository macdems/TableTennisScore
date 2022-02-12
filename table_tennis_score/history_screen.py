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
from kivy.properties import ObjectProperty
from kivy.utils import get_hex_from_color
from kivymd.uix.behaviors import TouchBehavior
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import ThreeLineListItem
from kivymd.uix.screen import MDScreen

from .lang import txt
from .model import Match, dbsession
from .widgets import MenuBehavior


class GameListItem(ThreeLineListItem, TouchBehavior, MenuBehavior):
    data = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dialog = None

    def on_data(self, instance, value):
        gray = None
        player1, player2 = value.player1.name, value.player2.name
        if value.player1.deleted:
            gray = get_hex_from_color(App.get_running_app().theme_cls.secondary_text_color) if gray is None else gray
            player1 = f"[color={gray}]{player1}[/color]"
        if value.player2.deleted:
            gray = get_hex_from_color(App.get_running_app().theme_cls.secondary_text_color) if gray is None else gray
            player2 = f"[color={gray}]{player2}[/color]"
        score1, score2 = value.score1, value.score2
        sets = []
        finished = value.finished
        total = 65535
        second_line = ""
        if finished:
            if score1 > score2:
                player1 = f"[b]{player1}[/b]"
                score1 = f"[b]{score1}[/b]"
            elif score2 > score1:
                player2 = f"[b]{player2}[/b]"
                score2 = f"[b]{score2}[/b]"
            self.text = f"{player1} : {player2}  ({score1}:{score2})"
        else:
            gray = get_hex_from_color(App.get_running_app().theme_cls.secondary_text_color) if gray is None else gray
            text = f"{player1} : {player2}"
            if score1 is not None:  #  and score2 is not None
                text += f"  [color={gray}]({score1}:{score2})[/color]"
                total = score1 + score2
            self.text = text
            second_line = " — " + txt.match_unfinished
        start = value.start
        if value.end:
            duration = value.end - start
            second_line = f" — {duration.seconds // 60}min {duration.seconds % 60}s" + second_line
        self.secondary_text = start.strftime("%Y-%m-%d %H:%M") + second_line
        for i, set in enumerate(value.sets):
            p1, p2 = set.points1, set.points2
            if finished or i < total:
                if p1 > p2:
                    p1 = f"[b]{p1}[/b]"
                elif p2 > p1:
                    p2 = f"[b]{p2}[/b]"
            sets.append(f"({p1}:{p2})")
        if sets:
            self.tertiary_text = " ".join(sets)
        else:
            self.tertiary_text = " "

    def get_menu(self):
        return [{'text': txt.menu_delete, 'callback': self._delete}]

    def on_long_touch(self, touch, *args):
        self.menu_open()

    def _delete(self, *args):
        if self._dialog is None:
            self._dialog = MDDialog(
                text=txt.confirm_match_delete.format(self.data.player1.name, self.data.player2.name),
                buttons=[
                    MDFlatButton(text=txt.button_cancel, on_releacase=lambda *args: self._dialog.dismiss()),
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
        self.data.delete()
        self.parent.remove_widget(self)
        App.get_running_app().root.ids.history_screen.offset -= 1


class HistoryScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.offset = 0

    def on_pre_enter(self):
        history = self.ids.history
        count = 0
        for data in reversed(dbsession.query(Match).order_by(Match.start).offset(self.offset).all()):
            item = GameListItem(data=data)
            history.add_widget(item, self.offset)
            count += 1
        self.offset += count
