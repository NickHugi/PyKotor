from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from qtpy.QtCore import QStringListModel, Qt
from qtpy.QtGui import QStandardItemModel
from qtpy.QtWidgets import QComboBox, QCompleter, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class EnvVar(NamedTuple):
    name: str
    description: str
    default: str
    possible_values: str
    doc_link: str
    group: str


ENV_VARS: list[EnvVar] = sorted(
    [
        EnvVar(name="QT_3D_OPENGL_CONTEXT_PROFILE", description="Specifies the OpenGL context profile for 3D.", default="core", possible_values="core, compatibility", doc_link="https://doc.qt.io/qt-5/qtopengl.html", group="3D"),  # noqa: E501
        EnvVar(name="QT_AUTO_SCREEN_SCALE_FACTOR", description="Enables automatic scaling of screen content.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/highdpi.html", group="High DPI"),  # noqa: E501
        EnvVar(name="QT_DEBUG_CONSOLE", description="Enables the debug console for logging.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qdebug.html", group="Debugging"),  # noqa: E501
        EnvVar(name="QT_DEBUG_PLUGINS", description="Enables debugging for plugins.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/plugins-howto.html", group="Debugging"),  # noqa: E501
        EnvVar(name="QT_DEPRECATION_WARNINGS", description="Enables or disables deprecation warnings.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qglobal.html#Q_DEPRECATED", group="General"),  # noqa: E501
        EnvVar(name="QT_EGLFS_HEIGHT", description="Specifies the height for EGLFS.", default="Your screen height", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="EGLFS"),  # noqa: E501
        EnvVar(name="QT_EGLFS_PHYSICAL_HEIGHT", description="Sets the physical height for EGLFS.", default="Screen physical height", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="EGLFS"),  # noqa: E501
        EnvVar(name="QT_EGLFS_PHYSICAL_WIDTH", description="Sets the physical width for EGLFS.", default="Screen physical width", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="EGLFS"),  # noqa: E501
        EnvVar(name="QT_EGLFS_WIDTH", description="Specifies the width for EGLFS.", default="Screen width", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="EGLFS"),  # noqa: E501
        EnvVar(name="QT_ENABLE_HIGHDPI_SCALING", description="Enables automatic high-DPI scaling.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/highdpi.html", group="High DPI"),  # noqa: E501
        EnvVar(name="QT_FB_FORCE_FULLSCREEN", description="Forces fullscreen mode in framebuffer.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="Framebuffer"),  # noqa: E501
        EnvVar(name="QT_FONT_DPI", description="Overrides the default font DPI.", default="96", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/highdpi.html", group="High DPI"),  # noqa: E501
        EnvVar(name="QT_FORCE_CLEANUP_ON_EXIT", description="Forces cleanup on exit.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtglobal.html", group="General"),  # noqa: E501
        EnvVar(name="QT_FORCE_PLUGIN_FILE_LOADING", description="Forces loading plugins from files.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/plugins-howto.html", group="Plugins"),  # noqa: E501
        EnvVar(name="QT_FORCE_TLS1_2", description="Forces the use of TLS 1.2.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtnetwork.html", group="Network"),  # noqa: E501
        EnvVar(name="QT_FORCE_XRUNTIME", description="Forces the use of XRUNTIME.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/x11extras.html", group="X11"),  # noqa: E501
        EnvVar(name="QT_GSTREAMER_PLUGIN_PATH", description="Specifies the path for GStreamer plugins.", default="System path", possible_values="Any valid directory path", doc_link="https://doc.qt.io/qt-5/qtmultimedia.html", group="Multimedia"),  # noqa: E501
        EnvVar(name="QT_GRAPHICSSYSTEM", description="Specifies the graphics system to use.", default="opengl", possible_values="opengl, raster", doc_link="https://doc.qt.io/qt-5/qtsystems.html", group="Graphics"),  # noqa: E501
        EnvVar(name="QT_IM_MODULE", description="Specifies the input method module to use.", default="xim", possible_values="xim, ibus, fcitx", doc_link="https://doc.qt.io/qt-5/inputmethods.html", group="Input"),  # noqa: E501
        EnvVar(name="QT_LARGEFILE_SUPPORT", description="Enables support for large files.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtglobal.html", group="Filesystem"),  # noqa: E501
        EnvVar(name="QT_LINUX_ACCESSIBILITY_ALWAYS_ON", description="Forces accessibility support on Linux.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtglobal.html", group="Accessibility"),  # noqa: E501
        EnvVar(name="QT_LOGGING_CONF", description="Specifies the logging configuration file.", default="None", possible_values="Any valid file path", doc_link="https://doc.qt.io/qt-5/qloggingcategory.html", group="Logging"),  # noqa: E501
        EnvVar(name="QT_LOGGING_DEPLOY", description="Enables logging for deployment.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qloggingcategory.html", group="Logging"),  # noqa: E501
        EnvVar(name="QT_LOGGING_RULES", description="Configures logging rules for categories.", default="None", possible_values="Category filter string", doc_link="https://doc.qt.io/qt-5/qloggingcategory.html", group="Logging"),  # noqa: E501
        EnvVar(name="QT_LOGGING_TO_CONSOLE", description="Enables logging to the console.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qloggingcategory.html", group="Logging"),  # noqa: E501
        EnvVar(name="QT_NETWORK_PROXY", description="Configures network proxy settings.", default="None", possible_values="proxy settings", doc_link="https://doc.qt.io/qt-5/qnetworkproxy.html", group="Network"),  # noqa: E501
        EnvVar(name="QT_NO_CHILD_STYLE", description="Disables child widget styling.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/stylesheet.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_NO_COLOR_STYLE", description="Disables color styling.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/stylesheet.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_NO_FONT_FALLBACK", description="Disables font fallback.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qfont.html", group="Fonts"),  # noqa: E501
        EnvVar(name="QT_NO_LINKING", description="Disables linking checks.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtglobal.html", group="General"),  # noqa: E501
        EnvVar(name="QT_NO_SHORTCUT_OVERRIDE", description="Disables shortcut overrides.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qshortcut.html", group="Input"),  # noqa: E501
        EnvVar(name="QT_NO_VENDOR_VARIABLES", description="Disables vendor-specific environment variables.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtglobal.html", group="General"),  # noqa: E501
        EnvVar(name="QT_OPENGL", description="Sets the type of OpenGL implementation.", default="desktop", possible_values="desktop, es2, software", doc_link="https://doc.qt.io/qt-5/qtopengl.html", group="Graphics"),  # noqa: E501
        EnvVar(name="QT_OPENGL_DEBUG", description="Enables OpenGL debugging.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtopengl.html", group="Graphics"),  # noqa: E501
        EnvVar(name="QT_PLUGIN_PATH", description="Specifies the search path for plugins.", default="System path", possible_values="Any valid directory path", doc_link="https://doc.qt.io/qt-5/plugins-howto.html", group="Plugins"),  # noqa: E501
        EnvVar(name="QT_QPA_EGLFS_DISABLE_INPUT", description="Disables input on EGLFS.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="EGLFS"),  # noqa: E501
        EnvVar(name="QT_QPA_EGLFS_FORCEVSYNC", description="Forces VSync on EGLFS.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="EGLFS"),  # noqa: E501
        EnvVar(name="QT_QPA_EGLFS_INTEGRATION", description="Specifies the EGLFS backend.", default="None", possible_values="eglfs, kms, mali", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="EGLFS"),  # noqa: E501
        EnvVar(name="QT_QPA_EGLFS_KMS_CONFIG", description="Specifies KMS configuration for EGLFS.", default="None", possible_values="Any valid file path", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="EGLFS"),  # noqa: E501
        EnvVar(name="QT_QPA_EGLFS_NO_VSYNC", description="Disables VSync on EGLFS.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="EGLFS"),  # noqa: E501
        EnvVar(name="QT_QPA_FB_DRM", description="Enables DRM support in the framebuffer.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="Framebuffer"),  # noqa: E501
        EnvVar(name="QT_QPA_FB_FORCE_DOUBLE_BUFFER", description="Forces double buffering in framebuffer.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="Framebuffer"),  # noqa: E501
        EnvVar(name="QT_QPA_FB_FORCE_FULLSCREEN", description="Forces fullscreen mode in framebuffer.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="Framebuffer"),  # noqa: E501
        EnvVar(name="QT_QPA_FB_NO_LIBINPUT", description="Disables libinput support in framebuffer.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="Framebuffer"),  # noqa: E501
        EnvVar(name="QT_QPA_FB_NO_TSLIB", description="Disables tslib support in framebuffer.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="Framebuffer"),  # noqa: E501
        EnvVar(name="QT_QPA_FB_TSLIB", description="Enables tslib support on Linux/FB.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/embedded-linux.html", group="Framebuffer"),  # noqa: E501
        EnvVar(name="QT_QPA_FONTDIR", description="Specifies the font directory.", default="System path", possible_values="Any valid directory path", doc_link="https://doc.qt.io/qt-5/qpa.html", group="Fonts"),  # noqa: E501
        EnvVar(name="QT_QPA_FORCE_NATIVE_WINDOWS", description="Forces native windows in QPA.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_GENERIC_PLUGINS", description="Specifies generic plugins to load.", default="None", possible_values="Comma-separated list of plugins", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_MULTIMONITOR", description="Enables multi-monitor support.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_NO_SYSTEM_TRAY", description="Disables the system tray.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_OFFSCREEN", description="Enables offscreen rendering.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_PLATFORM", description="Specifies the platform plugin to load.", default="xcb", possible_values="xcb, wayland, eglfs", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_PLATFORM_PLUGIN_PATH", description="Specifies the platform plugin search path.", default="System path", possible_values="Any valid directory path", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_PLATFORMTHEME", description="Specifies the platform theme plugin to use.", default="None", possible_values="Any valid theme name", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_RHI_BACKEND", description="Specifies the RHI backend to use.", default="None", possible_values="vulkan, metal, d3d11, opengl", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_SCREEN_SCALE_FACTORS", description="Specifies screen scale factors.", default="None", possible_values="Comma-separated list of scale factors", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_USE_RGBA", description="Forces the use of RGBA for platform surfaces.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_XCB_NATIVE_PAINTING", description="Enables native painting on XCB.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_XCB_TABLET_LEGACY", description="Enables legacy tablet support on XCB.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_XCB_GL_INTEGRATION", description="Selects the XCB OpenGL integration plugin.", default="None", possible_values="xcb-glx, xcb-egl", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_XCB_NO_MITSHM", description="Disables MIT-SHM on X11.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QPA_XCB_RENDERER", description="Specifies the renderer to use on XCB.", default="None", possible_values="Any valid renderer name", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_QUICK_CONTROLS_1_STYLE", description="Specifies the style for Quick Controls 1.", default="None", possible_values="Any valid style name", doc_link="https://doc.qt.io/qt-5/qtquickcontrols-index.html", group="Quick Controls"),  # noqa: E501,
        EnvVar(name="QT_QUICK_CONTROLS_CONF", description="Specifies the configuration file for Quick Controls.", default="None", possible_values="Any valid file path", doc_link="https://doc.qt.io/qt-5/qtquickcontrols-index.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_QUICK_CONTROLS_FALLBACK_STYLE", description="Sets the fallback style for Quick Controls.", default="None", possible_values="Any valid style name", doc_link="https://doc.qt.io/qt-5/qtquickcontrols-index.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_QUICK_CONTROLS_HOVER_ENABLED", description="Enables hover events for Quick Controls.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtquickcontrols-index.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_QUICK_CONTROLS_MATERIAL_THEME", description="Sets the Material theme for Quick Controls.", default="None", possible_values="Any valid theme name", doc_link="https://doc.qt.io/qt-5/qtquickcontrols-index.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_QUICK_CONTROLS_STYLE", description="Specifies the style for Quick Controls.", default="None", possible_values="Any valid style name", doc_link="https://doc.qt.io/qt-5/qtquickcontrols-index.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_SCALE_FACTOR", description="Sets the scale factor for the application.", default="1.0", possible_values="Any positive floating-point value", doc_link="https://doc.qt.io/qt-5/highdpi.html", group="High DPI"),  # noqa: E501
        EnvVar(name="QT_SSL_CERTIFICATES", description="Specifies the path to SSL certificates.", default="System path", possible_values="Any valid directory path", doc_link="https://doc.qt.io/qt-5/qtnetwork.html", group="Network"),  # noqa: E501
        EnvVar(name="QT_SSL_NO_WARN_CIPHERS", description="Disables SSL cipher warnings.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtnetwork.html", group="Network"),  # noqa: E501
        EnvVar(name="QT_STYLE_OVERRIDE", description="Forces the use of a specific style.", default="None", possible_values="Any valid style name", doc_link="https://doc.qt.io/qt-5/qstyle.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_USE_NATIVE_WINDOWS", description="Enables or disables native windows.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_USE_QIODEVICE_OPEN_MODE", description="Uses the open mode of QIODevice.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qiodevice.html", group="General"),  # noqa: E501
        EnvVar(name="QT_USE_QSTRINGBUILDER", description="Enables the use of QStringBuilder.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qstringbuilder.html", group="General"),  # noqa: E501
        EnvVar(name="QT_VIRTUALKEYBOARD_DISABLE_TIMESTAMPS", description="Disables timestamps for virtual keyboard.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtvirtualkeyboard.html", group="Virtual Keyboard"),  # noqa: E501
        EnvVar(name="QT_VIRTUALKEYBOARD_LAYOUT_PATH", description="Specifies the path for virtual keyboard layouts.", default="None", possible_values="Any valid directory path", doc_link="https://doc.qt.io/qt-5/qtvirtualkeyboard.html", group="Virtual Keyboard"),  # noqa: E501
        EnvVar(name="QT_VULKAN_LAYER_PATH", description="Specifies the path to Vulkan layers.", default="None", possible_values="Any valid directory path", doc_link="https://doc.qt.io/qt-5/qvulkaninstance.html", group="Vulkan"),  # noqa: E501
        EnvVar(name="QT_WEBENGINE_CHROMIUM_FLAGS", description="Passes flags to the embedded Chromium.", default="None", possible_values="Any valid Chromium flag", doc_link="https://doc.qt.io/qt-5/qtwebengine.html", group="WebEngine"),  # noqa: E501
        EnvVar(name="QT_WEBENGINE_DISABLE_GPU", description="Disables GPU acceleration in WebEngine.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtwebengine.html", group="WebEngine"),  # noqa: E501
        EnvVar(name="QT_WIDGETS_BYPASS_NATIVE_EVENTS", description="Bypasses native events in Qt Widgets.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtwidgets-index.html", group="Widgets"),  # noqa: E501
        EnvVar(name="QT_WIDGETS_DISABLE_NATIVE_WIDGETS", description="Disables native widgets support.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtwidgets-index.html", group="Widgets"),  # noqa: E501
        EnvVar(name="QT_WIDGETS_FATAL_WARNINGS", description="Treats warnings as fatal in Qt Widgets.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtwidgets-index.html", group="Widgets"),  # noqa: E501
        EnvVar(name="QT_XCB_FORCE_SOFTWARE_VSYNC", description="Forces software VSync on XCB.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="XCB"),  # noqa: E501
        EnvVar(name="QT_XCB_GL_INTEGRATION", description="Selects the XCB OpenGL integration plugin.", default="xcb-glx", possible_values="xcb-glx, xcb-egl", doc_link="https://doc.qt.io/qt-5/qpa.html", group="XCB"),  # noqa: E501
        EnvVar(name="QT_XCB_RENDERER", description="Specifies the renderer to use on XCB.", default="None", possible_values="Any valid renderer name", doc_link="https://doc.qt.io/qt-5/qpa.html", group="XCB"),  # noqa: E501
        EnvVar(name="QT_XCB_TABLET_LEGACY", description="Enables legacy tablet support on XCB.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpa.html", group="XCB"),  # noqa: E501
        EnvVar(name="QT_X11_NO_MITSHM", description="Disables MIT-SHM on X11.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/x11extras.html", group="X11"),  # noqa: E501
        EnvVar(name="QTWEBENGINE_CHROMIUM_FLAGS", description="Passes flags to the embedded Chromium.", default="None", possible_values="Any valid Chromium flag", doc_link="https://doc.qt.io/qt-5/qtwebengine.html", group="WebEngine"),  # noqa: E501
        EnvVar(name="QTWEBENGINE_DISABLE_SANDBOX", description="Disables the Chromium sandbox.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtwebengine.html", group="WebEngine"),  # noqa: E501
        EnvVar(name="QTWEBENGINE_PROCESS_PATH", description="Specifies the WebEngine process path.", default="None", possible_values="Any valid file path", doc_link="https://doc.qt.io/qt-5/qtwebengine.html", group="WebEngine"),  # noqa: E501
        EnvVar(name="QTWEBENGINE_PROFILE", description="Specifies the WebEngine profile to use.", default="None", possible_values="Any valid profile name", doc_link="https://doc.qt.io/qt-5/qtwebengine.html", group="WebEngine"),  # noqa: E501
        EnvVar(name="QT_QPA_PLATFORMTHEME", description="Specifies the platform theme to use.", default="None", possible_values="Any valid theme name", doc_link="https://doc.qt.io/qt-5/qpa.html", group="QPA"),  # noqa: E501
        EnvVar(name="QT_ENABLE_GLYPH_CACHE", description="Enables the glyph cache in the raster engine.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpainter.html", group="Graphics"),  # noqa: E501
        EnvVar(name="QT_LOGGING_ENABLED", description="Enables logging globally for the application.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qloggingcategory.html", group="Logging"),  # noqa: E501
        EnvVar(name="QT_NO_DIRECT3D", description="Disables Direct3D support.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/windows.html", group="Graphics"),  # noqa: E501
        EnvVar(name="QT_OPACITY_THRESHOLD", description="Sets the opacity threshold for translucent windows.", default="0.5", possible_values="Any positive floating-point value", doc_link="https://doc.qt.io/qt-5/qwidget.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_SCALE_FACTOR_ROUNDING_POLICY", description="Specifies the rounding policy for scaling factors.", default="Round", possible_values="Round, Ceil, Floor", doc_link="https://doc.qt.io/qt-5/qhighdpiscaling.html", group="High DPI"),  # noqa: E501
        EnvVar(name="QT_WIDGETS_TEXTURE_SIZE", description="Specifies the texture size for widget rendering.", default="None", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/qtwidgets-index.html", group="Widgets"),  # noqa: E501
        EnvVar(name="QT_WINRT_FORCE", description="Forces the use of WinRT platform integration.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/winrt.html", group="Windows"),  # noqa: E501
        EnvVar(name="QT_WINRT_HIDPI_SCALING", description="Enables HiDPI scaling on WinRT.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/winrt.html", group="Windows"),  # noqa: E501
        EnvVar(name="QT_ANIMATION_DURATION_FACTOR", description="Scales the duration of animations globally.", default="1.0", possible_values="Any positive floating-point value", doc_link="https://doc.qt.io/qt-5/qpropertyanimation.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_AUTO_SCREEN_ROTATION", description="Enables automatic screen rotation based on sensor data.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qscreen.html", group="General"),  # noqa: E501
        EnvVar(name="QT_COMPACT_CONTROLS", description="Forces the use of compact controls for UI elements.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtquickcontrols-index.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_CUSTOM_CURSOR_THEME", description="Specifies a custom theme for mouse cursors.", default="None", possible_values="Any valid theme name", doc_link="https://doc.qt.io/qt-5/qcursor.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_ENABLE_EXTENDED_TYPES", description="Enables support for extended data types in QVariant.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qvariant.html", group="General"),  # noqa: E501
        EnvVar(name="QT_ENABLE_TRANSLUCENT_WINDOWS", description="Enables translucent window support.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qwidget.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_FONT_CACHE_SIZE", description="Sets the size of the font cache.", default="2048", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/qfont.html", group="Fonts"),  # noqa: E501
        EnvVar(name="QT_GRAPHICSSYSTEM_DEBUG", description="Enables debugging for the graphics system.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtopengl.html", group="Graphics"),  # noqa: E501
        EnvVar(name="QT_HOTKEYS_DISABLED", description="Disables global hotkeys in the application.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qshortcut.html", group="Input"),  # noqa: E501
        EnvVar(name="QT_IGNORE_DEPRECATED_WARNINGS", description="Ignores warnings about deprecated functions.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qglobal.html#Q_DECL_DEPRECATED", group="Debugging"),  # noqa: E501
        EnvVar(name="QT_IMAGE_CACHE_SIZE", description="Sets the size of the image cache.", default="1024", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/qimage.html", group="Graphics"),  # noqa: E501
        EnvVar(name="QT_IM_SWITCHER_VISIBLE", description="Forces the visibility of the input method switcher.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qinputmethod.html", group="Input"),  # noqa: E501
        EnvVar(name="QT_INVERT_COLORS", description="Inverts colors globally in the application.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qcolor.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_KEEP_SYSTEM_IDLE", description="Prevents the system from entering idle state while the application is running.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qsystemtrayicon.html", group="General"),  # noqa: E501
        EnvVar(name="QT_KEYBOARD_LAYOUT", description="Specifies the keyboard layout to use.", default="System layout", possible_values="Any valid layout identifier", doc_link="https://doc.qt.io/qt-5/qkeysequence.html", group="Input"),  # noqa: E501
        EnvVar(name="QT_MAXIMUM_TEXTURE_SIZE", description="Sets the maximum texture size for rendering.", default="None", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/qopenglwidget.html", group="Graphics"),  # noqa: E501
        EnvVar(name="QT_MINIMUM_WIDGET_SIZE", description="Sets the minimum size for all widgets.", default="None", possible_values="Any valid size", doc_link="https://doc.qt.io/qt-5/qwidget.html", group="Widgets"),  # noqa: E501
        EnvVar(name="QT_MOUSE_ACCELERATION", description="Enables or disables mouse acceleration.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qcursor.html", group="Input"),  # noqa: E501
        EnvVar(name="QT_NO_ANIMATIONS", description="Disables all animations in the application.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qpropertyanimation.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_NO_SCREEN_SAVER", description="Prevents the screen saver from being activated.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qscreen.html", group="General"),  # noqa: E501
        EnvVar(name="QT_NO_SPLASH_SCREEN", description="Disables the splash screen.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qsplashscreen.html", group="General"),  # noqa: E501
        EnvVar(name="QT_NO_UNDERSCORE_ACCEL", description="Disables underscore shortcuts in menus.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qmenu.html", group="Input"),  # noqa: E501
        EnvVar(name="QT_OPENGL_FORCE_MSAA", description="Forces multisample anti-aliasing (MSAA) in OpenGL.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qopenglwidget.html", group="Graphics"),  # noqa: E501
        EnvVar(name="QT_OPACITY_ROUNDED", description="Enables rounded opacity values for widgets.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qwidget.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_OVERRIDE_WINDOW_STATE", description="Overrides the default window state behavior.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qwindow.html", group="General"),  # noqa: E501
        EnvVar(name="QT_POINTER_EVENTS_ENABLED", description="Enables pointer events globally in the application.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qevent.html", group="Input"),  # noqa: E501
        EnvVar(name="QT_PRELOAD_THEMES", description="Preloads themes to speed up theme switching.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qstyle.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_PRINT_DEBUG_INFO", description="Prints debug information to the console.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qdebug.html", group="Debugging"),  # noqa: E501
        EnvVar(name="QT_QUICK_ACCELERATED_RENDERING", description="Forces accelerated rendering in Qt Quick.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtquick-index.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_QUICK_DISABLE_SHADERS", description="Disables shader programs in Qt Quick.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtquick-index.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_QUICK_FORCE_GL_TEXTURE", description="Forces the use of GL textures in Qt Quick.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtquick-index.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_QUICK_FPS", description="Enables displaying frames per second (FPS) in Qt Quick applications.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtquick-index.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_QUICK_PARTICLE_SYSTEM", description="Enables the particle system in Qt Quick.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qtquick-particles.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_QUICK_TOUCH_HANDLERS", description="Enables touch handlers in Qt Quick.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qquickitem.html", group="Quick Controls"),  # noqa: E501
        EnvVar(name="QT_QWS_DISPLAY", description="Specifies the display to use in Qt for Embedded Linux.", default="/dev/fb0", possible_values="Any valid framebuffer device", doc_link="https://doc.qt.io/archives/qt-4.8/qws.html", group="Embedded Linux"),  # noqa: E501
        EnvVar(name="QT_QWS_MOUSE_PROTO", description="Specifies the mouse protocol for Qt for Embedded Linux.", default="Auto", possible_values="Auto, linuxinput, qvfbmouse", doc_link="https://doc.qt.io/archives/qt-4.8/qws.html", group="Embedded Linux"),  # noqa: E501
        EnvVar(name="QT_QWS_SIZE", description="Sets the size of the display in Qt for Embedded Linux.", default="None", possible_values="Any valid size", doc_link="https://doc.qt.io/archives/qt-4.8/qws.html", group="Embedded Linux"),  # noqa: E501
        EnvVar(name="QT_QWS_KEYBOARD", description="Specifies the keyboard protocol for Qt for Embedded Linux.", default="Auto", possible_values="Auto, linuxinput, qvfbkbd", doc_link="https://doc.qt.io/archives/qt-4.8/qws.html", group="Embedded Linux"),  # noqa: E501
        EnvVar(name="QT_QWS_SHM", description="Enables shared memory support in Qt for Embedded Linux.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/archives/qt-4.8/qws.html", group="Embedded Linux"),  # noqa: E501
        EnvVar(name="QT_QWS_DEPTH", description="Specifies the color depth for Qt for Embedded Linux.", default="16", possible_values="16, 24, 32", doc_link="https://doc.qt.io/archives/qt-4.8/qws.html", group="Embedded Linux"),  # noqa: E501
        EnvVar(name="QT_QWS_NO_TRANSFORMATIONS", description="Disables transformations in Qt for Embedded Linux.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/archives/qt-4.8/qws.html", group="Embedded Linux"),  # noqa: E501
        EnvVar(name="QT_QWS_SERVER", description="Specifies the Qt Windowing System (QWS) server.", default="None", possible_values="Any valid server path", doc_link="https://doc.qt.io/archives/qt-4.8/qws.html", group="Embedded Linux"),  # noqa: E501
        EnvVar(name="QT_REDUCE_DEBUG_OUTPUT", description="Reduces the amount of debug output generated.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qdebug.html", group="Debugging"),  # noqa: E501
        EnvVar(name="QT_SCROLL_BAR_FADE_DURATION", description="Sets the fade duration for scroll bars.", default="400", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/qscrollbar.html", group="Widgets"),  # noqa: E501
        EnvVar(name="QT_SCROLL_BAR_POLICY", description="Specifies the scroll bar policy.", default="Auto", possible_values="Auto, AlwaysOn, AlwaysOff", doc_link="https://doc.qt.io/qt-5/qscrollarea.html", group="Widgets"),  # noqa: E501
        EnvVar(name="QT_STYLE_SHEET_LOADING", description="Enables style sheet loading from an external file.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/stylesheet.html", group="Styling"),  # noqa: E501
        EnvVar(name="QT_TOUCHPAD_SCROLLING", description="Enables touchpad scrolling in the application.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qscrollarea.html", group="Input"),  # noqa: E501
        EnvVar(name="QT_USE_NATIVE_DIALOGS", description="Forces the use of native file dialogs.", default="1", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qfiledialog.html", group="General"),  # noqa: E501
        EnvVar(name="QT_USE_SOFTWARE_OPENGL", description="Forces the use of software rendering for OpenGL.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/qopenglwidget.html", group="Graphics"),  # noqa: E501
        EnvVar(name="QT_WAYLAND_DISABLE_INPUT_METHOD", description="Disables the input method on Wayland.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/wayland.html", group="Wayland"),  # noqa: E501
        EnvVar(name="QT_WAYLAND_FORCE_DPI", description="Forces the DPI setting on Wayland.", default="None", possible_values="Any positive integer", doc_link="https://doc.qt.io/qt-5/wayland.html", group="Wayland"),  # noqa: E501
        EnvVar(name="QT_WAYLAND_USE_NATIVE_WINDOWS", description="Forces the use of native windows on Wayland.", default="0", possible_values="0, 1", doc_link="https://doc.qt.io/qt-5/wayland.html", group="Wayland"),  # noqa: E501
        EnvVar(name="QT_WIDGET_ANIMATION_SPEED", description="Sets the speed of widget animations.", default="1.0", possible_values="Any positive floating-point value", doc_link="https://doc.qt.io/qt-5/qwidget.html", group="Styling"),  # noqa: E501
    ],
    key=lambda x: x[0],
)


class EnvVariableDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        from toolset.gui.common.localization import translate as tr
        self.setWindowTitle(tr("Edit Qt Environment Variable"))

        # Layouts
        main_layout = QVBoxLayout(self)
        name_layout = QHBoxLayout()
        value_layout = QHBoxLayout()
        buttons_layout = QHBoxLayout()
        docs_layout = QVBoxLayout()

        # Widgets
        self.name_label = QLabel("Variable name:")
        name_layout.addWidget(self.name_label)
        self.value_label = QLabel("Variable value:")
        value_layout.addWidget(self.value_label)

        self.name_edit = QComboBox()
        self.name_edit.setEditable(True)

        for env_var in ENV_VARS:
            self.name_edit.addItem(env_var.name)
            self.name_edit.setItemData(self.name_edit.count() - 1, env_var.description, Qt.ToolTipRole)
        name_layout.addWidget(self.name_edit)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.value_edit = QLineEdit()
        self.value_completer = QCompleter()
        self.value_edit.setCompleter(self.value_completer)
        self.value_edit.textChanged.connect(self.check_value_validity)
        value_layout.addWidget(self.value_edit)

        self.browse_dir_button = QPushButton("Browse Directory...")
        buttons_layout.addWidget(self.browse_dir_button)
        self.browse_file_button = QPushButton("Browse File...")
        buttons_layout.addWidget(self.browse_file_button)
        buttons_layout.addStretch()
        self.ok_button = QPushButton("OK")
        buttons_layout.addWidget(self.ok_button)
        self.cancel_button = QPushButton("Cancel")
        buttons_layout.addWidget(self.cancel_button)

        self.doc_link_label = QLabel()
        self.doc_link_label.setOpenExternalLinks(True)
        self.doc_link_label.setTextFormat(Qt.RichText)
        docs_layout.addWidget(self.doc_link_label)

        self.description_edit = QTextEdit()
        self.description_edit.setReadOnly(True)
        self.description_edit.setFrameStyle(QFrame.NoFrame)  # For a cleaner look
        self.description_edit.setStyleSheet("background-color: transparent;")
        self.description_edit.setMaximumHeight(self.description_edit.minimumSizeHint().height())
        docs_layout.addWidget(self.description_edit)

        # Setup Layouts
        main_layout.addLayout(name_layout)
        main_layout.addLayout(value_layout)
        main_layout.addLayout(buttons_layout)
        main_layout.addLayout(docs_layout)

        # Connections
        self.name_edit.currentTextChanged.connect(self.update_description_and_completer)
        self.browse_dir_button.clicked.connect(self.browse_directory)
        self.browse_file_button.clicked.connect(self.browse_file)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Initialize description and completer
        self.update_description_and_completer()

    def update_description_and_completer(self):
        """Updates the description, doc link, and value completer based on the selected variable."""
        current_var = next(
            (
                var
                for var in ENV_VARS
                if var.name == self.name_edit.currentText()
            ),
            None,
        )
        if current_var:
            self.doc_link_label.setText(f'<a href="{current_var.doc_link}">Documentation ({current_var.doc_link})</a>')
            self.description_edit.setText(current_var.description)

            # Update completer for value_edit
            if current_var.possible_values:
                possible_values = current_var.possible_values.split(", ")
                self.value_completer.setModel(QStandardItemModel())
                self.value_completer.setModel(QStringListModel(possible_values))
            else:
                self.value_completer.setModel(QStandardItemModel())  # Empty model if no possible values


    def check_value_validity(self):
        """Checks if the current value matches the possible values and adds a red border if it doesn't."""
        current_var = next(
            (
                var
                for var in ENV_VARS
                if var.name == self.name_edit.currentText()
            ),
            None,
        )
        if current_var and current_var.possible_values:
            if current_var.possible_values == "Any positive integer":
                try:
                    value = int(self.value_edit.text())
                    if value > 0:
                        self.value_edit.setStyleSheet("")  # Valid positive integer
                    else:
                        self.value_edit.setStyleSheet("border: 1px solid red;")  # Not a positive integer
                except ValueError:
                    self.value_edit.setStyleSheet("border: 1px solid red;")  # Not an integer
            else:
                possible_values = current_var.possible_values.split(", ")
                if self.value_edit.text() not in possible_values:
                    self.value_edit.setStyleSheet("border: 1px solid red;")
                else:
                    self.value_edit.setStyleSheet("")
        else:
            self.value_edit.setStyleSheet("")

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.value_edit.setText(directory)

    def browse_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file:
            self.value_edit.setText(file)

    def get_data(self) -> tuple[str, str]:
        return self.name_edit.currentText(), self.value_edit.text()

    def set_data(self, name: str, value: str):
        self.name_edit.setCurrentText(name)
        self.value_edit.setText(value)
