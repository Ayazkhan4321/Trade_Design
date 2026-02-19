# Compatibility shim: re-export UserManagementService from the Left_panel implementation
# This allows imports like `from accounts.services.user_management import UserManagementService`
# to work across the project without changing existing import locations.

try:
    from Left_panel.accounts.services.user_management.service import UserManagementService  # type: ignore
except Exception:
    # Fallback import when running from different working directories
    try:
        from Left_panel.accounts.services.user_management.service import UserManagementService  # type: ignore
    except Exception:
        # If both fails, expose a placeholder that raises on use to make errors explicit
        class UserManagementService:  # type: ignore
            def __init__(self, *args, **kwargs):
                raise RuntimeError("UserManagementService shim could not import real implementation")

__all__ = ["UserManagementService"]
