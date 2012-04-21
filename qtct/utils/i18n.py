# -*- coding: utf-8 -*-
"""
    qtct.utils.i18n
    ~~~~~~~~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""


import os
import logging
import pkg_resources
from qtct import __package_name__, __version__
from babel import Locale
from babel.support import Translations as BaseTranslations
from PySide import QtCore, QtGui

log = logging.getLogger(__name__)

def get_resource(module, path):
    package_req = "%s>=%s" % (__package_name__, __version__)
    return pkg_resources.require(package_req)[0].get_resource_filename(
            pkg_resources._manager, os.path.join(*(module.split('.')+[path]))
    )

__AVAILABLE_LOCALES = []

def get_available_locales():
    global __AVAILABLE_LOCALES
    if not __AVAILABLE_LOCALES:
        available_locales = []
        i18n_base_path = get_resource("qtct", "i18n")
        for locale in os.listdir(i18n_base_path):
            mo_file_path = os.path.join(
                i18n_base_path, locale, "LC_MESSAGES", "qtct.mo"
            )
            if os.path.isfile(mo_file_path):
                available_locales.append(Locale(locale))

        __AVAILABLE_LOCALES = available_locales
    return __AVAILABLE_LOCALES


class Translations(BaseTranslations):

    @classmethod
    def load(cls):
        settings = QtCore.QSettings()
        locale = settings.value("locale")
        if not locale:
            settings.setValue("locale", "en")

        locale = settings.value("locale")
        log.debug("Setting locale to: %s", locale)
        translations = BaseTranslations.load(
            get_resource("qtct", "i18n"), [locale, "en"], domain='qtct'
        )
        return translations


def lazy_gettext(text, *args, **kwargs):
    try:
        translation = QtGui.qApp.translations.ugettext(text)
        if args and kwargs:
            return translation.replace('%s', '%%s') % kwargs % args
        elif args:
            return translation % args
        elif kwargs:
            return translation % kwargs
        else:
            return translation
    except (KeyError, AttributeError):
        return text.replace('%s', '%%s') % kwargs % args

_ = lazy_gettext