from ninja import Router
from .models import AuditLog
from django.db.models import Q

router = Router()

@router.get("/logs")
def get_audit_logs(request, action: str = None, model: str = None, search: str = None):
    """Récupérer les logs d'audit avec filtres"""
    if not request.user.is_authenticated:
        return {"error": "Non authentifié"}
    
    if request.user.role != 'admin':
        return {"error": "Permission refusée"}
    
    logs = AuditLog.objects.all()
    
    if action:
        logs = logs.filter(action=action)
    
    if model:
        logs = logs.filter(model_name=model)
    
    if search:
        logs = logs.filter(
            Q(username__icontains=search) |
            Q(object_repr__icontains=search) |
            Q(model_name__icontains=search)
        )
    
    result = []
    for log in logs[:200]:  # Limiter à 200 pour les performances
        result.append({
            "id": log.id,
            "username": log.username,
            "action": log.action,
            "model_name": log.model_name,
            "object_id": log.object_id,
            "object_repr": log.object_repr,
            "changes": log.changes,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp.isoformat(),
        })
    
    return result