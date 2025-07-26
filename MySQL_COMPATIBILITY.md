# MySQL Compatibility Guide
*GovTracker2 Python Migration by Replit Agent*

## Overview
This document explains how to switch GovTracker2 from PostgreSQL (development) to MySQL (production) while maintaining full compatibility and functionality.

## Database Configuration

### Environment Variables
To switch to MySQL, update your environment variables:

```bash
# PostgreSQL (Development)
DATABASE_URL=postgresql://username:password@localhost:5432/govtracker2

# MySQL (Production)
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/govtracker2
