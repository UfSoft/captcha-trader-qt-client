
import logging
from PySide import QtCore

def MaintainStateAndGeometry(klass):
    original_setVisible = klass.setVisible
    classname = klass.__name__

    def save_state_for(self, obj=None):
        settings = QtCore.QSettings()
        settings.beginGroup(classname)
        if obj:
            settings.beginGroup(obj.objectName())
            setting = '%s/%s' % (classname, obj.objectName())
        else:
            obj = self
            setting = classname

        if obj and hasattr(obj, 'saveState'):
            logging.getLogger(__name__).trace("Saving state for %s", setting)
            settings.setValue('state', obj.saveState())

    klass.save_state_for = save_state_for

    def restore_state_for(self, obj=None):
        settings = QtCore.QSettings()
        settings.beginGroup(classname)
        if obj:
            settings.beginGroup(obj.objectName())
            setting = '%s/%s' % (classname, obj.objectName())
        else:
            obj = self
            setting = classname

        if obj and hasattr(obj, 'restoreState') and settings.value('state'):
            logging.getLogger(__name__).trace("Restoring state for %s", setting)
            obj.restoreState(settings.value('state'))

    klass.restore_state_for = restore_state_for

    def save_geometry_for(self, obj=None):
        settings = QtCore.QSettings()
        settings.beginGroup(classname)
        if obj:
            settings.beginGroup(obj.objectName())
            setting = '%s/%s' % (classname, obj.objectName())
        else:
            obj = self
            setting = classname

        if obj and hasattr(obj, 'saveGeometry'):
            logging.getLogger(__name__).trace("Saving geometry for %s", setting)
            settings.setValue('geometry', obj.saveGeometry())

    klass.save_geometry_for = save_geometry_for

    def restore_geometry_for(self, obj=None):
        settings = QtCore.QSettings()
        settings.beginGroup(classname)
        if obj:
            settings.beginGroup(obj.objectName())
            setting = '%s/%s' % (classname, obj.objectName())
        else:
            obj = self
            setting = classname

        if obj and hasattr(obj, 'restoreGeometry') and settings.value('geometry'):
            logging.getLogger(__name__).trace("Restoring geometry for %s", setting)
            obj.restoreGeometry(settings.value('geometry'))

    klass.restore_geometry_for = restore_geometry_for

    if hasattr(klass, 'setVisible'):
        def setVisible(self, visible):
            if visible:
                restore_geometry_for(self)
                restore_state_for(self)
            else:
                save_state_for(self)
                save_geometry_for(self)
            return original_setVisible(self, visible)
        klass.setVisible = setVisible

    return klass
