"""Async SQLite database helpers for the Miss Westie bot."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import aiosqlite


@dataclass(slots=True)
class MusicDrop:
    title: str
    artist: str
    link: str | None
    release_date: str | None
    submitted_by: int
    created_at: datetime


@dataclass(slots=True)
class CollabOpportunity:
    title: str
    description: str
    contact: str
    status: str
    created_by: int
    created_at: datetime


@dataclass(slots=True)
class FeedbackItem:
    user_id: int
    feedback: str
    status: str
    created_at: datetime


@dataclass(slots=True)
class SupportTicket:
    user_id: int
    issue: str
    status: str
    created_at: datetime


@dataclass(slots=True)
class RoleRequest:
    user_id: int
    role_name: str
    status: str
    created_at: datetime


@dataclass(slots=True)
class ReleaseAnnouncement:
    title: str
    description: str
    release_date: str | None
    link: str | None
    created_by: int
    created_at: datetime


class Database:
    """Lightweight helper around :mod:`aiosqlite` with convenience methods."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> aiosqlite.Connection:
        if self._conn is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = await aiosqlite.connect(self.path)
            self._conn.row_factory = aiosqlite.Row
            await self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def initialize(self) -> None:
        """Create required tables if they do not exist."""

        conn = await self.connect()
        await conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS music_drops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                link TEXT,
                release_date TEXT,
                submitted_by INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS collabs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                contact TEXT NOT NULL,
                status TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                feedback TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                issue TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS role_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role_name TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                release_date TEXT,
                link TEXT,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        await conn.commit()

    # ------------------------------------------------------------------
    # Insert helpers
    # ------------------------------------------------------------------

    async def _insert(self, table: str, data: dict[str, Any]) -> int:
        columns = ", ".join(data.keys())
        placeholders = ", ".join([":" + key for key in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        async with self._lock:
            conn = await self.connect()
            cursor = await conn.execute(query, data)
            await conn.commit()
            return cursor.lastrowid

    async def _fetch_all(self, query: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        conn = await self.connect()
        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def _execute(self, query: str, params: Sequence[Any]) -> None:
        async with self._lock:
            conn = await self.connect()
            await conn.execute(query, params)
            await conn.commit()

    # ------------------------------------------------------------------
    # Music drops
    # ------------------------------------------------------------------

    async def log_music_drop(self, drop: MusicDrop) -> int:
        payload = asdict(drop)
        payload["created_at"] = drop.created_at.isoformat()
        return await self._insert("music_drops", payload)

    async def recent_music_drops(self, limit: int = 5) -> list[dict[str, Any]]:
        query = (
            "SELECT id, title, artist, link, release_date, submitted_by, created_at "
            "FROM music_drops ORDER BY created_at DESC LIMIT ?"
        )
        return await self._fetch_all(query, (limit,))

    # ------------------------------------------------------------------
    # Collabs
    # ------------------------------------------------------------------

    async def create_collab(self, collab: CollabOpportunity) -> int:
        payload = asdict(collab)
        payload["created_at"] = collab.created_at.isoformat()
        return await self._insert("collabs", payload)

    async def list_collabs(self, status: str | None = None) -> list[dict[str, Any]]:
        if status:
            return await self._fetch_all(
                "SELECT * FROM collabs WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        return await self._fetch_all("SELECT * FROM collabs ORDER BY created_at DESC")

    async def update_collab_status(self, collab_id: int, status: str) -> None:
        await self._execute("UPDATE collabs SET status = ? WHERE id = ?", (status, collab_id))

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------

    async def store_feedback(self, feedback: FeedbackItem) -> int:
        payload = asdict(feedback)
        payload["created_at"] = feedback.created_at.isoformat()
        return await self._insert("feedback", payload)

    async def list_feedback(self, status: str | None = None) -> list[dict[str, Any]]:
        if status:
            return await self._fetch_all(
                "SELECT * FROM feedback WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        return await self._fetch_all("SELECT * FROM feedback ORDER BY created_at DESC")

    async def update_feedback_status(self, feedback_id: int, status: str) -> None:
        await self._execute("UPDATE feedback SET status = ? WHERE id = ?", (status, feedback_id))

    # ------------------------------------------------------------------
    # Support tickets
    # ------------------------------------------------------------------

    async def create_support_ticket(self, ticket: SupportTicket) -> int:
        payload = asdict(ticket)
        payload["created_at"] = ticket.created_at.isoformat()
        return await self._insert("support_tickets", payload)

    async def list_support_tickets(self, status: str | None = None) -> list[dict[str, Any]]:
        if status:
            return await self._fetch_all(
                "SELECT * FROM support_tickets WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        return await self._fetch_all("SELECT * FROM support_tickets ORDER BY created_at DESC")

    async def update_support_ticket(self, ticket_id: int, status: str) -> None:
        await self._execute("UPDATE support_tickets SET status = ? WHERE id = ?", (status, ticket_id))

    # ------------------------------------------------------------------
    # Role requests
    # ------------------------------------------------------------------

    async def create_role_request(self, request: RoleRequest) -> int:
        payload = asdict(request)
        payload["created_at"] = request.created_at.isoformat()
        return await self._insert("role_requests", payload)

    async def list_role_requests(self, status: str | None = None) -> list[dict[str, Any]]:
        if status:
            return await self._fetch_all(
                "SELECT * FROM role_requests WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        return await self._fetch_all("SELECT * FROM role_requests ORDER BY created_at DESC")

    async def update_role_request(self, request_id: int, status: str) -> None:
        await self._execute("UPDATE role_requests SET status = ? WHERE id = ?", (status, request_id))

    # ------------------------------------------------------------------
    # Releases
    # ------------------------------------------------------------------

    async def create_release(self, release: ReleaseAnnouncement) -> int:
        payload = asdict(release)
        payload["created_at"] = release.created_at.isoformat()
        return await self._insert("releases", payload)

    async def recent_releases(self, limit: int = 5) -> list[dict[str, Any]]:
        query = (
            "SELECT id, title, description, release_date, link, created_by, created_at "
            "FROM releases ORDER BY CASE WHEN release_date IS NULL THEN 1 ELSE 0 END, release_date DESC, created_at DESC LIMIT ?"
        )
        return await self._fetch_all(query, (limit,))

    async def update_release(self, release_id: int, **fields: Any) -> None:
        if not fields:
            return
        assignments = ", ".join(f"{key} = ?" for key in fields)
        params = list(fields.values()) + [release_id]
        await self._execute(f"UPDATE releases SET {assignments} WHERE id = ?", params)


__all__ = [
    "Database",
    "MusicDrop",
    "CollabOpportunity",
    "FeedbackItem",
    "SupportTicket",
    "RoleRequest",
    "ReleaseAnnouncement",
]
