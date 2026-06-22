from fastapi import Depends, HTTPException, status
from app.models.client_models import Clients
from app.auth.jwt import get_current_user

def require_role(required_role: str):
    def role_checker(current_user: Clients = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return current_user
    return role_checker

require_admin = require_role("admin")
require_manager = require_role("manager")
require_dentist = require_role("dentist")

def require_manager_or_dentist(current_user: Clients = Depends(get_current_user)):
    """Доступно менеджеру, стоматологу и админу"""
    if current_user.role not in ["manager", "dentist", "admin"]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return current_user