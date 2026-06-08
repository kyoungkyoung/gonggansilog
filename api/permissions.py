from rest_framework import permissions


class IsContractParty(permissions.BasePermission):
    """계약 당사자(임대인 또는 임차인)만 접근 가능"""

    def has_object_permission(self, request, view, obj):
        contract = getattr(obj, 'contract', obj)
        return contract.tenant == request.user or contract.landlord == request.user
