export type Track = {
  id: number;
  title: string;
  artist: string;
  addedBy: string;
  votes: number;
  art: string;
};

export type ChatMessage = {
  id: string;
  user_id: string;
  text: string;
  created_at: string;
  user: JamBoxUser;
};

export type SpotifyProfile = {
  id: string;
  display_name: string;
  images?: { url: string }[];
};

export type SpotifyPlaylist = {
  id: string;
  name: string;
  images?: { url: string }[];
  items?: { total: number };
  tracks?: { total: number };
  owner: { display_name: string };
};

export type SpotifyTrack = {
  id: string;
  name: string;
  uri: string;
  duration_ms: number;
  artists: { name: string }[];
  album: {
    name: string;
    images?: { url: string }[];
  };
};

export type SpotifyPlaylistItem = {
  item?: SpotifyTrack | null;
  track?: SpotifyTrack | null;
};

export type JamBoxUser = {
  id: string;
  spotify_id: string;
  display_name: string;
  email: string | null;
  avatar_url: string | null;
  created_at: string;
};

export type JamBoxRoomMember = {
  user_id: string;
  is_owner: boolean;
  can_control_music: boolean;
  created_at: string;
  user: JamBoxUser;
};

export type JamBoxPlayback = {
  spotify_uri: string;
  spotify_track_id: string;
  queue_uris: string[];
  title: string;
  artist: string;
  album_image_url: string | null;
  duration_ms: number;
  position_ms: number;
  is_playing: boolean;
  version: number;
  changed_at: string;
};

export type JamBoxRoom = {
  id: string;
  code: string;
  name: string;
  owner_id: string;
  is_active: boolean;
  created_at: string;
  members: JamBoxRoomMember[];
  playback: JamBoxPlayback | null;
  messages: ChatMessage[];
};
