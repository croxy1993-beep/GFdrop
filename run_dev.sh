#!/bin/sh
pip install -r requirements-dev.txt && GFDROP_DATA=./.devdata python3 app.py
