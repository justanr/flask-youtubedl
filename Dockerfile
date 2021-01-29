FROM python:3.8-slim as BUILD
ENV WHEELHOUSE=/wheelhouse
ENV PIP_WHEEL_DIR=${WHEELHOUSE}
ENV PIP_FIND_LINKS=${WHEELHOUSE}
RUN apt-get update -qy && \
    apt-get install -qyy \
    -o APT::Install-Recommends=False \
    -o APT::Install-Suggests=False \
    gcc \
    build-essential

RUN mkdir ${WHEELHOUSE} && pip install wheel
COPY ./requirements.txt /requirements.txt
RUN pip wheel -r requirements.txt

FROM python:3.8-slim as APP
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1



# build app
COPY --from=BUILD /wheelhouse /wheelhouse
WORKDIR /fytdl
COPY ./requirements.txt .
RUN pip install --no-index -f /wheelhouse -r requirements.txt
COPY ./setup.py .
COPY ./src ./src
RUN pip install --no-index -f /wheehouse -e .

# launch stuff
COPY ./scripts/launch.sh .
ENTRYPOINT ["/fytdl/launch.sh"]
CMD ["celery"]

# user management
#RUN groupadd -g 9999 fytdl && useradd -r -u 9999 -g 9999 fytdl
#RUN mkdir /var/run/fytdl && chown -R /var/run/fytdl && chown -R fytdl .
#USER fytdl

