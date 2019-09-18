import wx
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
import wx.lib.scrolledpanel
import lorem

class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.number_of_buttons = 0
        self.colors = {"":wx.Colour(255, 255, 255, 100), "critical":wx.Colour(255, 0, 0, 100), "non-critical":wx.Colour(0, 255, 0, 100),"translatable":wx.Colour(0, 0, 255, 100)}
        self.frame = parent
 
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        url_input = wx.TextCtrl(self, style=wx.TE_LEFT)
        url_input.SetValue("http://www.irs.gov")
        self.mainSizer.Add(url_input, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=4)

        analyze_btn = wx.Button(self, label='Analyze page')
        analyze_btn.Bind(wx.EVT_BUTTON, self.on_analyze_press)
        self.mainSizer.Add(analyze_btn, 0, wx.ALL | wx.CENTER, 5)

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

        self.scripts_panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1, size=(750,400), style=wx.SIMPLE_BORDER)
        self.scripts_panel.SetupScrolling()
        self.scripts_panel.SetBackgroundColour('#FFFFFF')
        self.mainSizer.Add(self.scripts_panel, 0, wx.CENTER, 5)

        self.SetSizer(self.mainSizer)
        self.gs = None

    def on_analyze_press(self, event):
        self.scriptButtons = []
        self.choiceBoxes = []

        self.features_text = ExpandoTextCtrl(self.features_panel, size=(360,290))
        self.features_text.SetValue(lorem.text() * 2)
        self.Bind(EVT_ETC_LAYOUT_NEEDED, None, self.features_text)

        self.features_sizer = wx.BoxSizer(wx.VERTICAL)
        self.features_sizer.Add(self.features_text, 0, wx.CENTER, 5)
        self.features_panel.SetSizer(self.features_sizer)

        self.content_text = ExpandoTextCtrl(self.content_panel, size=(360,290))
        self.content_text.SetValue(lorem.text() * 2)
        self.Bind(EVT_ETC_LAYOUT_NEEDED, None, self.content_text)

        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.content_sizer.Add(self.content_text, 0, wx.CENTER, 5)
        self.content_panel.SetSizer(self.content_sizer)

        while self.gs != None and len(self.gs.GetChildren()) > 0:
            self.gs.Hide(self.number_of_buttons-1)
            self.gs.Remove(self.number_of_buttons-1)
            self.number_of_buttons -= 1
            self.frame.fSizer.Layout()

        numScripts = 40
        self.gs = wx.GridSizer(numScripts//2+1,4,5,5)

        for cnt in range(numScripts):

            self.scriptButtons.append(wx.ToggleButton(self.scripts_panel, label="script"+str(cnt), size=(100,25)))
            # self.scriptButtons[cnt].Bind(wx.EVT_TOGGLEBUTTON, self.on_script_press)
            self.scriptButtons[cnt].myname = "script"+str(cnt)
            self.gs.Add(self.scriptButtons[cnt], 0, wx.ALL, 0)
            self.number_of_buttons += 1

            choiceBox = wx.ComboBox(self.scripts_panel, value="", style=wx.CB_READONLY, choices=("","critical","non-critical","translatable"))
            choiceBox.Bind(wx.EVT_COMBOBOX, self.OnChoice)
            choiceBox.index = len(self.choiceBoxes)
            self.choiceBoxes.append(choiceBox)

            self.gs.Add(choiceBox, 0, wx.ALL,0)
            self.number_of_buttons += 1

        self.scripts_panel.SetSizer(self.gs)
        self.frame.fSizer.Layout()

    def OnChoice(self,event): 
        choiceBox = self.choiceBoxes[event.GetEventObject().index]
        choiceBox.SetBackgroundColour(self.colors[choiceBox.GetValue()])

class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="JS Cleaner")
        self.fSizer = wx.BoxSizer(wx.VERTICAL)
        panel = MyPanel(self)
        self.fSizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(self.fSizer)
        self.Fit()
        self.Show()
 
if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame()
    frame.SetSize(800, 800)
    app.MainLoop()