from djangorestframework_camel_case.render import CamelCaseJSONRenderer


class ApiJSONRenderer(CamelCaseJSONRenderer):
    """
    Wrap all successful JSON responses into:
    { "code": 200, "message": "Success", "data": <original_data> }

    - Keeps camelCase output (inherits CamelCaseJSONRenderer)
    - Avoids double-wrapping if response already has code/message/data
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        # If data is already wrapped, keep it as-is
        if isinstance(data, dict) and {"code", "message", "data"} <= set(data.keys()):
            wrapped = data
        else:
            status_code = getattr(response, "status_code", 200) if response else 200
            # Only wrap 2xx responses here; errors are handled by custom exception handler
            if 200 <= status_code < 300:
                wrapped = {"code": 200, "message": "Success", "data": data}
            else:
                wrapped = data

        return super().render(wrapped, accepted_media_type, renderer_context)
