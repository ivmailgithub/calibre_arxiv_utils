# ==============================================================================
# FILE: __init__.py
# D:\prod\calibreDupTitleFixer\claudefixes13\smart_title_fixer_v1_4\claude_smart_title_fixer_v4_j_redoallfilesinpkg.py
# so something toasted the last build and calibre refuses to open with a bad dict error so either a bad py file build or the add menu action code
# barfs calibre completely ... i remove the addin from C:\Users\ilim\AppData\Roaming\calibre\plugins
# ==============================================================================
# ==============================================================================
# FILE: __init__.py v6k now claude claims the automenu loader is corrupting the calibre startup of the menu bar and the fix is to wait 100ms????
# ==============================================================================
# ==============================================================================
from calibre.customize import InterfaceActionBase

class SmartTitleFixer(InterfaceActionBase):
    name = 'Smart Title Fixer'
    description = 'Fix duplicate titles using filenames, with preview, undo, and settings'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Your Name'
    version = (1, 2, 0)
    minimum_calibre_version = (5, 0, 0)

    # FIXED: Must include :ClassName
    actual_plugin = 'calibre_plugins.smart_title_fixer.action:SmartTitleFixerAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.smart_title_fixer.action import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()

