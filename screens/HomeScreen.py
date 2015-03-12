from kivy.clock import Clock
import os
from platform import system
import subprocess
import signal
from Queue import Queue, Empty
from threading  import Thread
import sys
import utils

__author__ = 'woolly_sammoth'

from kivy.uix.screenmanager import Screen


class HomeScreen(Screen):

    def __init__(self, PlungeApp, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.PlungeApp = PlungeApp
        self.start_button = self.ids.start_button.__self__
        self.log_output = self.ids.log_output.__self__
        self.running_label = self.ids.running_label.__self__
        self.overall_buy_side = self.ids.overall_buy_side.__self__
        self.overall_sell_side = self.ids.overall_sell_side.__self__

        Clock.schedule_interval(self.get_stats, self.PlungeApp.config.getint('server', 'period'))
        self.get_stats(0)
        return

    def get_stats(self, dt):
        self.status = dict(utils.get("http://%s:%s/status" %
                                     (self.PlungeApp.config.get('server', 'host'),
                                      self.PlungeApp.config.get('server', 'port'))))
        self.exchanges = dict(utils.get("http://%s:%s/exchanges" %
                                        (self.PlungeApp.config.get('server', 'host'),
                                         self.PlungeApp.config.get('server', 'port'))))
        self.exchange = {}
        for exchange in self.PlungeApp.exchanges:
            self.exchange[exchange] = dict(utils.get("http://%s:%s/%s" %
                                                     (self.PlungeApp.config.get('server', 'host'),
                                                      self.PlungeApp.config.get('server', 'port'),
                                                      self.PlungeApp.config.get(exchange, 'public'))))

        self.update_overall_liquidity()

    def update_overall_liquidity(self):
        liquidity = list(self.status['liquidity'])
        self.overall_buy_side.text = str(liquidity[0])
        self.overall_sell_side.text = str(liquidity[1])


    def toggle_client(self):
        text = self.start_button.text
        if text == "Start":
            self.start_client()
        else:
            self.stop_client()

    def start_client(self):
        override = self.PlungeApp.config.getint('config', 'override')
        config_file = self.PlungeApp.config.get('config', 'file')
        if os.path.isfile(config_file):
            if override == 1:
                self.run_client()
                return
            else:
                os.remove(config_file)
        self.build_config_file()
        self.run_client()

    def build_config_file(self):
        with open(self.PlungeApp.config.get('config', 'file'), "w+") as config_file:
            for exchange in self.PlungeApp.exchanges:
                active = self.PlungeApp.config.getint('exchanges', exchange)
                if active == 0:
                    continue
                address = self.PlungeApp.config.get(exchange, 'address')
                if address == "":
                    self.PlungeApp.show_popup(self.PlungeApp.get_string("Config_Error"),
                                              self.PlungeApp.get_string("No_Address") %
                                              self.PlungeApp.get_string(exchange))
                    return
                if not utils.check_checksum(address):
                    self.PlungeApp.show_popup(self.PlungeApp.get_string("Config_Error"),
                                              self.PlungeApp.get_string("Invalid_Address") %
                                              self.PlungeApp.get_string(exchange))
                    return
                public = self.PlungeApp.config.get(exchange, 'public')
                if public == "":
                    self.PlungeApp.show_popup(self.PlungeApp.get_string("Config_Error"),
                                              self.PlungeApp.get_string("No_Public") %
                                              self.PlungeApp.get_string(exchange))
                    return
                secret = self.PlungeApp.config.get(exchange, 'secret')
                if secret == "":
                    self.PlungeApp.show_popup(self.PlungeApp.get_string("Config_Error"),
                                              self.PlungeApp.get_string("No_Secret") %
                                              self.PlungeApp.get_string(exchange))
                    return
                nubot = "nubot" if self.PlungeApp.config.getint(exchange, 'nubot') == 1 else ""
                for currency in self.PlungeApp.currencies:
                    active = self.PlungeApp.config.getdefaultint(exchange, currency, 0)
                    if active == 1:
                        config_file.write("%s %s %s %s %s %s\n" % (address, currency.upper(), exchange, public, secret, nubot))
        config_file.close()

    def enqueue_output(self, out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

    def run_client(self):
        host = self.PlungeApp.config.get('server', 'host')
        ip = self.PlungeApp.config.get('server', 'port')
        config_file = self.PlungeApp.config.get('config', 'file')
        command = ""
        ON_POSIX = 'posix' in sys.builtin_module_names
        if system() == 'Linux':
            command = ["python", "%s/client/client.py" % os.getcwd(), "%s:%s" % (host, ip), "%s" % config_file]
        try:
            self.output = subprocess.Popen(command, stderr=subprocess.PIPE, bufsize=1, close_fds=ON_POSIX)
            self.q = Queue()
            self.t = Thread(target=self.enqueue_output, args=(self.output.stderr, self.q))
            self.t.daemon = True
            self.t.start()
        except OSError as e:
            self.PlungeApp.show_popup(self.PlungeApp.get_string('Popup_Error'),
                                      "%s\n\n%s" % (self.PlungeApp.get_string('Client_Run_Error'), e.strerror))
            return
        Clock.schedule_interval(self.read_output, 0.2)
        self.running_label.color = (0, 1, 0.28235, 1)
        self.running_label.text = self.PlungeApp.get_string("Client_Started")
        self.start_button.text = self.PlungeApp.get_string('Stop')

    def read_output(self, dt):
        try:
            line = self.q.get_nowait()
        except Empty:
            return
        else:
            self.log_output.text += line

    def stop_client(self):
        self.output.send_signal(signal.SIGTERM)
        self.log_output.text += 'Stopped!\n'
        self.running_label.color = (0.93725, 0.21176, 0.07843, 1)
        self.running_label.text = self.PlungeApp.get_string("Client_Stopped")
        self.start_button.text = self.PlungeApp.get_string('Start')