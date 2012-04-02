#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
"""
    :copyright: © 2011 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

import os
import subprocess
from setuptools import setup
from distutils import log
from distutils.cmd import Command, DistutilsOptionError

import qtct as package

class CompileUI(Command):
    """Build PyQt (.ui) files and resources."""

    description = "build PySide Qt GUIs (.ui)."

    user_options = [
        ('input-dir=', 'i', 'Input directory path where to search \'.ui\' files.'),
        ('output-dir=', 'o', 'Output directory path for the generated UI files.'),
        ('indent=', 'I', 'set indent width to N spaces, tab if N is 0 (default: 4)'),
        ('i18n-module', 'm', 'specify from which module the \'_()\' function '
                             'should be imported. Ex: mymodule.i18n'),
        ('ui-execute', 'x', 'generate extra code to test and display the class'),
        ('from-imports', 'F', 'generate imports relative to \'.\''),
        ('generated-extension=', 'E', 'the extension for the generated files. '
                                      'Default: ".py"'),
        ('resources-file=', 'r', 'generate the provided resources file')
    ]
    boolean_options = ['from-imports', 'ui-execute']

    def initialize_options(self):
        self.input_dir = None
        self.output_dir = None
        self.indent = 4
        self.i18n_module = None
        self.ui_execute = False
        self.from_imports = False
        self.generated_extension = '.py'
        self.resources_file = None

    def finalize_options(self):
        if self.input_dir is None:
            raise DistutilsOptionError("You need to specify the input "
                                       "directory from where to search for the "
                                       "'.ui' files")
        if self.output_dir is None:
            raise DistutilsOptionError("You need to specify the output "
                                       "directory for the generated files")
        if self.i18n_module is None:
            raise DistutilsOptionError("You need to specify from which module "
                                       "the '_()' function should be imported "
                                       "from. Example: mymodule.i18n")
        if not self.generated_extension.startswith('.'):
            raise DistutilsOptionError('Valid extensions must include a '
                                       'leading dot(.). Examples: ".py", ".pyx"')
        if self.resources_file is not None:
            import subprocess
            try:
                subprocess.check_call(["which", "pyside-rcc"])
            except subprocess.CalledProcessError:
                raise DistutilsOptionError("Cannot find \"pyside-rcc\" on "
                                           "your path.")

    def run(self):
        for filename in os.listdir(self.input_dir):
            fpath = os.path.join(self.input_dir, filename)
            if not os.path.isfile(fpath):
                continue
            elif not filename.endswith('.ui'):
                continue
            self.compile_ui(fpath)
        if self.resources_file:
            import subprocess
            output = os.path.join(
                self.output_dir, 'resources_rc%s' % self.generated_extension
            )
            try:
                subprocess.check_call(
                    ["pyside-rcc", "-o", output, self.resources_file]
                )
                log.info("Compiled %s to %s", self.resources_file, output)
            except subprocess.CalledProcessError, err:
                log.error("Failed to compile resources file: %s", err)


    def compile_ui(self, ui_file, py_file=None):
        """Compile the .ui files to python modules."""
        self._wrapuic(i18n_module=self.i18n_module)
        if py_file is None:
            py_file = os.path.join(
                self.output_dir,
                os.path.basename(ui_file).replace(
                    '.ui', self.generated_extension
                ).lower()
            )

        fi = open(ui_file, 'r')
        fo = open(py_file, 'wt')
        try:
            from pysideuic import compileUi
            compileUi(fi, fo, execute=self.ui_execute, indent=self.indent,
                      from_imports=self.from_imports)
            log.info("Compiled %s into %s", ui_file, py_file)
        except ImportError:
            log.warn("You need to have pyside-tools installed in order to "
                     "compile .ui files.")
        except Exception, err:
            log.warn("Failed to generate %r from %r: %s", py_file, ui_file, err)
            if not os.path.exists(py_file) or not not file(py_file).read():
                raise SystemExit(1)
            return
        finally:
            fi.close()
            fo.close()

    _wrappeduic = False
    @classmethod
    def _wrapuic(cls, i18n_module=None):
        """Wrap uic to use gettext's _() in place of tr()"""
        if cls._wrappeduic:
            return

        try:
            from pysideuic.Compiler import compiler, qtproxies, indenter

            class _UICompiler(compiler.UICompiler):
                """Specialised compiler for qt .ui files."""
                def createToplevelWidget(self, classname, widgetname):
                    o = indenter.getIndenter()
                    o.level = 0
                    o.write('from %s import _' % i18n_module)
                    return super(_UICompiler, self).createToplevelWidget(
                        classname, widgetname
                    )
            compiler.UICompiler = _UICompiler

            class _i18n_string(qtproxies.i18n_string):
                """Provide a translated text."""
                def __str__(self):
                    return "_('%s')" % self.string.encode('string-escape')

            qtproxies.i18n_string = _i18n_string

            cls._wrappeduic = True
        except ImportError:
            log.warn("You need to have pyside-tools installed in order to "
                     "compile .ui files.")


setup(name=package.__package_name__,
      version=package.__version__,
      author=package.__author__,
      author_email=package.__email__,
      url=package.__url__,
      description=package.__summary__,
      long_description=package.__description__,
      license=package.__license__,
      platforms="Linux",
      keywords = "QtCt - Qt Captcha Trader Client",
      packages = ['qtct'],
      package_data = {
          'qtct': [
              'i18n/*/LC_MESSAGES/qtct.mo'
          ]
      },
      install_requires = [
        "Distribute",
      ],
      cmdclass = {
        'compile_ui': CompileUI,
      },
      message_extractors = {
        'qtct': [
            ('**.py', 'python', None),
            ('**.pyx', 'python', None),
        ],
      },
      entry_points = """
      [console_scripts]
      captcha-trader-client = qtct.main:main

      [distutils.commands]
      compile = babel.messages.frontend:compile_catalog
      extract = babel.messages.frontend:extract_messages
         init = babel.messages.frontend:init_catalog
       update = babel.messages.frontend:update_catalog

      """,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Desktop Environment',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Operating System :: Linux',
          'Programming Language :: Python',
          'Topic :: Utilities',
      ]
)
