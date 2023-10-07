"""Representations of rows of the filter tree."""

from __future__ import annotations

import enum
from typing import Any, Iterable, assert_never

import attrs

from usdb_syncer.song_data import SongData


class SongMatch:
    """Interface for objects that can be matched against a song."""

    def matches_song(self, _song: SongData) -> bool:
        raise NotImplementedError


class SongArtistMatch(str, SongMatch):
    """str that can be matched against a song's artist."""

    def matches_song(self, song: SongData) -> bool:
        return self == song.data.artist


class SongTitleMatch(str, SongMatch):
    """str that can be matched against a song's title."""

    def matches_song(self, song: SongData) -> bool:
        return self == song.data.title


class SongEditionMatch(str, SongMatch):
    """str that can be matched against a song's edition."""

    def matches_song(self, song: SongData) -> bool:
        return self == song.data.edition


class SongLanguageMatch(str, SongMatch):
    """str that can be matched against a song's language."""

    def matches_song(self, song: SongData) -> bool:
        return self == song.data.language


@attrs.define(kw_only=True)
class TreeItem:
    """A row in the tree."""

    data: Any
    parent: TreeItem | None
    row_in_parent: int = attrs.field(default=0, init=False)
    children: tuple[TreeItem, ...] = attrs.field(factory=tuple, init=False)
    checked: bool = attrs.field(default=False, init=False)
    checkable: bool = attrs.field(default=False, init=False)

    def toggle_checked(self) -> None:
        pass


@attrs.define(kw_only=True)
class RootItem(TreeItem):
    """The root item of the tree. Only used internally."""

    data: None = attrs.field(default=None, init=False)
    parent: None = attrs.field(default=None, init=False)
    children: tuple[FilterItem, ...] = attrs.field(factory=tuple, init=False)

    def add_child(self, child: FilterItem) -> None:
        child.parent = self
        child.row_in_parent = len(self.children)
        self.children = (*self.children, child)


@attrs.define(kw_only=True)
class FilterItem(TreeItem):
    """A top-level row in the tree representing a filter kind."""

    data: Filter
    parent: RootItem
    children: tuple[VariantItem, ...] = attrs.field(factory=tuple, init=False)
    checked_children: set[int] = attrs.field(factory=set, init=False)

    def add_child(self, child: VariantItem) -> None:
        child.parent = self
        child.row_in_parent = len(self.children)
        self.children = (*self.children, child)

    def accepts_song(self, song: SongData) -> bool:
        return not self.checked_children or any(
            self.children[i].accepts_song(song) for i in self.checked_children
        )

    def is_checkable(self) -> bool:
        return bool(self.checked_children)

    def toggle_checked(self) -> None:
        if self.checked:
            self.uncheck_children()

    def uncheck_children(self) -> None:
        for child in self.children:
            child.checked = False
        self.checked_children.clear()
        self.checkable = self.checked = False

    def check_child(self, child: int) -> None:
        self.uncheck_children()
        self.checked_children.add(child)
        self.checkable = self.checked = self.children[child].checked = True


@attrs.define(kw_only=True)
class VariantItem(TreeItem):
    """A node row in the tree representing one variant of a specific filter."""

    data: SongMatch
    parent: FilterItem
    checkable: bool = attrs.field(default=True, init=False)
    children: tuple[TreeItem, ...] = attrs.field(factory=tuple, init=False)

    def accepts_song(self, song: SongData) -> bool:
        return self.data.matches_song(song)

    def is_checkable(self) -> bool:
        return True

    def toggle_checked(self) -> None:
        if self.checked:
            self.parent.uncheck_children()
        else:
            self.parent.check_child(self.row_in_parent)


class Filter(enum.Enum):
    """Kinds of filters in the tree."""

    # STATUS = enum.auto()
    ARTIST = 0
    TITLE = enum.auto()
    EDITION = enum.auto()
    LANGUAGE = enum.auto()
    GOLDEN_NOTES = enum.auto()
    RATING = enum.auto()
    VIEWS = enum.auto()

    def __str__(self) -> str:
        match self:
            # case self.STATUS:
            #     return "Status"
            case Filter.ARTIST:
                return "Artist"
            case Filter.TITLE:
                return "Title"
            case Filter.EDITION:
                return "Edition"
            case Filter.LANGUAGE:
                return "Language"
            case Filter.GOLDEN_NOTES:
                return "Golden Notes"
            case Filter.RATING:
                return "Rating"
            case Filter.VIEWS:
                return "Views"
            case _ as unreachable:
                assert_never(unreachable)

    def static_variants(self) -> Iterable[SongMatch]:
        match self:
            case Filter.ARTIST | Filter.TITLE | Filter.EDITION | Filter.LANGUAGE:
                return []
            # case Filter.STATUS:
            #     vars = DownloadStatus
            #     func = status_is_match
            case Filter.GOLDEN_NOTES:
                return GoldenNotesVariant
            case Filter.RATING:
                return RatingVariant
            case Filter.VIEWS:
                return ViewsVariant
            case _ as unreachable:
                assert_never(unreachable)


class RatingVariant(SongMatch, enum.Enum):
    """Selectable variants for the song rating filter."""

    R_NONE = None
    R_1 = 1
    R_2 = 2
    R_3 = 3
    R_4 = 4
    R_5 = 5

    def __str__(self) -> str:
        if self == RatingVariant.R_NONE:
            return "None"
        return self.value * "★"

    def matches_song(self, song: SongData) -> bool:
        return self.value == song.data.rating


class GoldenNotesVariant(SongMatch, enum.Enum):
    """Selectable variants for the golden notes filter."""

    NO = False
    YES = True

    def __str__(self) -> str:
        match self:
            case GoldenNotesVariant.NO:
                return "No"
            case GoldenNotesVariant.YES:
                return "Yes"
            case _ as unreachable:
                assert_never(unreachable)

    def matches_song(self, song: SongData) -> bool:
        return self.value is song.data.golden_notes


class ViewsVariant(SongMatch, enum.Enum):
    """Selectable variants for the views filter."""

    V_0 = (0, 100)
    V_100 = (100, 200)
    V_200 = (200, 300)
    V_300 = (300, 400)
    V_400 = (400, 500)
    V_500 = (500, None)

    def __str__(self) -> str:
        if self.value[1] is None:
            return f"{self.value[0]}+"
        return f"{self.value[0]} to {self.value[1] - 1}"

    def matches_song(self, song: SongData) -> bool:
        return self.value[0] <= song.data.views and (
            self.value[1] is None or song.data.views < self.value[1]
        )
