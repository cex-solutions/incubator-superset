#!/bin/bash
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
set -eo pipefail

while [[ ! -f /var/configs/superset_config.py ]]
do
  echo "Config file /var/configs/superset_config.py not visible yet. Waiting ..."
  sleep 2
done

### Move configuration file in correct location
echo "Copying /var/configs/superset_config.py /code/cEX/superset_config.py"
cp /var/configs/superset_config.py /app/pythonpath/superset_config.py

if [ "${#}" -ne 0 ]; then
    exec "${@}"
else
    gunicorn \
      -w 10 \
      -k gevent \
      --timeout 120 \
      -b "0.0.0.0:${SUPERSET_PORT}" \
      --limit-request-line 0 \
      --limit-request-field_size 0 \
      --access-logfile '-' \
      --error-logfile '-' \
      --statsd-host statsd:8125 \
      "${FLASK_APP}"
fi

