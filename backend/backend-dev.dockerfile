FROM python:3.9-alpine AS build
WORKDIR /opt/scaife-stack/src/
RUN apk --no-cache add build-base \
    curl \
    git \
    libxml2-dev \
    libxslt-dev \
    linux-headers \
    && pip install --disable-pip-version-check --upgrade pip setuptools wheel virtualenv
ENV PATH="/opt/scaife-stack/bin:${PATH}" VIRTUAL_ENV="/opt/scaife-stack"
COPY requirements.txt requirements-dev.txt /opt/scaife-stack/src/
RUN set -x \
    && virtualenv /opt/scaife-stack \
    && pip install -r requirements-dev.txt

FROM python:3.9-alpine
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt/scaife-stack/src/ \
    PATH="/opt/scaife-stack/bin:${PATH}" \
    VIRTUAL_ENV="/opt/scaife-stack"

WORKDIR /opt/scaife-stack/src/
COPY --from=build /opt/scaife-stack/ /opt/scaife-stack/

RUN set -x \
    && runDeps="$( \
        scanelf --needed --nobanner --format '%n#p' --recursive /opt/scaife-stack \
            | tr ',' '\n' \
            | sort -u \
            | awk 'system("[ -e /usr/local/lib/" $1 " ]") == 0 { next } { print "so:" $1 }' \
        )" \
    && apk --no-cache add \
        $runDeps \
        curl \
        bash
