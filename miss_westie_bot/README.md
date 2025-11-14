# Miss Westie Discord Bot

A modular Discord bot tailored for Miss Westie's community workflows. The bot provides helpers for music drop announcements, collaboration requests, producer spotlights, release tracking, role applications, feedback collection, and support ticket triage.

## Features

- **Music Drops** – Log upcoming songs and share the latest releases with the server.
- **Collaboration Board** – Capture opportunities and mark them as filled when complete.
- **Producer Roster** – Allow verified community members to request producer status and publish the approved list.
- **Release Tracker** – Maintain a calendar of upcoming drops and broadcast them to announcement channels.
- **Role Requests** – Generalised workflow for community role applications.
- **Feedback Inbox** – Accept community suggestions and let staff manage their lifecycle.
- **Support Tickets** – Provide a lightweight helpdesk queue for moderators.
- **Terraform Utilities** – Quick commands for surfacing setup checklists and reloading cogs after structural changes.

## Getting Started

1. Install dependencies (see `requirements.txt` or the project `pyproject.toml`).
2. Create a `.env` file with `DISCORD_BOT_TOKEN` and any optional `MISS_WESTIE_*` overrides from `config.py`.
3. Run the bot:
   ```bash
   python -m miss_westie_bot.bot
   ```

On start-up the bot initialises its SQLite database and loads all cogs listed in `miss_westie_bot.cogs.DEFAULT_COGS`.

## Configuration

Configuration is centralised in `config.py` and can be overridden with environment variables:

- `MISS_WESTIE_PREFIX` – Command prefix for hybrid commands (default `!`).
- `MISS_WESTIE_DESCRIPTION` – Bot description string.
- `MISS_WESTIE_ACTIVITY` / `MISS_WESTIE_STATUS` – Presence information.
- `MISS_WESTIE_DB` – Location of the SQLite file.
- `MISS_WESTIE_STAFF_ROLES` – Comma-separated role names treated as staff.
- `MISS_WESTIE_VERIFIED_ROLES` – Comma-separated role names required for community submissions.
- `MISS_WESTIE_ANNOUNCEMENT_CHANNELS` – Comma-separated channel IDs for release broadcasts.

## Database Schema

The bot relies on SQLite tables created automatically in `db.py`:

- `music_drops` – Music drop metadata submitted by staff.
- `collabs` – Collaboration opportunities with status tracking.
- `feedback` – Member feedback with workflow status.
- `support_tickets` – Support queue entries.
- `role_requests` – Generic role applications (also reused for producer roster).
- `releases` – Release announcements and optional links.

Each table is managed through typed dataclasses to keep queries tidy and type-friendly.

## Development Notes

- Commands are implemented as hybrid commands so they work as both slash and prefix commands.
- Custom command guards in `utils/checks.py` honour the configured role names while still allowing guild managers to bypass restrictions when needed.
- Logging is centralised via `utils/logging_utils.configure_logging` to avoid duplicate handlers during reloads.

Contributions and refinements are welcome—just keep the experience pastel, friendly, and efficient for the Miss Westie crew!
