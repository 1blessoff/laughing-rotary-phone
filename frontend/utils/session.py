
# GESTIONNAIRE DE SESSION ISOLÉ PAR NAVIGATEUR

class SessionManager:
    """
    Gestionnaire de session Flet compatible Web / Multi-utilisateurs.
    S'appuie sur page.session de Flet pour isoler la mémoire de chaque utilisateur.
    Contient un fallback local si l'objet 'page' n'est pas fourni.
    """

    def __init__(self):
        # Fallback pour le stockage temporaire global si page n'est pas passée
        self._fallback_data = {}

    def get(self, key: str, default=None, page=None):
        """Récupère une valeur dans la session du navigateur de l'utilisateur."""
        if page and hasattr(page, "session"):
            val = page.session.get(key)
            return val if val is not None else default
        return self._fallback_data.get(key, default)

    def set(self, key: str, value, page=None):
        """Stocke une valeur dans la session du navigateur de l'utilisateur."""
        if page and hasattr(page, "session"):
            page.session.set(key, value)
        else:
            self._fallback_data[key] = value

    def remove(self, key: str, page=None):
        """Supprime une clé de la session."""
        if page and hasattr(page, "session"):
            if page.session.contains_key(key):
                page.session.remove(key)
        if key in self._fallback_data:
            del self._fallback_data[key]

    def clear(self, page=None):
        """Efface toute la session de l'utilisateur actuel."""
        if page and hasattr(page, "session"):
            page.session.clear()
        self._fallback_data.clear()


# Instance globale unique à importer dans l'application
session = SessionManager()