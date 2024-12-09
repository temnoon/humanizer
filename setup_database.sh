#!/bin/bash
# setup_database.sh

# Source environment variables
set -a
source .env
set +a

# Create database and users
psql -U postgres << EOF
CREATE DATABASE humanizer;
\c humanizer

-- Create extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create roles
CREATE ROLE humanizer_admin WITH LOGIN PASSWORD '${HUMANIZER_ADMIN_PASSWORD}';
CREATE ROLE humanizer_app WITH LOGIN PASSWORD '${HUMANIZER_APP_PASSWORD}';
CREATE ROLE humanizer_readonly WITH LOGIN PASSWORD '${HUMANIZER_READONLY_PASSWORD}';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE humanizer TO humanizer_admin;
GRANT CONNECT ON DATABASE humanizer TO humanizer_app;
GRANT CONNECT ON DATABASE humanizer TO humanizer_readonly;

-- Schema permissions
GRANT ALL ON SCHEMA public TO humanizer_admin;
GRANT USAGE ON SCHEMA public TO humanizer_app;
GRANT USAGE ON SCHEMA public TO humanizer_readonly;
