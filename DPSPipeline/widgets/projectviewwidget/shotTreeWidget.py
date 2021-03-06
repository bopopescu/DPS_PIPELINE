import sharedDB

import re

from PyQt4 import QtCore,QtGui
from DPSPipeline.widgets import noWheelCombobox
from DPSPipeline.widgets.projectviewwidget import shotTreeWidgetItem
import operator
from PyQt4.QtCore import pyqtSlot,SIGNAL,SLOT

class ShotTreeWidget(QtGui.QTreeWidget):
    
    newVersion = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self,_project,_sequence,_parentWidgetItem):
        super(QtGui.QTreeWidget, self).__init__()
       
        self.phaseList = []
        #self._project = _project
        self._sequence = _sequence
        self.setProject(_project)
        
        self._parentWidgetItem = _parentWidgetItem
        
        self.rowHeight = 45

        self.shotTreeItem = QtGui.QTreeWidgetItem()

        self.SetupTable()
        self.UpdateShots()        
        self.UpdateBackgroundColors()
        
        self.itemEntered.connect(self.ChangeSelection)
	self.itemPressed.connect(self.ChangeSelection)
        
        if hasattr(_parentWidgetItem, 'sequenceDescription'):
            self.itemEntered.connect(self._parentWidgetItem.sequenceDescription.UpdateShotNumberValue)
            self.itemPressed.connect(self._parentWidgetItem.sequenceDescription.UpdateShotNumberValue)
        
        sharedDB.mySQLConnection.newTaskSignal.connect(self.AttachTaskToButton)
        
	self.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
	self.header().customContextMenuRequested.connect( self.showProjectMenu)
	
        #disables vertical scroll bar
        #self.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
    
    def SetupTable(self):
        if self._phases is not None:
        
            self.shotPhaseNames = ["ShotID","Name"]
             
            self.statuses = ["Not Started","In Progress","On Hold","Done"]        
            
            self.SetShotPhaseNames()
            
            self.setHeaderLabels(self.shotPhaseNames)
            
            #Hides project id column				
            self.setColumnHidden(0,True)
            self.header().setResizeMode(QtGui.QHeaderView.Fixed)
            self.setColumnWidth(1,40)
    
            #center all headers
            for col in range(0,len(self.shotPhaseNames)):
                self.headerItem().setTextAlignment(col,QtCore.Qt.AlignHCenter)
                self.header().setResizeMode(col,QtGui.QHeaderView.Fixed)
                self.setColumnWidth(col,85)
    
    
    def UpdateShots(self):
        if self._shots is not None:
            self.clear()
            if len(self._shots.values()):
		sortedShots = self._shots.values()
		sortedShots.sort(key=operator.attrgetter('_number'))

		#self._shots.sort(key=operator.attrgetter('_number'))
		for x in range(0, len(sortedShots)):
		    shot=sortedShots[x]                    
		    
		    shotWidgetItem = shotTreeWidgetItem.ShotTreeWidgetItem(shotWidget = self,shotPhaseNames = self.shotPhaseNames, shot = shot, phases = self.phaseList, project = self._project)
		    shotWidgetItem.setSizeHint(3,QtCore.QSize(0,self.rowHeight))
		    
		    if str(shot._idstatuses) == "5" or str(shot._idstatuses) == "6":
			shotWidgetItem.setHidden(1)
		self.sortItems(1,QtCore.Qt.AscendingOrder)
		
		self.UpdateWidgetHeight()
    def UpdateWidgetHeight(self):
        
        height = self.topLevelItemCount()*self.rowHeight+40
        #self._parentWidgetItem.setSizeHint(0,QtCore.QSize(0,height))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(0,height)
        
    
    def UpdateBackgroundColors(self):
        try:
	    for x in range(0,self.topLevelItemCount()):           
	    
		#sets alternating background colors
		bgc = QtGui.QColor(200,200,200)			
		if x%2:
		    bgc = QtGui.QColor(250,250,250)
		     
		     
                for col in range(0,self.columnCount()):
                    self.topLevelItem(x).setBackground(col,bgc)
	except:
	    print "Unable to change color on shot item, sequence was removed from list"
    
    def AddShot(self,shot):
        #print self.shotPhaseNames[0]
        #print shot._number
        #print self._phases
        #print self._project._name
        shotWidgetItem = shotTreeWidgetItem.ShotTreeWidgetItem(shotWidget = self,shotPhaseNames = self.shotPhaseNames, shot = shot, phases = self.phaseList, project = self._project)
        self.sortItems(1,QtCore.Qt.AscendingOrder)
        self.UpdateBackgroundColors()
        shotWidgetItem.setSizeHint(3,QtCore.QSize(0,self.rowHeight))
        self.UpdateWidgetHeight()
    
    def SetShotPhaseNames(self):        
        #for phaseid in self._phases:
        #    phase = self._phases[str(phaseid)]
	self.phaseList = []
	for phase in self._phases:
	    if phase._taskPerShot and str(phase._idstatuses) != '5' and str(phase._idstatuses) != '6':
                self.phaseList.append(phase)
		self.shotPhaseNames.append(phase._name)        
    
    def AttachTaskToButton(self, idtasks):
        #find task with id
        task = None
        if str(idtasks) in sharedDB.myTasks:
	    task = sharedDB.myTasks[str(idtasks)] 
        
        if task is not None:
            #iterate through items to find correct shot index
            for x in range(0,self.topLevelItemCount()):
                if self.topLevelItem(x).shot._idshots == task._idshots:
                    sTreeWidgetItem = self.topLevelItem(x)
                    for btn in sTreeWidgetItem.btns:
                        #if btn phaseid = task phase id
                        if str(btn._forPhase) == str(task._idphases):
                            btn._task = task
                            btn.getTaskState()
                            task.taskChanged.connect(btn.getTaskState)
                    
                    break
        
    def setProject(self, project):
        self._project = project
        if project is not None:
            self._phases = project._phases.values()
	    self._phases.sort(key=operator.attrgetter('_startdate'))
            if self._sequence is not None:
                self._shots = self._sequence._shots
            else:
                self._shots = None
        else:
            self._phases = None
            self._shots = None
    
    #Disable arrow keys for this qtree
    def keyPressEvent(self, event):
        pass
    
    def wheelEvent(self, event):
	if hasattr (self._parentWidgetItem, "_progressList"):
            self._parentWidgetItem._progressList.wheelEvent(event)
    
    def ChangeSelection(self,itemwidget, column):
        sharedDB.sel.select([itemwidget,itemwidget.shot])
	
    def showProjectMenu( self, pos):
        """
        Displays the header menu for this tree widget.
        
        :param      pos | <QPoint> || None
        """
        '''
	
	header = self.header()
        index  = header.logicalIndexAt(pos)
        self._headerIndex = index
        
        # show a pre-set menu
        if self._headerMenu:
            menu = self._headerMenu
        else:
            menu = self.createHeaderMenu(index)
        '''
	#print self.uiGanttTREE.itemFromIndex(index)._dbEntry._type
	
	#point = QtGui.QCursor.pos()
        
        #self.headerMenuAboutToShow.emit(menu, index)
	
	#menu	 = QtGui.QMenu()
        
        #statusMenu = menu.addMenu("Status Visibility")
	
        #menu.exec_(point)
	
	headerText = self.headerItem().text(self.header().logicalIndexAt(pos))
	
	index =  self.header().logicalIndexAt(pos);
	
	#globalPos = self.mapToGlobal(pos)
	menu = QtGui.QMenu()
	
	point = QtGui.QCursor.pos()
        
	if headerText != "Name":
	    #statusMenu = menu.addMenu("Status Visibility")
	    if sharedDB.currentUser._idPrivileges < 3:
		menu.addAction(('APPROVE ALL '+ headerText))
		#approveAll.triggered.connect(self.toggleShowNotStartedAction)
		menu.addSeparator()
	    
	    menu.addAction("Claim all shots - "+headerText)
	    
	    menu.addSeparator()
	    
	    selectPhaseAction = menu.addAction("Select "+headerText+" Phase")
	    selectPhaseAction.setData("phaseassignment_"+str(self.phaseList[index-2].id()))
	    
	    selectProjectAction = menu.addAction("Select Project")
	    selectProjectAction.setData("project_"+str(self._project.id()))
	    
	    menu.triggered.connect( self.contextMenuActions )
	    menu.exec_(point)
	    
    
    def contextMenuActions(self, action):
	#go through rows of text	
	if ( action.text().contains("APPROVE ALL") ):
	    headerText = re.sub("APPROVE ALL ","",str(action.text()))
	    for x in range(0,self.columnCount()):
		if self.headerItem().text(x) == headerText:
		    for y in range(0,self.topLevelItemCount()):
			taskwidget = self.itemWidget(self.topLevelItem(y),x)
			if taskwidget._btn._task is not None and taskwidget._btn._currentState == 2:
			    taskwidget._btn.updateApproval()
	elif ( action.text().contains("Claim all shots") ):
	    headerText = re.sub("Claim all shots - ","",str(action.text()))
	    username = sharedDB.currentUser._name
	    for x in range(0,self.columnCount()):
		if self.headerItem().text(x) == headerText:
		    for y in range(0,self.topLevelItemCount()):
			taskwidget = self.itemWidget(self.topLevelItem(y),x)
			if taskwidget._uLabel.task is not None and taskwidget._uLabel.task._idusers == 0:
			    taskwidget._uLabel.setUserFromName(username)
	elif ( action.text().contains("Select ") ):
	    actiondata = action.data().toPyObject().split("_")	    
	    if actiondata[0] == "phaseassignment":
		sharedDB.sel.select([sharedDB.myPhaseAssignments[str(actiondata[1])]])
	    if actiondata[0] == "project":
		sharedDB.sel.select([sharedDB.myProjects[str(actiondata[1])]])
	    
	