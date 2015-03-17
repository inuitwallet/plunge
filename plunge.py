from kivy.clock import Clock
import logging
import time
import utils

__author__ = 'woolly_sammoth'

from kivy.config import Config

Config.set('graphics', 'borderless', '0')
Config.set('graphics', 'width', '1000')
Config.set('graphics', 'height', '1000')
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

import os
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
        self.settings_cls = 'Settings'
        self.utils = utils.utils(self)
        self.exchanges = ['ccedk', 'poloniex', 'bitcoincoid', 'bter']
        self.active_exchanges = []
        self.currencies = ['btc', 'ltc', 'eur', 'usd', 'ppc']
        self.active_currencies = []

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

        self.topActionBar = TopActionBar()
        self.root.add_widget(self.topActionBar)
        self.root.add_widget(self.mainScreenManager)
        return self.root

    def get_string(self, text):
        try:
            self.logger.debug("Getting string for %s" % text)
            return_string = self.lang[text]
        except (ValueError, KeyError):
            self.logger.error("No string found for %s in %s language file" % (text, self.language))
            return_string = 'Language Error'
        return return_string

    def build_config(self, config):
        config.setdefaults('server', {'host': "104.245.36.10", 'port': 2019, 'period': 30})
        config.setdefaults('config', {'file': os.getcwd() + "/users.dat", 'override': 0})
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
        config.setdefaults('standard', {'language': 'English'})

    def build_settings(self, settings):
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
        if section == "server" and key == "period":
            Clock.unschedule(self.homeScreen.get_stats)
            self.logger.info("Setting refresh Period to %s" % self.config.get('server', 'period'))
            Clock.schedule_interval(self.homeScreen.get_stats, self.config.getint('server', 'period'))
        self.active_exchanges = self.utils.get_active_exchanges()
        self.homeScreen.exchange_spinner.values = [self.get_string(exchange) for exchange in self.active_exchanges]
        self.homeScreen.set_exchange_spinners()

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