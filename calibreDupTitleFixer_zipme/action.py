from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import info_dialog
from calibre.gui2.dialogs.message_box import MessageBox
from PyQt5.Qt import QWidget, QVBoxLayout, QCheckBox, QLineEdit, QLabel, QPushButton, QTextEdit

from calibre_plugins.smart_title_fixer.utils import (
    fix_duplicates,
    undo_last_run,
    start_new_batch,
    get_prefs,
    set_prefs,
    preview_duplicates,
)
from calibre_plugins.smart_title_fixer.auto import AutoFixer


class SmartTitleFixerAction(InterfaceAction):
    name = 'Smart Title Fixer'

    def genesis(self):
        self.qaction.setText('Smart Title Fixer')
        self.qaction.setToolTip('Fix duplicate titles using filenames')
        self.qaction.triggered.connect(self.run_preview)

        # Undo action
        self.undo_action = self.create_action(
            spec=('Undo Smart Title Fixer', None, 'Undo last title fix run'),
            attr='undo_action'
        )
        self.undo_action.triggered.connect(self.run_undo)

        # Auto-fixer
        self.auto_fixer = AutoFixer(self.gui)

    def run_preview(self):
        db = self.gui.current_db
        prefs = get_prefs(db)

        # Get preview of what would change
        changes = preview_duplicates(db, same_author_only=prefs['same_author_only'])
        if not changes:
            info_dialog(self.gui, 'Smart Title Fixer', 'No duplicate titles found.', show=True)
            return

        # Show preview dialog
        dlg = PreviewDialog(self.gui, changes)
        if dlg.exec_():
            batch_id = start_new_batch()
            fixed_count = fix_duplicates(
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
        db = self.gui.current_db
        restored = undo_last_run(db)
        info_dialog(
            self.gui,
            'Undo Smart Title Fixer',
            f'Restored {restored} titles from last run.',
            show=True
        )


class PreviewDialog(MessageBox):
    def __init__(self, parent, changes):
        super().__init__(
            parent,
            'Smart Title Fixer Preview',
            'The following titles will be changed:',
            show_copy_button=False
        )
        text = '\n'.join(
            f'ID {book_id}: "{old}" -> "{new}"'
            for book_id, old, new in changes
        )
        self.textbox = QTextEdit(self)
        self.textbox.setReadOnly(True)
        self.textbox.setPlainText(text)
        self.layout().addWidget(self.textbox)


class ConfigWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = parent.gui.current_db if hasattr(parent, 'gui') else None
        self.prefs = get_prefs(self.db)

        layout = QVBoxLayout(self)

        self.same_author_only = QCheckBox('Only treat duplicates with the same author as duplicates')
        self.same_author_only.setChecked(self.prefs['same_author_only'])
        layout.addWidget(self.same_author_only)

        layout.addWidget(QLabel('Regex cleanup for filenames (applied before title-casing):'))
        self.regex_pattern = QLineEdit(self.prefs['regex_pattern'])
        layout.addWidget(self.regex_pattern)

        layout.addWidget(QLabel('Regex replacement:'))
        self.regex_replacement = QLineEdit(self.prefs['regex_replacement'])
        layout.addWidget(self.regex_replacement)

        layout.addStretch(1)

    def save_settings(self):
        self.prefs['same_author_only'] = self.same_author_only.isChecked()
        self.prefs['regex_pattern'] = self.regex_pattern.text()
        self.prefs['regex_replacement'] = self.regex_replacement.text()
        set_prefs(self.db, self.prefs)


def get_config_widget():
    # calibre passes the main window as parent when calling config_widget()
    from calibre.gui2 import main
    return ConfigWidget(main())
