# ==============================================================================
# FILE: utils.py ... fix all_id call change
# ==============================================================================
# ==============================================================================
# FILE: utils.py fix menu action method which crashes calibre on startup with corrupted dict
# ==============================================================================
# ==============================================================================
# FILE: utils.py v6k now claude clamims the automenu loader is corrupting the calibre startup of the menu bar and the fix is to wait 100ms????
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
