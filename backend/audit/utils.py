from .models import AuditLog
from django.utils import timezone

def log_action(request, action, model_name, object_id=None, object_repr="", changes=None):
    """Fonction utilitaire pour enregistrer une action dans les logs"""
    try:
        user = request.user if request.user.is_authenticated else None
        username = request.user.username if request.user.is_authenticated else "Anonymous"
        
        AuditLog.objects.create(
            user=user,
            username=username,
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes or {},
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:200],
            timestamp=timezone.now()
        )
    except Exception as e:
        print(f"Erreur log audit: {e}")