from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow users with 'admin' role to access the API.
    Based on the specification requirement that only admin users can access the API.
    """
    
    def has_permission(self, request, view):
        """
        Return True if permission is granted, False otherwise.
        Only authenticated users with 'admin' role are allowed.
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # User must have 'admin' role
        return request.user.role == 'admin'
    
    def has_object_permission(self, request, view, obj):
        """
        Return True if permission is granted for the specific object.
        """
        # Same logic for object-level permissions
        return self.has_permission(request, view)


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access to any authenticated user,
    but only allow write permissions to users with 'admin' role.
    """
    
    def has_permission(self, request, view):
        """
        Return True if permission is granted.
        Read permissions for any authenticated user,
        Write permissions only for admin users.
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admin users
        return request.user.role == 'admin'
    
    def has_object_permission(self, request, view, obj):
        """
        Return True if permission is granted for the specific object.
        """
        return self.has_permission(request, view)
