#!/bin/bash

until nc -z rabbit 5672; do
    echo "$(date) - waiting for rabbitmq..."
    sleep 1
done

nameko run --config ./config.yaml datetime_worker