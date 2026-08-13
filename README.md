# Unsplash MCP Server

MCP server for searching Unsplash photos with attribution data built into every result. The repository supports both local `stdio` use and remote Streamable HTTP deployment with Docker, Portainer and Nginx Proxy Manager.

## Features

- Search Unsplash photos by keyword
- Retrieve random photos
- Trigger Unsplash download tracking
- Return photographer and Unsplash attribution data
- Local MCP operation over `stdio`
- Remote MCP operation over Streamable HTTP
- Docker/Portainer deployment
- Designed for reverse-proxy operation behind Nginx Proxy Manager

## Requirements

- Unsplash API access key
- Python 3.11+ for local operation, or Docker for container operation
- FastMCP 2.3+

Create an Unsplash API application in the Unsplash developer portal and copy its access key.

## MCP tools

### `search_photos`
Search photos by keyword. Supports pagination, ordering, color, orientation and content filtering.

### `get_random_photos`
Retrieve one or more random photos, optionally filtered by keyword and orientation.

### `track_download`
Call Unsplash's download tracking endpoint for a selected photo and return its download URL.

## Local installation (stdio)

```bash
git clone https://github.com/sartorisdatenschutz/unsplash-mcp.git
cd unsplash-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install .
cp .env.example .env
# Set UNSPLASH_ACCESS_KEY in .env
python server.py
```

`stdio` is the default transport when `server.py` is run directly.

Example MCP client configuration:

```json
{
  "mcpServers": {
    "unsplash": {
      "command": "/path/to/unsplash-mcp/.venv/bin/python",
      "args": ["/path/to/unsplash-mcp/server.py"],
      "env": {
        "UNSPLASH_ACCESS_KEY": "your_access_key_here"
      }
    }
  }
}
```

## Remote HTTP operation

```env
UNSPLASH_ACCESS_KEY=your_access_key_here
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

Then run `python server.py`. The default FastMCP Streamable HTTP endpoint is:

```text
http://HOST:8000/mcp
```

## Docker

```bash
docker build -t unsplash-mcp .
docker run --rm \
  -e UNSPLASH_ACCESS_KEY=your_access_key_here \
  -p 8000:8000 \
  unsplash-mcp
```

The Docker image runs as an unprivileged user and includes a TCP health check.

## Portainer + Nginx Proxy Manager

The included `docker-compose.yml` is intended for a Portainer Git repository stack. The MCP container does not publish port 8000 to the Docker host. Nginx Proxy Manager reaches it over the existing external Docker network `proxy_network`.

### 1. Shared proxy network

The deployment expects the existing external Docker network:

```text
proxy_network
```

You can verify it with:

```bash
docker network inspect proxy_network
```

Both Nginx Proxy Manager and `unsplash-mcp` must be attached to this network.

### 2. Portainer stack

Create a new Portainer stack from this Git repository and set:

```env
UNSPLASH_ACCESS_KEY=your_real_unsplash_access_key
```

No proxy-network environment variable is required; `docker-compose.yml` references `proxy_network` directly.

Deploy the stack. The container should become healthy and be reachable from Nginx Proxy Manager as:

```text
unsplash-mcp:8000
```

### 3. Nginx Proxy Manager

Create a Proxy Host with:

| Setting | Value |
| --- | --- |
| Domain | `mcp.example.com` |
| Scheme | `http` |
| Forward Hostname | `unsplash-mcp` |
| Forward Port | `8000` |
| Websockets Support | enabled |
| Block Common Exploits | enabled |

Request an SSL certificate, enable Force SSL and use the public MCP URL:

```text
https://mcp.example.com/mcp
```

Do not configure the NPM proxy host to strip `/mcp` from the request path.

## Security

The Unsplash access key is a server-side credential and must never be committed to Git. Configure it as an environment variable in Portainer.

The MCP endpoint itself does **not** currently implement client authentication. Do not expose it publicly unless access is restricted by a trusted reverse proxy, VPN, firewall, identity-aware proxy or another authentication layer. Nginx Proxy Manager Access Lists can be suitable only when the MCP client supports the chosen authentication method.

The container uses the following hardening measures by default:

- non-root runtime user
- all Linux capabilities dropped
- `no-new-privileges`
- no published host port in the Portainer compose stack
- existing external `proxy_network`

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `UNSPLASH_ACCESS_KEY` | required | Unsplash API access key |
| `MCP_TRANSPORT` | `stdio` outside Docker | `stdio`, `http` or `streamable-http` |
| `MCP_HOST` | `0.0.0.0` | HTTP bind address |
| `MCP_PORT` | `8000` | HTTP listen port |

## Unsplash usage requirements

When using images returned by this MCP server, follow the current Unsplash API requirements. The server returns attribution information and provides the `track_download` tool for download tracking.

## License

MIT License. See `LICENSE`.
