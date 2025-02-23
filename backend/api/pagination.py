from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList


class FoodgramRecipeUserPagination(PageNumberPagination):
    """Custom paginator for overriding the number of pages."""

    def get_page_size(self, request: Request) -> int:
        """Retrieves the page size from the 'limit' query parameter.

        Args:
            request (Request): The incoming request object.

        Returns:
            int: The page size specified by the 'limit' parameter.
        """

        return request.query_params.get('limit', self.page_size)

    def get_paginated_response(self, data: ReturnList) -> Response:
        """Generates a custom paginated response.

        Args:
            data: The paginated data.

        Returns:
            Response: The response containing pagination metadata and results.
        """

        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
