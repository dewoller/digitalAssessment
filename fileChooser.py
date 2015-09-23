#!/usr/bin/python
import os
import wx
import processFile
import re
 
wildcardZip = "Compressed zip files (*.zip)|*.zip|" \
            "All files (*.*)|*.*"
 
wildcardXLS = "Excel files (*.xls*)|*.xls*" 
 
 
########################################################################
class MyForm(wx.Frame):
 
    #----------------------------------------------------------------------
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          "Mark Coding Assignments")
        self.defaultOutputFile = ""
        self.saveWildcard = ""
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.currentDirectory = os.getcwd()
        maf=""
        ts=""
        tss=""
 
        # create the buttons and bindings
        self.answerFileDlgBtn = wx.Button(self.panel, label="Model Answer File")
        self.answerFileDlgBtn.Bind(wx.EVT_BUTTON, self.onOpenAnswerFile)
 
        self.singleFileDlgBtn = wx.Button(self.panel, label="Single Submission File")
        self.singleFileDlgBtn.Bind(wx.EVT_BUTTON, self.onOpenSingleFile)

        self.zipFileDlgBtn = wx.Button(self.panel, label="Zip file containing multiple submissions")
        self.zipFileDlgBtn.Bind(wx.EVT_BUTTON, self.onOpenZipFile)
 
        self.saveFileDlgBtn = wx.Button(self.panel, label="Output File")
        self.saveFileDlgBtn.Bind(wx.EVT_BUTTON, self.onSaveFile)
        self.saveFileDlgBtn.Enable(False)
 
        self.markBtn = wx.Button(self.panel, label="         Mark!         ")
        self.markBtn.Bind(wx.EVT_BUTTON, self.onDoMark)
        self.markBtn.Enable(False)
 
        self.answerFilePrompt = wx.StaticText(self.panel, label="Answer File:")
        self.singleFilePrompt = wx.StaticText(self.panel, label="Single File:")
        self.zipFilePrompt = wx.StaticText(self.panel, label="Zip File:")
        self.saveFilePrompt = wx.StaticText(self.panel, label="Save File:")

        self.answerFile = wx.TextCtrl(self.panel, 
                style=wx.TE_MULTILINE|wx.TE_READONLY, size=(380, 75), value=maf)
        self.singleFile = wx.TextCtrl(self.panel, 
                style=wx.TE_MULTILINE|wx.TE_READONLY, size=(380, 75), value=ts)
        self.zipFile = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY, size=(380, 75))
        self.saveFile = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY, size=(380, 75), value=tss)

        # Set sizer for the frame, so we can change frame size to match widgets

        # hgap is between columns, vgap between rows
        self.sizer = wx.GridBagSizer(hgap=10, vgap=5)

        self.sizer.Add(self.answerFilePrompt, pos=(0, 0)) 
        self.sizer.Add(self.answerFile, pos=(0, 1))  
        self.sizer.Add(self.answerFileDlgBtn, pos=(0, 2))  

        self.sizer.Add(self.singleFilePrompt, pos=(1, 0)) 
        self.sizer.Add(self.singleFile, pos=(1, 1))  
        self.sizer.Add(self.singleFileDlgBtn, pos=(1, 2))  

        self.sizer.Add(self.zipFilePrompt, pos=(2, 0)) 
        self.sizer.Add(self.zipFile, pos=(2, 1))  
        self.sizer.Add(self.zipFileDlgBtn, pos=(2, 2))  

        self.sizer.Add(self.saveFilePrompt, pos=(3, 0)) 
        self.sizer.Add(self.saveFile, pos=(3, 1))  
        self.sizer.Add(self.saveFileDlgBtn, pos=(3, 2))  

        self.sizer.Add(self.markBtn, pos=(4, 0)) 


        # Set simple sizer for a nice border
        self.border = wx.BoxSizer()
        self.border.Add(self.sizer, 1, wx.ALL | wx.EXPAND, 5)

        # Use the sizers
        self.panel.SetSizerAndFit(self.border)  
        self.SetSizerAndFit(self.sizer) 
        self.enableBtns()




    #----------------------------------------------------------------------
    def enableBtns( self ):
        self.markBtn.Enable( (
         (self.singleFile.GetValue() != "" or self.zipFile.GetValue() != "") 
                    and self.saveFile.GetValue() != ""
                    and self.answerFile.GetValue() != ""))
    
        self.saveFileDlgBtn.Enable( (
         (self.singleFile.GetValue() != "" or self.zipFile.GetValue() != "") ))
                    
    
    #----------------------------------------------------------------------
    def onOpenAnswerFile(self, event):
        dlg = wx.FileDialog(
            self, message="Choose answer file",
            defaultDir=self.currentDirectory, 
            defaultFile="",
            wildcard=wildcardXLS,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.answerFile.SetValue( dlg.GetPath())
            self.enableBtns()
        dlg.Destroy()
    #----------------------------------------------------------------------
    def onOpenSingleFile(self, event):
        dlg = wx.FileDialog(
            self, message="Choose student submission file",
            defaultDir=self.currentDirectory, 
            defaultFile="",
            wildcard=wildcardXLS,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.singleFile.SetValue( dlg.GetPath())
            self.zipFile.SetValue( "")
            self.markBtn.SetLabel("Mark single submission")
            self.defaultOutputFile =  dlg.GetPath() + ".results.xlsx"
            if self.saveWildcard != wildcardXLS:
                self.saveFile.SetValue("")
            self.saveWildcard = wildcardXLS
            self.enableBtns()
        dlg.Destroy()
    #----------------------------------------------------------------------
    def onOpenZipFile(self, event):
        dlg = wx.FileDialog(
            self, message="Choose LMS student submission zip file",
            defaultDir=self.currentDirectory, 
            defaultFile="",
            wildcard=wildcardZip,
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.zipFile.SetValue( dlg.GetPath())
            self.singleFile.SetValue("")
            self.markBtn.SetLabel("Mark multiple submissions")
            self.defaultOutputFile =  dlg.GetPath() + ".results.zip"
            if self.saveWildcard != wildcardZip:
                self.saveFile.SetValue("")
            self.saveWildcard = wildcardZip
            self.enableBtns()
        dlg.Destroy()
 
    #----------------------------------------------------------------------
    def onSaveFile(self, event):
        """
        Create and show the Save FileDialog
        """
        dlg = wx.FileDialog(
            self, message="Save output as ...", 
            defaultDir=self.currentDirectory, 
            defaultFile= self.defaultOutputFile,
            wildcard=self.saveWildcard, style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.saveFile.SetValue( dlg.GetPath())
            self.enableBtns()
        dlg.Destroy()
 
#----------------------------------------------------------------------
    def onDoMark(self, event):
        wait = wx.BusyCursor()
        if self.singleFile.GetValue() != "":
            out  = self.saveFile.GetValue()
            if not re.match( ".*xlsx", out ):
                out = out + ".xlsx"
            processFile.processSubmission( self.answerFile.GetValue(), 
                self.singleFile.GetValue(), out )
        else:
            processFile.processSubmissionZip( self.answerFile.GetValue(), 
                self.zipFile.GetValue(), self.saveFile.GetValue())
        del wait
 
#----------------------------------------------------------------------
# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frame = MyForm()
    frame.Show()
    app.MainLoop()
