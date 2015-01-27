#!/usr/bin/python

""" Defines the root QGraphicsScene class for the node system. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

import datetime

from projexui.qt import wrapVariant, unwrapVariant, Signal
from projexui.qt.QtCore           import  QObject, \
                                          QPointF, \
                                          QRectF, \
                                          QSize,\
                                          Qt
                                
from projexui.qt.QtGui            import  QApplication,\
                                          QBrush, \
                                          QColor, \
                                          QFontMetrics,\
                                          QGraphicsRectItem, \
                                          QLinearGradient,\
                                          QToolTip,\
                                          QCursor,\
                                          QIcon,\
                                          QPen

import projex.text
from projex.enum import enum

from projexui.xanimation import XObjectAnimation
from projexui.widgets.xnodewidget.xnodelayer      import XNodeLayer
from projexui.widgets.xnodewidget.xnodehotspot    import XNodeHotspot
from projexui.widgets.xnodewidget.xnodeconnection import XConnectionLocation,\
                                                         XNodeConnection

class XNodeDispatcher( QObject ):
    """
    The dispatcher class will represent the signal emitter for a node \
    object.  QGraphicsItem's are not QObject's (at least until Qt 4.6), \
    and so this will guarantee backward compatibility.
    """
    geometryChanged     = Signal(QPointF)
    visibilityChanged   = Signal(bool)
    removed             = Signal()

class XNodeAnimation(XObjectAnimation):
    def updateCurrentValue(self, value):
        """
        Disables snapping during the current value update to ensure a smooth
        transition for node animations.  Since this can only be called via
        code, we don't need to worry about snapping to the grid for a user.
        """
        xsnap = None
        ysnap = None
        
        if value != self.endValue():
            xsnap = self.targetObject().isXSnappedToGrid()
            ysnap = self.targetObject().isYSnappedToGrid()
            
            self.targetObject().setXSnapToGrid(False)
            self.targetObject().setYSnapToGrid(False)
        
        super(XNodeAnimation, self).updateCurrentValue(value)
        
        if value != self.endValue():
            self.targetObject().setXSnapToGrid(xsnap)
            self.targetObject().setYSnapToGrid(ysnap)

#------------------------------------------------------------------------------

class XNode( QGraphicsRectItem ):
    """
    Defines the base node class for a system. This class can and should \
    be subclassed and redefined for your specific usage of it.
    """
    # defines the dispatcher class for this node class, this
    # can be redefined in subclasses
    Dispatcher  = XNodeDispatcher
    BaseName    = 'node'
    
    HotspotStyle = XNodeHotspot.Style # keeping backward compatibility
    
    # pylint: disable-msg=W0613
    
    def __init__( self, scene ):
        # define first or isVisible will fail
        self._layer                     = None
        self._isolatedHidden            = False
        self._visible                   = True
        
        super(XNode, self).__init__()
        
        # set the default parameters
        flags  = self.ItemIsMovable 
        flags |= self.ItemIsSelectable 
        flags |= self.ItemIsFocusable
        
        self.setFlags( flags )
        self.setAcceptHoverEvents(True)
        
        # need this flag for Qt 4.6+
        try:
            self.setFlag(self.ItemSendsGeometryChanges)
        except AttributeError:
            pass
        
        # create custom properties
        self._pressTime                 = datetime.datetime.now()
        self._icon                      = None
        self._iconSize                  = QSize(16, 16)
        self._disableWithLayer          = False
        self._dirty                     = True
        self._xLocked                   = False
        self._xSnapToGrid               = True
        self._yLocked                   = False
        self._ySnapToGrid               = True
        self._ignoreMouseEvents         = False
        self._margins                   = (0, 0, 0, 0)
        self._minimumWidth              = scene.cellWidth() * 4
        self._minimumHeight             = scene.cellHeight()
        self._displayName               = ''
        self._objectId                  = self.generateId()
        self._objectName                = scene.uniqueNodeName(self.BaseName)
        self._customData                = {}
        self._enabled                   = True
        self._penColor                  = QColor('black')
        self._baseColor                 = QColor('white')
        self._borderColor               = QColor(60, 60, 60)
        self._alternateColor            = QColor(220, 220, 220)
        self._disabledPenColor          = QColor(100, 100, 100)
        self._disabledColor             = QColor(180, 180, 180)
        self._disabledAlternateColor    = QColor(150, 150, 150)
        self._highlightColor            = QColor(240, 240, 100)
        self._hotspotColor              = QColor(255, 255, 255)
        self._hoverSpot                 = None
        self._roundingRadius            = 0
        self._highlightPadding          = 6.0
        self._hotspotStyle              = XNode.HotspotStyle.Invisible
        self._hotspotPressed            = False
        self._hotspots                  = []
        self._dropzones                 = []
        self._drawHotspotsUnderneath    = False
        self._titleFont                 = None
        self._wordWrap                  = False
        
        # create the dispatch object
        self.dispatch               = self.Dispatcher()
        self.setLayer( scene.currentLayer() )
    
    def addDropzone( self, dropzone ):
        """
        Adds a new dropzone to the node.
        
        :param      dropzone | <XNodeHotspot>
        """
        self._dropzones.append(dropzone)
    
    def addHotspot( self, hotspot ):
        """
        Adds a new hotspot to the system.
        
        :param      hotspot | <XNodeHotspot>
        """
        self._hotspots.append(hotspot)
    
    def adjustTitleFont( self ):
        """
        Adjusts the font used for the title based on the current with and \
        display name.
        """
        if ( self._titleFont ):
            return
        
        m = self.contentsMargins()
        w = self.rect().width() - (m[0] + m[2] + self.roundingRadius() * 2)
        
        if ( not w ):
            return
        
        font    = QApplication.font()
        text    = self.displayName()
        if not self.wordWrap() or projex.text.wordcount(text) == 1:
            metrics = QFontMetrics(font)
            
            while ( w < metrics.width(text) ):
                new_size = font.pointSize() - 1
                if ( new_size <= 5 ):
                    break
                
                font.setPointSize(new_size)
                metrics = QFontMetrics(font)
        
        self._titleFont = font
    
    def adjustSize( self ):
        """
        Adjusts the size of this node to support the length of its contents.
        """
        cell      = self.scene().cellWidth() * 2
        minheight = cell
        minwidth  = 2 * cell
        
        # fit to the grid size
        metrics = QFontMetrics(QApplication.font())
        width   = metrics.width(self.displayName()) + 20
        width   = ((width/cell) * cell) + (cell % width)
        
        height  = self.rect().height()
        
        # adjust for the icon
        icon = self.icon()
        if icon and not icon.isNull():
            width += self.iconSize().width() + 2
            height = max(height, self.iconSize().height() + 2)
        
        self.setMinimumWidth(max(width, minwidth))
        self.setMinimumHeight(max(height, minheight))
        
        self.rebuild()
    
    def alternateColor( self ):
        """
        Return the alternate color for this node.
        
        :return     <QColor>
        """
        return self._alternateColor
    
    def baseColor( self ):
        """
        Returns the base color for this node.
        
        :return     <QColor>
        """
        return self._baseColor
    
    def borderColor( self ):
        """
        Returns the base color for this node.
        
        :return     <QColor>
        """
        return self._borderColor
    
    def blockSignals( self, state = True ):
        """
        Blocks the dispatcher from sending signals based on the inputed \
        state value.
                    
        :param      state       <bool>
        """
        self.dispatch.blockSignals(state)
    
    def boundingRect( self ):
        """
        Determines the bounding rectangle for this node.
        
        :return     <QRectF>
        """
        rect = super(XNode, self).boundingRect()
        
        pad = self.highlightPadding()
        x = rect.x() - pad / 2.0
        y = rect.y() - pad / 2.0
        w = rect.width() + pad
        h = rect.height() + pad
        
        return QRectF( x, y, w, h )
        
    def brush( self ):
        """
        Return the main brush for this node.
        
        :return     <QBrush>
        """
        # create the background brush
        grad = QLinearGradient()
        rect = self.rect()
        
        grad.setStart(QPointF(0, rect.y()))
        grad.setFinalStop(QPointF(0, rect.bottom()))
        
        grad.setColorAt(0, self.baseColor())
        grad.setColorAt(1, self.alternateColor())
            
        return QBrush(grad)
    
    def centerOn(self, point):
        """
        Centers this node on the inputed point.
        
        :param      point | <QPointF>
        """
        rect = self.rect()
        x = point.x() - rect.width() / 2.0
        y = point.y() - rect.height() / 2.0
        
        self.setPos(x, y)
    
    def clearConnections( self, cls ):
        """
        Clears all the connections for this node.
        
        :param      cls | <subclass of XNodeConnection> || None
        
        :return     <int> | number of connections removed
        """
        count = 0
        for connection in self.connections(cls):
            connection.remove()
            count += 1
        return count
    
    def clearDropzones( self ):
        """
        Clears the dropzones and slots from this node.
        """
        self._dropzones = []
    
    def clearHotspots( self ):
        """
        Clears the hotspots and slots from this node.
        """
        self._hotspots = []
    
    def contentsMargins( self ):
        """
        Returns the margins that will be used when drawing this node.
        
        :return     (<int> left, <int> top, <int> right, <int> bottom)
        """
        return self._margins
    
    def connections( self, cls = None ):
        """
        Returns a list of connections from the scene that match the inputed
        class for this node.
        
        :param      cls | <subclass of XNodeConnection> || None
        
        :return     [<XNodeConnection>, ..]
        """
        scene = self.scene()
        if ( not scene ):
            return []
        
        if ( not cls ):
            cls = XNodeConnection
        
        output = []
        for item in scene.items():
            if ( not isinstance(item, cls) ):
                continue
            
            if ( item.inputNode() == self or item.outputNode() == self ):
                output.append(item)
        
        return output
    
    def connectDropzone( self, 
                         rect, 
                         slot, 
                         color = None,
                         style = None,
                         name  = '',
                         toolTip = '' ):
        """
        Connects the inputed dropzone to the given slot at the defined rect.
        
        :param      rect    | <QRectF>
                    slot    | <method> || <function>
        
        :return     <XNodeHotspot>
        """
        if ( not color ):
            color = self.hotspotColor()
        if ( not style ):
            style = self.hotspotStyle()
        
        hotspot = XNodeHotspot(rect, 
                               slot, 
                               name,
                               toolTip)
        
        hotspot.setColor(color)
        hotspot.setStyle(style)
        self._dropzones.append(hotspot)
        return hotspot
    
    def connectHotspot( self, 
                        rect, 
                        slot, 
                        color = None, 
                        style = None, 
                        name = '',
                        toolTip = '' ):
        """
        Defines a new hotspot rect for the given hotspot type.
        
        :param      rect        | <QRectF>
                    slot        | <method> || <function>
                    color       | <QColor> || None
                    style       | <XNode.HotspotStyle> || None
                    toolTip     | <str>
        
        :return     <XNodeHotspot>
        """
        if ( not color ):
            color = self.hotspotColor()
        if ( not style ):
            style = self.hotspotStyle()
        
        hotspot = XNodeHotspot(rect, 
                               slot, 
                               name,
                               toolTip)
        
        hotspot.setColor(color)
        hotspot.setStyle(style)
        
        self._hotspots.append(hotspot)
        return hotspot
    
    def connectTo( self, node, cls = None ):
        """
        Creates a connection between this node and the inputed node.
        
        :param      node | <XNode>
                    cls  | <subclass of XNodeConnection> || None
        
        :return     <XNodeConnection>
        """
        if ( not node ):
            return
        
        con = self.scene().addConnection(cls)
        con.setOutputNode(self)
        con.setInputNode(node)
        
        return con
    
    def customData( self, key, default = None ):
        """
        Return the custom data that is stored on this node for the \
        given key, returning the default parameter if none was found.
        
        :param      key         <str>
        :param      default     <variant>
        
        :return     <variant>
        """
        return self._customData.get(str(key), default)
    
    def disconnectFrom( self, node, cls = None ):
        """
        Disconnects from the inputed node.  If there is a class provided, then
        only a particular type of connection will be removed
        
        :param      node | <XNode>
                    cls  | <subclass of XNodeConnection> || None
        
        :return     <int> | number of connections removed
        """
        count = 0
        for connection in self.connections(cls):
            if ( connection.inputNode() == node or \
                 connection.outputNode() == node ):
                connection.remove()
        return count
    
    def disabledAlternateColor( self ):
        """
        Returns the alternate color for this node when it is disabled.
        
        :return     <QColor>
        """
        return self._disabledAlternateColor
    
    def disabledBrush( self ):
        """
        Return the main brush for this node.
        
        :return     <QBrush>
        """
        # create the background brush
        grad = QLinearGradient()
        rect = self.rect()
        
        grad.setStart(QPointF(0, rect.y()))
        grad.setFinalStop(QPointF(0, rect.bottom()))
        
        grad.setColorAt(0, self.disabledColor())
        grad.setColorAt(1, self.disabledAlternateColor())
            
        return QBrush(grad)
    
    def disabledColor( self ):
        """
        Returns the color this node should render when its disabled.
        
        :return     <QColor>
        """
        return self._disabledColor
    
    def disabledPenColor( self ):
        """
        Returns the disabled pen color for this node.
        
        :return     <QColor>
        """
        return self._disabledPenColor
    
    def disableWithLayer( self ):
        """
        Returns whether or not this node should toggle its enabled state with \
        the layer current value changing.
        
        :return     <bool>
        """
        return self._disableWithLayer
    
    def displayName( self ):
        """
        Return the user friendly name for this node.  if the display name \
        is not implicitly set, then the words for the object name \
        will be used.
        
        :return     <str>
        """
        if ( not self._displayName ):
            return projex.text.pretty(self.objectName())
        return self._displayName
    
    def draw( self, painter, option, rect ):
        """
        Draws the node for the graphics scene.  this method can and should \
        be overloaded to create custom nodes.
        
        :param      painter     <QPainter>
        :param      option      <QGraphicsItemSytleOption>
        :param      rect        <QRectF>
        """
        painter.save()
        
        # draw the node
        rect    = self.rect()
        
        left, top, right, bottom = self.contentsMargins()
        
        x = rect.x() + left
        y = rect.y() + top
        w = rect.width() - (left + right)
        h = rect.height() - (top + bottom)
        r = self.roundingRadius()
        
        painter.setRenderHint(painter.Antialiasing)
        painter.setRenderHint(painter.TextAntialiasing)
        
        # draw the border
        painter.save()
        pen = QPen(self.borderColor())
        pen.setWidthF(0.8)
        painter.setRenderHint(painter.Antialiasing)
        painter.setPen(pen)
        painter.drawRoundedRect(x, y, w, h, r, r)
        painter.restore()
        
        # draw the icon
        icon = self.icon()
        if icon and not icon.isNull():
            pixmap = icon.pixmap(self.iconSize())
            offset = (h - self.iconSize().height()) / 2
            painter.drawPixmap(x + 4, offset, pixmap)
            x += self.iconSize().width() + 4
            w -= self.iconSize().width() + 4
        
        # draw the font
        x += 6
        w -= 12
        metrics = QFontMetrics(self.titleFont())
        if not self.wordWrap():
            e_text  = metrics.elidedText(unicode(self.displayName()), 
                                         Qt.ElideRight,
                                         w)
        else:
            e_text = self.displayName()
        
        # draw the text
        painter.setFont(self.titleFont())
        painter.drawText( x, 
                          y, 
                          w, 
                          h, 
                          Qt.AlignCenter | Qt.TextWordWrap, 
                          e_text )
        
        painter.restore()

    def drawHotspots( self, painter ):
        """
        Draws all the hotspots for the renderer.
        
        :param      painter | <QPaint>
        """
        # draw hotspots
        for hotspot in (self._hotspots + self._dropzones):
            hstyle = hotspot.style()
            if ( hstyle == XNode.HotspotStyle.Invisible ):
                continue
            
            hotspot.render(painter)
    
    def drawHotspotsUnderneath( self ):
        """
        Returns whether or not the hotspots should be drawn above or below the
        node itself.
        
        :return     <bool>
        """
        return self._drawHotspotsUnderneath
    
    def drawHighlight( self, painter, option, rect ):
        """
        Draws the highlight around this node.
        
        :param      painter | <QPainter>
                    option  | <QGraphicsItemSytleOption>
                    rect    | <QRectF>
        """
        
        pad = self.highlightPadding()
        left, top, right, bottom = self.contentsMargins()
        
        x = (-pad / 2.0) + left
        y = (-pad / 2.0) + top
        w = (self.rect().width() + pad + 1) - (left + right) - 1
        h = (self.rect().height() + pad + 1) - (top + bottom) - 1
        rradius = self.roundingRadius()
        
        # draw the highlight
        painter.setRenderHint(painter.Antialiasing)
        painter.setPen( Qt.NoPen )
        painter.setBrush( self.highlightBrush() )
        painter.drawRoundedRect( x, y, w, h, rradius, rradius )
        painter.setRenderHint(painter.Antialiasing, False)
    
    def dropzoneAt( self, point ):
        """
        Returns the dropzone at the inputed point.
        
        :param      point | <QPoint>
        """
        for dropzone in self._dropzones:
            rect = dropzone.rect()
            if ( rect.contains(point) ):
                return dropzone
        return None
    
    def emitGeometryChanged( self, point = None ):
        """
        Emits the geometryChanged signal, provided the dispatcher's \
        signals are not currently blocked.  If the point value is not \
        provided, the object's current position will be used.
        
        :param      point      | <QPointF> || None
        
        :return     <bool> emitted
        """
        # check the signals blocked
        if ( self.signalsBlocked() ):
            return False
        
        # grab the point
        if ( point == None ):
            point = self.pos()
        
        # emit the signal
        self.dispatch.geometryChanged.emit(point)
        return True
    
    def emitRemoved( self ):
        """
        Emits the removed signal, provided the dispatcher's signals \
        are not currently blocked.
        
        :return     <bool> emitted
        """
        # check the signals blocked
        if ( self.signalsBlocked() ):
            return False
        
        # emit the signal
        self.dispatch.removed.emit()
        return True
    
    def findDropzone( self, name ):
        """
        Finds the dropzone based on the inputed name.
        
        :param      name | <str>
        
        :return     <XNodeHotspot> || None
        """
        for dropzone in self._dropzones:
            if ( dropzone.name() == name ):
                return dropzone
        return None
    
    def findHotspot( self, name ):
        """
        Finds the hotspot based on the inputed name.
        
        :param      name | <str>
        
        :return     <XNodeHotspot> || None
        """
        for hotspot in self._hotspots:
            if ( hotspot.name() == name ):
                return hotspot
        return None
    
    def forceRemove( self ):
        """
        Removes the object from the scene by queuing it up for removal.
        """
        scene = self.scene()
        if ( scene ):
            scene.forceRemove(self)
    
    def generateId( self ):
        """
        Generates a random unique id for this node instance.
        
        :return     <int> || <uuid>
        """
        # try to use the uuid module
        try:
            import uuid
            return uuid.uuid1()
        
        # otherwise, use the random module
        except ImportError:
            import random
            return random.randint(-1000000000000, 1000000000000)
    
    def hasCustomData( self, key ):
        """
        Returns whether or not there is the given key in the custom data.
        
        :param      key | <str>
        
        :return     <bool>
        """
        return str(key) in self._customData
    
    def highlightBrush( self ):
        """
        Returns the brush to use when highlighting a node.
        
        :return     <QBrush>
        """
        return QBrush(self.highlightColor())
        
    def highlightPadding( self ):
        """
        Returns the padding amount that will be used when drawing this nodes \
        highlighting.
        
        :return     <int>
        """
        return self._highlightPadding
    
    def highlightColor( self ):
        """
        Returns the color to use when highlighting this node.
        
        :return     <QColor>
        """
        return self._highlightColor
    
    def hotspotAt( self, point ):
        """
        Returns the hotspot at the inputed point.
        
        :param      point | <QPoint>
        
        :return     <XNodeHotspot> || None
        """
        for hotspot in self._hotspots:
            rect = hotspot.rect()
            if ( rect.contains(point) ):
                return hotspot
        return None
    
    def hotspotColor( self ):
        """
        Returns the color used for the hotspot when it is not an invisible \
        render.
        
        :return     <QColor>
        """
        return self._hotspotColor
    
    def hotspotStyle( self ):
        """
        Returns the style to be used for the hotspots in this node.
        
        :return     <XNode.HotspotStyle>
        """
        return self._hotspotStyle
    
    def hoverEnterEvent( self, event ):
        """
        Prompts the tool tip for this node based on the inputed event.
        
        :param      event | <QHoverEvent>
        """
        # process the parent event
        super(XNode, self).hoverEnterEvent(event)
        
        # hover over a hotspot
        hotspot = self.hotspotAt(event.pos())
        if not hotspot:
            hotspot = self.dropzoneAt(event.pos())
        
        old_spot = self._hoverSpot
        
        if hotspot and hotspot != old_spot:
            # update the new hotspot
            self._hoverSpot = hotspot
            
            if old_spot:
                old_spot.hoverLeaveEvent(event)
            
            if hotspot.hoverEnterEvent(event):
                self.update()
        
        elif old_spot and not hotspot:
            self._hoverSpot = None
            
            if old_spot.hoverLeaveEvent(event):
                self.update()
    
    def hoverMoveEvent(self, event):
        """
        Prompts the tool tip for this node based on the inputed event.
        
        :param      event | <QHoverEvent>
        """
        # process the parent event
        super(XNode, self).hoverMoveEvent(event)
        
        # hover over a hotspot
        hotspot = self.hotspotAt(event.pos())
        if not hotspot:
            hotspot = self.dropzoneAt(event.pos())
        
        old_spot = self._hoverSpot
        
        if hotspot and hotspot != old_spot:
            # update the new hotspot
            self._hoverSpot = hotspot
            
            if old_spot:
                old_spot.hoverLeaveEvent(event)
            
            if hotspot.hoverEnterEvent(event):
                self.update()
        
        elif old_spot and not hotspot:
            self._hoverSpot = None
            
            if old_spot.hoverLeaveEvent(event):
                self.update()
    
    def hoverLeaveEvent(self, event):
        """
        Processes the hovering information for this node.
        
        :param      event | <QHoverEvent>
        """
        if self._hoverSpot:
            if self._hoverSpot.hoverLeaveEvent(event):
                self.update()
        
        self._hoverSpot = None
        
        super(XNode, self).hoverLeaveEvent(event)
    
    def icon(self):
        """
        Returns the icon for this instance.
        
        :return     <QIcon> || None
        """
        return self._icon
    
    def iconSize(self):
        """
        Returns the icon size for this node.
        
        :return     <QSize>
        """
        return self._iconSize
    
    def inputConnections(self, cls=None):
        """
        Returns a list of input connections from the scene that match the 
        inputed class for this node.
        
        :param      cls | <subclass of XNodeConnection> || None
        
        :return     [<XNodeConnection>, ..]
        """
        scene = self.scene()
        if ( not scene ):
            return []
        
        if ( not cls ):
            cls = XNodeConnection
        
        output = []
        for item in scene.items():
            if ( not isinstance(item, cls) ):
                continue
            
            if ( item.inputNode() == self ):
                output.append(item)
        
        return output
    
    def isDirty( self ):
        """
        Returns whether or not the node needs to be rebuilt.
        
        :return     <bool>
        """
        return self._dirty
    
    def isEnabled( self ):
        """
        Returns whether or not this node is enabled.
        """
        if ( self._disableWithLayer and self._layer ):
            lenabled = self._layer.isEnabled()
        else:
            lenabled = True
            
        return self._enabled and lenabled
    
    def isIsolateHidden( self ):
        """
        Returns whether or not this node is hidden due to isolation.
        
        :return     <bool>
        """
        return self._isolatedHidden
    
    def isLocked( self ):
        """
        Returns if both the x and y directions are locked, or if the scene \
        is in view mode.
        
        :return     <bool>
        """
        # return if the layer is not the current layer
        if ( self._layer and not self._layer.isCurrent() ):
            return True
        
        # return whether or not the node is enabld or locked
        return not self._enabled or (self._xLocked and self._yLocked)
    
    def isSnappedToGrid( self ):
        """
        Returns if both the x and y directions are snapping to the grid.
        
        :return     <bool>
        """
        return (self._xSnapToGrid and self._ySnapToGrid)
    
    def isYLocked( self ):
        """
        Returns whether or not the y direction is locked.
        
        :return     <bool>
        """
        return self._yLocked
    
    def isYSnappedToGrid( self ):
        """
        Returns whehter or not the y direction is snapping to the grid.
        
        :return     <bool>
        """
        return self._ySnapToGrid
    
    def isXLocked( self ):
        """
        Returns whether or not the x direction is locked.
        
        :return     <bool>
        """
        return self._xLocked
    
    def isXSnappedToGrid( self ):
        """
        Returns whether or not the x direction is snapping to the grid.
        
        :return     <bool>
        """
        return self._xSnapToGrid
    
    def isVisible( self ):
        """
        Returns whether or not this item is visible.
        
        :return     <bool>
        """
        layer = self.layer()
        if ( layer and not layer.isVisible() ):
            return False
#        
#        if ( self.isIsolateHidden() ):
#            return False
#        
        return self._visible
    
    def itemChange( self, change, value ):
        """
        Overloads the base QGraphicsItem itemChange method to \
        handle snapping and locking of an object as the user \
        moves it around in the scene.
        
        :param      change      <int>
        :param      value       <variant>
        
        :return     <variant>
        """
        # only operate when it is a visible, geometric change
        if ( not (self.isVisible() and change == self.ItemPositionChange) ):
            return super(XNode, self).itemChange( change, value )
            
        scene = self.scene()
        # only operate when we have a scene
        if ( not scene ):
            return super(XNode, self).itemChange( change, value )
            
        point = unwrapVariant(value)
        
        # update the x position
        if ( self.isXLocked() ):
            point.setX( self.pos().x() )
        elif ( self.isXSnappedToGrid() ):
            offset_x = self.rect().width() / 2.0
            center_x = point.x() + offset_x
            center_x -= center_x % scene.cellWidth()
            
            point.setX(center_x - offset_x)
            
        # update the y position
        if ( self.isYLocked() ):
            point.setY( self.pos().y() )
        elif ( self.isYSnappedToGrid() ):
            offset_y = self.rect().height() / 2.0
            center_y = point.y() + offset_y
            center_y -= center_y % scene.cellHeight()
            
            point.setY(center_y - offset_y)
            
        # create the return value
        new_value = wrapVariant(point)
        
        # call the base method to operate on the new point
        result = super(XNode, self).itemChange(change, new_value)
        
        # emit the geometry changed signal
        self.emitGeometryChanged(point)
        
        # return the result
        return result
    
    def layer( self ):
        """
        Returns the layer that this node is assigned to.
        
        :return     <XNodeLayer> || None
        """
        return self._layer
    
    def minimumHeight( self ):
        """
        Returns the minimum height for this node.
        
        :return     <float>
        """
        return self._minimumHeight
    
    def minimumWidth( self ):
        """
        Returns the minimum width for this node.
        
        :return     <float>
        """
        return self._minimumWidth
    
    def mouseDoubleClickEvent(self, event):
        """
        Ignores the mouse click events - propogated via the XNodeScene
        nodeDoubleClicked signal.
        
        :param      event | <QMouseEvent>
        """
        event.ignore()
    
    def mousePressEvent( self, event ):
        """
        Overloads the mouse press event to handle special cases and \
        bypass when the scene is in view mode.
        
        :param      event   <QMousePressEvent>
        """
        event.setAccepted(False)
        self._hotspotPressed = False
        # ignore events when the scene is in view mode
        scene = self.scene()
        if ( self.isLocked() or (scene and scene.inViewMode()) ):
            event.ignore()
            self._ignoreMouseEvents = True
            return
        
        self._ignoreMouseEvents = False
        
        # block the selection signals
        if ( scene ):
            scene.blockSelectionSignals(True)
            
            # clear the selection
            if ( not (self.isSelected() or 
                      event.modifiers() == Qt.ControlModifier) ):
                for item in scene.selectedItems():
                    if ( item != self ):
                        item.setSelected(False)
        
        # determine if we need to start any connections
        hotspot = self.hotspotAt(event.pos())
        if ( hotspot ):
            hotspot.slot()(event)
        
            # check if the event is accepted
            if ( event.isAccepted() ):
                self._hotspotPressed = True
                return
        
        # try to start the connection
        event.accept()
        self._pressTime = datetime.datetime.now()
        super(XNode, self).mousePressEvent(event)
        
    def mouseMoveEvent( self, event ):
        """
        Overloads the mouse move event to ignore the event when \
        the scene is in view mode.
        
        :param      event   <QMouseMoveEvent>
        """
        event.setAccepted(False)
        if self._hotspotPressed:
            event.accept()
            return
        
        # ignore events when the scene is in view mode
        scene = self.scene()
        if ( self.isLocked() or self._ignoreMouseEvents or \
             (scene and (scene.inViewMode() or scene.isConnecting()))):
            event.ignore()
            self._ignoreMouseEvents = True
            return
        
        # call the base method
        event.accept()
        super(XNode, self).mouseMoveEvent(event)
    
    def mouseReleaseEvent( self, event ):
        """
        Overloads the mouse release event to ignore the event when the \
        scene is in view mode, and release the selection block signal.
         
         :param     event   <QMouseReleaseEvent>
        """
        event.setAccepted(False)
        if self._hotspotPressed:
            event.accept()
            self._hotspotPressed = False
            return
        
        # ignore events when the scene is in view mode
        scene = self.scene()
        if ( self.isLocked() or self._ignoreMouseEvents or \
             (scene and (scene.inViewMode() or scene.isConnecting()))):
            event.ignore()
            self._ignoreMouseEvents = False
            return
        
        super(XNode, self).mouseReleaseEvent(event)
        
        # emit the geometry changed signal
        self.emitGeometryChanged()
        
        # unblock the selection signals
        if ( scene ):
            scene.blockSelectionSignals(False)
            
            delta = datetime.datetime.now() - self._pressTime
            if not scene.signalsBlocked() and delta.seconds < 1:
                scene.nodeClicked.emit(self)
    
    def objectName( self ):
        """
        Returns the unique object name for this node.
        
        :return     <str>
        """
        return self._objectName
    
    def objectId( self ):
        """
        Returns the unique object identifier that was assinged on creation.
        
        :return     <int>
        """
        return self._objectId
    
    def opacity( self ):
        """
        Returns the 0-1 percentage opacity value for this node.
        
        :return     <float>
        """
        if ( self.isIsolateHidden() ):
            return 0.1
        
        opacity = super(XNode, self).opacity()
        layer = self.layer()
        if ( layer ):
            return layer.opacity() * opacity
        
        return opacity
    
    def outputConnections(self, cls=None):
        """
        Returns a list of output connections from the scene that match the 
        inputed class for this node.
        
        :param      cls | <subclass of XNodeConnection> || None
        
        :return     [<XNodeConnection>, ..]
        """
        scene = self.scene()
        if ( not scene ):
            return []
        
        if ( not cls ):
            cls = XNodeConnection
        
        output = []
        for item in scene.items():
            if ( not isinstance(item, cls) ):
                continue
            
            if ( item.outputNode() == self ):
                output.append(item)
        
        return output
    
    def paint( self, painter, option, widget ):
        """
        Overloads the default QGraphicsItem paint event to update the \
        node when necessary and call the draw method for the node.
        
        :param      painter     <QPainter>
        :param      option      <QStyleOptionGraphicsItem>
        :param      widget      <QWidget>
        """
        painter.save()
        painter.setOpacity( self.opacity() )
        
        # rebuild when dirty
        if self.isDirty():
            self.rebuild()
            self.adjustTitleFont()
        
        # draw the highlight
        if self.isSelected():
            self.drawHighlight(painter, option, widget)
        
        if self.drawHotspotsUnderneath():
            self.drawHotspots(painter)
        
        if self.isEnabled():
            painter.setPen(self.penColor())
            painter.setBrush(self.brush())
        else:
            painter.setPen(self.disabledPenColor())
            painter.setBrush(self.disabledBrush())
        
        # draw the item
        self.draw(painter, option, widget)
        
        if not self.drawHotspotsUnderneath():
            self.drawHotspots(painter)
        
        painter.restore()
    
    def penColor( self ):
        """
        Return the pen for this node.
        
        :return     <QColor>
        """
        return self._penColor
    
    def positionAt( self, location, fixedX = None, fixedY = None ):
        """
        Calculates the position at the inputed location.
        
        :param      location        <XConnectionLocation>
        :param      fixedX          <float> || None
        :param      fixedY          <float> || None
            
        :return     <QPointF>
        """
        # figure the position information
        rect    = self.sceneRect()
        
        if ( rect.height() < self.minimumHeight() ):
            rect.setHeight(self.minimumHeight())
        
        if ( rect.width() < self.minimumWidth() ):
            rect.setWidth(self.minimumWidth())
        
        cx      = rect.center().x()
        cy      = rect.center().y()
        x       = cx
        y       = cy
            
        if ( location == XConnectionLocation.Left ):
            x = rect.left()
        
        # define a right-based x
        elif ( location & XConnectionLocation.Right ):
            x = rect.right()
        
        # define a top-based y
        elif ( location & XConnectionLocation.Top ):
            y = rect.top()
        
        # define a bottom-based y
        elif ( location & XConnectionLocation.Bottom ):
            y = rect.bottom()
        
        # use the fixed locations if provided
        if ( fixedX != None ):
            x = rect.x() + fixedX
        if ( fixedY != None ):
            y = rect.y() + fixedY
        
        return QPointF(x, y)
    
    def prepareToRemove( self ):
        """
        Handles any preparation logic that needs to happen before \
        this node is removed.
        
        :return     <bool> success
        """
        self.emitRemoved()
        return True
    
    def rebuild( self, scene = None ):
        """
        This method is where you will rebuild the geometry and \
        data for a node.
        
        :param      scene       <QGraphicsScene> || None
        
        :return     <bool> success
        """
        rect = QRectF( 0, 0, self.minimumWidth(), self.minimumHeight() )
        self.setRect( rect )
        return True
    
    def roundingRadius( self ):
        """
        Returns the desired rounding radius for the node when drawing.
                    
        :param      <int>
        """
        return self._roundingRadius
    
    def scenePos( self ):
        """
        Returns the scene position for this node by resolving any \
        inhertiance position data since QGraphicsItem's return \
        relative-space positions.
        
        :return     <QPointF>
        """
        pos     = self.pos()
        pitem   = self.parentItem()
        
        while (pitem):
            pos     = pitem.pos() + pos
            pitem   = pitem.parentItem()
        
        return pos
    
    def sceneRect( self ):
        """
        Returns the scene geometry for this node by resolving any \
        inheritance position data since QGraphicsItem's return \
        relative-space positions.
        
        :return     <QRectF>
        """
        pos     = self.scenePos()
        rect    = self.rect()
        return QRectF(pos.x(), pos.y(), rect.width(), rect.height())
    
    def setAlternateColor( self, color ):
        """
        Sets the alternate color for this node.
        
        :param      color       <QColor>
        """
        self._alternateColor = QColor(color)
        self.setDirty()
    
    def setBaseColor( self, color ):
        """
        Sets the primary color for this node.
        
        :param      color       <QColor>
        """
        self._baseColor = QColor(color)
        self.setAlternateColor( self._baseColor.darker(125) )
        self.setBorderColor( self._baseColor.darker(180) )
        self.setDirty()
        self.update()
    
    def setBorderColor( self, color ):
        """
        Sets the border color for this node to the inputed color.
        
        :param      color | <QColor>
        """
        self._borderColor = QColor(color)
        self.setDirty()
    
    def setContentsMargins( self, left, top, right, bottom ):
        """
        Sets the contents margins for this node to the inputed values.
        
        :param      left    | <int>
                    top     | <int>
                    right   | <int>
                    bottom  | <int>
        """
        self._margins   = (left, top, right, bottom)
        self._titleFont = None
    
    def setCustomData( self, key, value ):
        """
        Sets the custom data on this node for the given \
        key to the inputed value.
        
        :param      key     <str>
        :param      value   <variant>
        """
        self._customData[str(key)] = value
    
    def setDisabledAlternateColor( self, color ):
        """
        Sets the alternate color used when drawing this node as disabled.
        
        :param      color | <QColor>
        """
        self._disabledAlternateColor = QColor(color)
        self.setDirty()
    
    def setDisabledColor( self, color ):
        """
        Sets the disabled color used when drawing this node as disabled.
        
        :param      color | <QColor>
        """
        self._disabledColor = QColor(color)
        self.setDisabledAlternateColor( self._disabledColor.darker(125) )
        self.setDirty()
    
    def setDisabledPenColor( self, color ):
        """
        Sets the pen color to be used when drawing this node as disabled.
        
        :param      color | <QColor>
        """
        self._disabledPenColor = QColor(color)
    
    def setDisableWithLayer( self, state ):
        """
        Sets whether or not this node's enabled state should be affected by \
        whether or not its layer is set to current.
        
        :param      state | <bool>
        """
        self._disableWithLayer = state
        self.setDirty()
    
    def setDisplayName( self, name ):
        """
        Sets the display name for this node.
        
        :param      name    <str>
        """
        self._displayName = name
        self._titleFont = None
    
    def setDirty( self, state = True ):
        """
        Flags this node as needing a rebuild based on the given state.
        
        :param      state   <bool>
        """
        self._dirty = state
    
    def setDrawHotspotsUnderneath( self, state ):
        """
        Sets whether or not the hotspots should be drawn underneath this node.
        
        :param      state | <bool>
        """
        self._drawHotspotsUnderneath = state
        
    def setHighlightColor( self, color ):
        """
        Sets the color to be used when highlighting a node.
        
        :param      color       <QColor>
        """
        self._highlightColor = color
        self.setDirty()
    
    def setHighlightPadding( self, padding ):
        """
        Sets the amount of padding that will be used when rendering the \
        highlight border around the node.
        
        :param      padding | <float>
        """
        self._highlightPadding = float(padding)
    
    def setHotspotColor( self, color ):
        """
        Sets the hotspot color for this node to the inputed color.
        
        :param      color | <QColor>
        """
        self._hotspotColor = color
    
    def setHotspotStyle( self, hstyle ):
        """
        Sets the hotspot style for rendering hotspots for this node to the \
        intpued style.
        
        :param      hstyle | <XNode.HotspotStyle>
        """
        self._hotspotStyle = hstyle
    
    def setIcon(self, icon):
        """
        Sets the icon for this item to the inputed icon.
        
        :param      icon | <str> || <QIcon> || None
        """
        if icon:
            self._icon = QIcon(icon)
        else:
            self._icon = None
    
    def setIconSize(self, iconSize):
        """
        Sets the size for this icon to the inputed size.
        
        :param      iconSize | <QSize>
        """
        self._iconSize = iconSize
    
    def setIsolateHidden( self, state ):
        """
        Sets whether or not this item is hidden due to isolation.
        
        :param      state | <bool>
        """
        self._isolatedHidden = state
        
        super(XNode, self).setVisible(self.isVisible())
    
    def setLayer( self, layer ):
        """
        Sets the layer that this node is associated with to the given layer.
        
        :param      layer       | <XNodeLayer> || None
        
        :return     <bool> changed
        """
        if ( layer == self._layer ):
            return False
        
        self._layer = layer
        self.syncLayerData()
            
        return True
    
    def setLocked( self, state = True ):
        """
        Locks the node in both the x and y directions.
        
        :param      state   <bool>
        """
        self._xLocked = state
        self._yLocked = state
    
    def setMinimumHeight( self, value ):
        """
        Sets the minimum height for this node.
        
        :param      value   <int>
        """
        self._minimumHeight = value
    
    def setMinimumWidth( self, value ):
        """
        Sets the minimum width for this node.
        
        :param      value   <int>
        """
        self._minimumWidth = value
    
    def setObjectName( self, name ):
        """
        Sets the unique object name for this node by grabbing the next \
        available unique name from the scene based on the inputed string.  \
        The resulting name will be returned.
        
        :warning    this method will create a unique name based
                    on the inputed name - there is no guarantee
                    that the name inputed will be the name set,
                    so use the returned value to ensure you have
                    the right name
        
        :param      name        <str>
        
        :return     <str>
        """
        scene = self.scene()
        if ( scene ):
            name = scene.uniqueNodeName(name)
        self._objectName = name
        self._titleFont = None
        self.update()
        
    def setPenColor( self, color ):
        """
        Sets the pen for this node.
        
        :param      color     <QColor>
        """
        self._penColor = QColor(color)
        self.setDirty()
    
    def setRect( self, rect ):
        """
        Sets the rect for this node, ensuring that the width and height \
        meet the minimum requirements.
        
        :param      rect        <QRectF>
        """
        mwidth  = self.minimumWidth()
        mheight = self.minimumHeight()
        
        if ( rect.width() < mwidth ):
            rect.setWidth(mwidth)
        if ( rect.height() < mheight ):
            rect.setHeight(mheight)
        
        return super(XNode, self).setRect(rect)
    
    def setRoundingRadius( self, radius ):
        """
        Sets the desired rounding radius for this node.
        `
        :param      radius   <int>
        """
        self._roundingRadius = radius
        self.setDirty()
    
    def setSnapToGrid( self, state = True ):
        """
        Sets the snap to grid property for both the x and y directions \
        based on the inputed value.
        
        :param      state   <bool>
        """
        self._xSnapToGrid = state
        self._ySnapToGrid = state
    
    def setVisible( self, state ):
        """
        Sets whether or not this node is visible in the scene.
        
        :param      state | <bool>
        """
        self._visible = state
        
        super(XNode, self).setVisible(self.isVisible())
        
        self.dispatch.visibilityChanged.emit(state)
        self.setDirty()
    
    def setWordWrap(self, state = True):
        """
        Sets whether or not this node will wrap its text.
        
        :param      state | <bool>
        """
        self._titleFont = None
        self._wordWrap = state
    
    def setXLocked( self, state = True ):
        """
        Locks the node in the x direction.
        
        :param      state   <bool>
        """
        self._xLocked = state
    
    def setXSnapToGrid( self, state = True ):
        """
        Marks whether or not the node will snap to the scene \
        grid in the x direction.
        
        :param      state   <bool>
        """
        self._xSnapToGrid = state
    
    def setYLocked( self, state = True ):
        """
        Locks the node in the y direction.
        
        :param      state   <bool>
        """
        self._yLocked = state
    
    def setYSnapToGrid( self, state = True ):
        """
        Marks whether or not the node will snap to the scene grid \
        in the y direction.
                    
        :param      state   <bool>
        """
        self._ySnapToGrid = state
    
    def signalsBlocked( self ):
        """
        Returns whether or not this item's dispatch object has its \
        signals blocked.
        
        :return     <bool>
        """
        return self.dispatch.signalsBlocked()
    
    def syncLayerData( self, layerData = None ):
        """
        Syncs the layer information for this item from the given layer data.
        
        :param      layerData | <dict> || None
        """
        if ( not self._layer ):
            return
            
        if ( not layerData ):
            layerData = self._layer.layerData()
        
        self.setVisible( layerData.get('visible', True) )
        
        if ( layerData.get('current') ):
            # set the default parameters
            flags  = self.ItemIsMovable 
            flags |= self.ItemIsSelectable 
            flags |= self.ItemIsFocusable
            
            # need this flag for Qt 4.6+
            try:
                flags |= self.ItemSendsGeometryChanges
            except AttributeError:
                pass
            
            self.setFlags( flags )
            self.setAcceptHoverEvents(True)
            self.setZValue(100)
            
        else:
            # set the default parameters
            self.setFlags( self.ItemIsFocusable )
            self.setAcceptHoverEvents(True)
            self.setZValue(layerData.get('zValue', 0))
    
    def titleFont( self ):
        """
        Returns the font that is being used for this node's title.
        
        :return     <QFont>
        """
        return self._titleFont
    
    def triggerDropzoneAt( self, point, connection ):
        """
        Triggers the connected dropzone slot at the inputed point.
        
        :param      point       | <QPointF>
                    connection  | <Connection>
        """
        dropzone = self.dropzoneAt(point)
        if ( dropzone ):
            dropzone.slot()(connection)
    
    def wordWrap(self):
        """
        Returns whether or not this node will wrap its words.
        
        :return     <bool>
        """
        return self._wordWrap