# MQTT

**MQTT (Message Queuing Telemetry Transport)** is a lightweight publish/subscribe protocol invented in 1999 by Andy Stanford-Clark (IBM) and Arlen Nipper (Eurotech) to move SCADA data from remote oil-pipeline sensors over costly, high-latency satellite links .

Because it keeps the on-wire header to just 2 bytes, offers three quality-of-service (QoS) delivery guarantees, and operates happily on spotty or bandwidth-constrained networks, MQTT has become the **de-facto messaging standard for the Internet of Things (IoT)**, mobile apps, and cloud backends .

This beginner-friendly guide explains the core ideas—brokers, topics, QoS, retained messages, security, and the v5.0 feature set—then walks you through installing Mosquitto, writing your first secure Python client with Paho, and adopting best practices and troubleshooting tips drawn from real-world deployments.

---

## 1. What exactly is MQTT?

* **Open standard:** MQTT is an OASIS and ISO/IEC 20922 standard, specifying 15 packet types that ride on a single TCP connection .
* **Publish/Subscribe model:** Clients never talk directly; they publish messages to a **broker**, which delivers them to all clients subscribed to the same **topic** .
* **Tiny footprint:** The entire protocol fits easily on 8-bit MCUs and narrow-band links thanks to its minimal header and keep-alive pings .

---

## 2. Why do people choose MQTT?

| Constraint            | MQTT Response                                       | Source |
| --------------------- | --------------------------------------------------- | ------ |
| Low bandwidth / power | 2-byte fixed header, long keep-alive intervals      |        |
| Unreliable links      | Offline buffering, QoS 1/2 retransmission           |        |
| Loose coupling        | Publishers don’t need addresses of subscribers      |        |
| Cross-language        | Dozens of client libraries (C, Python, JavaScript…) |        |

---

## 3. Core Concepts

### 3.1 Broker & Client

A **broker** (e.g. Eclipse Mosquitto) accepts client TCP/TLS connections on port 1883 or 8883, authenticates them, and handles all message routing and persistence .
A **client** is any device or app that opens one connection to the broker and then sends `PUBLISH`, `SUBSCRIBE`, or other control packets as needed .

### 3.2 Topics & Wildcards

Topics are UTF-8 strings separated by `/` (e.g. `factory/line1/temperature`) .
Subscribers can use `+` (single level) or `#` (multi-level) wildcards (`factory/+/temperature`, `factory/#`) to match whole branches of the hierarchy .
Good topic design avoids overly deep trees and never embeds client identifiers inside wildcards .

### 3.3 Quality of Service (QoS)

| Level | Guarantee                        | Typical Use              |
| ----- | -------------------------------- | ------------------------ |
| 0     | *At most once* (fire-and-forget) | High-rate sensor streams |
| 1     | *At least once* (may duplicate)  | Command acknowledgments  |
| 2     | *Exactly once*                   | Billing, alarms          |

### 3.4 Retained Messages & Last Will

Setting the **retain flag** lets a broker store the most recent value on a topic so that late-joining clients get an immediate snapshot .
A **Last-Will & Testament (LWT)** is a pre-registered message the broker publishes if the client disconnects ungracefully, signalling failure to peers .

---

## 4. How the protocol flows

1. **CONNECT → CONNACK** – client identifies itself, negotiates keep-alive, optionally authenticates.
2. **SUBSCRIBE → SUBACK** – client tells broker the topic filters & QoS levels it wants.
3. **PUBLISH** – broker fan-outs application payloads to matching subscribers.
4. **PINGREQ/PINGRESP** – lightweight heartbeat to keep NATs alive.
5. **DISCONNECT** – graceful shutdown.
   All control-packet structures and rules are formalised in the v5.0 spec .

---

## 5. MQTT 3.1.1 vs 5.0 – what changed?

| Area           | 3.1.1                 | 5.0 Enhancements                              | 
| -------------- | --------------------- | --------------------------------------------- |
| Reason Codes   | Only CONNACK          | All ACKs carry detailed reason codes          |
| Properties     | None                  | User properties, message expiry, flow control |
| Shared Subs    | Broker-specific       | Standard `$share/{group}/topic` syntax        |
| Session Expiry | Clean-session Boolean | Expiry interval in seconds                    |

---

## 6. Getting Started – Hands-On

### 6.1 Install a Local Broker (Mosquitto)

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install mosquitto mosquitto-clients
# open firewall on 1883 (unencrypted) and 8883 (TLS) if needed
```

Mosquitto ships with sensible defaults, but from v2.0 onward you *must* explicitly enable authentication for remote access .

### 6.2 First Python Client with Paho

```python
import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
TOPIC  = "demo/hello"

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code", rc)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    print(msg.topic, msg.payload.decode())

client = mqtt.Client(client_id="my_python_demo", protocol=mqtt.MQTTv5)
client.tls_set()                 # use system CA certs
client.connect(BROKER, 8883, keepalive=60)
client.on_connect = on_connect
client.on_message = on_message

client.publish(TOPIC, "MQTT is alive!", qos=1, retain=True)
client.loop_forever()
```

The Paho client hides packet details and supports MQTT v3 & v5 out of the box .

---

## 7. Securing Your Deployment

* **TLS/SSL:** Always encrypt internet-facing traffic on port 8883 to protect credentials and payloads; the TLS handshake adds CPU overhead but is mandatory for production .
* **Authentication:** Mosquitto supports password files, external plugins (e.g. JWT, LDAP), and anonymous lockdown controls from v2.0 + .
* **Authorization (ACL):** Restrict clients to the minimum topic namespaces they need, e.g. `siteA/sensor/#` read-only.
* **Additional v5.0 tools:** Per-message user properties let you tag messages for downstream security appliances or audit logs .

---

## 8. Popular Use-Cases

| Domain               | How MQTT Helps                    | Example                                                                      |
| -------------------- | --------------------------------- | ---------------------------------------------------------------------------- |
| Home automation      | Stateless control & event updates | Lighting and HVAC with Home Assistant                                        |
| Industrial telemetry | Low-bandwidth SCADA, PLC data     | Pipeline flow & valve control                                                |
| Mobile messaging     | Battery-friendly push             | Facebook Messenger originally used MQTT for chat presence                    |
| Cloud IoT            | Massive fan-in to analytics       | AWS IoT Core, Azure IoT Hub, Google Cloud IoT Core all expose MQTT endpoints |

---

## 9. Best Practices & Troubleshooting

* **Topic hygiene:** Prefer noun/verb order (`device/{id}/status`) and avoid wildcards in publishes to keep ACLs simple .
* **Choose QoS wisely:** Use QoS 0 for high-frequency telemetry, QoS 1 for commands, and QoS 2 only when duplicates are unacceptable .
* **Retain with care:** Clear stale retained messages by publishing zero-length payloads with the retain flag set to avoid misinformation on reboot .
* **Diagnose connections:** If clients drop, check keep-alive settings, broker authentication logs, TLS certificate dates, and network MTU issues .
* **Scale horizontally:** Use shared subscriptions (`$share/group/topic`) or a clustered broker (HiveMQ, EMQX) when subscriber counts explode .

---

## 10. Further Learning

| Resource                             | Why it Matters                        |
| ------------------------------------ | ------------------------------------- |
| MQTT Essentials blog series (HiveMQ) | Concise deep dives on every feature   |
| Official OASIS specs                 | Canonical packet definitions, errata  |
| Eclipse Mosquitto docs               | Broker installation & security guides |
| Paho MQTT client docs                | Multi-language client APIs & samples  |
| IBM Developer articles               | Architectural context & IoT examples  |
| MQTT FAQ (mqtt.org)                  | Protocol history & community links    |
