from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response')
        if response and response.status_code >=200 and response.status_code < 300:
            success = True
        else:
            success = False
        result = {
            'success': success,
            'data': data
        }
        return super().render(result, accepted_media_type, renderer_context)

