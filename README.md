<p align="center">
    <a href="https://www.42berlin.de/" target="_blank">
        <kbd>
            <img src="https://github.com/42Berlin/.github/blob/main/assets/logo-pink.png?raw=true" width="128" alt="42 Berlin logo"/>
        </kbd>
    </a>
</p>

<p align="center">
  <a href="#what-is-this">About</a> &nbsp;|&nbsp; <a href="#key-features">Key Features</a> &nbsp;|&nbsp; <a href="#installation">Installation</a> &nbsp;|&nbsp; <a href="#configuration">Configuration</a> &nbsp;|&nbsp; <a href="#usage">Usage</a> &nbsp;|&nbsp; <a href="#contribute">Contribute</a>
</p>

<p align="center">
  <sub>Created by ???</sub
</p>

<p align="center" style="margin: 0; padding: 0; line-height: 1;">&darr;</p>

<p align="center">
  <sub>Adapted by <a href="https://hive.fi">Hive Helsinki</a> for all the 42 Network (the best 🫶🏻)</sub>
</p>

<p align="center" style="margin: 0; padding: 0; line-height: 1;">&darr;</p>

<p align="center">
  <sub>Re-adapted by <a href="https://42berlin.de">42 Berlin</a> to include new API v3 calls, inspired by <a href="https://github.com/maperrea/api42-wrapper/blob/master/api42/api42.py">42api-wrapper</a> from 19 Belgium 🖤</sub>
</p>


## What is this?
This is a Python script that facilitates making requests to the 42 Network's API. It will do all the hard work such as getting, refreshing, updating tokens and pagination. All you need to do is provide the endpoint from which you want to retrieve data, and this script will take care of the rest.

Example usage:
```python
from api42lib import IntraAPIClient

ic = IntraAPIClient(config_path="./config.yml")

users = ic.pages_threaded("users")
for user in users:
    print(user["login"])

freezes = ic.pages_threaded("freeze/v2/freezes")
for freeze in freezes:
    print(freeze["id"])
```

This is a fork of the original [42API-Lib](https://github.com/hivehelsinki/42api-lib) made by Hive.

You can explore the API Documentation and available endpoints [here](https://api.intra.42.fr/apidoc).

## Key Features
* **API v2 and v3 Support:** The library is compatible with both API v2 and v3 calls, allowing users to continue using v2 routes while also using the new v3 endpoints. You can use any of the following URL formats to make a request:
  ```yaml
  V2:
  - *
  - https://api.intra.42.fr/v2/*
  - /v2/*
  - v2/*

  V3:
  - pace-system/v1/*
  - freeze/v2/*
  - v3/pace-system/v1/*
  - /v3/pace-system/v1/*
  - v3/freeze/v2/*
  - /v3/freeze/v2/*
  - https://pace-system.42.fr/api/v1/*
  - https://freeze.42.fr/api/v2/*
  ```

* **Token Management:** Tokens are managed internally and requested when the `expires_at` date is reached, avoiding the need to make an initial request to check if the token was valid.

* **Singleton:** The library uses a singleton pattern to ensure that only one instance of the `IntraAPIClient` class is created. This avoids the need to pass the instance around in your code and tokens are shared across all instances.

* **Variable config file path**: The class has a `config_file` parameter that allows you to specify a different configuration file. If you don't provide a file path, the library will look for a `config.yml` file in the current directory.

* **Threads**: Re-worked the `pages_threaded` method. Also the number of threads is dynamically calculated based on available CPUs.


## Installation
We recommend using a virtual environment. We use [Poetry](https://python-poetry.org/) for dependency management, but you can use any other package manager you prefer.

Run the following command to install the package with Poetry:
```bash
poetry add api42lib
```

If you prefer to use pip, you can install the package with the following command:
```bash
pip install api42lib
```


## Configuration
You can copy the sample file and edit it with your api credentials:

```bash
cp config.sample.yml config.yml
```

Here is an overview of the config.yml file:
```yaml
intra:
  v2:
    client: ""   # <- insert your v2 app’s UID here
    secret: ""   # <- insert your app’s SECRET here
    uri: "https://api.intra.42.fr/v2/oauth/token"
    endpoint: "https://api.intra.42.fr/v2"
    scopes: "public"
  v3:
    client: ""   # <- insert your v3 app’s UID here
    secret: ""   # <- insert your app’s SECRET here
    login: ""    # <- insert your intra LOGIN here
    password: "" # <- insert your intra PASSWORD here
    uri: 'https://auth.42.fr/auth/realms/staff-42/protocol/openid-connect/token'
```

To get the v2 client and secret, you will have to create an app, you can find how by [reading the manual](https://api.intra.42.fr/apidoc/guides/getting_started).

The v3 client and secrets are provided by 42 Central. These calls also require the login and password of a user with the appropriate permissions.


## Usage
You can import the `IntraAPIClient` class and create an instance of it:
```python
from api42lib import IntraAPIClient

ic = IntraAPIClient()
```

If the config.yml is in another path other than the root directory, you can specify it as a parameter:
```python
from api42lib import IntraAPIClient

ic = IntraAPIClient(config_path="path/to/config.yml")
```

The library supports following methods: `GET`, `POST`, `PATCH`, `PUT` and `DELETE`.
The basic app will only be able to use `GET`, for other methods, you will have to take a look at Roles Entities for permissions.

To use the previous methods, you need to provide the specific endpoint. For example:
```python
# For v2 calls
response = ic.get("teams")
response = ic.get("v2/teams")
response = ic.get("/v2/teams")
# For v3 calls
response = ic.get("freeze/v2/freezes")
response = ic.get("v3/freeze/v2/freezes")
response = ic.get("/v3/freeze/v2/freezes")
response = ic.get("pace-system/v1/users")
response = ic.get("v3/pace-system/v1/users")
response = ic.get("/v3/pace-system/v1/users")
```

Or with a full URL:
```python
# For v2 calls
response = ic.get("https://api.intra.42.fr/v2/teams")
# For v3 calls
response = ic.get("https://pace-system.42.fr/api/v1/users")
response = ic.get("https://freeze.42.fr/api/v2/freezes")
```

This example will return a request object.
To work with the response data, you may want to convert it to a json object:
```python
if response.status_code == 200: # Make sure response status is OK
    data = response.json()
```

### Parameters:
If (should be when by now) you have read the API documentary, you may have noticed that you can apply all kinds of parameters to the request. These parameters include things like `sort`, `filter` and `range`. Make sure you always check the specific page in the documentation because different endpoints have different parameters and different ways of using them.

Parameters can be used to further specify your request without making the actual request string a mess. They are given as a parameter to the class method and should be in object format. An example of parameters and their usage:
```python
params = {
   "filter[primary_campus]": 51,
   "filter[cursus]": 21,
   "range[final_mark]": "100,125",
   "sort":" -final_mark,name"
}
```

Here we are filtering by `campus` and `cursus`, results must be in a specified range of `final_mark` and they must be sorted in descending order based on `final_mark` and ascending order based on `name`.

To use the parameters with a certain request, you simply add them as a keyword argument params:
```python
response = ic.get("teams", params=params)
```

### Pagination:
Most of the endpoints are paginated with the request parameters `page`(both v2 & v3) and `per_page`(only for v2). In order to receive all of the data of a certain endpoint, you usually need to do multiple requests.

* `ic.pages()` retrieves all data from an endpoint, making multiple requests until all data is retrieved.
* `ic.pages_threaded()` does the same thing but in multiple threads, reducing the time it takes to retrieve requests.

Example usage:
```python
userList = ic.pages_threaded("users")
```

Enable a progress bar for lengthy operations (enabled by default):
```python
ic.progress_bar_enable()
```

To disable the progress bar:
```python
ic.progress_bar_disable()
```

## Contribute
Spot an Error? Want to Contribute? Submit a pull request to fix or add features!

To develop your own changes clone this repository, make changes and install the package locally to test it:
```bash
pip install .
```

You can run all tests with pytest (make sure to have pytest installed first):
```bash
pytest
```
