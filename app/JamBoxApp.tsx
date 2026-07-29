"use client";

import {
  type CSSProperties,
  FormEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Icon } from "../components/ui/Icon";
import { Logo } from "../components/ui/Logo";
import { RoomModal } from "../components/room/RoomModal";
import { SpotifySignInButton } from "../components/spotify/SpotifySignInButton";
import {
  closeJamBoxRoom,
  connectToJamBoxRoom,
  createJamBoxRoom,
  getJamBoxRoom,
  JamBoxApiError,
  joinJamBoxRoom,
  leaveJamBoxRoom,
  registerJamBoxUser,
  sendJamBoxMessage,
  updateJamBoxPlayback,
} from "../lib/jambox/client";
import {
  clearSpotifySession,
  getSpotifyPlaylists,
  getSpotifyPlaylistTracks,
  readStoredSpotifyProfile,
  searchSpotifyTracks,
  startSpotifyLogin,
} from "../lib/spotify/client";
import {
  activateSpotifyRoomPlayer,
  applyRoomPlayback,
  createSpotifyRoomPlayer,
  currentPlaybackPosition,
  pauseSpotifyPlayback,
  skipSpotifyPlayback,
} from "../lib/spotify/playback";
import { initialQueue } from "../mocks/room";
import type {
  ChatMessage,
  JamBoxRoom,
  SpotifyPlaylist,
  SpotifyProfile,
  SpotifyTrack,
} from "../types/jambox";

const ACTIVE_ROOM_STORAGE_KEY = "jambox_active_room_code";
const roomPlaylistStorageKey = (roomCode: string) =>
  `jambox_room_playlist:${roomCode}`;

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
const [trackSearch, setTrackSearch] = useState("");
const [searchResults, setSearchResults] = useState<SpotifyTrack[]>([]);
const [searchLoading, setSearchLoading] = useState(false);

  const [view, setView] = useState<"home" | "room">("home");
  const [modal, setModal] =
    useState<"create" | "join" | null>(null);
  const [roomName, setRoomName] =
    useState("Friday Night Mix");
  const [roomCode, setRoomCode] = useState("JAM-482");
  const [activeRoom, setActiveRoom] = useState<JamBoxRoom | null>(null);
  const [jamBoxUserId, setJamBoxUserId] = useState("");
  const [roomError, setRoomError] = useState("");
  const [roomSubmitting, setRoomSubmitting] = useState(false);
  const [songPickerOpen, setSongPickerOpen] = useState(false);
  const [spotifyDeviceId, setSpotifyDeviceId] = useState("");
  const [roomAudioEnabled, setRoomAudioEnabled] = useState(false);
  const spotifyPlayerRef = useRef<SpotifyPlayer | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [playbackClock, setPlaybackClock] = useState(0);
  const [demoIsPlaying, setDemoIsPlaying] = useState(true);
  const [queue] = useState(initialQueue);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState("");
  const [toast, setToast] = useState("");
  const musicPanelWidth = 460;
  const [musicPanelCollapsed, setMusicPanelCollapsed] = useState(false);
  const [themeColors, setThemeColors] = useState({ primary: "#ff5c8a", secondary: "#7c3aed", deep: "#090b1d" });

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

    let cancelled = false;

    const restoreActiveRoom = async () => {
      const savedRoomCode = window.localStorage.getItem(
        ACTIVE_ROOM_STORAGE_KEY,
      );
      if (!savedRoomCode) return;

      try {
        const user = await registerJamBoxUser(spotifyProfile);
        const room = await getJamBoxRoom(savedRoomCode);
        const isMember = room.members.some(
          (member) => member.user_id === user.id,
        );

        if (!isMember) {
          window.localStorage.removeItem(ACTIVE_ROOM_STORAGE_KEY);
          return;
        }

        if (cancelled) return;
        setJamBoxUserId(user.id);
        setActiveRoom(room);
        setMessages(room.messages);
        setRoomName(room.name);
        setRoomCode(room.code);
        setView("room");
      } catch {
        window.localStorage.removeItem(ACTIVE_ROOM_STORAGE_KEY);
      }
    };

    void restoreActiveRoom();

    return () => {
      cancelled = true;
    };
  }, [spotifyProfile]);

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

  const activeRoomCode = activeRoom?.code;

  useEffect(() => {
    if (activeRoomCode) {
      window.localStorage.setItem(ACTIVE_ROOM_STORAGE_KEY, activeRoomCode);
    }
  }, [activeRoomCode]);

  useEffect(() => {
    if (
      view !== "room" ||
      !activeRoomCode ||
      spotifyPlaylists.length === 0 ||
      selectedPlaylist
    ) {
      return;
    }

    const savedPlaylistId = window.localStorage.getItem(
      roomPlaylistStorageKey(activeRoomCode),
    );
    const savedPlaylist = spotifyPlaylists.find(
      (playlist) => playlist.id === savedPlaylistId,
    );
    if (!savedPlaylist) return;

    let cancelled = false;
    setPlaylistLoading(true);
    setPlaylistError("");

    void getSpotifyPlaylistTracks(savedPlaylist.id)
      .then((tracks) => {
        if (!cancelled) {
          setSelectedPlaylist(savedPlaylist);
          setPlaylistTracks(tracks);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setPlaylistError("Bu çalma listesindeki şarkılar alınamadı.");
        }
      })
      .finally(() => {
        if (!cancelled) setPlaylistLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeRoomCode, selectedPlaylist, spotifyPlaylists, view]);

  useEffect(() => {
    if (view !== "room" || !activeRoomCode || !jamBoxUserId) {
      return;
    }

    return connectToJamBoxRoom(jamBoxUserId, activeRoomCode, {
      onRoomUpdated: async () => {
        try {
          setActiveRoom(await getJamBoxRoom(activeRoomCode));
        } catch (error) {
          console.error("Oda güncellenemedi:", error);
        }
      },
      onPlaybackUpdated: async () => {
        try {
          setActiveRoom(await getJamBoxRoom(activeRoomCode));
        } catch (error) {
          console.error("Oynatma durumu güncellenemedi:", error);
        }
      },
      onMessageCreated: (newMessage) => {
        setMessages((items) =>
          items.some((item) => item.id === newMessage.id)
            ? items
            : [...items, newMessage],
        );
      },
      onRoomClosed: () => {
        window.localStorage.removeItem(ACTIVE_ROOM_STORAGE_KEY);
        setActiveRoom(null);
        setMessages([]);
        setView("home");
        setToast("Oda sahibi odayı kapattı.");
      },
    });
  }, [activeRoomCode, jamBoxUserId, view]);

  useEffect(() => {
    if (view !== "room" || !spotifyProfile) return;

    let stopped = false;
    void createSpotifyRoomPlayer((message) => setToast(message))
      .then(({ player, deviceId }) => {
        if (stopped) {
          player.disconnect();
          return;
        }
        spotifyPlayerRef.current = player;
        setSpotifyDeviceId(deviceId);
        player.addListener("not_ready", ({ device_id }) => {
          if (device_id === deviceId) {
            setSpotifyDeviceId("");
            setRoomAudioEnabled(false);
          }
        });
      })
      .catch((error) => {
        setToast(
          error instanceof Error
            ? error.message
            : "Spotify oynatıcısı başlatılamadı.",
        );
      });

    return () => {
      stopped = true;
      spotifyPlayerRef.current?.disconnect();
      spotifyPlayerRef.current = null;
      setSpotifyDeviceId("");
      setRoomAudioEnabled(false);
    };
  }, [spotifyProfile, view]);

  useEffect(() => {
    const artwork = activeRoom?.playback?.album_image_url;
    if (!artwork) {
      setThemeColors({ primary: "#ff5c8a", secondary: "#7c3aed", deep: "#090b1d" });
      return;
    }

    const image = new Image();
    image.crossOrigin = "anonymous";
    image.src = artwork;
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = 24;
      canvas.height = 24;
      const context = canvas.getContext("2d", { willReadFrequently: true });
      if (!context) return;
      context.drawImage(image, 0, 0, 24, 24);
      const pixels = context.getImageData(0, 0, 24, 24).data;
      const colors: Array<{ r: number; g: number; b: number; score: number }> = [];
      for (let index = 0; index < pixels.length; index += 16) {
        const r = pixels[index];
        const g = pixels[index + 1];
        const b = pixels[index + 2];
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const saturation = max - min;
        const brightness = (r + g + b) / 3;
        if (brightness > 28 && brightness < 235) {
          colors.push({ r, g, b, score: saturation * 1.6 + brightness * .25 });
        }
      }
      colors.sort((a, b) => b.score - a.score);
      const primary = colors[0] ?? { r: 255, g: 92, b: 138 };
      const secondary =
        colors.find((color) =>
          Math.abs(color.r - primary.r) +
          Math.abs(color.g - primary.g) +
          Math.abs(color.b - primary.b) > 120
        ) ?? colors[Math.min(4, colors.length - 1)] ?? { r: 124, g: 58, b: 237 };
      setThemeColors({
        primary: `rgb(${primary.r} ${primary.g} ${primary.b})`,
        secondary: `rgb(${secondary.r} ${secondary.g} ${secondary.b})`,
        deep: `rgb(${Math.round(primary.r * .11)} ${Math.round(primary.g * .11)} ${Math.round(primary.b * .11)})`,
      });
    };
  }, [activeRoom?.playback?.album_image_url]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: messages.length > 1 ? "smooth" : "auto",
      block: "end",
    });
  }, [messages.length]);

  const playback = activeRoom?.playback ?? null;
  const canControlMusic =
    activeRoom?.members.find((member) => member.user_id === jamBoxUserId)
      ?.can_control_music ?? false;
  const lastAppliedPlaybackRef = useRef("");

  useEffect(() => {
    if (!playback || !spotifyDeviceId || !roomAudioEnabled) return;
    const playbackKey = `${spotifyDeviceId}:${playback.version}`;
    if (lastAppliedPlaybackRef.current === playbackKey) return;
    lastAppliedPlaybackRef.current = playbackKey;

    void applyRoomPlayback(playback, spotifyDeviceId).catch((error) => {
      setToast(
        error instanceof Error
          ? error.message
          : "Ortak oynatma uygulanamadı.",
      );
    });
  }, [playback, roomAudioEnabled, spotifyDeviceId]);

  useEffect(() => {
    if (!playback?.is_playing) return;
    const timer = window.setInterval(() => setPlaybackClock(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [playback?.is_playing]);
const openSpotifyPlaylist = async (
  playlist: SpotifyPlaylist
) => {
  setSelectedPlaylist(playlist);
  if (activeRoomCode) {
    window.localStorage.setItem(
      roomPlaylistStorageKey(activeRoomCode),
      playlist.id,
    );
  }
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
    window.localStorage.removeItem(ACTIVE_ROOM_STORAGE_KEY);

    setSpotifyProfile(null);
    setSpotifyPlaylists([]);
    setActiveRoom(null);
    setMessages([]);
    setView("home");
  };

  function openRoom(kind: "create" | "join") {
    setRoomError("");
    setModal(kind);
  }

  async function submitRoom(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!spotifyProfile) {
      setRoomError("Önce Spotify ile giriş yapmalısın.");
      return;
    }

    setRoomSubmitting(true);
    setRoomError("");

    try {
      const user = await registerJamBoxUser(spotifyProfile);
      const room =
        modal === "create"
          ? await createJamBoxRoom(user.id, roomName)
          : await joinJamBoxRoom(user.id, roomCode);

      setJamBoxUserId(user.id);
      setActiveRoom(room);
      setMessages(room.messages);
      setRoomName(room.name);
      setRoomCode(room.code);
      window.localStorage.setItem(ACTIVE_ROOM_STORAGE_KEY, room.code);
      setModal(null);
      setView("room");
    } catch (error) {
      setRoomError(
        error instanceof JamBoxApiError
          ? error.message
          : "Backend bağlantısı kurulamadı. Docker servislerini kontrol et.",
      );
    } finally {
      setRoomSubmitting(false);
    }
  }

  async function exitRoom() {
    if (!activeRoom || !jamBoxUserId) {
      window.localStorage.removeItem(ACTIVE_ROOM_STORAGE_KEY);
      setView("home");
      return;
    }

    try {
      if (activeRoom.owner_id === jamBoxUserId) {
        await closeJamBoxRoom(jamBoxUserId, activeRoom.code);
      } else {
        await leaveJamBoxRoom(jamBoxUserId, activeRoom.code);
      }

      window.localStorage.removeItem(ACTIVE_ROOM_STORAGE_KEY);
      setActiveRoom(null);
      setMessages([]);
      setView("home");
    } catch (error) {
      setToast(
        error instanceof JamBoxApiError
          ? error.message
          : "Odadan çıkılamadı.",
      );
    }
  }

  async function playTrackTogether(track: SpotifyTrack) {
    if (!activeRoom || !jamBoxUserId) return;
    try {
      let player = spotifyPlayerRef.current;
      let deviceId = spotifyDeviceId;

      if (!player || !deviceId) {
        const created = await createSpotifyRoomPlayer((message) => setToast(message));
        player = created.player;
        deviceId = created.deviceId;
        spotifyPlayerRef.current = player;
        setSpotifyDeviceId(deviceId);
      }

      try {
        await activateSpotifyRoomPlayer(player, deviceId);
      } catch (error) {
        const isMissingDevice =
          error instanceof Error &&
          (error.message.includes("Device not found") ||
            error.message.includes("404"));
        if (!isMissingDevice) throw error;

        player.disconnect();
        const recreated = await createSpotifyRoomPlayer((message) => setToast(message));
        player = recreated.player;
        deviceId = recreated.deviceId;
        spotifyPlayerRef.current = player;
        setSpotifyDeviceId(deviceId);
        await activateSpotifyRoomPlayer(player, deviceId);
      }

      setRoomAudioEnabled(true);
      const room = await updateJamBoxPlayback(jamBoxUserId, activeRoom.code, {
        spotify_uri: track.uri,
        spotify_track_id: track.id,
        queue_uris: playlistTracks.some((item) => item.uri === track.uri)
          ? playlistTracks.map((item) => item.uri)
          : [track.uri, ...playlistTracks.map((item) => item.uri)],
        title: track.name,
        artist: track.artists.map((artist) => artist.name).join(", "),
        album_image_url: track.album.images?.[0]?.url ?? null,
        duration_ms: track.duration_ms,
        position_ms: 0,
        is_playing: true,
      });
      setActiveRoom(room);
      setSongPickerOpen(false);
    } catch (error) {
      setToast(
        error instanceof JamBoxApiError
          ? error.message
          : "Şarkı başlatılamadı.",
      );
    }
  }

  async function enableRoomAudio() {
    if (!spotifyPlayerRef.current || !spotifyDeviceId) {
      setToast("Spotify oynatıcısı henüz hazırlanıyor.");
      return;
    }
    try {
      await activateSpotifyRoomPlayer(
        spotifyPlayerRef.current,
        spotifyDeviceId,
      );
      setRoomAudioEnabled(true);
      if (playback) {
        lastAppliedPlaybackRef.current = "";
        await applyRoomPlayback(playback, spotifyDeviceId);
        lastAppliedPlaybackRef.current = `${spotifyDeviceId}:${playback.version}`;
      }
      setToast("Ortak ses etkinleştirildi.");
    } catch (error) {
      setToast(
        error instanceof Error ? error.message : "Ortak ses etkinleştirilemedi.",
      );
    }
  }

  async function toggleRoomPlayback() {
    if (!activeRoom?.playback || !jamBoxUserId) return;
    const current = activeRoom.playback;
    try {
      if (current.is_playing && spotifyDeviceId) {
        await pauseSpotifyPlayback(spotifyDeviceId);
      }

      setActiveRoom(
        await updateJamBoxPlayback(jamBoxUserId, activeRoom.code, {
          spotify_uri: current.spotify_uri,
          spotify_track_id: current.spotify_track_id,
          queue_uris: current.queue_uris,
          title: current.title,
          artist: current.artist,
          album_image_url: current.album_image_url,
          duration_ms: current.duration_ms,
          position_ms: Math.floor(currentPlaybackPosition(current)),
          is_playing: !current.is_playing,
        }),
      );
    } catch (error) {
      setToast(
        error instanceof JamBoxApiError
          ? error.message
          : "Oynatma durumu değiştirilemedi.",
      );
    }
  }

  async function skipRoomTrack(direction: "previous" | "next") {
    if (!activeRoom || !jamBoxUserId || !spotifyDeviceId) return;
    if (!canControlMusic) {
      setToast("Bu odada müzik kontrol yetkin yok.");
      return;
    }
    try {
      const state = await skipSpotifyPlayback(direction, spotifyDeviceId);
      const track = state.track;
      setActiveRoom(
        await updateJamBoxPlayback(jamBoxUserId, activeRoom.code, {
          spotify_uri: track.uri,
          spotify_track_id: track.id,
          queue_uris: activeRoom.playback?.queue_uris ?? [track.uri],
          title: track.name,
          artist: track.artists.map((artist) => artist.name).join(", "),
          album_image_url: track.album.images?.[0]?.url ?? null,
          duration_ms: track.duration_ms,
          position_ms: state.positionMs,
          is_playing: state.isPlaying,
        }),
      );
    } catch (error) {
      setToast(
        error instanceof Error
          ? error.message
          : "Spotify şarkısı değiştirilemedi.",
      );
    }
  }

  function formatMessageTime(timestamp: string): string {
    return new Intl.DateTimeFormat("tr-TR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(timestamp));
  }

  function formatTime(milliseconds: number): string {
    const seconds = Math.floor(milliseconds / 1000);
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  }

  const displayedPosition = useMemo(
    () =>
      playback
        ? Math.min(
            currentPlaybackPosition(playback) + playbackClock * 0,
            playback.duration_ms,
          )
        : 0,
    [playback, playbackClock],
  );

  async function playRandomTrack() {
    if (!canControlMusic) {
      setToast("Bu odada müzik kontrol yetkin yok.");
      return;
    }
    if (playlistTracks.length === 0) {
      setToast("Önce bir Spotify çalma listesi seç.");
      return;
    }

    const randomTrack =
      playlistTracks[Math.floor(Math.random() * playlistTracks.length)];
    await playTrackTogether(randomTrack);
  }

  async function searchTracks(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!trackSearch.trim()) return;

    setSearchLoading(true);
    try {
      setSearchResults(await searchSpotifyTracks(trackSearch));
    } catch (error) {
      setToast(
        error instanceof Error
          ? error.message
          : "Spotify araması yapılamadı.",
      );
    } finally {
      setSearchLoading(false);
    }
  }

  async function sendMessage(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!message.trim()) return;

    const text = message.trim();
    setMessage("");
    try {
      const sentMessage = await sendJamBoxMessage(jamBoxUserId, roomCode, text);
      setMessages((items) =>
        items.some((item) => item.id === sentMessage.id)
          ? items
          : [...items, sentMessage],
      );
    } catch (error) {
      setMessage(text);
      setToast(
        error instanceof JamBoxApiError
          ? error.message
          : "Mesaj gönderilemedi.",
      );
    }
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
      <main
        className={`site-shell room-page${
          musicPanelCollapsed ? " music-panel-collapsed" : ""
        }`}
        style={
          {
            "--room-album-art": playback?.album_image_url
              ? `url("${playback.album_image_url}")`
              : "none",
            "--music-panel-width": `${musicPanelWidth}px`,
            "--album-primary": themeColors.primary,
            "--album-secondary": themeColors.secondary,
            "--album-deep": themeColors.deep,
          } as CSSProperties
        }
      >
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
            onClick={exitRoom}
          >
            {activeRoom?.owner_id === jamBoxUserId
              ? "Close room"
              : "Leave room"}
          </button>
        </header>

        <button
          className="music-drawer-toggle"
          onClick={() => setMusicPanelCollapsed((collapsed) => !collapsed)}
          aria-label={musicPanelCollapsed ? "Müzik panelini aç" : "Müzik panelini kapat"}
          title={musicPanelCollapsed ? "Müzik panelini aç" : "Müzik panelini kapat"}
        >
          {musicPanelCollapsed ? "‹" : "›"}
        </button>

        <section className="room-layout">
          <aside className="listeners-panel panel">
            <div className="section-heading">
              <h2>Listeners</h2>
              <span>{activeRoom?.members.length ?? 0} online</span>
            </div>

            {(activeRoom?.members ?? []).map((member, index) => (
              <div className="listener" key={member.user_id}>
                <span
                  className={`avatar ${
                    ["purple", "coral", "blue", "cream"][index % 4]
                  }`}
                >
                  {member.user.display_name.slice(0, 2).toUpperCase()}
                </span>

                <span>
                  <strong>{member.user.display_name}</strong>
                  <small>{member.is_owner ? "Host" : "Listening"}</small>
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

          <section className={`player-panel panel${playback?.is_playing ? " is-playing" : ""}`}>
            <div className="now-playing-label">
              <span className="equalizer">
                <i />
                <i />
                <i />
              </span>
              NOW PLAYING
            </div>

            {playback?.album_image_url ? (
              <img
                key={playback.spotify_track_id}
                className="large-art"
                src={playback.album_image_url}
                alt={`${playback.title} albüm kapağı`}
              />
            ) : (
              <div
                className="large-art sunset"
                aria-label="Henüz şarkı seçilmedi"
              >
                <span>JM</span>
              </div>
            )}

            <div className="track-copy">
              <h1>{playback?.title ?? "Bir şarkı seç"}</h1>
              <p>{playback?.artist ?? "Ortak dinleme başlamaya hazır"}</p>
            </div>

            <div className="progress">
              <span>{formatTime(displayedPosition)}</span>
              <div>
                <i
                  style={{
                    width: playback
                      ? `${(displayedPosition / playback.duration_ms) * 100}%`
                      : "0%",
                  }}
                />
              </div>
              <span>{formatTime(playback?.duration_ms ?? 0)}</span>
            </div>

            <div className="player-controls">
              <button
                onClick={() => skipRoomTrack("previous")}
                disabled={!playback || !roomAudioEnabled || !canControlMusic}
                aria-label="Previous track"
              >
                ‹
              </button>

              <button
                className="main-play"
                onClick={toggleRoomPlayback}
                disabled={!playback}
                aria-label={
                  playback?.is_playing ? "Pause" : "Play"
                }
              >
                <Icon
                  name={playback?.is_playing ? "pause" : "play"}
                  size={30}
                />
              </button>

              <button
                onClick={() => skipRoomTrack("next")}
                disabled={!playback || !roomAudioEnabled || !canControlMusic}
                aria-label="Next track"
              >
                ›
              </button>
            </div>

            <p className="host-note">
              {roomAudioEnabled ? (
                "Spotify bu odada senkronize ediliyor"
              ) : (
                <button onClick={enableRoomAudio}>
                  Sesi etkinleştir
                </button>
              )}
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
                  key={item.id}
                >
                  <span
                    className={`avatar small ${
                      ["purple", "coral", "blue", "cream"][index % 4]
                    }`}
                  >
                    {item.user.display_name.slice(0, 1).toUpperCase()}
                  </span>

                  <div>
                    <div className="message-meta">
                      <strong>{item.user.display_name}</strong>
                      <time dateTime={item.created_at}>
                        {formatMessageTime(item.created_at)}
                      </time>
                    </div>
                    <p>{item.text}</p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} aria-hidden="true" />
            </div>

            <div className="chat-quick-actions" aria-label="Hızlı emojiler">
              {["🎵", "🔥", "💜", "✨", "😂"].map((emoji) => (
                <button
                  type="button"
                  key={emoji}
                  onClick={() => setMessage((current) => `${current}${emoji}`)}
                  aria-label={`${emoji} emojisini mesaja ekle`}
                >
                  {emoji}
                </button>
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

          <section className="activities-panel panel" aria-labelledby="activities-title">
            <div className="section-heading">
              <div>
                <span className="music-panel-eyebrow">PLAY TOGETHER</span>
                <h2 id="activities-title">Activities</h2>
              </div>
              <span>More coming soon</span>
            </div>
            <div className="activity-grid">
              <button className="activity-card" disabled>
                <span className="activity-icon">× ○</span>
                <strong>Tic-Tac-Toe</strong>
                <small>Classic 3×3 game</small>
                <b>Coming soon</b>
              </button>
              <button className="activity-card" disabled>
                <span className="activity-icon">● ●</span>
                <strong>Connect Four</strong>
                <small>Four in a row</small>
                <b>Coming soon</b>
              </button>
              <button className="activity-card" disabled>
                <span className="activity-icon">▥</span>
                <strong>Polls</strong>
                <small>Ask, vote, decide</small>
                <b>Coming soon</b>
              </button>
              <button className="activity-card" disabled>
                <span className="activity-icon">＋</span>
                <strong>More activities</strong>
                <small>Built for the whole room</small>
                <b>Coming soon</b>
              </button>
            </div>
          </section>

          <section className="queue-panel panel music-library-panel">
            <div className="section-heading queue-heading">
              <div>
                <span className="music-panel-eyebrow">ROOM MUSIC</span>
                <h2>{selectedPlaylist?.name ?? "Bir çalma listesi seç"}</h2>
                <p>
                  {selectedPlaylist
                    ? `${playlistTracks.length} gerçek Spotify şarkısı`
                    : "Oda için kullanılacak Spotify listesini belirle."}
                </p>
              </div>

              <div className="music-panel-actions">
                {selectedPlaylist && (
                  <button
                    onClick={playRandomTrack}
                    disabled={!canControlMusic || playlistTracks.length === 0}
                  >
                    Karışık çal
                  </button>
                )}
                <button
                  onClick={() => {
                    if (activeRoomCode) {
                      window.localStorage.removeItem(
                        roomPlaylistStorageKey(activeRoomCode),
                      );
                    }
                    setSelectedPlaylist(null);
                    setPlaylistTracks([]);
                    setPlaylistError("");
                    setSongPickerOpen(true);
                  }}
                >
                  <Icon name="plus" size={18} />
                  {selectedPlaylist ? "Başka liste seç" : "Liste seç"}
                </button>
              </div>
            </div>

            {selectedPlaylist ? (
              <>
                {playlistLoading && <p>Şarkılar yükleniyor...</p>}
                {playlistError && <p className="music-panel-error">{playlistError}</p>}
                <div className="room-track-list">
                  {playlistTracks.map((track, index) => (
                    <button
                      className="room-track-row"
                      key={track.id}
                      onClick={() => playTrackTogether(track)}
                      disabled={!canControlMusic}
                      title={
                        canControlMusic
                          ? "Bu şarkıyı odada çal"
                          : "Müzik kontrol yetkin yok"
                      }
                    >
                      <span className="queue-index">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      {track.album.images?.[0]?.url ? (
                        <img src={track.album.images[0].url} alt="" />
                      ) : (
                        <span className="track-image-placeholder" />
                      )}
                      <span className="room-track-copy">
                        <strong>{track.name}</strong>
                        <small>
                          {track.artists.map((artist) => artist.name).join(", ")}
                        </small>
                      </span>
                      <Icon name="play" size={18} />
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <button
                className="empty-music-library"
                onClick={() => setSongPickerOpen(true)}
              >
                <Icon name="plus" size={22} />
                Spotify çalma listesi seç
              </button>
            )}

            <div className="spotify-room-search">
              <div>
                <h3>Listede olmayan bir şarkıyı ara</h3>
                <p>Spotify kataloğunda sanatçı veya şarkı adıyla arama yap.</p>
              </div>
              <form onSubmit={searchTracks}>
                <input
                  value={trackSearch}
                  onChange={(event) => setTrackSearch(event.target.value)}
                  placeholder="Şarkı veya sanatçı ara"
                  aria-label="Spotify şarkısı ara"
                />
                <button disabled={searchLoading || !trackSearch.trim()}>
                  {searchLoading ? "Aranıyor…" : "Ara"}
                </button>
              </form>

              {searchResults.length > 0 && (
                <div className="search-track-results">
                  {searchResults.map((track) => (
                    <button
                      key={track.id}
                      onClick={() => playTrackTogether(track)}
                      disabled={!canControlMusic}
                    >
                      {track.album.images?.[0]?.url && (
                        <img src={track.album.images[0].url} alt="" />
                      )}
                      <span>
                        <strong>{track.name}</strong>
                        <small>
                          {track.artists.map((artist) => artist.name).join(", ")}
                        </small>
                      </span>
                      <Icon name="play" size={17} />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </section>
        </section>

        {toast && (
          <div className="toast">{toast}</div>
        )}

        {songPickerOpen && (
          <div className="song-picker-backdrop">
            <section className="song-picker panel">
              <div className="section-heading">
                <h2>Birlikte çal</h2>
                <button
                  className="close-track-panel"
                  onClick={() => setSongPickerOpen(false)}
                  aria-label="Şarkı seçiciyi kapat"
                >
                  ×
                </button>
              </div>

              {!selectedPlaylist ? (
                <div className="song-picker-playlists">
                  {spotifyPlaylists.map((playlist) => (
                    <button
                      key={playlist.id}
                      onClick={() => openSpotifyPlaylist(playlist)}
                    >
                      {playlist.images?.[0]?.url && (
                        <img src={playlist.images[0].url} alt="" />
                      )}
                      <span>{playlist.name}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <>
                  <button
                    className="ghost-button"
                    onClick={() => {
                      if (activeRoomCode) {
                        window.localStorage.removeItem(
                          roomPlaylistStorageKey(activeRoomCode),
                        );
                      }
                      setSelectedPlaylist(null);
                      setPlaylistTracks([]);
                      setPlaylistError("");
                    }}
                  >
                    ← Çalma listeleri
                  </button>
                  {playlistLoading && <p>Şarkılar yükleniyor...</p>}
                  <div className="song-picker-tracks">
                    {playlistTracks.map((track) => (
                      <button
                        key={track.id}
                        onClick={() => playTrackTogether(track)}
                      >
                        {track.album.images?.[0]?.url && (
                          <img src={track.album.images[0].url} alt="" />
                        )}
                        <span>
                          <strong>{track.name}</strong>
                          <small>
                            {track.artists.map((artist) => artist.name).join(", ")}
                          </small>
                        </span>
                        <Icon name="play" size={18} />
                      </button>
                    ))}
                  </div>
                </>
              )}
            </section>
          </div>
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
                      setDemoIsPlaying(!demoIsPlaying)
                    }
                  >
                    <Icon
                      name={
                        demoIsPlaying
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
          error={roomError}
          isSubmitting={roomSubmitting}
          onRoomNameChange={setRoomName}
          onRoomCodeChange={setRoomCode}
          onClose={() => setModal(null)}
          onSubmit={submitRoom}
        />
      )}
    </main>
  );
}
