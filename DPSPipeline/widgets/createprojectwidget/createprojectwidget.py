import weakref
import projexui
import sharedDB
import math
import sys

from datetime import timedelta
#from projexui import qt import Signal
from PyQt4 import QtGui,QtCore
from PyQt4.QtGui    import QWidget,QDockWidget
from PyQt4.QtCore   import QDate,QTime
from DPSPipeline.database import projects
#from DPSPipeline.widgets.createprojectwidget import clientIPLineEdit

class CreateProjectWidget(QWidget):
   
    def __init__( self, parent = None ):
        
        super(CreateProjectWidget, self).__init__( parent )
        
        # load the user interface# load the user interface
        if getattr(sys, 'frozen', None):
	    #print (sys._MEIPASS+"/ui/createprojectwidget.ui");
	    projexui.loadUi(sys._MEIPASS, self, uifile = (sys._MEIPASS+"/ui/createprojectwidget.ui"))
	    
	else:
	    projexui.loadUi(__file__, self)
        #projexui.loadUi(__file__, self)
        
        # define custom properties
	
	self.dockWidget = QDockWidget()
        parent.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self.dockWidget)
        self.dockWidget.setFloating(1)
        self.dockWidget.setWindowTitle("Create Project")
        self.dockWidget.setWidget(self)
	
	#self.setWindowFlags(QtCore.Qt.Tool)
        
        self._backend               = None
        
	#self.myClientNameLineEdit = clientIPLineEdit.ClientIPLineEdit(self)
	#self.clientIPBoxLayout.addWidget(self.myClientNameLineEdit)
	
        #connects buttons
        self.createButton.clicked.connect(self.CreateProject)
        self.cancelButton.clicked.connect(self.cancel)
        self.UpdateClientList()
	self.clientComboBox.currentIndexChanged.connect(self.UpdateIPList)
	
	self.UpdateIPList(self.clientComboBox.currentIndex())        
	
        #self.open()

    def UpdateClientList(self):
	self.clientComboBox.clear()
	for client in sharedDB.myClients.values():
	    self.clientComboBox.addItem(client._name,QtCore.QVariant(client._idclients))
    
    def UpdateIPList(self, sentclientcmboboxindex):
	self.ipComboBox.clear()
	#print sharedDB.myClients[str(self.clientComboBox.itemData(self.clientComboBox.currentIndex()).toString())]
	if str(self.clientComboBox.itemData(self.clientComboBox.currentIndex()).toString()) in sharedDB.myClients:
	    client = sharedDB.myClients[str(self.clientComboBox.itemData(self.clientComboBox.currentIndex()).toString())]
	    #if str(client._idclients) == self.clientComboBox.itemData(sentclientid).toString():
	    for ip in client._ips.values():
		self.ipComboBox.addItem(ip._name,QtCore.QVariant(ip._idips))


    def cancel(self):
        self.close()

    def setDefaults(self):
        #set initial values
        self.duedateEdit.setDate(QDate.currentDate().addDays(30))
        self.xres_spinBox.setValue(1280)
        self.yres_spinBox.setValue(720)
        
	self.phaseListWidget.clear()
	
        for myPhase in sharedDB.myPhases.values():        
            if myPhase._name != "DUE":
                item = QtGui.QListWidgetItem(myPhase._name)
                self.phaseListWidget.addItem(item)
                self.phaseListWidget.setItemSelected(item,True)
        
        
        self.descriptionTextEdit.setText("")
        self.durationEdit.setTime(QTime.fromString("00:01:00"))
        self.projectNameQLineEdit.setText("Project Name")
        self.fps.setValue(25)
        
    '''def open(self):
	self.show()
	self.activateWindow()
    '''	
    def CreateProject(self):        
        name = str(self.projectNameQLineEdit.text())
        folderLocation = ''
        #idstatus = 0
        idips = str(self.ipComboBox.itemData(self.ipComboBox.currentIndex()).toString())
	idclients = str(self.clientComboBox.itemData(self.clientComboBox.currentIndex()).toString())
	fps = self.fps.value()
        renderWidth = self.xres_spinBox.value()
        renderHeight = self.yres_spinBox.value()
        due_date = self.duedateEdit.date().toPyDate();
        renderPriority = 50
        description = self.descriptionTextEdit.toPlainText()
        phases = []
        
        #for each list item
        for item in self.phaseListWidget.selectedItems():
            #get phase of same name
            for x in range(0,len(sharedDB.myPhases))[::-1]:
                #print sharedDB.myPhases[x]._name
                #print item.text
                if sharedDB.myPhases.values()[x]._name == item.text():                    
		    phases.append(sharedDB.phaseAssignments.PhaseAssignments(_idphases = sharedDB.myPhases.values()[x].id(), _startdate = due_date,_enddate = due_date,_updated = 0))
                    continue
            #start from due date and work backwards
            #for 
        
        phases = InitializeDates(phases,due_date,self.durationEdit.time())
        
        #Add due date into phases
        phases.append(sharedDB.phaseAssignments.PhaseAssignments(_idphases = 16, _startdate = due_date,_enddate = due_date,_updated = 0))
        
        newProj = sharedDB.projects.Projects(_name = name, _folderLocation = '', _idstatuses = 1, _fps = fps, _renderWidth = renderWidth, _renderHeight = renderHeight, _due_date = due_date, _renderPriority = renderPriority, _description = description, _idips = idips, _idclients = idclients, _new = 0)
	
	newProj._new = 1
	newProj.Save()
	#sharedDB.myProjects.append(newProj)
	
	#connect phases to projectid
	
	for phase in phases:
	    newProj.AddPhase(phase)
	    '''
	    phase._idprojects = newProj._idprojects
	    phase.project = newProj
	    phase._new = 1
	    phase.Save()
	    newProj._phases[str(phase.id())] = phase
	    '''
	
	if str(idips) in sharedDB.myIps:
	    ip = sharedDB.myIps[str(idips)]
	    ip._projects[str(newProj.id())] = newProj
	
	newProj.UpdateStartDate()
	
        self.close();
        
def InitializeDates(phases,due_date,duration):
    currentDate = due_date
    for phase in phases[::-1]:
        #enddate = currentDate-1
        phase._enddate = currentDate - timedelta(days=1)
        
        #iterate through phases until there's a match
        if str(phase._idphases) in sharedDB.myPhases:
	    myPhase = sharedDB.myPhases[str(phase._idphases)]
	    #multiply duration(minutes) by _manHoursToMinuteRatio / work hours in a day       
	    daysGoal = math.ceil(QTime().secsTo(duration)/60.0*myPhase._manHoursToMinuteRatio/8.0)
	    #print daysGoal
	    numdays = 0
	    #while numdays < work days
	    while numdays<daysGoal:
		#subtract day from currentDate
		currentDate = currentDate - timedelta(days=1)
		#if workday
		if currentDate.weekday()<5:
		    numdays = numdays+1
	    #phase start date = currentdate
	    phase._startdate = currentDate
                
    return phases