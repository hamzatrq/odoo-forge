# Network Tools

Expose a local Odoo instance to the internet via SSH or Cloudflare tunnels.

## `odoo_network_expose`

Create a tunnel to expose local Odoo to the internet.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | `int` | `8069` | Local port to expose |
| `method` | `str` | `"ssh"` | Tunnel method: `"ssh"` or `"cloudflare"` |
| `subdomain` | `str` | `null` | Preferred subdomain (if supported) |

**Returns:** Public URL, tunnel method, local port.

**Example:** `"Expose my Odoo instance to the internet using Cloudflare"`

---

## `odoo_network_status`

Check active network tunnels.

**Parameters:** None

**Returns:** Active tunnel count and details (method, port, URL).

---

## `odoo_network_stop`

Stop active network tunnels. Omit port to stop all tunnels.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | `int` | `null` | Specific port to stop (null = all) |

**Returns:** Number of tunnels stopped.
