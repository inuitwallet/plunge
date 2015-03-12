import os
import utils

__author__ = 'woolly_sammoth'

from kivy.config import Config, ConfigParser

Config.set('graphics', 'width', '1000')
Config.set('graphics', 'height', '1000')
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'fullscreen', '0')
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager
from kivy.animation import Animation
from kivy.uix.actionbar import ActionBar
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.popup import Popup
from kivy.lang import Builder

import json

import screens.HomeScreen as HomeScreen


class TopActionBar(ActionBar):
    def __init__(self, **kwargs):
        super(TopActionBar, self).__init__(**kwargs)
        return


class PlungeApp(App):
    def __init__(self, **kwargs):
        super(PlungeApp, self).__init__(**kwargs)
        self.isPopup = False
        self.use_kivy_settings = False

        self.exchanges = ["ccedk", "poloniex", "bitcoincoid"]
        self.currencies = ["btc", "ltc", "ppc", "eur", "usd"]
        return

    def build(self):

        self.language = self.config.get('language', 'active_language')
        try:
            self.lang = json.load(open('res/json/languages/' + self.language + '.json', 'r'))
        except (ValueError, IOError) as e:
            print('')
            print('##################################################################')
            print('')
            print('There was an Error loading the ' + self.language + ' language file.')
            print('')
            print(str(e))
            print('')
            print('##################################################################')
            raise SystemExit

        self.root = BoxLayout(orientation='vertical')

        self.mainScreenManager = ScreenManager(transition=SlideTransition(direction='left'))
        Builder.load_file('screens/HomeScreen.kv')
        self.homeScreen = HomeScreen.HomeScreen(self)
        self.mainScreenManager.add_widget(self.homeScreen)

        self.topActionBar = TopActionBar()
        self.root.add_widget(self.topActionBar)
        self.root.add_widget(self.mainScreenManager)
        return self.root

    def get_string(self, text):
        try:
            return_string = self.lang[text]
        except (ValueError, KeyError):
            return_string = 'Language Error'
        return return_string

    def build_config(self, config):
        config.setdefaults('language', {'active_language': 'english'})
        config.setdefaults('server', {'host': "104.245.36.10", 'port': 2019, 'period': 30})
        config.setdefaults('config', {'file': os.getcwd() + "/users.dat", 'override': 0})
        config.setdefaults('exchanges', {'ccedk': 1, 'poloniex': 1, 'bitcoincoid': 1})
        config.setdefaults('ccedk',
                           {'address': '', 'public': '', 'secret': '', 'nubot': 0,
                            "btc": 0, "ltc": 0, "ppc": 0, "eur": 0, "usd": 0})
        config.setdefaults('poloniex',
                           {'address': '', 'public': '', 'secret': '', 'nubot': 0, "btc": 0})
        config.setdefaults('bitcoincoid',
                           {'address': '', 'public': '', 'secret': '', 'nubot': 0,
                            "btc": 0, "ltc": 0, "ppc": 0, "eur": 0, "usd": 0})

    def build_settings(self, settings):
        settings.add_json_panel(self.get_string('Plunge_Configuration'), self.config, 'settings/plunge.json')
        if self.config.getint('exchanges', 'ccedk') == 1:
            settings.add_json_panel(self.get_string('CCEDK_Settings'), self.config, 'settings/ccedk.json')
        if self.config.getint('exchanges', 'poloniex') == 1:
            settings.add_json_panel(self.get_string('Poloniex_Settings'), self.config, 'settings/poloniex.json')
        if self.config.getint('exchanges', 'bitcoincoid') == 1:
            settings.add_json_panel(self.get_string('BitcoinCoId_Settings'), self.config, 'settings/bitcoincoid.json')

    def on_config_change(self, config, section, key, value):
        if section == "exchanges":
            self.close_settings()
            self.destroy_settings()
            self.open_settings()

    def show_popup(self, title, text):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=text, size_hint=(1, .7)))
        button = Button(text=self.get_string('OK'), size_hint=(1, .3))
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