import wx
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
import wx.lib.scrolledpanel

import os
import jsbeautifier

import requests
from time import sleep
from selenium.webdriver import ActionChains

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup, Tag
from collections import OrderedDict

features = [".lookupPrefix",".prefix",".childNodes",".open",".isEqualNode",".documentURI",".lastChild",".nodeName",".title",".implementation",".normalizeDocument",".forms",".input",".anchors",".createCDATASection",".URL",".getElementsByTagName",".createEntityReference",".domConfig",".createElement",".xmlStandalone",".referrer",".textContent",".doctype",".namespaceURI",".strictErrorChecking",".xmlEncoding",".appendChild",".domain",".createAttribute",".links",".adoptNode",".Type",".nextSibling",".firstChild",".images",".close",".xmlVersion",".event",".form",".createComment",".removeChild",".nodeValue",".localName",".ownerDocument",".previousSibling",".body",".isDefaultNamespace",".nodeType",".track",".isSameNode",".cookie",".createDocumentFragment",".getElementsByName",".baseURI",".lookupNamespaceURI",".parentNode",".getElementById",".attributes",".createTextNode"]

class JSCleaner(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self,parent,id,title,size=(800,800), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)

		self.number_of_buttons = 2

		self.vbox = wx.BoxSizer(wx.VERTICAL)
		self.display = wx.TextCtrl(self, style=wx.TE_LEFT)
		self.display.SetValue("http://yasirzaki.net")
		# self.display.SetValue("http://nyuad.nyu.edu")
		self.vbox.Add(self.display, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=4)

		my_btn = wx.Button(self, label='Analyze page')
		my_btn.Bind(wx.EVT_BUTTON, self.on_press)
		self.vbox.Add(my_btn, 0, wx.ALL | wx.CENTER, 5)

		self.textBox = ExpandoTextCtrl (self)
		self.vbox.Add(self.textBox, 0, wx.EXPAND, 5)
		self.Bind(EVT_ETC_LAYOUT_NEEDED, self.OnRefit, self.textBox)
		self.number_of_buttons += 1

		self.SetSizer(self.vbox)

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

			self.html = self.html.replace("</body>",self.JavaScripts[name][2]+"</body>")
			f = open("after.html","w")
			f.write(self.html)
			f.close()

			driver.get("file:///Users/yz48/Desktop/after.html")

		else:
			self.textBox.SetValue("")

			os.system("clear")
			
			self.html = self.html.replace(self.JavaScripts[name][2]+"</body>", "</body>")
			f = open("after.html","w")
			f.write(self.html)
			f.close()

			driver.get("file:///Users/yz48/Desktop/after.html")

	def on_press(self, event):
		url = self.display.GetValue()
		if not url:
			return

		self.JavaScripts = {}

		driver.get(url)
		html_source = driver.page_source

		self.html = str(BeautifulSoup(html_source, 'html.parser'))
		f = open("before.html","w")
		f.write(self.html)
		f.close()

		#Here is the part which extracts Scripts
		scripts = driver.find_elements_by_tag_name("script")
		scriptsCount = self.html.count("<script")

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

			if 'src="' in text:
				src = text.split('src=')[1].split('"')[1]
				if src[:2] == "//":
					req = requests.get("http:"+src)
				elif src[:1] == "/":
					req = requests.get(url+src)
				else:
					req = requests.get(src)
				contentText = req.text
			else:
				contentText = text

			self.html = self.html.replace(text,"\n")

			textBox = wx.ToggleButton(self.panel, label="script"+str(cnt), size=(100,50))
			textBox.myname = "script"+str(cnt)
			textBox.Bind(wx.EVT_TOGGLEBUTTON, self.on_script_press)
			textBox.myname = "script"+str(cnt)
			self.gs.Add(textBox, 0, wx.ALL,0)

			if firstButton == False:
				firstButton = textBox

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

	
	def OnRefit(self, evt):
		# self.Fit()
		# self.vbox.Layout()
		self.panel.SetSizer(self.gs)

			# self.vbox.Add(grid)

			# self.textBox = ExpandoTextCtrl (self.panel)
			# self.vbox.Add(self.textBox, 0, wx.ALL | wx.EXPAND, 5)
			# self.Bind(EVT_ETC_LAYOUT_NEEDED, self.OnRefit, self.textBox)
			# self.number_of_buttons += 1

			# self.vbox.Layout()
			# self.Fit()

			# # print (self.html)
			# f = open("after.html","w")
			# f.write(self.html)
			# f.close()

			# driver.get("file:///Users/yzaki/Desktop/after.html")



if __name__ == '__main__':
	app = wx.App()
	ex = JSCleaner(parent=None, id=-1, title='Calculator')
	ex.SetSize(800, 800)
	ex.Show()
	driver = webdriver.Chrome()
	app.MainLoop()
	driver.quit()
