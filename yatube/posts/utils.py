from django.core.paginator import Paginator

from .consts import LIMIT_POSTS


def get_page_context(request, queryset):
    paginator = Paginator(queryset, LIMIT_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
