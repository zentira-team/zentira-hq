/**
 * Kantor Virtual 3D Voxel v2 — Ruangan Studio Luas (30 x 22) + Lingkungan Kota & Taman Hidup.
 * Mengikuti praktik threejs-lighting, threejs-materials, threejs-textures, dan threejs-performance
 * (InstancedMesh untuk pohon/semak/bunga, procedural CanvasTexture lantai kayu, sky dome + fog horizon).
 */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const UNIT_BOX = new THREE.BoxGeometry(1, 1, 1);

const CAM_PRESETS = {
  iso: {
    pos: new THREE.Vector3(25, 20.5, 27),
    target: new THREE.Vector3(0.5, 1.5, 0.0),
  },
  indoor: {
    pos: new THREE.Vector3(9.4, 5.4, 8.8),
    target: new THREE.Vector3(-1.6, 1.8, -3.2),
  },
  outdoor: {
    pos: new THREE.Vector3(26, 15.5, 34),
    target: new THREE.Vector3(0.0, 2.8, 4.5),
  },
};

const DESK_LAYOUT = {
  manager: {
    desk: [-10.2, -8.2],
    chair: [-10.2, -6.55],
    lounge: [-9.2, -5.65],
    color: 0xf43f5e,
    shirt: 0x111114,
    pants: 0x09090b,
    hair: 0x16171d,
    skin: 0xfde2c8,
    outfit: "suit",
    accessory: "blindfold",
    prop: "executive",
  },
  trend: {
    desk: [-3.2, -7.2],
    chair: [-3.2, -5.6],
    lounge: [-9.8, 2.2],
    color: 0x38bdf8,
    shirt: 0x0284c7,
    pants: 0x1e293b,
    hair: 0x451a03,
    skin: 0xfde2c8,
    accessory: "glasses",
    prop: "globe",
  },
  repurpose: {
    desk: [3.2, -7.2],
    chair: [3.2, -5.6],
    lounge: [-7.4, -2.4],
    color: 0xf472b6,
    shirt: 0xdb2777,
    pants: 0x334155,
    hair: 0x1e1b4b,
    skin: 0xfad7b8,
    accessory: "headphones",
    prop: "clapper",
  },
  leads: {
    desk: [9.8, -7.2],
    chair: [9.8, -5.6],
    lounge: [-0.8, 3.4],
    color: 0x34d399,
    shirt: 0x059669,
    pants: 0x1e293b,
    hair: 0x3f2305,
    skin: 0xf5cba7,
    accessory: "cap",
    prop: "pin",
  },
  finance: {
    desk: [3.6, 5.0],
    chair: [3.6, 6.6],
    lounge: [-7.2, 6.6],
    color: 0xfbbf24,
    shirt: 0xd97706,
    pants: 0x1e293b,
    hair: 0x27272a,
    skin: 0xfde2c8,
    accessory: "glasses",
    prop: "coins",
  },
  cs: {
    desk: [9.8, 5.0],
    chair: [9.8, 6.6],
    lounge: [6.4, -0.4],
    color: 0xa78bfa,
    shirt: 0x7c3aed,
    pants: 0x312e81,
    hair: 0x4a2511,
    skin: 0xfad7b8,
    accessory: "headset",
    prop: "heart",
  },
};

const MEETING_SEATS = {
  manager: { pos: [-2.4, -0.8], yaw: Math.PI / 2 },
  trend: { pos: [-0.35, -2.45], yaw: 0 },
  repurpose: { pos: [1.95, -2.45], yaw: 0 },
  leads: { pos: [-0.35, 0.85], yaw: Math.PI },
  finance: { pos: [1.95, 0.85], yaw: Math.PI },
  cs: { pos: [4.0, -0.8], yaw: -Math.PI / 2 },
};

const MEETING_CHAT_LINES = {
  manager: [
    "Oke tim, kita rapikan target Zentira hari ini!",
    "Siap eksekusi arahan Founder secepatnya!",
    "Konten Denn & Miki + web UMKM jalan bareng ya.",
  ],
  trend: [
    "Tren Indonesia hari ini ada beberapa topik segar!",
    "Aku sudah siapkan 3 ide cerita yang relate.",
  ],
  repurpose: [
    "Siap langsung racik paket TikTok, Reels & Shorts!",
    "Hook 3 detiknya sudah kupastikan nendang.",
  ],
  leads: [
    "Ada beberapa UMKM potensial tanpa website nih!",
    "Draf penawaran WA siap dikirim begitu ACC.",
  ],
  finance: [
    "Buku kas, DP, & pengingat pelunasan aman rapi!",
    "Kalau ada invoice baru tinggal bilang aja ya.",
  ],
  cs: [
    "Rate card & checklist QC brief endorse siap!",
    "Balasan klien bakal kubuat cepat dan ramah.",
  ],
};

const DEPART_LINES = [
  "Sampai besok Bos!",
  "Waktunya istirahat, hati-hati ya!",
  "Otw pulang naik Shuttle Zentira!",
  "Kantor beres, kita cabut dulu!",
];

const ARRIVE_LINES = [
  "Pagi Bos! Siap kerja!",
  "Zentira HQ buka, semangat tim!",
  "Ngopi dulu lalu gas eksekusi!",
  "Siap menerima tugas hari ini!",
];

const materialCache = new Map();

function getStandardMat(color, opts = {}) {
  const key = `${color}_${opts.roughness ?? 0.8}_${opts.metalness ?? 0.05}_${opts.emissive ?? 0}_${opts.emissiveIntensity ?? 0}_${opts.opacity ?? 1}`;
  if (!opts.unique && materialCache.has(key)) {
    return materialCache.get(key);
  }
  const mat = new THREE.MeshStandardMaterial({
    color,
    roughness: opts.roughness ?? 0.8,
    metalness: opts.metalness ?? 0.05,
    emissive: opts.emissive ?? 0x000000,
    emissiveIntensity: opts.emissiveIntensity ?? 0,
    transparent: opts.opacity !== undefined && opts.opacity < 1,
    opacity: opts.opacity ?? 1,
  });
  if (!opts.unique) materialCache.set(key, mat);
  return mat;
}

function makeBox(w, h, d, color, opts = {}) {
  const mat = getStandardMat(color, opts);
  const mesh = new THREE.Mesh(UNIT_BOX, mat);
  mesh.scale.set(w, h, d);
  mesh.castShadow = opts.castShadow ?? true;
  mesh.receiveShadow = opts.receiveShadow ?? true;
  return mesh;
}

function makeWoodFloorTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext("2d");

  const planks = 8;
  const plankH = 512 / planks;
  const palette = ["#e8cba3", "#e2c093", "#ecd3af", "#dcb786", "#e5c69b"];

  for (let i = 0; i < planks; i++) {
    const y = i * plankH;
    ctx.fillStyle = palette[i % palette.length];
    ctx.fillRect(0, y, 512, plankH);

    // Subtle wood grain lines
    ctx.fillStyle = "rgba(120, 72, 32, 0.06)";
    for (let g = 0; g < 6; g++) {
      ctx.fillRect(0, y + 6 + g * 9, 512, 2);
    }

    // Plank seam
    ctx.fillStyle = "rgba(105, 65, 30, 0.18)";
    ctx.fillRect(0, y + plankH - 2, 512, 2);

    // Staggered vertical plank joint
    const jointX = ((i * 173 + 90) % 440) + 36;
    ctx.fillRect(jointX, y, 2, plankH);
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(6, 4.5);
  return tex;
}

function makeGrassTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#84c772";
  ctx.fillRect(0, 0, 256, 256);

  const cell = 32;
  for (let x = 0; x < 256; x += cell) {
    for (let y = 0; y < 256; y += cell) {
      const shade = ((x / cell + y / cell) % 2 === 0) ? "rgba(255,255,255,0.05)" : "rgba(0,40,0,0.05)";
      ctx.fillStyle = shade;
      ctx.fillRect(x, y, cell, cell);
    }
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(22, 22);
  return tex;
}

function drawZentiraSign(canvas, logoImg) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.fillStyle = "#111114";
  ctx.fillRect(0, 0, w, h);

  // Subtle architectural hairline border
  ctx.strokeStyle = "#27272a";
  ctx.lineWidth = 8;
  ctx.strokeRect(12, 12, w - 24, h - 24);

  // Left logo emblem (blend seamlessly into matte obsidian with 'lighten')
  const logoSize = 152;
  const logoX = 76;
  const logoY = Math.round((h - logoSize) / 2);
  if (logoImg && logoImg.complete && logoImg.naturalWidth > 0) {
    ctx.save();
    ctx.globalCompositeOperation = "lighten";
    ctx.drawImage(logoImg, logoX, logoY, logoSize, logoSize);
    ctx.restore();
  } else {
    ctx.fillStyle = "#ffffff";
    ctx.font = "900 108px Inter, Segoe UI, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("Z", logoX + logoSize / 2, h / 2 + 4);
  }

  // Clean single-line studio title: ZENTIRA TEAM (no subtitle!)
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillStyle = "#fafafa";
  ctx.font = "800 84px Inter, Segoe UI, sans-serif";
  ctx.fillText("ZENTIRA TEAM", 272, h / 2 + 4);
  ctx.textBaseline = "alphabetic";
}

function makeSignTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 240;
  drawZentiraSign(canvas, null);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  const wallLogo = new Image();
  wallLogo.crossOrigin = "anonymous";
  wallLogo.onload = () => {
    drawZentiraSign(canvas, wallLogo);
    tex.needsUpdate = true;
  };
  wallLogo.src = "/static/assets/zentira-wall.png";
  return { canvas, tex };
}

function makeFounderPlaqueTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 168;
  const ctx = canvas.getContext("2d");

  // Matte obsidian architectural plaque background
  ctx.fillStyle = "#111114";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Brushed champagne-gold inner hairline frame
  ctx.strokeStyle = "#d4af37";
  ctx.lineWidth = 4;
  ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);
  ctx.strokeStyle = "rgba(212, 175, 55, 0.35)";
  ctx.lineWidth = 2;
  ctx.strokeRect(20, 20, canvas.width - 40, canvas.height - 40);

  // Eyebrow title with minimal flanking gold rules
  ctx.textAlign = "center";
  ctx.fillStyle = "#e6c767";
  ctx.font = "700 22px Inter, Segoe UI, sans-serif";
  ctx.fillText("✦   F O U N D E R   ✦", canvas.width / 2, 62);

  // Founder full name
  ctx.fillStyle = "#fafafa";
  ctx.font = "800 44px Inter, Segoe UI, sans-serif";
  ctx.fillText("RADEN SATRIA JAYA WINATA", canvas.width / 2, 122);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeFounderDeskPlateTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 112;
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = "#111114";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#d4af37";
  ctx.lineWidth = 4;
  ctx.strokeRect(6, 6, canvas.width - 12, canvas.height - 12);

  ctx.textAlign = "center";
  ctx.fillStyle = "#e6c767";
  ctx.font = "700 18px Inter, Segoe UI, sans-serif";
  ctx.fillText("FOUNDER  •  ZENTIRA", canvas.width / 2, 42);

  ctx.fillStyle = "#fafafa";
  ctx.font = "700 25px Inter, Segoe UI, sans-serif";
  ctx.fillText("Raden Satria Jaya Winata", canvas.width / 2, 82);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeRoomPlaqueTexture(eyebrow, title) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 112;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#111114";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#d4af37";
  ctx.lineWidth = 4;
  ctx.strokeRect(6, 6, canvas.width - 12, canvas.height - 12);
  ctx.textAlign = "center";
  ctx.fillStyle = "#e6c767";
  ctx.font = "700 18px Inter, Segoe UI, sans-serif";
  ctx.fillText(eyebrow, canvas.width / 2, 42);
  ctx.fillStyle = "#fafafa";
  ctx.font = "800 30px Inter, Segoe UI, sans-serif";
  ctx.fillText(title, canvas.width / 2, 84);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeShuttleLogoTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#18181b";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#ec4899";
  ctx.fillRect(0, 106, canvas.width, 10);
  ctx.fillStyle = "#d4af37";
  ctx.fillRect(0, 96, canvas.width, 6);
  ctx.textAlign = "center";
  ctx.fillStyle = "#fafafa";
  ctx.font = "900 42px Inter, Segoe UI, sans-serif";
  ctx.fillText("ZENTIRA", canvas.width / 2, 54);
  ctx.fillStyle = "#d4d4d8";
  ctx.font = "700 20px Inter, Segoe UI, sans-serif";
  ctx.fillText("STUDIO SHUTTLE  •  HQ", canvas.width / 2, 84);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function drawInstagramPlaque(canvas, igImg) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.fillStyle = "#111114";
  ctx.fillRect(0, 0, w, h);

  // Subtle architectural border
  ctx.strokeStyle = "#27272a";
  ctx.lineWidth = 6;
  ctx.strokeRect(8, 8, w - 16, h - 16);

  // Signature Instagram gradient accent bar along bottom edge
  const grad = ctx.createLinearGradient(28, 0, w - 28, 0);
  grad.addColorStop(0.0, "#feda75");
  grad.addColorStop(0.32, "#fa7e1e");
  grad.addColorStop(0.65, "#d62976");
  grad.addColorStop(1.0, "#962fbf");
  ctx.fillStyle = grad;
  ctx.fillRect(28, h - 20, w - 56, 7);

  // Rounded Instagram icon on left
  const ix = 44;
  const iy = 38;
  const isize = 122;
  const r = 28;
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(ix + r, iy);
  ctx.lineTo(ix + isize - r, iy);
  ctx.quadraticCurveTo(ix + isize, iy, ix + isize, iy + r);
  ctx.lineTo(ix + isize, iy + isize - r);
  ctx.quadraticCurveTo(ix + isize, iy + isize, ix + isize - r, iy + isize);
  ctx.lineTo(ix + r, iy + isize);
  ctx.quadraticCurveTo(ix, iy + isize, ix, iy + isize - r);
  ctx.lineTo(ix, iy + r);
  ctx.quadraticCurveTo(ix, iy, ix + r, iy);
  ctx.closePath();
  ctx.clip();

  if (igImg && igImg.complete && igImg.naturalWidth > 0) {
    ctx.drawImage(igImg, ix, iy, isize, isize);
  } else {
    const iconGrad = ctx.createLinearGradient(ix, iy + isize, ix + isize, iy);
    iconGrad.addColorStop(0, "#feda75");
    iconGrad.addColorStop(0.35, "#fa7e1e");
    iconGrad.addColorStop(0.7, "#d62976");
    iconGrad.addColorStop(1, "#4f5bd5");
    ctx.fillStyle = iconGrad;
    ctx.fillRect(ix, iy, isize, isize);
  }
  ctx.restore();

  // Crisp Swiss typography for handle
  ctx.textAlign = "left";
  ctx.fillStyle = "#a1a1aa";
  ctx.font = "700 22px Inter, Segoe UI, sans-serif";
  ctx.fillText("INSTAGRAM  •  FOUNDER", 196, 82);

  ctx.fillStyle = "#ffffff";
  ctx.font = "800 54px Inter, Segoe UI, sans-serif";
  ctx.fillText("@quietdenn", 194, 144);
}

function makeInstagramPlaqueTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 640;
  canvas.height = 208;
  drawInstagramPlaque(canvas, null);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = () => {
    drawInstagramPlaque(canvas, img);
    tex.needsUpdate = true;
  };
  img.src = "/static/assets/instagram.jpg";
  return tex;
}

function makeSkyTexture(topHex, midHex, botHex) {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  const grad = ctx.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0.0, topHex);
  grad.addColorStop(0.52, midHex);
  grad.addColorStop(1.0, botHex);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 64, 256);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

export class VoxelOffice3D {
  constructor(canvas, bubbleLayer, onSelectAgent, onDismissAgent = null) {
    this.canvas = canvas;
    this.bubbleLayer = bubbleLayer;
    this.onSelectAgent = onSelectAgent;
    this.onDismissAgent = onDismissAgent;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xcde6fb);
    this.scene.fog = new THREE.Fog(0xdceefb, 62, 165);

    this.isMobile =
      window.innerWidth <= 768 ||
      Boolean(window.matchMedia && window.matchMedia("(pointer: coarse)").matches);

    const aspect = window.innerWidth / window.innerHeight;
    const initFov = aspect < 0.85 ? 45 : 36;
    this.camera = new THREE.PerspectiveCamera(initFov, aspect, 0.2, 240);
    this.camera.position.copy(CAM_PRESETS.iso.pos);

    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      powerPreference: this.isMobile ? "default" : "high-performance",
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.isMobile ? 1.5 : 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.04;

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.maxPolarAngle = Math.PI / 2.08;
    this.controls.minDistance = 2.5;
    this.controls.maxDistance = 95;
    this.controls.zoomSpeed = this.isMobile ? 1.25 : 1.15;
    this.controls.rotateSpeed = this.isMobile ? 0.85 : 1.0;
    this.controls.target.copy(CAM_PRESETS.iso.target);

    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();
    this.clickables = [];
    this.agents3d = {};
    this.clouds = [];
    this.cars = [];
    this.steamBits = [];
    this.nightWindowMeshes = [];
    this.lampBulbs = [];
    this.lampLights = [];
    this.pendantLights = [];
    this.selectedAgentId = null;
    this.hoveredAgentId = null;
    this.clock = new THREE.Clock();
    this.camLerpPos = null;
    this.camLerpTarget = null;
    this.isPointerDragging = false;
    this.pointerDownPos = { x: 0, y: 0 };

    // Enclosed studio, office mode (work/meeting/holiday) & Shuttle Van choreography state
    this.currentTheme = "day";
    this.activeCamPreset = "iso";
    this.roofMode = "auto";
    this.officeMode = "work";
    this.prevOfficeMode = null;
    this.lastModeSeq = -1;
    this.commuteState = "at_office";
    this.unboardQueue = [];
    this.unboardTimer = 0;
    this.doorOpenAmount = 0;
    this.vanDoorOpenAmount = 0;
    this.meetingSpeakerOrder = ["manager", "trend", "repurpose", "leads", "finance", "cs"];
    this.meetingSpeakerIdx = 0;
    this.meetingChatTimer = 1.6;
    this.meetingChatLineIdx = 0;

    // External Cinema Engine deterministic simulation hooks
    this.simTime = 0;
    this.externalRenderControl = false;

    this.skyDayTex = makeSkyTexture("#60a5fa", "#bae6fd", "#eef6ff");
    this.skyNightTex = makeSkyTexture("#050816", "#111b36", "#1e1b4b");

    this._setupSkyDome();
    this._setupLights();
    this._buildOutdoorWorld();
    this._buildSpaciousStudio();
    this._buildInteriorZones();
    this._buildShuttleVan();
    this._buildAllWorkstationsAndAgents();
    this._updateEnclosureVisibility();
    this._bindEvents();
    this._animate();
  }

  _setupSkyDome() {
    const geo = new THREE.SphereGeometry(130, 24, 16);
    const mat = new THREE.MeshBasicMaterial({
      map: this.skyDayTex,
      side: THREE.BackSide,
      fog: false,
    });
    this.skyDome = new THREE.Mesh(geo, mat);
    this.scene.add(this.skyDome);
  }

  _setupLights() {
    this.hemiLight = new THREE.HemisphereLight(0xf0f9ff, 0x8d7b68, 0.85);
    this.scene.add(this.hemiLight);

    this.ambientLight = new THREE.AmbientLight(0xffffff, 0.42);
    this.scene.add(this.ambientLight);

    this.sunLight = new THREE.DirectionalLight(0xfff7ed, 1.55);
    this.sunLight.position.set(22, 32, 18);
    this.sunLight.castShadow = true;
    const shadowRes = this.isMobile ? 1024 : 2048;
    this.sunLight.shadow.mapSize.set(shadowRes, shadowRes);
    this.sunLight.shadow.camera.near = 4;
    this.sunLight.shadow.camera.far = 92;
    const d = 28;
    this.sunLight.shadow.camera.left = -d;
    this.sunLight.shadow.camera.right = d;
    this.sunLight.shadow.camera.top = d;
    this.sunLight.shadow.camera.bottom = -d;
    this.sunLight.shadow.normalBias = 0.04;
    this.sunLight.shadow.bias = -0.0003;
    this.scene.add(this.sunLight);

    // Grounded interior fill lights positioned at floor lamps & wall sconces (no floating fixtures!)
    for (const [px, py, pz] of [
      [-13.2, 3.3, 8.6],
      [-5.6, 3.8, -10.3],
      [3.6, 3.8, -10.3],
      [13.4, 3.3, 8.6],
      [-10.2, 6.8, -7.8],
      [0.8, 7.2, -0.5],
    ]) {
      const pLight = new THREE.PointLight(0xffdfb0, 14, 22, 2);
      pLight.position.set(px, py, pz);
      this.scene.add(pLight);
      this.pendantLights.push(pLight);
    }
  }

  setBrandLogo(logoUrl) {
    if (!this.signCanvas || !this.signTex) return;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      drawZentiraSign(this.signCanvas, img);
      this.signTex.needsUpdate = true;
    };
    img.src = logoUrl;
  }

  _applyInteriorLights() {
    const isNight = this.currentTheme === "night";
    const isClosed = this.commuteState === "on_holiday";
    const baseInterior = isClosed ? (isNight ? 7 : 3) : (isNight ? 54 : 18);
    this.pendantLights.forEach((l) => (l.intensity = baseInterior));
    if (this.neonStrip) {
      this.neonStrip.material.emissiveIntensity = isClosed ? 0.12 : (isNight ? 1.65 : 0.48);
    }
  }

  setTheme(mode) {
    this.currentTheme = mode === "night" ? "night" : "day";
    const isNight = this.currentTheme === "night";
    this.skyDome.material.map = isNight ? this.skyNightTex : this.skyDayTex;
    this.skyDome.material.needsUpdate = true;

    if (isNight) {
      this.scene.background.setHex(0x0b1024);
      this.scene.fog.color.setHex(0x111834);
      this.hemiLight.color.setHex(0x312e81);
      this.hemiLight.groundColor.setHex(0x1e293b);
      this.hemiLight.intensity = 0.45;
      this.ambientLight.intensity = 0.22;
      this.sunLight.color.setHex(0x818cf8);
      this.sunLight.intensity = 0.55;
      this.lampLights.forEach((l) => (l.intensity = 42));
      this.lampBulbs.forEach((m) => (m.material.emissiveIntensity = 1.8));
      this.nightWindowMeshes.forEach((m) => (m.material.emissiveIntensity = 0.95));
    } else {
      this.scene.background.setHex(0xcde6fb);
      this.scene.fog.color.setHex(0xdceefb);
      this.hemiLight.color.setHex(0xf0f9ff);
      this.hemiLight.groundColor.setHex(0x8d7b68);
      this.hemiLight.intensity = 0.88;
      this.ambientLight.intensity = 0.44;
      this.sunLight.color.setHex(0xfff7ed);
      this.sunLight.intensity = 1.55;
      this.lampLights.forEach((l) => (l.intensity = 0));
      this.lampBulbs.forEach((m) => (m.material.emissiveIntensity = 0.15));
      this.nightWindowMeshes.forEach((m) => (m.material.emissiveIntensity = 0.08));
    }
    this._applyInteriorLights();
  }

  setRoofMode(mode) {
    if (!["auto", "closed", "open"].includes(mode)) return;
    this.roofMode = mode;
    this._updateEnclosureVisibility();
  }

  _updateEnclosureVisibility() {
    if (!this.roofGroup || !this.frontWallGroup || !this.rightWallGroup) return;
    const cp = this.camera.position;
    const camInside =
      Math.abs(cp.x) < 14.7 && Math.abs(cp.z) < 10.7 && cp.y > 0.2 && cp.y < 8.65;

    let showEnclosed = false;
    if (this.roofMode === "closed") {
      showEnclosed = true;
    } else if (this.roofMode === "open") {
      showEnclosed = false;
    } else {
      // Auto mode: enclosed when inside the tall studio OR viewing the exterior building; cutaway in Isometric overview
      showEnclosed =
        camInside ||
        this.activeCamPreset === "indoor" ||
        this.activeCamPreset === "outdoor";
    }

    this.roofGroup.visible = showEnclosed;
    this.frontWallGroup.visible = showEnclosed;
    this.rightWallGroup.visible = showEnclosed;
    if (this.cutawayBorderGroup) {
      this.cutawayBorderGroup.visible = !showEnclosed;
    }
  }

  setCameraPreset(presetName) {
    this.activeCamPreset = CAM_PRESETS[presetName] ? presetName : "iso";
    const p = CAM_PRESETS[this.activeCamPreset];
    this.camLerpPos = p.pos.clone();
    this.camLerpTarget = p.target.clone();
    this._updateEnclosureVisibility();
  }

  // =====================================================
  // 1. OUTDOOR VOXEL WORLD (Courtyard, Trees, Street, Town)
  // =====================================================
  _buildOutdoorWorld() {
    const world = new THREE.Group();

    // Vast meadow ground (180 x 180) so horizon never shows empty void
    const grassTex = makeGrassTexture();
    grassTex.anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(190, 190),
      new THREE.MeshStandardMaterial({ map: grassTex, roughness: 0.95 })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.32;
    ground.receiveShadow = true;
    world.add(ground);

    // Stone courtyard terrace surrounding the studio building (38 x 30)
    const terrace = makeBox(38, 0.24, 30, 0xe2e8f0, { castShadow: false, roughness: 0.9 });
    terrace.position.set(0, -0.2, 0);
    world.add(terrace);

    // Wooden patio deck outside the front-left glass lounge
    const patio = makeBox(11, 0.12, 4.6, 0xc29360, { castShadow: false });
    patio.position.set(-9.5, -0.06, 13.5);
    world.add(patio);

    // Two-lane asphalt road wrapping Front (z = 21) & Right (x = 25) + Back (z = -21) + Left (x = -25)
    const roadMat = getStandardMat(0x334155, { roughness: 0.92 });
    const buildRoadSeg = (w, d, x, z) => {
      const m = new THREE.Mesh(UNIT_BOX, roadMat);
      m.scale.set(w, 0.08, d);
      m.position.set(x, -0.27, z);
      m.receiveShadow = true;
      world.add(m);
    };
    buildRoadSeg(96, 7.2, 0, 21.5);
    buildRoadSeg(96, 7.2, 0, -21.5);
    buildRoadSeg(7.2, 96, 25.5, 0);
    buildRoadSeg(7.2, 96, -25.5, 0);

    // Sidewalks bordering roads
    const walkMat = getStandardMat(0xcbd5e1, { roughness: 0.88 });
    const addWalk = (w, d, x, z) => {
      const m = new THREE.Mesh(UNIT_BOX, walkMat);
      m.scale.set(w, 0.16, d);
      m.position.set(x, -0.22, z);
      m.receiveShadow = true;
      world.add(m);
    };
    addWalk(44, 2.2, 0, 16.8);
    addWalk(44, 2.2, 0, -16.8);
    addWalk(2.2, 36, 20.8, 0);
    addWalk(2.2, 36, -20.8, 0);

    // Instanced road dashed lane markers (1 draw call!)
    const dashPositions = [];
    for (let x = -40; x <= 40; x += 4.5) {
      if (Math.abs(x) > 21 && Math.abs(x) < 29) continue;
      dashPositions.push([x, 21.5, 1.8, 0.22]);
      dashPositions.push([x, -21.5, 1.8, 0.22]);
    }
    for (let z = -40; z <= 40; z += 4.5) {
      if (Math.abs(z) > 17 && Math.abs(z) < 25) continue;
      dashPositions.push([25.5, z, 0.22, 1.8]);
      dashPositions.push([-25.5, z, 0.22, 1.8]);
    }
    const dashInst = new THREE.InstancedMesh(
      UNIT_BOX,
      getStandardMat(0xf8fafc, { roughness: 0.6 }),
      dashPositions.length
    );
    const dummy = new THREE.Object3D();
    dashPositions.forEach(([x, z, sx, sz], i) => {
      dummy.position.set(x, -0.22, z);
      dummy.scale.set(sx, 0.03, sz);
      dummy.updateMatrix();
      dashInst.setMatrixAt(i, dummy.matrix);
    });
    world.add(dashInst);

    // Instanced Voxel Trees (Oak + Sakura Blossom) around courtyard & neighborhood
    this._buildInstancedTrees(world);

    // Outdoor Park Benches & Street Lamps (positioned clear of the Front Shuttle Drop-Off Bay!)
    for (const [bx, bz, rot] of [[-17.2, 8.5, Math.PI / 2], [-17.2, -5.5, Math.PI / 2], [9.2, 14.2, 0]]) {
      const bench = new THREE.Group();
      bench.position.set(bx, -0.08, bz);
      bench.rotation.y = rot;
      const seat = makeBox(2.0, 0.14, 0.6, 0x92400e); seat.position.y = 0.45;
      const back = makeBox(2.0, 0.45, 0.12, 0x78350f); back.position.set(0, 0.72, -0.24);
      const l1 = makeBox(0.14, 0.44, 0.55, 0x334155); l1.position.set(-0.78, 0.22, 0);
      const l2 = makeBox(0.14, 0.44, 0.55, 0x334155); l2.position.set(0.78, 0.22, 0);
      bench.add(seat, back, l1, l2);
      world.add(bench);
    }

    // Crisp Front Entrance Walkway & Zentira Shuttle Drop-Off Pad
    const entryWalk = makeBox(4.2, 0.1, 4.8, 0xf1f5f9, { castShadow: false, roughness: 0.85 });
    entryWalk.position.set(0, -0.04, 13.5);
    const dropBay = makeBox(9.2, 0.09, 2.8, 0x1e293b, { castShadow: false, roughness: 0.92 });
    dropBay.position.set(0, -0.24, 17.5);
    const dropStripeL = makeBox(0.16, 0.03, 2.5, 0xfbbf24, { castShadow: false });
    dropStripeL.position.set(-4.3, -0.19, 17.5);
    const dropStripeR = makeBox(0.16, 0.03, 2.5, 0xfbbf24, { castShadow: false });
    dropStripeR.position.set(4.3, -0.19, 17.5);
    const dropCurb = makeBox(9.2, 0.05, 0.24, 0xfbbf24, { castShadow: false });
    dropCurb.position.set(0, -0.17, 16.05);
    world.add(entryWalk, dropBay, dropStripeL, dropStripeR, dropCurb);

    for (const [lx, lz] of [[-19.6, 15.8], [19.6, 15.8], [-19.6, -15.8], [19.6, -15.8], [-6.8, 15.4], [6.8, 15.4]]) {
      const lamp = new THREE.Group();
      lamp.position.set(lx, -0.1, lz);
      const pole = makeBox(0.18, 4.2, 0.18, 0x334155); pole.position.y = 2.1;
      const arm = makeBox(0.7, 0.14, 0.18, 0x334155); arm.position.set(0.25, 4.15, 0);
      const bulb = makeBox(0.36, 0.36, 0.36, 0xfef08a, {
        emissive: 0xfde047,
        emissiveIntensity: 0.15,
        unique: true,
        castShadow: false,
      });
      bulb.position.set(0.48, 3.92, 0);
      lamp.add(pole, arm, bulb);
      this.lampBulbs.push(bulb);

      const pLight = new THREE.PointLight(0xfde68a, 0, 14, 2);
      pLight.position.set(lx + 0.48, 3.6, lz);
      world.add(pLight);
      this.lampLights.push(pLight);
      world.add(lamp);
    }

    // Surrounding Cozy Voxel Neighborhood Buildings (so outside windows & skyline are rich & alive!)
    const buildings = [
      // Back side across road (visible right through studio back panoramic windows!)
      { x: -16, z: -33, w: 9, h: 10, d: 8, body: 0xfde68a, roof: 0xd97706, awning: 0xef4444 },
      { x: -4, z: -34, w: 10, h: 13.5, d: 8, body: 0xe0f2fe, roof: 0x0284c7 },
      { x: 9, z: -33, w: 11, h: 9.5, d: 8, body: 0xfce7f3, roof: 0xdb2777, awning: 0x10b981 },
      { x: 22, z: -34, w: 9, h: 15, d: 9, body: 0xe2e8f0, roof: 0x475569 },
      // Left side across road (visible through left panoramic windows!)
      { x: -37, z: -15, w: 9, h: 11, d: 9, body: 0xdcfce7, roof: 0x15803d },
      { x: -37, z: -2, w: 8.5, h: 8.5, d: 10, body: 0xffedd5, roof: 0xea580c, awning: 0x3b82f6 },
      { x: -37, z: 12, w: 9.5, h: 12.5, d: 9, body: 0xede9fe, roof: 0x6d28d9 },
      // Right & front-distant skyline
      { x: 37, z: -14, w: 9, h: 12, d: 9, body: 0xf1f5f9, roof: 0x334155 },
      { x: 37, z: 2, w: 8.5, h: 9, d: 10, body: 0xfef3c7, roof: 0xb45309, awning: 0xec4899 },
      { x: 37, z: 16, w: 9, h: 11, d: 9, body: 0xdbeafe, roof: 0x1d4ed8 },
      { x: -14, z: 34, w: 10, h: 9, d: 8, body: 0xfce7f3, roof: 0xbe185d },
      { x: 4, z: 35, w: 11, h: 10.5, d: 8, body: 0xe0e7ff, roof: 0x4338ca },
    ];
    for (const b of buildings) {
      this._addTownBuilding(world, b);
    }

    // 4 Animated Voxel Mini-Cars cruising smoothly on the neighborhood roads (clear of Shuttle Drop-Off!)
    this._addVoxelCar(world, { color: 0xf43f5e, axis: "x", lane: 20.5, dir: 1, pos: -26, speed: 5.2 });
    this._addVoxelCar(world, { color: 0x38bdf8, axis: "x", lane: 23.6, dir: -1, pos: 20, speed: 4.5 });
    this._addVoxelCar(world, { color: 0xfbbf24, axis: "x", lane: -19.8, dir: -1, pos: 12, speed: 4.8 });
    this._addVoxelCar(world, { color: 0x34d399, axis: "z", lane: -23.8, dir: 1, pos: -18, speed: 4.2 });

    // High drifting voxel clouds
    for (let i = 0; i < 6; i++) {
      const cloud = new THREE.Group();
      const c1 = makeBox(4.2, 1.1, 2.2, 0xffffff, { castShadow: false, roughness: 0.95 });
      const c2 = makeBox(2.6, 0.95, 1.8, 0xffffff, { castShadow: false, roughness: 0.95 });
      c2.position.set(0.6, 0.8, 0);
      cloud.add(c1, c2);
      cloud.position.set(-48 + i * 19, 18 + (i % 3) * 2.4, -36 + (i % 2) * 28);
      cloud.userData.speed = 0.55 + (i % 3) * 0.18;
      world.add(cloud);
      this.clouds.push(cloud);
    }

    this.scene.add(world);
  }

  _buildInstancedTrees(parent) {
    const treeSpots = [
      // Courtyard perimeter trees (visible through office windows!)
      [-18.2, -13.5, "sakura"], [-12.5, -14.2, "oak"], [-4.0, -14.6, "oak"],
      [5.5, -14.4, "sakura"], [15.5, -13.8, "oak"], [18.5, -6.5, "sakura"],
      [18.5, 4.5, "oak"], [17.8, 13.5, "oak"], [-18.2, -1.5, "sakura"],
      [-18.2, 12.8, "oak"], [-14.0, 15.2, "sakura"], [11.5, 15.0, "oak"],
      // Outer neighborhood park trees
      [-28, -28, "oak"], [-10, -27, "sakura"], [14, -27, "oak"], [30, -24, "sakura"],
      [-31, 4, "oak"], [-31, 20, "sakura"], [31, -4, "oak"], [31, 24, "sakura"],
      [-24, 29, "oak"], [18, 29, "sakura"],
    ];

    const trunks = [];
    const oakLeaves = [];
    const sakuraLeaves = [];

    for (const [tx, tz, kind] of treeSpots) {
      const h = kind === "sakura" ? 2.4 : 2.8;
      trunks.push({ x: tx, y: h / 2 - 0.15, z: tz, sx: 0.55, sy: h, sz: 0.55 });
      const targetList = kind === "sakura" ? sakuraLeaves : oakLeaves;
      targetList.push({ x: tx, y: h + 0.7, z: tz, sx: 2.5, sy: 1.4, sz: 2.5 });
      targetList.push({ x: tx + 0.2, y: h + 1.65, z: tz - 0.15, sx: 1.75, sy: 1.0, sz: 1.75 });
      targetList.push({ x: tx - 0.3, y: h + 0.35, z: tz + 0.35, sx: 1.2, sy: 0.85, sz: 1.2 });
    }

    const addInst = (items, color) => {
      const inst = new THREE.InstancedMesh(UNIT_BOX, getStandardMat(color, { roughness: 0.88 }), items.length);
      inst.castShadow = true;
      inst.receiveShadow = true;
      const d = new THREE.Object3D();
      items.forEach((it, i) => {
        d.position.set(it.x, it.y, it.z);
        d.scale.set(it.sx, it.sy, it.sz);
        d.updateMatrix();
        inst.setMatrixAt(i, d.matrix);
      });
      parent.add(inst);
    };

    addInst(trunks, 0x78350f);
    addInst(oakLeaves, 0x22c55e);
    addInst(sakuraLeaves, 0xf9a8d4);
  }

  _addTownBuilding(parent, b) {
    const g = new THREE.Group();
    g.position.set(b.x, -0.32, b.z);

    const body = makeBox(b.w, b.h, b.d, b.body, { castShadow: false });
    body.position.y = b.h / 2;
    const roof = makeBox(b.w + 0.5, 0.65, b.d + 0.5, b.roof, { castShadow: false });
    roof.position.y = b.h + 0.32;
    g.add(body, roof);

    if (b.awning) {
      const awn = makeBox(b.w * 0.72, 0.35, 1.4, b.awning, { castShadow: false });
      awn.position.set(0, 2.8, b.d / 2 + 0.5);
      g.add(awn);
    }

    // Lit voxel windows on all visible faces
    const floors = Math.max(2, Math.floor(b.h / 3.1));
    const winMat = new THREE.MeshStandardMaterial({
      color: 0xfef3c7,
      emissive: 0xfde047,
      emissiveIntensity: 0.08,
      roughness: 0.3,
    });
    for (let fl = 0; fl < floors; fl++) {
      const wy = 2.1 + fl * 2.8;
      if (wy > b.h - 1.2) break;
      for (const wx of [-b.w * 0.25, 0, b.w * 0.25]) {
        const wf = new THREE.Mesh(UNIT_BOX, winMat);
        wf.scale.set(1.25, 1.35, 0.12);
        wf.position.set(wx, wy, b.d / 2 + 0.04);
        g.add(wf);
        const wb = new THREE.Mesh(UNIT_BOX, winMat);
        wb.scale.set(1.25, 1.35, 0.12);
        wb.position.set(wx, wy, -b.d / 2 - 0.04);
        g.add(wb);
      }
      for (const wz of [-b.d * 0.25, b.d * 0.25]) {
        const ws = new THREE.Mesh(UNIT_BOX, winMat);
        ws.scale.set(0.12, 1.35, 1.25);
        ws.position.set(b.w / 2 + 0.04, wy, wz);
        g.add(ws);
        const ws2 = new THREE.Mesh(UNIT_BOX, winMat);
        ws2.scale.set(0.12, 1.35, 1.25);
        ws2.position.set(-b.w / 2 - 0.04, wy, wz);
        g.add(ws2);
      }
    }
    this.nightWindowMeshes.push({ material: winMat });
    parent.add(g);
  }

  _addVoxelCar(parent, cfg) {
    const car = new THREE.Group();
    const chassis = makeBox(2.2, 0.6, 1.25, cfg.color); chassis.position.y = 0.45;
    const cabin = makeBox(1.25, 0.55, 1.12, 0xf8fafc); cabin.position.set(-0.1, 0.98, 0);
    const hl1 = makeBox(0.1, 0.18, 0.22, 0xfef08a, { emissive: 0xfde047, emissiveIntensity: 0.9, castShadow: false });
    hl1.position.set(1.12, 0.48, -0.38);
    const hl2 = hl1.clone(); hl2.position.z = 0.38;
    car.add(chassis, cabin, hl1, hl2);

    for (const [wx, wz] of [[-0.65, -0.62], [0.65, -0.62], [-0.65, 0.62], [0.65, 0.62]]) {
      const wheel = makeBox(0.42, 0.42, 0.18, 0x18181b);
      wheel.position.set(wx, 0.22, wz);
      car.add(wheel);
    }

    if (cfg.axis === "x") {
      car.position.set(cfg.pos, -0.22, cfg.lane);
      car.rotation.y = cfg.dir > 0 ? 0 : Math.PI;
    } else {
      car.position.set(cfg.lane, -0.22, cfg.pos);
      car.rotation.y = cfg.dir > 0 ? -Math.PI / 2 : Math.PI / 2;
    }
    car.userData = cfg;
    parent.add(car);
    this.cars.push(car);
  }

  // =====================================================
  // 2. ENCLOSED HIGH-CEILING ARCHITECTURAL STUDIO (30 x 22 x 8.8)
  // Full 4 solid walls + skylight roof + sliding glass front doors + smart auto-cutaway
  // =====================================================
  _buildSpaciousStudio() {
    const studio = new THREE.Group();
    this.frontWallGroup = new THREE.Group();
    this.rightWallGroup = new THREE.Group();
    this.roofGroup = new THREE.Group();
    this.cutawayBorderGroup = new THREE.Group();
    this.entranceGroup = new THREE.Group();

    // Raised concrete studio slab (30.8 x 22.8)
    const slab = makeBox(30.8, 0.34, 22.8, 0x475569, { castShadow: false });
    slab.position.set(0, -0.17, 0);
    studio.add(slab);

    // Warm procedural wood plank floor (1 draw call!)
    const woodTex = makeWoodFloorTexture();
    woodTex.anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(30, 22),
      new THREE.MeshStandardMaterial({ map: woodTex, roughness: 0.74, metalness: 0.04 })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = 0.01;
    floor.receiveShadow = true;
    studio.add(floor);

    const glassMat = new THREE.MeshPhysicalMaterial({
      color: 0xbfdbfe,
      roughness: 0.12,
      metalness: 0.08,
      transparent: true,
      opacity: 0.32,
    });

    const addWallTo = (parent, w, h, d, x, y, z, col = 0xf5f3ef) => {
      const seg = makeBox(w, h, d, col, { castShadow: false });
      seg.position.set(x, y, z);
      parent.add(seg);
    };

    const addFramedWindowTo = (parent, w, h, x, y, z, rotY = 0, curtains = true) => {
      const wg = new THREE.Group();
      wg.position.set(x, y, z);
      wg.rotation.y = rotY;

      const pane = new THREE.Mesh(UNIT_BOX, glassMat);
      pane.scale.set(w - 0.24, h - 0.24, 0.08);
      wg.add(pane);

      const fTop = makeBox(w + 0.12, 0.18, 0.56, 0x27272a, { castShadow: false }); fTop.position.y = h / 2;
      const fBot = makeBox(w + 0.24, 0.2, 0.68, 0xffffff, { castShadow: false }); fBot.position.set(0, -h / 2, 0.06);
      const fL = makeBox(0.18, h, 0.56, 0x27272a, { castShadow: false }); fL.position.x = -w / 2;
      const fR = makeBox(0.18, h, 0.56, 0x27272a, { castShadow: false }); fR.position.x = w / 2;
      const mV = makeBox(0.1, h - 0.16, 0.24, 0x3f3f46, { castShadow: false });
      const mH = makeBox(w - 0.16, 0.08, 0.24, 0x3f3f46, { castShadow: false }); mH.position.y = 0.28;
      wg.add(fTop, fBot, fL, fR, mV, mH);

      if (curtains) {
        const curL = makeBox(0.42, h + 0.35, 0.14, 0xe2e8f0, { castShadow: false }); curL.position.set(-w / 2 + 0.15, -0.05, 0.32);
        const curR = makeBox(0.42, h + 0.35, 0.14, 0xe2e8f0, { castShadow: false }); curR.position.set(w / 2 - 0.15, -0.05, 0.32);
        wg.add(curL, curR);
      }
      parent.add(wg);
    };

    // --- BACK WALL (z = -11.15, HIGH CEILING height = 8.8!) ---
    addWallTo(studio, 30.6, 1.55, 0.5, 0, 0.775, -11.15);          // solid lower wall
    addWallTo(studio, 30.6, 4.25, 0.5, 0, 6.675, -11.15);          // tall upper architectural header wall
    addWallTo(studio, 3.3, 3.0, 0.5, -13.65, 3.05, -11.15);        // left pillar
    addWallTo(studio, 13.4, 3.0, 0.5, -0.5, 3.05, -11.15);         // center feature wall
    addWallTo(studio, 3.9, 3.0, 0.5, 13.35, 3.05, -11.15);         // right pillar
    addWallTo(studio, 30.8, 0.26, 0.64, 0, 8.93, -11.15, 0x27272a); // roof coping
    addWallTo(studio, 30.1, 0.24, 0.12, 0, 0.12, -10.86, 0xb88b5a); // baseboard
    addFramedWindowTo(studio, 4.8, 3.0, -9.6, 3.05, -11.15, 0);
    addFramedWindowTo(studio, 5.2, 3.0, 8.8, 3.05, -11.15, 0);

    // --- LEFT WALL (x = -15.15, HIGH CEILING height = 8.8!) ---
    addWallTo(studio, 0.5, 1.55, 22.8, -15.15, 0.775, 0, 0xf1efe9);
    addWallTo(studio, 0.5, 4.25, 22.8, -15.15, 6.675, 0, 0xf1efe9);
    addWallTo(studio, 0.5, 3.0, 4.8, -15.15, 3.05, -9.0, 0xf1efe9);
    addWallTo(studio, 0.5, 3.0, 3.7, -15.15, 3.05, 0.05, 0xf1efe9);
    addWallTo(studio, 0.5, 3.0, 4.5, -15.15, 3.05, 9.15, 0xf1efe9);
    addWallTo(studio, 0.64, 0.26, 22.8, -15.15, 8.93, 0, 0x27272a);
    addWallTo(studio, 0.12, 0.24, 22.0, -14.86, 0.12, 0, 0xb88b5a);
    addFramedWindowTo(studio, 4.8, 3.0, -15.15, 3.05, -4.2, Math.PI / 2);
    addFramedWindowTo(studio, 5.0, 3.0, -15.15, 3.05, 4.4, Math.PI / 2);

    // --- RIGHT WALL (x = +15.15, height = 8.8, auto-managed in rightWallGroup!) ---
    addWallTo(this.rightWallGroup, 0.5, 1.55, 22.8, 15.15, 0.775, 0, 0xf1efe9);
    addWallTo(this.rightWallGroup, 0.5, 4.25, 22.8, 15.15, 6.675, 0, 0xf1efe9);
    addWallTo(this.rightWallGroup, 0.5, 3.0, 4.8, 15.15, 3.05, -9.0, 0xf1efe9);
    addWallTo(this.rightWallGroup, 0.5, 3.0, 3.7, 15.15, 3.05, 0.05, 0xf1efe9);
    addWallTo(this.rightWallGroup, 0.5, 3.0, 4.5, 15.15, 3.05, 9.15, 0xf1efe9);
    addWallTo(this.rightWallGroup, 0.64, 0.26, 22.8, 15.15, 8.93, 0, 0x27272a);
    addFramedWindowTo(this.rightWallGroup, 4.8, 3.0, 15.15, 3.05, -4.2, -Math.PI / 2, false);
    addFramedWindowTo(this.rightWallGroup, 5.0, 3.0, 15.15, 3.05, 4.4, -Math.PI / 2, false);

    // --- FRONT WALL (z = +11.15, height = 8.8, glass storefront + grand doorway at x = 0!) ---
    // Door opening at x = -1.9 .. +1.9, y = 0 .. 3.75
    addWallTo(this.frontWallGroup, 13.4, 1.35, 0.5, -8.6, 0.675, 11.15);   // lower-left front wall
    addWallTo(this.frontWallGroup, 13.4, 1.35, 0.5, 8.6, 0.675, 11.15);    // lower-right front wall
    addWallTo(this.frontWallGroup, 30.6, 4.25, 0.5, 0, 6.675, 11.15);      // tall upper facade wall
    addWallTo(this.frontWallGroup, 3.8, 0.8, 0.5, 0, 4.15, 11.15);         // lintel above doorway
    addWallTo(this.frontWallGroup, 3.5, 3.2, 0.5, -13.55, 2.95, 11.15);    // far-left corner pillar
    addWallTo(this.frontWallGroup, 3.7, 3.2, 0.5, -3.75, 2.95, 11.15);     // left door pillar
    addWallTo(this.frontWallGroup, 3.7, 3.2, 0.5, 3.75, 2.95, 11.15);      // right door pillar
    addWallTo(this.frontWallGroup, 3.5, 3.2, 0.5, 13.55, 2.95, 11.15);     // far-right corner pillar
    addWallTo(this.frontWallGroup, 30.8, 0.26, 0.64, 0, 8.93, 11.15, 0x27272a);
    addFramedWindowTo(this.frontWallGroup, 6.2, 3.2, -8.7, 2.95, 11.15, Math.PI, false);
    addFramedWindowTo(this.frontWallGroup, 6.2, 3.2, 8.7, 2.95, 11.15, Math.PI, false);

    // Exterior Architectural ZENTIRA HQ Signboard on Front Facade (visible from Sekitar Gedung!)
    const { canvas: signCanvas, tex: signTex } = makeSignTexture();
    this.signCanvas = signCanvas;
    this.signTex = signTex;
    const extSignMats = [
      getStandardMat(0x111114), getStandardMat(0x111114),
      getStandardMat(0x111114), getStandardMat(0x111114),
      new THREE.MeshStandardMaterial({ map: signTex, roughness: 0.3 }),
      getStandardMat(0x111114),
    ];
    const extSignBoard = new THREE.Mesh(new THREE.BoxGeometry(8.6, 2.05, 0.24), extSignMats);
    extSignBoard.position.set(0, 6.75, 11.5);
    this.frontWallGroup.add(extSignBoard);

    // --- PERMANENT ENTRANCE PORTAL (Animated Sliding Double Glass Doors + Architectural Canopy) ---
    // Kept visible in ALL views so agents always walk cleanly through real sliding doors!
    const doorFrameL = makeBox(0.22, 3.75, 0.58, 0x18181b, { castShadow: false });
    doorFrameL.position.set(-1.95, 1.875, 11.15);
    const doorFrameR = makeBox(0.22, 3.75, 0.58, 0x18181b, { castShadow: false });
    doorFrameR.position.set(1.95, 1.875, 11.15);
    const doorHeader = makeBox(4.12, 0.24, 0.58, 0x18181b, { castShadow: false });
    doorHeader.position.set(0, 3.8, 11.15);
    const canopy = makeBox(5.6, 0.16, 2.3, 0x27272a, { castShadow: false });
    canopy.position.set(0, 3.92, 12.25);
    const canopyTrim = makeBox(5.66, 0.06, 0.12, 0xd4af37, { metalness: 0.6, roughness: 0.3, castShadow: false });
    canopyTrim.position.set(0, 3.92, 13.42);
    const welcomeMat = makeBox(3.4, 0.04, 1.4, 0x18181b, { castShadow: false });
    welcomeMat.position.set(0, 0.03, 11.4);

    // Sliding glass door leaves (slide outward along X when agents approach!)
    this.doorLeft = new THREE.Group();
    const dlPane = new THREE.Mesh(UNIT_BOX, glassMat);
    dlPane.scale.set(1.78, 3.55, 0.1);
    const dlFrame = makeBox(1.84, 3.62, 0.14, 0x27272a, { opacity: 0.5, castShadow: false });
    const dlHandle = makeBox(0.08, 0.72, 0.18, 0xd4af37, { metalness: 0.65, roughness: 0.25, castShadow: false });
    dlHandle.position.set(0.74, -0.1, 0);
    this.doorLeft.add(dlPane, dlFrame, dlHandle);
    this.doorLeft.position.set(-0.92, 1.82, 11.15);

    this.doorRight = new THREE.Group();
    const drPane = new THREE.Mesh(UNIT_BOX, glassMat);
    drPane.scale.set(1.78, 3.55, 0.1);
    const drFrame = makeBox(1.84, 3.62, 0.14, 0x27272a, { opacity: 0.5, castShadow: false });
    const drHandle = makeBox(0.08, 0.72, 0.18, 0xd4af37, { metalness: 0.65, roughness: 0.25, castShadow: false });
    drHandle.position.set(-0.74, -0.1, 0);
    this.doorRight.add(drPane, drFrame, drHandle);
    this.doorRight.position.set(0.92, 1.82, 11.15);

    this.entranceGroup.add(
      doorFrameL, doorFrameR, doorHeader, canopy, canopyTrim, welcomeMat,
      this.doorLeft, this.doorRight
    );

    // --- FULL HIGH-CEILING ROOF + GLASS SKYLIGHT ATRIUM + CEILING-MOUNTED LAMPS ---
    // Built with 4 perimeter roof slabs leaving a bright 10 x 6 central skylight atrium!
    addWallTo(this.roofGroup, 30.8, 0.34, 8.2, 0, 9.0, -7.2, 0xe7e5e4);  // back roof section
    addWallTo(this.roofGroup, 30.8, 0.34, 8.2, 0, 9.0, 7.2, 0xe7e5e4);   // front roof section
    addWallTo(this.roofGroup, 10.4, 0.34, 6.2, -10.2, 9.0, 0, 0xe7e5e4); // left roof section
    addWallTo(this.roofGroup, 10.4, 0.34, 6.2, 10.2, 9.0, 0, 0xe7e5e4);  // right roof section

    // Skylight glass panel + dark steel frame in center of roof
    const skyGlass = new THREE.Mesh(UNIT_BOX, glassMat);
    skyGlass.scale.set(10.0, 0.12, 6.2);
    skyGlass.position.set(0, 9.1, 0);
    const skyFrameF = makeBox(10.4, 0.36, 0.24, 0x27272a, { castShadow: false }); skyFrameF.position.set(0, 9.18, 3.15);
    const skyFrameB = makeBox(10.4, 0.36, 0.24, 0x27272a, { castShadow: false }); skyFrameB.position.set(0, 9.18, -3.15);
    const skyFrameL = makeBox(0.24, 0.36, 6.4, 0x27272a, { castShadow: false }); skyFrameL.position.set(-5.1, 9.18, 0);
    const skyFrameR = makeBox(0.24, 0.36, 6.4, 0x27272a, { castShadow: false }); skyFrameR.position.set(5.1, 9.18, 0);
    const skyMullion = makeBox(0.16, 0.28, 6.2, 0x3f3f46, { castShadow: false }); skyMullion.position.set(0, 9.16, 0);
    this.roofGroup.add(skyGlass, skyFrameF, skyFrameB, skyFrameL, skyFrameR, skyMullion);

    // Subtle exterior rooftop architectural solar panels + parapet railing
    for (const sx of [-11.5, -8.5, 8.5, 11.5]) {
      const solar = makeBox(2.2, 0.12, 3.4, 0x1e3a8a, { metalness: 0.35, roughness: 0.25, castShadow: false });
      solar.position.set(sx, 9.3, -6.8);
      solar.rotation.x = 0.16;
      this.roofGroup.add(solar);
    }

    // Interior ceiling acoustic wood beams + attached linear light bars (ONLY shown with roof — zero floating!)
    for (const bx of [-10.0, 0.0, 10.0]) {
      const rod1 = makeBox(0.08, 0.9, 0.08, 0x27272a, { castShadow: false }); rod1.position.set(bx, 8.4, -7.0);
      const rod2 = makeBox(0.08, 0.9, 0.08, 0x27272a, { castShadow: false }); rod2.position.set(bx, 8.4, -4.6);
      const bar = makeBox(0.26, 0.16, 3.0, 0x18181b, { castShadow: false }); bar.position.set(bx, 7.95, -5.8);
      const emit = makeBox(0.18, 0.06, 2.8, 0xfef3c7, { emissive: 0xfde68a, emissiveIntensity: 0.85, castShadow: false });
      emit.position.set(bx, 7.86, -5.8);
      this.roofGroup.add(rod1, rod2, bar, emit);
    }

    // Cutaway low architectural border (shown only in Isometric cutaway view when walls hide)
    addWallTo(this.cutawayBorderGroup, 13.0, 0.2, 0.22, -8.6, 0.1, 11.05, 0x3f3f46);
    addWallTo(this.cutawayBorderGroup, 13.0, 0.2, 0.22, 8.6, 0.1, 11.05, 0x3f3f46);
    addWallTo(this.cutawayBorderGroup, 0.22, 0.2, 22.2, 15.05, 0.1, 0, 0x3f3f46);

    // Feature ZENTIRA Signboard mounted cleanly on center solid wall (zero obstruction!)
    const signMats = [
      getStandardMat(0x111114), getStandardMat(0x111114),
      getStandardMat(0x111114), getStandardMat(0x111114),
      new THREE.MeshStandardMaterial({ map: signTex, roughness: 0.32 }),
      getStandardMat(0x111114),
    ];
    const signBoard = new THREE.Mesh(new THREE.BoxGeometry(6.8, 1.65, 0.18), signMats);
    signBoard.position.set(-1.0, 4.25, -10.8);
    studio.add(signBoard);

    this.neonStrip = makeBox(6.9, 0.08, 0.12, 0xfafafa, {
      emissive: 0xec4899,
      emissiveIntensity: 0.45,
      unique: true,
      castShadow: false,
    });
    this.neonStrip.position.set(-1.0, 3.34, -10.78);
    studio.add(this.neonStrip);

    // Warm oak acoustic wall slats behind center studio wall
    for (let sx = -5.6; sx <= 3.6; sx += 0.54) {
      const slat = makeBox(0.14, 3.0, 0.08, 0xc29360, { castShadow: false });
      slat.position.set(sx, 1.7, -10.85);
      studio.add(slat);
    }

    // Architectural Founder Plaque mounted cleanly on the oak slat feature wall below ZENTIRA
    const founderTex = makeFounderPlaqueTexture();
    founderTex.anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
    const founderBacking = makeBox(5.48, 0.78, 0.07, 0xd4af37, {
      metalness: 0.62,
      roughness: 0.28,
      castShadow: false,
    });
    founderBacking.position.set(-1.0, 2.48, -10.78);
    const founderMats = [
      getStandardMat(0x111114), getStandardMat(0x111114),
      getStandardMat(0x111114), getStandardMat(0x111114),
      new THREE.MeshStandardMaterial({ map: founderTex, roughness: 0.28, metalness: 0.12 }),
      getStandardMat(0x111114),
    ];
    const founderPlaque = new THREE.Mesh(new THREE.BoxGeometry(5.36, 0.68, 0.09), founderMats);
    founderPlaque.position.set(-1.0, 2.48, -10.74);
    studio.add(founderBacking, founderPlaque);

    // Creator Instagram Wall Sign (@quietdenn) mounted cleanly on Left Solid Column above Espresso Bar
    const igTex = makeInstagramPlaqueTexture();
    igTex.anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
    const igSignGroup = new THREE.Group();
    igSignGroup.position.set(-14.82, 3.22, 0.05);
    igSignGroup.rotation.y = Math.PI / 2;
    const igMats = [
      getStandardMat(0x111114), getStandardMat(0x111114),
      getStandardMat(0x111114), getStandardMat(0x111114),
      new THREE.MeshStandardMaterial({ map: igTex, roughness: 0.28, metalness: 0.08 }),
      getStandardMat(0x111114),
    ];
    const igBoard = new THREE.Mesh(new THREE.BoxGeometry(2.86, 0.94, 0.12), igMats);
    const igGlowBar = makeBox(2.88, 0.05, 0.08, 0xfafafa, {
      emissive: 0xd62976,
      emissiveIntensity: 0.65,
      castShadow: false,
    });
    igGlowBar.position.set(0, -0.52, 0.02);
    igSignGroup.add(igBoard, igGlowBar);
    studio.add(igSignGroup);

    // 2 Grounded Wall Sconces mounted directly onto the solid back wall flanking ZENTIRA sign
    for (const wx of [-5.5, 3.5]) {
      const mount = makeBox(0.26, 0.34, 0.14, 0x18181b, { castShadow: false });
      mount.position.set(wx, 4.05, -10.84);
      const glow = makeBox(0.2, 0.46, 0.2, 0xfef3c7, {
        emissive: 0xfde68a,
        emissiveIntensity: 0.85,
        castShadow: false,
      });
      glow.position.set(wx, 4.07, -10.7);
      studio.add(mount, glow);
    }

    // Mounted Whiteboard with sticky notes on right solid pillar
    const wbFrame = makeBox(2.6, 1.75, 0.08, 0x27272a, { castShadow: false });
    wbFrame.position.set(13.2, 3.1, -10.86);
    const wb = makeBox(2.44, 1.6, 0.08, 0xffffff, { roughness: 0.3, castShadow: false });
    wb.position.set(13.2, 3.1, -10.83);
    studio.add(wbFrame, wb);
    const noteCols = [0xfef08a, 0xfbcfe8, 0xbae6fd, 0xa7f3d0, 0xfde68a, 0xddd6fe];
    noteCols.forEach((col, i) => {
      const note = makeBox(0.32, 0.32, 0.04, col, { castShadow: false });
      note.position.set(12.45 + (i % 3) * 0.72, 3.4 - Math.floor(i / 3) * 0.62, -10.77);
      studio.add(note);
    });

    // 2 Grounded Standing Floor Lamps (zero floating lamps!)
    for (const [fx, fz] of [[-13.6, 8.8], [13.6, 8.8]]) {
      const fl = new THREE.Group();
      fl.position.set(fx, 0, fz);
      const base = makeBox(0.75, 0.12, 0.75, 0x27272a); base.position.y = 0.06;
      const pole = makeBox(0.12, 3.1, 0.12, 0x3f3f46); pole.position.y = 1.6;
      const shade = makeBox(0.76, 0.65, 0.76, 0xfef3c7, {
        emissive: 0xfde68a,
        emissiveIntensity: 0.55,
      });
      shade.position.y = 3.25;
      fl.add(base, pole, shade);
      studio.add(fl);
    }

    studio.add(
      this.frontWallGroup,
      this.rightWallGroup,
      this.roofGroup,
      this.cutawayBorderGroup,
      this.entranceGroup
    );
    this.scene.add(studio);
  }

  // =====================================================
  // 3. INTERIOR ZONES (Boss Corner, Filming Set, Meeting, Coffee Lounge)
  // =====================================================
  _buildInteriorZones() {
    const props = new THREE.Group();

    // --- Zone A: Private Glass Executive Manager Office (Back-Left: x -14.8..-6.2, z -10.8..-4.6) ---
    const mgrRoom = new THREE.Group();
    const mgrRug = makeBox(7.8, 0.04, 5.4, 0x334155, { castShadow: false, roughness: 0.92 });
    mgrRug.position.set(-10.5, 0.025, -7.7);
    mgrRoom.add(mgrRug);

    const partGlassMat = new THREE.MeshPhysicalMaterial({
      color: 0xe2e8f0,
      roughness: 0.08,
      metalness: 0.06,
      transparent: true,
      opacity: 0.24,
    });
    // Right glass partition wall at x = -6.2 (z = -10.8 .. -4.6, height = 4.2)
    const rgPane = new THREE.Mesh(UNIT_BOX, partGlassMat);
    rgPane.scale.set(0.08, 3.9, 6.0);
    rgPane.position.set(-6.2, 2.05, -7.7);
    const rgTop = makeBox(0.18, 0.18, 6.26, 0x18181b, { castShadow: false }); rgTop.position.set(-6.2, 4.1, -7.7);
    const rgBot = makeBox(0.18, 0.22, 6.26, 0x18181b, { castShadow: false }); rgBot.position.set(-6.2, 0.11, -7.7);
    const rgPost1 = makeBox(0.18, 4.15, 0.18, 0x18181b, { castShadow: false }); rgPost1.position.set(-6.2, 2.08, -4.6);
    const rgPost2 = makeBox(0.12, 4.15, 0.12, 0x27272a, { castShadow: false }); rgPost2.position.set(-6.2, 2.08, -7.7);
    mgrRoom.add(rgPane, rgTop, rgBot, rgPost1, rgPost2);

    // Front glass partition wall at z = -4.6 with open executive doorway at x = -8.4..-6.6!
    const fgPane = new THREE.Mesh(UNIT_BOX, partGlassMat);
    fgPane.scale.set(6.1, 3.9, 0.08);
    fgPane.position.set(-11.6, 2.05, -4.6);
    const fgTop = makeBox(8.7, 0.18, 0.18, 0x18181b, { castShadow: false }); fgTop.position.set(-10.5, 4.1, -4.6);
    const fgBot = makeBox(6.3, 0.22, 0.18, 0x18181b, { castShadow: false }); fgBot.position.set(-11.65, 0.11, -4.6);
    const fgDoorPost = makeBox(0.18, 4.15, 0.18, 0x18181b, { castShadow: false }); fgDoorPost.position.set(-8.5, 2.08, -4.6);
    const fgMidPost = makeBox(0.12, 4.15, 0.12, 0x27272a, { castShadow: false }); fgMidPost.position.set(-11.65, 2.08, -4.6);
    const doorTransom = new THREE.Mesh(UNIT_BOX, partGlassMat);
    doorTransom.scale.set(2.2, 0.85, 0.08);
    doorTransom.position.set(-7.35, 3.6, -4.6);
    const doorLintel = makeBox(2.3, 0.14, 0.2, 0x18181b, { castShadow: false });
    doorLintel.position.set(-7.35, 3.15, -4.6);
    mgrRoom.add(fgPane, fgTop, fgBot, fgDoorPost, fgMidPost, doorTransom, doorLintel);

    // Obsidian & Gold Room Header Plaque above Manager's Glass Office Doorway
    const mgrPlaqueTex = makeRoomPlaqueTexture("EXECUTIVE OFFICE", "RUANG MANAJER");
    const mgrPlaqueMats = [
      getStandardMat(0x111114), getStandardMat(0x111114),
      getStandardMat(0x111114), getStandardMat(0x111114),
      new THREE.MeshStandardMaterial({ map: mgrPlaqueTex, roughness: 0.28, metalness: 0.15 }),
      getStandardMat(0x111114),
    ];
    const mgrPlaque = new THREE.Mesh(new THREE.BoxGeometry(2.15, 0.46, 0.1), mgrPlaqueMats);
    mgrPlaque.position.set(-7.35, 3.62, -4.48);
    mgrRoom.add(mgrPlaque);

    // Executive guest armchair inside Manager Office
    const guestChair = new THREE.Group();
    guestChair.position.set(-13.6, 0, -6.5);
    const gcSeat = makeBox(1.15, 0.46, 1.25, 0x18181b); gcSeat.position.y = 0.23;
    const gcBack = makeBox(0.28, 0.95, 1.25, 0x27272a); gcBack.position.set(-0.46, 0.65, 0);
    const gcCush = makeBox(0.85, 0.14, 1.0, 0xf43f5e); gcCush.position.set(0.1, 0.5, 0);
    guestChair.add(gcSeat, gcBack, gcCush);
    mgrRoom.add(guestChair);

    // Studio Bookshelf & Golden Trophy inside Manager's Back-Left Executive Corner
    const shelf = new THREE.Group();
    shelf.position.set(-13.3, 0, -10.15);
    const shBack = makeBox(2.8, 3.1, 0.12, 0x78350f); shBack.position.set(0, 1.55, -0.32);
    const shLeft = makeBox(0.14, 3.1, 0.74, 0x92400e); shLeft.position.set(-1.33, 1.55, 0);
    const shRight = makeBox(0.14, 3.1, 0.74, 0x92400e); shRight.position.set(1.33, 1.55, 0);
    shelf.add(shBack, shLeft, shRight);
    const bookColors = [0x38bdf8, 0xec4899, 0x34d399, 0xfbbf24, 0xa78bfa, 0xf97316];
    for (let row = 0; row < 4; row++) {
      const plank = makeBox(2.6, 0.1, 0.72, 0xb45309);
      plank.position.set(0, 0.35 + row * 0.9, 0);
      shelf.add(plank);
      if (row < 3) {
        for (let b = 0; b < 5; b++) {
          const bk = makeBox(0.28, 0.56, 0.48, bookColors[(row * 3 + b) % bookColors.length]);
          bk.position.set(-0.92 + b * 0.44, 0.68 + row * 0.9, 0.04);
          shelf.add(bk);
        }
      }
    }
    const trophy = makeBox(0.7, 0.48, 0.16, 0xfbbf24, { metalness: 0.55, roughness: 0.25 });
    trophy.position.set(0, 3.36, 0);
    shelf.add(trophy);
    mgrRoom.add(shelf);
    props.add(mgrRoom);

    // --- Zone B: Denn & Miki Mini Animation & Ring-Light Set (Left-Center, clear of Glass Office) ---
    const setGroup = new THREE.Group();
    setGroup.position.set(-13.0, 0, -2.7);
    const backdrop = makeBox(0.16, 2.9, 2.3, 0xfce7f3); backdrop.position.set(-1.2, 1.45, 0);
    const matFloor = makeBox(2.2, 0.05, 2.3, 0xfdf2f8, { castShadow: false }); matFloor.position.set(0, 0.03, 0);
    const stand = makeBox(0.1, 2.1, 0.1, 0x27272a); stand.position.set(0.85, 1.05, 0);
    const ringGlow = makeBox(0.12, 0.68, 0.68, 0xffffff, { emissive: 0xffffff, emissiveIntensity: 0.85 });
    ringGlow.position.set(0.85, 2.2, 0);
    setGroup.add(backdrop, matFloor, stand, ringGlow);
    props.add(setGroup);

    // --- Zone C: Upgraded 6-Seat Executive Meeting Table (for interactive Team Meetings!) ---
    const meet = new THREE.Group();
    meet.position.set(0.8, 0, -0.8);
    const mRug = makeBox(8.4, 0.04, 5.2, 0xe2e8f0, { castShadow: false }); mRug.position.y = 0.02;
    const mTop = makeBox(5.4, 0.14, 2.3, 0xf8fafc, { roughness: 0.3 }); mTop.position.y = 0.92;
    const mLeg1 = makeBox(0.24, 0.88, 1.4, 0x27272a); mLeg1.position.set(-1.75, 0.44, 0);
    const mLeg2 = makeBox(0.24, 0.88, 1.4, 0x27272a); mLeg2.position.set(1.75, 0.44, 0);
    const laptop = makeBox(0.65, 0.06, 0.48, 0x334155); laptop.position.set(-1.55, 1.02, 0);
    const laptopScr = makeBox(0.62, 0.42, 0.05, 0x38bdf8, { emissive: 0x38bdf8, emissiveIntensity: 0.4 });
    laptopScr.position.set(-1.25, 1.24, 0);
    laptopScr.rotation.y = Math.PI / 2;

    // Executive Founder Desk Nameplate on the central studio table
    const deskPlateTex = makeFounderDeskPlateTexture();
    const plateBase = makeBox(1.52, 0.07, 0.24, 0xd4af37, { metalness: 0.6, roughness: 0.3 });
    plateBase.position.set(0.6, 1.025, 0.05);
    const plateMats = [
      getStandardMat(0x111114), getStandardMat(0x111114),
      getStandardMat(0x111114), getStandardMat(0x111114),
      new THREE.MeshStandardMaterial({ map: deskPlateTex, roughness: 0.3, metalness: 0.12 }),
      getStandardMat(0x111114),
    ];
    const plateFace = new THREE.Mesh(new THREE.BoxGeometry(1.46, 0.32, 0.06), plateMats);
    plateFace.position.set(0.6, 1.18, 0.05);
    plateFace.rotation.x = -0.22;
    meet.add(mRug, mTop, mLeg1, mLeg2, laptop, laptopScr, plateBase, plateFace);

    // 6 Meeting Chairs positioned cleanly to match MEETING_SEATS (Denn at head of table + 5 specialists)
    const meetChairSpecs = [
      { x: -3.2, z: 0.0, rot: -Math.PI / 2, accent: 0xf43f5e },
      { x: -1.15, z: -1.65, rot: Math.PI, accent: 0x38bdf8 },
      { x: 1.15, z: -1.65, rot: Math.PI, accent: 0xf472b6 },
      { x: -1.15, z: 1.65, rot: 0, accent: 0x34d399 },
      { x: 1.15, z: 1.65, rot: 0, accent: 0xfbbf24 },
      { x: 3.2, z: 0.0, rot: Math.PI / 2, accent: 0xa78bfa },
    ];
    for (const cs of meetChairSpecs) {
      const mCh = new THREE.Group();
      mCh.position.set(cs.x, 0, cs.z);
      mCh.rotation.y = cs.rot;
      const mcBase = makeBox(0.62, 0.08, 0.62, 0x3f3f46); mcBase.position.y = 0.05;
      const mcStem = makeBox(0.12, 0.44, 0.12, 0x3f3f46); mcStem.position.y = 0.25;
      const mcSeat = makeBox(0.72, 0.12, 0.68, 0x475569); mcSeat.position.y = 0.5;
      const mcBack = makeBox(0.68, 0.62, 0.1, 0x1e293b); mcBack.position.set(0, 0.84, 0.3);
      const mcPip = makeBox(0.68, 0.08, 0.11, cs.accent); mcPip.position.set(0, 1.15, 0.3);
      mCh.add(mcBase, mcStem, mcSeat, mcBack, mcPip);
      meet.add(mCh);
    }
    props.add(meet);

    // --- Zone D: Wooden Slat Partition separating Lounge & Central Entrance Walkway ---
    for (let pz = 2.4; pz <= 8.2; pz += 0.68) {
      const post = makeBox(0.14, 2.4, 0.14, 0xb45309);
      post.position.set(-3.0, 1.2, pz);
      props.add(post);
    }
    const planterBox = makeBox(0.75, 0.55, 6.2, 0xf8fafc);
    planterBox.position.set(-3.0, 0.28, 5.3);
    props.add(planterBox);

    // --- Zone E: Spacious Cozy Coffee Bar & Lounge (Front-Left) ---
    const lounge = new THREE.Group();
    const lRug = makeBox(8.6, 0.05, 7.6, 0xfef3c7, { castShadow: false });
    lRug.position.set(-8.6, 0.025, 5.2);
    lounge.add(lRug);

    // L-shaped Teal Voxel Sofa
    const sofa = new THREE.Group();
    sofa.position.set(-12.2, 0, 5.0);
    const sBase = makeBox(1.4, 0.55, 4.8, 0x0f766e); sBase.position.y = 0.28;
    const sBack = makeBox(0.35, 1.1, 4.8, 0x115e59); sBack.position.set(-0.52, 0.78, 0);
    const sCush1 = makeBox(1.0, 0.2, 2.1, 0x2dd4bf); sCush1.position.set(0.12, 0.62, -1.12);
    const sCush2 = makeBox(1.0, 0.2, 2.1, 0x2dd4bf); sCush2.position.set(0.12, 0.62, 1.12);
    const sExt = makeBox(2.4, 0.55, 1.4, 0x0f766e); sExt.position.set(1.8, 0.28, 1.7);
    const sExtBack = makeBox(2.4, 1.1, 0.35, 0x115e59); sExtBack.position.set(1.8, 0.78, 2.25);
    sofa.add(sBase, sBack, sCush1, sCush2, sExt, sExtBack);
    lounge.add(sofa);

    // Coffee table + steaming mugs
    const cTable = new THREE.Group();
    cTable.position.set(-9.4, 0, 4.4);
    const ctTop = makeBox(1.8, 0.14, 2.6, 0x92400e); ctTop.position.y = 0.56;
    const mug1 = makeBox(0.22, 0.24, 0.22, 0xffffff); mug1.position.set(-0.25, 0.74, -0.45);
    const mug2 = makeBox(0.22, 0.24, 0.22, 0xfbbf24); mug2.position.set(0.28, 0.74, 0.4);
    cTable.add(ctTop, mug1, mug2);
    for (const [lx, lz] of [[-0.75, -1.1], [0.75, -1.1], [-0.75, 1.1], [0.75, 1.1]]) {
      const leg = makeBox(0.12, 0.52, 0.12, 0x78350f); leg.position.set(lx, 0.26, lz);
      cTable.add(leg);
    }
    lounge.add(cTable);

    // Espresso Bar Counter
    const bar = new THREE.Group();
    bar.position.set(-13.4, 0, 0.2);
    const bBody = makeBox(1.5, 1.15, 3.2, 0x78350f); bBody.position.y = 0.58;
    const bTop = makeBox(1.65, 0.14, 3.35, 0xfafafa); bTop.position.y = 1.2;
    const machine = makeBox(0.75, 0.8, 0.85, 0x18181b); machine.position.set(-0.1, 1.66, -0.65);
    const mLed = makeBox(0.14, 0.14, 0.14, 0x22c55e, { emissive: 0x22c55e, emissiveIntensity: 1.0 });
    mLed.position.set(0.3, 1.82, -0.65);
    const pastry = makeBox(0.65, 0.55, 0.9, 0xe0f2fe, { opacity: 0.45 }); pastry.position.set(0, 1.54, 0.75);
    bar.add(bBody, bTop, machine, mLed, pastry);
    lounge.add(bar);

    // Coffee steam particles
    for (let i = 0; i < 3; i++) {
      const bit = makeBox(0.1, 0.1, 0.1, 0xffffff, { castShadow: false });
      bit.position.set(-9.65, 0.95 + i * 0.26, 3.95);
      bit.userData = { baseY: 0.92, phase: i * 2.1 };
      lounge.add(bit);
      this.steamBits.push(bit);
    }

    // Indoor potted plants positioned cleanly without colliding with Glass Office or floor lamps
    for (const [px, pz] of [[-5.4, -10.1], [13.9, -9.6], [13.9, 1.2], [-4.5, 9.6]]) {
      const p = new THREE.Group();
      p.position.set(px, 0, pz);
      const pot = makeBox(0.85, 0.78, 0.85, 0xc2410c); pot.position.y = 0.39;
      const l1 = makeBox(1.1, 0.55, 1.1, 0x16a34a); l1.position.y = 1.35;
      const l2 = makeBox(0.78, 0.55, 0.78, 0x4ade80); l2.position.set(0.12, 1.85, -0.08);
      const stem = makeBox(0.18, 0.6, 0.18, 0x15803d); stem.position.y = 0.95;
      p.add(pot, stem, l1, l2);
      props.add(p);
    }

    props.add(lounge);
    this.scene.add(props);
  }

  // =====================================================
  // 3B. ZENTIRA STUDIO SHUTTLE VAN (for Masuk / Libur)
  // =====================================================
  _buildShuttleVan() {
    const van = new THREE.Group();
    const lowerBody = makeBox(5.6, 1.05, 2.35, 0x18181b); lowerBody.position.y = 0.88;
    const upperBody = makeBox(5.2, 1.02, 2.26, 0xf8fafc); upperBody.position.set(-0.1, 1.88, 0);
    const nose = makeBox(0.65, 0.92, 2.24, 0x27272a); nose.position.set(2.55, 1.25, 0);
    const roofCap = makeBox(4.8, 0.16, 2.15, 0x27272a); roofCap.position.set(-0.15, 2.45, 0);
    const stripe = makeBox(5.64, 0.14, 2.38, 0xec4899, { castShadow: false }); stripe.position.y = 1.38;

    // Front windshield + side windows
    const wind = makeBox(0.12, 0.78, 1.98, 0x0f172a, { roughness: 0.15, metalness: 0.35, castShadow: false });
    wind.position.set(2.52, 1.88, 0);
    const winSideL = makeBox(3.8, 0.66, 0.08, 0x1e293b, { roughness: 0.2, castShadow: false });
    winSideL.position.set(-0.4, 1.9, 1.15);
    const winSideR = winSideL.clone(); winSideR.position.z = -1.15;

    // Branded ZENTIRA SHUTTLE side panels
    const vanLogoTex = makeShuttleLogoTexture();
    const logoMat = new THREE.MeshStandardMaterial({ map: vanLogoTex, roughness: 0.32 });
    const sideDecalR = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.78), logoMat);
    sideDecalR.position.set(-0.45, 0.88, 1.19);
    const sideDecalL = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.78), logoMat);
    sideDecalL.position.set(-0.45, 0.88, -1.19);
    sideDecalL.rotation.y = Math.PI;

    // Animated sliding side door facing the studio (-Z side!)
    this.shuttleDoor = makeBox(1.55, 1.65, 0.12, 0xe4e4e7);
    this.shuttleDoor.position.set(0.6, 1.32, -1.18);

    // Headlights & taillights
    const hl1 = makeBox(0.12, 0.28, 0.42, 0xfef08a, { emissive: 0xfde047, emissiveIntensity: 1.4, castShadow: false });
    hl1.position.set(2.85, 0.88, -0.72);
    const hl2 = hl1.clone(); hl2.position.z = 0.72;
    const tl1 = makeBox(0.12, 0.32, 0.36, 0xef4444, { emissive: 0xef4444, emissiveIntensity: 1.1, castShadow: false });
    tl1.position.set(-2.82, 0.96, -0.76);
    const tl2 = tl1.clone(); tl2.position.z = 0.76;

    van.add(
      lowerBody, upperBody, nose, roofCap, stripe,
      wind, winSideL, winSideR, sideDecalR, sideDecalL,
      this.shuttleDoor, hl1, hl2, tl1, tl2
    );

    // 4 Voxel Wheels
    for (const [wx, wz] of [[-1.65, -1.18], [1.65, -1.18], [-1.65, 1.18], [1.65, 1.18]]) {
      const tire = makeBox(0.76, 0.76, 0.28, 0x09090b);
      tire.position.set(wx, 0.38, wz);
      const hub = makeBox(0.36, 0.36, 0.32, 0x94a3b8, { castShadow: false });
      hub.position.set(wx, 0.38, wz);
      van.add(tire, hub);
    }

    van.position.set(-48, -0.22, 17.5);
    van.visible = false;
    this.shuttleVan = van;
    this.scene.add(van);
  }

  // =====================================================
  // 4. FIVE WORKSTATIONS & ARTICULATED VOXEL AGENTS
  // =====================================================
  _buildDesk(agentId, cfg) {
    const group = new THREE.Group();
    group.position.set(cfg.desk[0], 0, cfg.desk[1]);

    // Spacious workstation desk (Executive walnut-obsidian for Manager, clean white for specialists)
    const isExec = cfg.prop === "executive";
    const top = makeBox(isExec ? 3.3 : 3.0, 0.16, 1.55, isExec ? 0x18181b : 0xfafafa); top.position.y = 0.92;
    const accentTrim = makeBox(isExec ? 3.34 : 3.04, 0.08, 0.12, cfg.color, {
      emissive: cfg.color,
      emissiveIntensity: isExec ? 0.45 : 0.25,
    });
    accentTrim.position.set(0, 0.92, 0.74);
    group.add(top, accentTrim);

    for (const [lx, lz] of [[-1.35, -0.65], [1.35, -0.65], [-1.35, 0.65], [1.35, 0.65]]) {
      const leg = makeBox(0.14, 0.88, 0.14, 0x3f3f46);
      leg.position.set(lx, 0.44, lz);
      group.add(leg);
    }

    // Wide studio monitor + screen
    const stand = makeBox(0.22, 0.3, 0.2, 0x27272a); stand.position.set(0, 1.12, -0.24);
    const frame = makeBox(1.55, 0.9, 0.1, 0x18181b); frame.position.set(0, 1.6, -0.26);
    const screen = makeBox(1.4, 0.76, 0.04, 0x0f172a, {
      emissive: cfg.color,
      emissiveIntensity: 0.2,
      unique: true,
      castShadow: false,
    });
    screen.position.set(0, 1.6, -0.19);
    const kb = makeBox(0.95, 0.05, 0.3, 0x27272a); kb.position.set(0, 1.02, 0.28);
    // Grounded mini desk lamp on left side of desk
    const dlBase = makeBox(0.24, 0.06, 0.24, 0x27272a); dlBase.position.set(-1.12, 1.03, -0.32);
    const dlStem = makeBox(0.06, 0.46, 0.06, 0x3f3f46); dlStem.position.set(-1.12, 1.28, -0.32);
    const dlHead = makeBox(0.26, 0.16, 0.26, 0xfef3c7, { emissive: 0xfde68a, emissiveIntensity: 0.5 });
    dlHead.position.set(-1.06, 1.52, -0.26);
    group.add(stand, frame, screen, kb, dlBase, dlStem, dlHead);

    // Desk prop
    if (cfg.prop === "globe") {
      const g = makeBox(0.36, 0.36, 0.36, 0x38bdf8); g.position.set(1.1, 1.24, -0.15);
      group.add(g);
    } else if (cfg.prop === "clapper") {
      const cl = makeBox(0.45, 0.36, 0.09, 0x18181b); cl.position.set(1.08, 1.18, -0.1);
      const st = makeBox(0.45, 0.09, 0.1, 0xfafafa); st.position.set(1.08, 1.34, -0.1);
      group.add(cl, st);
    } else if (cfg.prop === "pin") {
      const pin = makeBox(0.3, 0.42, 0.3, 0x34d399); pin.position.set(1.1, 1.21, -0.15);
      group.add(pin);
    } else if (cfg.prop === "coins") {
      for (let i = 0; i < 3; i++) {
        const coin = makeBox(0.32, 0.1, 0.32, 0xfbbf24); coin.position.set(1.1, 1.05 + i * 0.11, -0.15);
        group.add(coin);
      }
    } else if (cfg.prop === "heart") {
      const pod = makeBox(0.34, 0.34, 0.34, 0xa78bfa); pod.position.set(1.1, 1.17, -0.15);
      group.add(pod);
    } else if (cfg.prop === "executive") {
      // Second command monitor + gold executive desk plaque
      const sideFrame = makeBox(0.92, 0.66, 0.08, 0x18181b);
      sideFrame.position.set(1.15, 1.48, -0.1);
      sideFrame.rotation.y = -0.35;
      const sideScr = makeBox(0.82, 0.56, 0.04, 0x0f172a, {
        emissive: 0xf43f5e,
        emissiveIntensity: 0.35,
        castShadow: false,
      });
      sideScr.position.set(1.13, 1.48, -0.05);
      sideScr.rotation.y = -0.35;
      const plaque = makeBox(0.75, 0.16, 0.14, 0xfbbf24, { metalness: 0.5, roughness: 0.3 });
      plaque.position.set(0.85, 1.07, 0.48);
      group.add(sideFrame, sideScr, plaque);
    }

    // Ergonomic Chair
    const chair = new THREE.Group();
    chair.position.set(0, 0, 1.32);
    const cSeat = makeBox(0.8, 0.12, 0.76, cfg.color); cSeat.position.y = 0.56;
    const cBack = makeBox(0.78, 0.78, 0.12, 0x18181b); cBack.position.set(0, 0.96, 0.34);
    const cStem = makeBox(0.14, 0.52, 0.14, 0x3f3f46); cStem.position.y = 0.26;
    const cBase = makeBox(0.72, 0.08, 0.72, 0x3f3f46); cBase.position.y = 0.05;
    chair.add(cSeat, cBack, cStem, cBase);
    group.add(chair);

    // Subtle selection floor ring
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(1.72, 1.92, 32),
      new THREE.MeshBasicMaterial({
        color: cfg.color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.0,
      })
    );
    ring.rotation.x = -Math.PI / 2;
    ring.position.set(0, 0.03, 0.45);
    group.add(ring);

    group.traverse((child) => {
      if (child.isMesh) {
        child.userData.agentId = agentId;
        this.clickables.push(child);
      }
    });

    this.scene.add(group);
    return { group, screen, ring };
  }

  _buildVoxelCharacter(agentId, cfg) {
    const root = new THREE.Group();
    root.position.set(cfg.lounge[0], 0, cfg.lounge[1]);

    const shadow = new THREE.Mesh(
      new THREE.CircleGeometry(0.5, 16),
      new THREE.MeshBasicMaterial({ color: 0x09090b, transparent: true, opacity: 0.22 })
    );
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.y = 0.03;
    root.add(shadow);

    const bodyGroup = new THREE.Group();
    root.add(bodyGroup);

    const isSuit = cfg.outfit === "suit";
    const shoeColor = isSuit ? 0x18181b : 0xffffff;

    const leftLeg = new THREE.Group();
    leftLeg.position.set(-0.15, 0.58, 0);
    const lLeg = makeBox(0.24, 0.54, 0.26, cfg.pants); lLeg.position.y = -0.27;
    const lShoe = makeBox(0.26, 0.12, 0.32, shoeColor); lShoe.position.set(0, -0.52, 0.03);
    leftLeg.add(lLeg, lShoe);

    const rightLeg = new THREE.Group();
    rightLeg.position.set(0.15, 0.58, 0);
    const rLeg = makeBox(0.24, 0.54, 0.26, cfg.pants); rLeg.position.y = -0.27;
    const rShoe = makeBox(0.26, 0.12, 0.32, shoeColor); rShoe.position.set(0, -0.52, 0.03);
    rightLeg.add(rLeg, rShoe);

    const torso = makeBox(0.62, 0.7, 0.36, cfg.shirt); torso.position.y = 0.94;
    if (isSuit) {
      // Crisp white dress shirt front, crimson executive tie, structured suit lapels & coat tail
      const dressShirt = makeBox(0.24, 0.52, 0.05, 0xfafafa, { castShadow: false });
      dressShirt.position.set(0, 1.02, 0.175);
      const tie = makeBox(0.09, 0.44, 0.05, 0xf43f5e, { castShadow: false });
      tie.position.set(0, 0.98, 0.195);
      const lapelL = makeBox(0.11, 0.42, 0.05, 0x27272a, { castShadow: false });
      lapelL.position.set(-0.14, 1.04, 0.185);
      const lapelR = makeBox(0.11, 0.42, 0.05, 0x27272a, { castShadow: false });
      lapelR.position.set(0.14, 1.04, 0.185);
      const coatHem = makeBox(0.64, 0.18, 0.38, 0x111114);
      coatHem.position.set(0, 0.56, -0.01);
      bodyGroup.add(dressShirt, tie, lapelL, lapelR, coatHem);
    }

    const leftArm = new THREE.Group();
    leftArm.position.set(-0.42, 1.22, 0);
    const lArm = makeBox(0.19, 0.58, 0.21, cfg.shirt); lArm.position.y = -0.24;
    const lHand = makeBox(0.17, 0.15, 0.19, cfg.skin); lHand.position.y = -0.54;
    leftArm.add(lArm, lHand);
    if (isSuit) {
      const lCuff = makeBox(0.195, 0.07, 0.215, 0xfafafa, { castShadow: false });
      lCuff.position.y = -0.47;
      leftArm.add(lCuff);
    }

    const rightArm = new THREE.Group();
    rightArm.position.set(0.42, 1.22, 0);
    const rArm = makeBox(0.19, 0.58, 0.21, cfg.shirt); rArm.position.y = -0.24;
    const rHand = makeBox(0.17, 0.15, 0.19, cfg.skin); rHand.position.y = -0.54;
    rightArm.add(rArm, rHand);
    if (isSuit) {
      const rCuff = makeBox(0.195, 0.07, 0.215, 0xfafafa, { castShadow: false });
      rCuff.position.y = -0.47;
      rightArm.add(rCuff);
    }

    const head = new THREE.Group();
    head.position.set(0, 1.62, 0);
    const skull = makeBox(0.66, 0.64, 0.62, cfg.skin);
    const hairTop = makeBox(0.7, 0.22, 0.66, cfg.hair); hairTop.position.y = 0.28;
    const hairBack = makeBox(0.68, 0.45, 0.15, cfg.hair); hairBack.position.set(0, 0.09, -0.28);
    head.add(skull, hairTop, hairBack);

    if (cfg.accessory === "blindfold") {
      // Crisp white layered eye bandage (perban mata) wrapped around the head + knot tails at back!
      const bandageMain = makeBox(0.71, 0.22, 0.67, 0xf8fafc);
      bandageMain.position.set(0, 0.03, 0.0);
      const bandageCrease = makeBox(0.72, 0.035, 0.68, 0xcbd5e1, { castShadow: false });
      bandageCrease.position.set(0, 0.03, 0.0);
      const knot = makeBox(0.16, 0.14, 0.1, 0xf1f5f9);
      knot.position.set(0, 0.02, -0.35);
      const tailL = makeBox(0.08, 0.26, 0.06, 0xf8fafc);
      tailL.position.set(-0.08, -0.1, -0.37);
      tailL.rotation.z = 0.28;
      const tailR = makeBox(0.08, 0.3, 0.06, 0xf1f5f9);
      tailR.position.set(0.08, -0.12, -0.37);
      tailR.rotation.z = -0.32;
      // Stylish swept spiky jet-black voxel hair crown + subtle forehead fringe above crisp white bandage
      const spike1 = makeBox(0.68, 0.16, 0.56, cfg.hair); spike1.position.set(0, 0.42, 0.04);
      const spike2 = makeBox(0.46, 0.14, 0.42, cfg.hair); spike2.position.set(-0.08, 0.5, 0.08);
      const fringe = makeBox(0.56, 0.09, 0.1, cfg.hair); fringe.position.set(0.04, 0.19, 0.31);
      head.add(bandageMain, bandageCrease, knot, tailL, tailR, spike1, spike2, fringe);
    } else {
      const eyeL = makeBox(0.09, 0.11, 0.04, 0x09090b, { castShadow: false }); eyeL.position.set(-0.15, 0.02, 0.31);
      const eyeR = makeBox(0.09, 0.11, 0.04, 0x09090b, { castShadow: false }); eyeR.position.set(0.15, 0.02, 0.31);
      head.add(eyeL, eyeR);
    }

    if (cfg.accessory === "glasses") {
      const gl = makeBox(0.5, 0.16, 0.05, 0x18181b, { castShadow: false }); gl.position.set(0, 0.03, 0.33);
      head.add(gl);
    } else if (cfg.accessory === "headphones") {
      const band = makeBox(0.74, 0.1, 0.16, 0xec4899); band.position.set(0, 0.38, 0);
      const eL = makeBox(0.12, 0.3, 0.24, 0xec4899); eL.position.set(-0.38, 0.02, 0);
      const eR = makeBox(0.12, 0.3, 0.24, 0xec4899); eR.position.set(0.38, 0.02, 0);
      head.add(band, eL, eR);
    } else if (cfg.accessory === "cap") {
      const cap = makeBox(0.72, 0.18, 0.68, 0x059669); cap.position.set(0, 0.34, 0.04);
      const brim = makeBox(0.64, 0.07, 0.28, 0x047857); brim.position.set(0, 0.26, 0.4);
      head.add(cap, brim);
    } else if (cfg.accessory === "headset") {
      const ear = makeBox(0.1, 0.26, 0.22, 0x7c3aed); ear.position.set(0.37, 0, 0);
      const mic = makeBox(0.3, 0.05, 0.05, 0x18181b); mic.position.set(0.24, -0.12, 0.26);
      head.add(ear, mic);
    }

    bodyGroup.add(leftLeg, rightLeg, torso, leftArm, rightArm, head);
    root.traverse((child) => {
      if (child.isMesh) {
        child.userData.agentId = agentId;
        this.clickables.push(child);
      }
    });
    this.scene.add(root);

    const tagEl = document.createElement("div");
    tagEl.className = "voxel-tag";
    tagEl.addEventListener("click", (ev) => {
      ev.stopPropagation();
      this.selectAgent(agentId);
      if (this.onSelectAgent) this.onSelectAgent(agentId);
    });
    this.bubbleLayer.appendChild(tagEl);

    return { root, bodyGroup, head, leftArm, rightArm, leftLeg, rightLeg, tagEl };
  }

  _buildAllWorkstationsAndAgents() {
    for (const [agentId, cfg] of Object.entries(DESK_LAYOUT)) {
      const desk = this._buildDesk(agentId, cfg);
      const char = this._buildVoxelCharacter(agentId, cfg);
      const sparkle = makeBox(0.18, 0.18, 0.18, cfg.color, {
        emissive: cfg.color,
        emissiveIntensity: 1.0,
        castShadow: false,
      });
      sparkle.visible = false;
      sparkle.position.set(cfg.desk[0], 2.2, cfg.desk[1]);
      this.scene.add(sparkle);

      this.agents3d[agentId] = {
        id: agentId,
        cfg,
        desk,
        char,
        sparkle,
        status: "idle",
        name: agentId,
        role: "",
        bubble: "",
        unread: false,
        tempBubble: "",
        tempBubbleKind: "",
        tempBubbleTimer: 0,
        boarded: false,
        seatedMeeting: false,
        waypoints: [],
        targetPos: new THREE.Vector3(cfg.lounge[0], 0, cfg.lounge[1]),
        wanderTimer: 2 + Math.random() * 4,
      };
    }
  }

  _setRouteTo(entry, destX, destZ) {
    const pos = entry.char.root.position;
    entry.waypoints = [];
    entry.seatedMeeting = false;

    const inMgrStart = pos.x < -6.2 && pos.z < -4.6;
    const inMgrDest = destX < -6.2 && destZ < -4.6;
    const outStart = pos.z > 11.15;
    const outDest = destZ > 11.15;

    // 1. Exit Manager's Private Glass Office through its doorway (-7.5, -4.6)
    if (inMgrStart && !inMgrDest) {
      entry.waypoints.push(new THREE.Vector3(-7.5, 0, -5.2));
      entry.waypoints.push(new THREE.Vector3(-7.5, 0, -3.5));
    }

    // 2. Enter building from outside through the sliding main front glass doors (0, 11.15)
    if (outStart && !outDest) {
      entry.waypoints.push(new THREE.Vector3(0, 0, 12.2));
      entry.waypoints.push(new THREE.Vector3(0, 0, 9.6));
    }

    // 3. Navigate cleanly around the lounge slat partition (x = -3.0, z = 2.4..8.2)
    const curX = entry.waypoints.length ? entry.waypoints[entry.waypoints.length - 1].x : pos.x;
    const curZ = entry.waypoints.length ? entry.waypoints[entry.waypoints.length - 1].z : pos.z;
    if (!outDest && ((curX < -3.1 && destX > -2.6 && (curZ > 1.8 || destZ > 1.8)) ||
        (curX > -2.6 && destX < -3.1 && (curZ > 1.8 || destZ > 1.8)))) {
      entry.waypoints.push(new THREE.Vector3(-2.6, 0, 1.5));
      entry.waypoints.push(new THREE.Vector3(destX < -3.1 ? -4.8 : -0.4, 0, 1.5));
    }

    // 4. Enter Manager's Private Glass Office via its doorway
    if (!inMgrStart && inMgrDest) {
      entry.waypoints.push(new THREE.Vector3(-7.5, 0, -3.5));
      entry.waypoints.push(new THREE.Vector3(-7.5, 0, -5.2));
    }

    // 5. Exit building outdoors through the sliding front glass doors (0, 11.15)
    if (!outStart && outDest) {
      entry.waypoints.push(new THREE.Vector3(0, 0, 9.6));
      entry.waypoints.push(new THREE.Vector3(0, 0, 12.6));
    }

    entry.waypoints.push(new THREE.Vector3(destX, 0, destZ));
    entry.targetPos.copy(entry.waypoints.shift());
  }

  _setTempBubble(entry, text, kind = "commute", duration = 2.8) {
    entry.tempBubble = text;
    entry.tempBubbleKind = kind;
    entry.tempBubbleTimer = duration;
    this._refreshTag(entry);
  }

  _routeIdleAgentByMode(entry) {
    if (entry.boarded) return;
    if (this.officeMode === "meeting") {
      const seat = MEETING_SEATS[entry.id];
      if (seat) {
        this._setRouteTo(entry, seat.pos[0], seat.pos[1]);
        return;
      }
    }
    this._setRouteTo(entry, entry.cfg.lounge[0], entry.cfg.lounge[1]);
  }

  syncOfficeMode(mode, modeSeq = 0) {
    const normalized = ["work", "meeting", "holiday"].includes(mode) ? mode : "work";
    const isInitialLoad = this.prevOfficeMode === null;
    if (!isInitialLoad && normalized === this.officeMode && modeSeq === this.lastModeSeq) {
      return;
    }

    const oldMode = this.officeMode;
    this.officeMode = normalized;
    this.prevOfficeMode = normalized;
    this.lastModeSeq = modeSeq;

    if (isInitialLoad) {
      if (normalized === "holiday") {
        this.commuteState = "on_holiday";
        for (const entry of Object.values(this.agents3d)) {
          entry.boarded = true;
          entry.char.root.visible = false;
          entry.char.tagEl.style.display = "none";
        }
        this._applyInteriorLights();
      } else if (normalized === "meeting") {
        this.commuteState = "at_office";
        for (const entry of Object.values(this.agents3d)) {
          if (entry.status === "idle") this._routeIdleAgentByMode(entry);
        }
      }
      return;
    }

    if (normalized === "holiday") {
      // Trigger Zentira Shuttle Van pickup + agents walking out front glass doors!
      if (this.commuteState === "on_holiday") return;
      this.unboardQueue = [];
      this.commuteState = "departing_arrive";
      this.shuttleVan.visible = true;
      if (this.shuttleVan.position.x > 6 || this.shuttleVan.position.x < -50) {
        this.shuttleVan.position.set(-46, -0.22, 17.5);
      }
      const list = Object.values(this.agents3d);
      list.forEach((entry, idx) => {
        if (!entry.boarded) {
          this._setTempBubble(entry, DEPART_LINES[idx % DEPART_LINES.length], "commute", 3.6);
          // Stagger boarding positions outside doorway toward the van
          this._setRouteTo(entry, (idx - 2.5) * 0.32, 15.8);
        }
      });
      this._applyInteriorLights();
      return;
    }

    // Switching to "work" (Masuk) or "meeting"
    const wasAway =
      oldMode === "holiday" ||
      this.commuteState === "on_holiday" ||
      this.commuteState.startsWith("departing_");

    if (wasAway) {
      // Trigger Zentira Shuttle Van arrival dropping off all agents at front entrance!
      this.commuteState = "arriving_drive";
      this.shuttleVan.visible = true;
      this.shuttleVan.position.set(-46, -0.22, 17.5);
      this.unboardQueue = Object.keys(this.agents3d);
      this.unboardTimer = 0.25;
      for (const entry of Object.values(this.agents3d)) {
        entry.boarded = true;
        entry.char.root.visible = false;
        entry.char.tagEl.style.display = "none";
        entry.waypoints = [];
      }
      this._applyInteriorLights();
      return;
    }

    // Already at office: smoothly switch between "work" and "meeting"
    this.meetingChatTimer = 1.4;
    for (const entry of Object.values(this.agents3d)) {
      if (entry.tempBubbleKind === "meeting") {
        entry.tempBubble = "";
        entry.tempBubbleTimer = 0;
        this._refreshTag(entry);
      }
      if (entry.status === "idle") {
        this._routeIdleAgentByMode(entry);
      }
    }
  }

  syncAgentsState(agentsList) {
    for (const data of agentsList) {
      const entry = this.agents3d[data.id];
      if (!entry) continue;

      const prevStatus = entry.status;
      entry.status = data.status;
      entry.name = data.name;
      entry.role = data.role;
      entry.bubble = data.bubble;
      entry.unread = Boolean(data.unread);
      entry.number = data.number;

      if (!entry.boarded) {
        if (data.status === "working" || data.status === "done" || data.status === "error") {
          if (prevStatus === "idle") {
            this._setRouteTo(entry, entry.cfg.chair[0], entry.cfg.chair[1]);
          } else {
            entry.targetPos.set(entry.cfg.chair[0], 0, entry.cfg.chair[1]);
          }
        } else if (prevStatus !== "idle") {
          this._routeIdleAgentByMode(entry);
        }
      }

      this._refreshTag(entry, data.color);
    }
  }

  _refreshTag(entry, colorHex) {
    entry.char.tagEl.replaceChildren();
    if (entry.unread || entry.status === "done") {
      const badge = document.createElement("span");
      badge.className = "voxel-alert";
      badge.textContent = "SIAP";
      entry.char.tagEl.appendChild(badge);
    }

    const activeBubbleText =
      entry.status !== "idle"
        ? entry.bubble
        : entry.tempBubble || entry.bubble;
    const bubbleKind =
      entry.status !== "idle"
        ? entry.status
        : entry.tempBubble
          ? entry.tempBubbleKind || "meeting"
          : "idle";

    const showBubble =
      Boolean(activeBubbleText) &&
      (entry.status !== "idle" ||
        Boolean(entry.tempBubble) ||
        this.selectedAgentId === entry.id ||
        this.hoveredAgentId === entry.id);
    if (showBubble) {
      const b = document.createElement("div");
      const canDismiss = entry.status === "done" || entry.status === "error";
      b.className = `voxel-bubble ${bubbleKind}${canDismiss ? " dismissible" : ""}`;
      const txt = document.createElement("span");
      txt.textContent = activeBubbleText;
      b.appendChild(txt);

      if (canDismiss && this.onDismissAgent) {
        const closeBtn = document.createElement("button");
        closeBtn.type = "button";
        closeBtn.className = "voxel-bubble-close";
        closeBtn.title = "Tutup teks & kembalikan agent seperti biasa";
        closeBtn.textContent = "×";
        closeBtn.addEventListener("click", (ev) => {
          ev.stopPropagation();
          this.onDismissAgent(entry.id);
        });
        b.appendChild(closeBtn);
      }
      entry.char.tagEl.appendChild(b);
    }

    const plate = document.createElement("div");
    plate.className = "voxel-nameplate";
    const dot = document.createElement("span");
    dot.className = "voxel-dot";
    dot.style.background = colorHex || `#${entry.cfg.color.toString(16).padStart(6, "0")}`;
    const label = document.createElement("span");
    label.textContent = entry.name;
    plate.append(dot, label);
    entry.char.tagEl.appendChild(plate);
  }

  selectAgent(agentId) {
    this.selectedAgentId = agentId;
    for (const entry of Object.values(this.agents3d)) {
      this._refreshTag(entry);
    }
    if (!agentId || !this.agents3d[agentId]) return;
    const entry = this.agents3d[agentId];
    this.camLerpPos = null;
    this.camLerpTarget = new THREE.Vector3(
      entry.cfg.desk[0] * 0.55,
      1.1,
      entry.cfg.desk[1] * 0.55
    );
  }

  resetCamera() {
    this.setCameraPreset("iso");
  }

  _bindEvents() {
    window.addEventListener("resize", () => {
      if (this.externalRenderControl) return;
      const aspect = window.innerWidth / window.innerHeight;
      this.camera.aspect = aspect;
      this.camera.fov = aspect < 0.85 ? 45 : 36;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
    });

    this.canvas.addEventListener("pointerdown", (e) => {
      this.isPointerDragging = false;
      this.pointerDownPos = { x: e.clientX, y: e.clientY };
      this.camLerpPos = null;
      this.camLerpTarget = null;
    });

    this.canvas.addEventListener("pointermove", (e) => {
      const dx = e.clientX - this.pointerDownPos.x;
      const dy = e.clientY - this.pointerDownPos.y;
      if (Math.hypot(dx, dy) > 6) this.isPointerDragging = true;

      const hit = this._raycastAgent(e);
      if (hit !== this.hoveredAgentId) {
        const prev = this.hoveredAgentId;
        this.hoveredAgentId = hit;
        if (prev && this.agents3d[prev]) this._refreshTag(this.agents3d[prev]);
        if (hit && this.agents3d[hit]) this._refreshTag(this.agents3d[hit]);
      }
      this.canvas.style.cursor = hit ? "pointer" : "grab";
    });

    this.canvas.addEventListener("pointerup", (e) => {
      if (this.isPointerDragging) return;
      const hit = this._raycastAgent(e);
      if (hit) {
        this.selectAgent(hit);
        if (this.onSelectAgent) this.onSelectAgent(hit);
      }
    });
  }

  _raycastAgent(event) {
    const rect = this.canvas.getBoundingClientRect();
    this.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hits = this.raycaster.intersectObjects(this.clickables, false);
    return hits.length > 0 ? hits[0].object.userData.agentId || null : null;
  }

  _animate() {
    requestAnimationFrame(() => this._animate());
    if (this.externalRenderControl) {
      this.clock.getDelta();
      return;
    }
    const dt = Math.min(this.clock.getDelta(), 0.05);
    this.stepSimulation(dt);
    this.controls.update();
    this.renderFrame();
  }

  renderFrame() {
    this.renderer.render(this.scene, this.camera);
  }

  stepSimulation(dt) {
    this.simTime += dt;
    const elapsed = this.simTime;

    // Drifting sky clouds
    for (const cloud of this.clouds) {
      cloud.position.x += cloud.userData.speed * dt;
      if (cloud.position.x > 64) cloud.position.x = -64;
    }

    // Moving voxel cars around the neighborhood
    for (const car of this.cars) {
      const c = car.userData;
      if (c.axis === "x") {
        car.position.x += c.dir * c.speed * dt;
        if (car.position.x > 46) car.position.x = -46;
        if (car.position.x < -46) car.position.x = 46;
      } else {
        car.position.z += c.dir * c.speed * dt;
        if (car.position.z > 46) car.position.z = -46;
        if (car.position.z < -46) car.position.z = 46;
      }
    }

    // Coffee mug steam
    for (const bit of this.steamBits) {
      const cycle = (elapsed * 0.55 + bit.userData.phase) % 1;
      bit.position.y = bit.userData.baseY + cycle * 0.9;
      bit.scale.setScalar(0.1 * (1 - cycle * 0.7));
    }

    // Smooth camera preset / agent focus transitions (interactive mode only)
    if (!this.externalRenderControl) {
      if (this.camLerpPos) {
        this.camera.position.lerp(this.camLerpPos, 0.075);
        if (this.camera.position.distanceTo(this.camLerpPos) < 0.08) this.camLerpPos = null;
      }
      if (this.camLerpTarget) {
        this.controls.target.lerp(this.camLerpTarget, 0.08);
        if (this.controls.target.distanceTo(this.camLerpTarget) < 0.05) this.camLerpTarget = null;
      }
    }

    // Auto-update enclosed roof & walls if camera glides inside/outside studio
    this._updateEnclosureVisibility();

    // Update Zentira Shuttle Van choreography (Libur / Masuk)
    this._updateShuttleChoreography(dt);

    // Interactive Meeting conversation rotation when agents are seated around the table
    if (this.officeMode === "meeting" && this.commuteState === "at_office") {
      const seatedIds = Object.values(this.agents3d)
        .filter((e) => e.seatedMeeting && e.status === "idle" && !e.boarded)
        .map((e) => e.id);
      if (seatedIds.length >= 2) {
        this.meetingChatTimer -= dt;
        if (this.meetingChatTimer <= 0) {
          this.meetingChatTimer = 3.2;
          const ordered = this.meetingSpeakerOrder.filter((id) => seatedIds.includes(id));
          if (ordered.length > 0) {
            const speakerId = ordered[this.meetingSpeakerIdx % ordered.length];
            this.meetingSpeakerIdx = (this.meetingSpeakerIdx + 1) % ordered.length;
            const lines = MEETING_CHAT_LINES[speakerId] || ["Siap koordinasi tim!"];
            const line = lines[this.meetingChatLineIdx % lines.length];
            this.meetingChatLineIdx += 1;
            this._setTempBubble(this.agents3d[speakerId], line, "meeting", 2.9);
          }
        }
      }
    }

    // Animate All 6 Voxel Employees (Walking, Working, Seated Meeting, Shuttle Commute)
    const projVec = new THREE.Vector3();
    let anyoneNearFrontDoor = false;
    const activeMeetingSpeakerId =
      this.officeMode === "meeting"
        ? Object.values(this.agents3d).find((e) => e.tempBubbleKind === "meeting" && e.tempBubbleTimer > 0)?.id || null
        : null;

    for (const entry of Object.values(this.agents3d)) {
      const { char, desk, sparkle, cfg } = entry;
      const pos = char.root.position;

      // Decay temporary chat bubbles (meeting / commute greetings)
      if (entry.tempBubbleTimer > 0) {
        entry.tempBubbleTimer -= dt;
        if (entry.tempBubbleTimer <= 0) {
          entry.tempBubble = "";
          entry.tempBubbleKind = "";
          this._refreshTag(entry);
        }
      }

      if (entry.boarded) {
        char.root.visible = false;
        char.tagEl.style.display = "none";
        sparkle.visible = false;
        desk.ring.material.opacity = 0;
        continue;
      }

      char.root.visible = true;
      char.tagEl.style.display = "";

      if (Math.hypot(pos.x, pos.z - 11.15) < 3.4) {
        anyoneNearFrontDoor = true;
      }

      // Casual lounge wandering ONLY in normal "work" mode when idle at office
      if (
        this.officeMode === "work" &&
        this.commuteState === "at_office" &&
        entry.status === "idle" &&
        entry.waypoints.length === 0
      ) {
        entry.wanderTimer -= dt;
        if (entry.wanderTimer <= 0) {
          entry.wanderTimer = 5.5 + Math.random() * 5;
          const ox = (Math.random() - 0.5) * 1.2;
          const oz = (Math.random() - 0.5) * 1.2;
          if (entry.id === "manager") {
            // Keep Denn strolling naturally inside his private glass executive suite!
            entry.targetPos.set(
              Math.max(-12.2, Math.min(-7.6, cfg.lounge[0] + ox)),
              0,
              Math.max(-6.4, Math.min(-5.1, cfg.lounge[1] + oz))
            );
          } else {
            entry.targetPos.set(
              Math.max(-11.8, Math.min(11.5, cfg.lounge[0] + ox)),
              0,
              Math.max(-3.6, Math.min(8.4, cfg.lounge[1] + oz))
            );
          }
        }
      }

      const dx = entry.targetPos.x - pos.x;
      const dz = entry.targetPos.z - pos.z;
      const dist = Math.hypot(dx, dz);

      if (dist > 0.14) {
        entry.seatedMeeting = false;
        const fastWalk =
          entry.status === "working" ||
          this.commuteState.startsWith("departing_") ||
          this.commuteState.startsWith("arriving_");
        const speed = fastWalk ? 4.8 : 2.2;
        const step = Math.min(dist, speed * dt);
        pos.x += (dx / dist) * step;
        pos.z += (dz / dist) * step;

        const targetYaw = Math.atan2(dx, dz);
        let diff = targetYaw - char.root.rotation.y;
        while (diff > Math.PI) diff -= Math.PI * 2;
        while (diff < -Math.PI) diff += Math.PI * 2;
        char.root.rotation.y += diff * Math.min(1, dt * 10);

        const swing = Math.sin(elapsed * (fastWalk ? 13 : 8.5)) * 0.65;
        char.leftLeg.rotation.x = swing;
        char.rightLeg.rotation.x = -swing;
        char.leftArm.rotation.x = -swing * 0.8;
        char.rightArm.rotation.x = swing * 0.8;
        char.bodyGroup.position.y = Math.abs(Math.sin(elapsed * 12)) * 0.06;
      } else if (entry.waypoints.length > 0) {
        entry.targetPos.copy(entry.waypoints.shift());
      } else {
        // Reached destination
        if (this.commuteState === "departing_boarding" && pos.z > 14.5) {
          // Step into the parked Zentira Shuttle Van!
          entry.boarded = true;
          char.root.visible = false;
          char.tagEl.style.display = "none";
          continue;
        }

        if (entry.status === "working") {
          char.leftLeg.rotation.x *= 0.85;
          char.rightLeg.rotation.x *= 0.85;
          let diff = Math.PI - char.root.rotation.y;
          while (diff > Math.PI) diff -= Math.PI * 2;
          while (diff < -Math.PI) diff += Math.PI * 2;
          char.root.rotation.y += diff * Math.min(1, dt * 10);

          char.leftArm.rotation.x = -1.1 + Math.sin(elapsed * 18) * 0.28;
          char.rightArm.rotation.x = -1.1 + Math.cos(elapsed * 18) * 0.28;
          char.head.rotation.y = Math.sin(elapsed * 3.5) * 0.14;
          char.bodyGroup.position.y = Math.sin(elapsed * 8) * 0.03;
          desk.screen.material.emissive.setHex(cfg.color);
          desk.screen.material.emissiveIntensity = 0.72 + Math.sin(elapsed * 9) * 0.25;
          sparkle.visible = true;
          sparkle.position.y = 2.1 + ((elapsed * 0.9) % 0.9);
          sparkle.rotation.y += dt * 4;
        } else if (entry.status === "done") {
          char.leftLeg.rotation.x *= 0.85;
          char.rightLeg.rotation.x *= 0.85;
          char.leftArm.rotation.x = -0.35 + Math.sin(elapsed * 6) * 0.25;
          char.rightArm.rotation.x = -0.35 + Math.sin(elapsed * 6) * 0.25;
          char.bodyGroup.position.y = Math.abs(Math.sin(elapsed * 5.2)) * 0.16;
          desk.screen.material.emissive.setHex(0x10b981);
          desk.screen.material.emissiveIntensity = 0.75;
          sparkle.visible = false;
        } else if (entry.status === "error") {
          char.leftLeg.rotation.x *= 0.85;
          char.rightLeg.rotation.x *= 0.85;
          char.head.rotation.z = Math.sin(elapsed * 4) * 0.15;
          char.bodyGroup.position.y = 0;
          desk.screen.material.emissive.setHex(0xef4444);
          desk.screen.material.emissiveIntensity = 0.75;
          sparkle.visible = false;
        } else if (this.officeMode === "meeting" && this.commuteState === "at_office") {
          // Seated interactive Meeting pose!
          entry.seatedMeeting = true;
          const seat = MEETING_SEATS[entry.id];
          if (seat) {
            let diff = seat.yaw - char.root.rotation.y;
            while (diff > Math.PI) diff -= Math.PI * 2;
            while (diff < -Math.PI) diff += Math.PI * 2;
            char.root.rotation.y += diff * Math.min(1, dt * 8);
          }
          char.bodyGroup.position.y += (-0.18 - char.bodyGroup.position.y) * Math.min(1, dt * 10);
          char.leftLeg.rotation.x += (-1.45 - char.leftLeg.rotation.x) * Math.min(1, dt * 10);
          char.rightLeg.rotation.x += (-1.45 - char.rightLeg.rotation.x) * Math.min(1, dt * 10);
          char.head.rotation.z *= 0.85;

          const isTalking = activeMeetingSpeakerId === entry.id;
          if (isTalking) {
            char.leftArm.rotation.x = -0.78 + Math.sin(elapsed * 9.5) * 0.34;
            char.rightArm.rotation.x = -0.68 + Math.cos(elapsed * 8.5) * 0.34;
            char.head.rotation.y = Math.sin(elapsed * 4.2) * 0.22;
            char.head.rotation.x = Math.sin(elapsed * 6.5) * 0.08;
          } else {
            char.leftArm.rotation.x += (-0.55 - char.leftArm.rotation.x) * Math.min(1, dt * 8);
            char.rightArm.rotation.x += (-0.55 - char.rightArm.rotation.x) * Math.min(1, dt * 8);
            char.head.rotation.y = Math.sin(elapsed * 1.4 + cfg.desk[0]) * 0.22;
            char.head.rotation.x = Math.sin(elapsed * 2.6 + cfg.desk[0]) * 0.06;
          }
          desk.screen.material.emissive.setHex(cfg.color);
          desk.screen.material.emissiveIntensity = 0.16;
          sparkle.visible = false;
        } else {
          char.leftLeg.rotation.x *= 0.85;
          char.rightLeg.rotation.x *= 0.85;
          char.leftArm.rotation.x *= 0.85;
          char.rightArm.rotation.x *= 0.85;
          char.head.rotation.x *= 0.85;
          char.head.rotation.z *= 0.85;
          char.head.rotation.y = Math.sin(elapsed * 1.1 + cfg.desk[0]) * 0.25;
          char.bodyGroup.position.y = Math.sin(elapsed * 2.4 + cfg.desk[0]) * 0.03;
          desk.screen.material.emissive.setHex(cfg.color);
          desk.screen.material.emissiveIntensity = 0.2;
          sparkle.visible = false;
        }
      }

      const isHl = this.selectedAgentId === entry.id || this.hoveredAgentId === entry.id;
      desk.ring.material.opacity = isHl ? 0.85 : 0.0;

      projVec.set(pos.x, 2.45 + char.bodyGroup.position.y, pos.z);
      projVec.project(this.camera);
      const visible = projVec.z < 1 && !document.body.classList.contains("zen-mode");
      char.tagEl.style.opacity = visible ? "1" : "0";
      char.tagEl.style.pointerEvents = visible ? "auto" : "none";
      if (visible) {
        char.tagEl.style.left = `${(projVec.x * 0.5 + 0.5) * window.innerWidth}px`;
        char.tagEl.style.top = `${(-projVec.y * 0.5 + 0.5) * window.innerHeight}px`;
      }
    }

    // Smoothly slide main front glass doors open/closed as agents pass through!
    const doorTarget = anyoneNearFrontDoor ? 1.0 : 0.0;
    this.doorOpenAmount += (doorTarget - this.doorOpenAmount) * Math.min(1, dt * 6);
    if (this.doorLeft && this.doorRight) {
      this.doorLeft.position.x = -0.92 - this.doorOpenAmount * 1.45;
      this.doorRight.position.x = 0.92 + this.doorOpenAmount * 1.45;
    }
  }

  _updateShuttleChoreography(dt) {
    if (!this.shuttleVan) return;
    const van = this.shuttleVan;
    let wantVanDoorOpen = false;

    if (this.commuteState === "departing_arrive") {
      van.visible = true;
      van.position.x += Math.min(15 * dt, Math.max(3.5 * dt, (0 - van.position.x) * 2.2 * dt));
      if (van.position.x >= -0.15) {
        van.position.x = 0;
        this.commuteState = "departing_boarding";
      }
    } else if (this.commuteState === "departing_boarding") {
      wantVanDoorOpen = true;
      const allBoarded = Object.values(this.agents3d).every((e) => e.boarded);
      if (allBoarded) {
        this.commuteState = "departing_leave";
      }
    } else if (this.commuteState === "departing_leave") {
      van.position.x += 13.5 * dt;
      if (van.position.x > 52) {
        van.visible = false;
        this.commuteState = "on_holiday";
        this._applyInteriorLights();
      }
    } else if (this.commuteState === "arriving_drive") {
      van.visible = true;
      van.position.x += Math.min(15 * dt, Math.max(3.8 * dt, (0 - van.position.x) * 2.2 * dt));
      if (van.position.x >= -0.15) {
        van.position.x = 0;
        this.commuteState = "arriving_unboard";
      }
    } else if (this.commuteState === "arriving_unboard") {
      wantVanDoorOpen = true;
      this.unboardTimer -= dt;
      if (this.unboardTimer <= 0 && this.unboardQueue.length > 0) {
        this.unboardTimer = 0.55;
        const aid = this.unboardQueue.shift();
        const entry = this.agents3d[aid];
        if (entry) {
          entry.boarded = false;
          entry.char.root.position.set(0.3, 0, 15.6);
          entry.char.root.visible = true;
          entry.char.tagEl.style.display = "";
          const greetIdx = this.meetingSpeakerOrder.indexOf(aid);
          this._setTempBubble(
            entry,
            ARRIVE_LINES[Math.max(0, greetIdx) % ARRIVE_LINES.length],
            "commute",
            3.0
          );
          if (entry.status !== "idle") {
            this._setRouteTo(entry, entry.cfg.chair[0], entry.cfg.chair[1]);
          } else {
            this._routeIdleAgentByMode(entry);
          }
        }
      }
      if (this.unboardQueue.length === 0 && this.unboardTimer <= -0.35) {
        this.commuteState = "arriving_leave";
      }
    } else if (this.commuteState === "arriving_leave") {
      van.position.x += 13.5 * dt;
      if (van.position.x > 52) {
        van.visible = false;
        this.commuteState = "at_office";
      }
    }

    const vTarget = wantVanDoorOpen ? 1.0 : 0.0;
    this.vanDoorOpenAmount += (vTarget - this.vanDoorOpenAmount) * Math.min(1, dt * 6);
    if (this.shuttleDoor) {
      this.shuttleDoor.position.x = 0.6 - this.vanDoorOpenAmount * 1.3;
    }
  }

  // =====================================================
  // 5. CINEMA ENGINE STAGE HOOKS (for deterministic 60fps MP4 & Live Preview)
  // =====================================================
  enterCinemaMode({ width, height, fov }) {
    const saved = {
      theme: this.currentTheme,
      roofMode: this.roofMode,
      officeMode: this.officeMode,
      camPreset: this.activeCamPreset,
      camPos: this.camera.position.clone(),
      camTarget: this.controls.target.clone(),
    };

    this.externalRenderControl = true;
    this.controls.enabled = false;
    this.camLerpPos = null;
    this.camLerpTarget = null;

    this.renderer.setPixelRatio(1);
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.fov = fov;
    this.camera.updateProjectionMatrix();

    // Stage all 6 agents inside the Shuttle Van ready to arrive smoothly at Scene 2!
    this.officeMode = "meeting";
    this.commuteState = "on_holiday";
    this.shuttleVan.visible = false;
    this.shuttleVan.position.set(-46, -0.22, 17.5);
    this.unboardQueue = Object.keys(this.agents3d);
    this.unboardTimer = 0.25;
    for (const entry of Object.values(this.agents3d)) {
      entry.boarded = true;
      entry.seatedMeeting = false;
      entry.char.root.visible = false;
      entry.char.tagEl.style.display = "none";
      entry.waypoints = [];
    }
    this.setTheme("day");
    this.setRoofMode("closed");
    return saved;
  }

  triggerCinemaShuttleArrival() {
    this.commuteState = "arriving_drive";
    this.shuttleVan.visible = true;
    this.shuttleVan.position.set(-46, -0.22, 17.5);
    this.unboardQueue = Object.keys(this.agents3d);
    this.unboardTimer = 0.25;
    this._applyInteriorLights();
  }

  exitCinemaMode(saved) {
    this.externalRenderControl = false;
    this.canvas.style.width = "";
    this.canvas.style.height = "";
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.isMobile ? 1.5 : 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight, true);
    const aspect = window.innerWidth / window.innerHeight;
    this.camera.aspect = aspect;
    this.camera.fov = aspect < 0.85 ? 45 : 36;
    this.camera.updateProjectionMatrix();
    this.controls.enabled = true;

    if (saved) {
      this.setTheme(saved.theme);
      this.setRoofMode(saved.roofMode);
      this.activeCamPreset = saved.camPreset;
      this.camera.position.copy(saved.camPos);
      this.controls.target.copy(saved.camTarget);
      this.shuttleVan.visible = false;
      this.unboardQueue = [];
      this.officeMode = saved.officeMode;
      this.commuteState = saved.officeMode === "holiday" ? "on_holiday" : "at_office";

      for (const entry of Object.values(this.agents3d)) {
        if (saved.officeMode === "holiday") {
          entry.boarded = true;
          entry.char.root.visible = false;
          entry.char.tagEl.style.display = "none";
        } else {
          entry.boarded = false;
          entry.char.root.visible = true;
          entry.char.tagEl.style.display = "";
          if (saved.officeMode === "meeting" && MEETING_SEATS[entry.id]) {
            const seat = MEETING_SEATS[entry.id];
            entry.char.root.position.set(seat.pos[0], 0, seat.pos[1]);
            entry.targetPos.set(seat.pos[0], 0, seat.pos[1]);
            entry.waypoints = [];
          } else {
            entry.char.root.position.set(entry.cfg.lounge[0], 0, entry.cfg.lounge[1]);
            entry.targetPos.set(entry.cfg.lounge[0], 0, entry.cfg.lounge[1]);
            entry.waypoints = [];
          }
        }
      }
      this._applyInteriorLights();
      this._updateEnclosureVisibility();
    }
  }
}
