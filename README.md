# Coffee Counter web API

A simple web API for recording my coffee consumption.

[![python](https://img.shields.io/badge/Python-3.7-3776AB.svg?style=flat&logo=python&logoColor=FFFF9A)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.63.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com) <br>
[![pytest](https://github.com/jhrcook/coffee-counter-api/actions/workflows/CI.yml/badge.svg)](https://github.com/jhrcook/coffee-counter-api/actions/workflows/CI.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

**API root: [//a7a9ck.deta.dev](//a7a9ck.deta.dev)** <br>
**Interactive API documentation: [//a7a9ck.deta.dev/docs](//a7a9ck.deta.dev/docs)**

## Uses

### SwiftBar Plugin

I have created a [SwiftBar plugin](https://github.com/jhrcook/SwiftBar-Plugins/blob/master/coffee-tracker.1h.py) that queries the API for the active bags and presents them in a drop-down menu.
When one of the labels is tapped, the plugin then registers a use of the bag with the API.

<img src="https://github.com/jhrcook/SwiftBar-Plugins/blob/master/.assets/coffee-tracker-screenshot.png" width="250px">

### Streamlit web app

I have built a [Streamlit](http://streamlit.io/) web application for visualizing and analyzing the data collected through this API: [app](https://share.streamlit.io/jhrcook/coffee-counter-streamlit/app.py) | [source](https://github.com/jhrcook/coffee-counter-streamlit)
