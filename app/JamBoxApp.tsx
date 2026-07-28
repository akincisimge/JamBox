"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Icon } from "../components/ui/Icon";
import { Logo } from "../components/ui/Logo";
import { RoomModal } from "../components/room/RoomModal";
import { SpotifySignInButton } from "../components/spotify/SpotifySignInButton";
import {
  clearSpotifySession,
  getSpotifyPlaylists,
  getSpotifyPlaylistTracks,
  readStoredSpotifyProfile,
  startSpotifyLogin,
} from "../lib/spotify/client";
import { initialMessages, initialQueue } from "../mocks/room";
import type {
  SpotifyPlaylist,
  SpotifyProfile,
  SpotifyTrack,
} from "../types/jambox";

export default function JamBoxApp() {
  const [spotifyProfile, setSpotifyProfile] =
    useState<SpotifyProfile | null>(null);

  const [spotifyPlaylists, setSpotifyPlaylists] =
    useState<SpotifyPlaylist[]>([]);
    const [selectedPlaylist, setSelectedPlaylist] =
  useState<SpotifyPlaylist | null>(null);

const [playlistTracks, setPlaylistTracks] =
  useState<SpotifyTrack[]>([]);

const [playlistLoading, setPlaylistLoading] =
  useState(false);

const [playlistError, setPlaylistError] =
  useState("");

  const [view, setView] = useState<"home" | "room">("home");
  const [modal, setModal] =
    useState<"create" | "join" | null>(null);
  const [roomName, setRoomName] =
    useState("Friday Night Mix");
  const [roomCode, setRoomCode] = useState("JAM-482");
  const [isPlaying, setIsPlaying] = useState(true);
  const [queue, setQueue] = useState(initialQueue);
  const [messages, setMessages] = useState(initialMessages);
  const [message, setMessage] = useState("");
  const [toast, setToast] = useState("");

  useEffect(() => {
    const savedProfile = readStoredSpotifyProfile();
    if (!savedProfile) return;

    const loadProfile = window.setTimeout(
      () => setSpotifyProfile(savedProfile),
      0,
    );

    return () => window.clearTimeout(loadProfile);
  }, []);

  useEffect(() => {
    if (!spotifyProfile) return;

    const loadPlaylists = async () => {
      try {
        setSpotifyPlaylists(await getSpotifyPlaylists());
      } catch (error) {
        console.error(
          "Spotify playlist hatası:",
          error
        );
      }
    };

    loadPlaylists();
  }, [spotifyProfile]);
const openSpotifyPlaylist = async (
  playlist: SpotifyPlaylist
) => {
  setSelectedPlaylist(playlist);
  setPlaylistTracks([]);
  setPlaylistError("");
  setPlaylistLoading(true);

  try {
    setPlaylistTracks(
      await getSpotifyPlaylistTracks(playlist.id)
    );
  } catch (error) {
    console.error(
      "Spotify şarkı listesi hatası:",
      error
    );

    setPlaylistError(
      "Bu çalma listesindeki şarkılar alınamadı."
    );
  } finally {
    setPlaylistLoading(false);
  }
};
  const loginWithSpotify = async () => {
    try {
      await startSpotifyLogin();
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : "Spotify girişi başlatılamadı."
      );
    }
  };

  const logoutFromSpotify = () => {
    clearSpotifySession();

    setSpotifyProfile(null);
    setSpotifyPlaylists([]);
  };

  const sortedQueue = useMemo(
    () => [...queue].sort((a, b) => b.votes - a.votes),
    [queue]
  );

  function openRoom(kind: "create" | "join") {
    setModal(kind);
  }

  function submitRoom(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (modal === "create") {
      setRoomCode(
        `JAM-${Math.floor(100 + Math.random() * 900)}`
      );
    }

    setModal(null);
    setView("room");
  }

  function vote(id: number) {
    setQueue((items) =>
      items.map((item) =>
        item.id === id
          ? { ...item, votes: item.votes + 1 }
          : item
      )
    );
  }

  function sendMessage(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!message.trim()) return;

    setMessages((items) => [
      ...items,
      {
        name: "You",
        text: message.trim(),
        color: "cream",
      },
    ]);

    setMessage("");
  }

  async function copyCode() {
    await navigator.clipboard?.writeText(roomCode);
    setToast("Room code copied");

    window.setTimeout(() => {
      setToast("");
    }, 1800);
  }

  if (view === "room") {
    return (
      <main className="site-shell room-page">
        <header className="topbar room-topbar">
          <Logo />

          <div className="room-identity">
            <span className="live-dot" />
            LIVE
            <strong>{roomName}</strong>
          </div>

          <button
            className="room-code"
            onClick={copyCode}
          >
            <span>{roomCode}</span>
            <Icon name="copy" size={17} />
          </button>

          <button
            className="ghost-button leave-button"
            onClick={() => setView("home")}
          >
            Leave room
          </button>
        </header>

        <section className="room-layout">
          <aside className="listeners-panel panel">
            <div className="section-heading">
              <h2>Listeners</h2>
              <span>4 online</span>
            </div>

            {[
              ["SA", "Simge", "Host", "purple"],
              ["MY", "Maya", "Listening", "coral"],
              ["AL", "Alex", "Listening", "blue"],
              ["JR", "Jordan", "Listening", "cream"],
            ].map(([initial, name, status, color]) => (
              <div className="listener" key={name}>
                <span className={`avatar ${color}`}>
                  {initial}
                </span>

                <span>
                  <strong>{name}</strong>
                  <small>{status}</small>
                </span>

                <i className="online-dot" />
              </div>
            ))}

            <button
              className="invite-button"
              onClick={copyCode}
            >
              <Icon name="plus" size={18} />
              Invite people
            </button>
          </aside>

          <section className="player-panel panel">
            <div className="now-playing-label">
              <span className="equalizer">
                <i />
                <i />
                <i />
              </span>
              NOW PLAYING
            </div>

            <div
              className="large-art sunset"
              aria-label="Abstract sunset album artwork"
            >
              <span>JM</span>
            </div>

            <div className="track-copy">
              <h1>Midnight Drive</h1>
              <p>Nova Lane</p>
            </div>

            <div className="progress">
              <span>1:45</span>
              <div>
                <i />
              </div>
              <span>3:48</span>
            </div>

            <div className="player-controls">
              <button aria-label="Previous track">
                ‹
              </button>

              <button
                className="main-play"
                onClick={() =>
                  setIsPlaying(!isPlaying)
                }
                aria-label={
                  isPlaying ? "Pause" : "Play"
                }
              >
                <Icon
                  name={isPlaying ? "pause" : "play"}
                  size={30}
                />
              </button>

              <button aria-label="Next track">
                ›
              </button>
            </div>

            <p className="host-note">
              Playback is controlled by the room host
            </p>
          </section>

          <aside className="chat-panel panel">
            <div className="section-heading">
              <h2>Room chat</h2>
              <span>
                {messages.length} messages
              </span>
            </div>

            <div className="messages">
              {messages.map((item, index) => (
                <div
                  className="message"
                  key={`${item.name}-${index}`}
                >
                  <span
                    className={`avatar small ${item.color}`}
                  >
                    {item.name.slice(0, 1)}
                  </span>

                  <div>
                    <strong>{item.name}</strong>
                    <p>{item.text}</p>
                  </div>
                </div>
              ))}
            </div>

            <form
              className="message-form"
              onSubmit={sendMessage}
            >
              <input
                value={message}
                onChange={(event) =>
                  setMessage(event.target.value)
                }
                placeholder="Say something…"
                aria-label="Chat message"
              />

              <button aria-label="Send message">
                <Icon name="send" size={19} />
              </button>
            </form>
          </aside>

          <section className="queue-panel panel">
            <div className="section-heading queue-heading">
              <div>
                <h2>Up next</h2>
                <p>
                  Vote to shape what plays next
                </p>
              </div>

              <button>
                <Icon name="plus" size={18} />
                Add a song
              </button>
            </div>

            <div className="queue-list">
              {sortedQueue.map((track, index) => (
                <article
                  className="queue-item"
                  key={track.id}
                >
                  <span className="queue-index">
                    0{index + 1}
                  </span>

                  <span
                    className={`mini-art ${track.art}`}
                  />

                  <div className="queue-track">
                    <strong>{track.title}</strong>
                    <small>{track.artist}</small>
                  </div>

                  <span className="added-by">
                    Added by{" "}
                    <strong>{track.addedBy}</strong>
                  </span>

                  <button
                    className="vote-button"
                    onClick={() => vote(track.id)}
                    aria-label={`Vote for ${track.title}`}
                  >
                    ▲{" "}
                    <strong>{track.votes}</strong>
                  </button>
                </article>
              ))}
            </div>
          </section>
        </section>

        {toast && (
          <div className="toast">{toast}</div>
        )}
      </main>
    );
  }

  return (
    <main className="site-shell" id="home">
      <header className="topbar">
        <Logo />

        <nav aria-label="Main navigation">
          <a className="active" href="#home">
            Home
          </a>
          <a href="#features">Explore</a>
          <a href="#how">How it works</a>
        </nav>

        <SpotifySignInButton
          profile={spotifyProfile}
          onClick={
            spotifyProfile
              ? logoutFromSpotify
              : loginWithSpotify
          }
        />
      </header>

      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">
            <i /> REAL-TIME LISTENING ROOMS
          </span>

          <h1>
            Listen
            <br />
            <span>Together.</span>
          </h1>

          <p>
            Create a room, invite your people, and
            shape the queue together—live.
          </p>

          <div className="hero-actions">
            <button
              className="primary-button"
              onClick={() => openRoom("create")}
            >
              <Icon name="plus" />
              Create a room
            </button>

            <button
              className="secondary-button"
              onClick={() => openRoom("join")}
            >
              <Icon name="hash" />
              Join with code
            </button>
          </div>

          <div className="social-proof">
            <div className="avatar-stack">
              <span className="avatar purple">S</span>
              <span className="avatar coral">M</span>
              <span className="avatar blue">A</span>
              <span className="avatar cream">J</span>
            </div>

            <p>
              <strong>
                Built for shared moments
              </strong>
              <br />
              No awkward playlist handoffs.
            </p>
          </div>
        </div>

        <div className="hero-card">
          <div className="card-glow" />

          <div className="live-card">
            <div className="live-card-top">
              <span>
                <i /> LIVE ROOM
              </span>
              <strong>4 listeners</strong>
            </div>

            <div className="listener-row">
              <span className="avatar purple">
                SA
              </span>
              <span className="avatar coral">
                MY
              </span>
              <span className="avatar blue">
                AL
              </span>
              <span className="avatar cream">
                JR
              </span>
            </div>

            <div className="mini-player">
              <div className="album-art sunset">
                <span>JM</span>
              </div>

              <div className="mini-player-body">
                <div>
                  <h2>Midnight Drive</h2>
                  <p>Nova Lane</p>
                </div>

                <div className="mini-progress">
                  <span />
                  <i />
                </div>

                <div className="mini-controls">
                  <button>‹</button>

                  <button
                    className="play"
                    onClick={() =>
                      setIsPlaying(!isPlaying)
                    }
                  >
                    <Icon
                      name={
                        isPlaying
                          ? "pause"
                          : "play"
                      }
                      size={25}
                    />
                  </button>

                  <button>›</button>
                </div>
              </div>
            </div>

            <div className="up-next">
              <h3>Up next</h3>

              {queue.map((track, index) => (
                <div
                  className="next-row"
                  key={track.id}
                >
                  <span
                    className={`mini-art ${track.art}`}
                  />
                  <span className="number">
                    {index + 1}
                  </span>

                  <span>
                    <strong>{track.title}</strong>
                    <small>{track.artist}</small>
                  </span>

                  <small>
                    added by
                    <br />
                    <strong>
                      {track.addedBy}
                    </strong>
                  </small>

                  <b>⋮</b>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {spotifyProfile && (
        <section
          className="spotify-playlists-section"
          id="spotify-playlists"
        >
          <div className="spotify-section-heading">
            <div>
              <span>YOUR SPOTIFY LIBRARY</span>
              <h2>Çalma listelerin</h2>
            </div>

            <strong>
              {spotifyPlaylists.length} liste
            </strong>
          </div>

          {spotifyPlaylists.length > 0 ? (
            <div className="spotify-playlist-grid">
              {spotifyPlaylists.map(
                (playlist) => (
                  <article
  className="spotify-playlist-card"
  key={playlist.id}
  onClick={() =>
    openSpotifyPlaylist(playlist)
  }
  role="button"
  tabIndex={0}
  aria-label={`${playlist.name} çalma listesini aç`}
>
                    {playlist.images?.[0]
                      ?.url ? (
                      <img
                        src={
                          playlist.images[0].url
                        }
                        alt={playlist.name}
                      />
                    ) : (
                      <div className="playlist-placeholder">
                        <Icon
                          name="play"
                          size={32}
                        />
                      </div>
                    )}

                    <div>
                      <h3>{playlist.name}</h3>
                      <p>
  {playlist.items?.total ??
    playlist.tracks?.total ??
    0}{" "}
  şarkı
</p>
                      <small>
                        {
                          playlist.owner
                            .display_name
                        }
                      </small>
                    </div>
                  </article>
                )
              )}
            </div>
          ) : (
            <p className="spotify-empty-message">
              Spotify çalma listesi bulunamadı.
            </p>
          )}
        </section>
      )}
{selectedPlaylist && (
  <section className="spotify-track-panel">
    <div className="track-panel-header">
      <div className="track-panel-playlist">
        {selectedPlaylist.images?.[0]?.url && (
          <img
            src={selectedPlaylist.images[0].url}
            alt={selectedPlaylist.name}
          />
        )}

        <div>
          <span>SEÇİLEN ÇALMA LİSTESİ</span>
          <h2>{selectedPlaylist.name}</h2>
          <p>
            {selectedPlaylist.items?.total ??
              selectedPlaylist.tracks?.total ??
              0}{" "}
            şarkı
          </p>
        </div>
      </div>

      <button
        className="close-track-panel"
        onClick={() => {
          setSelectedPlaylist(null);
          setPlaylistTracks([]);
          setPlaylistError("");
        }}
        aria-label="Şarkı listesini kapat"
      >
        ×
      </button>
    </div>

    {playlistLoading && (
      <p className="playlist-loading">
        Şarkılar Spotify’dan getiriliyor...
      </p>
    )}

    {playlistError && (
      <p className="playlist-error">
        {playlistError}
      </p>
    )}

    {!playlistLoading &&
      !playlistError &&
      playlistTracks.length === 0 && (
        <p className="playlist-empty">
          Bu çalma listesinde gösterilebilecek şarkı bulunamadı.
        </p>
      )}

    {!playlistLoading &&
      !playlistError &&
      playlistTracks.length > 0 && (
        <div className="spotify-track-list">
          {playlistTracks.map((track, index) => (
            <article
              className="spotify-track-row"
              key={track.id}
            >
              <span className="track-number">
                {String(index + 1).padStart(2, "0")}
              </span>

              {track.album.images?.[0]?.url ? (
                <img
                  src={track.album.images[0].url}
                  alt={track.album.name}
                />
              ) : (
                <div className="track-image-placeholder">
                  <Icon name="play" size={18} />
                </div>
              )}

              <div className="spotify-track-info">
                <strong>{track.name}</strong>
                <span>
                  {track.artists
                    .map((artist) => artist.name)
                    .join(", ")}
                </span>
              </div>

              <span className="track-duration">
                {Math.floor(track.duration_ms / 60000)}:
                {String(
                  Math.floor(
                    (track.duration_ms % 60000) / 1000
                  )
                ).padStart(2, "0")}
              </span>

              <a
                href={`https://open.spotify.com/track/${track.id}`}
                target="_blank"
                rel="noreferrer"
              >
                Spotify’da aç
              </a>
            </article>
          ))}
        </div>
      )}
  </section>
)}
      <section
        className="feature-strip"
        id="features"
      >
        <article>
          <span>01</span>
          <h2>One room, one vibe</h2>
          <p>
            Everyone hears the same moment
            together.
          </p>
        </article>

        <article>
          <span>02</span>
          <h2>The queue is democratic</h2>
          <p>
            Add tracks and vote favorites to the
            top.
          </p>
        </article>

        <article>
          <span>03</span>
          <h2>React in real time</h2>
          <p>
            Chat, react, and turn listening into a
            memory.
          </p>
        </article>
      </section>

      <section className="how-section" id="how">
        <p>HOW JAMBOX WORKS</p>
        <h2>
          Three clicks. One shared soundtrack.
        </h2>

        <button
          className="text-link"
          onClick={() => openRoom("create")}
        >
          Start your first room
          <Icon name="arrow" />
        </button>
      </section>

      {modal && (
        <RoomModal
          mode={modal}
          roomName={roomName}
          roomCode={roomCode}
          onRoomNameChange={setRoomName}
          onRoomCodeChange={setRoomCode}
          onClose={() => setModal(null)}
          onSubmit={submitRoom}
        />
      )}
    </main>
  );
}
