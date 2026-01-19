# ==============================================================================
# FILE: __init__.py
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


# ==============================================================================
# FILE: plugin-import-name-smart_title_fixer.txt
# ==============================================================================
# Just create this file with this content (or leave empty):
smart_title_fixer


# ==============================================================================
# FILE: action.py
# ==============================================================================
from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import info_dialog, get_icons
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


# ==============================================================================
# FILE: auto.py
# ==============================================================================
class AutoFixer:
    """Automatically fix titles on import"""
    
    def __init__(self, gui):
        self.gui = gui
        
        # FIXED: Don't modify iactions during initialization!
        # Just store reference and connect to signal
        
        # Connect to library changed signal
        if hasattr(gui, 'library_view') and hasattr(gui.library_view, 'model'):
            try:
                # Use QTimer to delay connection until after initialization
                from PyQt5.Qt import QTimer
                QTimer.singleShot(100, lambda: self._connect_signal())
            except Exception as e:
                print(f'Could not schedule signal connection: {e}')
    
    def _connect_signal(self):
        """Connect to books_added signal after Calibre finishes initializing"""
        try:
            if hasattr(self.gui, 'library_view') and hasattr(self.gui.library_view, 'model'):
                self.gui.library_view.model().books_added.connect(self.books_added)
        except Exception as e:
            print(f'Could not connect to books_added signal: {e}')

    def books_added(self, book_ids):
        """Called when new books are added to library"""
        # Lazy import to avoid circular dependencies
        from calibre_plugins.smart_title_fixer import utils
        
        db = self.gui.current_db
        prefs = utils.get_prefs(db)
        
        if not prefs.get('auto_on_import', False):
            return

        batch_id = utils.start_new_batch()
        for book_id in book_ids:
            try:
                utils.fix_single_book(db, book_id, batch_id=batch_id, prefs=prefs)
            except Exception as e:
                print(f'Error fixing book {book_id}: {e}')


# ==============================================================================
# FILE: utils.py
# ==============================================================================
import os
import re
from datetime import datetime
import uuid
from calibre.utils.config import JSONConfig

# Use Calibre's config directory
LOG_PATH = os.path.join(
    os.path.expanduser('~/.config/calibre'),
    'smart_title_fixer.log'
)
PREFS_KEY = 'plugins/smart_title_fixer'

DEFAULT_PREFS = {
    'same_author_only': False,
    'regex_pattern': '',
    'regex_replacement': '',
    'auto_on_import': False,
}

def get_prefs(db=None):
    """Get plugin preferences"""
    cfg = JSONConfig(PREFS_KEY)
    prefs = {}
    for k, v in DEFAULT_PREFS.items():
        prefs[k] = cfg.get(k, v)
    return prefs

def set_prefs(db, prefs):
    """Save plugin preferences"""
    cfg = JSONConfig(PREFS_KEY)
    for k, v in prefs.items():
        cfg[k] = v

def start_new_batch():
    """Generate unique batch ID for logging"""
    return str(uuid.uuid4())

def apply_regex_cleanup(name, prefs):
    """Apply user-defined regex to filename"""
    pattern = prefs.get('regex_pattern', '').strip()
    repl = prefs.get('regex_replacement', '')
    
    if pattern:
        try:
            name = re.sub(pattern, repl, name)
        except re.error as e:
            print(f'Regex error: {e}')
    return name

def clean_filename(name, prefs):
    """Convert filename to clean title"""
    # Remove extension
    base = os.path.splitext(name)[0]
    
    # Apply custom regex
    base = apply_regex_cleanup(base, prefs)
    
    # Replace underscores with spaces
    base = base.replace('_', ' ')
    
    # Collapse multiple spaces
    base = re.sub(r'\s+', ' ', base)
    
    # Title case and trim
    return base.strip().title()

def get_filename_for_book(db, book_id):
    """Get the filename of the first format for a book"""
    try:
        fmts = db.formats(book_id, index_is_id=True)
        if not fmts:
            return None
        
        fmt = fmts.split(',')[0].strip()
        path = db.format_abspath(book_id, fmt, index_is_id=True)
        
        if not path or not os.path.exists(path):
            return None
        
        return os.path.basename(path)
    except Exception as e:
        print(f'Error getting filename for book {book_id}: {e}')
        return None

def log_change(batch_id, book_id, old_title, new_title):
    """Log a title change for undo capability"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'{ts}|{batch_id}|{book_id}|{old_title}|{new_title}\n'
    
    try:
        # Ensure directory exists
        log_dir = os.path.dirname(LOG_PATH)
        os.makedirs(log_dir, exist_ok=True)
        
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception as e:
        print(f'Error writing log: {e}')

def fix_single_book(db, book_id, batch_id=None, prefs=None):
    """Fix a single book's title based on filename"""
    if prefs is None:
        prefs = get_prefs(db)

    filename = get_filename_for_book(db, book_id)
    if not filename:
        return False

    new_title = clean_filename(filename, prefs)
    mi = db.get_metadata(book_id, index_is_id=True)
    old_title = mi.title or ''

    if old_title == new_title:
        return False

    mi.title = new_title
    db.set_metadata(book_id, mi, commit=True)

    if batch_id:
        log_change(batch_id, book_id, old_title, new_title)

    return True

def build_key(mi, prefs):
    """Build a key for identifying duplicates"""
    title_key = (mi.title or '').strip().lower()
    
    if prefs.get('same_author_only', False):
        authors = ', '.join(mi.authors or []).strip().lower()
        return (title_key, authors)
    
    return title_key

def preview_duplicates(db, same_author_only=False):
    """Preview what changes would be made"""
    prefs = get_prefs(db)
    prefs['same_author_only'] = same_author_only
    
    # FIXED: Use db.all_ids() not db.all_book_ids()
    all_ids = db.all_ids()
    key_map = {}

    for book_id in all_ids:
        mi = db.get_metadata(book_id, index_is_id=True)
        key = build_key(mi, prefs)
        key_map.setdefault(key, []).append(book_id)

    changes = []
    for key, ids in key_map.items():
        if len(ids) > 1:
            for book_id in ids:
                filename = get_filename_for_book(db, book_id)
                if not filename:
                    continue
                
                mi = db.get_metadata(book_id, index_is_id=True)
                old_title = mi.title or ''
                new_title = clean_filename(filename, prefs)
                
                if old_title != new_title:
                    changes.append((book_id, old_title, new_title))
    
    return changes

def fix_duplicates(db, same_author_only=False, batch_id=None):
    """Fix all duplicate titles"""
    prefs = get_prefs(db)
    prefs['same_author_only'] = same_author_only

    # FIXED: Use db.all_ids() not db.all_book_ids()
    all_ids = db.all_ids()
    key_map = {}

    for book_id in all_ids:
        mi = db.get_metadata(book_id, index_is_id=True)
        key = build_key(mi, prefs)
        key_map.setdefault(key, []).append(book_id)

    changed = 0
    for key, ids in key_map.items():
        if len(ids) > 1:
            for book_id in ids:
                if fix_single_book(db, book_id, batch_id=batch_id, prefs=prefs):
                    changed += 1

    return changed

def undo_last_run(db):
    """Undo the last batch of changes"""
    if not os.path.exists(LOG_PATH):
        return 0

    try:
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f'Error reading log: {e}')
        return 0

    if not lines:
        return 0

    # Find last batch ID
    last_batch_id = None
    for line in reversed(lines):
        parts = line.strip().split('|')
        if len(parts) >= 4:
            last_batch_id = parts[1].strip()
            break

    if not last_batch_id:
        return 0

    # Restore titles from last batch
    restored = 0
    new_log = []

    for line in lines:
        parts = line.strip().split('|')
        if len(parts) < 4:
            new_log.append(line)
            continue

        batch_id = parts[1].strip()
        
        if batch_id == last_batch_id:
            try:
                book_id = int(parts[2].strip())
                old_title = parts[3].strip()
                
                mi = db.get_metadata(book_id, index_is_id=True)
                mi.title = old_title
                db.set_metadata(book_id, mi, commit=True)
                restored += 1
            except Exception as e:
                print(f'Error restoring book: {e}')
                new_log.append(line)
        else:
            new_log.append(line)

    # Rewrite log without last batch
    try:
        with open(LOG_PATH, 'w', encoding='utf-8') as f:
            f.writelines(new_log)
    except Exception as e:
        print(f'Error writing log: {e}')

    return restored
