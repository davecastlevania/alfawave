import datetime
import logging
import sys

import cryptography.exceptions
import requests
import requests_http_message_signatures
from django import forms
from django.utils import timezone
from django.utils.http import parse_http_date

from . import exceptions, utils

if sys.version_info < (3, 9):
    from backports.zoneinfo import ZoneInfo
else:
    from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

#  the request Date should be between now - 30s and now + 30s
DATE_HEADER_VALID_FOR = 30


def verify_date(raw_date):
    if not raw_date:
        raise forms.ValidationError("Missing date header")

    try:
        ts = parse_http_date(raw_date)
    except ValueError as e:
        raise forms.ValidationError(str(e))
    dt = datetime.datetime.utcfromtimestamp(ts)
    dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    delta = datetime.timedelta(seconds=DATE_HEADER_VALID_FOR)
    now = timezone.now()
    if dt < now - delta or dt > now + delta:
        logger.debug(
            f"Request Date {raw_date} is too too far in the future or in the past"
        )
        raise forms.ValidationError(
            "Request Date is too far in the future or in the past"
        )

    return dt


def verify(request, public_key):
    date = request.headers.get("Date")
    logger.debug(
        "Verifying request with date %s and headers %s", date, str(request.headers)
    )
    verify_date(date)
    try:
        return requests_http_message_signatures.HTTPSignatureHeaderAuth.verify(
            request, key_resolver=lambda **kwargs: public_key
        )
    except cryptography.exceptions.InvalidSignature:
        logger.warning(
            "Could not verify request with date %s and headers %s",
            date,
            str(request.headers),
        )
        raise


def verify_django(django_request, public_key):
    """
    Given a django WSGI request, create an underlying requests.PreparedRequest
    instance we can verify
    """
    headers = utils.clean_wsgi_headers(django_request.META)
    for h, v in list(headers.items()):
        # we include lower-cased version of the headers for compatibility
        # with requests_http_message_signatures
        headers[h.lower()] = v
    try:
        signature = headers["Signature"]
    except KeyError:
        raise exceptions.MissingSignature
    url = f"http://noop{django_request.path}"
    query = django_request.META["QUERY_STRING"]
    if query:
        url += f"?{query}"
    signature_headers = signature.split('headers="')[1].split('",')[0]
    expected = signature_headers.split(" ")
    logger.debug("Signature expected headers: %s", expected)
    for header in expected:
        if header == "(request-target)":
            # this one represent the request body, so not an actual HTTP header
            continue
        try:
            headers[header]
        except KeyError:
            logger.debug("Missing header: %s", header)
    request = requests.Request(
        method=django_request.method, url=url, data=django_request.body, headers=headers
    )
    for h in request.headers.keys():
        v = request.headers[h]
        if v:
            request.headers[h] = str(v)
    request.prepare()
    return verify(request, public_key)


def get_auth(private_key, private_key_id):
    return requests_http_message_signatures.HTTPSignatureHeaderAuth(
        headers=["(request-target)", "user-agent", "host", "date"],
        algorithm="rsa-sha256",
        key=private_key.encode("utf-8"),
        key_id=private_key_id,
    )
