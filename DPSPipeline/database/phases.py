import mysql.connector
import sharedDB
from DPSPipeline.database.connection import Connection

'''
'1', 'Storyboarding'
'2', 'Modeling'
'3', 'Rigging'
'4', 'Layout'
'5', 'Blocking'
'6', 'Animation'
'7', 'Approval'
'8', 'Set Dressing'
'9', 'FX'
'10', 'Sound(Final)'
'11', 'Texturing'
'12', 'Shotprep'
'13', 'Lookdev'
'14', 'Lighting'
'15', 'Rendering'
'16', 'DUE'
'17', 'Sound (Rough)'
'''

class Phases():

	def __init__(self,_idphases = 0,_name = '',_ganttChartBGColor = '255,0,0',_ganttChartTextColor = '0,0,0',_manHoursToMinuteRatio = "0.1",_iddepartments = 0,_taskPerShot = 1,_defaultTaskStatus = 0):
		
		# define custom properties
		self._idphases           = _idphases
		self._name               = _name
		self._ganttChartBGColor    = _ganttChartBGColor
		self._ganttChartTextColor    = _ganttChartTextColor
		self._manHoursToMinuteRatio    = _manHoursToMinuteRatio
		self._iddepartments    = _iddepartments
		self._taskPerShot     = _taskPerShot
		self._defaultTaskStatus = _defaultTaskStatus
		
		if (sharedDB.currentUser._iddepartments == 0 or sharedDB.currentUser._iddepartments == _iddepartments):
			self._visible = 1
		else:
			self._visible = 0
			
def GetPhaseNames():
	phases = []

	rows = sharedDB.mySQLConnection.query("SELECT idphases,name,ganttChartBGColor,ganttChartTextColor,manHoursToMinuteRatio,idDepartment,taskPerShot,defaultTaskStatus FROM phases")
	
	for row in rows:
		#print row[0]
		phases.append(Phases(_idphases = row[0],_name = row[1],_ganttChartBGColor = row[2],_ganttChartTextColor = row[3],_manHoursToMinuteRatio = row[4],_iddepartments = row[5],_taskPerShot = row[6],_defaultTaskStatus = row[7]))

	return phases

def getPhaseByID(sentid):
	for phase in sharedDB.myPhases:		
		if str(phase._idphases) == str(sentid):
			return phase