from calibre_plugins.smart_title_fixer.utils import fix_single_book, start_new_batch, get_prefs

class AutoFixer:
    def __init__(self, gui):
        self.gui = gui
        gui.iactions.append(self)

    def books_added(self, book_ids):
        db = self.gui.current_db
        prefs = get_prefs(db)
        if not prefs['auto_on_import']:
            return

        batch_id = start_new_batch()
        for book_id in book_ids:
            fix_single_book(db, book_id, batch_id=batch_id, prefs=prefs)

