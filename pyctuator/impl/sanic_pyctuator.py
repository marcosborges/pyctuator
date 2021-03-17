import json
from collections import defaultdict
from datetime import datetime, date
from http import HTTPStatus
from typing import Dict, Tuple, Any, Mapping, List

from sanic import Sanic, Blueprint, response, request
from werkzeug.datastructures import Headers

from pyctuator.httptrace import TraceRecord, TraceRequest, TraceResponse
from pyctuator.impl import SBA_V2_CONTENT_TYPE
from pyctuator.impl.pyctuator_impl import PyctuatorImpl
from pyctuator.impl.pyctuator_router import PyctuatorRouter


#class CustomJSONEncoder(JSONEncoder):
#    """ Override Sanick's JSON encoding of datetime to assure ISO format is used.
#
#    By default, when Sanick is rendering a response to JSON, it is formatting datetime, date and time according to
#    RFC-822 which is different from the ISO format used by SBA.
#
#    This encoder overrides the default datetime encoding and is only used by the Pyctuator blueprint so it shouldn't
#    interfere with whatever encoding users are using.
#
#    See https://stackoverflow.com/questions/43663552/keep-a-datetime-date-in-yyyy-mm-dd-format-when-using-Sanicks-json
#    """
#
#    # pylint: disable=method-hidden
#    def default(self, o: Any) -> Any:
#        try:
#            if isinstance(o, (datetime, date)):
#                return o.isoformat()
#            iterable = iter(o)
#        except TypeError:
#            pass
#        else:
#            return list(iterable)
#        return JSONEncoder.default(self, o)


class SanicPyctuator(PyctuatorRouter):

    # pylint: disable=too-many-locals, unused-variable
    def __init__(
            self,
            app: Sanic,
            pyctuator_impl: PyctuatorImpl

    ) -> None:
        super().__init__(app, pyctuator_impl)

        path_prefix: str = pyctuator_impl.pyctuator_endpoint_path_prefix
        sanic_blueprint: Blueprint = Blueprint("sanic_blueprint", "pyctuator", )
#       sanic_blueprint.json_encoder = CustomJSONEncoder

#        @app.before_request
#        def intercept_requests_and_responses() -> None:
#            request_time = datetime.now()
#
#            @after_this_request
#            def after_response(response: Response) -> Response:
#                response_time = datetime.now()
#
#                # Set the SBA-V2 content type for responses from Pyctuator
#                if request.path.startswith(self.pyctuator_impl.pyctuator_endpoint_path_prefix):
#                    response.headers["Content-Type"] = SBA_V2_CONTENT_TYPE
#
#                # Record the request and response
#                self.record_request_and_response(response, request_time, response_time)
#                return response

        @sanic_blueprint.route("/")
        def get_endpoints() -> Any:
            return response.json(self.get_endpoints_data())

        @sanic_blueprint.route("/env")
        def get_environment() -> Any:
            return response.json(pyctuator_impl.get_environment())

        @sanic_blueprint.route("/info")
        def get_info() -> Any:
            return response.json(pyctuator_impl.app_info)

        @sanic_blueprint.route("/health")
        def get_health() -> Any:
            return response.json(pyctuator_impl.get_health())

        @sanic_blueprint.route("/metrics")
        def get_metric_names() -> Any:
            return response.json(pyctuator_impl.get_metric_names())

        @sanic_blueprint.route("/metrics/<metric_name>")
        def get_metric_measurement(metric_name: str) -> Any:
            return response.json(pyctuator_impl.get_metric_measurement(metric_name))

        # Retrieving All Loggers
        @sanic_blueprint.route("/loggers")
        def get_loggers() -> Any:
            return response.json(pyctuator_impl.logging.get_loggers())

        #@sanic_blueprint.route("/loggers/<logger_name>", methods=['POST'])
        #def set_logger_level(logger_name: str) -> Dict:
        #    request_dict = json.loads(request.data)
        #    pyctuator_impl.logging.set_logger_level(logger_name, request_dict.get("configuredLevel", None))
        #    return {}

        @sanic_blueprint.route("/loggers/<logger_name>")
        def get_logger(logger_name: str) -> Any:
            return response.json(pyctuator_impl.logging.get_logger(logger_name))

        @sanic_blueprint.route("/threaddump")
        @sanic_blueprint.route("/dump")
        def get_thread_dump() -> Any:
            return response.json(pyctuator_impl.get_thread_dump())

#        @sanic_blueprint.route("/logfile")
#        def get_logfile() -> Tuple[response, int]:
#            range_header: str = request.headers.environ.get('HTTP_RANGE')
#            if not range_header:
#                response: make_response(pyctuator_impl.logfile.log_messages.get_range())
#                return response, HTTPStatus.OK
#
#            str_res, start, end = pyctuator_impl.logfile.get_logfile(range_header)
#
#            resp: response = make_response(str_res)
#            resp.headers["Content-Type"] = "text/html; charset=UTF-8"
#            resp.headers["Accept-Ranges"] = "bytes"
#            resp.headers["Content-Range"] = f"bytes {start}-{end}/{end}"
#
#            return resp, HTTPStatus.PARTIAL_CONTENT

#        @sanic_blueprint.route("/trace")
#        @sanic_blueprint.route("/httptrace")
#        def get_httptrace() -> Any:
#            return response.json(pyctuator_impl.http_tracer.get_httptrace())

        app.blueprint(sanic_blueprint, url_prefix=path_prefix)

    def _create_headers_dictionary_sanic(self, headers: Headers) -> Mapping[str, List[str]]:
        headers_dict: Mapping[str, List[str]] = defaultdict(list)
        for (key, value) in headers.items():
            headers_dict[key].append(value)
        return dict(headers_dict)

#    def record_request_and_response(
#            self,
#            response: response,
#            request_time: datetime,
#            response_time: datetime,
#    ) -> None:
#        new_record = TraceRecord(
#            request_time,
#            None,
#            None,
#            TraceRequest(request.method, str(request.url), self._create_headers_dictionary_sanic(request.headers)),
#            TraceResponse(response.status_code, self._create_headers_dictionary_sanic(response.headers)),
#            int((response_time.timestamp() - request_time.timestamp()) * 1000),
#        )
#        self.pyctuator_impl.http_tracer.add_record(record=new_record)
#