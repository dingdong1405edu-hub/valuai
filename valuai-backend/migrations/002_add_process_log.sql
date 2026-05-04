-- Migration 002: Add process_log column to valuations table
-- Run against Railway PostgreSQL after 001_init.sql

ALTER TABLE valuations
    ADD COLUMN IF NOT EXISTS process_log JSONB NOT NULL DEFAULT '{}';
