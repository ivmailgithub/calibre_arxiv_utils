from calibre.customize import InterfaceActionBase

class SmartTitleFixer(InterfaceActionBase):
    name = 'Smart Title Fixer'
    description = 'Fix duplicate titles using filenames, with undo support'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'You'
    version = (1, 1, 0)
    minimum_calibre_version = (5, 0, 0)
    actual_plugin = 'action.py'
