#!/usr/bin/env bash

archiving/archive.sh -b "$DC_S3_ARCHIVE_BUCKET" -p "$DC_S3_ARCHIVE_PREFIX" -s "$DC_S3_ARCHIVE_SUFFIX" -y "$DC_ARCHIVE_YAML_SAFETY" -d "$DC_ARCHIVE_DAYS"