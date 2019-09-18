import wx
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
import wx.lib.scrolledpanel
import os
import jsbeautifier
import requests
from time import sleep
from selenium import webdriver
from bs4 import BeautifulSoup, Tag
from collections import OrderedDict

import gzip
import shutil
import pymysql
from selenium.webdriver.common.keys import Keys
import zlib
import brotli
from io import StringIO
import io

# read DB user name and password
db_name = "JSCleaner"
db_user = "root"
db_password = input("please enter DB password ")

http_proxy  = "http://127.0.0.1:9999"
https_proxy = "https://127.0.0.1:9999"

proxyDict = { 
              "http"  : http_proxy, 
              "https" : https_proxy 
            }

features = [".lookupPrefix",".prefix",".childNodes",".open",".isEqualNode",".documentURI",".lastChild",".nodeName",".title",".implementation",".normalizeDocument",".forms",".input",".anchors",".createCDATASection",".URL",".getElementsByTagName",".createEntityReference",".domConfig",".createElement",".xmlStandalone",".referrer",".textContent",".doctype",".namespaceURI",".strictErrorChecking",".xmlEncoding",".appendChild",".domain",".createAttribute",".links",".adoptNode",".Type",".nextSibling",".firstChild",".images",".close",".xmlVersion",".event",".form",".createComment",".removeChild",".nodeValue",".localName",".ownerDocument",".previousSibling",".body",".isDefaultNamespace",".nodeType",".track",".isSameNode",".cookie",".createDocumentFragment",".getElementsByName",".baseURI",".lookupNamespaceURI",".parentNode",".getElementById",".attributes",".createTextNode"]

def decode_gzip(filepath):
	f = open (filepath + ".c", "rb")
	content = f.read()
	# data = gzip.GzipFile('', 'rb', 9, StringIO.StringIO(content))
	data = gzip.GzipFile('', 'rb', 9, io.BytesIO(content))
	
	data = data.read()
	return data

def decode_br_content(filepath):
	f = open (filepath + ".c", "rb")
	content = f.read()
	decoded_content = brotli.decompress(content)
	return decoded_content

def getScriptText(filename):
	encoding = None
	contentText = ""

	with open(os.getcwd() + "/../proxy/data/"+filename + ".h") as f:
		for line in f:
			if "Content-Encoding:" in line:
				encoding = line.split(' ',1)[1]

	if encoding != None:
		#Decode gzip
		if "gzip" in encoding:
			contentText = decode_gzip(os.getcwd() + "/../proxy/data/"+filename).decode("utf-8")

		#Decode br
		if "br" in encoding:
			contentText = decode_br_content(os.getcwd() + "/../proxy/data/"+filename).decode("utf-8")
	else:
		f = open(os.getcwd() + "/../proxy/data/"+filename+".c", "r")
		contentText = f.read()
		f.close()

	return contentText


class JSCleaner(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self,parent,id,title,size=(800,800), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)

		self.number_of_buttons = 2

		self.vbox = wx.BoxSizer(wx.VERTICAL)
		self.display = wx.TextCtrl(self, style=wx.TE_LEFT)
		# self.display.SetValue("http://yasirzaki.net")
		self.display.SetValue("http://www.irs.gov")
		self.vbox.Add(self.display, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=4)

		my_btn = wx.Button(self, label='Analyze page')
		my_btn.Bind(wx.EVT_BUTTON, self.on_press)
		self.vbox.Add(my_btn, 0, wx.ALL | wx.CENTER, 5)

		self.textBox = ExpandoTextCtrl (self)
		self.vbox.Add(self.textBox, 0, wx.EXPAND, 5)
		self.Bind(EVT_ETC_LAYOUT_NEEDED, self.OnRefit, self.textBox)
		self.number_of_buttons += 1

		self.SetSizer(self.vbox)
		self.url = ""

	def on_script_press(self, event):
		try:
			name = event.GetEventObject().myname
			toggle = event.GetEventObject().GetValue()
		except:
			name = "script0"
			toggle = True

		if toggle:
			self.textBox.SetValue(self.JavaScripts[name][0])

			print("\n")
			print("-"*20)
			os.system("clear")
			print (jsbeautifier.beautify(self.JavaScripts[name][1]))
			# print (self.JavaScripts[name][2])

			self.html = self.html.replace("<!--"+name+"-->",self.JavaScripts[name][2])
			self.encode_save_index (self.html, "irs.gov", os.getcwd() + "/../proxy/data/")
			driver.get(self.url + "/js.html")

		else:
			self.selectAll.SetValue(False)
			self.textBox.SetValue("")

			os.system("clear")
			
			self.html = self.html.replace(self.JavaScripts[name][2], "<!--"+name+"-->")
			self.encode_save_index (self.html, "irs.gov", os.getcwd() + "/../proxy/data/")
			driver.get(self.url + "/js.html")

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
			
			self.encode_save_index (self.html, "irs.gov", os.getcwd() + "/../proxy/data/")
			driver.get(self.url + "/js.html")
			
			# Toggle all script buttons
			for btn in self.scriptButtons:
				btn.SetValue(True)

		else:
			# Remove all scripts
			for name in self.JavaScripts:
				if self.JavaScripts[name][2] in self.html:
					self.html = self.html.replace(self.JavaScripts[name][2], "<!--"+name+"-->")

			self.encode_save_index (self.html, "irs.gov", os.getcwd() + "/../proxy/data/")
			driver.get(self.url + "/js.html")

			# Untoggle all script buttons
			for btn in self.scriptButtons:
				btn.SetValue(False)


	def on_press(self, event):
		self.url = self.display.GetValue()
		if not self.url:
			return

		self.JavaScripts = {}
		self.scriptButtons = []

		driver.get(self.url)
		html_source = driver.page_source

		self.html = str(BeautifulSoup(html_source, 'html.parser'))

		#Here is the part which extracts Scripts
		scripts = driver.find_elements_by_tag_name("script")
		scriptsCount = self.html.count("<script")

		self.selectAll = wx.ToggleButton(self, label='Select All')
		self.selectAll.Bind(wx.EVT_TOGGLEBUTTON, self.on_all_press)
		self.vbox.Add(self.selectAll, 0, wx.ALIGN_LEFT | wx.ALL, 5)
		self.number_of_buttons += 1

		self.panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, size=(600,700), style=wx.SIMPLE_BORDER) #pos=(20,100)
		self.panel.SetupScrolling()
		self.panel.SetBackgroundColour('#FFFFFF')
		
		self.vbox.Add(self.panel, 0, wx.EXPAND, 5)
		self.SetSizer(self.vbox)

		self.gs = wx.GridSizer(scriptsCount,4,5,5)

		cnt = 0

		firstButton = False

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

				sql = "SELECT filename FROM caching WHERE url LIKE '%{0}%'".format(src)
				d.execute(sql)

				if d.rowcount > 0:
					filename = d.fetchone()[0]
					contentText = getScriptText(filename)
				else:
					src = src.strip("/").split("/")
					src[0] = src[0]+":443"
					src = "/".join(src)

					sql = "SELECT filename FROM caching WHERE url LIKE '%{0}%'".format(src)
					d.execute(sql)

					if d.rowcount > 0:
						filename = d.fetchone()[0]
						contentText = getScriptText(filename)
					else:
						print (d.rowcount, src)

				print (text)
				print (contentText[:200])
				print ("---"*20)

				d.close()
				conn.close()

			else:
				contentText = text

			self.html = self.html.replace(text,"\n<!--script"+str(cnt)+"-->\n")
			self.scriptButtons.append(wx.ToggleButton(self.panel, label="script"+str(cnt), size=(100,50)))
			self.scriptButtons[cnt].Bind(wx.EVT_TOGGLEBUTTON, self.on_script_press)
			self.scriptButtons[cnt].myname = "script"+str(cnt)
			self.gs.Add(self.scriptButtons[cnt], 0, wx.ALL, 0)

			if firstButton == False:
				firstButton = self.scriptButtons[cnt]

			labels = ["critical","non-critical","translatable"]
			colors = [wx.Colour(255, 0, 0),wx.Colour(0, 255, 0),wx.Colour(0, 0, 255)]

			for i in range(3):
				textBox = wx.ToggleButton(self.panel, label=labels[i], size=(100,25))
				textBox.SetBackgroundColour(colors[i])
				textBox.SetForegroundColour(colors[i])
				self.gs.Add(textBox, 0, wx.ALL,0)

			tmp = {}
			for feature in features:
				if feature in contentText:
					tmp[feature] = contentText.count(feature)
			tmp_sorted = OrderedDict(sorted(tmp.items(), key=lambda x: x[1], reverse=True))
			tmp = ""
			for k, v in tmp_sorted.items():
				tmp += "{0}: {1}\n".format(k,v) 

			self.JavaScripts["script"+str(cnt)] = [tmp, contentText, text]
			self.number_of_buttons += 1
			cnt += 1

		self.panel.SetSizer(self.gs)
		self.textBox.SetValue("Feature display will be here\n\n\n\n\n")

		self.encode_save_index (self.html, "irs.gov", os.getcwd() + "/../proxy/data/")

		driver.get(self.url + "/js.html")

	def encode_save_index(self, content, name, path):
		with gzip.open(path + name + ".c", "wb") as f:
			f.write(content.encode())
			f.close
			print ("HTML is encoded and saved!")

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

	def OnRefit(self, evt):
		self.panel.SetSizer(self.gs)


if __name__ == '__main__':
	app = wx.App()
	ex = JSCleaner(parent=None, id=-1, title='JS Analyzer')
	ex.SetSize(800, 800)
	ex.Show()

	fp = webdriver.FirefoxProfile("/Users/yz48/Library/Application Support/Firefox/Profiles/rcda2lkh.default-release")
	# driver = webdriver.Firefox(executable_path="./geckodriver", firefox_profile=fp)
	driver = webdriver.Firefox(firefox_profile=fp)
	driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.SHIFT + 'k')

	app.MainLoop()
	driver.quit()
