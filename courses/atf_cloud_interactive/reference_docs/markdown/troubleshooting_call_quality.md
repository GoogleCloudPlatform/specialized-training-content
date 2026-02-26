# Cymbal Meet — Troubleshooting Guide: Call Quality

## Diagnosing and Resolving Audio/Video Quality Issues

Version 2.8 | Last Updated: January 2026 | Document ID: CM-TSG-CQ-001

---

## 1. Overview

Call quality is the single most important factor in user satisfaction with Cymbal Meet. Poor call quality drives users back to legacy tools, reduces ad-hoc call adoption, and increases support ticket volume. This guide covers call quality issues for all Cymbal Meet clients — desktop, web, mobile, and conference room devices.

### Call Quality Score

Every Cymbal Meet call receives a quality score from 1.0 to 5.0, calculated from:
- Audio clarity (30% weight)
- Video resolution stability (25% weight)
- Latency and jitter (20% weight)
- Packet loss impact (15% weight)
- Connection reliability / drop count (10% weight)

| Score Range | Rating | User Experience |
| --- | --- | --- |
| 4.5-5.0 | Excellent | Crystal clear audio/video, no perceptible delays |
| 3.8-4.5 | Good | Minor occasional artifacts, fully usable |
| 3.0-3.8 | Fair | Noticeable quality dips, some audio dropouts |
| 2.0-3.0 | Poor | Frequent freezing, audio delays, participants disconnect |
| 1.0-2.0 | Unusable | Calls fail to connect or drop within minutes |

**Target:** Organization-wide average call quality score should be **above 3.8**. Scores consistently below 3.5 indicate a systemic issue requiring investigation.

## 2. Common Call Quality Problems

### 2.1 Audio Issues

#### Echo and Feedback

**Symptoms:** Participants hear their own voice repeated back with a delay; feedback loops create screeching sounds.

**Root Causes:**
- Speaker audio being picked up by microphone (acoustic echo)
- Multiple devices in the same room (laptop + conference room device)
- External speakers too close to microphone
- Echo cancellation disabled or malfunctioning

**Resolution:**
1. Ensure only ONE audio device is active per participant location
2. Use headsets for individual participants (eliminates acoustic echo entirely)
3. Conference room devices: verify echo cancellation is enabled (Settings > Audio > Echo Cancellation)
4. If echo persists on a conference room device, run Audio Calibration: Settings > Audio > Calibrate Room Audio
5. Check that firmware is current — echo cancellation improvements are included in every release

#### Audio Dropouts (Words Missing)

**Symptoms:** Words or entire phrases go missing; audio cuts in and out; "robotic" sounding voice.

**Root Causes:**
- Packet loss above 1% (see Device Performance guide for network troubleshooting)
- Insufficient upload bandwidth (<100 Kbps available for audio)
- Client CPU overload (audio encoding deprioritized)
- Bluetooth headset interference or battery issues

**Resolution:**
1. Check network: Admin Console > Calls > select call > Network Metrics
2. If packet loss >1%, refer to Device Performance guide Section 3.2
3. Desktop client: close competing bandwidth-heavy applications (large downloads, video streaming)
4. Bluetooth users: ensure headset is charged (>20% battery), try wired headset to isolate
5. Enable Audio Resilience mode: Settings > Audio > Enable Resilience (adds 50ms buffer, trades latency for continuity)

### 2.2 Video Issues

#### Low Resolution / Blurry Video

**Symptoms:** Video appears pixelated, 240p/480p instead of expected 720p/1080p.

**Root Causes:**
- Bandwidth adaptation — Cymbal Meet automatically reduces resolution when bandwidth is constrained
- Camera hardware limitations (older laptops, low-quality webcams)
- High CPU usage causing encoder to reduce resolution

**Bandwidth Requirements by Resolution:**

| Resolution | Minimum Bandwidth | Recommended | CPU Requirement |
| --- | --- | --- | --- |
| 1080p (Full HD) | 2.5 Mbps up/down | 4.0 Mbps | Moderate |
| 720p (HD) | 1.0 Mbps up/down | 2.0 Mbps | Low |
| 480p (SD) | 0.5 Mbps up/down | 0.8 Mbps | Minimal |
| 240p (Low) | 0.15 Mbps up/down | 0.3 Mbps | Minimal |

**Resolution Steps:**
1. Run bandwidth test: Cymbal Meet client > Settings > Network > Test Connection
2. If bandwidth is sufficient but resolution is low, check CPU usage during calls
3. For desktop: ensure hardware acceleration is enabled (Settings > Video > Hardware Acceleration)
4. For web client: use Chrome or Edge (hardware acceleration support). Firefox and Safari may fall back to software encoding.

#### Video Freezing

**Symptoms:** Video freezes while audio continues; frozen for 2-10 seconds then resumes; "slideshow" effect.

**Root Causes:**
- Jitter (variation in packet arrival time) above 30ms
- Packet loss on the video stream (UDP)
- Network congestion causing buffer underrun
- Corporate proxy or firewall inspecting/delaying video packets

**Resolution Steps:**
1. Check jitter metrics: Admin Console > Calls > select call > Network Metrics > Jitter
2. If jitter >30ms consistently: configure QoS to prioritize Cymbal Meet video traffic (DSCP AF41)
3. Verify media traffic is NOT routed through a proxy (see Device Performance guide, Section 5)
4. If the issue is specific to the web client: check browser extensions that may interfere with WebRTC
5. Enable Adaptive Jitter Buffer: Settings > Video > Adaptive Buffer (adds 20-50ms latency but smooths playback)

### 2.3 Call Drops

**Symptoms:** Participants are disconnected mid-call; "Reconnecting..." banner appears frequently; calls end abruptly.

**Root Causes:**
- Network connectivity loss (WiFi disconnect, VPN timeout, ISP outage)
- Firewall session timeout (TCP idle timeout too short for signaling connection)
- Corporate VPN reconnection cycle (VPN drops and reconnects, interrupting the media stream)
- Client crash due to memory or CPU exhaustion

**Understanding Drop Count:**

| Drops per Call | Assessment | Likely Cause |
| --- | --- | --- |
| 0 | Normal | N/A |
| 1 | Occasional issue | Transient network blip, WiFi roaming |
| 2-3 | Significant issue | Systematic network problem, VPN instability |
| 4+ | Critical | Infrastructure failure, incompatible network config |

**Healthy organizations average <0.3 drops per call.** An average above 1.0 indicates a systemic problem requiring immediate investigation.

**Resolution Steps:**

1. Identify pattern: Admin Console > Calls > filter by drops > 0
   - All users affected → Network infrastructure issue
   - Specific users → Individual client or connectivity issue
   - Time-of-day pattern → Congestion or scheduled network maintenance
   - Specific client type → Client bug or platform-specific issue

2. For VPN-related drops:
   - Configure split tunneling to exclude Cymbal Meet traffic from VPN
   - If split tunneling is not possible, increase VPN idle timeout to 300 seconds
   - Consider Cymbal Meet's Direct Connect mode (bypasses VPN for media while keeping signaling on VPN)

3. For firewall-related drops:
   - Set TCP idle timeout to at least 300 seconds for Cymbal Meet signaling connections
   - Allow UDP 10000-20000 for media (stateful firewall should maintain sessions)
   - Verify NAT session timeout is at least 120 seconds

4. For WiFi-related drops:
   - Enable fast roaming (802.11r) on WiFi access points
   - Ensure adequate WiFi coverage in all meeting-capable areas
   - Use 5GHz band exclusively for Cymbal Meet devices (less interference than 2.4GHz)

## 3. Client-Specific Issues

### 3.1 Desktop Client (Windows / macOS)

**Common Issues:**
- High CPU usage during calls with gallery view (10+ participants)
  - Fix: Limit gallery view to 9 tiles (Settings > Video > Gallery Limit)
- Screen sharing causes video quality drop
  - Fix: Enable hardware-accelerated screen capture (Settings > Screen Share > Hardware Capture)
- Audio device switching mid-call when peripherals connect/disconnect
  - Fix: Lock audio device (Settings > Audio > Lock Device During Calls)

**Minimum System Requirements:**
- CPU: 4 cores, 2.0 GHz
- RAM: 8 GB
- Network: 5 Mbps symmetric
- OS: Windows 10 (21H2+) or macOS 12+

### 3.2 Web Client

**Browser Compatibility:**
| Browser | Video Quality | Screen Share | Known Limitations |
| --- | --- | --- | --- |
| Chrome 100+ | Full HD | Full support | None |
| Edge 100+ | Full HD | Full support | None |
| Firefox 100+ | HD (720p max) | Full support | No hardware acceleration for video encode |
| Safari 16+ | HD (720p max) | Tab share only | No system audio share; WebRTC limitations |

**Web Client Troubleshooting:**
1. Clear browser cache and cookies for cymbalmeet.com
2. Disable browser extensions (ad blockers and privacy extensions often interfere with WebRTC)
3. Check that camera and microphone permissions are granted
4. Verify WebRTC is not disabled (chrome://webrtc-internals for diagnostics)

### 3.3 Mobile Client (iOS / Android)

**Common Issues:**
- Battery drain during long calls
  - Fix: Reduce video resolution to 720p (Settings > Video > Max Resolution)
- Audio routing confusion (speaker vs earpiece vs Bluetooth)
  - Fix: Tap the audio routing icon during call to explicitly select output
- Poor quality on cellular
  - Fix: Enable "Mobile Data Saver" mode (Settings > Network > Data Saver) — reduces bandwidth to 0.5 Mbps

### 3.4 Conference Room Devices

See the dedicated **Troubleshooting Guide: Device Performance** (CM-TSG-DEV-001) for comprehensive device troubleshooting.

**Quick Checks:**
- Reboot the device if issues started recently
- Check firmware version (update if behind)
- Run network diagnostics from the device menu
- Verify room audio calibration is current

## 4. IT Security Configurations That Impact Call Quality

### 4.1 Corporate Proxy and SSL Inspection

**Problem:** Many organizations route all traffic through a corporate proxy for security inspection. When Cymbal Meet media traffic (especially UDP-based audio and video) passes through a proxy, it introduces significant latency and jitter.

**Impact:**
- Added latency: 30-100ms per hop through the proxy
- Jitter increase: 15-40ms
- Potential packet reordering
- SSL inspection may break certificate pinning, causing connection failures

**Solution:**
1. Configure proxy bypass for all Cymbal Meet domains:
   - `*.cymbalmeet.com`
   - `media.cymbalmeet.com`
   - `signaling.cymbalmeet.com`
2. If full bypass is not permitted by security policy, bypass at minimum the media domain (`media.cymbalmeet.com`) on UDP 10000-20000
3. Work with the security team to add Cymbal Meet's certificate chain to the SSL inspection allowlist

### 4.2 Locked-Down Client Configuration

**Problem:** IT administrators sometimes restrict Cymbal Meet client features for security reasons, inadvertently disabling functionality that impacts quality and adoption.

**Commonly Restricted Features and Their Impact:**

| Restricted Feature | Security Rationale | Impact on Users | Recommended Alternative |
| --- | --- | --- | --- |
| Quick-call / instant meeting | Prevent unauthorized meetings | Eliminates ad-hoc calls; users can only join scheduled meetings. Dramatically reduces ad-hoc adoption rates (typically to <5%). | Use meeting policies instead — allow quick calls within the organization but require approval for external guests |
| Peer-to-peer media | Force all media through corporate network | Adds 20-50ms latency; all calls route through media relay | Allow P2P within corporate network; relay only for external participants |
| Recording | Compliance / privacy | Users cannot record meetings for later reference | Enable recording with automatic DLP scanning and retention policies |
| Screen sharing | Data loss prevention | Cannot share screens during calls; major productivity impact | Allow screen sharing within organization; block for external meetings |
| Virtual backgrounds | GPU resource usage | Minor — some users prefer virtual backgrounds for home office privacy | Allow but disable GPU-intensive effects (blur is lightweight) |

**Assessment Approach:**
1. Review the Cymbal Meet admin policy configuration: Admin Console > Policies
2. Identify which features are disabled organization-wide vs. by group
3. Evaluate whether the security concern can be addressed through a less restrictive policy
4. Test any policy changes with a pilot group before rolling out organization-wide

### 4.3 VPN and Split Tunneling

**Problem:** Full-tunnel VPN routes ALL traffic through the corporate network, including Cymbal Meet media. This adds unnecessary latency and consumes VPN bandwidth.

**Solution:** Enable split tunneling for Cymbal Meet:
- Route signaling traffic (`signaling.cymbalmeet.com`) through VPN (acceptable — low bandwidth)
- Route media traffic (`media.cymbalmeet.com`) directly to internet (critical — high bandwidth, latency-sensitive)
- This is consistent with zero-trust principles — media is encrypted end-to-end regardless of VPN

## 5. Organization-Wide Quality Improvement Plan

When an organization's average call quality score is below 3.5, follow this systematic approach:

### Step 1: Diagnose Scope (Day 1-2)

- Pull call quality reports for the past 30 days from Admin Console > Analytics > Call Quality
- Segment by: client type, location/office, time of day, call size
- Identify whether the issue is universal or concentrated

### Step 2: Address Infrastructure (Day 3-7)

- Network assessment: Verify QoS, bandwidth, proxy configuration
- Client assessment: Check minimum system requirements, firmware versions
- Refer to the relevant sections of this guide and the Device Performance guide

### Step 3: Address Client Configuration (Day 7-10)

- Review IT security policies for unnecessary restrictions
- Deploy client updates if versions are behind
- Enable hardware acceleration on all capable devices

### Step 4: Monitor and Iterate (Day 10-30)

- Set up weekly quality score reports by segment
- Target: average score improvement of 0.3-0.5 points per week
- Escalate to Cymbal Meet L2 Support if scores don't improve after infrastructure fixes

### Step 5: Ongoing Monitoring

- Set alerts for quality score drops below 3.5 (organization-wide) or 3.0 (individual user/device)
- Review monthly quality trends in the Admin Console dashboard
- Include call quality metrics in quarterly business reviews with your CSM

## 6. Escalation Path

| Level | When to Escalate | Contact |
| --- | --- | --- |
| Self-Service | Single-user or single-call issues | This guide + Admin Console |
| L1 Support | Recurring issues for a user or room | support@cymbalmeet.com |
| L2 Support | Organization-wide quality below 3.5 | Your assigned CSM |
| L3 Engineering | Suspected platform bug or media server issue | CSM escalation to Engineering |

---

*Cymbal Meet Technical Support — For urgent call quality issues affecting multiple users, contact your Customer Success Manager directly for expedited assistance.*
