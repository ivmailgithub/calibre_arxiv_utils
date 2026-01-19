
# ==============================================================================
# FILE: action.py claude fixes v01f for all_id api change
# ==============================================================================
#from calibre.gui2.actions import InterfaceAction
#from calibre.gui2 import info_dialog    # this is infer class from plugin and call it will throw an error, get_icons
# note this error is repeated 3 times in 3 builds that correct something else
# make that 4 times error is repeated after correction

# ==============================================================================
# FILE: action.py
# ==============================================================================
from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import info_dialog # now 7 times repeats this bug, get_icons
from PyQt5.Qt import (
    QWidget, QVBoxLayout, QCheckBox, QLineEdit, 
    QLabel, QTextEdit, QDialog, QPushButton, QHBoxLayout, QMenu
)


class SmartTitleFixerAction(InterfaceAction):
    name = 'Smart Title Fixer'
    action_spec = (
        'Smart Title Fixer',
        None,
        'Fix duplicate titles using filenames',
        None
    )

    def genesis(self):
        # Set icon
        icon = get_icons('images/icon.png', 'Smart Title Fixer')
        self.qaction.setIcon(icon)
        
        # Create and set menu
        menu = QMenu(self.gui)
        self.qaction.setMenu(menu)
        
        # Add menu actions
        self.create_menu_action(
            menu,
            'fix-duplicates',
            'Fix Duplicate Titles',
            icon=icon,
            triggered=self.run_preview
        )
        
        self.create_menu_action(
            menu,
            'undo-action',
            'Undo Last Fix',
            icon=icon,
            triggered=self.run_undo
        )
        
        # OPTIONAL: Auto-fixer (commented out if causing issues)
        # Uncomment when you want auto-import functionality
        try:
            from calibre_plugins.smart_title_fixer.auto import AutoFixer
            # Delay initialization to avoid modifying iactions during startup
            from PyQt5.Qt import QTimer
            QTimer.singleShot(1000, lambda: self._init_auto_fixer())
        except Exception as e:
            print(f'Could not initialize auto-fixer: {e}')
    
    def _init_auto_fixer(self):
        """Initialize auto-fixer after Calibre has fully started"""
        try:
            from calibre_plugins.smart_title_fixer.auto import AutoFixer
            self.auto_fixer = AutoFixer(self.gui)
        except Exception as e:
            print(f'Error initializing auto-fixer: {e}')

    def run_preview(self):
        from calibre_plugins.smart_title_fixer import utils
        
        db = self.gui.current_db
        prefs = utils.get_prefs(db)

        changes = utils.preview_duplicates(db, same_author_only=prefs['same_author_only'])
        if not changes:
            info_dialog(
                self.gui, 
                'Smart Title Fixer', 
                'No duplicate titles found.', 
                show=True
            )
            return

        dlg = PreviewDialog(self.gui, changes)
        if dlg.exec_():
            batch_id = utils.start_new_batch()
            fixed_count = utils.fix_duplicates(
                db,
                same_author_only=prefs['same_author_only'],
                batch_id=batch_id
            )
            info_dialog(
                self.gui,
                'Smart Title Fixer',
                f'Fixed {fixed_count} titles using filenames.',
                show=True
            )

    def run_undo(self):
        from calibre_plugins.smart_title_fixer import utils
        
        db = self.gui.current_db
        restored = utils.undo_last_run(db)
        info_dialog(
            self.gui,
            'Undo Smart Title Fixer',
            f'Restored {restored} titles from last run.',
            show=True
        )


class PreviewDialog(QDialog):
    """Preview dialog showing what will be changed"""
    
    def __init__(self, parent, changes):
        super().__init__(parent)
        self.setWindowTitle('Smart Title Fixer Preview')
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Info label
        label = QLabel(f'The following {len(changes)} titles will be changed:')
        layout.addWidget(label)
        
        # Text display
        text = '\n'.join(
            f'ID {book_id}: "{old}" → "{new}"'
            for book_id, old, new in changes
        )
        self.textbox = QTextEdit(self)
        self.textbox.setReadOnly(True)
        self.textbox.setPlainText(text)
        layout.addWidget(self.textbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton('Apply Changes')
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)


class ConfigWidget(QWidget):
    """Configuration widget for plugin settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Get database from parent if available
        self.db = None
        if hasattr(parent, 'gui') and hasattr(parent.gui, 'current_db'):
            self.db = parent.gui.current_db
        
        # Lazy import to avoid circular dependencies
        from calibre_plugins.smart_title_fixer import utils
        self.prefs = utils.get_prefs(self.db)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Same author only checkbox
        self.same_author_only = QCheckBox(
            'Only treat duplicates with the same author as duplicates'
        )
        self.same_author_only.setChecked(self.prefs['same_author_only'])
        layout.addWidget(self.same_author_only)

        # Regex pattern
        layout.addWidget(QLabel('Regex cleanup for filenames:'))
        self.regex_pattern = QLineEdit(self.prefs['regex_pattern'])
        self.regex_pattern.setPlaceholderText(r'e.g., \[.*?\]|^\d+[-_]\s*')
        layout.addWidget(self.regex_pattern)

        # Regex replacement
        layout.addWidget(QLabel('Regex replacement:'))
        self.regex_replacement = QLineEdit(self.prefs['regex_replacement'])
        self.regex_replacement.setPlaceholderText('Usually empty')
        layout.addWidget(self.regex_replacement)

        # Auto import checkbox
        self.auto_on_import = QCheckBox(
            'Automatically fix titles when books are imported'
        )
        self.auto_on_import.setChecked(self.prefs['auto_on_import'])
        layout.addWidget(self.auto_on_import)

        # Help text
        help_text = QLabel(
            '<i>Note: Changes are logged for undo capability</i>'
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        layout.addStretch(1)

    def save_settings(self):
        """Save settings when user clicks OK"""
        from calibre_plugins.smart_title_fixer import utils
        
        self.prefs['same_author_only'] = self.same_author_only.isChecked()
        self.prefs['regex_pattern'] = self.regex_pattern.text()
        self.prefs['regex_replacement'] = self.regex_replacement.text()
        self.prefs['auto_on_import'] = self.auto_on_import.isChecked()
        utils.set_prefs(self.db, self.prefs)

