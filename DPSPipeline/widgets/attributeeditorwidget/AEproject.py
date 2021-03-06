import projexui
import sharedDB
import sys

from DPSPipeline.widgets import textEditAutosave

from PyQt4 import QtGui,QtCore

class AEProject(QtGui.QWidget):

    def __init__( self, parent = None ):
    
	super(AEProject, self).__init__( parent )
	
	'''
	# load the user interface# load the user interface
	if getattr(sys, 'frozen', None):
	    projexui.loadUi(sys._MEIPASS, self, uifile = (sys._MEIPASS+"/ui/AEproject.ui"))	    
	else:
	    projexui.loadUi(__file__, self)
	'''
	self.setMinimumSize(300,0)
	self.resize(300,self.height())
		    
	self.baseLayout = QtGui.QVBoxLayout()
	self.baseLayout.setContentsMargins(2,2,2,2)
	self.setLayout(self.baseLayout)
	
	self.ProjectBox = QtGui.QGroupBox()
	self.baseLayout.addWidget(self.ProjectBox)
	
	self.aeprojectlayout = QtGui.QVBoxLayout()
	self.aeprojectlayout.setContentsMargins(2,2,2,2)
	self.ProjectBox.setLayout(self.aeprojectlayout)


	#Status Box
	self.statusBox = QtGui.QGroupBox()
	self.statusBox.setTitle("Status")
	self.aeprojectlayout.addWidget(self.statusBox)

	self.projectStatus = QtGui.QComboBox()
	self.projectStatus.currentIndexChanged[QtCore.QString].connect(self.saveStatus)
	#self.projectStatus.currentIndexChanged[QtCore.QString].connect(sharedDB.myTasksWidget.propogateUI)
	
	self.statusLayout = QtGui.QVBoxLayout()
	self.statusLayout.setContentsMargins(2,2,2,2)
	self.statusBox.setLayout(self.statusLayout)
	self.statusLayout.addWidget(self.projectStatus)
	
	#Status Description Box
	self.statusDescrBox = QtGui.QGroupBox()
	self.statusDescrBox.setFixedHeight(70)
	self.statusDescrBox.setTitle("Status Description")
	self.aeprojectlayout.addWidget(self.statusDescrBox)
	
	self.statusDescription = textEditAutosave.TextEditAutoSave()
	self.statusDescription.save.connect(self.SaveStatusDescription)
	
	self.statusDescrLayout = QtGui.QVBoxLayout()
	self.statusDescrLayout.setContentsMargins(2,2,2,2)
	self.statusDescrBox.setLayout(self.statusDescrLayout)
	self.statusDescrLayout.addWidget(self.statusDescription)
	
	
	#Budget
	self.budgetBox = QtGui.QGroupBox()
	self.budgetBox.setFixedHeight(70)
	self.budgetBox.setTitle("Budget")
	self.aeprojectlayout.addWidget(self.budgetBox)
	
	self.budgetsb = QtGui.QSpinBox()
	self.budgetsb.setValue(0)
	#validator = QtGui.QIntValidator()
	#self.budgetLine.setValidator(validator)
	self.budgetsb.setMinimum(0)
	self.budgetsb.setMaximum(999999999)
	self.budgetsb.setPrefix("$")
	self.budgetsb.valueChanged.connect(self.saveBudget)
	
	self.budgetLayout = QtGui.QVBoxLayout()
	self.budgetLayout.setContentsMargins(2,2,2,2)
	self.budgetBox.setLayout(self.budgetLayout)
	self.budgetLayout.addWidget(self.budgetsb)
	
	#Total Hours Assigned
	self.hoursBox = QtGui.QGroupBox()
	self.hoursBox.setFixedHeight(70)
	self.hoursBox.setTitle("Hours Assigned")
	self.aeprojectlayout.addWidget(self.hoursBox)
	
	self.hoursLine = QtGui.QLabel("0")

	self.hoursLayout = QtGui.QVBoxLayout()
	self.hoursLayout.setContentsMargins(2,2,2,2)
	self.hoursBox.setLayout(self.hoursLayout)
	self.hoursLayout.addWidget(self.hoursLine)	

	#Bottom spacer
	self.spacer = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
	self.aeprojectlayout.addItem(self.spacer)

	self.setHidden(1)
	self.setEnabled(0)
    
    def LoadProject(self, sentProject):

	self._blockUpdates = 1
	
	if isinstance(sentProject, sharedDB.projects.Projects):
	    self._currentProject = sentProject

	if self._currentProject is not None:
	    
	    if len(sharedDB.sel.items):
		if hasattr(sharedDB.sel.items[len(sharedDB.sel.items)-1], "_type") and sharedDB.sel.items[len(sharedDB.sel.items)-1]._type == "project":	    
		    self.setEnabled(1)
		    self.setHidden(0)
		    self.setPrivileges()
		    
		    self._currentProject.projectChanged.connect(self.LoadProject)	    
		    
		    #set title
		    self.ProjectBox.setTitle("Project: "+str(self._currentProject._name))
		    
		    #set Status
		    self.propogateStatuses()
		    self.setStatus()
		    
		    #set Description
		    self.statusDescription.blockSignals = 1
		    
		    #set Budget
		    self.budgetsb.setValue(int(self._currentProject._budget))
		    
		    #set Hours assigned
		    self.setHoursLine()
		    
		    self.statusDescription.setText("")
		    if self._currentProject._statusDescription is not None:			
			self.statusDescription.setSource(self._currentProject,'_statusDescription')
			self.statusDescription.getSourceText()	
			
		    self.statusDescription.blockSignals = 0
	    
	self._blockUpdates = 0
    
    def setStatus(self):
	self.projectStatus.blockSignals(1)
	statusGoal = int(self._currentProject._idstatuses)
	
	if statusGoal<0:
	    statusGoal = 0
	    
	for x in range(0,self.projectStatus.count()):
	    if 	self.projectStatus.itemData(x).toString() == str(statusGoal):	
		self.projectStatus.setCurrentIndex(x)
		break
	
	self.projectStatus.blockSignals(0)
	
    def saveStatus(self):
	
	self._currentProject.setIdstatuses(self.projectStatus.itemData(self.projectStatus.currentIndex()).toString())
    
    def saveBudget(self):
	
	self._currentProject.setBudget(self.budgetsb.value())
        
    def setPrivileges (self):
	if sharedDB.currentUser._idPrivileges > 1:
	    self.budgetBox.setHidden(1)
	    
	if sharedDB.currentUser._idPrivileges < 2:
	    self.projectStatus.setEnabled(1)
	    self.statusDescription.setEnabled(1)
	else:
	    self.projectStatus.setEnabled(0)
	    self.statusDescription.setEnabled(0)
	
    def setHoursLine (self):
	hours = 0
	
	for phase in self._currentProject._phases.values():
	    if phase._idstatuses != 5 and phase._idstatuses != 6:
		hours = hours + int(phase._hoursalotted)
	    
	self.hoursLine.setText(str(hours))
	
    
    
    def propogateStatuses(self):
	self.projectStatus.blockSignals(1)
	self.projectStatus.clear()
	for status in sharedDB.myStatuses.values():
	    self.projectStatus.addItem(status._name, QtCore.QVariant(status._idstatuses))
	self.projectStatus.blockSignals(0)
	
    def SaveStatusDescription(self):
	#if not self._blockUpdates:
	if self._currentProject is not None:
	    if not (self.statusDescription.toPlainText() == self._currentProject._statusDescription):
		    self._currentProject._statusDescription = self.statusDescription.toPlainText()
		    self._currentProject._updated = 1