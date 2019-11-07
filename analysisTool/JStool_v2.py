#-*- coding: utf-8 -*-
import wx
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
import wx.lib.scrolledpanel
import lorem
from selenium import webdriver
from bs4 import BeautifulSoup, Tag
import jsbeautifier
from collections import OrderedDict, namedtuple
import gzip, shutil, pymysql, zlib, brotli, os
from io import StringIO
import io
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import binascii
from time import sleep
import config
import requests
import time

name = "jacinta"

# read DB user name and password
db_name = "mydb_mitmjscleaner"
db_user = "jscleaner"
db_password = config.users[name].password

proxy_IP = "10.224.41.171"
proxy_port = 8080

# proxy variables
http_proxy = "http://" + proxy_IP + ":" + str(proxy_port)
https_proxy = "https://" + proxy_IP + ":" + str(proxy_port)
proxyDict = {"http":http_proxy, "https":https_proxy}

# feature store (60 features)
features = [".lookupPrefix",".prefix",".childNodes",".open",".isEqualNode",".documentURI",".lastChild",".nodeName",".title",".implementation",".normalizeDocument",".forms",".input",".anchors",".createCDATASection",".URL",".getElementsByTagName",".createEntityReference",".domConfig",".createElement",".xmlStandalone",".referrer",".textContent",".doctype",".namespaceURI",".strictErrorChecking",".xmlEncoding",".appendChild",".domain",".createAttribute",".links",".adoptNode",".Type",".nextSibling",".firstChild",".images",".close",".xmlVersion",".event",".form",".createComment",".removeChild",".nodeValue",".localName",".ownerDocument",".previousSibling",".body",".isDefaultNamespace",".nodeType",".track",".isSameNode",".cookie",".createDocumentFragment",".getElementsByName",".baseURI",".lookupNamespaceURI",".parentNode",".getElementById",".attributes",".createTextNode"]

# decoding functions
def decode_gzip(filepath):
    f = open (filepath + ".c", "rb")
    return gzip.GzipFile('', 'rb', 9, io.BytesIO(f.read())).read()

def decode_br_content(filepath):
    f = open (filepath + ".c", "rb")
    return brotli.decompress( f.read())

def getScriptText(filename):
    encoding = None
    contentText = ""

    with open(PROXY_DATA_PATH+filename + ".h") as f:
        for line in f:
            if "Content-Encoding:" in line:
                encoding = line.split(' ',1)[1]

    if encoding != None:
        # Decode gzip
        if "gzip" in encoding:
            contentText = decode_gzip(PROXY_DATA_PATH+filename).decode(encoding='utf-8', errors='ignore')

        # Decode br
        if "br" in encoding:
            contentText = decode_br_content(PROXY_DATA_PATH+filename).decode(encoding='utf-8', errors='ignore')
    else:
        f = open(PROXY_DATA_PATH+filename+".c", "r", encoding='utf-8', errors='ignore')
        contentText = f.read()
        f.close()

    return contentText

class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.number_of_buttons = 0
        self.colors = {"":wx.Colour(255, 255, 255, 100), "critical":wx.Colour(255, 0, 0, 100), "non-critical":wx.Colour(0, 255, 0, 100),"translatable":wx.Colour(0, 0, 255, 100)}
        self.frame = parent
        self.fileName = ""
 
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.url_input = wx.TextCtrl(self, style=wx.TE_LEFT)
        self.url_input.SetValue("https://www.google.com")
        self.url_input.Bind(wx.EVT_KEY_DOWN, self.on_key_press)
        self.mainSizer.Add(self.url_input, flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, border=25)

        # StaticText field for error messages
        self.err_msg = wx.StaticText(self, label="")
        self.err_msg.SetForegroundColour((255,0,0)) # make text red
        self.mainSizer.Add(self.err_msg, 0, flag=wx.LEFT, border=25)

        analyze_btn = wx.Button(self, label='Analyze page')
        analyze_btn.Bind(wx.EVT_BUTTON, self.on_analyze_press)
        self.mainSizer.Add(analyze_btn, 0, wx.ALL | wx.CENTER, 25)

        self.scripts_panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, size=(750,400))
        self.scripts_panel.SetupScrolling()
        # self.scripts_panel.Hide()
        # self.scripts_panel.SetBackgroundColour('#FFFFFF')
        self.mainSizer.Add(self.scripts_panel, 0, wx.CENTER | wx.BOTTOM, 25)

        self.select_all_btn = wx.ToggleButton(self, label='Select All')
        self.select_all_btn.Bind(wx.EVT_TOGGLEBUTTON, self.on_all_press)
        self.select_all_btn.Hide()
        self.mainSizer.Add(self.select_all_btn, 0, wx.BOTTOM | wx.CENTER, 25)

        self.diff_btn = wx.Button(self, label='Get diff')
        self.diff_btn.Bind(wx.EVT_BUTTON, self.on_diff_press)
        self.diff_btn.Hide()
        self.mainSizer.Add(self.diff_btn, 0, wx.BOTTOM | wx.CENTER, 25)

        vbox = wx.BoxSizer(wx.HORIZONTAL)
        self.features_panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, size=(375,300), style=wx.SIMPLE_BORDER)
        self.features_panel.SetupScrolling()
        self.features_panel.SetBackgroundColour('#FFFFFF')
        vbox.Add(self.features_panel, 0, wx.CENTER, 5)
        
        self.content_panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, size=(375,300), style=wx.SIMPLE_BORDER)
        self.content_panel.SetupScrolling()
        self.content_panel.SetBackgroundColour('#FFFFFF')
        vbox.Add(self.content_panel, 0, wx.CENTER, 5)
        self.mainSizer.Add(vbox, 0, wx.CENTER, 5)

        self.SetSizer(self.mainSizer)
        self.gs = None

        self.features_panel.Hide()
        self.content_panel.Hide()

        self.features_text = ExpandoTextCtrl(self.features_panel, size=(360,290), style=wx.TE_READONLY)
        self.features_text.SetValue("Features listing")
        self.Bind(EVT_ETC_LAYOUT_NEEDED, None, self.features_text)

        self.features_sizer = wx.BoxSizer(wx.VERTICAL)
        self.features_sizer.Add(self.features_text, 0, wx.CENTER, 5)
        self.features_panel.SetSizer(self.features_sizer)

        self.content_text = ExpandoTextCtrl(self.content_panel, size=(360,290), style=wx.TE_READONLY)
        self.content_text.SetValue("Script code")
        self.Bind(EVT_ETC_LAYOUT_NEEDED, None, self.content_text)

        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.content_sizer.Add(self.content_text, 0, wx.CENTER, 5)
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

        try:
            driver.get(self.url + self.suffix)
            self.err_msg.SetLabel("")
        except Exception as e:
            self.err_msg.SetLabel(str(e))
            print(e)
            return

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

        while self.gs != None and len(self.gs.GetChildren()) > 0:
            self.gs.Hide(self.number_of_buttons-1)
            self.gs.Remove(self.number_of_buttons-1)
            self.number_of_buttons -= 1
            self.frame.fSizer.Layout()

        # Get index.html from proxy
        req = requests.get(self.url, proxies=proxyDict, verify=False)
        if req.status_code != requests.codes.ok:
            print("Could not get request")
        
        html = req.text

        if req.headers['content-encoding'] == 'br':
            html = str(brotli.decompress(req.content))

        # Here is the part which extracts Scripts
        scripts = driver.find_elements_by_tag_name("script")
        numScripts = html.count("<script")
        if numScripts == 0:
            print(html)

        # Create display to house script buttons
        if numScripts%2 != 0:
            self.gs = wx.GridSizer(numScripts//2+1,4,5,5)
        else:
            self.gs = wx.GridSizer(numScripts//2,4,5,5)

        cnt = 0
        while "<script" in html:
            sIndex = html.find("<script")
            eIndex = html.find("</script>")
            text = html[sIndex:eIndex+9]
            print("SCRIPT #", cnt)
            print(text[:200])
            contentText = text
            if ' src="' in text or " src='" in text:
                if ' src="' in text:
                    src = text.split(' src=')[1].split('"')[1]
                else:
                    src = text.split(' src=')[1].split("'")[1]
                src = src.split("?")[0]
                if src[:4] != "http":
                    if src[0] == "/":
                        src = self.url + src
                    else:
                        src = self.url + "/" + src
                html = html.replace(text, "\n<!--script from " + src + "-->\n")
                contentText = ""

                print("getting " + src)
                req = requests.get(src, proxies=proxyDict, verify=False)
                contentText = req.text

                print (contentText[:500])

            else:
                contentText = text
            
            print ("---"*20)

            html = html.replace(text,"\n<!--script"+str(cnt)+"-->\n")
            self.scriptButtons.append(wx.ToggleButton(self.scripts_panel, label="script"+str(cnt), size=(100,25)))
            self.scriptButtons[cnt].Bind(wx.EVT_TOGGLEBUTTON, self.on_script_press)
            self.scriptButtons[cnt].myname = "script"+str(cnt)
            self.gs.Add(self.scriptButtons[cnt], 0, wx.LEFT|wx.TOP, 25)
            self.number_of_buttons += 1

            choiceBox = wx.ComboBox(self.scripts_panel, value="", style=wx.CB_READONLY, choices=("","critical","non-critical","translatable"))
            choiceBox.Bind(wx.EVT_COMBOBOX, self.OnChoice)
            choiceBox.index = len(self.choiceBoxes)
            self.choiceBoxes.append(choiceBox)

            self.gs.Add(choiceBox, 0, wx.TOP, 25)
            self.number_of_buttons += 1

            tmp = {}
            for feature in features:
                if feature in contentText:
                    tmp[feature] = contentText.count(feature)
            tmp_sorted = OrderedDict(sorted(tmp.items(), key=lambda x: x[1], reverse=True))
            tmp = ""
            for k, v in tmp_sorted.items():
                tmp += "{0}: {1}\n".format(k,v) 

            self.JavaScripts["script"+str(cnt)] = [tmp, contentText, text]
            cnt += 1

        self.scripts_panel.SetSizer(self.gs)
        self.frame.fSizer.Layout()

        final_html = BeautifulSoup(driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')
        f = open("before.html", "w")
        f.write(final_html.prettify())
        f.close()

    def on_all_press(self, event):
        try:
            toggle = event.GetEventObject().GetValue()
        except:
            toggle = True

        self.suffix = "?JSTool="

        if toggle:
            # Toggle all script buttons
            for i, btn in enumerate(self.scriptButtons):
                btn.SetValue(True)
                self.suffix += "_" + str(i)

        else:
            # Untoggle all script buttons
            for btn in self.scriptButtons:
                btn.SetValue(False)

            self.suffix += "none"

        driver.get(self.url + self.suffix)

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

        else:
            self.select_all_btn.SetValue(False)
            self.features_text.SetValue("")
            self.content_text.SetValue("")

        self.suffix = "?JSTool="
        numActive = 0
        for i, btn in enumerate(self.scriptButtons):
            if btn.GetValue() == True:
                self.suffix += "_" + str(i)
                numActive += 1
        if len(self.suffix) == 8:
            self.suffix += "none"
        driver.get(self.url + self.suffix)
        # req = requests.get(self.url + self.suffix, proxies=proxyDict, verify=False)
        # print(req.text)
        # print("Number of active scripts:", req.text.count("<script"))
        # print("Number of buttons pressed:", numActive)
        # print(driver.page_source)
        # print("Number of scripts after rendering:", driver.page_source.count("<script"))

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

    def OnChoice(self,event): 
        choiceBox = self.choiceBoxes[event.GetEventObject().index]
        choiceBox.SetBackgroundColour(self.colors[choiceBox.GetValue()])


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

    options = FirefoxOptions()
    options.log.level = "trace"
    options.add_argument("-devtools")

    # start selenium firefox web driver
    fp = webdriver.FirefoxProfile(config.users[name].profile)
    fp.set_preference("devtools.toolbox.selectedTool", "netmonitor")
    fp.set_preference("browser.cache.disk.enable", False)
    fp.set_preference("browser.cache.memory.enable", False)
    fp.set_preference("browser.cache.offline.enable", False)
    fp.set_preference("network.http.use-cache", False)
    driver = webdriver.Firefox(options=options, firefox_profile=fp)
    # driver = webdriver.Firefox(executable_path="./geckodriver", firefox_profile=fp)

    app.MainLoop()
    driver.quit()
    if os.path.isfile("after.html"):
        os.remove("after.html")
