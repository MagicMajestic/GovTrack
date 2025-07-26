# GovTracker2 Migration Notes
*GovTracker2 Python Migration by Replit Agent*

## Overview
This document outlines the migration from Node.js + TypeScript to Python 3.12 + Flask, detailing the key differences, architectural changes, and migration considerations.

## Technology Stack Changes

### Backend Framework
- **Before**: Node.js + Express + TypeScript
- **After**: Python 3.12 + Flask + SQLAlchemy

### Database ORM
- **Before**: TypeORM (for PostgreSQL/MySQL)
- **After**: SQLAlchemy (with MySQL compatibility layer)

### Discord Bot
- **Before**: discord.js
- **After**: discord.py

### Task Scheduling
- **Before**: node-cron
- **After**: APScheduler

## Key Architectural Changes

### 1. Application Structure
