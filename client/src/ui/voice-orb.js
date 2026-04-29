/**
 * Voice Orb - Three.js animated orb with 4 states
 * States: idle, listening, thinking, speaking
 * Falls back to CSS orb if Three.js unavailable
 */

const ORB_STATES = {
  IDLE: 'idle',
  LISTENING: 'listening',
  THINKING: 'thinking',
  SPEAKING: 'speaking'
};

// Simplex noise implementation (compact)
class SimplexNoise {
  constructor() {
    this.grad3 = [
      [1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],
      [1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],
      [0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1]
    ];
    this.p = [];
    for (let i = 0; i < 256; i++) this.p[i] = Math.floor(Math.random() * 256);
    this.perm = [];
    for (let i = 0; i < 512; i++) this.perm[i] = this.p[i & 255];
  }

  dot(g, x, y, z) { return g[0]*x + g[1]*y + g[2]*z; }

  noise3d(x, y, z) {
    const F3 = 1.0/3.0, G3 = 1.0/6.0;
    const s = (x+y+z)*F3;
    const i = Math.floor(x+s), j = Math.floor(y+s), k = Math.floor(z+s);
    const t = (i+j+k)*G3;
    const X0 = i-t, Y0 = j-t, Z0 = k-t;
    const x0 = x-X0, y0 = y-Y0, z0 = z-Z0;

    let i1,j1,k1,i2,j2,k2;
    if (x0>=y0) {
      if (y0>=z0) {i1=1;j1=0;k1=0;i2=1;j2=1;k2=0;}
      else if (x0>=z0) {i1=1;j1=0;k1=0;i2=1;j2=0;k2=1;}
      else {i1=0;j1=0;k1=1;i2=1;j2=0;k2=1;}
    } else {
      if (y0<z0) {i1=0;j1=0;k1=1;i2=0;j2=1;k2=1;}
      else if (x0<z0) {i1=0;j1=1;k1=0;i2=0;j2=1;k2=1;}
      else {i1=0;j1=1;k1=0;i2=1;j2=1;k2=0;}
    }

    const x1=x0-i1+G3, y1=y0-j1+G3, z1=z0-k1+G3;
    const x2=x0-i2+2*G3, y2=y0-j2+2*G3, z2=z0-k2+2*G3;
    const x3=x0-1+3*G3, y3=y0-1+3*G3, z3=z0-1+3*G3;

    const ii=i&255, jj=j&255, kk=k&255;
    const gi0=this.perm[ii+this.perm[jj+this.perm[kk]]]%12;
    const gi1=this.perm[ii+i1+this.perm[jj+j1+this.perm[kk+k1]]]%12;
    const gi2=this.perm[ii+i2+this.perm[jj+j2+this.perm[kk+k2]]]%12;
    const gi3=this.perm[ii+1+this.perm[jj+1+this.perm[kk+1]]]%12;

    let n0,n1,n2,n3;
    let t0=0.6-x0*x0-y0*y0-z0*z0;
    n0 = t0<0 ? 0 : (t0*=t0, t0*t0*this.dot(this.grad3[gi0],x0,y0,z0));
    let t1=0.6-x1*x1-y1*y1-z1*z1;
    n1 = t1<0 ? 0 : (t1*=t1, t1*t1*this.dot(this.grad3[gi1],x1,y1,z1));
    let t2=0.6-x2*x2-y2*y2-z2*z2;
    n2 = t2<0 ? 0 : (t2*=t2, t2*t2*this.dot(this.grad3[gi2],x2,y2,z2));
    let t3=0.6-x3*x3-y3*y3-z3*z3;
    n3 = t3<0 ? 0 : (t3*=t3, t3*t3*this.dot(this.grad3[gi3],x3,y3,z3));

    return 32*(n0+n1+n2+n3);
  }
}

export class VoiceOrb {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.state = ORB_STATES.IDLE;
    this.targetState = ORB_STATES.IDLE;
    this.amplitude = 0;
    this.targetAmplitude = 0;
    this.analyser = null;
    this.analyserData = null;
    this.playbackAnalyser = null;
    this.playbackData = null;
    this.noise = new SimplexNoise();
    this.time = 0;
    this.transitionProgress = 1;
    this.useThreeJS = false;
    this.isSmall = false;
    this.animationId = null;

    // Color configs per state
    this.stateColors = {
      idle: { r: 0, g: 0.94, b: 1, glow: 'rgba(0,240,255,0.3)' },
      listening: { r: 0, g: 0.94, b: 1, glow: 'rgba(0,240,255,0.6)' },
      thinking: { r: 0.66, g: 0.33, b: 0.97, glow: 'rgba(168,85,247,0.5)' },
      speaking: { r: 0.66, g: 0.33, b: 0.97, glow: 'rgba(168,85,247,0.6)' }
    };

    this.init();
  }

  init() {
    if (typeof THREE !== 'undefined') {
      try {
        this.initThreeJS();
        this.useThreeJS = true;
      } catch (e) {
        console.warn('[VoiceOrb] Three.js init failed, using CSS fallback:', e);
        this.initCSSFallback();
      }
    } else {
      console.warn('[VoiceOrb] Three.js not loaded, using CSS fallback');
      this.initCSSFallback();
    }
    this.animate();
  }

  initThreeJS() {
    const w = this.container.clientWidth || 200;
    const h = this.container.clientHeight || 200;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    this.camera.position.z = 4;

    this.renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x000000, 0);
    this.container.appendChild(this.renderer.domElement);

    // Icosphere geometry
    const geometry = new THREE.IcosahedronGeometry(1, 4);
    this.basePositions = geometry.attributes.position.array.slice();

    // Custom shader material
    this.material = new THREE.MeshPhongMaterial({
      color: new THREE.Color(0, 0.94, 1),
      emissive: new THREE.Color(0, 0.3, 0.4),
      shininess: 100,
      transparent: true,
      opacity: 0.85,
      wireframe: false
    });

    this.mesh = new THREE.Mesh(geometry, this.material);
    this.scene.add(this.mesh);

    // Wireframe overlay
    const wireMat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(0, 0.94, 1),
      wireframe: true,
      transparent: true,
      opacity: 0.15
    });
    this.wireframe = new THREE.Mesh(geometry.clone(), wireMat);
    this.wireframe.scale.set(1.01, 1.01, 1.01);
    this.scene.add(this.wireframe);

    // Outer glow sphere
    const glowGeo = new THREE.IcosahedronGeometry(1.3, 3);
    const glowMat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(0, 0.94, 1),
      transparent: true,
      opacity: 0.05,
      side: THREE.BackSide
    });
    this.glowMesh = new THREE.Mesh(glowGeo, glowMat);
    this.scene.add(this.glowMesh);

    // Lights
    const ambientLight = new THREE.AmbientLight(0x404060, 0.5);
    this.scene.add(ambientLight);
    const pointLight = new THREE.PointLight(0x00f0ff, 1.5, 10);
    pointLight.position.set(2, 2, 3);
    this.scene.add(pointLight);
    this.pointLight = pointLight;

    const backLight = new THREE.PointLight(0xa855f7, 0.8, 10);
    backLight.position.set(-2, -1, -2);
    this.scene.add(backLight);
    this.backLight = backLight;

    // Waveform ring (for listening state)
    this.waveformRing = this.createWaveformRing();
    this.scene.add(this.waveformRing);
    this.waveformRing.visible = false;

    // Ripple rings (for speaking state)
    this.rippleRings = [];
    for (let i = 0; i < 3; i++) {
      const ring = this.createRippleRing();
      ring.visible = false;
      ring.userData.progress = i * 0.33;
      this.scene.add(ring);
      this.rippleRings.push(ring);
    }

    // Handle resize
    this._resizeHandler = () => {
      const w = this.container.clientWidth;
      const h = this.container.clientHeight;
      if (w && h) {
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
      }
    };
    window.addEventListener('resize', this._resizeHandler);
  }

  createWaveformRing() {
    const segments = 64;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(segments * 3);
    const radius = 1.6;
    for (let i = 0; i < segments; i++) {
      const angle = (i / segments) * Math.PI * 2;
      positions[i * 3] = Math.cos(angle) * radius;
      positions[i * 3 + 1] = Math.sin(angle) * radius;
      positions[i * 3 + 2] = 0;
    }
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.LineBasicMaterial({
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.6
    });
    const ring = new THREE.LineLoop(geometry, material);
    ring.userData.basePositions = positions.slice();
    ring.userData.segments = segments;
    return ring;
  }

  createRippleRing() {
    const geometry = new THREE.RingGeometry(1.2, 1.25, 64);
    const material = new THREE.MeshBasicMaterial({
      color: 0xa855f7,
      transparent: true,
      opacity: 0.4,
      side: THREE.DoubleSide
    });
    return new THREE.Mesh(geometry, material);
  }

  initCSSFallback() {
    this.cssOrb = document.createElement('div');
    this.cssOrb.className = 'css-orb';
    this.cssOrb.innerHTML = `
      <div class="css-orb-core"></div>
      <div class="css-orb-glow"></div>
      <div class="css-orb-ring"></div>
      <div class="css-orb-ripple css-orb-ripple-1"></div>
      <div class="css-orb-ripple css-orb-ripple-2"></div>
      <div class="css-orb-ripple css-orb-ripple-3"></div>
    `;
    this.container.appendChild(this.cssOrb);
  }

  setState(newState) {
    if (newState === this.state) return;
    this.targetState = newState;
    this.transitionProgress = 0;

    // Update CSS fallback classes
    if (this.cssOrb) {
      this.cssOrb.className = 'css-orb css-orb-' + newState;
    }

    // Update container data attribute for external CSS
    this.container.dataset.orbState = newState;
    this.state = newState;
  }

  connectMicAnalyser(stream) {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const source = ctx.createMediaStreamSource(stream);
      this.analyser = ctx.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.7;
      source.connect(this.analyser);
      this.analyserData = new Uint8Array(this.analyser.frequencyBinCount);
    } catch (e) {
      console.warn('[VoiceOrb] Could not create mic analyser:', e);
    }
  }

  connectPlaybackAnalyser(audioContext) {
    try {
      this.playbackAnalyser = audioContext.createAnalyser();
      this.playbackAnalyser.fftSize = 256;
      this.playbackAnalyser.smoothingTimeConstant = 0.7;
      this.playbackData = new Uint8Array(this.playbackAnalyser.frequencyBinCount);
      return this.playbackAnalyser;
    } catch (e) {
      console.warn('[VoiceOrb] Could not create playback analyser:', e);
      return null;
    }
  }

  getAmplitude() {
    let data = null;
    let analyser = null;

    if (this.state === ORB_STATES.LISTENING && this.analyser && this.analyserData) {
      analyser = this.analyser;
      data = this.analyserData;
    } else if (this.state === ORB_STATES.SPEAKING && this.playbackAnalyser && this.playbackData) {
      analyser = this.playbackAnalyser;
      data = this.playbackData;
    }

    if (analyser && data) {
      analyser.getByteFrequencyData(data);
      let sum = 0;
      for (let i = 0; i < data.length; i++) sum += data[i];
      return sum / data.length / 255;
    }
    return 0;
  }

  animate() {
    this.animationId = requestAnimationFrame(() => this.animate());
    this.time += 0.016;

    // Smooth amplitude
    this.targetAmplitude = this.getAmplitude();
    this.amplitude += (this.targetAmplitude - this.amplitude) * 0.15;

    // Smooth transition
    if (this.transitionProgress < 1) {
      this.transitionProgress = Math.min(1, this.transitionProgress + 0.03);
    }

    if (this.useThreeJS) {
      this.updateThreeJS();
    }
  }

  updateThreeJS() {
    const state = this.state;
    const colors = this.stateColors[state];
    const positions = this.mesh.geometry.attributes.position.array;
    const base = this.basePositions;

    // Displacement parameters per state
    let noiseScale, noiseSpeed, displacementAmt, breathAmt, rotSpeed;

    switch (state) {
      case ORB_STATES.IDLE:
        noiseScale = 1.5;
        noiseSpeed = 0.3;
        displacementAmt = 0.05;
        breathAmt = 0.03 * Math.sin(this.time * 1.2);
        rotSpeed = 0.001;
        break;
      case ORB_STATES.LISTENING:
        noiseScale = 2.0;
        noiseSpeed = 0.8;
        displacementAmt = 0.08 + this.amplitude * 0.35;
        breathAmt = 0.02 * Math.sin(this.time * 2);
        rotSpeed = 0.003;
        break;
      case ORB_STATES.THINKING:
        noiseScale = 1.8;
        noiseSpeed = 1.5;
        displacementAmt = 0.12;
        breathAmt = 0.04 * Math.sin(this.time * 3);
        rotSpeed = 0.008;
        break;
      case ORB_STATES.SPEAKING:
        noiseScale = 1.6;
        noiseSpeed = 0.6;
        displacementAmt = 0.06 + this.amplitude * 0.25;
        breathAmt = 0.02 * Math.sin(this.time * 1.5);
        rotSpeed = 0.002;
        break;
    }

    // Apply vertex displacement
    for (let i = 0; i < positions.length; i += 3) {
      const bx = base[i], by = base[i+1], bz = base[i+2];
      const len = Math.sqrt(bx*bx + by*by + bz*bz);
      const nx = bx/len, ny = by/len, nz = bz/len;
      const noiseVal = this.noise.noise3d(
        nx * noiseScale + this.time * noiseSpeed,
        ny * noiseScale + this.time * noiseSpeed * 0.7,
        nz * noiseScale + this.time * noiseSpeed * 0.5
      );
      const displacement = 1 + noiseVal * displacementAmt + breathAmt;
      positions[i] = bx * displacement;
      positions[i+1] = by * displacement;
      positions[i+2] = bz * displacement;
    }
    this.mesh.geometry.attributes.position.needsUpdate = true;

    // Rotate
    this.mesh.rotation.y += rotSpeed;
    this.mesh.rotation.x += rotSpeed * 0.3;
    this.wireframe.rotation.copy(this.mesh.rotation);

    // Update wireframe geometry to match
    const wfPositions = this.wireframe.geometry.attributes.position.array;
    for (let i = 0; i < positions.length; i++) {
      wfPositions[i] = positions[i] * 1.01;
    }
    this.wireframe.geometry.attributes.position.needsUpdate = true;

    // Colors
    this.material.color.lerp(new THREE.Color(colors.r, colors.g, colors.b), 0.05);
    this.material.emissive.lerp(new THREE.Color(colors.r * 0.4, colors.g * 0.4, colors.b * 0.4), 0.05);
    this.wireframe.material.color.lerp(new THREE.Color(colors.r, colors.g, colors.b), 0.05);
    this.glowMesh.material.color.lerp(new THREE.Color(colors.r, colors.g, colors.b), 0.05);
    this.pointLight.color.lerp(new THREE.Color(colors.r, colors.g, colors.b), 0.05);

    // Glow opacity based on state
    const glowTarget = state === ORB_STATES.IDLE ? 0.05 : (state === ORB_STATES.LISTENING ? 0.12 + this.amplitude * 0.15 : 0.1);
    this.glowMesh.material.opacity += (glowTarget - this.glowMesh.material.opacity) * 0.05;

    // Glow scale pulse
    const glowScale = 1.3 + breathAmt * 2 + this.amplitude * 0.3;
    this.glowMesh.scale.set(glowScale, glowScale, glowScale);

    // Waveform ring (listening)
    const showRing = state === ORB_STATES.LISTENING;
    this.waveformRing.visible = showRing;
    if (showRing) {
      this.updateWaveformRing();
    }

    // Ripple rings (speaking)
    const showRipples = state === ORB_STATES.SPEAKING;
    this.rippleRings.forEach((ring, i) => {
      ring.visible = showRipples;
      if (showRipples) {
        ring.userData.progress += 0.008 + this.amplitude * 0.01;
        if (ring.userData.progress > 1) ring.userData.progress = 0;
        const p = ring.userData.progress;
        const scale = 1.2 + p * 1.5;
        ring.scale.set(scale, scale, scale);
        ring.material.opacity = (1 - p) * 0.4 * (0.5 + this.amplitude);
      }
    });

    this.renderer.render(this.scene, this.camera);
  }

  updateWaveformRing() {
    const positions = this.waveformRing.geometry.attributes.position.array;
    const base = this.waveformRing.userData.basePositions;
    const segments = this.waveformRing.userData.segments;
    const data = this.analyserData;

    for (let i = 0; i < segments; i++) {
      const dataIndex = Math.floor((i / segments) * (data ? data.length : 1));
      const val = data ? data[dataIndex] / 255 : 0;
      const radius = 1.6 + val * 0.3;
      const angle = (i / segments) * Math.PI * 2;
      positions[i * 3] = Math.cos(angle) * radius;
      positions[i * 3 + 1] = Math.sin(angle) * radius;
    }
    this.waveformRing.geometry.attributes.position.needsUpdate = true;
    this.waveformRing.rotation.z += 0.002;
    this.waveformRing.material.opacity = 0.3 + this.amplitude * 0.5;
  }

  setSmall(small) {
    if (this.isSmall === small) return;
    this.isSmall = small;
    if (this.useThreeJS && this.camera) {
      this.camera.position.z = small ? 5 : 4;
      this._resizeHandler();
    }
  }

  destroy() {
    if (this.animationId) cancelAnimationFrame(this.animationId);
    if (this._resizeHandler) window.removeEventListener('resize', this._resizeHandler);
    if (this.renderer) {
      this.renderer.dispose();
      this.renderer.domElement.remove();
    }
  }
}

export { ORB_STATES };
