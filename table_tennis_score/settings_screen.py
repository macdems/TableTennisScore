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

from kivymd.uix.screen import MDScreen

from .widgets import ComboListItem


class SettingsComboListItem(ComboListItem):

    def on_release(self):
        self.menu_open(self.ids.left)


class SettingsScreen(MDScreen):
    pass
