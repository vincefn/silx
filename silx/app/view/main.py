# coding: utf-8
# /*##########################################################################
# Copyright (C) 2016-2018 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ############################################################################*/
"""Module containing launcher of the `silx view` application"""

__authors__ = ["V. Valls"]
__license__ = "MIT"
__date__ = "17/01/2019"

import sys
import argparse
import logging
import signal


_logger = logging.getLogger(__name__)
"""Module logger"""


def createParser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'files',
        nargs=argparse.ZERO_OR_MORE,
        help='Data file to show (h5 file, edf files, spec files)')
    parser.add_argument(
        '--debug',
        dest="debug",
        action="store_true",
        default=False,
        help='Set logging system in debug mode')
    parser.add_argument(
        '--use-opengl-plot',
        dest="use_opengl_plot",
        action="store_true",
        default=False,
        help='Use OpenGL for plots (instead of matplotlib)')
    parser.add_argument(
        '--fresh',
        dest="fresh_preferences",
        action="store_true",
        default=False,
        help='Start the application using new fresh user preferences')
    return parser


def mainQt(options):
    """Part of the main depending on Qt"""
    if options.debug:
        logging.root.setLevel(logging.DEBUG)

    #
    # Import most of the things here to be sure to use the right logging level
    #

    import silx
    import silx.utils.files
    from silx.gui import qt
    # Make sure matplotlib is configured
    # Needed for Debian 8: compatibility between Qt4/Qt5 and old matplotlib
    from silx.gui.plot import matplotlib

    try:
        # it should be loaded before h5py
        import hdf5plugin  # noqa
    except ImportError:
        _logger.debug("Backtrace", exc_info=True)

    import h5py

    app = qt.QApplication([])
    qt.QLocale.setDefault(qt.QLocale.c())

    def sigintHandler(*args):
        """Handler for the SIGINT signal."""
        qt.QApplication.quit()

    signal.signal(signal.SIGINT, sigintHandler)
    sys.excepthook = qt.exceptionHandler

    timer = qt.QTimer()
    timer.start(500)
    # Application have to wake up Python interpreter, else SIGINT is not
    # catched
    timer.timeout.connect(lambda: None)

    settings = qt.QSettings(qt.QSettings.IniFormat,
                            qt.QSettings.UserScope,
                            "silx",
                            "silx-view",
                            None)
    if options.fresh_preferences:
        settings.clear()

    from .Viewer import Viewer
    window = Viewer(parent=None, settings=settings)
    window.setAttribute(qt.Qt.WA_DeleteOnClose, True)

    if options.use_opengl_plot:
        # It have to be done after the settings (after the Viewer creation)
        silx.config.DEFAULT_PLOT_BACKEND = "opengl"

    # NOTE: under Windows, cmd does not convert `*.tif` into existing files
    options.files = silx.utils.files.expand_filenames(options.files)

    for filename in options.files:
        # TODO: Would be nice to add a process widget and a cancel button
        try:
            window.appendFile(filename)
        except IOError as e:
            _logger.error(e.args[0])
            _logger.debug("Backtrace", exc_info=True)

    window.show()
    result = app.exec_()
    # remove ending warnings relative to QTimer
    app.deleteLater()
    return result


def main(argv):
    """
    Main function to launch the viewer as an application

    :param argv: Command line arguments
    :returns: exit status
    """
    parser = createParser()
    options = parser.parse_args(argv[1:])
    mainQt(options)


if __name__ == '__main__':
    main(sys.argv)
