import json
import logging
from json.decoder import JSONDecodeError

from django.core.cache import caches
from django.utils.functional import LazyObject

import requests
from graphene_django.views import GraphQLView

from .draftjs_helpers import create_exporter


# FIXME: Configure logging in settings.py
logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


LATEST_REVISION_FIELD = "latestRevision"
COMMENTS_ON_FIELD = "commentsOn"

IMGPROXY_ENDPOINT = "https://sv-imgproxy-demo.herokuapp.com"
CHS_HOMER_COMMENTARY_ENDPOINT = "https://homer.chs.harvard.edu/api/comments/"
CHS_WP_CONTENT_ENDPOINT = "https://classical-inquiries.chs.harvard.edu/wp-content"


class DraftJSExporter(LazyObject):
    def _setup(self):
        self._wrapped = create_exporter()  # pragma: no cover


EXPORTER = DraftJSExporter()


class GraphQLViewLazy(LazyObject):
    def _setup(self):
        self._wrapped = GraphQLView({})  # pragma: no cover


GRAPHQL_VIEW_INSTANCE = GraphQLViewLazy()


def get_proxy_image_url(src):
    """
    Works around CORS issues
    """
    # FIXME: Finish imgproxy app setup
    # https://docs.imgproxy.net/configuration
    return f"{IMGPROXY_ENDPOINT}/insecure/plain/{src}"


def get_urn(request):
    try:
        data = json.loads(request.body)
    except JSONDecodeError:
        data = {}

    query = GRAPHQL_VIEW_INSTANCE.get_graphql_params(request, data)[0]
    doc = GRAPHQL_VIEW_INSTANCE.backend.document_from_string({}, query)
    return (
        doc.document_ast.definitions[0]
        .selection_set.selections[0]
        .arguments[0]
        .value.value
    )


def query_nac(urn):
    # TODO: implement pagination on requests
    # FIXME: Send user agent
    r = requests.get(f"{CHS_HOMER_COMMENTARY_ENDPOINT}?urn_search={urn}")
    return r.json()["results"]


def prepare_payload(results):
    """
    1) Query to CHS API
    2) Render content from Draft.js, proxy wp-content images
    3) Cache results
    4) Serve from cache to avoid re-hitting the NAC upstream
    """
    extracted = []
    for result in results:
        latest_revision = result["revisions"][0]
        try:
            content_state = json.loads(latest_revision["text"])
        except JSONDecodeError:
            content = latest_revision["text"]
        else:
            for k, v in content_state["entityMap"].items():
                if v["type"] == "IMAGE":
                    v["data"]["src"] = get_proxy_image_url(v["data"]["src"])
            content = EXPORTER.render(content_state)

        content = content.replace(
            'src="{CHS_WP_CONTENT_ENDPOINT}',
            f'src="https://{IMGPROXY_ENDPOINT}/insecure/plain/https://classical-inquiries.chs.harvard.edu/wp-content',
        )

        extracted.append(
            {
                "_id": result["id"],
                LATEST_REVISION_FIELD: {
                    "title": latest_revision["title"],
                    "text": content,
                },
                "commenters": [
                    {
                        "_id": c["username"],
                        "name": " ".join([c["first_name"], c["last_name"]]),
                    }
                    for c in result["commenters"]
                ],
            }
        )

    return {"data": {COMMENTS_ON_FIELD: extracted}}


def proxy_query(request):
    logger.info(f"Proxying request to {CHS_HOMER_COMMENTARY_ENDPOINT}")
    cache = caches["nac_proxy"]
    urn = get_urn(request)
    key = urn
    data = cache.get(key)
    if not data:
        results = query_nac(urn)
        data = prepare_payload(results)
        cache.set(key, data, None)
    else:
        logger.info(f"Retrieved from cache: {urn}")
    return data
