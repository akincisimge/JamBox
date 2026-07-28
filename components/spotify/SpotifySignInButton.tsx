import type { SpotifyProfile } from "../../types/jambox";
import { Icon } from "../ui/Icon";

type SpotifySignInButtonProps = {
  profile: SpotifyProfile | null;
  onClick: () => void;
};

export function SpotifySignInButton({
  profile,
  onClick,
}: SpotifySignInButtonProps) {
  return (
    <button className="sign-in" onClick={onClick}>
      {profile ? (
        <>
          {profile.images?.[0]?.url ? (
            <img
              src={profile.images[0].url}
              alt={profile.display_name}
              style={{
                width: "26px",
                height: "26px",
                borderRadius: "50%",
                objectFit: "cover",
              }}
            />
          ) : (
            <Icon name="users" size={19} />
          )}
          {profile.display_name}
        </>
      ) : (
        <>
          <Icon name="users" size={19} />
          Spotify ile giriş
        </>
      )}
    </button>
  );
}
