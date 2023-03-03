"""Meta data about a song that USDB shows in the result list."""

from __future__ import annotations

from json import JSONEncoder
from typing import Any

import attrs

from usdb_syncer import SongId


@attrs.frozen(auto_attribs=True, kw_only=True)
class UsdbSong:
    """Meta data about a song that USDB shows in the result list."""

    song_id: SongId
    artist: str
    title: str
    language: str
    edition: str
    golden_notes: bool
    rating: int
    views: int

    @classmethod
    def from_json(cls, dct: dict[str, Any]) -> UsdbSong:
        dct["song_id"] = SongId(dct["song_id"])
        return cls(**dct)

    @classmethod
    def from_html(
        cls,
        *,
        song_id: str,
        artist: str,
        title: str,
        language: str,
        edition: str,
        golden_notes: str,
        rating: str,
        views: str,
    ) -> UsdbSong:
        return cls(
            song_id=SongId.parse(song_id),
            artist=artist,
            title=title,
            language=language,
            edition=edition,
            golden_notes=golden_notes == "Yes",
            rating=rating.count("star.png"),
            views=int(views),
        )


class UsdbSongEncoder(JSONEncoder):
    """Custom JSON encoder"""

    def default(self, o: Any) -> Any:
        if isinstance(o, UsdbSong):
            return attrs.asdict(o, recurse=False)
        if isinstance(o, SongId):
            return int(o.value)
        return super().default(o)
