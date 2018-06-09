import pytest
import datetime
import os
import uuid

from django.core.management import call_command
from django.core.management.base import CommandError

from funkwhale_api.providers.audiofile import tasks
from funkwhale_api.music import tasks as music_tasks

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")


def test_can_create_track_from_file_metadata_no_mbid(db, mocker):
    metadata = {
        "artist": ["Test artist"],
        "album": ["Test album"],
        "title": ["Test track"],
        "TRACKNUMBER": ["4"],
        "date": ["2012-08-15"],
    }
    m1 = mocker.patch("mutagen.File", return_value=metadata)
    m2 = mocker.patch(
        "funkwhale_api.music.metadata.Metadata.get_file_type", return_value="OggVorbis"
    )
    track = tasks.import_track_data_from_path(os.path.join(DATA_DIR, "dummy_file.ogg"))

    assert track.title == metadata["title"][0]
    assert track.mbid is None
    assert track.position == 4
    assert track.album.title == metadata["album"][0]
    assert track.album.mbid is None
    assert track.album.release_date == datetime.date(2012, 8, 15)
    assert track.artist.name == metadata["artist"][0]
    assert track.artist.mbid is None


def test_can_create_track_from_file_metadata_mbid(factories, mocker):
    album = factories["music.Album"]()
    mocker.patch(
        "funkwhale_api.music.models.Album.get_or_create_from_api",
        return_value=(album, True),
    )

    album_data = {
        "release": {
            "id": album.mbid,
            "medium-list": [
                {
                    "track-list": [
                        {
                            "id": "03baca8b-855a-3c05-8f3d-d3235287d84d",
                            "position": "4",
                            "number": "4",
                            "recording": {
                                "id": "2109e376-132b-40ad-b993-2bb6812e19d4",
                                "title": "Teen Age Riot",
                            },
                        }
                    ],
                    "track-count": 1,
                }
            ],
        }
    }
    mocker.patch("funkwhale_api.musicbrainz.api.releases.get", return_value=album_data)
    track_data = album_data["release"]["medium-list"][0]["track-list"][0]
    metadata = {
        "musicbrainz_albumid": [album.mbid],
        "musicbrainz_trackid": [track_data["recording"]["id"]],
    }
    m1 = mocker.patch("mutagen.File", return_value=metadata)
    m2 = mocker.patch(
        "funkwhale_api.music.metadata.Metadata.get_file_type", return_value="OggVorbis"
    )
    track = tasks.import_track_data_from_path(os.path.join(DATA_DIR, "dummy_file.ogg"))

    assert track.title == track_data["recording"]["title"]
    assert track.mbid == track_data["recording"]["id"]
    assert track.position == 4
    assert track.album == album
    assert track.artist == album.artist


def test_management_command_requires_a_valid_username(factories, mocker):
    path = os.path.join(DATA_DIR, "dummy_file.ogg")
    user = factories["users.User"](username="me")
    mocker.patch(
        "funkwhale_api.providers.audiofile.management.commands.import_files.Command.do_import",  # noqa
        return_value=(mocker.MagicMock(), []),
    )
    with pytest.raises(CommandError):
        call_command("import_files", path, username="not_me", interactive=False)
    call_command("import_files", path, username="me", interactive=False)


def test_in_place_import_only_from_music_dir(factories, settings):
    user = factories["users.User"](username="me")
    settings.MUSIC_DIRECTORY_PATH = "/nope"
    path = os.path.join(DATA_DIR, "dummy_file.ogg")
    with pytest.raises(CommandError):
        call_command(
            "import_files", path, in_place=True, username="me", interactive=False
        )


def test_import_files_creates_a_batch_and_job(factories, mocker):
    m = mocker.patch("funkwhale_api.music.tasks.import_job_run")
    user = factories["users.User"](username="me")
    path = os.path.join(DATA_DIR, "dummy_file.ogg")
    call_command("import_files", path, username="me", async=False, interactive=False)

    batch = user.imports.latest("id")
    assert batch.source == "shell"
    assert batch.jobs.count() == 1

    job = batch.jobs.first()

    assert job.status == "pending"
    with open(path, "rb") as f:
        assert job.audio_file.read() == f.read()

    assert job.source == "file://" + path
    m.assert_called_once_with(import_job_id=job.pk, use_acoustid=False)


def test_import_files_skip_if_path_already_imported(factories, mocker):
    user = factories["users.User"](username="me")
    path = os.path.join(DATA_DIR, "dummy_file.ogg")
    existing = factories["music.TrackFile"](source="file://{}".format(path))

    call_command("import_files", path, username="me", async=False, interactive=False)
    assert user.imports.count() == 0


def test_import_files_works_with_utf8_file_name(factories, mocker):
    m = mocker.patch("funkwhale_api.music.tasks.import_job_run")
    user = factories["users.User"](username="me")
    path = os.path.join(DATA_DIR, "utf8-éà◌.ogg")
    call_command("import_files", path, username="me", async=False, interactive=False)
    batch = user.imports.latest("id")
    job = batch.jobs.first()
    m.assert_called_once_with(import_job_id=job.pk, use_acoustid=False)


def test_import_files_in_place(factories, mocker, settings):
    settings.MUSIC_DIRECTORY_PATH = DATA_DIR
    m = mocker.patch("funkwhale_api.music.tasks.import_job_run")
    user = factories["users.User"](username="me")
    path = os.path.join(DATA_DIR, "utf8-éà◌.ogg")
    call_command(
        "import_files",
        path,
        username="me",
        async=False,
        in_place=True,
        interactive=False,
    )
    batch = user.imports.latest("id")
    job = batch.jobs.first()
    assert bool(job.audio_file) is False
    m.assert_called_once_with(import_job_id=job.pk, use_acoustid=False)


def test_storage_rename_utf_8_files(factories):
    tf = factories["music.TrackFile"](audio_file__filename="été.ogg")
    assert tf.audio_file.name.endswith("ete.ogg")
