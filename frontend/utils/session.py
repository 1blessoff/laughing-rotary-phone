# Gestionnaire de session globale

class SessionManager:
    def __init__(self):
        self._data = {}
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def set(self, key, value):
        self._data[key] = value
    
    def clear(self):
        self._data.clear()
    
    def remove(self, key):
        if key in self._data:
            del self._data[key]

# Instance globale unique
session = SessionManager()