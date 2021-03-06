""" The mako """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2012, Projex Software'
__license__         = 'LGPL'

# maintenance information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

__depends__         = ['mako']

import logging
import os
import projex

projex.requires('mako')

logger = logging.getLogger(__name__)

try:
    import mako
    import mako.template
    import mako.lookup

except ImportError:
    logger.warning('The projex.makotext package requires mako to be installed.')
    mako = None

# import useful modules for the template
from datetime import datetime, date
import projex.text

_macros = {}

def register(macro):
    """
    Registers a macro method for the mako text rendering system.
    
    :param      macro | <method>
    """
    _macros[macro.__name__] = macro

def renderfile(filename,
               options=None,
               templatePaths=None,
               default='',
               silent=False):
    """
    Renders a file to text using the mako templating system.
    
    To learn more about mako and its usage, see [[www.makotemplates.org]]
    
    :return     <str> formatted text
    """
    if not mako:
        logger.debug('mako is not installed')
        return default
    
    if not mako:
        logger.debug('mako is not installed.')
        return default
    
    # use the default mako templates
    basepath = os.environ.get('MAKO_TEMPLATEPATH', '')
    if basepath and templatePaths:
        templatePaths += basepath.split(os.path.pathsep)
    elif basepath:
        templatePaths = basepath.split('os.path.pathsep')
    
    # update the default options
    scope = dict(os.environ)
    
    scope['projex_text'] = projex.text
    scope['date']        = date
    scope['datetime']    = datetime
    scope.update(_macros)
    
    scope.update(os.environ)
    
    if options is not None:
        scope.update(options)
    
    logger.debug('rendering mako file: %s', filename)
    if templatePaths:
        lookup = mako.lookup.TemplateLookup(directories = templatePaths)
        templ = mako.template.Template(filename = filename, lookup = lookup)
    else:
        templ = mako.template.Template(filename = filename)
    
    try:
        output = templ.render(**scope)
    except:
        output = default
        if not silent:
            logger.exception('Error rendering mako text')
    
    return output

def render(text,
           options=None,
           templatePaths=None,
           default=None,
           silent=False):
    """
    Renders a template text to a resolved text value using the mako templating
    system.
    
    Provides a much more robust templating option to the projex.text system.  
    While the projex.text method can handle many simple cases with no
    dependencies, the makotext module makes use of the powerful mako templating
    language.  This module provides a simple wrapper to the mako code.
    
    To learn more about mako and its usage, see [[www.makotemplates.org]]
    
    :param      text        <str>
    :param      options     <dict> { <str> key: <variant> value, .. }
    
    :return     <str> formatted text
    
    :usage      |import projex.makotext
                |options = { 'key': 10, 'name': 'eric' }
                |template = '${name.lower()}_${key}_${date.today()}.txt'
                |projex.makotext.render( template, options )
    """
    if not mako:
        logger.debug('mako is not installed.')
        return text if default is None else default
    
    # use the default mako templates
    basepath = os.environ.get('MAKO_TEMPLATEPATH', '')
    if basepath and templatePaths:
        templatePaths += basepath.split(os.path.pathsep)
    elif basepath:
        templatePaths = basepath.split('os.path.pathsep')
    
    # update the default options
    scope = dict(os.environ)
    
    scope['projex_text'] = projex.text
    scope['date']        = date
    scope['datetime']    = datetime
    scope.update(_macros)
    
    if options is not None:
        scope.update(options)
    
    if templatePaths:
        lookup = mako.lookup.TemplateLookup(directories = templatePaths)
        try:
            templ = mako.template.Template(text, lookup = lookup)
        except:
            output = text if default is None else default
            if not silent:
                logger.exception('Error compiling mako text')
    else:
        try:
            templ = mako.template.Template(text)
        except:
            output = text if default is None else default
            if not silent:
                logger.exception('Error compiling mako text')
    
    try:
        output = templ.render(**scope)
    except:
        output = text if default is None else default
        if not silent:
            logger.exception('Error rendering mako text')
    
    return output

def unregister(method):
    """
    Unregisters the given macro from the system.
    
    :param      name | <str>
    """
    _macros.pop(method.__name__, None)

#----------------------------------------------------------------------
# register some macros
#----------------------------------------------------------------------

def collectfiles(path, filt=None):
    """
    Collects some files based on the given filename.
    
    :param      path | <str>
                filt | <method>
        
    :return     [(<str> name, <str> filepath), ..]
    """
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    
    output = []
    for name in sorted(os.listdir(path)):
        filepath = os.path.join(path, name)
        if os.path.isfile(filepath):
            if not filt or filt(name):
                output.append((name, filepath))
    return output

register(collectfiles)