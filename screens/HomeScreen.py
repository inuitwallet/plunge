import calendar
from itertools import izip_longest
import json
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
import os
import time
from graph import Graph, MeshLinePlot, MeshStemPlot, SmoothLinePlot
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
import logging
from kivy.network.urlrequest import UrlRequest
from threading import Thread
import client.client

__author__ = 'woolly_sammoth'

from kivy.uix.screenmanager import Screen


class HeadingLabel(Label):
    pass


class SubHeadingLabel(Label):
    pass


class HomeScreen(Screen):

    def __init__(self, PlungeApp, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.PlungeApp = PlungeApp
        self.PlungeApp.logger.info("Home Page Init")
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
        self.exchange_balance_label = self.ids.exchange_balance.__self__
        self.exchange_ask_rate_label = self.ids.exchange_ask_rate.__self__
        self.exchange_bid_rate_label = self.ids.exchange_bid_rate.__self__
        self.exchange_efficiency_label = self.ids.exchange_efficiency.__self__
        self.personal_buy_side = self.ids.personal_buy_side.__self__
        self.personal_sell_side = self.ids.personal_sell_side.__self__
        self.personal_buy_side_rate = self.ids.personal_buy_side_rate.__self__
        self.personal_sell_side_rate = self.ids.personal_sell_side_rate.__self__
        self.personal_efficiency = self.ids.personal_efficiency.__self__
        self.personal_balance = self.ids.personal_balance.__self__
        self.min_liquidity = self.ids.min_liquidity.__self__
        self.min_rate = self.ids.min_rate.__self__
        self.min_efficiency = self.ids.min_efficiency.__self__
        self.min_balance = self.ids.min_balance.__self__

        self.PlungeApp.logger.debug("setting home page variables")

        self.getting_pool_stats = False
        self.getting_exchange_stats = False
        self.getting_personal_stats = False
        self.set_exchange_spinners()

        # set up variables
        self.primary_currency = None
        self.primary_exchange = None
        self.num_users = None
        self.sampling = None
        self.total_ask_liquidity = None
        self.total_bid_liquidity = None
        self.total_efficiency = None
        self.total_balance = None
        self.total_ask_rate = None
        self.total_bid_rate = None
        self.total_liquidity = None
        self.total_rate = None

        self.exchange_buy_side = {}
        self.exchange_sell_side = {}
        self.exchange_valid = {}
        for exchange in self.PlungeApp.active_exchanges:
            self.exchange_buy_side[exchange] = {}
            self.exchange_sell_side[exchange] = {}
            self.exchange_valid[exchange] = None

        self.client_logger = client.client.getlogger()
        log_handler = logging.StreamHandler(self.RedirectLogger(self.log_output))
        self.client_logger.addHandler(log_handler)

        # set up the dictionaries that hold the returned server data
        self.pool = {}
        self.stats = {}
        self.user = {}

        # set up the lists that hold the historical data for graphing
        self.pool_buy_liquidity = []
        self.pool_sell_liquidity = []
        self.pool_total_liquidity = []
        self.exchange_efficiency = {}
        self.exchange_balance = {}
        self.exchange_missing = {}
        self.exchange_rejects = {}
        self.exchange_buy_liquidity = {}
        self.exchange_sell_liquidity = {}
        self.exchange_total_liquidity = {}
        self.exchange_valid_submissions = {}
        self.exchange_ask_rate = {}
        self.exchange_bid_rate = {}
        self.total_buy_liquidity = []
        self.total_sell_liquidity = []
        self.total_liquidity_list = []
        self.total_efficiency_list = []
        self.total_balance_list = []
        self.total_ask_rate_list = []
        self.total_bid_rate_list = []

        # set up UI and start timers
        self.PlungeApp.logger.info("Setting refresh Period to %s" % self.PlungeApp.config.get('standard', 'period'))
        Clock.schedule_interval(self.get_stats, self.PlungeApp.config.getint('standard', 'period'))
        self.PlungeApp.logger.debug("finished homepage init")
        return

    def set_exchange_spinners(self):
        self.PlungeApp.logger.info("getting data for spinners")
        url = "http://%s:%s/exchanges" % (self.PlungeApp.config.get('server', 'host'),
                                          self.PlungeApp.config.get('server', 'port'))
        req = UrlRequest(url, self._set_exchange_spinners, self.exchange_spinner_error, self.exchange_spinner_error)

    def exchange_spinner_error(self, req, result):
        self.PlungeApp.logger.debug("get spinner values failed")
        self.PlungeApp.logger.warn("Spinner values failed. Returned %s" % req.resp_status)

    def _set_exchange_spinners(self, req, result):
        # see if any exchanges are enabled so that we can display the stats
        self.primary_exchange = ''
        self.primary_currency = ''
        self.PlungeApp.active_exchanges = []
        self.PlungeApp.logger.debug("set spinner text")
        for exchange in result:
            if exchange in self.PlungeApp.active_exchanges:
                continue
            self.PlungeApp.logger.debug("for %s" % exchange)
            self.PlungeApp.active_exchanges.append(exchange)
            if self.PlungeApp.get_string(exchange) == self.exchange_spinner.text:
                self.primary_exchange = exchange
        if self.primary_exchange != '':
            self.PlungeApp.logger.info("Set Primary Exchange to %s" % self.primary_exchange)
        else:
            self.PlungeApp.logger.debug("no primary exchange set")
            self.exchange_spinner.values = [self.PlungeApp.get_string(exchange) for
                                            exchange in self.PlungeApp.active_exchanges]
            self.primary_exchange = self.PlungeApp.active_exchanges[0]
            self.exchange_spinner.text = self.PlungeApp.get_string(self.primary_exchange)
            self.PlungeApp.logger.info("Set Primary Exchange to %s" % self.primary_exchange)
        self.PlungeApp.active_currencies = []
        self.PlungeApp.logger.debug("set currency spinner text")
        self.PlungeApp.logger.debug("%s" % str(result[self.primary_exchange]))
        for currency in result[self.primary_exchange]:
            if currency in self.PlungeApp.active_currencies:
                continue
            self.PlungeApp.logger.debug("set text for %s" % currency)
            self.PlungeApp.active_currencies.append(currency)
        self.currency_spinner.values = [currency.upper() for currency in self.PlungeApp.active_currencies]
        if self.primary_currency == '':
            self.primary_currency = self.PlungeApp.active_currencies[0].lower()
            self.PlungeApp.logger.info("Set Primary Currency to %s" % self.primary_currency)
            self.currency_spinner.text = self.primary_currency.upper()
        self.get_stats(0)

    def set_primary_currency(self):
        self.primary_currency = self.currency_spinner.text.lower()
        self.PlungeApp.logger.info("Set Primary Currency to %s" % self.primary_currency)
        self.get_stats(0)

    def update_lists(self, value, in_list):
        self.PlungeApp.logger.debug("update list with %s %s" % (str(value), str(type(value))))
        in_list.append(value)
        data_to_keep = self.PlungeApp.config.getint('standard', 'data')
        if data_to_keep > 0:
            while len(in_list) > data_to_keep:
                in_list.pop(0)

    def get_stats(self, dt):
        self.PlungeApp.logger.debug("build and start pool thread")
        pool = Thread(target=self.get_pool_stats, name='pool_thread')
        pool.start()
        self.PlungeApp.logger.debug("build and start exchange thread")
        exchange = Thread(target=self.get_exchange_stats, name='exchange_thread')
        exchange.start()
        self.PlungeApp.logger.debug("build and start personal thread")
        personal = Thread(target=self.get_personal_stats, name='personal_thread')
        personal.start()

    def get_pool_stats(self):
        # get the pool status
        self.PlungeApp.logger.debug("getting pool stats")
        if self.getting_pool_stats is True:
            self.PlungeApp.logger.debug("pool stats are already being fetched so ending")
            return
        self.getting_pool_stats = True
        self.PlungeApp.logger.info("Get the Pool Stats")
        url = 'http://%s:%s/status' % (self.PlungeApp.config.get('server', 'host'),
                                       self.PlungeApp.config.get('server', 'port'))
        req = UrlRequest(url, self.save_pool_stats, self.pool_stats_error, self.pool_stats_error)

    def pool_stats_error(self, req, result):
        self.PlungeApp.logger.warn('Pool stats failed. Returned %s' % req.resp_status)
        self.getting_pool_stats = False

    def save_pool_stats(self, req, result):
        self.PlungeApp.logger.info("Pool stats returned OK")
        self.pool = {}
        self.pool['buy_liquidity'] = result['liquidity'][0]
        self.pool['sell_liquidity'] = result['liquidity'][1]
        self.pool['num_users'] = result['users']
        self.pool['sampling'] = result['sampling']

        self.update_lists(self.pool['buy_liquidity'], self.pool_buy_liquidity)
        self.update_lists(self.pool['sell_liquidity'], self.pool_sell_liquidity)
        self.update_lists((self.pool['buy_liquidity'] + self.pool['sell_liquidity']), self.pool_total_liquidity)

        self.update_pool_stats()
        self.getting_pool_stats = False
        self.PlungeApp.logger.debug("getting pool stats finished.")

    def get_exchange_stats(self):
        # get the exchange status
        self.PlungeApp.logger.debug("getting exchange stats")
        if self.getting_exchange_stats is True:
            self.PlungeApp.logger.debug("exchange stats are already being fetched so ending")
            return
        self.getting_exchange_stats = True
        self.PlungeApp.logger.info("Get the Exchange Stats")
        url = "http://%s:%s/exchanges" % (self.PlungeApp.config.get('server', 'host'),
                                          self.PlungeApp.config.get('server', 'port'))
        req = UrlRequest(url, self.save_exchange_stats, self.exchange_stats_error, self.exchange_stats_error)

    def exchange_stats_error(self, req, result):
        self.PlungeApp.logger.warn('Exchange stats failed. Returned %s' % req.resp_status)
        self.getting_exchange_stats = False

    def save_exchange_stats(self, req, result):
        self.PlungeApp.logger.info("Exchange stats returned OK")
        self.stats = result
        self.getting_exchange_stats = False
        self.PlungeApp.logger.debug("getting exchange stats finished")

    def get_personal_stats(self):
        # get the individual status for each account
        self.PlungeApp.logger.debug("getting personal stats")
        if self.getting_personal_stats is True:
            self.PlungeApp.logger.debug("personal stats are already being fetched so ending")
            return
        self.getting_personal_stats = True
        self.saving_personal_stats = False
        self.user = {}
        self.PlungeApp.logger.info("Get the Personal Stats")
        with open('api_keys.json') as api_keys_file:
            try:
                api_keys = json.load(api_keys_file)
            except ValueError:
                api_keys = []
                self.PlungeApp.logger.debug("no api keys found")
        api_keys_file.close()
        if not self.PlungeApp.active_exchanges or not self.PlungeApp.active_currencies:
            self.PlungeApp.logger.debug("no active exchanges or active currencies found")
            self.getting_personal_stats = False
            return
        for self.personal_exchange in self.PlungeApp.active_exchanges:
            self.PlungeApp.logger.debug("set stats for %s" % self.personal_exchange)
            self.user[self.personal_exchange] = {'balance': 0, 'num_keys': 0, 'efficiency': 0}
            for currency in self.PlungeApp.active_currencies:
                self.user[self.personal_exchange][currency] = {'ask_liquidity': 0, 'bid_liquidity': 0, 'ask_rate': 0, 'bid_rate': 0}
            for set in api_keys:
                if set['exchange'] == self.personal_exchange:
                    self.public = set['public']
                    self.PlungeApp.logger.info("Get Personal Stats for %s - %s" % (self.personal_exchange, self.public))
                    url = "http://%s:%s/%s" % (self.PlungeApp.config.get('server', 'host'),
                                               self.PlungeApp.config.get('server', 'port'),
                                               self.public)
                    self.saving_personal_stats = True
                    req = UrlRequest(url, self.save_personal_stats, self.personal_stats_error,
                                     self.personal_stats_error)

                    while self.saving_personal_stats is True:
                        continue

                    if self.user[self.personal_exchange]['num_keys'] > 0:
                        self.user[self.personal_exchange]['efficiency'] /= \
                            float(self.user[self.personal_exchange]['num_keys'])

            # update the graph data lists
            self.PlungeApp.logger.debug("update personal graphs lists")
            self.ensure_lists(self.exchange_efficiency, self.personal_exchange)
            self.update_lists((self.user[self.personal_exchange]['efficiency'] * 100),
                              self.exchange_efficiency[self.personal_exchange])
            self.ensure_lists(self.exchange_balance, self.personal_exchange)
            self.update_lists(round(float(self.user[self.personal_exchange]['balance']), 4),
                              self.exchange_balance[self.personal_exchange])

        if self.primary_exchange in self.user:
            if self.primary_currency in self.user[self.primary_exchange]:
                self.update_personal_stats()
            else:
                self.PlungeApp.logger.warn("%s not found in personal stats" % self.primary_currency)
        else:
            self.PlungeApp.logger.warn("%s not found in personal stats" % self.primary_exchange)
        self.getting_personal_stats = False

    def personal_stats_error(self, req, result):
        self.PlungeApp.logger.warn('Personal stats failed for %s %s. Returned %s' % (self.personal_exchange,
                                                                             self.public, req.resp_status))
        self.saving_personal_stats = False

    def save_personal_stats(self, req, result):
        self.user[self.personal_exchange]['balance'] += result['balance']
        self.user[self.personal_exchange]['num_keys'] += 1
        self.user[self.personal_exchange]['efficiency'] += result['efficiency']
        self.PlungeApp.logger.debug("saving personal stats")
        if not self.PlungeApp.active_currencies:
            self.saving_personal_stats = False
            return
        self.PlungeApp.logger.info("Personal stats returned OK")
        for currency in self.PlungeApp.active_currencies:
            self.PlungeApp.logger.debug("saving stats for %s" % currency)
            if currency in result['units']:
                for order in result['units'][currency]['ask']:
                    self.user[self.personal_exchange][currency]['ask_liquidity'] += order['amount']
                for order in result['units'][currency]['bid']:
                    self.user[self.personal_exchange][currency]['bid_liquidity'] += order['amount']
                self.user[self.personal_exchange][currency]['ask_rate'] += result['units'][currency]['rate']['ask']
                self.user[self.personal_exchange][currency]['bid_rate'] += result['units'][currency]['rate']['bid']

                #  update the graph data lists
                self.ensure_lists(self.exchange_buy_liquidity, self.personal_exchange, currency)
                self.update_lists(self.user[self.personal_exchange][currency]['bid_liquidity'],
                                  self.exchange_buy_liquidity[self.personal_exchange][currency])

                self.ensure_lists(self.exchange_sell_liquidity, self.personal_exchange, currency)
                self.update_lists(self.user[self.personal_exchange][currency]['ask_liquidity'],
                                  self.exchange_sell_liquidity[self.personal_exchange][currency])

                self.ensure_lists(self.exchange_total_liquidity, self.personal_exchange, currency)
                self.update_lists((self.user[self.personal_exchange][currency]['ask_liquidity'] +
                                   self.user[self.personal_exchange][currency]['bid_liquidity']),
                                  self.exchange_total_liquidity[self.personal_exchange][currency])

                self.ensure_lists(self.exchange_ask_rate, self.personal_exchange, currency)
                self.update_lists(self.user[self.personal_exchange][currency]['ask_rate'],
                                  self.exchange_ask_rate[self.personal_exchange][currency])

                self.ensure_lists(self.exchange_bid_rate, self.personal_exchange, currency)
                self.update_lists(self.user[self.personal_exchange][currency]['bid_rate'],
                                  self.exchange_bid_rate[self.personal_exchange][currency])
            else:
                self.PlungeApp.logger.debug("%s not found in returned stats" % currency)
        self.saving_personal_stats = False

    @staticmethod
    def ensure_lists(list_name, exchange, currency=None):
        if exchange not in list_name:
            if currency is None:
                list_name[exchange] = []
                return
            else:
                list_name[exchange] = {}
        if currency is not None:
            if currency not in list_name[exchange]:
                list_name[exchange][currency] = []

    def update_pool_stats(self):
        self.PlungeApp.logger.info("Update Pool stats")
        self.pool_buy_side.text = "[ref='pool_buy_side']%.4f[/ref]" % self.pool['buy_liquidity']
        self.pool_sell_side.text = "[ref='pool_sell_side']%.4f[/ref]" % self.pool['sell_liquidity']

    def update_personal_stats(self):
        self.PlungeApp.logger.info("Update Personal stats")
        self.exchange_balance_label.text = "[ref='exchange_balance']%.8f[/ref]" % \
                                           self.user[self.primary_exchange]['balance']
        self.exchange_efficiency_label.text = "[ref='exchange_efficiency']%.2f%%[/ref]" % \
                                              (self.user[self.primary_exchange]['efficiency'] * 100)
        ask_rate = (self.user[self.primary_exchange][self.primary_currency]['ask_rate'] * 100)
        self.exchange_ask_rate_label.text = "[ref='exchange_missing']%.2f%%[/ref]" % ask_rate
        bid_rate = (self.user[self.primary_exchange][self.primary_currency]['bid_rate'] * 100)
        self.exchange_bid_rate_label.text = "[ref='exchange_rejects']%.2f%%[/ref]" % bid_rate

        self.calculations()

        self.exchange_buy_side_label.text = "[ref='exchange_buy_side']%.4f[/ref]" % \
                                            self.user[self.primary_exchange][self.primary_currency]['bid_liquidity']
        self.exchange_sell_side_label.text = "[ref='exchange_sell_side']%.4f[/ref]" % \
                                             self.user[self.primary_exchange][self.primary_currency]['ask_liquidity']
        self.personal_buy_side.text = "[ref='total_buy_side']%.4f[/ref]" % \
                                      self.total_bid_liquidity
        self.personal_buy_side_rate.text = "[ref='total_buy_side_rate']%.2f%%[/ref]" % (self.total_bid_rate * 100)
        self.personal_sell_side.text = "[ref='total_sell_side']%.4f[/ref]" % \
                                       self.total_ask_liquidity
        self.personal_sell_side_rate.text = "[ref='total_sell_side_rate']%.2f%%[/ref]" % (self.total_ask_rate * 100)
        self.personal_efficiency.text = "[ref='total_efficiency']%.2f%%[/ref]" % \
                                        (self.total_efficiency * 100)
        self.min_efficiency.text = "%.2f%%" % \
                                   (self.total_efficiency * 100)
        self.personal_balance.text = "[ref='total_balance']%.8f[/ref]" % \
                                     self.total_balance
        self.min_balance.text = "%.4f" %\
                                self.total_balance
        self.min_liquidity.text = "%.4f" % self.total_liquidity
        self.min_rate.text = "%.2f%%" % (self.total_rate * 100)

    def calculations(self):
        # total buy side liquidity
        self.total_ask_liquidity = 0
        self.total_bid_liquidity = 0
        self.total_ask_rate = 0
        ask_rate_sum = 0
        self.total_bid_rate = 0
        bid_rate_sum = 0
        self.total_efficiency = 0
        self.total_balance = 0
        self.total_liquidity = 0
        self.total_rate = 0
        self.PlungeApp.logger.info("Calculations")

        num_exchanges = 0

        for exchange in self.PlungeApp.active_exchanges:
            if exchange not in self.user:
                continue
            num_exchanges += 1
            self.total_efficiency += self.user[exchange]['efficiency']
            self.total_balance += self.user[exchange]['balance']
            for currency in self.PlungeApp.active_currencies:
                if currency not in self.user[exchange]:
                    continue
                self.total_ask_liquidity += self.user[exchange][currency]['ask_liquidity']
                self.total_bid_liquidity += self.user[exchange][currency]['bid_liquidity']
                ask_rate_sum += (self.user[exchange][currency]['ask_liquidity'] * self.user[exchange][currency]['ask_rate'])
                bid_rate_sum += (self.user[exchange][currency]['bid_liquidity'] * self.user[exchange][currency]['bid_rate'])

            # add exchange level lists


        self.total_efficiency /= num_exchanges

        self.total_ask_rate = (ask_rate_sum / self.total_ask_liquidity) if ask_rate_sum > 0 else 0
        self.total_bid_rate = (bid_rate_sum / self.total_bid_liquidity) if bid_rate_sum > 0 else 0
        self.total_liquidity = self.total_ask_liquidity + self.total_bid_liquidity
        total_rate_sum = ask_rate_sum + bid_rate_sum
        self.total_rate = (total_rate_sum / self.total_liquidity) if total_rate_sum > 0 else 0

        # update the total graphing lists
        self.update_lists(self.total_bid_liquidity, self.total_buy_liquidity)
        self.update_lists(self.total_ask_liquidity, self.total_sell_liquidity)
        self.update_lists(self.total_ask_rate, self.total_ask_rate_list)
        self.update_lists(self.total_bid_rate, self.total_bid_rate_list)
        self.update_lists(self.total_liquidity, self.total_liquidity_list)
        self.update_lists((self.total_efficiency * 100), self.total_efficiency_list)
        self.update_lists(round(float(self.total_balance), 4), self.total_balance_list)
        self.PlungeApp.logger.info("Calculations Finished")

    def toggle_client(self):
        text = self.start_button.text
        if text == "Start":
            self.PlungeApp.logger.info("Starting client")
            self.start_client()
        else:
            self.PlungeApp.logger.info("Stopping client")
            self.stop_client()

    def start_client(self):
        host = self.PlungeApp.config.get('server', 'host')
        port = self.PlungeApp.config.get('server', 'port')
        self.client = client.client.Client('%s:%s' % (host, port))
        with open('user_data.json') as user_file:
            user_data = json.load(user_file)
        user_file.close()
        num_rows = 0
        for exchange in user_data:
            if exchange not in self.PlungeApp.active_exchanges:
                self.PlungeApp.logger.info("%s not found in active exchanges" % exchange)
                continue
            for d in user_data[exchange]:
                set = self.client.set(str(d['public']), str(d['secret']), str(d['address']), str(exchange),
                                      str(d['unit']), (float(d['bid']) / 100), (float(d['ask']) / 100), str(d['bot']))
                self.PlungeApp.logger.info("added data row to client - %s %s %s %s %.8f/%.8f %s" %
                                           (exchange, str(d['public']), str(d['address']), str(d['unit']),
                                            (float(d['bid']) / 100), (float(d['ask']) / 100), str(d['bot'])))
                num_rows += 1
                if set is not True:
                    self.PlungeApp.show_popup(self.PlungeApp.get_string("Popup_Error"),
                                              self.PlungeApp.get_string("Client_Run_Error"))
                    return
        if num_rows == 0:
            self.PlungeApp.show_popup(self.PlungeApp.get_string("Popup_Error"),
                                      self.PlungeApp.get_string("Client_Run_No_Data"))
            self.PlungeApp.logger.warn("no data rows added to client")
            return
        self.client.start()
        self.PlungeApp.client_running = True
        self.running_label.color = (0, 1, 0.28235, 1)
        self.running_label.text = self.PlungeApp.get_string("Client_Started")
        self.PlungeApp.logger.info("Client Started")
        self.start_button.text = self.PlungeApp.get_string('Stop')

    class RedirectLogger(object):

        def __init__(self, text_display):
            self.out = text_display

        def write(self, string):
            self.out.text = self.out.text + string

    def stop_client(self):
        self.client.stop()
        self.client.join()
        self.log_output.text += 'Stopped!\n'
        self.PlungeApp.client_running = False
        self.running_label.color = (0.93725, 0.21176, 0.07843, 1)
        self.running_label.text = self.PlungeApp.get_string("Client_Stopped")
        self.start_button.text = self.PlungeApp.get_string('Start')
        self.PlungeApp.logger.info("Client Stopped")

    def draw_chart(self, title, y_label, points):
        y_min = min(points) if len(points) > 0 else 0
        y_max = max(points) if len(points) > 0 else 100
        y_diff = (y_max - y_min)
        y_major = float(y_diff) / float(10) if y_diff > 0 else 1
        period = self.PlungeApp.config.getint('standard', 'period')
        minute = (float(period) / float(60))
        x_major = float(30) / float(minute)
        x_minor = float(5) / float(minute)
        x_max = 1 if len(points) < 2 else (len(points) - 1)
        self.graph = Graph(ylabel=y_label, x_ticks_minor=x_minor, x_ticks_major=x_major, y_ticks_major=y_major,
                           y_grid_label=True, x_grid_label=True, padding=5, x_grid=True, y_grid=True, xmin=0,
                           xmax=x_max, ymin=(y_min-10), ymax=(y_max+10))
        tuple_points = []
        x = 0
        for point in points:
            tuple_points.append((x, point))
            x += 1
        if self.PlungeApp.config.getint('standard', 'smooth_line') == 1:
            plot = SmoothLinePlot(color=[0.93725, 0.21176, 0.07843, 1])
        else:
            plot = MeshLinePlot(color=[0.93725, 0.21176, 0.07843, 1])
        plot.points = tuple_points
        self.graph.add_plot(plot)
        self.show_graph_popup(title)

    def draw_liquidity_chart(self, title, buy_points, sell_points, stem=False):
        y_min = min(buy_points, sell_points)
        y_max = max(buy_points, sell_points)
        y_diff = (max(y_max) - min(y_min))
        y_major = float(y_diff) / float(10) if y_diff > 0 else 1
        period = self.PlungeApp.config.getint('standard', 'period')
        minute = (float(period) / float(60))
        x_major = float(30) / float(minute)
        x_minor = float(5) / float(minute)
        x_max = 1 if len(sell_points) < 2 else (len(sell_points) - 1)
        self.graph = Graph(ylabel='NBT', x_ticks_minor=x_minor, x_ticks_major=x_major, y_ticks_major=y_major,
                           y_grid_label=True, x_grid_label=True, padding=5, x_grid=True, y_grid=True, xmin=0,
                           xmax=x_max, ymin=(min(y_min)-50), ymax=(max(y_max)+50))
        if self.PlungeApp.config.getint('standard', 'smooth_line') == 1:
            buy_plot = SmoothLinePlot(color=[0, 0.65490, 0.82745, 1])
        else:
            buy_plot = MeshLinePlot(color=[0, 0.65490, 0.82745, 1])
        points = []
        x = 0
        for point in buy_points:
            points.append((x, point))
            x += 1
        buy_plot.points = points
        self.graph.add_plot(buy_plot)
        if self.PlungeApp.config.getint('standard', 'smooth_line') == 1:
            sell_plot = SmoothLinePlot(color=[1, 0.72157, 0, 1])
        else:
            sell_plot = MeshLinePlot(color=[1, 0.72157, 0, 1])
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
        button_layout = BoxLayout(size_hint=(1, 0.1), spacing=150)
        button = Button(text=self.PlungeApp.get_string('Close'), size_hint=(None, None), size=(250, 50))
        button_layout.add_widget(button)
        capture_button = Button(text=self.PlungeApp.get_string('Capture'), size_hint=(None, None), size=(250, 50))
        button_layout.add_widget(capture_button)
        content.add_widget(button_layout)
        self.graph_popup = Popup(title=title, content=content, auto_dismiss=False, size_hint=(.9, .9))
        button.bind(on_press=self.close_graph_popup)
        capture_button.bind(on_press=self.capture_graph)
        self.graph_popup.open()
        padding = ((self.graph_popup.width - ((button.width + capture_button.width) + 150)) / 2)
        button_layout.padding = (padding, 0, padding, 0)
        return

    def capture_graph(self, instance):
        if not os.path.isdir('saved_charts'):
            os.makedirs('saved_charts')
        file_name = 'saved_charts/%s.png' % calendar.timegm(time.gmtime())
        self.graph.export_to_png(file_name)
        self.PlungeApp.show_popup(self.PlungeApp.get_string("Graph_Saved"),
                                  self.PlungeApp.get_string("Graph_Saved_Text") % file_name)

    def close_graph_popup(self, instance, value=False):
        self.graph_popup.dismiss()
        self.graph = None
        return

    def show_pool_info(self):
        data = [('Total_Liquidity', (self.pool['buy_liquidity'] + self.pool['sell_liquidity'])),
                ('Num_Users', self.pool['num_users']),
                ('Sampling', self.pool['sampling'])]
        content = BoxLayout(orientation='vertical')
        grid = GridLayout(cols=2, size_hint=(1, 0.8))
        for d in data:
            grid.add_widget(Label(text=self.PlungeApp.get_string(d[0]) + ":", font_size=18,
                                  halign='right', markup=True))
            grid.add_widget(Label(text=str(d[1]), font_size=18, halign='left', markup=True))
        content.add_widget(grid)
        content.add_widget(BoxLayout(size_hint=(1, 0.1)))
        button_layout = BoxLayout(size_hint=(1, 0.1))
        button = Button(text=self.PlungeApp.get_string('Close'), size_hint=(1, None), height=50)
        button_layout.add_widget(button)
        content.add_widget(button_layout)
        self.info = Popup(title=self.PlungeApp.get_string('Pool_Info'), content=content, auto_dismiss=False,
                          size_hint=(None, None), size=(350, 300))
        button.bind(on_press=self.close_info)
        self.info.open()
        return

    def show_exchange_info(self):
        content = BoxLayout(orientation='vertical')
        scroll_view = ScrollView(do_scroll_x=False)
        top_grid = GridLayout(cols=2, spacing='5dp', size_hint=(1, 0.4))
        data = [(self.PlungeApp.get_string('Target'), self.PlungeApp.get_string('No_Data')),
                (self.PlungeApp.get_string('Maximal_Rate'), self.PlungeApp.get_string('No_Data')),
                (self.PlungeApp.get_string('Low'), self.PlungeApp.get_string('No_Data')),
                (self.PlungeApp.get_string('High'), self.PlungeApp.get_string('No_Data'))]
        if self.primary_exchange in self.stats:
            if self.primary_currency in self.stats[self.primary_exchange]:
                stats = self.stats[self.primary_exchange][self.primary_currency]
                data = [(self.PlungeApp.get_string('Target'), '%.2f / %.2f' % (stats['ask']['target'], stats['bid']['target'])),
                        (self.PlungeApp.get_string('Maximal_Rate'), '%.4f / %.4f' % (stats['ask']['rate'], stats['bid']['rate'])),
                        (self.PlungeApp.get_string('Low'), '%.4f / %.4f' % (stats['ask']['low'], stats['bid']['low'])),
                        (self.PlungeApp.get_string('High'), '%.4f / %.4f' % (stats['ask']['high'], stats['bid']['high']))]
        for d in data:
            top_grid.add_widget(Label(text=str(d[0]), font_size=18, halign='right', markup=True))
            top_grid.add_widget(Label(text=str(d[1]), font_size=18, halign='left', markup=True))
        bottom_layout = GridLayout(cols=1, spacing='5dp', size_hint_x=1, size_hint_y=None,
                                   row_default_height='30dp', row_force_default=True)
        bottom_layout.bind(minimum_height=bottom_layout.setter('height'))
        if self.primary_exchange in self.stats:
            if self.primary_currency in self.stats[self.primary_exchange]:
                stats = self.stats[self.primary_exchange][self.primary_currency]
                for x in range(1, (len(stats['ask']['orders'])+1)):
                    bottom_layout.add_widget(HeadingLabel(text='%s %d' % (self.PlungeApp.get_string('Order_Group'), x),
                                                          font_size=22))
                    side_layout = BoxLayout(orientation='horizontal')
                    side_layout.add_widget(HeadingLabel(text=self.PlungeApp.get_string('Ask'), font_size=20))
                    side_layout.add_widget(HeadingLabel(text=self.PlungeApp.get_string('Bid'), font_size=20))
                    bottom_layout.add_widget(side_layout)
                    column_layout = BoxLayout(orientation='horizontal')
                    column_layout.add_widget(SubHeadingLabel(text=self.PlungeApp.get_string('Amount'), font_size=18))
                    column_layout.add_widget(SubHeadingLabel(text=self.PlungeApp.get_string('Rate'), font_size=18))
                    column_layout.add_widget(SubHeadingLabel(text=self.PlungeApp.get_string('Amount'), font_size=18))
                    column_layout.add_widget(SubHeadingLabel(text=self.PlungeApp.get_string('Rate'), font_size=18))
                    bottom_layout.add_widget(column_layout)
                    orders = izip_longest(stats['ask']['orders'][x-1], stats['bid']['orders'][x-1],
                                          fillvalue={'amount': 0, 'cost': 0})
                    for order in orders:
                        order_grid = BoxLayout(orientation='horizontal')
                        order_grid.add_widget(Label(text='%.8f' % order[0]['amount'] if order[0]['amount'] > 0 else '%d' % order[0]['amount'], font_size=16))
                        order_grid.add_widget(Label(text='%.4f' % order[0]['cost'] if order[0]['cost'] > 0 else '%d' % order[0]['cost'], font_size=16))
                        order_grid.add_widget(Label(text='%.8f' % order[1]['amount'] if order[1]['amount'] > 0 else '%d' % order[1]['amount'], font_size=16))
                        order_grid.add_widget(Label(text='%.4f' % order[1]['cost'] if order[1]['cost'] > 0 else '%d' % order[1]['cost'], font_size=16))
                        bottom_layout.add_widget(order_grid)
        scroll_view.add_widget(bottom_layout)
        content.add_widget(top_grid)
        content.add_widget(BoxLayout(size_hint=(1, 0.05)))
        content.add_widget(scroll_view)
        content.add_widget(BoxLayout(size_hint=(1, 0.1)))
        button_layout = BoxLayout(size_hint=(1, 0.1))
        button = Button(text=self.PlungeApp.get_string('Close'), size_hint=(1, None), height=50)
        button_layout.add_widget(button)
        content.add_widget(button_layout)
        title = "%s %s ( ask / bid )" % (self.PlungeApp.get_string(self.primary_exchange), self.PlungeApp.get_string("Info"))
        self.info = Popup(title=title, content=content, auto_dismiss=False, size_hint=(.9, .9))
        button.bind(on_press=self.close_info)
        self.info.open()
        return

    def close_info(self, instance, value=False):
        self.info.dismiss()
        return