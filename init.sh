#!/bin/bash

echo "Creating application roles..."

mongosh <<EOF
use $MONGO_DB_NAME

db.createUser({
  user: "$APP_WRITER_USER",
  pwd: "$APP_WRITER_PASSWORD",
  roles: [ { role: "readWrite", db: "$MONGO_DB_NAME" } ]
});

db.createUser({
  user: "$APP_READER_USER",
  pwd: "$APP_READER_PASSWORD",
  roles: [ { role: "read", db: "$MONGO_DB_NAME" } ]
});
EOF