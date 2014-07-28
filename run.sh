#!/bin/sh
locust -f test.py --host localhost ||
echo "Did u entered virtualenv and installed all the dependencies from requirements.txt?"
