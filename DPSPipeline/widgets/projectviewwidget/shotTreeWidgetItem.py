from PyQt4 import QtCore,QtGui
from DPSPipeline.widgets import taskProgressButton
from DPSPipeline.widgets import userLabel
import sharedDB
import operator

class ShotTreeWidgetItem(QtGui.QTreeWidgetItem):
    
    def __init__(self,shotWidget = '', shotPhaseNames = [], shot = "", project = [], phases = []):
        super(QtGui.QTreeWidgetItem, self).__init__()
        self.shotWidget = shotWidget
        self.shotPhaseNames = shotPhaseNames
        self.shot = shot
        self.phases = phases
        self.project = project
        self.btns = []
        
        if shotWidget is not None:
            self.shotWidget.addTopLevelItem(self)
            
        #shot id
        self.setText(0,(str(self.shot._idshots)))
        
        #shot name
        self.setText(1,(str(self.shot._number)))        
        
        #if tasklist less than lenshotphasenames - 2
        columnIndex = 2
        
        #sort phases
        #sortedPhases = self.phases.values()
        #sortedPhases.sort(key=operator.attrgetter('_startdate'))
        
	self.setToolTip(1,("ShotID: "+str(self.shot._idshots)))
        for phase in self.phases:            
	    if phase._taskPerShot:
                currentTask = None
                
                if self.shot._tasks is not None:
                    for task in self.shot._tasks.values():
                        if task._idphases == phase._idphases:
                            currentTask = task
                
                
                #if task didn't exist, create task  
                '''
		if currentTask is None and sharedDB.autoCreateShotTasks:
                    currentTask = sharedDB.tasks.Tasks(_idphaseassignments = phase._idphaseassignments, _idprojects = self.project._idprojects, _idshots = shot._idshots, _idphases = phase._idphases, _new = 1)
                    
		    self.shot._tasks[str(currentTask.id())] = (currentTask)

                    currentTask.Save()
		    #sharedDB.myTasks.append(currentTask)
                '''        
                
                #create button for currentTask
                #btn = self.AddProgressButton(shotWidgetItem,columnIndex,85,currentTask._status)
                
                btn = taskProgressButton.TaskProgressButton(_task=currentTask,_shot = self.shot, _forPhase = phase._idphases)

                uLabel = userLabel.UserLabel(task = currentTask)
                btn.stateChanged.connect(uLabel.getUserFromTask)

                taskBtnWidget = QtGui.QWidget()
                vLayout = QtGui.QHBoxLayout()
                taskBtnWidget.setLayout(vLayout)
		taskBtnWidget._btn = btn
		taskBtnWidget._uLabel = uLabel
                vLayout.addWidget(btn)
                vLayout.addWidget(uLabel)
                self.shotWidget.setItemWidget(self,columnIndex,taskBtnWidget)
                
                self.btns.append(btn)
                
                #connect button state changed signal to task
                #print "Connecting statechange to: "+str(currentTask._idtasks)
                #btn.stateChanged.connect(currentTask.setShit)
                #btn.stateChanged.connect(self.test)

                columnIndex +=1
                
	 
		
    def deselect(self):
        self.shotWidget.UpdateBackgroundColors()
        
    def select(self):
        try:
            bgc = QtGui.QColor(250,250,0)
                                  
            for col in range(0,self.shotWidget.columnCount()):
                self.setBackground(col,bgc)
        except:
	    print "Unable to change color on shot item, sequence was removed from list"