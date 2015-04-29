import json
from kivy.app import App
from kivy.config import ConfigParser
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.metrics import dp
from kivy.uix.settings import SettingString, SettingSpacer, SettingNumeric, InterfaceWithTabbedPanel, Settings
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.network.urlrequest import UrlRequest
import time
import utils
import logging

__author__ = 'woolly_sammoth'


class InterfaceWithCloseButton(InterfaceWithTabbedPanel):

    def add_panel(self, panel, name, uid):
        scrollview = ScrollView()
        scrollview.add_widget(panel)
        self.tabbedpanel.default_tab_text = 'Plunge Configuration'
        self.tabbedpanel.default_tab_content = scrollview
        self.tabbedpanel.tab_width = 0.000001


class SettingsWithCloseButton(Settings):
    def __init__(self, *args, **kwargs):
        self.interface_cls = InterfaceWithCloseButton
        super(SettingsWithCloseButton, self).__init__(*args, **kwargs)


class SettingStringFocus(SettingString):
    """
    Overrides the SettingString class to automatically give keyboard focus to the input field of the pop up
    """

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
    """
    Overrides the SettingNumeric class to automatically give keyboard focus to the input field of the pop up
    """

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


class SettingStringExchange(SettingString):
    """
    Overrides the SettingString class to provide a customised popup suitable for exchange data input
    """

    num_rows = 0
    exchange = None
    chosen_api_key_pair = None
    ask_max = None
    bid_max = None
    utils = utils.utils('')
    keys_button = []
    address = []
    unit = []
    rates = []
    bot = []
    logger = logging.getLogger('Plunge')
    currencies = ['btc', 'ltc', 'eur', 'usd', 'ppc']
    bots = ['nubot', 'pybot', 'none']

    def on_panel(self, instance, value):
        if value is None:
            return
        self.bind(on_release=self._create_popup)

    def _dismiss(self, *largs):
        if self.textinput:
            self.textinput.focus = False
        if self.popup:
            self.popup.dismiss()
        self.popup = None
        self.num_rows = 0
        self.keys_button = []
        self.address = []
        self.unit = []
        self.rates = []
        self.bot = []

    def _validate(self, instance):
        with open('user_data.json', 'a+') as user_data:
            try:
                saved_data = json.load(user_data)
            except ValueError:
                saved_data = {}
        user_data.close()
        saved_data[self.exchange] = []
        good_records = 0
        content = TextInput(multiline=True, text='Saving...', background_color=[0.13725, 0.12157, 0.12549, 0],
                            foreground_color=[1, 1, 1, 1])
        popup = Popup(title='Saving Data for %s' % self.exchange, content=content,
                      size_hint=(None, None), size=(300, 500))
        popup.open()
        for x in range(0, self.num_rows, 1):
            self.logger.info("saving row %d for %s" % (x+1, self.exchange))
            content.text = '%s\nSaving row %d' % (content.text, x+1)
            this_row = {}
            public, secret = self.get_keys(self.keys_button[x].text)
            if public is None or secret is None:
                self.logger.warn("API Keys not set correctly")
                content.text = '%s\n=> API Keys not set correctly' % content.text
                continue
            this_row['public'] = public
            this_row['secret'] = secret
            this_row['address'] = self.address[x].text
            if not self.utils.check_checksum(this_row['address']) or not this_row['address'][:1] == 'B':
                self.logger.warn("Invalid payout address %s" % this_row['address'])
                content.text = '%s\n=> Invalid payout address' % content.text
                continue
            this_row['unit'] = self.unit[x].text
            rates = self.rates[x].text
            if "|" not in rates:
                self.logger.warn("no rates set")
                content.text = '%s\n=> No rates set' % content.text
                continue
            rate = rates.split(' | ')
            this_row['ask'] = rate[0]
            this_row['bid'] = rate[1]
            if this_row['ask'] == 0.00:
                this_row['ask'] = self.ask_max
            if this_row['bid'] == 0.00:
                this_row['bid'] = self.bid_max
            this_row['bot'] = self.bot[x].text
            if this_row in saved_data[self.exchange]:
                self.logger.warn("data already exists")
                content.text = '%s\n=> Data already exists' % content.text
                continue
            saved_data[self.exchange].append(this_row)
            good_records += 1
            content.text = '%s\nRow %d saved' % (content.text, x+1)
            self.logger.info(str(this_row))
        with open('user_data.json', 'w') as user_data:
            user_data.write(json.dumps(saved_data))
        user_data.close()
        content.text = '%s\nData Saved' % content.text
        self._dismiss()
        value = str(good_records)
        self.value = value

    def _create_popup(self, instance):
        """
        Create the main Exchange popup to which new rows can be added
        :param instance:
        :return:
        """
        self.exchange = self.key
        main_layout = BoxLayout(orientation='vertical', spacing='5dp')
        scroll_view = ScrollView(do_scroll_x=False)
        header = GridLayout(cols=5, spacing='5dp', row_default_height='50dp', row_force_default=True,
                            size_hint_y=None, height='50dp')
        header.add_widget(Label(text='API Keys', valign='top', size_hint_x=0.2))
        header.add_widget(Label(text='Payout Address (valid NBT)', valign='top', size_hint_x=0.4))
        header.add_widget(Label(text='Unit', valign='top', size_hint_x=0.1))
        header.add_widget(Label(text='Minimum interest rates', valign='top', size_hint_x=0.2))
        header.add_widget(Label(text='Bot', valign='top', size_hint_x=0.1))
        self.content = GridLayout(cols=5, spacing='5dp', row_default_height='50dp', row_force_default=True,
                                  size_hint_x=1, size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        main_layout.add_widget(header)
        scroll_view.add_widget(self.content)
        main_layout.add_widget(scroll_view)
        self.popup = popup = Popup(
            title=self.title, content=main_layout)

        # construct the content, widget are used as a spacer
        main_layout.add_widget(SettingSpacer())

        # buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height='50dp', spacing='5dp')
        btn = Button(text='Ok')
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel')
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        btn = Button(text='Add Row')
        btn.bind(on_release=self.add_row)
        btnlayout.add_widget(btn)
        main_layout.add_widget(btnlayout)

        self.load_data()

        # all done, open the popup !
        popup.open()

    def load_data(self):
        with open('user_data.json', 'a+') as data_file:
            try:
                data = json.load(data_file)
            except ValueError:
                data = {}
        data_file.close()
        if self.exchange not in data:
            self.add_row(None)
            return
        if len(data[self.exchange]) == 0:
            self.add_row(None)
            return
        for datum in data[self.exchange]:
            self.add_row(datum)

    def add_row(self, instance):
        """
        Add a row to the main exchange screen
        :param instance:
        :return:
        """
        self.num_rows += 1
        keys_button = Button(text='Set Keys', size_hint_x=0.2, id='%d' % self.num_rows)
        keys_button.bind(on_release=self.enter_keys)
        self.content.add_widget(keys_button)
        self.keys_button.append(keys_button)
        address = TextInput(size_hint_x=0.4, padding=[6, 10, 6, 10],
                            multiline=False, font_size=18, id='%d' % self.num_rows)
        address.bind(text=self.check_address)
        self.content.add_widget(address)
        self.address.append(address)
        unit = Spinner(values=self.currencies, text=self.currencies[0], size_hint_x=0.1, id='%d' % self.num_rows)
        self.selected_unit = self.currencies[0]
        unit.bind(text=self.set_unit)
        self.content.add_widget(unit)
        self.unit.append(unit)
        rates = Button(text='Set Rates', size_hint_x=0.2, id='%d' % self.num_rows)
        rates.bind(on_release=self.enter_rates)
        self.content.add_widget(rates)
        self.rates.append(rates)
        bot = Spinner(values=self.bots, text=self.bots[0], size_hint_x=0.1, id='%d' % self.num_rows)
        self.selected_bot = self.bots[0]
        bot.bind(text=self.set_bot)
        self.content.add_widget(bot)
        self.bot.append(bot)

        if isinstance(instance, dict):
            keys_button.text = instance['public'][:8] + ' / ' + instance['secret'][:8]
            address.text = instance['address']
            unit.text = instance['unit']
            rates.text = instance['ask'] + ' | ' + instance['bid']
            bot.text = instance['bot']

    def enter_keys(self, instance):
        """
        Show a pop-up in which previously entered api keys can be selected from a drop down
        There are edit and add buttons on the bottom which fire other methods
        :param instance:
        :return:
        """
        self.calling_keys_button = instance
        content = BoxLayout(orientation='vertical', spacing=10)
        top = BoxLayout(orientation='vertical', size_hint=(1, 0.7))
        top.add_widget(Label(text='API Key Pair', size_hint=(1, None), height='70dp'))
        self.api_key_spinner = Spinner(size_hint=(1, None), height='40dp')
        top.add_widget(self.api_key_spinner)
        self.api_key_spinner.bind(text=self.enable_edit)
        top.add_widget(BoxLayout())
        btnlayout = BoxLayout(spacing='5dp', size_hint=(1, 0.15))
        btn = Button(text='Ok', size_hint_y=None, height='50dp')
        btn.bind(on_release=self.close_api_keys_popup)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel', size_hint_y=None, height='50dp')
        btn.bind(on_release=self.close_api_keys_popup)
        btnlayout.add_widget(btn)
        self.edit_keys_button = Button(text='Edit Keys', size_hint_y=None, height='50dp', disabled=True)
        self.edit_keys_button.bind(on_release=self.edit_keys)
        btnlayout.add_widget(self.edit_keys_button)
        self.add_keys_button = Button(text='Add Keys', size_hint_y=None, height='50dp')
        self.add_keys_button.bind(on_release=self.add_keys)
        btnlayout.add_widget(self.add_keys_button)
        content.add_widget(top)
        content.add_widget(SettingSpacer())
        content.add_widget(btnlayout)
        popup_width = min(0.95 * Window.width, dp(500))
        self.enter_keys_popup = Popup(title='API Keys', content=content, auto_dismiss=False,
                                      size_hint=(None, None), size=(popup_width, '250dp'))
        self.update_api_spinners()
        if instance.text != 'Set Keys':
            self.api_key_spinner.text = instance.text
        self.enter_keys_popup.open()

    def enable_edit(self, instance, value):
        """
        The Edit button on the 'enter_api_keys' popup starts disabled.
        It is only enabled when a selection is made in the spinner
        :param instance:
        :param value:
        :return:
        """
        if value == '':
            self.edit_keys_button.disabled = True
        else:
            self.edit_keys_button.disabled = False
            self.edit_keys_button.id = value
            self.chosen_api_key_pair = value

    def edit_keys(self, instance):
        """
        Simply shows the add_keys popup with edit mode enabled
        :param instance:
        :return:
        """
        self.add_keys(instance, True)

    def add_keys(self, instance, edit=False):
        """
        Show a different pop-up into which api_keys can be entered.
        In edit mode the fields are pre-populated and a delete button is shown
        :param instance:
        :param edit:
        :return:
        """
        content = BoxLayout(orientation='vertical', spacing=10)
        grid = GridLayout(cols=2, spacing=10, size_hint=(1, 0.85))
        grid.add_widget(Label(text='Public', size_hint_x=None, width='100dp'))
        self.add_public_key = TextInput(size_hint=(1, None), height='40dp')
        self.add_public_key.bind(text=self.tab_switch)
        grid.add_widget(self.add_public_key)
        grid.add_widget(Label(text='Secret', size_hint_x=None, width='100dp'))
        self.add_secret_key = TextInput(size_hint=(1, None), height='40dp')
        self.add_secret_key.bind(text=self.tab_switch)
        grid.add_widget(self.add_secret_key)
        btnlayout = BoxLayout(spacing='5dp', size_hint=(1, 0.15))
        ok_btn = Button(text='Ok', size_hint_y=None, height='50dp')
        ok_btn.bind(on_release=self.save_api_keys)
        btnlayout.add_widget(ok_btn)
        btn = Button(text='Cancel', size_hint_y=None, height='50dp')
        btn.bind(on_release=self.save_api_keys)
        btnlayout.add_widget(btn)
        self.edit_public, self.edit_secret = None, None
        if edit is True:
            self.edit_public, self.edit_secret = self.get_keys(instance.id)
            if self.edit_public is None and self.edit_secret is None:
                return
            self.add_public_key.text = self.edit_public
            self.add_secret_key.text = self.edit_secret
            btn = Button(text='Delete', size_hint_y=None, height='50dp')
            btn.bind(on_release=self.delete_api_keys)
            btnlayout.add_widget(btn)

        content.add_widget(SettingSpacer())
        content.add_widget(grid)
        content.add_widget(btnlayout)
        self.add_keys_popup = Popup(title='Add API Keys', content=content, auto_dismiss=False,
                                    size_hint=(1, None), height='250dp')
        self.add_keys_popup.open()
        self.add_public_key.focus = True

    def tab_switch(self, instance, value):
        """
        tab switches from public to secret and back
        :return:
        """
        if '\t' not in value:
            return
        instance.text = value.replace('\t', '')
        if instance == self.add_public_key:
            self.add_secret_key.focus = True
        else:
            self.add_public_key.focus = True



    def update_api_spinners(self):
        """
        Populate the api_key selection spinner on the 'enter_api_keys' popup
        :return:
        """
        api_keys = self.fetch_api_keys_from_file()
        self.api_key_spinner.values = []
        self.api_key_spinner.text = ''
        for key_set in api_keys:
            if key_set['exchange'] != self.exchange:
                continue
            self.api_key_spinner.values.append(key_set['public'][:8] + ' / ' + key_set['secret'][:8])
        if self.chosen_api_key_pair is not None:
            self.api_key_spinner.text = self.chosen_api_key_pair

    def get_keys(self, keys):
        """
        When supplied truncated keys (as shown in the selection spinner)
        Get the full keys from the data file, ready for editting or saving
        :param keys:
        :return:
        """
        public = None
        secret = None
        if keys == 'Set Keys':
            return public, secret
        keys = keys.split(' / ')
        pub_key = keys[0]
        sec_key = keys[1]
        api_keys = self.fetch_api_keys_from_file()
        for key_set in api_keys:
            if key_set['exchange'] == self.exchange and key_set['public'][:8] == pub_key and key_set['secret'][:8] == sec_key:
                public = key_set['public']
                secret = key_set['secret']
        return public, secret

    def close_api_keys_popup(self, instance):
        """
        close the "enter_api_keys" popup.
        Cancel has no effect.
        OK saves the api key selection in te main data file
        :param instance:
        :return:
        """
        if instance.text == "Ok" and self.api_key_spinner.text != '':
            self.calling_keys_button.text = self.chosen_api_key_pair
        self.chosen_api_key_pair = None
        self.enter_keys_popup.dismiss()

    def save_api_keys(self, instance):
        """
        Save the Api Keys entered into the 'add_api_keys' popup
        These are saved to their own file for separate parsing
        :param instance:
        :return:
        """
        if instance.text == "Cancel" or self.add_public_key.text == "" or self.add_secret_key.text == "":
            self.add_keys_popup.dismiss()
            return
        api_keys = self.fetch_api_keys_from_file()
        if self.edit_public is not None and self.edit_secret is not None:
            for key_set in api_keys:
                if key_set['exchange'] == self.exchange and key_set['public'] == self.edit_public and key_set['secret'] == self.edit_secret:
                    key_set['public'] = self.add_public_key.text
                    key_set['secret'] = self.add_secret_key.text
        else:
            this_keys = {'exchange': self.exchange,
                         'public': self.add_public_key.text,
                         'secret': self.add_secret_key.text}
            for key_set in api_keys:
                if key_set == this_keys:
                    return

            api_keys.append(this_keys)

        self.save_api_keys_to_file(api_keys)

        self.chosen_api_key_pair = self.add_public_key.text[:8] + ' / ' + self.add_secret_key.text[:8]
        self.update_api_spinners()
        self.add_keys_popup.dismiss()

    def delete_api_keys(self, instance):
        """
        remove the chosen api key selection from the saved list
        :param instance:
        :return:
        """
        with open('api_keys.json', 'r') as api_keys_file:
            try:
                api_keys = json.load(api_keys_file)
            except ValueError:
                api_keys = []
            api_keys_file.close()
        if self.edit_public is not None and self.edit_secret is not None:
            new_api_keys = []
            for key_set in api_keys:
                if key_set['exchange'] == self.exchange and key_set['public'] == self.edit_public and key_set['secret'] == self.edit_secret:
                    continue
                new_api_keys.append(key_set)
        with open('api_keys.json', 'w+') as api_keys_file:
            api_keys_file.write(json.dumps(new_api_keys))
            api_keys_file.close()

        if self.calling_keys_button.text == self.edit_public[:8] + " / " + self.edit_secret[:8]:
            self.calling_keys_button.text = 'Set Keys'

        self.chosen_api_key_pair = None
        self.update_api_spinners()
        self.add_keys_popup.dismiss()

    @staticmethod
    def fetch_api_keys_from_file():
        """
        get all api_keys currently saved in the api_keys.json file
        :return:
        """
        with open('api_keys.json', 'a+') as api_keys_file:
            try:
                api_keys = json.load(api_keys_file)
            except ValueError:
                api_keys = []
            api_keys_file.close()
        return api_keys

    @staticmethod
    def save_api_keys_to_file(api_keys):
        """
        save the api_keys json instance back to the file
        :param api_keys:
        :return:
        """
        with open('api_keys.json', 'w+') as api_keys_file:
            api_keys_file.write(json.dumps(api_keys))
            api_keys_file.close()

    def check_address(self, instance, value):
        """
        validate an entered address by checking the checksum an ensuring the first character is 'B'
        :param instance:
        :param value:
        :return:
        """
        if self.utils.check_checksum(value) and value[:1] == 'B':
            instance.foreground_color = (0, 0, 0, 1)
        else:
            instance.foreground_color = (0.93725, 0.31176, 0.17843, 1)

    def set_unit(self, instance, value):
        self.selected_unit = value

    def set_bot(self, instance, value):
        self.selected_bot = value

    def set_pool_maximum_rate(self, req, result):
        if self.exchange not in result:
            self.rates_error(req, result)
            return
        if self.selected_unit.lower() not in result[self.exchange]:
            self.rates_error(req, result)
            return
        self.ask_max = (result[self.exchange][self.selected_unit.lower()]['ask']['rate'] * 100)
        self.bid_max = (result[self.exchange][self.selected_unit.lower()]['bid']['rate'] * 100)
        self.ask_slider.max = self.ask_max
        self.bid_slider.max = self.bid_max


    def rates_error(self, req, result):
        self.rates_content.add_widget(Label(text='Unable to get Maximum rate data from the server'))
        self.ask_slider.max = 0
        self.bid_slider.max = 0

    def enter_rates(self, instance):
        """
        Show a pop-up in which minimum interest rates can be entered on sliders
        :param instance:
        :return:
        """
        self.calling_rates_button = instance
        self.rates_content = BoxLayout(orientation='vertical')
        config = ConfigParser()
        config_ini = App.get_running_app().get_application_config()
        config.read(config_ini)
        url = "http://%s:%s/exchanges" % (config.get('server', 'host'), config.get('server', 'port'))
        self.ask_slider = Slider(step=0.01, size_hint=(0.9, 1))
        self.bid_slider = Slider(step=0.01, size_hint=(0.9, 1))
        req = UrlRequest(url, self.set_pool_maximum_rate, self.rates_error, self.rates_error)
        self.ask_slider.bind(on_touch_down=self.update_slider_values)
        self.ask_slider.bind(on_touch_up=self.update_slider_values)
        self.ask_slider.bind(on_touch_move=self.update_slider_values)
        self.bid_slider.bind(on_touch_down=self.update_slider_values)
        self.bid_slider.bind(on_touch_up=self.update_slider_values)
        self.bid_slider.bind(on_touch_move=self.update_slider_values)
        self.rates_content.add_widget(Label(text='Minimal Ask Rate'))
        ask_layout = BoxLayout()
        ask_layout.add_widget(self.ask_slider)
        self.ask_value = Label(size_hint=(0.1, 1))
        ask_layout.add_widget(self.ask_value)
        self.rates_content.add_widget(ask_layout)
        self.rates_content.add_widget(Label(text='Minimal Bid Rate'))
        bid_layout = BoxLayout()
        bid_layout.add_widget(self.bid_slider)
        self.bid_value = Label(size_hint=(0.1, 1))
        bid_layout.add_widget(self.bid_value)
        self.rates_content.add_widget(bid_layout)
        if instance.text != 'Set Rates':
            rates = instance.text.split(' | ')
            self.ask_slider.value = float(rates[0])
            self.bid_slider.value = float(rates[1])
        self.update_slider_values(None, None)
        btnlayout = BoxLayout(size_hint_y=None, height='50dp', spacing='5dp')
        btn = Button(text='Ok')
        btn.bind(on_release=self.close_rates_popup)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel')
        btn.bind(on_release=self.close_rates_popup)
        btnlayout.add_widget(btn)
        self.rates_content.add_widget(btnlayout)
        popup_width = min(0.95 * Window.width, dp(500))
        self.rates_popup = Popup(title='Minimal Interest Rates', content=self.rates_content, auto_dismiss=False,
                                 size_hint=(None, None), size=(popup_width, '300dp'))
        self.rates_popup.open()

    def update_slider_values(self, instance, value):
        self.ask_value.text = str(self.ask_slider.value)
        self.bid_value.text = str(self.bid_slider.value)

    def close_rates_popup(self, instance):
        if instance.text == "Ok":
            self.calling_rates_button.text = str(self.ask_slider.value) + ' | ' + str(self.bid_slider.value)
        self.rates_popup.dismiss()