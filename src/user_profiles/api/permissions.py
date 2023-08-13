from ninja import Router
from user_profiles.models import UserProfile
from user_profiles.schema import UserProfileSchema
from utilities.errors import ErrorOut, error404
from django.contrib.auth.models import Group


router = Router()


@router.patch(
    'assign_seller/{user_profile_id}',
    response={
        200: UserProfileSchema,
        403: None,
        404: ErrorOut
    }
)
def assign_seller(request, user_profile_id: int):
    if not request.user.has_perm('user_profiles.assign_seller'):
        return 403, None
    user_profile_query = UserProfile.objects.filter(pk=user_profile_id)
    if user_profile_query.exists():
        user_profile = user_profile_query[0]
        user_profile.groups.add(Group.objects.get(name='Seller'))
        return 200, user_profile
    else:
        return 404, error404('id', 'User Profile')['id']


@router.patch(
    'assign_admin/{user_profile_id}',
    response={
        200: UserProfileSchema,
        403: None,
        404: ErrorOut
    }
)
def assign_admin(request, user_profile_id: int):
    if not request.user.has_perm('user_profiles.assign_admin'):
        return 403, None
    user_profile_query = UserProfile.objects.filter(pk=user_profile_id)
    if user_profile_query.exists():
        user_profile = user_profile_query[0]
        user_profile.groups.add(Group.objects.get(name='Admin'))
        return 200, user_profile
    else:
        return 404, error404('id', 'User Profile')['id']


@router.patch(
    'remove_seller/{user_profile_id}',
    response={
        204: None,
        403: None,
        404: ErrorOut
    }
)
def remove_seller(request, user_profile_id: int):
    if not request.user.has_perm('user_profiles.assign_seller'):
        return 403, None
    user_profile_query = UserProfile.objects.filter(pk=user_profile_id)
    if user_profile_query.exists():
        user_profile = user_profile_query[0]
        user_profile.groups.remove(Group.objects.get(name='Seller'))
        return 204, None
    else:
        return 404, error404('id', 'User Profile')['id']


@router.patch(
    'remove_admin/{user_profile_id}',
    response={
        204: None,
        403: None,
        404: ErrorOut
    }
)
def remove_admin(request, user_profile_id: int):
    if not request.user.has_perm('user_profiles.assign_admin'):
        return 403, None
    user_profile_query = UserProfile.objects.filter(pk=user_profile_id)
    if user_profile_query.exists():
        user_profile = user_profile_query[0]
        user_profile.groups.remove(Group.objects.get(name='Admin'))
        return 204, None
    else:
        return 404, error404('id', 'User Profile')['id']
