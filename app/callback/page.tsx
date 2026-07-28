"use client";

import { useEffect, useRef, useState } from "react";

export default function SpotifyCallbackPage() {
  const [message, setMessage] = useState("Spotify hesabın bağlanıyor...");
  const hasStarted = useRef(false);

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    const completeLogin = async () => {
      try {
        const code = new URLSearchParams(window.location.search).get("code");
        const codeVerifier = localStorage.getItem("spotify_code_verifier");
        const clientId = process.env.NEXT_PUBLIC_SPOTIFY_CLIENT_ID;
        const redirectUri = process.env.NEXT_PUBLIC_SPOTIFY_REDIRECT_URI;

        if (!code || !codeVerifier || !clientId || !redirectUri) {
          throw new Error("Giriş bilgileri eksik.");
        }

        const tokenResponse = await fetch(
          "https://accounts.spotify.com/api/token",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({
              client_id: clientId,
              grant_type: "authorization_code",
              code,
              redirect_uri: redirectUri,
              code_verifier: codeVerifier,
            }),
          }
        );

        if (!tokenResponse.ok) {
          throw new Error("Spotify erişim anahtarı alınamadı.");
        }

        const tokenData = await tokenResponse.json();

        localStorage.setItem(
          "spotify_access_token",
          tokenData.access_token
        );

        if (tokenData.refresh_token) {
          localStorage.setItem(
            "spotify_refresh_token",
            tokenData.refresh_token
          );
        }

        const profileResponse = await fetch(
          "https://api.spotify.com/v1/me",
          {
            headers: {
              Authorization: `Bearer ${tokenData.access_token}`,
            },
          }
        );

        if (!profileResponse.ok) {
          throw new Error("Spotify profili alınamadı.");
        }

        const profile = await profileResponse.json();

        localStorage.setItem(
          "spotify_profile",
          JSON.stringify(profile)
        );

        localStorage.removeItem("spotify_code_verifier");
        setMessage("Giriş başarılı! JamBox açılıyor...");

        window.location.href = "/";
      } catch (error) {
        console.error(error);
        setMessage(
          "Giriş tamamlanamadı. Ana sayfaya dönüp tekrar deneyebilirsin."
        );
      }
    };

    completeLogin();
  }, []);

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background: "#070817",
        color: "white",
        fontFamily: "sans-serif",
      }}
    >
      <h2>{message}</h2>
    </main>
  );
}