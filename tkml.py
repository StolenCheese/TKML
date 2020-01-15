
from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext

from tkelements import *
import tkmlDecoder as decode
import tkgradientframe
import pygame_frame

import xml.etree.ElementTree as ET

class Label(Label):
    def __init__(self, master=None, **options):
        font = options.pop("font", "TkDefaultFont")
        fontSize = options.pop("fontsize", 9)
        options["font"] = (font, fontSize)
        super().__init__(master, **options)


'''#help
<head> - menu bar and title
<title> - sets title of window (text)
<menu> - starts menu bar
<cascade> - start menu in menu bar
<command> label:TEXT - add command to menu [Default - label]
<separator> - add seperator to menu
<radiobutton> value:BOOL
<checkbutton> value:BOOL
<dropdown> value:INT


// Actual TK classes

<body> minWidth:FLOAT [0] minHeight:FLOAT [0]- places widgets

<p> font:STRING fontsize:FLOAT [10]  image:STRING (file tag for image) - displays text(text) or image but not both
    image can be of type gif only - idk why
<input> placeHolder:STRING [""], placeHolderColor:STRING [grey],varname:STRING - entry object that can store input in varname
<radiobutton>
<checkbutton>
<button>

<colorpick> - color picker

//list elements - text: list of choices seperated by ";"
<dropdown> click to reveil choices
<listbox> box with list of choices
<spinbox> entry with arrows for choices - kinda bad

//layout elements

<grid> rows:INT [1] columns:INT [1] creates grid object - objects inside gain attrib gridx:INT [0],gridy:INT [0],gridspanx:INT [1],gridspany:INT [1]
<notebook> - maximum 10 tabs
<horizontal>
<vertical>
'''


FLOAT = "FLOAT"
INT = "INT"
STRING = "STRING"

consts = {
    "HORIZONTAL": HORIZONTAL,
    "VERTICAL": VERTICAL,
    "SINGLE": SINGLE,
    "EXTENDED": EXTENDED,
    "MULTIPLE": MULTIPLE,
    "BROWSE": BROWSE,
    "FLOAT": FLOAT,
    "INT": INT,
    "STRING": STRING
}

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text  # or whatever

#event wrappers

#used to decorate functions to call events

class Window(object):
    def callback(self,func):
        self.callbacks[func.__name__] = func
        return func
    def custom(self,obj):
        self.customs[obj.__name__] = obj
        return obj
    # Functions used to create the window:
    def GenerateElement(self, element, root):

        style = element.attrib.pop('style', '')
        if style != '':
            # get dict of all attrib accosiated with the style and include it - if tag is in style and element attrib the local tag will take priority
            styleTags = self.styles[style]
            for tag in styleTags.keys():
                if tag not in element.attrib:
                    element.attrib[tag] = styleTags[tag]

        callback = element.attrib.pop('callback', '')
        hasCallback = callback != ''

        callbackArgs = element.attrib.pop('arg', [])
        if callbackArgs != []:  # temporary conversion to list because args not passed as list
            callbackArgs = [callbackArgs]

        varname = element.attrib.pop("varname", "")
        hasVariable = varname != ''
        image = element.attrib.pop("image", '')

        if image != '':
            image = PhotoImage(file=image)

        ref = element.attrib.pop("ref", '')

        hasRef = ref != ''

        output = None

        usesStringVar = ['p', 'dropdown', 'spinbox']
        if element.tag in usesStringVar:
            if varname in self.values:
                element.attrib['textvariable'] = self.values[varname]
            else:
                stringVar = StringVar()
                if hasCallback:
                    stringVar.trace(
                        'w', lambda *a: self.OnCallback(callback, *callbackArgs))
                if hasVariable:
                    self.values[varname] = stringVar
                element.attrib['textvariable'] = stringVar
        if element.tag in self.customs:
            output = self.customs[element.tag](self, root,  **element.attrib)

        elif element.tag == "p":
            if type(element.attrib['textvariable']) is StringVar:
                element.attrib['textvariable'].set(element.text)
            if element.text != '':
                element.attrib['text'] = element.text
            if image == '':
                output = Label(root, **element.attrib)
            else:  # set up label with image object
                imageLabel = Label(root, image=image, **element.attrib)
                imageLabel.image = image  # keep reference so GC does not destroy it
                output = imageLabel

        elif element.tag == "progressbar":
            # controller must have access to value and like of bar
            # functions start,stop and step up to 100%
            bar = ttk.Progressbar()
            output = bar
            
        elif element.tag == "text":
            scrolled = element.attrib.pop('scrolled', False)
            if scrolled:
                text = scrolledtext.ScrolledText(root)
            else:
                text = Text(root)
            text.insert(END, element.text)
            output = text

        elif element.tag == 'seperator':
            output = ttk.Separator(root, **element.attrib)

        elif element.tag == "field":

            # Get type of entry - defaults to string for convience
            valueType = element.attrib.pop("type", STRING)
            vartagname = 'textvariable'
            if valueType == INT:
                vartagname = 'intvariable'
            elif valueType == FLOAT:
                vartagname = 'floatvariable'

            if varname in self.values:  # already variable defined, use that
                element.attrib[vartagname] = self.values[varname]

            else:  # create a new variable
                if valueType == FLOAT:
                    # setup float variable
                    variable = DoubleVar()

                elif valueType == STRING:
                    # setup string varaible
                    variable = StringVar()

                elif valueType == INT:
                    # setup int variable
                    variable = IntVar()

                if hasCallback:
                    variable.trace(
                        'w', lambda *args: self.OnCallback(callback, *callbackArgs))
                if hasVariable:
                    self.values[varname] = variable
                element.attrib[vartagname] = variable

            # return the correct type
            if valueType == FLOAT:
                output = FloatField(root, **element.attrib)
            elif valueType == INT:
                output = IntField(root, **element.attrib)
            elif valueType == STRING:
                output = Entry(root, **element.attrib)

        # custom widgets
        elif element.tag == "colorfield":
            output = tkgradientframe.ColorField(root, **element.attrib)
        elif element.tag == "pygameframe":
            element.attrib['flags'] = element.text.split(';')
            output = pygame_frame.PygameFrame(root, **element.attrib)

        elif element.tag == "button":
            if element.text != "":
                element.attrib['text'] = element.text
            if 'label' in element.attrib:
                element.attrib['text'] = element.attrib.pop('label', '')
            if hasCallback:  # lambda used to pass callback tag so function can be applied
                element.attrib["command"] = lambda: self.OnCallback(
                    callback, *callbackArgs)

            # change to page tag will change the selected page when the button is pressed
            changeToPage = element.attrib.pop('changetopage', '')
            if changeToPage != '':
                element.attrib['command'] = lambda x=changeToPage: self.ChangeToPage(
                    x)

            output = Button(root, **element.attrib)

        elif element.tag == "canvas":
            output = Canvas(root, **element.attrib)

        elif element.tag == "checkbutton":
            if element.text != "":
                element.attrib['text'] = element.text
            output = Checkbutton(root, **element.attrib)

        elif element.tag == "radiobutton":
            if element.text != "":
                element.attrib['text'] = element.text
            var = element.attrib.pop("group", "defaultgroup")
            if var not in self.values:
                self.values[var] = IntVar()
                self.values[var].trace(
                    "w", lambda *a: self.OnCallback(callback, *callbackArgs))
            output = Radiobutton(
                root, variable=self.values[var], **element.attrib)

        elif element.tag == "dropdown":
            options = element.text.split(';')
            stringVar.set(options[0])
            output = OptionMenu(root, stringVar, *options)

        elif element.tag == "slider":
            element.attrib['from_'] = int( element.attrib.pop('min', 0))
            element.attrib['to'] = int( element.attrib.pop("max", 1))
            if hasVariable:
                vartype = element.attrib.pop('type', FLOAT)
                if vartype == FLOAT:
                    variable = DoubleVar()
                elif vartype == INT:
                    variable = IntVar()
                defaultValue = element.attrib.pop('default', element.attrib['from_'])
                variable.set(defaultValue)
                if hasCallback:
                    variable.trace(
                        'w', lambda *a: self.OnCallback(callback, *callbackArgs))
                element.attrib['variable'] = variable
                self.values[varname] = variable
                
            output = Scale(root, **element.attrib)

        elif element.tag == "spinbox":
            spins = element.text.split(';')
            output = Spinbox(root, values=spins, **element.attrib)

        elif element.tag == "listbox":
            options = element.text.split(';')
            # if user wants scrollbar link scrollbar object to list events

            box = Listbox(root, **element.attrib)
            for option in options:
                box.insert(END, option)
            output = box

        elif element.tag == 'autogrid':
            # autogrid simply needs childs attached to it to work
            output = AutoGrid(root, **element.attrib)
            for child in element:
                output.AddChildToGrid(self.GenerateElement(child, output))
            output.UpdateItemGrid(50)

        elif element.tag == 'grid':
            output = self.GenerateChildrenInGrid(element)
        elif element.tag == "horizontal":
            output = self.GenerateHorizontalLayout(element, root=root)
        elif element.tag == "vertical":
            output = self.GenerateVerticalLayout(element, root=root)
        elif element.tag == "notebook":
            output = self.GenerateNotebook(element, root=root)
        if hasRef:
            self.elements[ref] = output
        return output

    def GenerateChildren(self, parent, root):
        for element in parent:

            if element.tag == "title":
                self.title = self.root.title(element.text)
            elif element.tag == "style":
                self.AddStyle(element)
            elif element.tag == "body" or element.tag == "head":
                widgets = self.GenerateChildren(element, root)
                if element.tag == "body":
                    minWidth = element.attrib.pop('minWidth', 0)
                    minHeight = element.attrib.pop('minHeight', 0)
                    self.root.minsize(minWidth, minHeight)
                for widget in widgets:
                    yield widget
            elif element.tag == "menu":
                self.GenerateMenuBar(element, root)
            else:
                widget = self.GenerateElement(element, root)
                widget.grid(sticky=N+S+W+E)
                yield widget

    def AddStyle(self, style):
        # style always needs a reference to be used by other elements
        ref = style.attrib.pop('ref', '')
        if ref == '':
            raise Exception('Style has no reference')
        self.styles[ref] = style.attrib

    def GetElementsStartingWith(self,root,start):
        for child in root:
            if child.tag.startswith(start):
                yield child

    def GetAttrib(self,root,att,outType,base,prefix=""):
        value = root.attrib.pop(att, base)
        if value == base:
            if prefix =="":
                prefix = "{}.".format(root.tag)
            for child in self.GetElementsStartingWith(root,prefix):
                #go through to see if there are any specific elements for list
                t = remove_prefix(child.tag,prefix)
                if t == att:
                    value = child.text
                    break
        return outType(value)
    
    def GetAttribs(self,root,att,prefix=""):
        if prefix =="":
            prefix = "{}.".format(root.tag)
        for child in self.GetElementsStartingWith(root,prefix):
            #go through to see if there are any specific elements for list
            t = remove_prefix(child.tag,prefix)
            if t == att:
                #need to add all nested attributes
                yield child
    def GetGridAttributes(self,element,p):
        return {
            "row": self.GetAttrib(element,"gridy",int,0,p),
            "column" : self.GetAttrib(element,"gridx",int,0,p),
            "pady" : self.GetAttrib(element,"pady",int,0,p),
            "ipadx" : self.GetAttrib(element,"ipadx",int,0,p),
            "ipady" : self.GetAttrib(element,"ipady",int,0,p),
            "padx" : self.GetAttrib(element,"padx",int,0,p),
            "sticky" : element.attrib.pop('sticky', 'wen'),
            "rowspan" : element.attrib.pop("gridspanx", 1),
            "columnspan" : element.attrib.pop("gridspany", 1)
            }

    def GetConfigureAttributes(self,element,p):
        return {
            "weight": self.GetAttrib(element,"weight",int,0,p),
            "minsize" : self.GetAttrib(element,"minsize",int,0,p),
            "pad" : self.GetAttrib(element,"pad",int,0,p)
            }
    
    def GenerateChildrenInGrid(self, grid):
        label = grid.attrib.pop('label', '')
        defaultColumnWeight = grid.attrib.pop('defaultcolumnweight', 0)
        defaultRowWeight = grid.attrib.pop('defaultrowweight', 0)

        if label == '':
            gridFrame = Frame(self.root, **grid.attrib)
        else:
            grid.attrib['text'] = label
            gridFrame = LabelFrame(self.root, **grid.attrib)

        columns = 1
        configuredColumns = []
        rows = 1
        configuredRows = []

        p = "grid."

        #configure columns then configure rows
        for rowConfig in self.GetAttribs(grid,"rowconfig"):
            row = int(rowConfig.attrib.pop('row', 0))
            configuredRows.append(row)
            
            gridFrame.rowconfigure(row, **rowConfig.attrib)
            
        for columnConfig in self.GetAttribs(grid,"columnconfig"):
            column = int(columnConfig.attrib.pop("column", 0))
            configuredColumns.append(column)
            at = columnConfig.attrib
            for child in columnConfig:
                #remove prefix and add text as tag of it's name
                name = remove_prefix(child.tag,"columnconfig.")
                at[name] = child.text
            gridFrame.columnconfigure(column, **at)
                
        for element in grid:
            if element.tag.startswith(p):
                continue

            gridAttributes = self.GetGridAttributes(element,p)

            if gridAttributes["column"] > columns:
                columns = gridAttributes["column"]  # If this row or column is the biggest
            if gridAttributes["row"] > rows:  # update the value so all unconfiged
                rows = gridAttributes["row"]  # zones can be defaulted
                
            generated = self.GenerateElement(element, gridFrame)
            try:
                generated.grid(**gridAttributes)
            except:
                raise Exception("Error Creating Element {}".format(element.tag))

        for row in range(rows+1):  # set defaults
            if row not in configuredRows:
                gridFrame.rowconfigure(row, weight=defaultRowWeight)
        for column in range(columns+1):
            if column not in configuredColumns:
                gridFrame.columnconfigure(column, weight=defaultColumnWeight)
        gridFrame.grid(sticky=W+E+N+S)
        return gridFrame

    def GenerateMenuBar(self, menubar, root):  # menubar - element
        menubarWidget = Menu(root, tearoff=0)

        for item in menubar:
            if item.tag == "cascade":  # create submenus within the menu
                self.GenerateMenuBar(item, root=menubarWidget)
            elif item.tag == "separator":
                menubarWidget.add_separator()
            elif item.tag == "command":
                function = item.attrib.pop('command', '')
                if function != '':
                    item.attrib['command'] = lambda f=function: self.OnCallback(
                        f)

                menubarWidget.add(item.tag, label=item.text, **item.attrib)
            else:
                boolVar = BooleanVar()
                value = item.attrib.pop("value", True)
                boolVar.set(value)

                menubarWidget.add(item.tag, label=item.text)

        if root == self.root:
            self.root.config(menu=menubarWidget)
        else:
            root.add_cascade(
                label=menubar.attrib['label'], menu=menubarWidget, underline=0)

    def GenerateNotebook(self, notebook, root):
        # Make each child of notebook object their own page
        # return the notebook object so it can be used elsewhere
        widget = ttk.Notebook(root)
        for index, child in enumerate(notebook):
            tabName = child.attrib.pop("tabname", "Tab {0}".format(index+1))
            tabFrame = Frame(widget)
            tabFrame.rowconfigure(0, weight=1)
            tabFrame.columnconfigure(0, weight=1)
            element = self.GenerateElement(child, root=tabFrame)
            element.grid(sticky='NSEW')
            widget.add(tabFrame, text=tabName)
        return widget

    def GenerateVerticalLayout(self, vertical, root):
        scrolled = vertical.attrib.pop("scrolled", False)
        frameWidget = Frame(root)
        frameWidget.columnconfigure(0, weight=1)
        for index, child in enumerate(vertical):
            self.AddChildToVerticalLayout(child, index, frameWidget)
        return frameWidget

    def AddChildToVerticalLayout(self, child, index, parent):
        parent.rowconfigure(index, **self.GetConfigureAttributes(child,"vertical."))
        grida = self.GetGridAttributes(child,"vertical.")
        grida["row"] = index
        grida["column"] = 0
        childWidget = self.GenerateElement(child, parent)

        childWidget.grid(**grida)

    def GenerateHorizontalLayout(self, horizontal, root=None):
        if root == None:
            root = self.root  # same as vertical but set coumn not row
        frameWidget = Frame(root)
        frameWidget.rowconfigure(0, weight=1)
        for index, child in enumerate(horizontal):

            frameWidget.columnconfigure(index, **self.GetConfigureAttributes(child,"horizontal."))
            grida = self.GetGridAttributes(child,"horizontal.")
            grida["row"] = 0
            grida["column"] = index
            
            childWidget = self.GenerateElement(child, root=frameWidget)

            childWidget.grid(**grida)
        return frameWidget

    def OnCallback(self, tag, *args):
        if tag in self.callbacks:
            self.callbacks[tag](*args)



    def __init__(self, tkml="",filename="", **kw):
        """Create A TKML Window"""
        if filename == "" and tkml == "":
            raise Exception("No Markup Specified")
        
        elif tkml == "":
            with open(filename) as f:
                tkml = f.read()

        self.values = {}
        # compile tkml to elements
        self.pages = kw.pop("pages",{})
        self.pages['root'] = tkml

        self.customs = {}
        # Element('tkml', tkml).children[0]

        
        self.callbacks = {}
        self.elements = {}
        self.styles = {}

        root = kw.pop("root",None)
        if root == None:
            self.root = Tk()
        else:
            self.root = root
            
        
        if (kw.pop("generate",True)):
            self.GenerateWindow()
        
    def GenerateWindow(self):
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        pages = {}
        for item in self.pages.keys():
            markup = self.pages[item]
            rootElement = ET.fromstring(markup)

            rootWidget = next(self.GenerateChildren(rootElement, self.root))

            rootWidget.grid(column=0, row=0)
            pages[item] = rootWidget

        self.pages = pages
        self.pages['root'].tkraise()

    #Turn window.values["varname"].get() into window.varname

    def __getattr__(self,name:str):
        if name == "values":
            super().__getattribute__(name)

        if name in self.values:
            return self.values[name].get()
        else:
            getattr(self,name)

    def __setattr__(self,name:str,value):
        if name == "values":
            object.__setattr__(self,name,value)

        if name in self.values:
            self.values[name].set(value)
        else:
            object.__setattr__(self,name,value)

    def ChangeToPage(self, page):
        # functions avalible to start the window
        self.pages[page].tkraise()

    def mainloop(self):
        self.root.mainloop()

    def AppendElements(self, tkml, parent):
        """Adds an element to a vertical element group"""
        # TODO Allow this to work on all widget tpyes, not just vertical

        rootElement =  ET.fromstring(tkml)
        if rootElement.tag == 'body':  # if only one element needs to be added the compiler dies :(
            # temporary fix to this by wrapping the object in the body tag before compiling
            rootElement = rootElement[0]
        childIndex = len(parent.children.values())

        self.AddChildToVerticalLayout(rootElement, childIndex, parent)

    def __enter__(self):
        # on enter with statement
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # on exit with statement do mainloop
        self.mainloop()


