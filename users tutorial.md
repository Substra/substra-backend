# Users by org


## Need
We have the will to manage users by organization.

Node to node authentication i.e worker to backend instances communication are not impacted and use the current Basic Auth implementation.

We want to be able to register them from an administration point of view.

Each user can login himself.

## Authentications

There are two main authentication available running in parallel:
- Secure JWT Authentication
- Session Authentication

Each authentication process owns its login view which run against the same database and one and only user management.


#### Secure JWT Authentication
The first one `Secure JWT Authentication` is mainly used for web single one page application as our susbtrafront project.
We use a Secure JWT Authentication and not a simple JWT Authentication for being sure we are free of XSS and/or CORS attacks.
More reading here: 
- https://medium.com/@jcbaey/authentication-in-spa-reactjs-and-vuejs-the-right-way-e4a9ac5cd9a3
- https://medium.com/lightrail/getting-token-authentication-right-in-a-stateless-single-page-application-57d0c6474e3
It can also be used by SDK and CLI projects such as our substra-sdk and substra-cli.

#### Session Authentication
The second one `Session Authentication` is a classic for server rendered pages, useful for our web browsable API available via django rest framework api.
It can also be used by SDK and CLI projects but is a little bit more difficult to implement, as two requests need to be done for logging in correctly.

## Testing

Three projects are impacted by this change:
- substrabac
- substrafront
- substra-cli

Each has a branch entitled `users`.

Launch a `substra-network` network with two organizations (classic).

### substra-cli

1. Go to the `users` branch.

That's all :)

#### Test

1. Install new version `pip install .`
2. Create configuration:
```bash
$> substra config --profile user -k -v 0.0 -u foo -p barbar10 http://owkin.substrabac:8000
```
3. Login
```bash
$> substra login --profile user
```
4. Request
```
$> substra list objective --profile user
KEY                                                                 NAME                                    METRICS                 
1cdafbb018dd195690111d74916b76c96892d897ec3587c814f287946db446c3    Skin Lesion Classification Objective    macro-average recall    
3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71    Skin Lesion Classification Objective    macro-average recall 
```

### substrabac

1. Go to the `users` branch.
2. Install new substra-cli with `pip install -e ../substra-cli`
3. Generate nodes username/password:
```bash
$> python ./substrabac/node/generate_nodes.py
```
4. Build docker images:
```bash
$> sh build-docker-images.sh
```
5. Run images:
```bash
$> python start.py -d --no-backup
```
6. Run populate.py

For each backend it will create by default an user with username `foo` and password `barbar10`.
The `populate.py` script uses these credentials for logging in.


#### Test:

1. Go to `http://owkin.substrabac:8000`, be sure to have the `mod_header` running for not having the version error message.
2. Click on the login link on the top right of the page.
3. Login
4. Enjoy


### susbtrafront

1. Go to the `users` branch.
2. Rebuild the images and run them:
```bash
$> docker-compose up -d --force-recreate --build 
```

#### Test:

1. Go to `http://owkin.substrabac:3000`, be sure to have deactivated the `mod_header` version control.
2. Login
4. Enjoy
