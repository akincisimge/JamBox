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
  reactions: Record<string, string[]>;
  message_type: "text" | "chess_invite" | "pisti_invite" | "papaz_kacti_invite";
  payload: Record<string, string>;
  created_at: string;
  user: JamBoxUser;
};

export type SpotifyProfile = { id: string; display_name: string; images?: { url: string }[] };
export type SpotifyPlaylist = { id: string; name: string; images?: { url: string }[]; items?: { total: number }; tracks?: { total: number }; owner: { display_name: string } };
export type SpotifyTrack = { id: string; name: string; uri: string; duration_ms: number; artists: { name: string }[]; album: { name: string; images?: { url: string }[] } };
export type SpotifyPlaylistItem = { item?: SpotifyTrack | null; track?: SpotifyTrack | null };

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

export type ChessGame = {
  id: string;
  creator_id: string;
  white_user_id: string;
  black_user_id: string | null;
  status: "waiting" | "active" | "finished";
  fen: string;
  turn: "white" | "black";
  move_history: string[];
  legal_moves: string[];
  move_labels: string[];
  draw_offer_user_id: string | null;
  winner_user_id: string | null;
  result: string | null;
  created_at: string;
  updated_at: string;
  white_user: JamBoxUser;
  black_user: JamBoxUser | null;
};

export type PistiCard = {
  id: string;
  suit: "clubs" | "diamonds" | "hearts" | "spades";
  rank: "A" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "J" | "Q" | "K";
};

export type PistiGame = {
  id: string;
  creator_id: string;
  player_one_user_id: string;
  player_two_user_id: string | null;
  status: "waiting" | "active" | "finished";
  turn_user_id: string | null;
  hand: PistiCard[];
  hand_counts: Record<string, number>;
  captured_counts: Record<string, number>;
  pisti_counts: Record<string, number>;
  table: PistiCard[];
  deck_count: number;
  scores: Record<string, number>;
  winner_user_id: string | null;
  player_one_user: JamBoxUser;
  player_two_user: JamBoxUser | null;
};

export type PapazKactiCard = {
  id: string;
  suit: "clubs" | "diamonds" | "hearts" | "spades";
  rank: "A" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "J" | "Q" | "K";
};

export type PapazKactiGame = {
  id: string;
  creator_id: string;
  player_one_user_id: string;
  player_two_user_id: string | null;
  player_three_user_id: string | null;
  player_four_user_id: string | null;
  status: "waiting" | "active" | "finished";
  turn_user_id: string | null;
  loser_user_id: string | null;
  hand: PapazKactiCard[];
  hand_counts: Record<string, number>;
  player_one_user: JamBoxUser;
  player_two_user: JamBoxUser | null;
  player_three_user: JamBoxUser | null;
  player_four_user: JamBoxUser | null;
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
  chess_game: ChessGame | null;
};
