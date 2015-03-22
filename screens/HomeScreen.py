from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.garden.graph import Graph, SmoothLinePlot, MeshStemPlot
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
import os
from platform import system
import subprocess
import signal
from Queue import Queue, Empty
from threading import Thread
import sys
from decimal import Decimal

__author__ = 'woolly_sammoth'

from kivy.uix.screenmanager import Screen


class HomeScreen(Screen):

    def __init__(self, PlungeApp, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.PlungeApp = PlungeApp
        self.PlungeApp.logger.info("Building Home Page")
        # strong links to widgets
        self.max_layout = self.ids.max_layout.__self__
        self.min_layout = self.ids.min_layout.__self__
        self.run_layout = self.ids.run_layout.__self__
        self.start_button = self.ids.start_button.__self__
        self.log_output = self.ids.log_output.__self__
        self.running_label = self.ids.running_label.__self__
        self.pool_buy_side = self.ids.pool_buy_side.__self__
        self.pool_sell_side = self.ids.pool_sell_side.__self__
        self.exchange_spinner = self.ids.exchange_spinner.__self__
        self.currency_spinner = self.ids.currency_spinner.__self__
        self.exchange_buy_side_label = self.ids.exchange_buy_side.__self__
        self.exchange_sell_side_label = self.ids.exchange_sell_side.__self__
        self.exchange_valid_label = self.ids.exchange_valid.__self__
        self.exchange_balance_label = self.ids.exchange_balance.__self__
        self.exchange_efficiency_label = self.ids.exchange_efficiency.__self__
        self.exchange_missing_label = self.ids.exchange_missing.__self__
        self.exchange_rejects_label = self.ids.exchange_rejects.__self__
        self.personal_buy_side = self.ids.personal_buy_side.__self__
        self.personal_sell_side = self.ids.personal_sell_side.__self__
        self.personal_efficiency = self.ids.personal_efficiency.__self__
        self.personal_balance = self.ids.personal_balance.__self__
        self.min_efficiency = self.ids.min_efficiency.__self__
        self.min_balance = self.ids.min_balance.__self__

        # set up variables
        self.primary_currency = None
        self.primary_exchange = None
        self.num_users = None
        self.sampling = None
        self.total_buy_side = None
        self.total_sell_side = None
        self.total_efficiency = None
        self.total_balance = None

        self.exchange_buy_side = {}
        self.exchange_sell_side = {}
        self.exchange_valid = {}
        for exchange in self.PlungeApp.active_exchanges:
            self.exchange_buy_side[exchange] = None
            self.exchange_sell_side[exchange] = None
            self.exchange_valid[exchange] = None

        # set up the dictionaries that hold the returned server data
        self.pool = {}
        self.stats = {}
        self.user = {}

        # set up the lists that hold the historical data for graphing
        self.pool_buy_liquidity = []
        self.pool_sell_liquidity = []
        self.exchange_efficiency = {}
        self.exchange_balance = {}
        self.exchange_missing = {}
        self.exchange_rejects = {}
        self.exchange_buy_liquidity = {}
        self.exchange_sell_liquidity = {}
        self.exchange_valid_submissions = {}
        self.total_buy_liquidity = []
        self.total_sell_liquidity = []
        self.total_efficiency_list = []
        self.total_balance_list = []

        # set up UI and start timers
        self.set_exchange_spinners()
        self.PlungeApp.logger.info("Setting refresh Period to %s" % self.PlungeApp.config.get('server', 'period'))
        Clock.schedule_interval(self.get_stats, self.PlungeApp.config.getint('server', 'period'))
        self.get_stats(0)
        return

    def set_exchange_spinners(self):
        set_spinners = Thread(target=self._set_exchange_spinners)
        set_spinners.start()

    def _set_exchange_spinners(self):
        # see if any exchanges are enabled so that we can display the stats
        self.primary_exchange = ''
        self.primary_currency = ''
        self.PlungeApp.active_exchanges = self.PlungeApp.utils.get_active_exchanges()
        for exchange in self.PlungeApp.active_exchanges:
            if self.PlungeApp.get_string(exchange) == self.exchange_spinner.text:
                self.primary_exchange = exchange
        self.PlungeApp.logger.info("Set Primary Exchange to %s" % self.primary_exchange)
        if self.primary_exchange == '':
            self.PlungeApp.active_exchanges = self.PlungeApp.utils.get_active_exchanges()
            if self.PlungeApp.active_exchanges:
                self.exchange_spinner.values = [self.PlungeApp.get_string(exchange) for
                                                exchange in self.PlungeApp.active_exchanges]
                self.primary_exchange = self.PlungeApp.active_exchanges[0]
                self.exchange_spinner.text = self.PlungeApp.get_string(self.primary_exchange)
            else:
                self.PlungeApp.show_popup(self.PlungeApp.get_string('Popup_Error'),
                                          self.PlungeApp.get_string('No_Exchanges'))
                return
        self.PlungeApp.active_currencies = self.PlungeApp.utils.get_active_currencies(self.primary_exchange)
        if self.PlungeApp.active_currencies:
            self.currency_spinner.values = [currency.upper() for currency in self.PlungeApp.active_currencies]
            self.primary_currency = self.PlungeApp.active_currencies[0]
            self.currency_spinner.text = self.primary_currency.upper()
        self.get_stats(0)

    def set_primary_currency(self):
        self.primary_currency = self.currency_spinner.text.lower()
        self.PlungeApp.logger.info("Set Primary Currency to %s" % self.primary_currency)
        self.get_stats(0)

    def get_stats(self, dt):
        pool = Thread(target=self.get_pool_stats)
        pool.start()
        exchange = Thread(target=self.get_exchange_stats)
        exchange.start()
        personal = Thread(target=self.get_personal_stats)
        personal.start()

    def update_lists(self, value, in_list):
        in_list.append(value)
        data_to_keep = self.PlungeApp.config.getint('standard', 'data')
        if data_to_keep > 0:
            while len(in_list) > data_to_keep:
                in_list.pop(0)

    def get_pool_stats(self):
        # get the pool status
        self.PlungeApp.logger.info("Get the Pool Stats")
        status = dict(self.PlungeApp.utils.get("http://%s:%s/status" %
                                               (self.PlungeApp.config.get('server', 'host'),
                                                self.PlungeApp.config.get('server', 'port'))))
        
        if 'error' not in status:
            self.PlungeApp.logger.info("Server returned %s" % status)
            self.pool = {}
            self.pool['buy_liquidity'] = status['liquidity'][0]
            self.pool['sell_liquidity'] = status['liquidity'][1]
            self.pool['num_users'] = status['users']
            self.pool['sampling'] = status['sampling']
            self.PlungeApp.logger.info("Pool stats - %s" % str(self.pool))

            self.update_lists(self.pool['buy_liquidity'], self.pool_buy_liquidity)
            self.update_lists(self.pool['sell_liquidity'], self.pool_sell_liquidity)

            self.update_pool_stats()
        else:
            self.PlungeApp.logger.error("%d - %s" % (status['code'], status['message']))

    def get_exchange_stats(self):
        # get the exchange status
        self.PlungeApp.logger.info("Get the Exchange Stats")
        exchanges = dict(self.PlungeApp.utils.get("http://%s:%s/exchanges" %
                                                  (self.PlungeApp.config.get('server', 'host'),
                                                   self.PlungeApp.config.get('server', 'port'))))

        if 'error' not in exchanges:
            self.PlungeApp.logger.info("Server returned %s" % exchanges)
            self.stats = {}
            for exchange in self.PlungeApp.active_exchanges:
                self.stats[exchange] = {}
                for currency in self.PlungeApp.active_currencies:
                    if currency in exchanges[exchange]:
                        self.stats[exchange][currency] = {}
                        self.stats[exchange][currency]['rate'] = str(round(exchanges[exchange][currency]['rate'], 4))
                        self.stats[exchange][currency]['fee'] = str(round(exchanges[exchange][currency]['fee'], 4))
                        self.stats[exchange][currency]['target'] = str(round(exchanges[exchange][currency]['target'], 4))
            self.PlungeApp.logger.info("Exchange Stats - %s" % str(self.stats))
        else:
            self.PlungeApp.logger.error("%d - %s" % (exchanges['code'], exchanges['message']))

    def get_personal_stats(self):
        #get the individual status for each acccount
        self.user = {}
        for exchange in self.PlungeApp.active_exchanges:
            self.PlungeApp.logger.info("Get Personal Stats for %s" % exchange)
            user = dict(self.PlungeApp.utils.get("http://%s:%s/%s" %
                                                 (self.PlungeApp.config.get('server', 'host'),
                                                  self.PlungeApp.config.get('server', 'port'),
                                                  self.PlungeApp.config.get(exchange, 'public'))))
            if 'error' not in user:
                self.PlungeApp.logger.info("Server returned %s" % user)
                self.user[exchange] = {}
                self.user[exchange]['efficiency'] = user['efficiency']
                self.user[exchange]['balance'] = user['balance']
                self.user[exchange]['missing'] = user['missing']
                self.user[exchange]['rejects'] = user['rejects']
                # update the graph data lists
                if exchange not in self.exchange_efficiency:
                    self.exchange_efficiency[exchange] = []
                self.update_lists((self.user[exchange]['efficiency'] * 100), self.exchange_efficiency[exchange])
                if exchange not in self.exchange_balance:
                    self.exchange_balance[exchange] = []
                self.update_lists(self.user[exchange]['balance'], self.exchange_balance[exchange])
                if exchange not in self.exchange_missing:
                    self.exchange_missing[exchange] = []
                self.update_lists(self.user[exchange]['missing'], self.exchange_missing[exchange])
                if exchange not in self.exchange_rejects:
                    self.exchange_rejects[exchange] = []
                self.update_lists(self.user[exchange]['rejects'], self.exchange_rejects[exchange])
                for currency in self.PlungeApp.active_currencies:
                    if currency in user['units']:
                        self.user[exchange][currency] = {}
                        self.user[exchange][currency]['ask_orders'] = user['units'][currency]['ask']
                        self.user[exchange][currency]['bid_orders'] = user['units'][currency]['bid']
                        self.user[exchange][currency]['last_error'] = user['units'][currency]['last_error']
                        self.user[exchange][currency]['rejects'] = user['units'][currency]['rejects']
                        self.user[exchange][currency]['missing'] = user['units'][currency]['missing']
                    else:
                        self.PlungeApp.logger.error("%s not found in server return" % currency)
            else:
                self.PlungeApp.logger.error("%d - %s" % (user['code'], user['message']))
        self.PlungeApp.logger.info("Personal Stats - %s" % str(self.user))
        if self.primary_exchange in self.user:
            if self.primary_currency in self.user[self.primary_exchange]:
                self.update_personal_stats()
            else:
                self.PlungeApp.logger.error("%s not found in personal stats" % self.primary_currency)
        else:
            self.PlungeApp.logger.error("%s not found in personal stats" % self.primary_exchange)

    def update_pool_stats(self):
        self.PlungeApp.logger.info("Update Pool stats")
        self.pool_buy_side.text = "[ref='pool_buy_side']%.4f[/ref]" % self.pool['buy_liquidity']
        self.pool_sell_side.text = "[ref='pool_sell_side']%.4f[/ref]" % self.pool['sell_liquidity']

    def update_personal_stats(self):
        self.PlungeApp.logger.info("Update stats")
        self.exchange_balance_label.text = "[ref='exchange_balance']%.4f[/ref]" % self.user[self.primary_exchange]['balance']
        self.exchange_efficiency_label.text = "[ref='exchange_efficiency']%.2f%%[/ref]" % (self.user[self.primary_exchange]['efficiency'] * 100)
        self.exchange_missing_label.text = "[ref='exchange_missing']%d[/ref]" % self.user[self.primary_exchange]['missing']
        self.exchange_rejects_label.text = "[ref='exchange_rejects']%d[/ref]" % self.user[self.primary_exchange]['rejects']

        self.calculations()

        self.exchange_buy_side_label.text = "[ref='exchange_buy_side']%.4f[/ref]" % self.exchange_buy_side[self.primary_exchange]
        self.exchange_sell_side_label.text = "[ref='exchange_sell_side']%.4f[/ref]" % self.exchange_sell_side[self.primary_exchange]
        self.exchange_valid_label.text = "[ref='exchange_valid']%d[/ref]" % self.exchange_valid[self.primary_exchange]

        self.personal_buy_side.text = "[ref='total_buy_side']%.4f[/ref]" % self.total_buy_side
        self.personal_sell_side.text = "[ref='total_sell_side']%.4f[/ref]" % self.total_sell_side
        self.personal_efficiency.text = "[ref='total_efficiency']%.2f%%[/ref]" % (self.total_efficiency * 100)
        self.min_efficiency.text = "%.2f%%" % (self.total_efficiency * 100)
        self.personal_balance.text = "[ref='total_balance']%.4f[/ref]" % self.total_balance
        self.min_balance.text = "%.4f" % self.total_balance

    def calculations(self):
        # total buy side liquidity
        self.total_buy_side = 0
        self.total_sell_side = 0
        self.total_efficiency = 0
        self.total_balance = 0
        self.PlungeApp.logger.info("Calculations")
        for exchange in self.PlungeApp.active_exchanges:
            self.exchange_buy_side[exchange] = 0
            self.exchange_sell_side[exchange] = 0
            if exchange in self.user:
                self.exchange_valid[exchange] = self.pool['sampling'] - (self.user[exchange]['missing'] + self.user[exchange]['rejects'])
                self.total_efficiency += self.user[exchange]['efficiency']
                self.total_balance += self.user[exchange]['balance']
                for currency in self.PlungeApp.active_currencies:
                    if currency in self.user[exchange]:
                        for order in self.user[exchange][currency]['bid_orders']:
                            self.total_buy_side += order[1]
                            self.exchange_buy_side[exchange] += order[1]
                        for order in self.user[exchange][currency]['ask_orders']:
                            self.total_sell_side += order[1]
                            self.exchange_sell_side[exchange] += order[1]
                    else:
                        self.PlungeApp.logger.error("%s not found in personal stats" % currency)
                # update exchange graphing lists
                if exchange not in self.exchange_buy_liquidity:
                    self.exchange_buy_liquidity[exchange] = []
                self.update_lists(self.exchange_buy_side[exchange], self.exchange_buy_liquidity[exchange])
                if exchange not in self.exchange_sell_liquidity:
                    self.exchange_sell_liquidity[exchange] = []
                self.update_lists(self.exchange_sell_side[exchange], self.exchange_sell_liquidity[exchange])
                if exchange not in self.exchange_valid_submissions:
                    self.exchange_valid_submissions[exchange] = []
                self.update_lists(self.exchange_valid[exchange], self.exchange_valid_submissions[exchange])
            else:
                self.PlungeApp.logger.error("%s not found in personal stats" % exchange)

        self.total_efficiency /= len(self.PlungeApp.active_exchanges)

        # update the total graphing lists
        self.update_lists(self.total_buy_side, self.total_buy_liquidity)
        self.update_lists(self.total_sell_side, self.total_sell_liquidity)
        self.update_lists((self.total_efficiency * 100), self.total_efficiency_list)
        self.update_lists(self.total_balance, self.total_balance_list)

    def toggle_client(self):
        text = self.start_button.text
        if text == "Start":
            self.PlungeApp.logger.info("Starting client")
            self.start_client()
        else:
            self.PlungeApp.logger.info("Stopping client")
            self.stop_client()

    def start_client(self):
        override = self.PlungeApp.config.getint('config', 'override')
        config_file = self.PlungeApp.config.get('config', 'file')
        if os.path.isfile(config_file):
            if override == 1:
                self.PlungeApp.logger.info("Starting client without building config file")
                self.run_client()
                return
            else:
                os.remove(config_file)
        if self.build_config_file():
            self.run_client()

    def build_config_file(self):
        self.PlungeApp.logger.info("Building config file")
        with open(self.PlungeApp.config.get('config', 'file'), "w+") as config_file:
            for exchange in self.PlungeApp.exchanges:
                self.PlungeApp.logger.info("Setting config for %s" % exchange)
                active = self.PlungeApp.config.getint('exchanges', exchange)
                if active == 0:
                    continue
                address = self.PlungeApp.config.get(exchange, 'address')
                if address == "":
                    self.PlungeApp.logger.error("No Payout Address set")
                    self.PlungeApp.show_popup(self.PlungeApp.get_string("Config_Error"),
                                              self.PlungeApp.get_string("No_Address") %
                                              self.PlungeApp.get_string(exchange))
                    return False
                if not self.PlungeApp.utils.check_checksum(address):
                    self.PlungeApp.logger.error("Invalid Payout Address")
                    self.PlungeApp.show_popup(self.PlungeApp.get_string("Config_Error"),
                                              self.PlungeApp.get_string("Invalid_Address") %
                                              self.PlungeApp.get_string(exchange))
                    return False
                public = self.PlungeApp.config.get(exchange, 'public')
                if public == "":
                    self.PlungeApp.logger.error("No Public API Key set")
                    self.PlungeApp.show_popup(self.PlungeApp.get_string("Config_Error"),
                                              self.PlungeApp.get_string("No_Public") %
                                              self.PlungeApp.get_string(exchange))
                    return False
                secret = self.PlungeApp.config.get(exchange, 'secret')
                if secret == "":
                    self.PlungeApp.logger.error("No Secret API Key set")
                    self.PlungeApp.show_popup(self.PlungeApp.get_string("Config_Error"),
                                              self.PlungeApp.get_string("No_Secret") %
                                              self.PlungeApp.get_string(exchange))
                    return False
                nubot = "nubot" if self.PlungeApp.config.getint(exchange, 'nubot') == 1 else ""
                for currency in self.PlungeApp.currencies:
                    active = self.PlungeApp.config.getdefaultint(exchange, currency, 0)
                    if active == 1:
                        config_file.write("%s %s %s %s %s %s\n" % (address, currency.upper(), exchange, public, secret, nubot))
        config_file.close()
        self.PlungeApp.logger.info("Config file built")
        return True

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
        self.PlungeApp.logger.info("Running client with command %s" % command)
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
        self.PlungeApp.client_running = True
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
        self.PlungeApp.client_running = False
        self.running_label.color = (0.93725, 0.21176, 0.07843, 1)
        self.running_label.text = self.PlungeApp.get_string("Client_Stopped")
        self.start_button.text = self.PlungeApp.get_string('Start')
        self.PlungeApp.logger.error("Client Stopped")

    def draw_chart(self, title, y_label, points):
        y_min = min(points) if len(points) > 0 else 0
        y_max = max(points) if len(points) > 0 else 100
        self.graph = Graph(ylabel=y_label, x_ticks_minor=5, x_ticks_major=25, y_ticks_major=5,
                      y_grid_label=True, x_grid_label=True, padding=5, x_grid=True, y_grid=True, xmin=0,
                      xmax=len(points), ymin=(y_min-10), ymax=(y_max+10))
        tuple_points = []
        x = 0
        for point in points:
            tuple_points.append((x, point))
            x += 1
        plot = SmoothLinePlot(color=[0.93725, 0.21176, 0.07843, 1])
        plot.points = tuple_points
        self.graph.add_plot(plot)
        self.show_graph_popup(title)

    def draw_liquidity_chart(self, title, buy_points, sell_points, stem=False):
        print(buy_points)
        print(sell_points)
        y_min = min(buy_points, sell_points)
        y_max = max(buy_points, sell_points)
        self.graph = Graph(ylabel='NBT', x_ticks_minor=5, x_ticks_major=25, y_ticks_major=5,
                      y_grid_label=True, x_grid_label=True, padding=5, x_grid=True, y_grid=True, xmin=0,
                      xmax=len(y_max), ymin=(min(y_min)-10), ymax=(max(y_max)+20))
        if stem is True:
            buy_plot = MeshStemPlot(color=[1, 0.72157, 0, 1])
        else:
            buy_plot = SmoothLinePlot(color=[1, 0.72157, 0, 1])
        points = []
        x = 0
        for point in buy_points:
            points.append((x, point))
            x += 1
        buy_plot.points = points
        self.graph.add_plot(buy_plot)
        if stem is True:
            sell_plot = MeshStemPlot(color=[0, 0.45490, 0.62745, 1])
        else:
            sell_plot = SmoothLinePlot(color=[0, 0.45490, 0.62745, 1])
        points = []
        x = 0
        for point in sell_points:
            points.append((x, point))
            x += 1
        sell_plot.points = points
        self.graph.add_plot(sell_plot)
        self.show_graph_popup(title)

    def show_graph_popup(self, title):
        content = BoxLayout(orientation='vertical')
        content.add_widget(self.graph)
        content.add_widget(BoxLayout(size_hint=(1, 0.1)))
        button_layout = BoxLayout(size_hint=(1, 0.1))
        button = Button(text=self.PlungeApp.get_string('Close'), size_hint=(None, None), size=(250, 50))
        button_layout.add_widget(button)
        content.add_widget(button_layout)
        self.graph_popup = Popup(title=title, content=content, auto_dismiss=False)
        button.bind(on_press=self.close_graph_popup)
        self.graph_popup.open()
        padding = ((self.graph_popup.width - button.width) / 2)
        button_layout.padding = (padding, 0, padding, 0)
        return

    def close_graph_popup(self, instance, value=False):
        self.graph_popup.dismiss()
        self.graph = None
        return

    def show_info(self, title, data):
        content = BoxLayout(orientation='vertical')
        grid = GridLayout(cols=2, size_hint=(1, 0.8))
        for d in data:
            grid.add_widget(Label(text=self.PlungeApp.get_string(d) + ":", font_size=18, halign='right', markup=True))
            grid.add_widget(Label(text=str(data[d]), font_size=18, halign='left', markup=True))
        content.add_widget(grid)
        content.add_widget(BoxLayout(size_hint=(1, 0.1)))
        button_layout = BoxLayout(size_hint=(1, 0.1))
        button = Button(text=self.PlungeApp.get_string('Close'), size_hint=(1, None), height=50)
        button_layout.add_widget(button)
        content.add_widget(button_layout)
        self.info = Popup(title=title, content=content, auto_dismiss=False, size_hint=(None, None), size=(300, 400))
        button.bind(on_press=self.close_info)
        self.info.open()
        return

    def close_info(self, instance, value=False):
        self.info.dismiss()
        return