# Victor - Highrise Trading Discord Bot

## Overview

Victor is a Discord bot that facilitates trading of Highrise metaverse items through a secure marketplace system with user verification. The bot integrates with the Highrise game API to verify user ownership and provides a web dashboard for administration. It uses Flask for the web interface and Discord.py for bot functionality, with both components running together to maintain 24/7 uptime.

## System Architecture

The application follows a dual-architecture approach with two main components:

1. **Discord Bot Application**: Built with Discord.py, handles all bot interactions and commands
2. **Flask Web Dashboard**: Provides administrative interface and keeps the bot alive

### Core Architecture Principles:
- **Async-First Design**: All operations use async/await patterns for optimal performance
- **Modular Command System**: Commands organized into cogs for maintainability
- **Database Abstraction**: Clean separation between data models and business logic
- **Keep-Alive Integration**: Flask server prevents bot from sleeping on cloud platforms

## Key Components

### 1. Database Layer
- **Primary Database**: SQLAlchemy with SQLite (configurable to PostgreSQL)
- **Models**: User accounts, marketplace listings, transactions, guilds, and activity logs
- **Migration Support**: Automatic table creation and schema management
- **Connection Management**: Pool recycling and pre-ping for reliability

### 2. Discord Bot System
- **Command Handler**: Slash commands using Discord.py's app_commands
- **User Verification**: Two-step process using Highrise bio validation
- **Marketplace Features**: Item listing, browsing, and purchase facilitation
- **Admin Controls**: Guild management and moderation tools

### 3. Flask Web Dashboard
- **Authentication**: Discord OAuth2 integration for secure access
- **Admin Interface**: User management, marketplace oversight, analytics
- **Real-time Updates**: AJAX-powered dashboard with live data refresh
- **Theme System**: Goth-cute aesthetic with pink/steel color scheme

### 4. Highrise API Integration
- **User Verification**: Profile fetching and bio validation
- **No Authentication Required**: Uses public Highrise Web API endpoints
- **Rate Limiting**: Built-in delays and retry logic for API stability

## Data Flow

### User Verification Process:
1. User runs `/verify <highrise_username>` command
2. Bot generates 8-character verification code
3. User adds code to their Highrise bio
4. Bot validates code via Highrise API
5. User status updated to "verified" in database

### Marketplace Transactions:
1. Verified users can list items with `/list` command
2. Other users browse with `/market` command
3. Purchase initiated with `/buy` command
4. Bot facilitates contact between buyer and seller
5. Transaction logged for history and analytics

### Web Dashboard Access:
1. User authenticates via Discord OAuth2
2. Session established with user permissions
3. Dashboard provides real-time bot statistics
4. Admin actions update database directly

## External Dependencies

### Required Services:
- **Discord API**: Bot token and OAuth2 application
- **Highrise Web API**: Open API, no authentication needed

### Python Packages:
- `discord.py`: Discord bot framework
- `flask`: Web dashboard framework
- `sqlalchemy`: Database ORM
- `aiohttp`: Async HTTP client for API calls
- `python-dotenv`: Environment variable management

### Optional Integrations:
- **PostgreSQL**: For production database (auto-detected from DATABASE_URL)
- **Cloud Deployment**: Configured for platforms like Replit, Railway, etc.

## Deployment Strategy

### Environment Variables:
- `DISCORD_BOT_TOKEN`: Required for bot functionality
- `SESSION_SECRET`: Flask session security (auto-generated if not set)
- `DATABASE_URL`: Optional PostgreSQL connection string
- `DISCORD_CLIENT_ID/SECRET`: For web dashboard OAuth2
- `PORT`: Web server port (defaults to 5000)

### Deployment Recommendations:
- **Always-On Hosting**: Use Reserved VM for 24/7 uptime
- **Database**: SQLite for development, PostgreSQL for production
- **Monitoring**: Health endpoints at `/` and `/health`
- **Logging**: Comprehensive logging to both file and console

### Startup Process:
1. Load environment variables from `.env` file
2. Initialize database connection and create tables
3. Start Flask web server in daemon thread
4. Initialize Discord bot with command cogs
5. Connect to Discord and begin event loop

## Changelog

- July 08, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.