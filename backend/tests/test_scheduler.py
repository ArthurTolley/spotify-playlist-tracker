"""Tests for scheduler job re-registration (register_auto_sync_jobs)."""

from types import SimpleNamespace

import pytest

from app import app, db
import app as app_module
from app import run_sync_job
from models import TrackedPlaylist, User


class StubScheduler:
    """Records add_job calls instead of scheduling anything."""

    def __init__(self):
        self.added_jobs = []

    def add_job(self, **kwargs):
        self.added_jobs.append(kwargs)
        return SimpleNamespace(id=kwargs["id"])


@pytest.fixture()
def fresh_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


def test_register_auto_sync_jobs_registers_only_enabled(monkeypatch, fresh_db):
    stub = StubScheduler()
    monkeypatch.setattr(app_module, "scheduler", stub)

    with app.app_context():
        user = User(id="scheduler-test-user")
        db.session.add(user)
        db.session.flush()
        enabled_tp = TrackedPlaylist(
            user_id=user.id,
            source_playlist_id="src-enabled",
            tracked_playlist_id="trk-enabled",
            tracked_playlist_name="Enabled",
            auto_sync_enabled=True,
            job_id="sync_old",
        )
        disabled_tp = TrackedPlaylist(
            user_id=user.id,
            source_playlist_id="src-disabled",
            tracked_playlist_id="trk-disabled",
            tracked_playlist_name="Disabled",
            auto_sync_enabled=False,
        )
        db.session.add_all([enabled_tp, disabled_tp])
        db.session.commit()

        app_module.register_auto_sync_jobs()

        assert len(stub.added_jobs) == 1
        job = stub.added_jobs[0]
        assert job["id"] == f"sync_{enabled_tp.id}"
        assert job["func"] is run_sync_job
        assert job["args"] == [enabled_tp.id]
        assert job["trigger"] == "interval"
        assert job["weeks"] == 1
        assert job["replace_existing"] is True


def test_register_auto_sync_jobs_noop_when_none_enabled(monkeypatch, fresh_db):
    stub = StubScheduler()
    monkeypatch.setattr(app_module, "scheduler", stub)

    with app.app_context():
        user = User(id="scheduler-test-user-2")
        db.session.add(user)
        db.session.flush()
        db.session.add(TrackedPlaylist(
            user_id=user.id,
            source_playlist_id="src-disabled-2",
            tracked_playlist_id="trk-disabled-2",
            tracked_playlist_name="Disabled Two",
            auto_sync_enabled=False,
        ))
        db.session.commit()

        app_module.register_auto_sync_jobs()

        assert stub.added_jobs == []
