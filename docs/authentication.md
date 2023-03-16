# Authentication

The API provide 3 authentication modes.
- Session ID: used by the DRF UI (API browser).
- Bearer token: used by the SDK (substra client).
- JWT cookie: used by the substra frontend.


## Session ID

- URL: `/api-auth/login/`
- Implemented in `backend.urls` [module](../backend/backend/url.py)
- Based on DRF `SessionAuthentication` [scheme](https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication)
  * The session key is stored on the server side (in `django_session` table), alongside an expiration date and an encoded dict of data containing the user ID.
  * The session key is a random string encoded in ASCII format. [Source](https://docs.djangoproject.com/fr/4.1/topics/http/sessions)
  * The server returns a cookie with the session key to the client.

1. Retrieve the login form to download the CSRF cookie and the form token.

```bash
curl \
  --request GET \
  --cookie-jar cookie-session.jar \
  http://substra-backend.org-1.com/api-auth/login/ | grep csrfmiddlewaretoken
<input type="hidden" name="csrfmiddlewaretoken" value="<form_token_value>">

cat cookie-session.jar
#HttpOnly_substra-backend.org-1.com    FALSE    /    FALSE    1696426424    csrftoken    <csrf_token_value>

2. Post the credentials using FORM data (including the form token) with the CSRF token in the header and the CSRF cookie.

```bash
curl \
  --request POST \
  --header 'X-CSRFToken: <csrf_token_value>' \
  --form username='org-1' \
  --form password='p@sswr0d44' \
  --form csrfmiddlewaretoken='<form_token_value>' \
  --cookie cookie-session.jar \
  --cookie-jar cookie-session.jar \
  http://substra-backend.org-1.com/api-auth/login/

cat cookie-session.jar
#HttpOnly_substra-backend.org-1.com    FALSE    /    FALSE    1666187244    sessionid    <session_id_value>
#HttpOnly_substra-backend.org-1.com    FALSE    /    FALSE    1696427244    csrftoken    <csrf_token_value>
```

3. Fetch any asset with the session-id cookie.

```bash
curl \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --cookie cookie-session.jar \
  http://substra-backend.org-1.com/algo/
{"count":0,"next":null,"previous":null,"results":[]}
```

## Bearer token

- URL: `/api-token-auth/`
- Implemented in `backend.views` [module](../backend/backend/views.py)
- Based on DRF `TokenAuthentication` [scheme](https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication)
  * The token is stored on server side (in `authtoken_token` table), alongside a creation date and and the user ID.
  * The token is a random string encoded in hexadecimal format. [Source](https://github.com/encode/django-rest-framework/blob/master/rest_framework/authtoken/models.py)
  * The token should be included in the `Authorization` HTTP header
- The API has a custom layer to handle the token expiration based on its creation date. [Source](../libs/expiry_token_authentication.py)

1. Post the credentials using JSON data to download the authentication token.

```bash
curl \
  --request POST \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --data '{"username":"org-1","password":"p@sswr0d44"}' \
  http://substra-backend.org-1.com/api-token-auth/
{"token":"<auth_token_value>","expires_at":"59841.718064"}
```

2. Fetch any asset with the authentication token in the header.

```bash
curl \
  --header 'Accept: application/json' \
  --header 'Authorization: Token <auth_token_value>' \
  http://substra-backend.org-1.com/algo/
{"count":0,"next":null,"previous":null,"results":[]}
```

### Bearer tokens when already authenticated

- URL: `/api-token-tap/`
- Implemented in `backend.views` [module](../backend/backend/views.py)

Generates bearer tokens for already authenticated users.

This is useful for a frontend client to generate bearer tokens for use in the Python SDK.

## JWT cookie

- URLs: `/me/login/`, `/me/refresh/`
- Implemented in `users.views.authentication` [module](../backend/users/views/authentication.py)
- Based on `rest_framework_simplejwt` [library](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/index.html).
  * Generate a [JWT token](https://jwt.io/introduction)
    - Header: contains the signing algorithm, encoded in Base 64.
    - Payload: contains authentication data (user ID, expiration date) encoded in Base 64.
    - Signature: the header and the payload encrypted with a secret.
- The API has a custom layer to split the JWT token in 3 cookies.
  * A long lifespan cookie which contains the header and the payload.
  * A short lifespan cookie which contains the signature, using HTTP only (not accessible by JS code to prevent from Cross-Site-Scripting / XSS attacks).
  * A short lifespan cookie which contains the refreshing expiration date, using HTTP only.

1. Post the credentials using JSON data to download the cookies.

```bash
curl \
  --request POST \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --data '{"username":"org-1","password":"p@sswr0d44"}' \
  --cookie-jar cookie-jwt.jar \
  http://substra-backend.org-1.com/me/login/
{"token_type":"access","exp":1665061851,"iat":1664975451,"jti":"8f6d98b667024db59dcc55f923db8d22","user_id":1}

cat cookie-jwt.jar
#HttpOnly_.org-1.com    TRUE    /    FALSE    1665580790    refresh           <refresh_value>
#HttpOnly_.org-1.com    TRUE    /    FALSE    0             signature         <signature_value>
.org-1.com              TRUE    /    FALSE    1665062390    header.payload    <header_payload_value>
```

2. Fetch any asset with the refresh and the JWT signature cookies and the JWT header/payload in the header.

```bash
curl \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: JWT <header_payload_value>' \
  --cookie cookie-jwt.jar \
  http://substra-backend.org-1.com/algo/
{"count":0,"next":null,"previous":null,"results":[]}
```

3. Post no data with the refresh cookie to refresh the cookies.

```bash
curl \
  --request POST \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --cookie cookie-jwt.jar \
  --cookie-jar cookie-jwt.jar \
  http://substra-backend.org-1.com/me/refresh/
{"token_type":"access","exp":1665069744,"iat":1664983339,"jti":"a1c7535880a64f6b864673bd6ee8fec0","user_id":1}
```

## OpenID Connect

- URL: `/oidc/authenticate`
- Implemented in:
  - `users.authentication` [module](../backend/users/authentication.py)
  - `users.views.authentication` [module](../backend/users/views/authentication.py)

Reach `/oidc/authenticate` with a browser. A string of redirects will end on `/oidc/callback`, which will set JWT tokens on the client and, if debug mode is on, also log in the user in the session for DRF's API browser.