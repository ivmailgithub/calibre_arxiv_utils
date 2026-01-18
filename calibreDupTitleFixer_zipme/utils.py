import os
import re
from datetime import datetime
import uuid
from calibre.utils.config import JSONConfig

LOG_PATH = os.path.expanduser('~/calibre_title_fixer.log')
PREFS_KEY = 'plugins_smart_title_fixer'

DEFAULT_PREFS = {
    'same_author_only': False,
    'regex_pattern': '',
    'regex_replacement': '',
    'auto_on_import': False,
}

def get_prefs(db=None):
    # Per-library prefs via JSONConfig
    cfg = JSONConfig(PREFS_KEY)
    for k, v in DEFAULT_PREFS.items():
        if k not in cfg:
            cfg[k] = v
    return dict(cfg)

def set_prefs(db, prefs):
    cfg = JSONConfig(PREFS_KEY)
    for k, v in prefs.items():
        cfg[k] = v

def start_new_batch():
    return str(uuid.uuid4())

def apply_regex_cleanup(name, prefs):
    pattern = prefs.get('regex_pattern') or ''
    repl = prefs.get('regex_replacement') or ''
    if pattern:
        try:
            name = re.sub(pattern, repl, name)
        except re.error:
            pass
    return name

def clean_filename(name, prefs):
    base = os.path.splitext(name)[0]
    base = apply_regex_cleanup(base, prefs)
    base = base.replace('_', ' ')
    base = re.sub(r'\s+', ' ', base)
    return base.strip().title()

def get_filename_for_book(db, book_id):
    fmts = db.formats(book_id)
    if not fmts:
        return None
    fmt = fmts.split(',')[0].strip()
    path = db.format_abspath(book_id, fmt)
    if not path:
        return None
    return os.path.basename(path)

def log_change(batch_id, book_id, old_title, new_title):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'{ts} | {batch_id} | {book_id} | {old_title} | {new_title}\n'
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass

def fix_single_book(db, book_id, batch_id=None, prefs=None):
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
    db.set_metadata(book_id, mi)

    if batch_id:
        log_change(batch_id, book_id, old_title, new_title)

    return True

def build_key(mi, prefs):
    title_key = (mi.title or '').strip().lower()
    if prefs['same_author_only']:
        authors = ', '.join(mi.authors or []).strip().lower()
        return (title_key, authors)
    return title_key

def preview_duplicates(db, same_author_only=False):
    prefs = get_prefs(db)
    prefs['same_author_only'] = same_author_only
    all_ids = list(db.all_book_ids())
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
    prefs = get_prefs(db)
    prefs['same_author_only'] = same_author_only

    all_ids = list(db.all_book_ids())
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
    if not os.path.exists(LOG_PATH):
        return 0

    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return 0

    last_batch_id = None
    for line in reversed(lines):
        parts = line.strip().split('|')
        if len(parts) >= 5:
            last_batch_id = parts[1].strip()
            break

    if not last_batch_id:
        return 0

    restored = 0
    new_log = []

    for line in lines:
        parts = line.strip().split('|')
        if len(parts) < 5:
            new_log.append(line)
            continue

        batch_id = parts[1].strip()
        book_id = int(parts[2].strip())
        old_title = parts[3].strip()

        if batch_id == last_batch_id:
            mi = db.get_metadata(book_id, index_is_id=True)
            mi.title = old_title
            db.set_metadata(book_id, mi)
            restored += 1
        else:
            new_log.append(line)

    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_log)

    return restored
