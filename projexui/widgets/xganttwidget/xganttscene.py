#!/usr/bin/python

""" Custom backend for managing gantt widget items within the view. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

from PyQt4.QtCore   import QDate,\
                                 QLine,\
                                 QRect,\
                                 Qt
                           
from PyQt4.QtGui    import QGraphicsScene,\
                                 QLinearGradient,\
                                 QBrush,\
                                 QColor

from datetime import datetime

class XGanttScene(QGraphicsScene):
    def __init__( self, ganttWidget ):
        super(XGanttScene, self).__init__(ganttWidget)
        
        # setup custom properties
        self._ganttWidget       = ganttWidget
        self._hlines            = []
        self._vlines            = []
        self._alternateRects    = []
        self._weekendRects      = []
	self._bookedRects      = []
	self._overbookedRects      = []
	self._underbookedRects      = []
	self._unassignedRects      = []
        self._topLabels         = []
        self._labels            = []
        self._dirty             = True
        
	self._maxOverbooked = 0
	
        # create connections
        ganttWidget.dateRangeChanged.connect(self.setDirty)
    
    def dateAt( self, x ):
        """
        Returns the date at the inputed x position.
        
        :return     <QDate>
        """
        gantt       = self.ganttWidget()
        dstart      = gantt.dateStart()
        days        = int(x / float(gantt.cellWidth()))
        
        return dstart.addDays(days)
    
    def dateXPos( self, date ):
        """
        Returns the x-position for the inputed date.
        
        :return     <int>
        """
        gantt    = self.ganttWidget()
        distance = gantt.dateStart().daysTo(date)
        return gantt.cellWidth() * distance
    
    def drawForeground( self, painter, rect ):
        """
        Draws the foreground for this scene.
        
        :param      painter | <QPainter>
                    rect    | <QRect>
        """
        gantt  = self.ganttWidget()
        header = gantt.treeWidget().header()
        width  = self.sceneRect().width()
        height = header.height()
        
        # create the main color
        palette     = gantt.palette()
        color       = palette.color(palette.Button)
        textColor   = palette.color(palette.ButtonText)
        borderColor = color.darker(140)
        text_align  = Qt.AlignBottom | Qt.AlignHCenter
        y           = rect.top()
        
        # create the gradient
        gradient = QLinearGradient()
        gradient.setStart(0, y)
        gradient.setFinalStop(0, y + height)
        gradient.setColorAt(0, color)
        gradient.setColorAt(1, color.darker(120))
        
        painter.setBrush(QBrush(gradient))
        painter.drawRect(0, y, width, height)
        
        # add top labels
        for rect, label in self._topLabels:
            rx = rect.x()
            ry = rect.y() + y
            rw = rect.width()
            rh = rect.height()
            
            painter.setPen(borderColor)
            painter.drawRect(rx, ry, rw, rh)
            
            painter.setPen(textColor)
            painter.drawText(rx, ry, rw, rh - 2, text_align, label)
        
        # add bottom labels
        for rect, label in self._labels:
            rx = rect.x()
            ry = rect.y() + y
            rw = rect.width()
            rh = rect.height()
            
            painter.setPen(borderColor)
            painter.drawRect(rx, ry, rw, rh)
            
            painter.setPen(textColor)
            painter.drawText(rx, ry, rw, rh - 2, text_align, label)
    
    def drawBackground( self, painter, rect ):
        """
        Draws the background for this scene.
        
        :param      painter | <QPainter>
                    rect    | <QRect>
        """
        if ( self._dirty ):
            self.rebuild()
        
        # draw the alternating rects
        gantt   = self.ganttWidget()
        
        # draw the alternating rects
        painter.setPen(Qt.NoPen)
        painter.setBrush(gantt.alternateBrush())
        for rect in self._alternateRects:
            painter.drawRect(rect)
        
        # draw the weekends
        painter.setBrush(gantt.weekendBrush())
        for rect in self._weekendRects:
            painter.drawRect(rect)
        
	# draw the holidays
	
        for rect in self._holidayRects:
            painter.setBrush(gantt.holidayBrush())
	    painter.drawRect(rect)
	    
	# draw the currentday
	if gantt._currentDayBrush is not None:
	    painter.setBrush(gantt._currentDayBrush)
	    for rect in self._currentDayRects:
		painter.drawRect(rect)
	
        # draw the default background
        painter.setPen(gantt.gridPen())
        painter.drawLines(self._hlines + self._vlines)
    
	#draw the booked
	for rect in self._bookedRects:
	    painter.setBrush(gantt.bookedBrush())
	    painter.drawRect(rect)
	    
	for rect in self._unavailableRects:
	    painter.setBrush(gantt.unavailableBrush())
	    painter.drawRect(rect)
	    
	for rect in self._bookedRects:
	    painter.setBrush(gantt.bookedBrush())
	    painter.drawRect(rect)    
	    
	for rect in self._underbookedRects:
	    painter.setBrush(gantt.underbookedBrush())
	    painter.drawRect(rect)
	
	for rect in self._unassignedRects:
	    painter.setBrush(gantt.unassignedBrush())
	    painter.drawRect(rect)
	
	for rect in self._overbookedRects:	    
	    darkenAmount = 100 + (100*( float(rect[1]) / float(self._maxOverbooked)))
	    #newBrush = gantt.overbookedBrush()[:]
	    
	    #newBrush = newBrush.setColor(newBrush.color().darker(darkenAmount))
	    painter.setBrush(QBrush(QColor(255,25,25).darker(darkenAmount)))
	    painter.drawRect(rect[0])
	    painter.drawText(rect[0], Qt.AlignCenter, str(rect[1]));
    
    def ganttWidget( self ):
        """
        Returns the gantt view that this scene is linked to.
        
        :return     <XGanttWidget>
        """
        return self._ganttWidget
    
    def isDirty( self ):
        """
        Returns if this gantt widget requires a redraw.
        
        :return     <bool>
        """
        return self._dirty
    
    def rebuild( self ):
        """
        Rebuilds the scene based on the current settings.
        
        :param      start | <QDate>
                    end   | <QDate>
        """
        gantt           = self.ganttWidget()
        start           = gantt.dateStart()
        end             = gantt.dateEnd()
        cell_width      = gantt.cellWidth()
        cell_height     = gantt.cellHeight()
        rect            = self.sceneRect()
        view            = gantt.viewWidget()
        height          = rect.height()
        header          = gantt.treeWidget().header()
        header_height   = header.height()
        
        if ( not header.isVisible() ):
            header_height   = 0
        
        self._labels            = []
        self._hlines            = []
        self._vlines            = []
        self._weekendRects      = []
	self._bookedRects       = []
	self._unavailableRects = []
	self._overbookedRects      = []
	self._underbookedRects      = []
	self._unassignedRects  = []
	self._holidayRects      = []
	self._currentDayRects   = []
        self._alternateRects    = []
        self._topLabels         = []
        
        # generate formatting info
        top_format      = 'MMM'
	Week            = 'd'
        label_format    = 'd'
        increment       = 1     # days
        
        # generate vertical lines
        x           = 0
        i           = 0
        half        = header_height / 2.0
        curr        = start
        top_label   = start.toString(top_format)
        top_rect    = QRect(0, 0, 0, half)
        alt_rect    = None
        
        while ( curr < end ):
            # update the month rect
            new_top_label = curr.toString(top_format)
            if ( new_top_label != top_label ):
                top_rect.setRight(x)
                self._topLabels.append((top_rect, top_label))
                top_rect  = QRect(x, 0, 0, half)
                top_label = new_top_label
                
                if ( alt_rect is not None ):
                    alt_rect.setRight(x)
                    self._alternateRects.append(alt_rect)
                    alt_rect = None
                else:
                    alt_rect = QRect(x, 0, 0, height)
            
            # create the line
            self._hlines.append(QLine(x, 0, x, height))
            
            # create the header label/rect
            label = str(curr.toString(label_format))
            rect  = QRect(x, half, cell_width, half)
            self._labels.append((rect, label))
            
	    # store weekend rectangles
            if ( curr.dayOfWeek() in (6, 7) ):
                rect = QRect(x, 0, cell_width, height)
                self._weekendRects.append(rect)
	    
	    # store current day rectangle
	    elif ( curr.toString("ddMMyyyy") == QDate.currentDate().toString("ddMMyyyy") ):
                rect = QRect(x, 0, cell_width, height)
                self._currentDayRects.append(rect)
		
            
            
	    # store holiday rectangles
	    
	    
	    
            # increment the dates
            curr = curr.addDays(increment)
            x += cell_width
            i += 1

	self._maxOverbooked = 0

        if gantt._availabilityEnabled:
	    #iterate through rows
	    for itemcount in range(0,gantt.topLevelItemCount()):
		#check top item, then check child items
		item = gantt.topLevelItem(itemcount)
		if item._dbEntry is not None:
		    if item._dbEntry._type == "phase":
			phase = item._dbEntry
			for key in phase._availability.keys():			    
			    if QDate.fromString(key,"yyyy-MM-dd") >= start:
				diff = start.daysTo(QDate.fromString(key,"yyyy-MM-dd"))
				rect = QRect((diff)*cell_width, header_height+cell_height*(itemcount), cell_width, cell_height)
				if phase._availability[key] == 1:
				    self._underbookedRects.append(rect)
				elif phase._availability[key] == 2:
				    self._bookedRects.append(rect)
				elif phase._availability[key] > 2:
				    if self._maxOverbooked < int (phase._availability[key]):
					self._maxOverbooked = int(phase._availability[key])
				    self._overbookedRects.append([rect,int(phase._availability[key])])
			'''
			for pa in item._dbEntry._phaseAssignments.values():
			    for key in pa._availability.keys():						    
				if pa._availability[key] > 8:
				    if QDate.fromString(key,"yyyy-MM-dd") >= start:
					diff = start.daysTo(QDate.fromString(key,"yyyy-MM-dd"))
					rect = QRect((diff)*cell_width, header_height+cell_height*(itemcount), cell_width, cell_height)
					self._overbookedRects.append(rect)
			'''
	
	
	# update the month rect
        top_rect.setRight(x)
        top_label = end.toString(top_format)
        self._topLabels.append((top_rect, top_label))
        
        if ( alt_rect is not None ):
            alt_rect.setRight(x)
            self._alternateRects.append(alt_rect)
        
        # resize the width to match the last date range
        new_width = x
        self.setSceneRect(0, 0, new_width, height)
        
        # generate horizontal lines
        y       = 0
        h       = height
        width   = new_width
        
        while ( y < h ):
            self._vlines.append(QLine(0, y, width, y))
            y += cell_height
        
        # clear the dirty flag
        self._dirty = False
    
    def setDayWidth( self, width ):
        """
        Sets the day width that will be used for drawing this gantt widget.
        
        :param      width | <int>
        """
        self._dayWidth = width
        
        start   = self.ganttWidget().dateStart()
        end     = self.ganttWidget().dateEnd()
        
        self._dirty = True

    def setWeekWidth( self, width ):
        """
        Sets the week width that will be used for drawing this gantt widget.
        
        :param      width | <int>
        """
        self._weekWidth = width*7
        
        start   = self.ganttWidget().dateStart()
        end     = self.ganttWidget().dateEnd()
        
        self._dirty = True
    
    def setDirty( self, state = True ):
        """
        Sets the dirty state for this scene.  When the scene is dirty, it will
        be rebuilt on the next draw.
        
        :param      state | <bool>
        """
        self._dirty = state
    
    def setSceneRect( self, *args ):
        """
        Overloads the set rect method to signal that the scene needs to be 
        rebuilt.
        
        :param      args | <arg variant>
        """
        super(XGanttScene, self).setSceneRect(*args)
        
        self._dirty = True