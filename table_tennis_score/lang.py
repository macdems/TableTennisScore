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

import yaml
from kivy.lang import Observable
from kivy.logger import Logger

DEFAULT = 'en'


class Text(Observable):
    _observers = []
    strings = {}

    def __init__(self, lang=DEFAULT):
        super().__init__()
        self._set_lang(lang)
        self._available_langs = None

    def _set_lang(self, lang):
        if lang not in self.strings:
            fname = os.path.join(os.path.dirname(__file__), '..', 'assets', 'lang', f'{lang}.yml')
            try:
                self.strings[lang] = yaml.load(open(fname), Loader=yaml.BaseLoader)
            except Exception as err:
                Logger.error(f'Lang: {err}')
        self.lang = lang

    @property
    def available_langs(self):
        if self._available_langs is None:
            self._available_langs = {'auto': "Auto"}
            fname = os.path.join(os.path.dirname(__file__), '..', 'assets', 'lang', '_index.yml')
            try:
                self._available_langs.update(yaml.load(open(fname), Loader=yaml.BaseLoader))
            except Exception as err:
                Logger.error(f'Lang: {err}')
        return self._available_langs

    def __getattr__(self, attr):
        string = str(attr)
        try:
            return self.strings.get(self.lang, self.strings[DEFAULT])[string]
        except KeyError:
            return self.strings[DEFAULT].get(string, string)

    def get(self, string, lang=None):
        if lang is None: lang = self.lang
        return self.strings[lang][string]

    def fbind(self, name, func, args, **kwargs):
        self._observers.append((func, args))

    def funbind(self, name, func, args, **kwargs):
        key = (func, args)
        if key in self._observers:
            self._observers.remove(key)
        else:
            return super().funbind(name, func, *args, **kwargs)

    def set_lang(self, lang):
        if lang != self.lang:
            self._set_lang(lang)
            for func, largs in self._observers:
                func(largs, None, lang)


txt = Text()
