# MQTT – Illustrated Guide


## 0  Bird’s‑Eye Overview

```mermaid
flowchart LR
    subgraph Edge
        A[Sensor / MCU<br> Publisher]
        C[Mobile App<br> Subscriber]
    end
    subgraph Cloud
        B[MQTT Broker]
        style B fill:#ffdef1,stroke:#333,stroke-width:2px
    end
    A -- PUBLISH --> B
    B -- FORWARD --> C
```

Tiny 🛰️ sensors speak TCP to a central **broker**; everybody agrees on **topics**, and QoS levels fine‑tune reliability.

---

## 1  MQTT Packet Zoo (all 15 types)

```mermaid
classDiagram
    class ControlPacket {
        <<abstract>>
        header
        variableHeader
        payload
    }
    ControlPacket <|-- CONNECT
    ControlPacket <|-- CONNACK
    ControlPacket <|-- PUBLISH
    ControlPacket <|-- PUBACK
    ControlPacket <|-- PUBREC
    ControlPacket <|-- PUBREL
    ControlPacket <|-- PUBCOMP
    ControlPacket <|-- SUBSCRIBE
    ControlPacket <|-- SUBACK
    ControlPacket <|-- UNSUBSCRIBE
    ControlPacket <|-- UNSUBACK
    ControlPacket <|-- PINGREQ
    ControlPacket <|-- PINGRESP
    ControlPacket <|-- DISCONNECT
    ControlPacket <|-- AUTH
```

This diagram shows the inheritance relationship of every MQTT v5 control packet. All share the same **fixed header** followed by optional sections.

- **CONNECT (1)** — Client’s opening salvo establishing a session; includes ClientID, keep‑alive, clean‑start flag, Last‑Will, credentials, and (MQTT 5) properties.
- **CONNACK (2)** — Broker’s verdict on the CONNECT; returns a reason code and whether a previous session is present.
- **PUBLISH (3)** — Carries your application payload. Flags encode DUP, QoS, RETAIN; variable header holds Topic, Packet ID, and Properties.
- **PUBACK (4)** — One‑packet acknowledgement that completes the QoS 1 round‑trip.
- **PUBREC (5)** — Step 1 of the QoS 2 handshake (“received”).
- **PUBREL (6)** — Step 2, publisher releases the message for delivery.
- **PUBCOMP (7)** — Step 3, broker confirms completion; exactly‑once achieved.
- **SUBSCRIBE (8)** — Client requests one or more topic filters with desired QoS.
- **SUBACK (9)** — Broker replies with granted QoS—or a failure code—per filter.
- **UNSUBSCRIBE (10)** — Client drops one or more subscriptions.
- **UNSUBACK (11)** — Confirmation that the filters are gone.
- **PINGREQ (12)** — Heartbeat probe sent if no traffic during the keep‑alive window.
- **PINGRESP (13)** — Broker’s heartbeat echo proving the socket is still alive.
- **DISCONNECT (14)** — Graceful close or error signal; in MQTT 5 it can carry detailed reason codes and session‑expiry info.
- **AUTH (15)** — Optional extended authentication exchange (e.g., SASL, JWT refresh) added in MQTT 5.

---

## 2  Client Connection State‑Machine

```mermaid
stateDiagram-v2
    [*] --> Disconnected
    Disconnected --> Connecting: CONNECT sent
    Connecting --> Connected: CONNACK OK
    Connected --> Subscribed: SUBSCRIBE/SUBACK
    Subscribed --> Active
    Connected --> Disconnecting: DISCONNECT sent
    Active --> Disconnecting: DISCONNECT
    Disconnecting --> Disconnected: TCP close
```

A client travels through **Connecting → Connected → Subscribed → Active**. Any ACK failure or TCP drop jumps it back to *Disconnected*.

---

## 3  QoS 2 Four‑Step Handshake (Detailed)

```mermaid
sequenceDiagram
    autonumber
    participant P as Publisher
    participant B as Broker

    Note over P,B: QoS 2 guarantees *exactly‑once* delivery

    P->>B: PUBLISH (id 0x42, QoS 2)
    B-->>P: PUBREC (id 0x42)
    P->>B: PUBREL (id 0x42)
    B-->>P: PUBCOMP (id 0x42)
```

---

## 4  Keep‑Alive Heartbeat Timeline

```mermaid
gantt
    dateFormat  HH:mm:ss
    title Client ↔ Broker keep‑alive (60 s)
    section TCP
    CONNECT           :done, 00:00:00, 1s
    Idle wait         :       00:00:01, 59s
    PINGREQ           : done, 00:01:00, 1s
    PINGRESP          : done, 00:01:01, 1s
    Idle wait         :       00:01:02, 59s
    PINGREQ           : done, 00:02:01, 1s
```

If no application traffic appears inside one **keep‑alive window**, the client must send **PINGREQ/PINGRESP** to prove liveness.

---

## 5  TLS Handshake & Auth Pipeline

```mermaid
flowchart LR
    subgraph Internet
        U[Client] -- TLS 1.2/1.3 --> RP[Reverse&nbsp;Proxy]
    end
    RP -- TLS or TCP --> B[MQTT&nbsp;Broker]
    B --> ACL[(ACL Store)]
    ACL -. verify .-> B
    style RP fill:#bbdefb,stroke:#0d47a1
    style ACL fill:#ffe082,stroke:#f57f17
```

*TLS encrypts*, plugins authenticate, then **ACLs** authorise topic access.

---

## 6  Retained Message Lifecycle

```mermaid
sequenceDiagram
    participant Pub as Publisher
    participant Brk as Broker
    participant New as New Subscriber

    Pub->>Brk: PUBLISH retain=true (temp = 22.4)
    Brk->>Brk: store last value

    New->>Brk: SUBSCRIBE sensors/temp
    Brk-->>New: PUBLISH retain flag (temp = 22.4)
```

Retain flag == *instant snapshot* for newcomers.

---

## 7  Shared Subscription Load‑Balancing

```mermaid
sequenceDiagram
    participant S1 as Worker #1
    participant S2 as Worker #2
    participant Bk as Broker
    participant Pub as Publisher

    Note over S1,S2: Both subscribe to <br>`$share/alpha/orders`

    Pub->>Bk: PUBLISH orders id 137
    alt round‑robin
        Bk-->>S1: PUBLISH orders 137
    else
        Bk-->>S2: PUBLISH orders 137
    end
```

**\$share/group/topic** spreads messages across a worker pool to parallelise processing.

---

## 8  Broker Cluster Topology (Horizontal Scale)

```mermaid
flowchart LR
    subgraph "AZ-1"
        B1[Broker Node 1]
        B2[Broker Node 2]
    end
    subgraph "AZ-2"
        B3[Broker Node 3]
    end
    B1 <-->|sync| B2
    B2 <-->|sync| B3
    B1 <-->|sync| B3
    C1([Client A]) --- B1
    C2([Client B]) --- B2
    C3([Client C]) --- B3
    style B1 fill:#e1bee7,stroke:#6a1b9a
    style B2 fill:#e1bee7,stroke:#6a1b9a
    style B3 fill:#e1bee7,stroke:#6a1b9a

```

Modern brokers (HiveMQ, EMQX) replicate sessions & retained data across nodes for **fault‑tolerance** and millions of connections.

---

## 9  Topic Design Cheat‑Sheet

```mermaid
flowchart TD
    good["device/{id}/status"]
    bad["{id}/status/device"]
    good --> easyACLs["Read ACL = device/*/status"]
    bad --> pain["Hard to wildcard"]
    style good fill:#c8e6c9,stroke:#2e7d32
    style bad fill:#ffcdd2,stroke:#c62828

```

Put **static nouns first** ➜ simpler ACLs & filters.

---

## 10  Troubleshooting Flow

```mermaid
flowchart TD
    conn[Client drops?] --> ka[Check keep‑alive]
    ka --> auth[Auth logs OK?]
    auth --> cert[Cert expiry OK?]
    cert --> mtu[MTU / QoS mismatch?]
    mtu --> fix[Adjust & retry]
```
