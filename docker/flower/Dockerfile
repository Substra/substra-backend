FROM python:3.6

ARG USER_ID=1001
ARG GROUP_ID=1001

RUN mkdir -p /usr/src/app && chown -R ${USER_ID}:${GROUP_ID} /usr/src/app
WORKDIR /usr/src/app

COPY --chown=${USER_ID}:${GROUP_ID} ./backend/requirements.txt /usr/src/app/.

RUN pip3 install -r requirements.txt
RUN pip3 install flower

COPY --chown=${USER_ID}:${GROUP_ID} ./backend/libs /usr/src/app/libs
COPY --chown=${USER_ID}:${GROUP_ID} ./backend/substrapp /usr/src/app/substrapp
COPY --chown=${USER_ID}:${GROUP_ID} ./backend/backend /usr/src/app/backend
COPY --chown=${USER_ID}:${GROUP_ID} ./backend/node /usr/src/app/node
COPY --chown=${USER_ID}:${GROUP_ID} ./backend/users /usr/src/app/users

USER ${USER_ID}:${GROUP_ID}
