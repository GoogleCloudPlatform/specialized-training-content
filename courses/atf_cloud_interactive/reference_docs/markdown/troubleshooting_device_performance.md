# Cymbal Meet — Troubleshooting Guide: Device Performance

## Diagnosing and Resolving Conference Room Device Issues

Version 3.1 | Last Updated: January 2026 | Document ID: CM-TSG-DEV-001

---

## 1. Overview

Cymbal Meet conference room devices ("boxes") are purpose-built hardware units installed in meeting rooms. They provide high-definition video, spatial audio, and intelligent camera framing for in-room participants. When devices underperform, meeting quality degrades for all participants — both in-room and remote.

This guide covers the most common device performance issues, their root causes, diagnostic procedures, and resolution steps.

## 2. Performance Baselines

Understanding normal operating parameters is essential for identifying issues. Devices that consistently exceed these thresholds require investigation.

### Normal Operating Parameters

| Metric | Healthy Range | Warning Threshold | Critical Threshold |
| --- | --- | --- | --- |
| CPU Usage | 20-45% | 60-75% | >75% |
| Memory Usage | 30-55% | 65-80% | >80% |
| Network Latency | 10-40ms | 50-80ms | >80ms |
| Packet Loss | 0.0-0.5% | 0.5-2.0% | >2.0% |
| Video Quality Score | 3.8-5.0 | 3.0-3.8 | <3.0 |

### Device Telemetry

Cymbal Meet devices report telemetry every 5 minutes during business hours (8 AM - 6 PM local time). Telemetry data includes CPU, memory, network, and video quality metrics. This data is available via the Cymbal Meet Admin Console and the BigQuery analytics pipeline.

## 3. Common Issues and Solutions

### 3.1 High Network Latency

**Symptoms:**
- Video freezing or stuttering
- Audio delay / echo
- Participants reporting "you're breaking up"
- Video quality score consistently below 3.5

**Root Causes (in order of likelihood):**

1. **Insufficient QoS (Quality of Service) Configuration**
   - The most common cause of latency issues, especially after office moves or network changes
   - Video traffic competes with bulk data transfers, cloud backups, and software updates
   - Impact: Latency spikes during business hours when network is congested

2. **Network Congestion**
   - Too many devices sharing insufficient bandwidth
   - Common when multiple conference rooms are in simultaneous use

3. **Routing Issues**
   - Traffic routing through unnecessary hops (VPN, proxy, or remote gateway)
   - Corporate proxy configurations that route video traffic through inspection appliances

4. **Physical Infrastructure**
   - Damaged or aging network cables
   - Switch port issues
   - WiFi interference (if device uses wireless backhaul)

**Diagnostic Steps:**

1. Check the Cymbal Meet Admin Console > Devices > Network Health for the affected room(s)
2. Compare latency patterns:
   - Consistent across all rooms → Network-wide issue (QoS, routing, ISP)
   - Isolated to specific rooms → Room-specific infrastructure issue
   - Time-of-day pattern → Congestion-related
3. Run a network diagnostic from the device: Settings > Network > Run Diagnostics
4. Check if a VPN or corporate proxy is in the traffic path: Settings > Network > Route Trace

**Resolution Steps:**

| Cause | Action | Expected Impact |
| --- | --- | --- |
| No QoS | Configure DSCP markings for Cymbal Meet traffic (EF for audio, AF41 for video). See Section 5 for detailed QoS configuration. | Latency drop of 40-70% within hours |
| Proxy routing | Exclude Cymbal Meet domains from proxy/VPN (*.cymbalmeet.com, media.cymbalmeet.com). Configure split tunneling. | Immediate latency improvement |
| Switch congestion | Upgrade to Gigabit switches, enable 802.1p priority queuing | Requires hardware change; 1-2 week timeline |
| Cable issues | Replace Cat5 with Cat6 cabling; test with cable certifier | Immediate after replacement |

### 3.2 High Packet Loss

**Symptoms:**
- Audio cutting out (words/phrases missing)
- Video artifacts (blocky, pixelated video)
- Screen sharing showing stale content
- Video quality score drops below 3.0

**Root Causes:**

1. **Network Infrastructure Degradation**
   - Failing switches or routers dropping packets
   - Overloaded network buffers
   - Duplex mismatch on switch ports

2. **Bandwidth Saturation**
   - Total traffic exceeds available bandwidth
   - Common during peak hours or when large file transfers coincide with meetings

3. **Wireless Interference** (if using WiFi backhaul)
   - Competing WiFi networks on overlapping channels
   - Microwave ovens, Bluetooth devices, or other 2.4GHz interference

4. **ISP or WAN Issues**
   - Upstream packet loss beyond the organization's network boundary
   - Peering issues between ISP and Cymbal Meet's media servers

**Diagnostic Steps:**

1. Review packet loss trends in Admin Console > Devices > select device > Telemetry
2. If packet loss affects ALL devices across ALL rooms:
   - Issue is likely WAN/ISP-level or core network infrastructure
   - Contact ISP to check for upstream issues
   - Run traceroute from device to Cymbal Meet media servers
3. If packet loss affects devices in SPECIFIC rooms or buildings:
   - Issue is likely local infrastructure
   - Check switch port error counters
   - Verify cable integrity
4. If packet loss is intermittent and time-correlated:
   - Likely bandwidth saturation
   - Identify competing traffic using network monitoring tools

**Resolution Steps:**

1. **Immediate Mitigation:** Enable Forward Error Correction (FEC) on affected devices: Settings > Audio/Video > Enable FEC. This adds ~10% bandwidth overhead but recovers from 1-3% packet loss.
2. **Infrastructure Fix:** Address root cause per diagnostic findings (replace failing hardware, add bandwidth, fix QoS)
3. **Monitoring:** Set up alerts in Admin Console for packet loss exceeding 1% on any device

### 3.3 Low Video Quality Score

**Symptoms:**
- Blurry or low-resolution video
- Camera not switching to HD despite sufficient bandwidth
- Quality score consistently below 3.5 even with good network metrics

**Root Causes:**

1. **Bandwidth allocation below HD threshold**
   - Cymbal Meet requires 2.5 Mbps per device for 1080p video
   - If allocated bandwidth drops below 1.5 Mbps, quality is capped at 720p
   - Below 0.8 Mbps, quality drops to 480p

2. **CPU throttling**
   - Device CPU overheating, causing clock speed reduction
   - Running outdated firmware that has known performance regressions

3. **Camera hardware issues**
   - Lens obstruction or smudging
   - Camera sensor degradation (rare, but possible on units >3 years old)

4. **Lighting conditions**
   - Low ambient light forces camera to high ISO, introducing noise
   - Strong backlighting from windows causes exposure issues

**Resolution Steps:**

1. Verify bandwidth: Settings > Network > Bandwidth Test (expect >2.5 Mbps for HD)
2. Check firmware version: Settings > About > Firmware. Update if behind current release (see Section 4)
3. Check CPU thermals: Admin Console > Device > Hardware Health. If CPU temp >80C, check ventilation
4. Clean camera lens; verify room lighting meets minimum 300 lux at face level
5. If quality score remains low after above steps, contact Cymbal Meet Support for hardware diagnostic

### 3.4 High CPU / Memory Usage

**Symptoms:**
- Device UI is sluggish
- Slow to join meetings
- Features like intelligent framing or noise cancellation disabled automatically
- Device reboots unexpectedly

**Root Causes:**

1. **Outdated firmware** — older versions may have memory leaks or inefficient processing
2. **Too many background processes** — digital signage, room calendar display, and meeting room sensors running simultaneously
3. **Hardware aging** — devices older than 4 years may struggle with newer codec requirements
4. **Large meeting rooms** — devices in rooms with 20+ participants use more CPU for multi-stream processing

**Resolution Steps:**

1. Update firmware to the latest stable release (see Section 4)
2. Disable non-essential features: Settings > Features > disable Digital Signage, Room Sensors if not needed
3. Reboot the device (Settings > System > Restart) — resolves temporary memory leaks
4. If CPU consistently >70% after firmware update, consider hardware upgrade (contact your CSM for upgrade pricing)

## 4. Firmware Management

### Current Firmware Versions

| Device Model | Latest Stable | Latest Beta | End of Support |
| --- | --- | --- | --- |
| Cymbal Room 100 | 4.2.1 | 4.3.0-beta2 | March 2027 |
| Cymbal Room 200 | 4.2.1 | 4.3.0-beta2 | June 2028 |
| Cymbal Room 300 | 4.2.1 | 4.3.0-beta2 | December 2029 |

### Update Procedure

1. Schedule updates during non-business hours (updates take 10-15 minutes and reboot the device)
2. Admin Console > Devices > select devices > Schedule Firmware Update
3. Choose "Staged rollout" for organizations with 10+ devices — update 20% first, monitor for 48 hours, then continue
4. Verify post-update: check that video quality score and CPU/memory metrics are stable or improved

### Known Firmware Issues

- **v4.1.x:** Memory leak in noise cancellation module. Devices reboot after 72 hours of continuous operation. Fixed in v4.2.0.
- **v4.0.x:** Packet loss measurement underreports by ~15%. Actual packet loss may be higher than telemetry shows. Fixed in v4.1.0.

## 5. Network Configuration — QoS Best Practices

### DSCP Markings for Cymbal Meet Traffic

| Traffic Type | DSCP Value | Per-Hop Behavior | Bandwidth Reservation |
| --- | --- | --- | --- |
| Audio (RTP) | 46 (EF) | Expedited Forwarding | 100 Kbps per device |
| Video (RTP) | 34 (AF41) | Assured Forwarding | 2.5 Mbps per device |
| Screen Share | 26 (AF31) | Assured Forwarding | 1.5 Mbps per device |
| Signaling (SIP/HTTPS) | 24 (CS3) | Class Selector | 50 Kbps per device |

### Minimum Bandwidth per Room

| Room Capacity | Minimum Bandwidth | Recommended Bandwidth |
| --- | --- | --- |
| 1-6 people | 5 Mbps | 10 Mbps |
| 7-15 people | 10 Mbps | 20 Mbps |
| 16-30 people | 15 Mbps | 30 Mbps |
| 30+ people | 25 Mbps | 50 Mbps |

### Firewall and Proxy Configuration

**Required Allowlist:**
- `*.cymbalmeet.com` — TCP 443 (signaling)
- `media.cymbalmeet.com` — UDP 10000-20000 (audio/video RTP)
- `telemetry.cymbalmeet.com` — TCP 443 (device telemetry)

**Critical:** Do NOT route media traffic (UDP) through a corporate proxy or SSL inspection appliance. This adds 30-80ms of latency and introduces packet loss. Use split tunneling or proxy bypass rules for Cymbal Meet media domains.

### Network Health Check Checklist

- [ ] QoS DSCP markings configured on all switches between device and WAN uplink
- [ ] Firewall allows UDP 10000-20000 to media.cymbalmeet.com
- [ ] Proxy bypass configured for *.cymbalmeet.com
- [ ] Each meeting room has dedicated bandwidth allocation (not shared with general office WiFi)
- [ ] Switch ports for Cymbal Meet devices are on a dedicated VLAN with priority queuing
- [ ] Cable infrastructure is Cat6 or better
- [ ] WiFi access points (if used for backhaul) are on 5GHz with DFS channels

## 6. Hardware Replacement Criteria

A device should be replaced when:

1. **End of support date has passed** — no more firmware updates, security patches, or telemetry support
2. **CPU consistently >70%** after latest firmware update with minimal features enabled
3. **Video quality score consistently <3.0** despite good network conditions (verified by other devices on same network performing well)
4. **Device requires rebooting more than once per week** due to crashes or freezes
5. **Physical damage** — damaged camera, microphone array malfunction, speaker distortion

Contact your Customer Success Manager to discuss upgrade options and pricing. Cymbal Meet offers a trade-in program with 20% credit toward new devices when returning functional units.

## 7. Escalation Path

| Level | Scope | Contact | SLA |
| --- | --- | --- | --- |
| Self-Service | Firmware updates, reboots, basic config | Admin Console | Immediate |
| L1 Support | Single-device issues, known issue workarounds | support@cymbalmeet.com | 4 hours |
| L2 Support | Multi-device issues, network analysis, firmware bugs | Assigned CSM escalation | 8 hours |
| L3 Engineering | Systemic issues, firmware defects, hardware recalls | CSM escalation to Engineering | 24 hours |

---

*Cymbal Meet Technical Support — For urgent device issues, contact support@cymbalmeet.com or call 1-800-CYMBAL-1 (24/7).*
