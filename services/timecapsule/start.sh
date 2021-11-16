#!/bin/sh

chown doctorwho: /app/data /app/settings
chmod -R 755 /app /app/wwwroot
chmod 700 /app/data /app/settings

su doctorwho -s /bin/sh -c 'dotnet timecapsule.dll'
