tpMayaLib
============================================================

.. image:: https://img.shields.io/github/license/tpoveda/tpMayaLib.svg
    :target: https://github.com/tpoveda/tpPyUtils/blob/master/LICENSE

Maya implementation for tpDccLib and tpQtLib packages.

Also, this module contains a lot of utilities functions and classes to work with Maya Python APIs (cmds and OpenMaya)

Installation
-------------------
Manual
~~~~~~~~~~~~~~~~~~~~~~
1. Clone/Download tpMayaLib anywhere in your PC (If you download the repo, you will need to extract
the contents of the .zip file).
2. Copy **tpMayaLib** folder located inside **source** folder in a path added to **sys.path**

Automatic
~~~~~~~~~~~~~~~~~~~~~~
Automatic installation for tpMayaLib is not finished yet.

Usage
-------------------
Initialization Code
~~~~~~~~~~~~~~~~~~~~~~
1. If tpDccLib or tpQtLib packages are being used, tpMayaLib will be automatic imported during the initialization
of those packages.
2. If tpDccLib and tpQtLib are not found in your sys.path, you will need to initialize manually tpMayaLib.

.. code-block:: python

    import tpMayaLib
    tpMayaLib.init()


Reloading
~~~~~~~~~~~~~~~~~~~~~~
For development purposes, you can enable reloading system, so 
you can reload tpMayaLib sources without the necessity of restarting
your Python session. Useful when working with DCCs.

1. If tpDccLib and tpQtLib packages are being used, tpMayaLib will be automatic reload by tpDccLib and tpQtLib reload systems.
2. If tpDccLib and tpQtLib are not found, you will need to reload tpMayaLib manually.

.. code-block:: python

    import tpMayaLib
    reload(tpMayaLib)
    tpMayaLib.init(True)


Enabling debug log
~~~~~~~~~~~~~~~~~~~~~~
By default, tpMayaLib logger only logs warning messages. To enable all log messages
you can set TPMAYALIB_DEV environment variables to 'True'

.. code-block:: python

    import os

    os.environ['TPMAYALIB_DEV'] = 'True'
    import tpMayaLib
    tpMayaLib.init()