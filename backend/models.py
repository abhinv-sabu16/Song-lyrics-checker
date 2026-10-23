from sqlalchemy import (
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)

    songs: Mapped[list["Song"]] = relationship(back_populates="artist")


class Song(Base):
    __tablename__ = "songs"
    __table_args__ = (
        UniqueConstraint("title", "artist_id", name="uq_song_title_artist"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), index=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    # Source attribution: where the lyrics came from and under what terms.
    source: Mapped[str] = mapped_column(String(300), default="original")
    license: Mapped[str] = mapped_column(String(100), default="original")

    artist: Mapped[Artist] = relationship(back_populates="songs")
    lines: Mapped[list["LyricLine"]] = relationship(
        back_populates="song",
        cascade="all, delete-orphan",
        order_by="LyricLine.line_number",
    )


class LyricLine(Base):
    __tablename__ = "lyric_lines"
    __table_args__ = (
        UniqueConstraint("song_id", "line_number", name="uq_line_song_number"),
        Index("ix_lines_normalized", "normalized_text"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id"), index=True)
    line_number: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    # Lowercased, whitespace-collapsed copy used for searching.
    # The original text is kept separately for display.
    normalized_text: Mapped[str] = mapped_column(Text)

    song: Mapped[Song] = relationship(back_populates="lines")