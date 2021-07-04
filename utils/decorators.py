from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def require_params(require_attrs='query_params', params=None):
    """
    The decorator to check if the request include all necessary parameters
    """
    if not params:
        params = []

    def decorator(view_func):
        """
        Use @wrap to parse the arguments of view_func
        the instance equals to the self in view_func
        """
        @wraps(view_func)
        def _wrapped_view(instance, request, *args, **kwargs):
            data = getattr(request, require_attrs)
            missing_params = [
                param
                for param in params
                if param not in data
            ]
            if missing_params:
                params_str = ', '.join(missing_params)
                return Response({
                    'success': False,
                    'message': 'missing {} in request'.format(params_str),
                }, status=status.HTTP_400_BAD_REQUEST)
            return view_func(instance, request, *args, **kwargs)
        return _wrapped_view
    return decorator

