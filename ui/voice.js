/* Voice for the display: hold-to-talk (button or Space) over WebRTC to the Pipecat voice bot.
   The peer connection is made once (offer proxied by Barnaby's server at /api/voice/offer); after that the mic track
   is simply enabled while you hold. ?handsfree=1 keeps the mic open (pair with BARNABY_WAKE=1 for "hey Barnaby").
   Barnaby's speech comes back as the remote audio track. */
(() => {
  'use strict';
  const B = window.Barnaby;
  const params = new URLSearchParams(location.search);
  const btn = document.getElementById('talk');
  const label = btn.querySelector('.label');
  const audio = new Audio(); audio.autoplay = true;
  let pc = null, micTrack = null, connecting = null, holding = false;
  const handsfree = params.has('handsfree');
  const APP = /^app3?$/.test(document.documentElement.dataset.skin || '');   // the app looks say "Listening…" on the button while held

  async function connect() {
    if (pc && pc.connectionState === 'connected') return;
    if (connecting) return connecting;
    connecting = (async () => {
      label.textContent = 'Connecting…';
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
      micTrack = stream.getAudioTracks()[0];
      micTrack.enabled = handsfree;
      pc = new RTCPeerConnection();
      pc.addTransceiver(micTrack, { direction: 'sendrecv', streams: [stream] });
      pc.ontrack = e => { audio.srcObject = e.streams[0] || new MediaStream([e.track]); };
      pc.onconnectionstatechange = () => {
        if (['failed', 'closed', 'disconnected'].includes(pc.connectionState)) { pc = null; label.textContent = 'Hold to talk'; }
      };
      await pc.setLocalDescription(await pc.createOffer());
      await new Promise(res => {                       // gather ICE (all local) before sending the offer
        if (pc.iceGatheringState === 'complete') return res();
        const t = setTimeout(res, 1500);
        pc.onicegatheringstatechange = () => { if (pc.iceGatheringState === 'complete') { clearTimeout(t); res(); } };
      });
      const r = await fetch('/api/voice/offer', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sdp: pc.localDescription.sdp, type: pc.localDescription.type }) });
      if (!r.ok) throw new Error('voice bot not reachable (' + r.status + ')');
      await pc.setRemoteDescription(await r.json());
      label.textContent = handsfree ? 'Listening' : 'Hold to talk';
    })();
    try { await connecting; } catch (e) { B.addMsg('error note', 'Voice', String(e.message || e)); pc = null; label.textContent = 'Hold to talk'; }
    finally { connecting = null; }
  }

  async function down() {
    if (holding) return;
    holding = true;
    btn.classList.add('on'); B.setStatus('listening');
    await connect();
    if (micTrack && holding) { micTrack.enabled = true; if (APP && !handsfree) label.textContent = 'Listening…'; }
  }
  function up() {
    if (!holding) return;
    holding = false;
    btn.classList.remove('on');
    if (APP && label.textContent === 'Listening…') label.textContent = 'Hold to talk';
    if (micTrack && !handsfree) setTimeout(() => { if (!holding) micTrack.enabled = false; }, 350); // keep the tail of the word
    B.setStatus(null);
  }

  btn.addEventListener('pointerdown', e => { e.preventDefault(); down(); });
  btn.addEventListener('pointerup', up);
  btn.addEventListener('pointerleave', up);
  document.addEventListener('keydown', e => {
    if (e.code === 'Space' && !e.repeat && !(e.target && e.target.tagName === 'INPUT')) { e.preventDefault(); down(); }
  });
  document.addEventListener('keyup', e => { if (e.code === 'Space' && !(e.target && e.target.tagName === 'INPUT')) up(); });
  if (handsfree) connect();
  window.BarnabyVoice = { connect };
})();
