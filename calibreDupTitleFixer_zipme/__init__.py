from calibre.customize import InterfaceActionBase

class SmartTitleFixer(InterfaceActionBase):
    name = 'CalibreDupTitleFixer'
    description = 'Fix duplicate titles using filenames, with preview, undo, and settings'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'copilot prompt'
    version = (1, 2, 0)
    minimum_calibre_version = (5, 0, 0)
    actual_plugin = 'action.py'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.smart_title_fixer.action import get_config_widget
        return get_config_widget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
