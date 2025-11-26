"""Database models and operations for iBroadcast TUI."""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os

Base = declarative_base()

class Artist(Base):
    """Artist model."""
    __tablename__ = 'artists'

    id = Column(Integer, primary_key=True)
    ibroadcast_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    track_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    albums = relationship("Album", back_populates="artist")
    tracks = relationship("Track", back_populates="artist")

class Album(Base):
    """Album model."""
    __tablename__ = 'albums'

    id = Column(Integer, primary_key=True)
    ibroadcast_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    artist_id = Column(Integer, ForeignKey('artists.id'), nullable=False)
    year = Column(Integer)
    track_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album")

class Track(Base):
    """Track model."""
    __tablename__ = 'tracks'

    id = Column(Integer, primary_key=True)
    ibroadcast_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    artist_id = Column(Integer, ForeignKey('artists.id'), nullable=False)
    album_id = Column(Integer, ForeignKey('albums.id'), nullable=False)
    duration = Column(Integer)  # in seconds
    track_number = Column(Integer)
    year = Column(Integer)
    file_path = Column(String(500))  # local cache path if downloaded
    stream_url = Column(String(500))  # streaming URL
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    artist = relationship("Artist", back_populates="tracks")
    album = relationship("Album", back_populates="tracks")

class Playlist(Base):
    """Playlist model."""
    __tablename__ = 'playlists'

    id = Column(Integer, primary_key=True)
    ibroadcast_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    track_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    tracks = relationship("PlaylistTrack", back_populates="playlist")

class PlaylistTrack(Base):
    """Junction table for playlist tracks."""
    __tablename__ = 'playlist_tracks'

    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey('playlists.id'), nullable=False)
    track_id = Column(Integer, ForeignKey('tracks.id'), nullable=False)
    position = Column(Integer, nullable=False)

    # Relationships
    playlist = relationship("Playlist", back_populates="tracks")
    track = relationship("Track")

# Database setup
DATABASE_URL = f"sqlite:///{os.path.expanduser('~/.ibroadcast-tui/library.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database."""
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(os.path.expanduser('~/.ibroadcast-tui/library.db'))
    os.makedirs(db_dir, exist_ok=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database on import
init_db()