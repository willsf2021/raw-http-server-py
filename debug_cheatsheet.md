# TCP Debug Cheatsheet

## Useful Commands

### Inspect connections
```bash
ss -tn | grep 5050              # connections on port 5050
ss -tan | grep 5050             # all states including LISTEN
ss -tlnp | grep 5050            # show process/PID holding the port
lsof -i :5050                   # alternative, more detailed
```

### Filter by state
```bash
ss -tn | grep ESTABLISHED       # active connections
ss -tn | grep CLOSE_WAIT        # leaked sockets
ss -tn | grep TIME_WAIT         # connections finishing teardown
ss -tn | grep SYN_RECV          # incomplete handshakes
```

### Count connections
```bash
ss -tn | grep 5050 | wc -l                              # total count
ss -tan | grep 5050 | awk '{print $1}' | sort | uniq -c # count by state
```

### Monitor in real time
```bash
watch -n 0.5 'ss -tn | grep 5050'
watch -n 0.5 'ss -tn | grep 5050 | wc -l'
watch -n 0.5 'ss -tan | grep 5050 | awk "{print \$1}" | sort | uniq -c'
```

### Inspect kernel queue (backlog)
```bash
ss -tln | grep 5050
# Send-Q = connections waiting in kernel queue
# Recv-Q = data in buffer waiting to be read by the app
```

---

## TCP States Reference

| State | Who | Meaning | Possible Causes |
|---|---|---|---|
| `LISTEN` | Server | Socket bound and waiting for connections | Normal — server is up |
| `SYN_SENT` | Client | Sent SYN, waiting for SYN-ACK | Normal during handshake; persists if server is unreachable |
| `SYN_RECV` | Server | Received SYN, sent SYN-ACK, waiting for ACK | Normal during handshake; many = possible SYN flood attack |
| `ESTABLISHED` | Both | Connection active | Normal — data can flow |
| `FIN_WAIT_1` | Closer | Sent FIN, waiting for ACK | Normal during teardown |
| `FIN_WAIT_2` | Closer | Sent FIN, got ACK, waiting for remote FIN | Remote app never called `close()` |
| `CLOSE_WAIT` | Receiver | Got FIN from remote, waiting for app to call `close()` | **Socket leak** — your code never called `conn.close()` |
| `CLOSING` | Both | Both sides sent FIN simultaneously | Rare, normal |
| `LAST_ACK` | Receiver | Sent FIN, waiting for final ACK | Normal, transient |
| `TIME_WAIT` | Closer | Both FINs exchanged, waiting before fully closing | Normal — kernel holds for 2×MSL (~60s) to avoid stale packets |
| `CLOSED` | Both | Connection fully terminated | Normal |

---

## Common Problems & Diagnosis

### Too many CLOSE_WAIT
```bash
ss -tn state close-wait | wc -l
```
**Cause:** Your application received a FIN from the client but never called `conn.close()`.
Common culprits: unhandled exceptions before `close()`, threads stuck in a loop, missing `finally` block.

**Fix:**
```python
try:
    handle(conn)
finally:
    conn.close()  # always runs, even on exception
```

---

### Too many TIME_WAIT
```bash
ss -tn state time-wait | wc -l
```
**Cause:** Normal behavior — the side that initiates `close()` goes into TIME_WAIT. High volume = many short-lived connections (e.g. no keep-alive, clients reconnecting often).

**Fix:** Enable `SO_REUSEADDR`, use HTTP keep-alive, or tune kernel with `net.ipv4.tcp_tw_reuse=1`.

---

### Too many SYN_RECV
```bash
ss -tn state syn-recv | grep 5050
```
**Cause:** Incomplete handshakes. Could be a **SYN flood attack** or clients behind a very slow network.

**Fix:** Enable SYN cookies: `sysctl -w net.ipv4.tcp_syncookies=1`

---

### Port already in use
```bash
lsof -i :5050
ss -tlnp | grep 5050
```
**Cause:** Previous process didn't release the socket, or a socket is stuck in TIME_WAIT.

**Fix:**
```python
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # before bind()
```

---

### Connections stuck in FIN_WAIT_2
```bash
ss -tn state fin-wait-2 | grep 5050
```
**Cause:** Your server closed its side but the remote never sent its FIN back. Often caused by clients that crashed or have a bug in their teardown logic.

**Fix:** Set a socket-level timeout or tune `net.ipv4.tcp_fin_timeout`.

---

## Quick Mental Model

```
kernel handles automatically:        your code is responsible for:
─────────────────────────────         ─────────────────────────────
SYN / SYN-ACK / ACK  (handshake)     calling accept()
ACK on received FIN                  calling recv() / send()
retransmissions                      calling close()
kernel backlog queue                 handling exceptions safely
```

> If you see CLOSE_WAIT piling up → your code has a socket leak.
> If you see SYN_RECV piling up → someone might be flooding you.
> If you see TIME_WAIT piling up → normal, but consider keep-alive.