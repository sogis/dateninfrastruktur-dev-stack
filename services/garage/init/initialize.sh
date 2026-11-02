#!/bin/sh
set -eu

BUCKET="${GARAGE_BUCKET:-ch.so.daten}"
PRIVATE_BUCKET="${GARAGE_PRIVATE_BUCKET:-ch.so.dateninfrastruktur.private}"
PRIVATE_KEY="${GARAGE_PRIVATE_OBJECT_KEY:-private-foundation-smoke.txt}"
PRIVATE_ID="${GARAGE_PRIVATE_OBJECT_ID:?GARAGE_PRIVATE_OBJECT_ID is required}"
ENDPOINT="${AWS_ENDPOINT_URL:-http://garage:3900}"
REGION="${AWS_DEFAULT_REGION:-garage}"

aws_call() {
  aws --endpoint-url "$ENDPOINT" --region "$REGION" "$@"
}

wait_for_api() {
  i=0
  until aws_call s3api list-buckets >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -gt 90 ]; then
      echo "Garage S3 API did not become ready." >&2
      exit 1
    fi
    sleep 1
  done
}

ensure_bucket() {
  bucket="$1"
  if ! aws_call s3api head-bucket --bucket "$bucket" >/dev/null 2>&1; then
    aws_call s3api create-bucket --bucket "$bucket" >/dev/null
  fi
  i=0
  until aws_call s3api head-bucket --bucket "$bucket" >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -gt 60 ]; then
      echo "Bucket ${bucket} did not become available." >&2
      exit 1
    fi
    sleep 1
  done
}

printf 'private-object-id=%s\n' "$PRIVATE_ID" > /tmp/private-foundation-smoke.txt

echo "Waiting for Garage S3 API at ${ENDPOINT} ..."
wait_for_api

echo "Ensuring public bucket ${BUCKET} exists ..."
ensure_bucket "$BUCKET"

echo "Configuring public website access and CORS on ${BUCKET} ..."
aws_call s3api put-bucket-website \
  --bucket "$BUCKET" \
  --website-configuration file:///init/website.json
aws_call s3api put-bucket-cors \
  --bucket "$BUCKET" \
  --cors-configuration file:///init/cors.json

echo "Ensuring private bucket ${PRIVATE_BUCKET} exists without website access ..."
ensure_bucket "$PRIVATE_BUCKET"
aws_call s3api delete-bucket-website --bucket "$PRIVATE_BUCKET" >/dev/null 2>&1 || true
aws_call s3api put-object \
  --bucket "$PRIVATE_BUCKET" \
  --key "$PRIVATE_KEY" \
  --body /tmp/private-foundation-smoke.txt >/dev/null
rm -f /tmp/private-foundation-smoke.txt

echo "Garage initialization completed for ${BUCKET} and ${PRIVATE_BUCKET}."
echo "Public object URL prefix: http://localhost:${GARAGE_PUBLIC_PORT:-18081}/${BUCKET}/"
