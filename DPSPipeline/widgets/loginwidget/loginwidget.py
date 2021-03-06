import sys
import sharedDB
import projexui
from DPSPipeline.database.connection import Connection

from PyQt4 import QtGui,QtCore
from PyQt4.QtGui    import QWidget
from PyQt4.QtCore   import QDate,QTime
from DPSPipeline.database import projects

class LoginWidget(QWidget):
   
    def __init__( self, parent = None ):
        
        super(LoginWidget, self).__init__( parent )
	
        # load the user interface# load the user interface
        if getattr(sys, 'frozen', None):
	    projexui.loadUi(sys._MEIPASS, self, uifile = (sys._MEIPASS+"/ui/loginwidget.ui"))	    
	else:
	    projexui.loadUi(__file__, self)
        
        # define custom properties
       
	sharedDB.loginWidget = self
        
        self._backend               = None
	self.setWindowFlags(QtCore.Qt.Tool|QtCore.Qt.WindowStaysOnTopHint)
	
	
        #connects buttons
        self.loginButton.clicked.connect(self.Login)
	self.user.returnPressed.connect(self.Login)
	self.password.returnPressed.connect(self.Login)
	
	if (sharedDB.autologin):
	    self.user.setText("dkonieczka")
	    self.password.setText("doodle")
	    self.Login()
	    self.close()
	
    def Login(self):        
        #print "Logging In"	
	sharedDB.mySQLConnection = Connection(_user = str(self.user.text()), _password = str(self.password.text()))
	
	if (self.remoteAccess.isChecked() or sharedDB.remote):
	    sharedDB.mySQLConnection.setHost("remote")
	else:
	    sharedDB.mySQLConnection.setHost("local")	
	
	if sharedDB.mySQLConnection.testConnection():	    
	    sharedDB.users.GetAllUsers()
	    for userid in sharedDB.myUsers:
		user = sharedDB.myUsers[str(userid)]
		if sharedDB.testuser != 0:
		    if str(user._username).lower() == str(sharedDB.testuser).lower():
			sharedDB.currentUser = user
		elif str(user._username).lower() == str(sharedDB.loginWidget.user.text()).lower():
		    sharedDB.currentUser = user
		    break
	    
	    sharedDB.mainWindow.EnableMainWindow()
	    sharedDB.mySQLConnection._queryProcessor.start()
	    self.close()
	    
	else:
	    message = QtGui.QMessageBox.question(self, 'Message',
            "Incorrect Username or Password", QtGui.QMessageBox.Ok)