FROM python:3.9 AS build
WORKDIR /opt/scaife-stack/src/
RUN pip install --disable-pip-version-check --upgrade pip setuptools wheel virtualenv
ENV PATH="/opt/scaife-stack/bin:${PATH}" VIRTUAL_ENV="/opt/scaife-stack"
COPY requirements.txt requirements-dev.txt /opt/scaife-stack/src/
RUN set -x \
    && virtualenv /opt/scaife-stack \
    && pip install -r requirements-dev.txt

FROM python:3.9
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt/scaife-stack/src/ \
    PATH="/opt/scaife-stack/bin:${PATH}" \
    VIRTUAL_ENV="/opt/scaife-stack"

WORKDIR /opt/scaife-stack/src/
COPY --from=build /opt/scaife-stack/ /opt/scaife-stack/
