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


class SetOver(Exception):

    def __init__(self, winner):
        self.winner = winner


class Match:

    def __init__(self, app, screen, player1, player2, sets=3, set_points=11):
        self._app = app
        self._screen = screen
        self.players = player1, player2
        self._match_sets = sets
        self._last_point = set_points - 1
        screen.set_players(player1, player2)

    def start(self, serving):
        self._sets = []
        self._points = []
        self._sets_history = []
        self._screen.set_score((0, 0), (0, 0))
        self._say('begin_match')
        self._screen.can_undo = False
        if serving:
            self._serving = serving - 1
            self._screen.set_serving(self._serving + 1)
            self._say('serving', self.players[self._serving].name)
        else:
            self._serving = None
            self._screen.set_serving(None)
            self._say('serve_play')

    def _select_serving(self):
        points = len(self._points)
        if self._points[0] is None: points -= 1
        if points < 2 * self._last_point:
            serving = ((points // 2) % 2) ^ self._serving
        else:
            serving = ((points - self._last_point) % 2) ^ self._serving
        self._screen.set_serving(serving + 1)
        return serving

    def _process_points(self):
        points = [self._points.count(p) for p in (0, 1)]
        serving = self._select_serving()
        try:
            if points[0] >= self._last_point and points[1] >= self._last_point:
                # Tie break
                delta = points[1] - points[0]
                if delta <= -2:
                    raise SetOver(0)
                elif delta >= 2:
                    raise SetOver(1)
                elif delta == -1:
                    self._screen.set_score((f'{self._last_point}+', self._last_point))
                    self._say('advantage', self.players[0].name)
                elif delta == 1:
                    self._screen.set_score((self._last_point, f'{self._last_point}+'))
                    self._say('advantage', self.players[1].name)
                else:
                    self._screen.set_score((self._last_point, self._last_point))
                    self._say('deuce')
            else:
                self._screen.set_score(points)
                self._say_score(points, serving)
                for i in 0, 1:
                    if points[i] > self._last_point: raise SetOver(i)
            self._say('serving', self.players[serving].name)
        except SetOver as set:
            self._sets_history.append(self._points)
            self._sets.append(set.winner)
            self._points = []
            sets = [self._sets.count(p) for p in (0, 1)]
            self._screen.set_score(sets=sets)
            winner = self.players[set.winner]
            if self._sets.count(set.winner) >= self._match_sets:
                self._say('wins_match', winner.name)
                stats = [[sp.count(p) for p in (0, 1)] for sp in self._sets_history]
                self._app.game_over(winner, sets, stats)
            else:
                self._say('wins_set', winner.name)
                self._screen.set_score((0, 0))
                self._say('change_places')
                self._say('score', 0, 0)
                self._serving = 1 - self._serving
                self._screen.set_serving(self._serving + 1)
                self._say('serving', self.players[self._serving].name)

    def score(self, player):
        player -= 1
        if not (self._points or self._sets):
            self._screen.can_undo = True
        if self._serving is None:
            self._points.append(None)
            self._serving = player
            self._screen.set_serving(player + 1)
            self._say('serving', self.players[player].name)
        else:
            self._points.append(player)
            self._process_points()

    def undo(self):
        if self._points:
            p = self._points.pop()
            if p is None:
                self._serving = None
                self._say('serve_play')
                self._screen.set_serving(None)
            else:
                self._process_points()
        elif self._sets:
            self._sets.pop()
            self._points = self._sets_history.pop()
            self._points.pop()
            self._say('change_places')
            self._serving = 1 - self._serving
            self._screen.set_score(sets=[self._sets.count(p) for p in (0, 1)])
            self._process_points()
        if not (self._points or self._sets):
            self._screen.can_undo = False

    @property
    def current_stats(self):
        stats = [[sp.count(p) for p in (0, 1)] for sp in (self._sets_history + [self._points])]
        sets = [self._sets.count(p) for p in (0, 1)]
        return sets, stats

    def _say_score(self, points, serving):
        """TODO"""
        self._say('score', *points)

    def _say(self, what, *args, **kwargs):
        """TODO"""
        print(what, *args)
