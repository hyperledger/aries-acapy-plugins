### Description:

- v1_0:
  - Uses a middleware wrapper around the existing basicmessage `connections/{id}/send-message` api, and will persist the sent message.
  - Messages between all agents/connections can be fetched via `GET /basicmessages` with optional query params for `connection_id` and `state`.

### Configuration:

- No additional configuration required.
