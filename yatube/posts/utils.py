from django.core.paginator import Paginator

LIMIT = 10


def get_page_context(request, queryset):
    paginator = Paginator(queryset, LIMIT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
