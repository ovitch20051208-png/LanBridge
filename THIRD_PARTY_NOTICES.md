# Third-party software

LanBridge's own source is MIT licensed. Dependency licenses remain applicable.
Builds include dynamically loaded Qt/PySide6 libraries; users may replace those
libraries and may reverse engineer the combined work to debug modifications to
the LGPL components. No additional restriction on those rights is imposed.

| Component | License / upstream source |
| --- | --- |
| Qt / PySide6 / Shiboken | LGPL-3.0 option for the used Core/Gui/Widgets/Network modules; [Qt source archives](https://download.qt.io/official_releases/qt/), [PySide source](https://code.qt.io/cgit/pyside/pyside-setup.git/) |
| Python | PSF License; [CPython source](https://www.python.org/downloads/source/) |
| cryptography | Apache-2.0 or BSD; [source](https://github.com/pyca/cryptography) |
| OpenSSL | Apache-2.0 for OpenSSL 3; [source](https://github.com/openssl/openssl) |
| zeroconf | LGPL-2.1-or-later; [source](https://github.com/python-zeroconf/python-zeroconf) |
| platformdirs | MIT; [source](https://github.com/tox-dev/platformdirs) |
| ifaddr | MIT; [source](https://github.com/ifaddr/ifaddr) |
| cffi / pycparser | MIT / BSD; [cffi](https://foss.heptapod.net/pypy/cffi), [pycparser](https://github.com/eliben/pycparser) |
| PyInstaller bootloader | GPL with bootloader distribution exception; [source](https://github.com/pyinstaller/pyinstaller) |

The build copies installed dependency license files into `licenses/` and records
their exact versions in `BUILD-INFO.json`. LGPL and GPL texts accompany the
distribution. Dependency projects retain their own copyright notices. No Qt
WebEngine, QML or GPL-only Qt module is intentionally included.

Source for a matching Qt build can be obtained from the exact release directory,
for example `https://download.qt.io/official_releases/qt/6.12/6.12.0/submodules/`,
and PySide from the corresponding `v6.12.0` source tag. Keep these materials
available to distribution recipients. Before a public release, review the full
transitive native-library notices and source-access obligations for the produced
platform bundle. This development package has not undergone a legal compliance
audit and is not represented as a signed production release.
