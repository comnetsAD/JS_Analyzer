#-*- coding: utf-8 -*-
import wx
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
import wx.lib.scrolledpanel
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
import jsbeautifier
from collections import OrderedDict
import gzip, shutil, brotli, os, json, time
import io
from time import sleep
import requests
# from browsermobproxy import Server

proxy_IP = "10.224.41.171"
proxy_port = 8080

# proxy variables
http_proxy = "http://" + proxy_IP + ":" + str(proxy_port)
https_proxy = "https://" + proxy_IP + ":" + str(proxy_port)
proxyDict = {"http":http_proxy, "https":https_proxy}

# feature store (60 features)
features = [".lookupPrefix",".prefix",".childNodes",".open",".isEqualNode",".documentURI",".lastChild",".nodeName",".title",".implementation",".normalizeDocument",".forms",".input",".anchors",".createCDATASection",".URL",".getElementsByTagName",".createEntityReference",".domConfig",".createElement",".xmlStandalone",".referrer",".textContent",".doctype",".namespaceURI",".strictErrorChecking",".xmlEncoding",".appendChild",".domain",".createAttribute",".links",".adoptNode",".Type",".nextSibling",".firstChild",".images",".close",".xmlVersion",".event",".form",".createComment",".removeChild",".nodeValue",".localName",".ownerDocument",".previousSibling",".body",".isDefaultNamespace",".nodeType",".track",".isSameNode",".cookie",".createDocumentFragment",".getElementsByName",".baseURI",".lookupNamespaceURI",".parentNode",".getElementById",".attributes",".createTextNode"]

class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.colors = {"":wx.Colour(255, 255, 255, 100), "critical":wx.Colour(255, 0, 0, 100), "non-critical":wx.Colour(0, 255, 0, 100),"translatable":wx.Colour(0, 0, 255, 100)}
        self.frame = parent
        self.fileName = ""
 
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.url_input = wx.TextCtrl(self, style=wx.TE_LEFT)
        self.url_input.SetValue("http://yasirzaki.net")
        self.url_input.Bind(wx.EVT_KEY_DOWN, self.on_key_press)
        self.mainSizer.Add(self.url_input, flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=25)

        # StaticText field for error messages
        self.err_msg = wx.StaticText(self, label="")
        self.err_msg.SetForegroundColour((255,0,0)) # make text red
        self.mainSizer.Add(self.err_msg, 0, flag=wx.LEFT, border=25)

        analyze_btn = wx.Button(self, label='Analyze page')
        analyze_btn.Bind(wx.EVT_BUTTON, self.on_analyze_press)
        self.mainSizer.Add(analyze_btn, 0, wx.ALL | wx.CENTER, 25)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.scripts_panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, size=(375,550))
        self.scripts_panel.SetupScrolling()
        # self.scripts_panel.Hide()
        # self.scripts_panel.SetBackgroundColour('#FFFFFF')
        hbox.Add(self.scripts_panel, 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.features_panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, size=(375,275))
        self.features_panel.SetupScrolling()
        # self.features_panel.SetBackgroundColour('#FFFFFF')
        vbox.Add(self.features_panel, 0, wx.CENTER, 5)
        
        self.content_panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, size=(375,275))
        self.content_panel.SetupScrolling()
        # self.content_panel.SetBackgroundColour('#FFFFFF')
        vbox.Add(self.content_panel, 0, wx.CENTER, 5)
        hbox.Add(vbox, 0)
        self.mainSizer.Add(hbox, 0, wx.CENTER | wx.BOTTOM, 25)

        self.select_all_btn = wx.ToggleButton(self, label='Select All')
        self.select_all_btn.Bind(wx.EVT_TOGGLEBUTTON, self.on_all_press)
        self.select_all_btn.Hide()
        self.mainSizer.Add(self.select_all_btn, 0, wx.BOTTOM | wx.CENTER, 25)

        self.diff_btn = wx.Button(self, label='Get diff')
        self.diff_btn.Bind(wx.EVT_BUTTON, self.on_diff_press)
        self.diff_btn.Hide()
        self.mainSizer.Add(self.diff_btn, 0, wx.BOTTOM | wx.CENTER, 25)

        self.SetSizer(self.mainSizer)
        self.gs = None

        # self.features_panel.Hide()
        # self.content_panel.Hide()

        self.features_text = ExpandoTextCtrl(self.features_panel, size=(375,275), style=wx.TE_READONLY)
        self.features_text.SetValue("Features listing")
        self.Bind(EVT_ETC_LAYOUT_NEEDED, None, self.features_text)

        self.features_sizer = wx.BoxSizer(wx.VERTICAL)
        self.features_sizer.Add(self.features_text, 0, wx.CENTER, 0)
        self.features_panel.SetSizer(self.features_sizer)

        self.content_text = ExpandoTextCtrl(self.content_panel, size=(375,275), style=wx.TE_READONLY)
        self.content_text.SetValue("Script code")
        self.Bind(EVT_ETC_LAYOUT_NEEDED, None, self.content_text)

        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.content_sizer.Add(self.content_text, 0, wx.CENTER, 0)
        self.content_panel.SetSizer(self.content_sizer)

    def on_analyze_press(self, event):
        self.analyze()

    def on_key_press(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
            self.analyze()
        else:
            event.Skip()

    def analyze(self):
        self.url = self.url_input.GetValue()
        self.suffix = "?JSTool=none"

        if not self.url:
            return

        # Get all scripts from original page and parse selenium rendered version
        try:
            driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': []})
            driver.get(self.url)
            self.err_msg.SetLabel("")
        except Exception as e:
            self.err_msg.SetLabel(str(e))
            print(e)
            return

        self.seleniumScripts = []
        html = BeautifulSoup(driver.page_source, 'html.parser').prettify()
        cnt = 0
        print('number of selenium scripts:')
        numScripts = html.count("<script")
        print(numScripts)
        if numScripts == 0:
            print(html)

        while "<script" in html:
            src = ""
            sIndex = html.find("<script")
            eIndex = html.find("</script>")
            text = html[sIndex:eIndex+9]

            html = html.replace(text,"\n<!--script"+str(cnt)+"-->\n")

            self.seleniumScripts.append(jsbeautifier.beautify(text))

            cnt += 1

        html = ""
        # End selenium-rendered parsing

        self.select_all_btn.Show()

        # Uncomment to show diff button
        # self.diff_btn.Show()
        
        self.select_all_btn.SetValue(False)
        self.features_panel.Show()
        self.content_panel.Show()
        self.features_text.SetValue("Features listing")
        self.content_text.SetValue("Script code")

        self.JavaScripts = {}
        self.scriptButtons = []
        self.choiceBoxes = []

        self.number_of_buttons = 0

        while self.gs != None and len(self.gs.GetChildren()) > 0:
            self.gs.Hide(0)
            self.gs.Remove(0)
            self.frame.fSizer.Layout()

        # Get index.html from proxy
        req = requests.get(self.url, proxies=proxyDict, verify=False)
        if req.status_code != requests.codes.ok:
            print("Could not get request")
        
        html = BeautifulSoup(req.text, 'html.parser').prettify()

        if req.headers['content-encoding'] == 'br':
            html = BeautifulSoup(brotli.decompress(req.content), 'html.parser').prettify()

        # Here is the part which extracts Scripts
        numScripts = html.count("<script")
        if numScripts == 0:
            print(html)

        # Create display to house script buttons
        self.gs = wx.BoxSizer(wx.VERTICAL)

        # Add scripts to self.JavaScripts and create buttons
        cnt = 0
        while "<script" in html:
            src = ""
            sIndex = html.find("<script")
            eIndex = html.find("</script>")
            text = html[sIndex:eIndex+9]
            contentText = text
            if ' src="' in text: # BeautifulSoup turns all single quotes into double quotes
                src = text.split(' src="')[1].split("?")[0]
                if src[:4] != "http":
                    if src[0] == "/":
                        src = self.url + src
                    else:
                        src = self.url + "/" + src
                contentText = ""

                print("getting " + src)
                req = requests.get(src, proxies=proxyDict, verify=False)
                contentText = req.text

                print (contentText[:500])
            # contentText = jsbeautifier.beautify(contentText)
            
            print ("---"*20)

            html = html.replace(text,"\n<!--script"+str(cnt)+"-->\n")
            text = jsbeautifier.beautify(text)
            print("SCRIPT #", cnt)
            print(text[:200])

            hbox = wx.BoxSizer(wx.HORIZONTAL)
            # create button
            self.scriptButtons.append(wx.ToggleButton(self.scripts_panel, label="script"+str(cnt)))
            self.scriptButtons[cnt].Bind(wx.EVT_TOGGLEBUTTON, self.on_script_press)
            self.scriptButtons[cnt].myname = "script"+str(cnt)
            hbox.Add(self.scriptButtons[cnt], 0, wx.ALL, 5)
            self.number_of_buttons += 1

            # create combobox
            choiceBox = wx.ComboBox(self.scripts_panel, value="", style=wx.CB_READONLY, choices=("","critical","non-critical","translatable"))
            choiceBox.Bind(wx.EVT_COMBOBOX, self.OnChoice)
            choiceBox.index = len(self.choiceBoxes)
            self.choiceBoxes.append(choiceBox)

            hbox.Add(choiceBox, 0, wx.ALL, 5)
            self.number_of_buttons += 1

            self.gs.Add(hbox, 0)

            # extract features
            tmp = {}
            for feature in features:
                if feature in contentText:
                    tmp[feature] = contentText.count(feature)
            tmp_sorted = OrderedDict(sorted(tmp.items(), key=lambda x: x[1], reverse=True))
            tmp = ""
            for k, v in tmp_sorted.items():
                tmp += "{0}: {1}\n".format(k,v) 

            self.JavaScripts["script"+str(cnt)] = [tmp, contentText, text, src]

            cnt += 1

        self.scripts_panel.SetSizer(self.gs)
        self.frame.fSizer.Layout()

        self.scriptURLs = []
        for script in self.JavaScripts:
            src = self.JavaScripts[script][3]
            if src != "":
                self.scriptURLs.append(src)

        # Get page with all scripts removed
        try:
            driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': ['*.js']})
            driver.get(self.url + self.suffix)
            self.err_msg.SetLabel("")
        except Exception as e:
            self.err_msg.SetLabel(str(e))
            print(e)
            return

        # for diff
        final_html = BeautifulSoup(driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')
        f = open("before.html", "w")
        f.write(final_html.prettify())
        f.close()

        # map selenium script number to that in index.html
        for script in self.JavaScripts:
            if self.JavaScripts[script][2] in self.seleniumScripts:
                i = self.seleniumScripts.index(self.JavaScripts[script][2])
                self.seleniumScripts[i] = script

        self.print_selenium_scripts()

        print('scripts blocked:')
        print(self.scriptURLs)
        print ("---"*20)

    def on_all_press(self, event):
        try:
            toggle = event.GetEventObject().GetValue()
        except:
            toggle = True

        self.suffix = "?JSTool="
        self.scriptURLs.clear()

        if toggle:
            # Toggle all script buttons
            for i, btn in enumerate(self.scriptButtons):
                btn.SetValue(True)
                self.suffix += "_" + str(i)

        else:
            # Untoggle all script buttons
            for btn in self.scriptButtons:
                btn.SetValue(False)

            # Block all external scripts
            for script in self.JavaScripts:
                src = self.JavaScripts[script][3]
                if src != "":
                    self.scriptURLs.append(src)

            self.suffix += "none"

        driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': self.scriptURLs})
        t = time.time()*1000
        driver.get(self.url + self.suffix)
        self.parse_log(t)

    def on_script_press(self, event):
        try:
            name = event.GetEventObject().myname
            toggle = event.GetEventObject().GetValue()
        except:
            name = "script0"
            toggle = True

        if toggle:
            JSContent = jsbeautifier.beautify(self.JavaScripts[name][1])
            self.features_text.SetValue(name + "\n\n" + self.JavaScripts[name][0])
            self.content_text.SetValue(JSContent)
            if self.JavaScripts[name][3] != "":
                self.scriptURLs.remove(self.JavaScripts[name][3])

        else:
            self.select_all_btn.SetValue(False)
            self.features_text.SetValue("")
            self.content_text.SetValue("")
            if self.JavaScripts[name][3] != "":
                self.scriptURLs.append(self.JavaScripts[name][3])

        self.suffix = "?JSTool="
        numActive = 0
        for i, btn in enumerate(self.scriptButtons):
            if btn.GetValue() == True:
                self.suffix += "_" + str(i)
                numActive += 1
        if len(self.suffix) == 8:
            self.suffix += "none"

        driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': self.scriptURLs})
        t = time.time()*1000
        driver.get(self.url + self.suffix)
        self.parse_log(t)

    def on_diff_press(self, event):
        final_html = BeautifulSoup(driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')
        try:
            f = open("after.html", "r")
            before = f.read()
            f.close()
            f = open("before.html", "w")
            f.write(before)
            f.close()
        except IOError:
            pass
        f = open("after.html", "w")
        f.write(final_html.prettify())
        f.close()
        os.system("diff before.html after.html | sed '/<!--script/,/<\/script>/d'")

    def OnChoice(self, event): 
        choiceBox = self.choiceBoxes[event.GetEventObject().index]
        choiceBox.SetBackgroundColour(self.colors[choiceBox.GetValue()])

    def parse_log(self, time):
        log = driver.get_log('performance')
        for entry in reversed(log):
            # only look at logs since time
            if entry['timestamp'] < time:
                break
            message = json.loads(entry['message'])['message']
            if message['method'] == 'Network.responseReceived':
                response = message['params']['response']
                content_type = response['mimeType']
                # content_type can also be found in response['headers']['content-type'] or response['headers']['Content-Type']
                # headers = response['headers']
                url = response['url']
                if 'javascript' in content_type:
                    print(url)
                    requestId = message['params']['requestId']
                    try:
                        responseBody = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': str(requestId)})
                        try:
                            # if responseBody['base64Encoded'] == True: decode first
                            if responseBody['base64Encoded'] == False:
                                content = jsbeautifier.beautify(responseBody['body'])
                                if content in self.seleniumScripts:
                                    i = self.seleniumScripts.index(content)
                                    self.seleniumScripts[i] = "from " + url + "\n" + self.seleniumScripts[i]
                            else:
                                print('need to decode body first')
                        except KeyError:
                            print(responseBody)
                    except Exception as e:
                        print(str(e))
                        print(requestId)
                        print(json.dumps(message['params'], indent=4, sort_keys=True))

            #print(json.dumps(message, indent=2, sort_keys=True))

    def print_selenium_scripts(self):
        # print mappings
        for i in range(len(self.seleniumScripts)):
            print("Selenium script #", i)
            print(self.seleniumScripts[i][:200])
            print("----------------------------")


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="JS Cleaner")
        
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        exitMenuItem = fileMenu.Append(101, "Exit", "Exit the application")
        aboutMenuItem = fileMenu.Append(102, "About", "About")

        menuBar.Append(fileMenu, "&File")
        self.Bind(wx.EVT_MENU, self.onExit, exitMenuItem)
        self.Bind(wx.EVT_MENU, self.onAbout, aboutMenuItem)
        self.SetMenuBar(menuBar)

        self.fSizer = wx.BoxSizer(wx.VERTICAL)
        panel = MyPanel(self)
        self.fSizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(self.fSizer)
        self.Fit()
        self.Show()

    def onExit(self, event):
        self.Close()

    def onAbout(self, event):
        msg = wx.MessageDialog(self, "This tool is built for JS analyses by the ComNets AD lab @ NYUAD. September 2019.","About",wx.OK | wx.ICON_INFORMATION)
        msg.ShowModal()

if __name__ == "__main__":
    app = wx.App(False)
    width, height = wx.GetDisplaySize()

    frame = MyFrame()
    frame.SetSize(800, 800)
    frame.SetMaxSize(wx.Size(800, 800))
    frame.SetMinSize(wx.Size(800, 800))

    PROXY = proxy_IP + ":" + str(proxy_port)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=%s' % PROXY)
    chrome_options.add_argument('--auto-open-devtools-for-tabs')
    caps = DesiredCapabilities.CHROME
    caps["goog:loggingPrefs"] = {"performance": "INFO"}
    chrome_options.add_experimental_option('perfLoggingPrefs', {"enablePage": True})
    # chrome_options.add_argument('--enable-devtools-experiments')

    driver = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)
    driver.execute_cdp_cmd('Network.enable', {})
    driver.execute_cdp_cmd('Network.setCacheDisabled', {'cacheDisabled': True})

    app.MainLoop()
    driver.quit()
    if os.path.isfile("after.html"):
        os.remove("after.html")
    if os.path.isfile("before.html"):
        os.remove("before.html")
