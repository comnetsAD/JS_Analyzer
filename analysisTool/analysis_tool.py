# -*- coding: utf-8 -*-
"""JavaScript analysis tool.

Author:
    Jacinta Hu

About:
    This tool makes it possible to view the effect of individual scripts
    on the overall functionality of a webpage.

Todo:
    * Make sure clicking "Analyze" again doesn't break the page
    * Trace nested scripts fully and show recursive calls through indentation of buttons
        * How to figure out initiating script when initiated from parser?
        * Is it possible to enable a nested script without enabling the script that called it?
            * May need to pair with selenium page_source script
    * Update encoding based on req.headers['content-type'] (if specified) in brotli decompression
    * Optimize for speed, especially upon initial page load
        * Check out anytree.cachedsearch instead of anytree.search
        * Any way to avoid making Network.getResponseBody requests?
            * Look for script in proxy instead?
    * Build a script dependency tree (in collaboration with Jahnae)
    * Update the proxy to handle files with long URLs (in collaboration with Gabriel)

"""

import logging
import os
import time
from collections import OrderedDict
import json
import base64
import bisect
from anytree import AnyNode, RenderTree, PreOrderIter
import anytree.cachedsearch
import requests
import brotli
import wx
from wx.lib.scrolledpanel import ScrolledPanel
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import InvalidArgumentException
from bs4 import BeautifulSoup
import jsbeautifier


def get_attribute(node, attribute):
    """Return the node.attribute or None if it doesn't exist."""
    try:
        return getattr(node, attribute)
    except AttributeError:
        return None


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
        self.url_input.SetValue("https://www.unicef.org/")
        self.url_input.Bind(wx.EVT_KEY_DOWN, self.on_key_press)
        self.main_sizer.Add(self.url_input, flag=wx.EXPAND |
                            wx.TOP | wx.LEFT | wx.RIGHT, border=25)

        # StaticText field for error messages
        self.err_msg = wx.StaticText(self, label="")
        self.err_msg.SetForegroundColour((255, 0, 0))  # make text red
        self.main_sizer.Add(self.err_msg, flag=wx.LEFT, border=25)

        analyze_btn = wx.Button(self, label='Analyze page')
        analyze_btn.Bind(wx.EVT_BUTTON, self.on_button_press)
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
        self.diff_btn.Bind(wx.EVT_BUTTON, self.on_button_press)
        self.diff_btn.Hide()
        self.main_sizer.Add(self.diff_btn, flag=wx.BOTTOM |
                            wx.CENTER, border=25)

        self.SetSizer(self.main_sizer)
        self.url = self.url_input.GetValue()
        self.suffix = "?JSTool=none"
        self.script_sizer = wx.BoxSizer(wx.VERTICAL)
        self.script_buttons = []
        self.choice_boxes = []
        self.number_of_buttons = 0
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

        self.script_tree = AnyNode(id='root')

    def on_button_press(self, event):
        """Handle wx.Button press."""
        btn = event.GetEventObject()
        if btn.GetLabel() == 'Analyze page':
            self.analyze()
        elif btn == self.diff_btn:
            self.on_diff_press()

    def on_key_press(self, event):
        """Handle keyboard input."""
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
            self.analyze()
        else:
            event.Skip()

    def add_button(self, script, index, depth):
        """Add script to self.script_buttons at index and update display."""
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(depth*25)
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

    def format_src(self, src):
        """Return formatted src string to be requested."""
        if src[:4] != "http":
            if src[0] == "/":
                if src[1] == "/":
                    src = "https:" + src
                else:
                    src = self.url + src[1:]
            else:
                src = self.url + src
        return src

    def get_response_body(self, request_id):
        """Return body of response with request_id."""
        response_body = self.driver.execute_cdp_cmd(
            'Network.getResponseBody',
            {'requestId': str(request_id)}
        )
        body = response_body['body']
        try:
            if response_body['base64Encoded']:
                logging.info('decoding body')
                # not yet tested
                body = base64.b64decode(body)
        except KeyError as error:
            logging.exception(str(error))
        body = jsbeautifier.beautify(body)
        return body

    def block_all_scripts(self):
        """Block scripts in self.script_tree."""
        self.script_urls.clear()
        for node in PreOrderIter(self.script_tree):
            if node.id[:6] != "script" and not node.is_root:
                self.script_urls.append(node.id)
        self.driver.execute_cdp_cmd('Network.setBlockedURLs',
                                    {'urls': self.script_urls})

    def wait_for_load(self):
        """Wait for page source to stop changing."""
        html = self.driver.page_source
        time.sleep(0.5)  # is this a reasonable amount of time?
        while html != self.driver.page_source:
            html = self.driver.page_source
            time.sleep(0.5)

    def analyze(self):
        """Do everything."""
        def reset_display():
            # Reset display
            self.suffix = "?JSTool=none"
            self.script_buttons.clear()
            self.choice_boxes.clear()
            self.number_of_buttons = 0
            self.select_all_btn.SetValue(False)
            self.select_all_btn.Show()
            self.features_panel.Show()
            self.content_panel.Show()
            self.features_text.SetValue("Features listing")
            self.content_text.SetValue("Script code")
            while self.script_sizer.GetChildren():
                self.script_sizer.Remove(0)
            self.frame.frame_sizer.Layout()

        def get_index_html():
            # Get index.html from proxy
            req = requests.get(self.url, proxies=PROXYDICT, verify=False)
            html = ""
            try:
                if req.headers['content-encoding'] == 'br':
                    html = BeautifulSoup(brotli.decompress(req.content).decode(
                        ENCODING), 'html.parser').prettify()
                else:
                    html = BeautifulSoup(req.text, 'html.parser').prettify()
            except KeyError:
                html = BeautifulSoup(req.text, 'html.parser').prettify()
            return html

        def parse_html(html):
            # Add index.html scripts to self.script_tree
            cnt = 0
            while "<script" in html:
                src = ""
                script_name = "script" + str(cnt)
                start_index = html.find("<script")
                end_index = html.find("</script>")
                text = html[start_index:end_index + 9]
                new_node = AnyNode(
                    id=script_name, parent=self.script_tree, content=text)
                if ' src="' in text:  # BeautifulSoup turns all single quotes into double quotes
                    src = text.split(' src="')[1].split('"')[0].split("?")[0]
                    src = self.format_src(src)
                    node = anytree.cachedsearch.find(
                        self.script_tree, lambda node: node.id == src)
                    if node:
                        node.parent = new_node
                html = html.replace(text, "\n<!--" + script_name + "-->\n")
                cnt += 1

        def create_buttons():
            # Add buttons to display
            index = 0
            original_script = False
            for node in PreOrderIter(self.script_tree):
                if node.depth == 1:
                    if node.id[:6] == "script":
                        original_script = True
                    else:
                        original_script = False
                if not original_script:
                    # Skip to next node with depth 1
                    continue
                node.button = index
                self.add_button(node.id, index, node.depth)
                index += 1
            self.scripts_panel.SetSizer(self.script_sizer)
            self.frame.frame_sizer.Layout()

        def display_loading_message():
            # Never managed to get this part to display before spinning wheel of death
            self.err_msg.SetForegroundColour((0, 0, 0))
            self.err_msg.SetLabel("Loading page... please wait")
            self.err_msg.SetForegroundColour((255, 0, 0))
            self.Update()

        display_loading_message()

        # Reset values
        self.url = self.url_input.GetValue()
        if self.url[-1] != "/":
            self.url = self.url + "/"
        if not self.url:
            return
        reset_display()
        self.script_tree = AnyNode(id=self.url)

        # Get original page and parse external scripts
        self.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': []})
        epoch_in_milliseconds = time.time() * 1000
        try:
            self.driver.get(self.url)
            self.err_msg.SetLabel("")
        except InvalidArgumentException as exception:
            self.err_msg.SetLabel(str(exception))
            return
        self.wait_for_load()
        scripts = self.parse_log(epoch_in_milliseconds)
        for script in scripts:
            # pylint: disable=undefined-loop-variable
            # pylint: disable=cell-var-from-loop
            parent = anytree.cachedsearch.find(self.script_tree,
                                               lambda node: node.id == script['parent'])
            AnyNode(id=script['url'], parent=parent, content=script['content'])
        self.print_scripts()

        # Parse inline scripts
        html = get_index_html()
        parse_html(html)
        self.print_scripts()

        # Create buttons
        create_buttons()

        # Get page with all scripts removed
        self.block_all_scripts()
        try:
            self.driver.get(self.url + self.suffix)
            self.err_msg.SetLabel("")
        except InvalidArgumentException as exception:
            self.err_msg.SetLabel(str(exception))
            return

        # for diff
        # final_html = BeautifulSoup(self.driver.execute_script(
            # "return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')
        # file_stream = open("before.html", "w")
        # file_stream.write(final_html.prettify())
        # file_stream.close()

    def on_all_press(self, event):
        """Handle 'Select All' button press."""
        toggle = event.GetEventObject().GetValue()

        self.suffix = "?JSTool="

        if toggle:
            # Toggle all script buttons
            for i, btn in enumerate(self.script_buttons):
                btn.SetValue(True)
                self.suffix += "_" + str(i)
            self.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': []})
        else:
            # Untoggle all script buttons
            for btn in self.script_buttons:
                btn.SetValue(False)
            self.block_all_scripts()
            self.suffix += "none"

        self.driver.get(self.url + self.suffix)

    def on_script_press(self, event):
        """Handle script button press."""
        def get_content_from_src(src):
            """Get content from src as a string."""
            logging.debug("getting %s", src)
            req = requests.get(src, proxies=PROXYDICT, verify=False)
            content_text = req.text
            try:
                if req.headers['content-encoding'] == 'br':
                    content_text = brotli.decompress(
                        req.content).decode(ENCODING)
            except KeyError:
                # no encoding
                pass
            content_text = jsbeautifier.beautify(content_text)
            return content_text

        def extract_features(content_text):
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

        name = event.GetEventObject().myname
        toggle = event.GetEventObject().GetValue()
        node = anytree.cachedsearch.find(
            self.script_tree, lambda node: node.id == name)

        if not get_attribute(node, 'content'):
            node.content = get_content_from_src(node.id)
        if not get_attribute(node, 'features'):
            node.features = extract_features(node.content)

        self.features_text.SetValue(name + "\n\n" + node.features)
        self.content_text.SetValue(node.content)

        if toggle:
            while node.depth > 1:
                self.script_buttons[node.button].SetValue(True)
                try:
                    self.script_urls.remove(node.id)
                except ValueError:
                    pass
                node = node.parent
            self.script_buttons[node.button].SetValue(True)
        else:
            self.select_all_btn.SetValue(False)
            for descendant in node.descendants:
                self.script_buttons[descendant.button].SetValue(False)
                self.script_urls.append(descendant.id)
            self.script_urls.append(node.id)

        self.suffix = "?JSTool="
        for btn in self.script_buttons:
            if btn.GetValue() and btn.myname[:6] == "script":
                self.suffix += "_" + btn.myname[6:]
        if self.suffix == "?JSTool=":
            self.suffix += "none"

        self.driver.execute_cdp_cmd('Network.setBlockedURLs',
                                    {'urls': self.script_urls})
        self.print_blocked_scripts()
        self.driver.get(self.url + self.suffix)

    def on_diff_press(self):
        """Print diff to terminal."""

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
        log = log[bisect.bisect_left(
            [entry['timestamp'] for entry in log], epoch_in_milliseconds):]
        log = [json.loads(entry['message'])['message'] for entry in log]

        def is_script_request(message):
            if message['method'] == 'Network.requestWillBeSent':
                if message['params']['type'] == 'Script':
                    return True
            return False

        # def is_script_response(message):
        #     if message['method'] == 'Network.responseReceived':
        #         if 'javascript' in message['params']['response']['mimeType']:
        #             return True
        #     return False

        def is_data_received(message):
            if message['method'] == 'Network.dataReceived':
                return True
            return False

        def get_request_info(message):
            request_id = message['params']['requestId']
            request_url = message['params']['request']['url']
            initiator = message['params']['initiator']
            if initiator['type'] == 'parser':
                # from index.html as src, need to identify script number somehow...
                # there are line numbers but are those usable?
                initiator = initiator['url']
            elif initiator['type'] == 'script':
                # pick last thing in callFrames because first thing doesn't always have URL?
                # need better understanding
                # each script has its own ID... if only I could figure out how to use it
                initiator = initiator['stack']['callFrames'][-1]['url']
            return [request_id, request_url, initiator]

        script_requests = []
        # script_responses = []
        data_received = []
        for message in log:
            if is_script_request(message):
                script_requests.append(message)
            # elif is_script_response(message):
            #     script_responses.append(message['params']['requestId'])
            elif is_data_received(message):
                data_received.append(message['params']['requestId'])

        for request in script_requests:
            request_id, url, initiator = get_request_info(request)
            if request_id in data_received:
                content = self.get_response_body(request_id)
                scripts.append(
                    {'url': url, 'parent': initiator, 'content': content})

        return scripts

    def print_scripts(self):
        """Print script tree."""
        print(RenderTree(self.script_tree).by_attr('id'))
        print("---" * 20)

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
        self.frame_sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(self.frame_sizer)
        self.Fit()
        self.Show()

    def on_exit(self, event):
        """Handle exit."""
        # pylint: disable=unused-argument
        self.Close()

    def on_about(self, event):
        """Handle about."""
        # pylint: disable=unused-argument
        msg = wx.MessageDialog(
            self,
            "This tool was built for JS analyses by the ComNets AD lab @ NYUAD. September 2019.",
            "About",
            wx.OK | wx.ICON_INFORMATION)
        msg.ShowModal()


def main():
    """Main function."""
    logging.basicConfig(level=logging.DEBUG)
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
