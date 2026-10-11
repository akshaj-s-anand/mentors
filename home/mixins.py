from django.utils.cache import patch_vary_headers


class AjaxListMixin:
    """
    For list views that load more cards as the visitor scrolls.

    - A request from the page's own JavaScript (X-Requested-With: XMLHttpRequest)
      renders only `partial_template_name` for that one page: script.js appends
      its cards to the grid.
    - A normal request for ?page=N renders the whole page with pages 1..N, so a
      reload, a shared link or the Back button shows everything scrolled so far.
    """

    partial_template_name = None
    paginate_by = 12

    def is_ajax(self):
        return self.request.headers.get('x-requested-with') == 'XMLHttpRequest'

    def get_template_names(self):
        if self.is_ajax() and self.partial_template_name:
            return [self.partial_template_name]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context.get('page_obj')

        if page_obj is not None and page_obj.number > 1 and not self.is_ajax():
            items = self.object_list[:page_obj.end_index()]
            context['object_list'] = items
            context[self.get_context_object_name(self.object_list)] = items

        # keep the active filters in the "load more" link
        query = self.request.GET.copy()
        query.pop('page', None)
        context['filter_query'] = query.urlencode()
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        # same URL, two representations: stop caches serving the fragment as a full page
        patch_vary_headers(response, ['X-Requested-With'])
        return response
