"""Tests for functions from the usdb_scraper module."""

import json
import os
from datetime import datetime
from io import StringIO

from bs4 import BeautifulSoup

from usdb_syncer import SongId
from usdb_syncer.usdb_scraper import _parse_song_page, _parse_song_txt_from_txt_page
from usdb_syncer.usdb_song import UsdbSong, UsdbSongEncoder


def get_soup(resource_dir: str, resource: str) -> BeautifulSoup:
    with open(os.path.join(resource_dir, "html", resource), encoding="utf8") as html:
        return BeautifulSoup(html, "lxml")


def test_encoding_and_decoding_song_meta() -> None:
    song = UsdbSong(
        song_id=SongId(123),
        artist="Foo",
        title="Bar",
        language="Esperanto",
        edition="",
        golden_notes=True,
        rating=0,
        views=1,
    )
    buf = StringIO()
    json.dump(song, buf, cls=UsdbSongEncoder)
    buf.seek(0)
    new_song = json.load(buf, object_hook=UsdbSong.from_json)
    assert isinstance(new_song, UsdbSong)
    assert song == new_song


def test__parse_song_txt_from_txt_page(resource_dir: str) -> None:
    soup = get_soup(resource_dir, "txt_page.htm")
    txt, success = _parse_song_txt_from_txt_page(soup)
    assert success is True
    assert txt.startswith("#ARTIST:")
    assert txt.endswith("\nE")


def test__parse_song_page_with_commented_embedded_video(resource_dir: str) -> None:
    song_id = SongId(26152)
    soup = get_soup(resource_dir, "song_page_with_embedded_video.htm")
    details = _parse_song_page(soup, song_id)
    assert details.song_id == song_id
    assert details.artist == "Revolverheld"
    assert details.title == "Ich lass für dich das Licht an"
    assert details.cover_url == "https://usdb.animux.de/data/cover/26152.jpg"
    assert details.bpm == 276.17
    assert details.gap == 120000
    assert details.golden_notes
    assert not details.song_check
    assert details.date_time == datetime(2022, 10, 10, 19, 47)
    assert details.uploader == "bohning"
    assert details.editors == []
    assert details.views == 27
    assert details.rating == 5
    assert details.votes == 1
    assert details.audio_sample is None
    assert len(details.comments) == 2
    assert details.comments[0].date_time == datetime(2022, 10, 11, 10, 46)
    assert details.comments[0].author == "sportgonzo"
    assert details.comments[0].contents.text == "Perfekt :-)"
    assert details.comments[0].contents.youtube_ids == []
    assert details.comments[0].contents.urls == []
    assert details.comments[1].date_time == datetime(2022, 10, 10, 19, 48)
    assert details.comments[1].author == "bohning"
    assert details.comments[1].contents.text == ""
    assert details.comments[1].contents.youtube_ids == ["Vf0MC3CFihY"]
    assert details.comments[1].contents.urls == []


def test__parse_song_page_with_commented_unembedded_video(resource_dir: str) -> None:
    song_id = SongId(16575)
    soup = get_soup(resource_dir, "song_page_with_unembedded_video.htm")
    details = _parse_song_page(soup, song_id)
    assert len(details.comments) == 1
    assert details.comments[0].contents.youtube_ids == ["WIAvMiUcCgw"]


def test__parse_song_page_without_comments_or_cover(resource_dir: str) -> None:
    song_id = SongId(26244)
    soup = get_soup(resource_dir, "song_page_without_comments_or_cover.htm")
    details = _parse_song_page(soup, song_id)
    assert details.song_id == song_id
    assert details.artist == "The Used"
    assert details.title == "River Stay"
    assert details.cover_url is None
    assert details.bpm == 305
    assert details.gap == 548
    assert details.golden_notes
    assert not details.song_check
    assert details.date_time == datetime(2022, 10, 30, 19, 4)
    assert details.uploader == "askusbloodfist"
    assert details.editors == []
    assert details.views == 0
    assert details.rating == 0
    assert details.votes == 0
    assert details.audio_sample is None
    assert len(details.comments) == 0
