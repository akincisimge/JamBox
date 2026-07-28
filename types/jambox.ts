export type Track = {
  id: number;
  title: string;
  artist: string;
  addedBy: string;
  votes: number;
  art: string;
};

export type ChatMessage = {
  name: string;
  text: string;
  color: string;
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
