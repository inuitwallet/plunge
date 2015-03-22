import sys
import traceback

__author__ = 'woolly_sammoth'

from kivy.config import Config

Config.set('graphics', 'borderless', '0')
#Config.set('graphics', 'width', '1000')
#Config.set('graphics', 'height', '1000')
Config.set('graphics', 'resizable', '1')
Config.set('graphics', 'fullscreen', '0')
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.actionbar import ActionBar
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.settings import SettingString, SettingSpacer, SettingNumeric
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

import logging
import time
import utils
import os
import json
import socketlogger

import screens.HomeScreen as HomeScreen


class SettingStringFocus(SettingString):

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation='vertical', spacing='5dp')
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(None, None),
            size=(popup_width, '250dp'))

        # create the textinput used for numeric input
        self.textinput = textinput = TextInput(
            text=self.value, font_size='24sp', multiline=False,
            size_hint_y=None, height='42sp')
        textinput.bind(on_text_validate=self._validate)
        self.textinput = textinput

        # construct the content, widget are used as a spacer
        content.add_widget(Widget())
        content.add_widget(textinput)
        content.add_widget(Widget())
        content.add_widget(SettingSpacer())

        # 2 buttons are created for acept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height='50dp', spacing='5dp')
        btn = Button(text='Ok')
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel')
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        # all done, open the popup !
        popup.open()
        textinput.focus = True
        textinput.cursor = (1, 3000)


class SettingNumericFocus(SettingNumeric):

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation='vertical', spacing='5dp')
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(None, None),
            size=(popup_width, '250dp'))

        # create the textinput used for numeric input
        self.textinput = textinput = TextInput(
            text=self.value, font_size='24sp', multiline=False,
            size_hint_y=None, height='42sp')
        textinput.bind(on_text_validate=self._validate)
        self.textinput = textinput

        # construct the content, widget are used as a spacer
        content.add_widget(Widget())
        content.add_widget(textinput)
        content.add_widget(Widget())
        content.add_widget(SettingSpacer())

        # 2 buttons are created for acept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height='50dp', spacing='5dp')
        btn = Button(text='Ok')
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel')
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        # all done, open the popup !
        popup.open()
        textinput.focus = True
        textinput.cursor = (1, 3000)


class TopActionBar(ActionBar):
    def __init__(self, PlungeApp, **kwargs):
        super(TopActionBar, self).__init__(**kwargs)
        self.PlungeApp = PlungeApp
        self.top_action_view = self.ids.top_action_view.__self__
        self.top_action_previous = self.ids.top_action_previous.__self__
        self.top_settings_button = self.ids.top_settings_button.__self__
        self.top_size_button = self.ids.top_size_button.__self__
        self.standard_height = self.height
        self.top_action_previous.bind(on_release=self.PlungeApp.open_settings)
        self.top_settings_button.bind(on_release=self.PlungeApp.open_settings)
        return

    def minimise(self, override=None):
        min = self.top_size_button.text if override is None else override
        if min == self.PlungeApp.get_string("Minimise"):
            Window.size = (350, 100)
            height = self.height
            self.height = 0.5 * height if height == self.standard_height else height
            self.top_size_button.text = self.PlungeApp.get_string("Maximise")
            self.top_action_previous.title = ''
            if self.PlungeApp.config.getint('server', 'monitor') == 0:
                if self.PlungeApp.client_running is True:
                    self.top_action_previous.title = self.PlungeApp.get_string("Running")
                    self.top_action_previous.color = (0, 1, 0.28235, 1)
                else:
                    self.top_action_previous.title = self.PlungeApp.get_string("Stopped")
                    self.top_action_previous.color = (0.93725, 0.21176, 0.07843, 1)
            self.top_action_previous.bind(on_release=self.minimise)
            self.top_action_previous.unbind(on_release=self.PlungeApp.open_settings)
            self.top_settings_button.text = ''
            self.top_settings_button.bind(on_release=self.minimise)
            self.top_settings_button.unbind(on_release=self.PlungeApp.open_settings)
            self.PlungeApp.homeScreen.clear_widgets()
            self.PlungeApp.homeScreen.add_widget(self.PlungeApp.homeScreen.min_layout)
            self.PlungeApp.is_min = True
        else:
            Window.size = (1000, 1000)
            height = self.height
            self.height = 2 * height if height != self.standard_height else height
            self.top_size_button.text = self.PlungeApp.get_string("Minimise")
            self.top_action_previous.title = self.PlungeApp.get_string('Main_Title')
            self.top_action_previous.color = (1, 1, 1, 1)
            self.top_action_previous.bind(on_release=self.PlungeApp.open_settings)
            self.top_action_previous.unbind(on_release=self.minimise)
            self.top_settings_button.text = self.PlungeApp.get_string("Settings")
            self.top_settings_button.bind(on_release=self.PlungeApp.open_settings)
            self.top_settings_button.unbind(on_release=self.minimise)
            self.PlungeApp.homeScreen.clear_widgets()
            self.PlungeApp.homeScreen.add_widget(self.PlungeApp.homeScreen.max_layout)
            self.PlungeApp.is_min = False
        return


class PlungeApp(App):
    def __init__(self, **kwargs):
        super(PlungeApp, self).__init__(**kwargs)
        self.isPopup = False
        self.use_kivy_settings = False
        self.settings_cls = 'Settings'
        self.utils = utils.utils(self)
        self.exchanges = ['ccedk', 'poloniex', 'bitcoincoid', 'bter']
        self.active_exchanges = []
        self.currencies = ['btc', 'ltc', 'eur', 'usd', 'ppc']
        self.active_currencies = []
        self.client_running = False
        self.is_min = False

        if not os.path.isdir('logs'):
            os.makedirs('logs')
        self.logger = logging.getLogger('Plunge')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('logs/%s_%d.log' % ('Plunge', time.time()))
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: %(message)s', datefmt="%Y/%m/%d-%H:%M:%S")
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        self.logger_socket = socketlogger.start_logging_receiver('Plunge')
        #sys.excepthook = self.log_uncaught_exceptions
        return


    def log_uncaught_exceptions(self, exctype, value, tb):
        self.logger.exception('\n===================\nException Caught\n\n%s\n===================\n' % value)
        return

    def build(self):
        self.logger.info("Fetching language from config")
        self.language = self.config.get('standard', 'language')
        try:
            self.lang = json.load(open('res/json/languages/' + self.language.lower() + '.json', 'r'))
        except (ValueError, IOError) as e:
            self.logger.error('')
            self.logger.error('##################################################################')
            self.logger.error('')
            self.logger.error('There was an Error loading the ' + self.language + ' language file.')
            self.logger.error('')
            self.logger.error(str(e))
            self.logger.error('')
            self.logger.error('##################################################################')
            raise SystemExit

        self.root = BoxLayout(orientation='vertical')

        self.mainScreenManager = ScreenManager(transition=SlideTransition(direction='left'))
        Builder.load_file('screens/HomeScreen.kv')
        self.homeScreen = HomeScreen.HomeScreen(self)
        self.mainScreenManager.add_widget(self.homeScreen)

        self.topActionBar = TopActionBar(self)
        self.root.add_widget(self.topActionBar)
        self.root.add_widget(self.mainScreenManager)
        self.homeScreen.clear_widgets()
        if self.config.getint('standard', 'start_min') == 1:
            self.topActionBar.minimise(self.get_string("Minimise"))
            self.is_min = True
        else:
            self.topActionBar.minimise(self.get_string("Maximise"))
            self.is_min = False
            self.set_monitor()
        return self.root

    def set_monitor(self):
        if self.is_min is False:
            self.homeScreen.max_layout.remove_widget(self.homeScreen.run_layout)
            if self.config.getint('server', 'monitor') == 1:
                Window.size = (1000, 800)
            else:
                self.homeScreen.max_layout.add_widget(self.homeScreen.run_layout)
                Window.size = (1000, 1000)

    def get_string(self, text):
        try:
            self.logger.debug("Getting string for %s" % text)
            return_string = self.lang[text]
        except (ValueError, KeyError):
            self.logger.error("No string found for %s in %s language file" % (text, self.language))
            return_string = 'Language Error'
        return return_string

    def build_config(self, config):
        config.setdefaults('server', {'host': "104.245.36.10", 'port': 2019, 'period': 30, 'monitor': 0})
        config.setdefaults('config', {'file': os.getcwd() + "/users.dat", 'override': 0, 'remote': 0,
                                      'remote_server': '', 'remote_port': ''})
        config.setdefaults('exchanges', {'ccedk': 0, 'poloniex': 0, 'bitcoincoid': 0, 'bter': 0})
        config.setdefaults('ccedk',
                           {'address': '', 'public': '', 'secret': '', 'nubot': 0,
                            'btc': 0, 'ltc': 0, 'ppc': 0, 'usd': 0, 'eur': 0})
        config.setdefaults('poloniex',
                           {'address': '', 'public': '', 'secret': '', 'nubot': 0, "btc": 0})
        config.setdefaults('bitcoincoid',
                           {'address': '', 'public': '', 'secret': '', 'nubot': 0, "btc": 0})
        config.setdefaults('bter',
                           {'address': '', 'public': '', 'secret': '', 'nubot': 0, "btc": 0})
        config.setdefaults('standard', {'language': 'English', 'start_min': 0, 'data': 0})

    def build_settings(self, settings):
        settings.register_type('string', SettingStringFocus)
        settings.register_type('numeric', SettingNumericFocus)
        settings.add_json_panel(self.get_string('Plunge_Configuration'), self.config, 'settings/plunge.json')
        if self.config.getint('exchanges', 'ccedk') == 1:
            settings.add_json_panel(self.get_string('CCEDK_Settings'), self.config, 'settings/ccedk.json')
        if self.config.getint('exchanges', 'poloniex') == 1:
            settings.add_json_panel(self.get_string('Poloniex_Settings'), self.config, 'settings/poloniex.json')
        if self.config.getint('exchanges', 'bitcoincoid') == 1:
            settings.add_json_panel(self.get_string('BitcoinCoId_Settings'), self.config, 'settings/bitcoincoid.json')
        if self.config.getint('exchanges', 'bter') == 1:
            settings.add_json_panel(self.get_string('Bter_Settings'), self.config, 'settings/bter.json')

    def on_config_change(self, config, section, key, value):
        if section == "exchanges":
            self.logger.info("%s/%s config changed to %s" % (section, key, value))
            self.close_settings()
            self.destroy_settings()
            self.open_settings()
        if section == "server":
            if key == "period":
                Clock.unschedule(self.homeScreen.get_stats)
                self.logger.info("Setting refresh Period to %s" % self.config.get('server', 'period'))
                Clock.schedule_interval(self.homeScreen.get_stats, self.config.getint('server', 'period'))
            if key == "monitor":
                self.set_monitor()
        self.active_exchanges = self.utils.get_active_exchanges()
        self.homeScreen.exchange_spinner.values = [self.get_string(exchange) for exchange in self.active_exchanges]
        self.homeScreen.set_exchange_spinners()
        self.homeScreen.get_stats(0)

    def show_popup(self, title, text):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=text, size_hint=(1, .9)))
        button = Button(text=self.get_string('OK'), size_hint=(None, None), width=250, height=50)
        content.add_widget(button)
        self.popup = Popup(title=title, content=content, auto_dismiss=False, size_hint=(None, None), size=(500, 200))
        button.bind(on_press=self.close_popup)
        self.popup.open()
        self.isPopup = True
        return

    def close_popup(self, instance, value=False):
        self.popup.dismiss()
        self.isPopup = False
        return


if __name__ == '__main__':
    Plunge = PlungeApp()
    Plunge.run()
