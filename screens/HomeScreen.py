from kivy.clock import Clock
import os
from platform import system
import subprocess
import signal
from Queue import Queue, Empty
from threading  import Thread
import sys
from decimal import Decimal

__author__ = 'woolly_sammoth'

from kivy.uix.screenmanager import Screen


class HomeScreen(Screen):

    def __init__(self, PlungeApp, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.PlungeApp = PlungeApp
        self.PlungeApp.logger.info("Building Home Page")
        self.max_layout = self.ids.max_layout.__self__
        self.min_layout = self.ids.min_layout.__self__
        self.start_button = self.ids.start_button.__self__
        self.log_output = self.ids.log_output.__self__
        self.running_label = self.ids.running_label.__self__
        self.pool_buy_side = self.ids.pool_buy_side.__self__
        self.pool_sell_side = self.ids.pool_sell_side.__self__
        self.pool_num_users = self.ids.pool_num_users.__self__
        self.pool_sampling = self.ids.pool_sampling.__self__
        self.exchange_spinner = self.ids.exchange_spinner.__self__
        self.currency_spinner = self.ids.currency_spinner.__self__
        self.exchange_rate = self.ids.exchange_rate.__self__
        self.exchange_fee = self.ids.exchange_fee.__self__
        self.exchange_target = self.ids.exchange_target.__self__
        self.exchange_balance = self.ids.exchange_balance.__self__
        self.exchange_efficiency = self.ids.exchange_efficiency.__self__
        self.exchange_missing = self.ids.exchange_missing.__self__
        self.exchange_rejects = self.ids.exchange_rejects.__self__
        self.exchange_last_error = self.ids.exchange_last_error.__self__
        self.personal_buy_side = self.ids.personal_buy_side.__self__
        self.personal_sell_side = self.ids.personal_sell_side.__self__
        self.personal_efficiency = self.ids.personal_efficiency.__self__
        self.personal_balance = self.ids.personal_balance.__self__
        self.min_efficiency = self.ids.min_efficiency.__self__
        self.min_balance = self.ids.min_balance.__self__

        self.pool_buy_liquidity = None
        self.pool_sell_liquidity = None
        self.num_users = None
        self.sampling = None

        self.stats = {}
        self.user = {}
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

    def get_pool_stats(self):
        # get the pool status
        self.PlungeApp.logger.info("Get the Pool Stats")
        status = dict(self.PlungeApp.utils.get("http://%s:%s/status" %
                                               (self.PlungeApp.config.get('server', 'host'),
                                                self.PlungeApp.config.get('server', 'port'))))
        
        if 'error' not in status:
            self.PlungeApp.logger.info("Server returned %s" % status)
            self.pool = {}
            self.pool['buy_liquidity'] = str(round(status['liquidity'][0], 4))
            self.pool['sell_liquidity'] = str(round(status['liquidity'][1], 4))
            self.pool['num_users'] = str(status['users'])
            self.pool['sampling'] = str(status['sampling'])
            self.PlungeApp.logger.info("Pool stats - %s" % str(self.pool))
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
            if self.primary_exchange in self.stats:
                if self.primary_currency in self.stats[self.primary_exchange]:
                    self.update_exchange_stats()
                else:
                    self.PlungeApp.logger.error("%s not found in exchange stats" % self.primary_currency)
            else:
                self.PlungeApp.logger.error("%s not found in exchange stats" % self.primary_exchange)
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
                self.user[exchange]['balance'] = "%.4f" % user['balance']
                self.user[exchange]['missing'] = str(user['missing'])
                self.user[exchange]['rejects'] = str(user['rejects'])
                for currency in self.PlungeApp.active_currencies:
                    if currency in user['units']:
                        self.user[exchange][currency] = {}
                        self.user[exchange][currency]['ask_orders'] = user['units'][currency]['ask']
                        self.user[exchange][currency]['bid_orders'] = user['units'][currency]['bid']
                        self.user[exchange][currency]['last_error'] = user['units'][currency]['last_error']
                        self.user[exchange][currency]['rejects'] = str(user['units'][currency]['rejects'])
                        self.user[exchange][currency]['missing'] = str(user['units'][currency]['missing'])
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
        self.pool_buy_side.text = self.pool['buy_liquidity']
        self.pool_sell_side.text = self.pool['sell_liquidity']
        self.pool_num_users.text = self.pool['num_users']
        self.pool_sampling.text = self.pool['sampling']

    def update_exchange_stats(self):
        self.PlungeApp.logger.info("Update Exchange stats")
        self.exchange_fee.text = self.stats[self.primary_exchange][self.primary_currency]['fee']
        self.exchange_rate.text = self.stats[self.primary_exchange][self.primary_currency]['rate']
        self.exchange_target.text = self.stats[self.primary_exchange][self.primary_currency]['target']

    def update_personal_stats(self):
        self.PlungeApp.logger.info("Update Personal stats")
        self.exchange_balance.text = self.user[self.primary_exchange]['balance']
        self.exchange_efficiency.text = "%s%%" % str(self.user[self.primary_exchange]['efficiency'] *100)
        self.exchange_missing.text = self.user[self.primary_exchange][self.primary_currency]['missing']
        self.exchange_rejects.text = self.user[self.primary_exchange][self.primary_currency]['rejects']
        self.exchange_last_error.text = self.user[self.primary_exchange][self.primary_currency]['last_error']
        # calculations
        # buy side liquidity
        buy_side = 0
        self.PlungeApp.logger.info("Calculating Buy Side Liquidity")
        for exchange in self.PlungeApp.active_exchanges:
            for currency in self.PlungeApp.active_currencies:
                if exchange in self.user:
                    if currency in self.user[exchange]:
                        for order in self.user[exchange][currency]['bid_orders']:
                            buy_side += order[1]
                    else:
                        self.PlungeApp.logger.error("%s not found in personal stats" % currency)
                else:
                    self.PlungeApp.logger.error("%s not found in personal stats" % exchange)
        # sell side liquidity
        sell_side = 0
        self.PlungeApp.logger.info("Calculating Sell Side Liquidity")
        for exchange in self.PlungeApp.active_exchanges:
            for currency in self.PlungeApp.active_currencies:
                if exchange in self.user:
                    if currency in self.user[exchange]:
                        for order in self.user[exchange][currency]['ask_orders']:
                            sell_side += order[1]
                    else:
                        self.PlungeApp.logger.error("%s not found in personal stats" % currency)
                else:
                    self.PlungeApp.logger.error("%s not found in personal stats" % exchange)
        # efficiency
        efficiency = 0
        self.PlungeApp.logger.info("Calculating Efficiency")
        for exchange in self.PlungeApp.active_exchanges:
            if exchange in self.user:
                efficiency += self.user[exchange]['efficiency']
            else:
                self.PlungeApp.logger.error("%s not found in personal stats" % exchange)
        efficiency = efficiency / len(self.PlungeApp.active_exchanges)
        # balance
        self.PlungeApp.logger.info("Calculating Balance")
        balance = 0
        for exchange in self.PlungeApp.active_exchanges:
            if exchange in self.user:
                balance += Decimal(self.user[exchange]['balance'])
            else:
                self.PlungeApp.logger.error("%s not found in personal stats" % exchange)

        self.personal_buy_side.text = str(round(buy_side, 4))
        self.personal_sell_side.text = str(round(sell_side, 4))
        self.personal_efficiency.text = "%s%%" % str(efficiency * 100)
        self.min_efficiency.text = "%s%%" % str(efficiency * 100)
        self.personal_balance.text = "%.4f" % balance
        self.min_balance.text = "%.4f" % balance

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