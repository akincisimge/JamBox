# Step 3: Real room API

## Added

- Spotify-profile user registration/upsert endpoint
- room creation with secure random invite codes
- room lookup, join, leave, and close endpoints
- owner-only music permission updates
- automatic owner membership with music control permission
- service-layer errors mapped to HTTP 403, 404, and 409 responses
- Swagger header input for the temporary `X-User-Id` identity

## Temporary identity

Until Spotify OAuth is moved to the backend, protected room endpoints accept
the current JamBox user UUID through `X-User-Id`. The authentication milestone
will replace this header with a secure server-side session without changing the
room service rules.
