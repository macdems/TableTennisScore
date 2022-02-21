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
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.utils import platform

from .lang import DEFAULT as DEFAULT_LANG

if platform == 'android':
    from jnius import autoclass, cast
    from android.runnable import run_on_ui_thread

    ActivityInfo = autoclass('android.content.pm.ActivityInfo')
    Locale = autoclass('java.util.Locale')
    Configuration = autoclass('android.content.res.Configuration')
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')

    if 'PYTHON_SERVICE_ARGUMENT' in os.environ:
        PythonService = autoclass('org.kivy.android.PythonService')
        currentActivity = PythonService.mService
    else:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        currentActivity = PythonActivity.mActivity

    def get_system_lang():
        """Return system locale.

        Returns:
            str: Country code.
        """
        try:
            return Locale.getDefault().toString()
        except:
            return DEFAULT_LANG

    def get_system_theme():
        """Return current system theme ('Light' or 'Dark').

        Returns:
            str: 'Light' or 'Dark'.
        """
        context = cast('android.content.Context', currentActivity.getApplicationContext())
        mode = context.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK
        return 'Dark' if mode == Configuration.UI_MODE_NIGHT_YES else 'Light'

    def set_orientation(mode, user=True):
        """Set application orientation.

        Args:
            mode (str): Orientation mode. One of 'auto', 'portrait', or 'landscape'.
            user (bool, optional): If True, tries to obey the user's orientation
                                   settings where applicable. Defaults to False.
        """
        if mode == 'auto':
            if user:
                currentActivity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER)
            else:
                currentActivity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR)
        elif mode == 'portrait':
            if user:
                currentActivity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER_PORTRAIT)
            else:
                currentActivity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT)
        elif mode == 'landscape':
            if user:
                currentActivity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER_LANDSCAPE)
            else:
                currentActivity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE)
        else:
            raise ValueError("'mode' must be one of 'auto', 'portrait', or 'landscape'")

    @run_on_ui_thread
    def lock_screen(lock):
        """Lock the screen always on

        Args:
            lock (bool): If True, lock the screen. Release the lock if False.
        """
        view = currentActivity.getWindow().getDecorView()
        view.setKeepScreenOn(lock)

    class TTS:
        """Test to Speach system.

        Args:
            language (str): Language/country code.
        """

        tts = None

        def __init__(self, language):
            if TTS.tts is None:
                TTS.tts = TextToSpeech(PythonActivity.mActivity, None)
            self.tts.setLanguage(Locale(language))

        def __call__(self, text, reset=False):
            """Say the phrase.

            Args:
               text (str): Text to pronounce.
               reset (bool, optional): If True, the speech in progress is interrupted. Defaults to False.
            """
            self.tts.speak(text, TextToSpeech.QUEUE_FLUSH if reset else TextToSpeech.QUEUE_ADD, None)

else:
    window_width = Window.size[0]
    Window.size = window_width, 1.8 * window_width

    def get_system_lang():
        return os.environ.get('LANG', DEFAULT_LANG).split('.')[0]

    def get_system_theme():
        return os.environ.get('KIVY_COLOR_STYLE', 'Light')

    def set_orientation(mode, user=True):
        if mode == 'portrait':
            Window.size = window_width, 1.8 * window_width
        elif mode == 'landscape':
            Window.size = 1.8 * window_width, window_width
        elif mode != 'auto':
            raise ValueError("'mode' must be one of 'auto', 'portrait', or 'landscape'")

    def lock_screen(lock):
        return

    class TTS:

        def __init__(self, country):
            self.country = country

        def __call__(self, text, reset=False):
            print(text)
