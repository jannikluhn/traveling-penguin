#!/bin/bash

rm -rf python
rm layer.zip
pip install -r requirements_layer.txt -t python
zip -r layer.zip python
rm -rf python
