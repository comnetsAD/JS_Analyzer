# -*- coding: utf-8 -*-
"""JavaScript analysis tool.

Author:
    Jacinta Hu

About:
    This tool makes it possible to view the effect of individual scripts
    on the overall functionality of a webpage.

Todo:
    * Trace nested scripts fully and show recursive calls through indentation of buttons
    * Optimize for speed, especially upon initial page load
    * Build a script dependency tree (in collaboration with Jahnae)
    * Update the proxy to handle files with long URLs (in collaboration with Gabriel)

"""

import os
import time
from collections import OrderedDict
import json
import base64
import requests
import brotli
import wx
from wx.lib.scrolledpanel import ScrolledPanel
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
import jsbeautifier

PROXY_IP = "10.224.41.171"
PROXY_PORT = 8080

# proxy variables
HTTP_PROXY = "http://" + PROXY_IP + ":" + str(PROXY_PORT)
HTTPS_PROXY = "https://" + PROXY_IP + ":" + str(PROXY_PORT)
PROXYDICT = {"http": HTTP_PROXY, "https": HTTPS_PROXY}
PROXY = PROXY_IP + ":" + str(PROXY_PORT)

# feature store (60 features)
FEATURES = [".lookupPrefix", ".prefix", ".childNodes", ".open", ".isEqualNode", ".documentURI",
            ".lastChild", ".nodeName", ".title", ".implementation", ".normalizeDocument", ".forms",
            ".input", ".anchors", ".createCDATASection", ".URL", ".getElementsByTagName",
            ".createEntityReference", ".domConfig", ".createElement", ".xmlStandalone",
            ".referrer", ".textContent", ".doctype", ".namespaceURI", ".strictErrorChecking",
            ".xmlEncoding", ".appendChild", ".domain", ".createAttribute", ".links", ".adoptNode",
            ".Type", ".nextSibling", ".firstChild", ".images", ".close", ".xmlVersion", ".event",
            ".form", ".createComment", ".removeChild", ".nodeValue", ".localName",
            ".ownerDocument", ".previousSibling", ".body", ".isDefaultNamespace", ".nodeType",
            ".track", ".isSameNode", ".cookie", ".createDocumentFragment", ".getElementsByName",
            ".baseURI", ".lookupNamespaceURI", ".parentNode", ".getElementById", ".attributes",
                        ".createTextNode"]

ENCODING = "utf-8"


class MyPanel(wx.Panel):
    """The GUI of the tool."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.frame = parent

        # start Chrome webdriver
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=%s' % PROXY)
        chrome_options.add_argument('--auto-open-devtools-for-tabs')
        caps = DesiredCapabilities.CHROME
        caps['goog:loggingPrefs'] = {'performance': 'INFO'}
        chrome_options.add_experimental_option(
            'perfLoggingPrefs', {'enablePage': True})
        self.driver = webdriver.Chrome(options=chrome_options,
                                       desired_capabilities=caps)
        self.driver.execute_cdp_cmd('Network.enable', {})
        self.driver.execute_cdp_cmd('Network.setCacheDisabled', {
            'cacheDisabled': True})

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # TextCtrl for user to input URL of site to analyze
        self.url_input = wx.TextCtrl(self, style=wx.TE_LEFT)
        self.url_input.SetValue("https://www.unicef.org")
        self.url_input.Bind(wx.EVT_KEY_DOWN, self.on_key_press)
        self.main_sizer.Add(self.url_input, flag=wx.EXPAND |
                            wx.TOP | wx.LEFT | wx.RIGHT, border=25)

        # StaticText field for error messages
        self.err_msg = wx.StaticText(self, label="")
        self.err_msg.SetForegroundColour((255, 0, 0))  # make text red
        self.main_sizer.Add(self.err_msg, flag=wx.LEFT, border=25)

        analyze_btn = wx.Button(self, label='Analyze page')
        analyze_btn.Bind(wx.EVT_BUTTON, self.on_analyze_press)
        self.main_sizer.Add(analyze_btn, flag=wx.ALL | wx.CENTER, border=25)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.scripts_panel = ScrolledPanel(
            self, -1, size=(375, 550))
        self.scripts_panel.SetupScrolling()
        hbox.Add(self.scripts_panel)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.features_panel = ScrolledPanel(
            self, -1, size=(375, 275))
        self.features_panel.SetupScrolling()
        vbox.Add(self.features_panel, flag=wx.CENTER, border=5)

        self.content_panel = ScrolledPanel(
            self, -1, size=(375, 275))
        self.content_panel.SetupScrolling()
        vbox.Add(self.content_panel, flag=wx.CENTER, border=5)
        hbox.Add(vbox)
        self.main_sizer.Add(hbox, flag=wx.CENTER | wx.BOTTOM, border=25)

        self.select_all_btn = wx.ToggleButton(self, label='Select All')
        self.select_all_btn.Bind(wx.EVT_TOGGLEBUTTON, self.on_all_press)
        self.select_all_btn.Hide()
        self.main_sizer.Add(self.select_all_btn,
                            flag=wx.BOTTOM | wx.CENTER, border=25)

        self.diff_btn = wx.Button(self, label='Get diff')
        self.diff_btn.Bind(wx.EVT_BUTTON, self.on_diff_press)
        self.diff_btn.Hide()
        self.main_sizer.Add(self.diff_btn, flag=wx.BOTTOM |
                            wx.CENTER, border=25)

        self.SetSizer(self.main_sizer)
        self.url = self.url_input.GetValue()
        self.suffix = "?JSTool=none"
        self.script_sizer = None
        self.script_buttons = []
        self.choice_boxes = []
        self.number_of_buttons = 0
        self.unknown_scripts = []
        self.javascripts = {}
        self.script_urls = []

        self.features_panel.Hide()
        self.content_panel.Hide()

        self.features_text = ExpandoTextCtrl(
            self.features_panel, size=(375, 275), style=wx.TE_READONLY)
        self.features_text.SetValue("Features listing")
        self.Bind(EVT_ETC_LAYOUT_NEEDED, None, self.features_text)

        self.features_sizer = wx.BoxSizer(wx.VERTICAL)
        self.features_sizer.Add(self.features_text, flag=wx.CENTER)
        self.features_panel.SetSizer(self.features_sizer)

        self.content_text = ExpandoTextCtrl(
            self.content_panel, size=(375, 275), style=wx.TE_READONLY)
        self.content_text.SetValue("Script code")
        self.Bind(EVT_ETC_LAYOUT_NEEDED, None, self.content_text)

        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.content_sizer.Add(self.content_text, flag=wx.CENTER)
        self.content_panel.SetSizer(self.content_sizer)

    def on_analyze_press(self, event):
        """Handle 'Analyze' button press."""
        self.analyze()

    def on_key_press(self, event):
        """Handle keyboard input."""
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
            self.analyze()
        else:
            event.Skip()

    def add_button(self, script, index):
        """Add script to self.script_buttons at index and update display."""
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(25)
        # create button
        self.script_buttons.insert(index, wx.ToggleButton(
            self.scripts_panel, label=script.split("/")[-1][:8]))
        self.script_buttons[index].Bind(
            wx.EVT_TOGGLEBUTTON, self.on_script_press)
        self.script_buttons[index].myname = script
        hbox.Add(self.script_buttons[index], flag=wx.ALL, border=5)
        self.number_of_buttons += 1

        # create combobox
        choice_box = wx.ComboBox(self.scripts_panel, value="", style=wx.CB_READONLY, choices=(
            "", "critical", "non-critical", "translatable"))
        choice_box.Bind(wx.EVT_COMBOBOX, self.on_choice)
        choice_box.index = len(self.choice_boxes)
        self.choice_boxes.insert(index, choice_box)

        hbox.Add(choice_box, flag=wx.ALL, border=5)
        self.number_of_buttons += 1

        self.script_sizer.Insert(index, hbox)
        self.frame.frame_sizer.Layout()
        self.script_urls.append(script)

    def get_content_from_src(self, src):
        """Get content from src as a string."""
        if src[:4] != "http":
            if src[0] == "/":
                if src[1] == "/":
                    src = "https:" + src
                else:
                    src = self.url + src
            else:
                src = self.url + "/" + src
        req = requests.get(src, proxies=PROXYDICT, verify=False)
        content_text = req.text
        try:
            if req.headers['content-encoding'] == 'br':
                # TO-DO: should update encoding based on
                # req.headers['content-type'] (if specified)
                content_text = brotli.decompress(req.content).decode(ENCODING)
        except KeyError:
            # no encoding
            pass
        content_text = jsbeautifier.beautify(content_text)
        return src, content_text

    def extract_features(self, content_text):
        """Count features in content_text and return a string."""
        tmp = {}
        for feature in FEATURES:
            if feature in content_text:
                tmp[feature] = content_text.count(feature)
        tmp_sorted = OrderedDict(
            sorted(tmp.items(), key=lambda x: x[1], reverse=True))
        tmp = ""
        for key, value in tmp_sorted.items():
            tmp += "{0}: {1}\n".format(key, value)
        return tmp

    def wait_for_load(self):
        """Wait for page source to stop changing."""
        html = self.driver.page_source
        time.sleep(0.5)  # is this a reasonable amount of time?
        while html != self.driver.page_source:
            html = self.driver.page_source
            time.sleep(0.5)

    def analyze(self):
        """Do everything."""
        # Never got this part to work
        self.err_msg.SetForegroundColour((0, 0, 0))
        self.err_msg.SetLabel("Loading page... please wait")
        self.err_msg.SetForegroundColour((255, 0, 0))
        self.Update()

        # Reset values
        self.url = self.url_input.GetValue()
        self.suffix = "?JSTool=none"
        self.unknown_scripts.clear()
        self.script_buttons.clear()
        self.choice_boxes.clear()
        self.javascripts.clear()
        self.number_of_buttons = 0
        if not self.url:
            return

        # Get all scripts from original page and parse selenium rendered
        # version
        try:
            self.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': []})
            epoch_in_milliseconds = time.time() * 1000
            self.driver.get(self.url)
            self.parse_log(epoch_in_milliseconds)
            self.err_msg.SetLabel("")
            self.wait_for_load()
        except Exception as exception:
            self.err_msg.SetLabel(str(exception))
            print(exception)
            return

        html = BeautifulSoup(self.driver.page_source, 'html.parser').prettify()

        # Populate list of unknown (source) scripts
        cnt = 0
        while "<script" in html:
            start_index = html.find("<script")
            end_index = html.find("</script>")
            text = html[start_index:end_index + 9]
            self.unknown_scripts.append(text)
            html = html.replace(text, "\n<!--script" + str(cnt) + "-->\n")
            cnt += 1
        print("number of selenium scripts:")
        print(len(self.unknown_scripts))
        # End selenium-rendered parsing

        # Uncomment to show diff button
        # self.diff_btn.Show()

        # Reset display
        self.select_all_btn.SetValue(False)
        self.select_all_btn.Show()
        self.features_panel.Show()
        self.content_panel.Show()
        self.features_text.SetValue("Features listing")
        self.content_text.SetValue("Script code")

        while self.script_sizer is not None and self.script_sizer.GetChildren():
            self.script_sizer.Remove(0)
        self.frame.frame_sizer.Layout()

        # TO-DO: make request asynchronously? Might save some time

        # Get index.html from proxy
        req = requests.get(self.url, proxies=PROXYDICT, verify=False)
        html = ""
        if req.headers['content-encoding'] == 'br':
            html = BeautifulSoup(brotli.decompress(req.content).decode(
                ENCODING), 'html.parser').prettify()
        else:
            html = BeautifulSoup(req.text, 'html.parser').prettify()

        # Create display to house script buttons
        self.script_sizer = wx.BoxSizer(wx.VERTICAL)

        # Add scripts to self.JavaScripts and create buttons
        cnt = 0
        while "<script" in html:
            src = ""
            start_index = html.find("<script")
            end_index = html.find("</script>")
            text = html[start_index:end_index + 9]
            content_text = text[text.find(">") + 1:text.find("</script>")]
            if ' src="' in text:  # BeautifulSoup turns all single quotes into double quotes
                src = text.split(' src="')[1].split('"')[0]
                src, content_text = self.get_content_from_src(src)

            html = html.replace(text, "\n<!--script" + str(cnt) + "-->\n")
            hbox = wx.BoxSizer(wx.HORIZONTAL)

            # create script button
            self.script_buttons.append(wx.ToggleButton(
                self.scripts_panel, label="script" + str(cnt)))
            self.script_buttons[cnt].Bind(
                wx.EVT_TOGGLEBUTTON, self.on_script_press)
            self.script_buttons[cnt].myname = "script" + str(cnt)
            hbox.Add(self.script_buttons[cnt], flag=wx.ALL, border=5)
            self.number_of_buttons += 1

            # create combobox
            choice_box = wx.ComboBox(self.scripts_panel, value="", style=wx.CB_READONLY, choices=(
                "", "critical", "non-critical", "translatable"))
            choice_box.Bind(wx.EVT_COMBOBOX, self.on_choice)
            choice_box.index = len(self.choice_boxes)
            self.choice_boxes.append(choice_box)

            hbox.Add(choice_box, flag=wx.ALL, border=5)
            self.number_of_buttons += 1
            self.script_sizer.Add(hbox)

            tmp = self.extract_features(content_text)
            self.javascripts["script" + str(cnt)] = {
                'features': tmp,
                'content': content_text,
                'text': text,
                'src': src
            }
            if text in self.unknown_scripts:
                self.unknown_scripts.remove(text)

            cnt += 1

        self.scripts_panel.SetSizer(self.script_sizer)
        self.frame.frame_sizer.Layout()

        self.script_urls.clear()
        for script in self.javascripts:
            src = self.javascripts[script]['src']
            if src != "":
                self.script_urls.append(src)

        i = 0
        while i < len(self.unknown_scripts):
            text = self.unknown_scripts[i]
            if ' src="' in text:  # BeautifulSoup turns all single quotes into double quotes
                src = text.split(' src="')[1].split('"')[0]
                src, content_text = self.get_content_from_src(src)
                tmp = self.extract_features(content_text)
                self.javascripts[src] = {
                    'features': tmp, 'content': content_text, 'text': text, 'src': src}
                self.unknown_scripts.pop(i)
            else:
                self.unknown_scripts[i] = jsbeautifier.beautify(
                    text[text.find(">") + 1:text.find("</script>")])
                i += 1

        # Get page with all scripts removed
        try:
            self.driver.execute_cdp_cmd(
                'Network.setBlockedURLs', {'urls': ['*.js']})
            self.driver.get(self.url + self.suffix)
            self.err_msg.SetLabel("")
        except Exception as exception:
            self.err_msg.SetLabel(str(exception))
            print(exception)
            return

        # for diff
        # final_html = BeautifulSoup(self.driver.execute_script(
            # "return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')
        # file_stream = open("before.html", "w")
        # file_stream.write(final_html.prettify())
        # file_stream.close()

        self.print_scripts()

    def on_all_press(self, event):
        """Handle 'Select All' button press."""
        try:
            toggle = event.GetEventObject().GetValue()
        except BaseException:
            toggle = True

        self.suffix = "?JSTool="
        self.script_urls.clear()

        if toggle:
            # Toggle all script buttons
            for i, btn in enumerate(self.script_buttons):
                btn.SetValue(True)
                self.suffix += "_" + str(i)

        else:
            # Untoggle all script buttons
            for btn in self.script_buttons:
                btn.SetValue(False)

            # Block all external scripts
            for script in self.javascripts:
                src = self.javascripts[script]['src']
                if src != "":
                    self.script_urls.append(src)

            self.suffix += "none"

        self.driver.execute_cdp_cmd('Network.setBlockedURLs',
                                    {'urls': self.script_urls})
        epoch_in_milliseconds = time.time() * 1000
        self.driver.get(self.url + self.suffix)
        self.wait_for_load()
        self.parse_log(epoch_in_milliseconds)

    def on_script_press(self, event):
        """Handle script button press."""
        try:
            name = event.GetEventObject().myname
            toggle = event.GetEventObject().GetValue()
            index = self.script_buttons.index(event.GetEventObject())
        except BaseException:
            name = "script0"
            toggle = True
            index = 0
        url = self.javascripts[name]['src']

        js_content = self.javascripts[name]['content']
        features_text = self.javascripts[name]['features']
        if name[:6] == "script":
            if url == "":
                features_text = name + ' inline\n\n' + features_text
            else:
                features_text = name + ' from ' + url + '\n\n' + features_text
        else:
            features_text = name + '\n\n' + features_text

        self.features_text.SetValue(features_text)
        self.content_text.SetValue(js_content)

        if toggle:
            if self.javascripts[name]['src'] != "":
                self.script_urls.remove(url)
        else:
            self.select_all_btn.SetValue(False)
            if self.javascripts[name]['src'] != "":
                self.script_urls.append(url)

        self.suffix = "?JSTool="
        for btn in self.script_buttons:
            if btn.GetValue() and btn.myname[:6] == "script":
                self.suffix += "_" + btn.myname[6:]
        if self.suffix == "?JSTool=":
            self.suffix += "none"

        self.driver.execute_cdp_cmd('Network.setBlockedURLs',
                                    {'urls': self.script_urls})
        epoch_in_milliseconds = time.time() * 1000
        self.driver.get(self.url + self.suffix)
        self.wait_for_load()
        scripts = self.parse_log(epoch_in_milliseconds)
        for scriptname in scripts:
            if scriptname not in [s.myname for s in self.script_buttons]:
                print('inserting', scriptname, 'under', name)
                self.add_button(scriptname, index + 1)
                if self.javascripts[scriptname]['src'] not in self.script_urls:
                    self.script_urls.append(
                        self.javascripts[scriptname]['src'])

        self.driver.execute_cdp_cmd('Network.setBlockedURLs',
                                    {'urls': self.script_urls})
        self.print_blocked_scripts()
        self.driver.get(self.url + self.suffix)

    def on_diff_press(self, event):
        """Handle 'Get Diff' button press."""
        final_html = BeautifulSoup(self.driver.execute_script(
            "return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')
        try:
            file_stream = open("after.html", "r")
            before = file_stream.read()
            file_stream.close()
            file_stream = open("before.html", "w")
            file_stream.write(before)
            file_stream.close()
        except IOError:
            pass
        file_stream = open("after.html", "w")
        file_stream.write(final_html.prettify())
        file_stream.close()
        os.system(r"diff before.html after.html | sed '/<!--script/,/<\/script>/d'")

    def on_choice(self, event):
        """Handle choiceBox selection."""
        choice_box = self.choice_boxes[event.GetEventObject().index]
        colors = {
            "": wx.Colour(255, 255, 255, 100),
            "critical": wx.Colour(255, 0, 0, 100),
            "non-critical": wx.Colour(0, 255, 0, 100),
            "translatable": wx.Colour(0, 0, 255, 100)
        }
        choice_box.SetBackgroundColour(colors[choice_box.GetValue()])

    def parse_log(self, epoch_in_milliseconds):
        """Return list of scripts requested since epoch_in_milliseconds."""
        scripts = []
        log = self.driver.get_log('performance')
        for entry in reversed(log):
            # only look at logs since time
            if entry['timestamp'] < epoch_in_milliseconds:
                break
            message = json.loads(entry['message'])['message']
            if message['method'] == 'Network.responseReceived':
                response = message['params']['response']
                content_type = response['mimeType']
                # content_type can also be found in
                # response['headers']['content-type'] or
                # response['headers']['Content-Type']
                url = response['url']
                if 'javascript' in content_type:
                    url = url.replace('&amp;', '&').replace('&', '&amp;')
                    found = False
                    for key, val in self.javascripts.items():
                        if url == val['src']:
                            scripts.append(key)
                            found = True
                            break
                    if not found:
                        print("script from", url, "not seen before")
                        request_id = message['params']['requestId']
                        try:
                            response_body = self.driver.execute_cdp_cmd('Network.getResponseBody', {
                                'requestId': str(request_id)})
                            try:
                                body = response_body['body']
                                if response_body['base64Encoded']:
                                    print('decoding body')
                                    # not yet tested
                                    body = base64.b64decode(body)
                                content = jsbeautifier.beautify(body)
                                if content in self.unknown_scripts:
                                    print("found script in unknownScripts")
                                    tmp = self.extract_features(content)
                                    self.javascripts[url] = {
                                        'features': tmp,
                                        'content': content,
                                        'text': content,
                                        'src': url
                                    }
                                    scripts.append(url)
                                    self.unknown_scripts.remove(content)
                                else:
                                    print("script not found:")
                                    # print(content[:200])
                                    # print("---" * 20)
                                    # self.print_known_scripts()
                            except KeyError as k:
                                print(k)
                        except Exception as exception:
                            print(str(exception))
            if message['method'] == 'Network.requestWillBeSent':
                if message['params']['type'] == 'Script':
                    try:
                        # initiator
                        initiator = message['params']['initiator']
                        if initiator['type'] == 'script':
                            initiator = initiator['stack']['callFrames'][0]['url']
                        else:
                            initiator = initiator['url']
                        # request
                        request_url = message['params']['request']['url']
                        print("requesting", request_url, "from", initiator)
                    except KeyError as exception:
                        print(exception)

            #print(json.dumps(message, indent=2, sort_keys=True))
        return scripts

    def print_scripts(self):
        """Print all stored scripts."""
        self.print_known_scripts()
        self.print_unknown_scripts()
        self.print_blocked_scripts()
        print("---" * 20)

    def print_known_scripts(self):
        """Print scripts with known sources."""
        print("KNOWN SCRIPTS")
        print("---" * 20)
        for key, val in self.javascripts.items():
            print(key)
            print(val['content'][:200])
            print("---" * 20)

    def print_unknown_scripts(self):
        """Print scripts with no known source."""
        print("UNKNOWN SCRIPTS")
        print("---" * 20)
        for content in self.unknown_scripts:
            print(content[:200])
            print("***" * 20)

    def print_blocked_scripts(self):
        """Print blocked URLs."""
        print('BLOCKED SCRIPTS:')
        for url in self.script_urls:
            print("\t", url)


class MyFrame(wx.Frame):
    """The outer frame of the tool."""

    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="JS Cleaner")

        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        exit_menu_item = file_menu.Append(101, "Exit", "Exit the application")
        about_menu_item = file_menu.Append(102, "About", "About")

        menu_bar.Append(file_menu, "&File")
        self.Bind(wx.EVT_MENU, self.on_exit, exit_menu_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_menu_item)
        self.SetMenuBar(menu_bar)

        self.frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel = MyPanel(self)
        self.frame_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(self.frame_sizer)
        self.Fit()
        self.Show()

    def on_exit(self, event):
        """Handle exit."""
        self.Close()

    def on_about(self, event):
        """Handle about."""
        msg = wx.MessageDialog(
            self,
            "This tool was built for JS analyses by the ComNets AD lab @ NYUAD. September 2019.",
            "About",
            wx.OK | wx.ICON_INFORMATION)
        msg.ShowModal()


def main():
    """Main function."""
    app = wx.App(False)
    # width, height = wx.GetDisplaySize()
    frame = MyFrame()
    frame.SetSize(800, 800)
    frame.SetMaxSize(wx.Size(800, 800))
    frame.SetMinSize(wx.Size(800, 800))
    frame.SetPosition((25, 25))

    app.MainLoop()
    if os.path.isfile("after.html"):
        os.remove("after.html")
    if os.path.isfile("before.html"):
        os.remove("before.html")
    frame.panel.driver.quit()

if __name__ == "__main__":
    main()
