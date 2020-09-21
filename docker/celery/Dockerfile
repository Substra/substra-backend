FROM python:3.6

ARG USER_ID=1001
ARG GROUP_ID=1001

RUN mkdir -p /usr/src/app && chown -R ${USER_ID}:${GROUP_ID} /usr/src/app
WORKDIR /usr/src/app

COPY ./backend/requirements.txt /usr/src/app/.
RUN chown -R ${USER_ID}:${GROUP_ID} /usr/src/app

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY ./backend/libs /usr/src/app/libs
COPY ./backend/substrapp /usr/src/app/substrapp
COPY ./backend/backend /usr/src/app/backend
COPY ./backend/node /usr/src/app/node
COPY ./backend/users /usr/src/app/users

RUN chown -R ${USER_ID}:${GROUP_ID} /usr/src/app


USER ${USER_ID}:${GROUP_ID}
