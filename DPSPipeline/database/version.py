
from DPSPipeline.database.connection import Connection
import sharedDB
#from DPSPipeline.projectview import ProjectView

from projexui import qt

from PyQt4 import QtCore
from PyQt4.QtCore import QObject

from datetime import datetime

class Version(QObject):

	newVersion = QtCore.pyqtSignal(QtCore.QString)
	
	def __init__(self, _name = ''):
		super(QObject, self).__init__()
		
		# define custom properties
		#self._idversion             = _idversion
		self._name                   = _name
			
	def CheckVersion(self):

		if not sharedDB.ignoreVersion:
			rows,lastrowid = sharedDB.mySQLConnection.query("SELECT name FROM version ORDER BY timestamp DESC", limitOverride = 1)

			if not str(rows[0][0]) == str(self._name):
				return False

		return True