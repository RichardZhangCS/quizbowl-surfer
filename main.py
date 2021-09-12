import kivy
import requests
import webbrowser
import re
import os
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from cairosvg import svg2png
from bs4 import BeautifulSoup
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager,Screen,NoTransition
from kivy.lang import Builder
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image, AsyncImage
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from functools import partial
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.graphics.svg import Svg
from kivy.uix.gridlayout import GridLayout 
from kivy.uix.stacklayout import StackLayout 
from kivy.uix.floatlayout import FloatLayout 
import qbwidgits
from qbwidgits import RV, SettingsButton, BackButton, SelectableText, SelectableLabel, SelectableRecycleBoxLayout


kv = Builder.load_file("main.kv")
class Entry():
    def __init__(self, topic, info):
        if topic == "":
            topic = " "
        if info == "":
            info = " "
        self.topic = topic
        self.info = info
    def __str__(self):
        return "|("+self.topic + ": " + self.info+")|"
        
class StartingWindow(Screen):
    pass

class SettingsWindow(Screen):
    pass

class NewEntryWebWindow(Screen):
    searchbutton = ObjectProperty(None)
    topicsearch = ObjectProperty(None)
    container = ObjectProperty(None)
    downloadbutton = ObjectProperty(None)
    selecttext = ObjectProperty(None)
    formulaNumber = 0
    def __init__(self, **kwargs):
        super().__init__()
        self.searchbutton.bind(on_release = self.getTopicInfo)
        self.downloadbutton.bind(on_release = self.downloadWebpage)
        Clock.schedule_once(self.setup_scrollview, 1)

    def setup_scrollview(self, dt):
        self.container.bind(minimum_height=self.container.setter('height'))
        
    def getTopicInfo(self, event):
        text = ["No information found."]
        page = requests.get("https://en.wikipedia.org/wiki/Special:Search?search=" + self.topicsearch.text + "&go=Go&ns0=1")
        soup = BeautifulSoup(page.content, 'html.parser')
        content = soup.select("div#mw-content-text p, div#mw-content-text h2, div#mw-content-text h3, div#mw-content-text dd,div#mw-content-text ul li.mw-search-result, div#mw-content-text div.mw-parser-output > ul li, span.mwe-math-element img")

        text = u""
        title = soup.select("h1#firstHeading")
        searchpage = False
        if (title[0].get_text() == "Search results"):
            self.resulttext.bind(on_ref_press=self.openWebpage)
            content = soup.select("ul.mw-search-results a")
            searchpage = True
            for link in content:
                if link.get_text():
                    indexone = str(link).index("href=\"")
                    indextwo = str(link).index("\"", indexone+6)
                    href = str(link)[indexone+6: indextwo]
                    text+="[ref="+href+"][color=0000ff]"+link.get_text()+"[/ref]\n"
        if not searchpage:
            for para in content:
                if str(para).startswith("<li>") or str(para).startswith("<ul>"):
                    text += " - "
                    text += para.get_text() + "\n"
                elif str(para).startswith("<h3"):
                    text += "[b]" + para.get_text() + "[/b]" + "\n"
                elif str(para).startswith("<h2"):
                    text += "[i][b]" + para.get_text() + "[/b][/i]" + "\n"
                elif str(para).startswith("<img"):
                    indexone = str(para).index('src=\"')+5
                    indextwo = str(para).index('\"', indexone)
                    link = str(para)[indexone:indextwo]
                    text += "[ref="+link+"][color=0000ff]Click to see formula[/color][/ref]\n"
                    self.resulttext.bind(on_ref_press=self.openImage)
                elif self.validifyContent(para):
                    text += para.get_text().replace('\n','') + "\n\n"
                    

        if "[b]See also[/b]" in text:
            self.resulttext.text = text[:text.index("[b]See also[/b]")]
        else:
            self.resulttext.text = text
        title = soup.select("h1#firstHeading")
        self.topicsearch.text = title[0].get_text()
        
    
    def downloadWebpage(self, event):
        nextScreen = sm.get_screen("newentryedit")
        nextScreen.selecttext.text = self.resulttext.text
        nextScreen.topicnamelabel.text = self.topicsearch.text
        nextScreen.oldtext = self.resulttext.text
        nextScreen.loadFigureText()
        nextScreen.selecttext.do_cursor_movement('cursor_home', control=True, alt=False)

    def validifyContent(self, para):
        return not str(para).startswith("<li id=\"cite_note") and not str(para).startswith("<li class=\"toclevel-") and not str(para).startswith("<p class=\"mw-empty") and not "class=\"nv-" in str(para)
    
    def openWebpage(self, instance, value):
        print(str(instance) + " " + str(value))
        self.topicsearch.text = value[6:]
        self.getTopicInfo(None)
    
    def openImage(self, instance, value):
        svgpage = requests.get(value)
        svg2png(bytestring=svgpage.content,write_to=str(self.formulaNumber)+'.png')
        popup = Popup(title="", content=Image(source = str(self.formulaNumber)+'.png'),size_hint=(None, None), size=(400, 400), background = 'atlas://data/images/defaulttheme/button_pressed')
        popup.open()
        os.remove(str(self.formulaNumber)+'.png')
        self.formulaNumber+=1
    
    def convertToFormula(self, string):
        result = ""
        string = string.replace("\\Delta","\u0394")
        string = string.replace('\\Delta', '\u0394')
        string = string.replace('{\\displaystyle', '')
        string = string.replace('\\mathbf', '')
        result = string
        print(result)
        return result
    

class NewEntryEditWindow(Screen):
    submitbutton = ObjectProperty(None)
    topicnamelabel = ObjectProperty(None)
    selecttext = ObjectProperty(None)
    entrytext = ObjectProperty(None)
    figurebutton = ObjectProperty(None)
    groupentrytext = ObjectProperty(None)
    submitdatecheckbox = ObjectProperty(None)
    oldtext = ""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.submitbutton.bind(on_release = self.submitToSheet)
        self.figurebutton.bind(on_release = self.onButtonPress)
        
    def submitToSheet(self, event):
        scope = ['https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('QB Surfer-874759bc9837.json', scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open("QB Surfer Test Sheet")

        selectedgroupsheet = spreadsheet.worksheet('Default')

        groupfound = False
        worksheet_list = spreadsheet.worksheets()
        groupname = self.groupentrytext.text
        for worksheet in worksheet_list:
            if (worksheet.title == groupname):
                selectedgroupsheet = worksheet
                groupfound = True
        if not groupfound and groupname:
            spreadsheet.add_worksheet(title=groupname, rows=0, cols=0)
            selectedgroupsheet = spreadsheet.worksheet(groupname)
        
        listentry = [self.topicnamelabel.text, self.entrytext.text]
        if self.submitdatecheckbox.active:
            now = datetime.now()
            dt_string = now.strftime("%m/%d/%Y %H:%M")
            listentry.append("Submitted on " + dt_string)
        selectedgroupsheet.append_row(listentry)
        sm.get_screen("editentryedit").entries.append(Entry(self.topicnamelabel.text, self.entrytext.text))
        sm.get_screen("editentryedit").entrylist.data.append({'text': self.topicnamelabel.text})
        self.entrytext.text = ""
    
    def loadFigureText(self):
        string = self.selecttext.text
        figureCounter = 0
        # downloading figures
        while '[ref=' in string:
            startindex = string.index('[ref=') +5
            endindex = string.index(']', startindex)
            figureCounter += 1
            endindex = string.index('[/ref]', startindex)+6
            string = string[0:startindex-5] + "See Figure " + str(figureCounter) + "\n" + string[endindex:]
        self.selecttext.text = string
    
    def loadFigureWindow(self):
        figureCounter = 0
        afterindex = 0
        # downloading figures
        while '[ref=' in self.oldtext[afterindex:]:
            startindex = self.oldtext.index('[ref=', afterindex) +5
            endindex = self.oldtext.index(']', startindex)
            afterindex = endindex+1
            link = self.oldtext[startindex:endindex] 
            svgpage = requests.get(link)
            svg2png(bytestring=svgpage.content,write_to='figures/figure'+str(figureCounter)+'.png')
            figureCounter += 1

    def onButtonPress(self, button): 
        self.clearFigureFolder()
        path = "figures"
        try:
            os.mkdir(path)
        except OSError:
            print ("Creation of the directory %s failed" % path)
        else:
            print ("Successfully created the directory %s " % path)

        scrollview = ScrollView(bar_width=10,
            bar_color=(1, 0, 0, 1),   # red
            bar_inactive_color=(0, 0, 1, 1),
            effect_cls="ScrollEffect",
            scroll_type=['bars'], size_hint = (1.0,0.9), pos_hint = {"x":0.0,"y":0.1})    
        figurelayout = GridLayout(cols = 1, size_hint_y=None)
        figurelayout.bind(minimum_height=figurelayout.setter('height'))
        figureCounter = 0
        afterindex = 0
        # downloading figures
        while '[ref=' in self.oldtext[afterindex:]:
            startindex = self.oldtext.index('[ref=', afterindex) +5
            endindex = self.oldtext.index(']', startindex)
            afterindex = endindex+1
            link = self.oldtext[startindex:endindex] 
            svgpage = requests.get(link)
            svg2png(bytestring=svgpage.content,write_to='figures/figure'+str(figureCounter)+'.png')
            individualFigure = GridLayout(cols=2, size_hint_y=None)
            figurelabel = Label(text = 'Figure ' + str(figureCounter+1))
            figureimage = Image(source='figures/figure'+str(figureCounter)+'.png', size_hint_y=None)
            individualFigure.add_widget(figurelabel)
            individualFigure.add_widget(figureimage)
            figurelayout.add_widget(individualFigure)
            figureCounter += 1 
        scrollview.add_widget(figurelayout)
        exitbutton = Button(text='Close', size_hint = (1.0,0.1), pos_hint = {"x":0.0,"y":0.0})
        root = FloatLayout()
        root.add_widget(scrollview)
        root.add_widget(exitbutton)
        popup = Popup(title ='Figure Window', content = root)   
        exitbutton.bind(on_release=popup.dismiss)
        exitbutton.bind(on_release=popup.dismiss)
        popup.open()    
    
    def clearFigureFolder(self):
        import shutil
        try:
            shutil.rmtree('figures')
        except FileNotFoundError:
            print('Figure folder not found')
  
class EditEntryEditWindow(Screen):
    entrylist = ObjectProperty(None)
    editor = ObjectProperty(None)
    clearbutton = ObjectProperty(None)
    webpagebutton = ObjectProperty(None)
    deletebutton = ObjectProperty(None)
    submitbutton = ObjectProperty(None)
    entries = []
    selectedentryview = None
    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('QB Surfer-874759bc9837.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("QB Surfer Test Sheet").worksheet('Default')
    def __init__(self, **kwargs):
        super().__init__()
        self.loadentries()
        self.entrylist.bind(on_touch_up=self.updateUI)
        self.clearbutton.bind(on_release=self.clear)
        self.deletebutton.bind(on_release=self.delete)
        self.submitbutton.bind(on_release=self.submit)

        Clock.schedule_interval(self.updateUI, 0.1)
        
    def loadentries(self):
        self.sheet = self.client.open("QB Surfer Test Sheet").worksheet('Default')
        self.entrylist.data.clear()
        self.entries.clear()
        for i in range(1, self.sheet.row_count+1):
            values_list = self.sheet.row_values(i)
            self.entries.append(Entry(values_list[0], values_list[1]))
            self.entrylist.data.append({'text': values_list[0]})
    
    def updateUI(self, *args):
        entryviews = self.entrylist.children[0].children
        for entryview in entryviews:
            if entryview.selected and self.selectedentryview is not entryview:
                self.selectedentryview = entryview
                if self.selectedentryview != None:
                    self.editor.text = getEntry(self.entries, self.selectedentryview.text).info 
                break

    def parseentries(self, text):
        self.entrylist.data.clear()
        afterindex = 0
        while afterindex < len(text):
            title = text[text.index("|(", afterindex) + 2: text.index(": ", afterindex)]
            info = text[text.index(": ", afterindex) + 2: text.index(")|", afterindex)]
            afterindex = text.index(")|", afterindex) + 2
            self.entries.append(Entry(title, info))
            self.entrylist.data.append({'text': title})
    
    def clear(self, event):
        self.editor.text = ""

    def delete(self, event):
        removeRowIndex = 1
        
        for i in range(1, self.sheet.row_count+1):
            values_list = self.sheet.row_values(i)
            if (values_list[0] == self.selectedentryview.text):
                removeRowIndex = i
        
        self.sheet.delete_row(removeRowIndex)

        if (self.selectedentryview == None):
            return
        self.entrylist.data.remove({'text':self.selectedentryview.text})
        if (not self.entrylist.data):
            self.editor.text = ""

    def submit(self, event):
        newinfo = self.editor.text
        editRowIndex = 1
        
        for i in range(1, self.sheet.row_count+1):
            values_list = self.sheet.row_values(i)
            if (values_list[0] == self.selectedentryview.text):
                editRowIndex = i
        
        self.sheet.update_cell(editRowIndex, 2, newinfo)

        entry = getEntry(self.entries, self.selectedentryview.text)
        entry.info = newinfo
        entryviews = self.entrylist.children[0].children
        for entryview in entryviews:
            entryview.selected = False
        self.editor.text = ""

def getEntry(entries, topic):
    for entry in entries:
        if entry.topic == topic:
            return entry

class EditEntryWebWindow(Screen):
    pass

sm = ScreenManager(transition=NoTransition())
sm.add_widget(StartingWindow())
sm.add_widget(SettingsWindow())
sm.add_widget(NewEntryWebWindow())
sm.add_widget(NewEntryEditWindow())
sm.add_widget(EditEntryEditWindow())
sm.add_widget(EditEntryWebWindow())

def listToString(s):  
    str1 = ""    
    for ele in s:  
        str1 += ele  
    return str1

class QBSurferApp(App):
    def build(self):
        return sm
        
if __name__ == '__main__':
    QBSurferApp().run()