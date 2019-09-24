#-*- coding: utf-8 -*-
import wx
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
import wx.lib.scrolledpanel
import lorem
from selenium import webdriver
from bs4 import BeautifulSoup, Tag
import jsbeautifier
from collections import OrderedDict
import gzip, shutil, pymysql, zlib, brotli, os
from io import StringIO
import io
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import binascii

# read DB user name and password
db_name = "JSCleaner"
db_user = "root"
db_password = "bremen2013" #input("please enter DB password ")

# proxy variables
http_proxy  = "http://127.0.0.1:9999"
https_proxy = "https://127.0.0.1:9999"
proxyDict = {"http":http_proxy, "https":https_proxy}

# proxy data path 
PROXY_DATA_PATH = os.getcwd() + "/../proxy/data/"

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
        #Decode gzip
        if "gzip" in encoding:
            contentText = decode_gzip(PROXY_DATA_PATH+filename).decode(encoding='utf-8', errors='ignore')

        #Decode br
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
        self.url_input.SetValue("http://www.irs.gov")
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
        self.mainSizer.Add(self.select_all_btn, 0, wx.LEFT | wx.BOTTOM | wx.CENTER, 25)

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
        if not self.url:
            return

        try:
            driver.get(self.url)
            self.err_msg.SetLabel("")
        except Exception as e:
            self.err_msg.SetLabel(str(e))
            print(e)
            return

        self.select_all_btn.Show()
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

        html_source = driver.page_source
        self.html = str(BeautifulSoup(html_source, 'html.parser'))

        #Here is the part which extracts Scripts
        scripts = driver.find_elements_by_tag_name("script")
        numScripts = self.html.count("<script")

        if numScripts%2 != 0:
            self.gs = wx.GridSizer(numScripts//2+1,4,5,5)
        else:
            self.gs = wx.GridSizer(numScripts//2,4,5,5)

        cnt = 0
        while "<script" in self.html:
            sIndex = self.html.find("<script")
            eIndex = self.html.find("</script>")
            text = self.html[sIndex:eIndex+9]

            if ' src="' in text:
                src = text.split(' src=')[1].split('"')[1].replace("http://","").replace("https://","")
                src = src.split("?")[0]
                contentText = ""

                # Connect to the database.
                conn = pymysql.connect(db=db_name,user=db_user,passwd=db_password,host='localhost',autocommit=True)
                d = conn.cursor()

                try:
                    sql = "SELECT filename FROM caching WHERE url LIKE '%{0}%'".format(src)
                    d.execute(sql)

                    if d.rowcount > 0:
                        filename = d.fetchone()[0]
                        contentText = getScriptText(filename)
                except:
                        contentText = ""

                print ("SCRIPT #", cnt)
                print (text)
                print (contentText[:500])
                print ("---"*20)

                d.close()
                conn.close()

            else:
                contentText = text

            self.html = self.html.replace(text,"\n<!--script"+str(cnt)+"-->\n")
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

        # check if we have already seen and saved the simplified page before in the DB
        conn = pymysql.connect(db=db_name,user=db_user,passwd=db_password,host='localhost',autocommit=True)
        d = conn.cursor()

        mainName = driver.current_url
        self.url = mainName

        # if "https://" in mainName:
        #     mainName = "https://" + mainName[8:len(mainName)-1] + ":443/"

        sql = "SELECT filename FROM caching WHERE url='{0}'".format(mainName+"JScleaner.html")
        d.execute(sql)

        if d.rowcount > 0:
            self.fileName = d.fetchone()[0]
        else:
            self.fileName = binascii.b2a_hex(os.urandom(15)).decode("utf-8")
            while os.path.exists(PROXY_DATA_PATH+self.fileName):
                self.fileName = binascii.b2a_hex(os.urandom(15)).decode("utf-8")

            sql = "INSERT INTO caching (url, filename) VALUES (%s,%s)"
            d.execute(sql, (mainName + "JScleaner.html", self.fileName))

            sql = "SELECT filename FROM caching WHERE url='{0}'".format(mainName)
            d.execute(sql)

            print (mainName)

            oldName = d.fetchone()[0]

            shutil.copy(PROXY_DATA_PATH + oldName + ".h", PROXY_DATA_PATH + self.fileName + ".h")


        print("Encoding the JSCleaner version")
        self.encode_save_index (self.html, self.fileName, PROXY_DATA_PATH)

        d.close()
        conn.close()

        print ("Loading the JScleaner version", self.url + "JScleaner.html")
        driver.get(self.url + "JScleaner.html")

    def on_all_press(self, event):
        try:
            toggle = event.GetEventObject().GetValue()
        except:
            toggle = True

        if toggle:
            # Insert all scripts
            for name in self.JavaScripts:
                if "<!--"+name+"-->" in self.html:
                    self.html = self.html.replace("<!--"+name+"-->", self.JavaScripts[name][2])
            
            self.encode_save_index (self.html, self.fileName, PROXY_DATA_PATH)
            driver.get(self.url + "JScleaner.html")
            
            # Toggle all script buttons
            for btn in self.scriptButtons:
                btn.SetValue(True)

        else:
            # Remove all scripts
            for name in self.JavaScripts:
                if self.JavaScripts[name][2] in self.html:
                    self.html = self.html.replace(self.JavaScripts[name][2], "<!--"+name+"-->")

            self.encode_save_index (self.html, self.fileName, PROXY_DATA_PATH)
            driver.get(self.url + "JScleaner.html")

            # Untoggle all script buttons
            for btn in self.scriptButtons:
                btn.SetValue(False)

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

            self.html = self.html.replace("<!--"+name+"-->",self.JavaScripts[name][2])
            self.encode_save_index (self.html, self.fileName, PROXY_DATA_PATH)
            driver.get(self.url + "JScleaner.html")

        else:
            self.select_all_btn.SetValue(False)
            self.features_text.SetValue("")
            self.content_text.SetValue("")
            
            self.html = self.html.replace(self.JavaScripts[name][2], "<!--"+name+"-->")
            self.encode_save_index (self.html, self.fileName, PROXY_DATA_PATH)
            driver.get(self.url + "JScleaner.html")

    def encode_save_index(self, content, name, path):
        with gzip.open(path + name + ".c", "wb") as f:
            f.write(content.encode())
            f.close
            # print ("HTML is encoded and saved!")

        content_size = os.path.getsize(path + name + ".c")

        with open(path + name + ".h") as f:
            new_text = ""
            existing_size = ""
            for line in f:
                if "Content-Length:" in line:
                    existing_size = line.split(' ',1)[1]
        
        if(existing_size != ""):
            with open(path + name + ".h") as f:
                atext = f.read().replace(existing_size, str(content_size)+ "\n")

            with open(path + name + ".h", "w") as f:
                f.write(atext)

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
    frame = MyFrame()
    frame.SetSize(800, 950)
    frame.SetMaxSize(wx.Size(800, 950))
    frame.SetMinSize(wx.Size(800, 950))

    options = FirefoxOptions()
    options.log.level = "trace"
    options.add_argument("-devtools")

    # start selenium firefox web driver
    #fp = webdriver.FirefoxProfile("/Users/Jacinta/Library/Application Support/Firefox/Profiles/kciui8dl.default")
    fp = webdriver.FirefoxProfile("/Users/yz48/Library/Application Support/Firefox/Profiles/rcda2lkh.default-release")
    fp.set_preference("devtools.toolbox.selectedTool", "netmonitor")
    fp.set_preference("browser.cache.disk.enable", False)
    fp.set_preference("browser.cache.memory.enable", False)
    fp.set_preference("browser.cache.offline.enable", False)
    fp.set_preference("network.http.use-cache", False)
    driver = webdriver.Firefox(options=options, firefox_profile=fp)
    # driver = webdriver.Firefox(executable_path="./geckodriver", firefox_profile=fp)

    app.MainLoop()
    driver.quit()