
# ==============================================================================
# FILE: auto.pyv6k now claude clamims the automenu loader is corrupting the calibre startup of the menu bar and the fix is to wait 100ms????
# and one fix is to skip over auto for now
# ==============================================================================
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

