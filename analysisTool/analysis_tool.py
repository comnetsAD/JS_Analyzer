# -*- coding: utf-8 -*-
"""JavaScript analysis tool.

Author:
    Jacinta Hu

About:
    This tool makes it possible to view the effect of individual scripts
    on the overall functionality of a webpage.

Todo:
    * Update the proxy to handle files with long URLs (in collaboration with Gabriel)
    * How to deal with preloaded <link as="script"> tags?
    * Figure out how best to display duplicate scripts
    * What happens if two scripts together bring a new script? UNICEF example (script 0 and 7)
    * How to highlight differences? Compare event listeners?
    * Libraries?
    * Image optimization
    * Save copy of site locally using proxy to allow for direct comparison of performance
    * Generate report showing changes

"""

import logging
import os
from io import BytesIO, DEFAULT_BUFFER_SIZE
import time
import json
import base64
import bisect
import struct
from anytree import AnyNode, RenderTree, PreOrderIter
import anytree.cachedsearch
import requests
import brotli
import wx
from wx.lib.scrolledpanel import ScrolledPanel
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import InvalidArgumentException, WebDriverException
from bs4 import BeautifulSoup
import jsbeautifier
from get_image_size import get_image_size_from_bytesio, UnknownImageFormat
from data import DOMAINS, CATEGORIES
from jaccard_sim import similarity_comparison


def get_attribute(obj, attribute):
    """Return the obj.attribute or None if it doesn't exist."""
    try:
        return getattr(obj, attribute)
    except AttributeError:
        return None

def get_resource(url):
    """Request resource from proxy and return response."""
    req = requests.get(url, proxies=PROXYDICT, verify=False)
    if 'html' in req.headers['content-type']:
        html = ""
        try:
            if req.headers['content-encoding'] == 'br':
                html = BeautifulSoup(brotli.decompress(req.content).decode(
                    ENCODING), 'html.parser').prettify()
            else:
                html = BeautifulSoup(req.text, 'html.parser').prettify()
        except KeyError:
            html = BeautifulSoup(req.text, 'html.parser').prettify()
        except brotli.error as error:
            logging.error(str(error))
        return html
    if 'script' in req.headers['content-type']:
        return req.text
    elif 'image' in req.headers['content-type']:
        return req.content

# PROXY_IP = "10.224.41.171"
PROXY_IP = "127.0.0.1"
PROXY_PORT = 8080

# proxy variables
HTTP_PROXY = "http://" + PROXY_IP + ":" + str(PROXY_PORT)
HTTPS_PROXY = "https://" + PROXY_IP + ":" + str(PROXY_PORT)
PROXYDICT = {"http": HTTP_PROXY, "https": HTTPS_PROXY}
PROXY = PROXY_IP + ":" + str(PROXY_PORT)

# feature store (50 features)
FEATURES = ['replace',
            'createElement',
            'javaEnabled',
            'get',
            'getElementById',
            'appendChild',
            'toString',
            'takeRecords',
            'getElementsByTagName',
            'addEventListener',
            'getAttribute',
            'append|replace',
            'open',
            'forEach',
            'preventDefault',
            'keys',
            'setAttribute',
            'setTimeout',
            'querySelector',
            'insertBefore',
            'add',
            'appendChild|createElement|open|setAttribute|write',
            'addEventListener|postMessage',
            'closest',
            'focus',
            'write',
            'min',
            'removeAttribute',
            'error',
            'animate',
            'removeChild',
            'postMessage',
            'remove',
            'contains',
            'addEventListener|createElement|querySelectorAll|replace',
            'sendBeacon',
            'max',
            'replaceState',
            'defaultValue',
            'attachEvent|createElement|getElementById|open',
            'removeEventListener',
            'search',
            'filter',
            'appendChild|querySelector',
            'createTextNode',
            'values',
            'add|appendChild|remove',
            # pylint: disable=line-too-long
            'appendChild|createElement|getElementById|getElementsByTagName|open|removeChild|setAttribute',
            'start',
            'appendChild|getAttribute|removeEventListener|replace']

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
        self.url_input.SetValue("http://yasirzaki.net/")
        self.url_input.Bind(wx.EVT_KEY_DOWN, self.on_key_press)
        self.main_sizer.Add(self.url_input, flag=wx.EXPAND |
                            wx.TOP | wx.LEFT | wx.RIGHT, border=25)

        # StaticText field for error messages
        self.err_msg = wx.StaticText(self, label="")
        self.err_msg.SetForegroundColour((255, 0, 0))  # make text red
        self.main_sizer.Add(self.err_msg, flag=wx.LEFT, border=25)

        analyze_btn = wx.Button(self, label='Analyze page')
        analyze_btn.Bind(wx.EVT_BUTTON, self.on_button_press)
        self.main_sizer.Add(analyze_btn, flag=wx.ALL | wx.CENTER, border=5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.scripts_panel = ScrolledPanel(self, size=(375, 550))
        self.scripts_panel.SetupScrolling()
        hbox.Add(self.scripts_panel)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.content_panel = ScrolledPanel(self, size=(375, 550))
        self.content_panel.SetupScrolling()
        vbox.Add(self.content_panel, flag=wx.CENTER, border=5)
        hbox.Add(vbox)
        self.main_sizer.Add(hbox, flag=wx.CENTER | wx.BOTTOM, border=25)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_btn = wx.Button(self, label='Apply Selection')
        self.apply_btn.Bind(wx.EVT_BUTTON, self.on_button_press)
        self.apply_btn.SetToolTip('Preview changes in the browser window.')
        self.apply_btn.Hide()
        hbox.Add(self.apply_btn, border=5)

        self.save_btn = wx.Button(self, label='Save Changes')
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_button_press)
        self.save_btn.SetToolTip('Push changes to the remote proxy.')
        self.save_btn.Hide()
        hbox.Add(self.save_btn, border=5)

        self.diff_btn = wx.Button(self, label='Get diff')
        self.diff_btn.Bind(wx.EVT_BUTTON, self.on_button_press)
        self.diff_btn.SetToolTip(
            'Print diff before and after changes to terminal window.')
        self.diff_btn.Hide()
        hbox.Add(self.diff_btn, border=5)
        self.main_sizer.Add(hbox, flag=wx.BOTTOM | wx.CENTER, border=25)

        self.SetSizer(self.main_sizer)
        self.url = self.url_input.GetValue()
        self.suffix = "?JSTool=none"
        self.script_sizer = wx.BoxSizer(wx.VERTICAL)
        self.script_buttons = []
        self.choice_boxes = []
        self.number_of_buttons = 0
        self.blocked_urls = []

        self.content_panel.Hide()

        self.content_text = ExpandoTextCtrl(
            self.content_panel, size=(375, 275), style=wx.TE_READONLY)
        self.content_text.SetValue("Script code")
        self.Bind(EVT_ETC_LAYOUT_NEEDED, None, self.content_text)

        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.content_sizer.Add(self.content_text, flag=wx.CENTER)
        self.content_panel.SetSizer(self.content_sizer)

        self.script_tree = AnyNode(id='root')
        self.images = {}

    def on_button_press(self, event):
        """Handle wx.Button press."""
        btn = event.GetEventObject()
        if btn.GetLabel() == 'Analyze page':
            self.analyze()
        elif btn == self.diff_btn:
            self.on_diff_press()
        elif btn == self.apply_btn:
            self.on_apply_press()
        elif btn == self.save_btn:
            self.on_save()

    def on_key_press(self, event):
        """Handle keyboard input."""
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
            self.analyze()
        else:
            event.Skip()

    def add_button(self, script, index, depth):  # copies
        """Add script to self.script_buttons at index and update display."""
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddSpacer(depth*25)
        # Create button
        # if copies > 1: do something to differentiate it
        self.script_buttons.insert(index, wx.CheckBox(
            self.scripts_panel, label=script.split("/")[-1][:9]))
        self.script_buttons[index].myname = script
        self.script_buttons[index].Bind(
            wx.EVT_CHECKBOX, self.on_script_press)
        self.script_buttons[index].SetToolTip(script)
        hbox.Add(self.script_buttons[index], flag=wx.ALL, border=5)
        self.number_of_buttons += 1

        # Create combobox
        # choice_box = wx.ComboBox(self.scripts_panel, value="", style=wx.CB_READONLY, choices=(
        #     "", "critical", "non-critical", "translatable"))
        # choice_box.Bind(wx.EVT_COMBOBOX, self.on_choice)
        # choice_box.index = len(self.choice_boxes)
        # self.choice_boxes.insert(index, choice_box)

        # hbox.Add(choice_box, flag=wx.ALL, border=5)
        # self.number_of_buttons += 1

        # Add labels
        matches = DOMAINS.get(script)
        if matches:
            for domain in matches:
                category = domain['categories'][0]
                name = domain['name']
                label = wx.StaticText(self.scripts_panel,
                                      label=category, style=wx.BORDER_RAISED)
                label.SetBackgroundColour(tuple(CATEGORIES[category]['color']))
                tool_tip = "Domain name: " + name + "\n" + \
                    CATEGORIES[category]['description']
                label.SetToolTip(tool_tip)
                hbox.Add(label, flag=wx.ALL, border=5)

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

    def get_response_body(self, request_id, content_type):
        """Return body of response with request_id."""
        try:
            response_body = self.driver.execute_cdp_cmd(
                'Network.getResponseBody',
                {'requestId': str(request_id)}
            )
        except WebDriverException as error:
            logging.error(str(error))
            return
        body = response_body['body']
        try:
            if response_body['base64Encoded']:
                logging.info('decoding body')
                # not yet tested
                body = base64.b64decode(body)
        except KeyError as error:
            logging.exception(str(error))
        if content_type == 'script':
            body = jsbeautifier.beautify(body)
        return body

    def block_all_scripts(self):
        """Adds all scripts in self.script_tree to self.blocked_urls."""
        self.blocked_urls.clear()
        for node in PreOrderIter(self.script_tree):
            if node.id[:6] != "script" and not node.is_root:
                self.blocked_urls.append(node.id)

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
            # self.diff_btn.Show()
            self.apply_btn.Show()
            self.content_panel.Show()
            self.content_text.SetValue("Script code")
            while self.script_sizer.GetChildren():
                self.script_sizer.Hide(0)
                self.script_sizer.Remove(0)
            self.images.clear()

        def get_index_html():
            # Get index.html from proxy
            return get_resource(self.url)

        def parse_html(html):
            # Add index.html scripts to self.script_tree
            cnt = 1
            while "<script" in html:
                src = ""
                script_name = "script" + str(cnt)
                start_index = html.find("<script")
                end_index = html.find("</script>")
                text = html[start_index:end_index + 9]
                new_node = AnyNode(
                    id=script_name, parent=self.script_tree, content=text, count=1)
                if ' src="' in text:  # BeautifulSoup turns all single quotes into double quotes
                    src = text.split(' src="')[1].split('"')[0]
                    src = self.format_src(src)
                    node = anytree.cachedsearch.find(
                        self.script_tree, lambda node: node.id == src)
                    if node:
                        node.parent = new_node
                html = html.replace(text, "\n<!--" + script_name + "-->\n")
                cnt += 1

        def create_buttons():
            # Add checkboxes to display
            # Check all
            self.add_button('Check all', 0, 1)

            index = 1
            # All other script checkboxes
            for node in PreOrderIter(self.script_tree):
                if node.is_root:
                    continue
                node.button = index
                self.add_button(node.id, index, node.depth)  # node.count
                index += 1
            self.scripts_panel.SetSizer(self.script_sizer)
            self.frame.frame_sizer.Layout()

        def display_loading_message():
            # Never managed to get this part to display before spinning wheel of death
            self.err_msg.SetForegroundColour((0, 0, 0))
            self.err_msg.SetLabel("Loading page... please wait")
            self.err_msg.SetForegroundColour((255, 0, 0))
            self.Update()

        def similarity(similarity_threshold):
            # Print script pairs in self.script_tree with Jaccard similarity > similarity_threshold
            names = []
            scripts = []
            for node in PreOrderIter(self.script_tree):
                if node.is_root:
                    continue
                names.append(node.id)
                scripts.append(node.content)
            results = similarity_comparison(scripts, similarity_threshold)
            logging.info("---" * 20)
            logging.info('scripts with similarity > %d', similarity_threshold)
            for tup in results:
                logging.info(names[tup[0]], names[tup[1]], tup[2])

        def compare_image_sizes(images):
            # Print difference in original and rendered image sizes for image URLs in images
            for url in images:
                body = get_resource(url)
                try:
                    stream = BytesIO(body)
                except TypeError:
                    logging.warning("body in %s, not in bytes", type(body))
                    stream = BytesIO(body.encode(ENCODING))
                try:
                    width, height = get_image_size_from_bytesio(
                        stream, DEFAULT_BUFFER_SIZE)
                    self.images[url] = {}
                    self.images[url]['ow'] = width
                    self.images[url]['oh'] = height
                except UnknownImageFormat as error:
                    logging.exception(str(error))
                except struct.error as error:
                    logging.error(str(error))

            for img in self.driver.find_elements_by_tag_name('img'):
                url = img.get_attribute('src')
                if url not in self.images.keys():
                    self.images[url] = {}
                self.images[url]['rw'] = img.size['width']
                self.images[url]['rh'] = img.size['height']

            logging.info("---" * 20)
            logging.info("potential improvements:")
            for url, dimensions in self.images.items():
                if len(dimensions.keys()) == 4:
                    # Successfully parsed original and rendered dimensions
                    logging.info(url)
                    logging.info("original: %d x %d",
                                 dimensions['ow'], dimensions['oh'])
                    logging.info("rendered: %d x %d",
                                 dimensions['rw'], dimensions['rh'])

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
        scripts, images = self.parse_log(epoch_in_milliseconds)
        for script in scripts:
            # pylint: disable=undefined-loop-variable
            # pylint: disable=cell-var-from-loop
            parent = anytree.cachedsearch.find(self.script_tree,
                                               lambda node: node.id == script['parent'])
            # Check if this node already exists
            node = anytree.cachedsearch.find(self.script_tree,
                                             lambda node: node.id == script['url'])
            if node and node.parent == parent:
                logging.warning('duplicate script! %s', script['url'])
                node.count += 1
            else:
                AnyNode(id=script['url'], parent=parent,
                        content=script['content'], count=1)
        # self.print_scripts()

        # Check image differences
        compare_image_sizes(images)

        # Parse inline scripts
        html = get_index_html()
        parse_html(html)
        self.print_scripts()

        # Check similarity
        similarity(0.8)

        # Create buttons
        create_buttons()

        # Get page with all scripts removed
        self.block_all_scripts()
        self.driver.execute_cdp_cmd('Network.setBlockedURLs',
                                    {'urls': self.blocked_urls})
        try:
            self.driver.get(self.url + self.suffix)
            self.err_msg.SetLabel("")
        except InvalidArgumentException as exception:
            self.err_msg.SetLabel(str(exception))
            return

        # Used for diff
        final_html = BeautifulSoup(self.driver.execute_script(
            "return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')
        file_stream = open("before.html", "w")
        file_stream.write(final_html.prettify())
        file_stream.close()

    def on_check_all(self, toggle):
        """Handle 'Select All' checkbox toggle."""
        self.suffix = "?JSTool="
        for btn in self.script_buttons:
            btn.SetValue(toggle)
            if toggle and btn.myname[:6] == "script":
                self.suffix += "_" + btn.myname[6:]

        if toggle:
            # Toggle all script buttons
            self.blocked_urls.clear()
        else:
            # Untoggle all script buttons
            self.block_all_scripts()
            self.suffix += "none"

    def on_apply_press(self):
        """Send request for page with changes."""
        self.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': self.blocked_urls})
        self.suffix = "?JSTool="
        for btn in self.script_buttons:
            if btn.GetValue() and btn.myname[:6] == "script":
                self.suffix += "_" + btn.myname[6:]
        if self.suffix == "?JSTool=":
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
            except brotli.error as error:
                logging.error(str(error))
            content_text = jsbeautifier.beautify(content_text)
            return content_text

        def extract_features(content_text):
            """Return vectorization of features in content_text."""
            tmp = {}
            for feature in FEATURES:
                if '|' not in feature:
                    tmp[feature] = content_text.count("."+feature+"(") + content_text.count("."+feature+" (")
            for feature in FEATURES:
                if '|' in feature:
                    feats = feature.split('|')
                    res = 1
                    for feat in feats:
                        try:
                            if tmp[feat] == 0:
                                res = 0
                                break
                        except KeyError:
                            if content_text.count("."+feat+"(") + content_text.count("."+feat+" (") == 0:
                                res = 0
                                break
                    tmp[feature] = res
            vector = []
            for feature in FEATURES:
                vector.append(tmp[feature])
            return vector

        name = event.GetEventObject().myname
        toggle = event.GetEventObject().GetValue()
        if name == 'Check all':
            self.on_check_all(toggle)
            return
        node = anytree.cachedsearch.find(
            self.script_tree, lambda node: node.id == name)

        if not get_attribute(node, 'content'):
            node.content = get_content_from_src(node.id)
        if not get_attribute(node, 'features'):
            node.features = extract_features(node.content)

        self.content_text.SetValue(name + "\n\n" + node.content)
        logging.debug(node.features)

        if toggle:
            while node.depth > 1:
                self.script_buttons[node.button].SetValue(True)
                try:
                    self.blocked_urls.remove(node.id)
                except ValueError:
                    logging.debug("Could not remove %s", node.id)
                node = node.parent
            self.script_buttons[node.button].SetValue(True)
            if node.id[:6] != "script":
                self.blocked_urls.remove(node.id)
        else:
            for descendant in node.descendants:
                self.script_buttons[descendant.button].SetValue(False)
                self.blocked_urls.append(descendant.id)
            if node.id[:6] != "script":
                self.blocked_urls.append(node.id)

    def on_diff_press(self):
        """Print diff to terminal."""

        after = BeautifulSoup(self.driver.execute_script(
            "return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')
        try:
            file_stream = open("after.html", "r")
            before = file_stream.read()
            file_stream.close()
            file_stream = open("before.html", "w")
            file_stream.write(before)
            file_stream.close()
            before = BeautifulSoup(before, 'html.parser')
        except IOError:
            pass
        file_stream = open("after.html", "w")
        file_stream.write(after.prettify())
        file_stream.close()
        os.system(r"git diff --no-index before.html after.html")
        # os.system(r"diff before.html after.html | sed '/<!--script/,/<\/script>/d'")

    def on_save(self):
        """Send report using Apache CGI Web Call."""

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
        images = []
        log = self.driver.get_log('performance')
        log = log[bisect.bisect_left(
            [entry['timestamp'] for entry in log], epoch_in_milliseconds):]
        log = [json.loads(entry['message'])['message'] for entry in log]

        def is_script_request(message):
            if message['method'] == 'Network.requestWillBeSent':
                if message['params']['type'] == 'Script':
                    return True
            return False

        def is_image_request(message):
            if message['method'] == 'Network.requestWillBeSent':
                if message['params']['type'] == 'Image':
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
                if initiator['stack']['callFrames']:
                    initiator = initiator['stack']['callFrames'][-1]['url']
            return [request_id, request_url, initiator]

        script_requests = []
        # script_responses = []
        image_requests = []
        data_received = []
        for message in log:
            if is_script_request(message):
                script_requests.append(message)
            # elif is_script_response(message):
            #     script_responses.append(message['params']['requestId'])
            elif is_image_request(message):
                image_requests.append(message)
            elif is_data_received(message):
                data_received.append(message['params']['requestId'])

        for request in script_requests:
            request_id, url, initiator = get_request_info(request)
            if request_id in data_received:
                # content = self.get_response_body(request_id, 'script')
                content = ""
                scripts.append(
                    {'url': url, 'parent': initiator, 'content': content})

        for request in image_requests:
            request_id, url, initiator = get_request_info(request)
            if request_id in data_received:
                images.append(url)

        return (scripts, images)

    def print_scripts(self):
        """Print script tree."""
        print(RenderTree(self.script_tree).by_attr('id'))
        print("---" * 20)

    def print_blocked_scripts(self):
        """Print blocked URLs."""
        print('BLOCKED SCRIPTS:')
        for url in self.blocked_urls:
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
    logging.basicConfig(level=logging.DEBUG)  # logging.INFO
    app = wx.App(False)
    # width, height = wx.GetDisplaySize()
    frame = MyFrame()
    frame.SetSize(800, 825)
    # frame.SetMaxSize(wx.Size(800, 825))
    # frame.SetMinSize(wx.Size(800, 825))
    # frame.SetPosition((25, 25))

    app.MainLoop()
    if os.path.isfile("after.html"):
        os.remove("after.html")
    if os.path.isfile("before.html"):
        os.remove("before.html")
    frame.panel.driver.quit()


if __name__ == "__main__":
    main()
