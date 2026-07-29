type SpotifyPlayerError = { message: string };

type SpotifyPlayerOptions = {
  name: string;
  getOAuthToken: (callback: (token: string) => void) => void;
  volume?: number;
};

type SpotifyReadyEvent = { device_id: string };

interface SpotifyPlayer {
  connect(): Promise<boolean>;
  disconnect(): void;
  activateElement(): Promise<void>;
  addListener(event: "ready", callback: (event: SpotifyReadyEvent) => void): boolean;
  addListener(
    event:
      | "initialization_error"
      | "authentication_error"
      | "account_error"
      | "playback_error",
    callback: (event: SpotifyPlayerError) => void,
  ): boolean;
}

interface Window {
  Spotify?: {
    Player: new (options: SpotifyPlayerOptions) => SpotifyPlayer;
  };
  onSpotifyWebPlaybackSDKReady?: () => void;
}
