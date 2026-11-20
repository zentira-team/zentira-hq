/**
 * Zentira Cinema Engine v2 — Curved CatmullRom 3D Drone Camera,
 * After Effects-style 2D Kinetic Typography & Motion Graphics Compositor,
 * and Deterministic Offline 60fps MP4 Renderer (WebCodecs H.264 + mp4-muxer).
 */
import * as THREE from "three";

const MP4_MUXER_URL = "https://cdn.jsdelivr.net/npm/mp4-muxer@5.1.4/build/mp4-muxer.mjs";

export const CINEMA_DURATION = 36.0;
const EXPORT_FPS = 60;

// --- After Effects-grade Easing Curves ---
const clamp01 = (x) => Math.max(0, Math.min(1, x));
const easeOutExpo = (t) => {
  const c = clamp01(t);
  return c === 1 ? 1 : 1 - Math.pow(2, -10 * c);
};
const easeInQuint = (t) => {
  const c = clamp01(t);
  return c * c * c * c * c;
};
const easeOutQuint = (t) => {
  const c = clamp01(t);
  return 1 - Math.pow(1 - c, 5);
};
const easeInOutSine = (t) => -(Math.cos(Math.PI * clamp01(t)) - 1) / 2;
const easeOutBack = (t) => {
  const c = clamp01(t);
  const c1 = 1.35;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(c - 1, 3) + c1 * Math.pow(c - 1, 2);
};
// Flowing cinema dolly velocity: avoids harsh stop-start robot feel while staying silky smooth!
const cinemaTravel = (t) => {
  const c = clamp01(t);
  return 0.24 * c + 0.76 * easeInOutSine(c);
};

// Envelope helper: directional entrance (easeOutExpo) -> smooth hold -> crisp accelerated exit (easeInQuint)
function animWindow(t, start, end, inDur = 0.65, outDur = 0.35) {
  if (t < start || t > end) return { active: false, enter: 0, exit: 1, alpha: 0 };
  const enter = easeOutExpo((t - start) / Math.max(0.05, inDur));
  const exit = t > end - outDur ? easeInQuint((t - (end - outDur)) / Math.max(0.05, outDur)) : 0;
  return {
    active: true,
    enter,
    exit,
    alpha: clamp01(enter) * (1 - clamp01(exit)),
  };
}

// --- 6 Generous Curved 3D Drone & Gimbal Scenes (36.0s total) ---
function buildCinemaScenes() {
  const mkCurve = (pts) =>
    new THREE.CatmullRomCurve3(
      pts.map(([x, y, z]) => new THREE.Vector3(x, y, z)),
      false,
      "centripetal"
    );

  return [
    {
      id: "exterior",
      start: 0.0,
      end: 6.2,
      label: "Scene 1 • Fasad Zentira HQ",
      theme: "day",
      roof: "closed",
      fovShift: [2.0, -0.5],
      posCurve: mkCurve([
        [-26.0, 16.5, 33.5],
        [-7.5, 13.8, 34.5],
        [14.5, 11.2, 29.5],
      ]),
      targetCurve: mkCurve([
        [-1.0, 3.4, 3.0],
        [0.0, 3.0, 5.2],
        [0.0, 2.5, 7.8],
      ]),
    },
    {
      id: "shuttle",
      start: 6.2,
      end: 13.0,
      label: "Scene 2 • Kedatangan Shuttle Van",
      theme: "day",
      roof: "closed",
      fovShift: [0.0, -1.5],
      posCurve: mkCurve([
        [12.4, 4.4, 25.4],
        [7.2, 3.7, 21.8],
        [2.4, 3.3, 18.8],
      ]),
      targetCurve: mkCurve([
        [-2.2, 1.8, 16.8],
        [0.0, 1.8, 14.4],
        [0.0, 2.0, 11.4],
      ]),
    },
    {
      id: "manager",
      start: 13.0,
      end: 18.5,
      label: "Scene 3 • @quietdenn & Ruang Manajer",
      theme: "day",
      roof: "closed",
      fovShift: [1.5, 0.0],
      posCurve: mkCurve([
        [-5.2, 3.65, 5.0],
        [-4.8, 3.4, 0.5],
        [-4.6, 3.15, -2.6],
      ]),
      targetCurve: mkCurve([
        [-14.5, 3.1, 0.15],
        [-12.6, 2.55, -4.6],
        [-10.2, 2.0, -7.8],
      ]),
    },
    {
      id: "branding",
      start: 18.5,
      end: 24.0,
      label: "Scene 4 • Zentira Team & Founder Wall",
      theme: "day",
      roof: "closed",
      fovShift: [1.0, -1.5],
      posCurve: mkCurve([
        [-4.0, 3.3, -1.6],
        [-1.0, 3.35, -0.35],
        [2.2, 3.3, -1.5],
      ]),
      targetCurve: mkCurve([
        [-1.0, 3.35, -10.8],
        [-1.0, 3.25, -10.8],
        [-1.0, 3.2, -10.8],
      ]),
    },
    {
      id: "meeting",
      start: 24.0,
      end: 30.2,
      label: "Scene 5 • Kolaborasi Meeting Tim AI",
      theme: "day",
      roof: "closed",
      fovShift: [1.5, 0.0],
      posCurve: mkCurve([
        [8.2, 5.2, 4.4],
        [1.8, 4.85, 7.3],
        [-5.2, 5.4, 4.9],
      ]),
      targetCurve: mkCurve([
        [0.8, 1.35, -0.8],
        [0.8, 1.3, -0.8],
        [0.8, 1.25, -0.8],
      ]),
    },
    {
      id: "finale",
      start: 30.2,
      end: CINEMA_DURATION,
      label: "Scene 6 • Night Mode Finale",
      theme: "night",
      roof: "closed",
      fovShift: [-1.0, 2.5],
      posCurve: mkCurve([
        [14.5, 9.2, 22.0],
        [22.5, 14.5, 29.5],
        [29.5, 19.6, 36.8],
      ]),
      targetCurve: mkCurve([
        [0.0, 2.8, 1.5],
        [0.0, 2.4, 1.5],
        [0.0, 2.2, 1.5],
      ]),
    },
  ];
}

// --- Canvas Drawing Primitives for After Effects-style Motion Graphics ---
function roundRectPath(ctx, x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.lineTo(x + w - rr, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + rr);
  ctx.lineTo(x + w, y + h - rr);
  ctx.quadraticCurveTo(x + w, y + h, x + w - rr, y + h);
  ctx.lineTo(x + rr, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - rr);
  ctx.lineTo(x, y + rr);
  ctx.quadraticCurveTo(x, y, x + rr, y);
  ctx.closePath();
}

function drawMaskedLine(ctx, text, x, y, font, color, enterT, exitT, align = "left", lineH = 72) {
  ctx.save();
  ctx.font = font;
  ctx.textAlign = align;
  ctx.textBaseline = "alphabetic";
  const metrics = ctx.measureText(text);
  const tw = metrics.width + 24;
  const clipX = align === "center" ? x - tw / 2 : align === "right" ? x - tw : x - 8;
  ctx.beginPath();
  ctx.rect(clipX, y - lineH * 0.92, tw + 16, lineH * 1.16);
  ctx.clip();

  const slideIn = (1 - enterT) * lineH * 1.08;
  const slideOut = -exitT * lineH * 1.05;
  ctx.globalAlpha = clamp01(enterT * 1.4) * (1 - exitT);
  ctx.fillStyle = color;
  ctx.fillText(text, x, y + slideIn + slideOut);
  ctx.restore();
}

function loadImageSafe(src) {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = src;
  });
}

// =====================================================
// 2D MOTION GRAPHICS & KINETIC TYPOGRAPHY COMPOSITOR
// =====================================================
class CinemaCompositor {
  constructor(canvas, width, height, aspect) {
    this.canvas = canvas;
    this.w = width;
    this.h = height;
    this.aspect = aspect;
    this.isVert = aspect === "9:16";
    this.canvas.width = width;
    this.canvas.height = height;
    this.ctx = canvas.getContext("2d", { alpha: false });
    this.logoImg = null;
    this.igImg = null;
  }

  async loadAssets() {
    const [logo, ig] = await Promise.all([
      loadImageSafe("/static/assets/zentira-wall.png"),
      loadImageSafe("/static/assets/instagram.jpg"),
    ]);
    this.logoImg = logo;
    this.igImg = ig;
    if (document.fonts && document.fonts.ready) {
      await document.fonts.ready.catch(() => {});
    }
  }

  drawFrame(webglCanvas, t, scenes) {
    const ctx = this.ctx;
    const w = this.w;
    const h = this.h;
    const s = Math.min(w, h) / 1080; // scale factor relative to 1080p

    // 1. Base 3D WebGL Frame
    ctx.globalAlpha = 1;
    ctx.drawImage(webglCanvas, 0, 0, w, h);

    // 2. Subtle Atmospheric Cinema Vignette + Editorial Bottom Gradient Scrim
    const vig = ctx.createRadialGradient(w * 0.5, h * 0.48, w * 0.25, w * 0.5, h * 0.5, Math.max(w, h) * 0.78);
    vig.addColorStop(0, "rgba(0,0,0,0)");
    vig.addColorStop(1, "rgba(6,7,12,0.34)");
    ctx.fillStyle = vig;
    ctx.fillRect(0, 0, w, h);

    const botScrim = ctx.createLinearGradient(0, h * 0.62, 0, h);
    botScrim.addColorStop(0, "rgba(8,8,12,0)");
    botScrim.addColorStop(1, "rgba(8,8,12,0.58)");
    ctx.fillStyle = botScrim;
    ctx.fillRect(0, h * 0.62, w, h * 0.38);

    // 3. Cinema Letterbox Bars (sleek 5.2% matte on 16:9; ultra-clean full-bleed on 9:16!)
    const barMax = this.isVert ? 0 : Math.round(h * 0.052);
    if (barMax > 0) {
      const barH = Math.round(barMax * easeOutExpo(t / 0.9));
      ctx.fillStyle = "#08080b";
      ctx.fillRect(0, 0, w, barH);
      ctx.fillRect(0, h - barH, w, barH);
    }

    // 4. Subtle Persistent Corner Brand Bug (top-right during middle scenes, hides on Outro)
    this._drawBrandBug(ctx, t, w, h, s, barMax);

    // 5. Scene-Specific After Effects Kinetic Typography & Motion Graphics
    this._drawScene1Intro(ctx, t, w, h, s, barMax);
    this._drawScene2CounterCard(ctx, t, w, h, s, barMax);
    this._drawScene3HudCallout(ctx, t, w, h, s, barMax);
    this._drawScene4FounderStrip(ctx, t, w, h, s, barMax);
    this._drawScene5CapabilityStagger(ctx, t, w, h, s, barMax);
    this._drawScene6OutroEndCard(ctx, t, w, h, s, barMax);

    // 6. Silk Cinema Cross-Scene Dip Transitions + Opening Fade-In & Closing Fade-Out
    this._drawTransitions(ctx, t, w, h, scenes);
  }

  _drawBrandBug(ctx, t, w, h, s, barMax) {
    const win = animWindow(t, 5.8, 31.2, 0.6, 0.4);
    if (!win.active) return;
    const padX = Math.round((this.isVert ? 54 : 64) * s);
    const padY = barMax + Math.round((this.isVert ? 66 : 36) * s);
    ctx.save();
    ctx.globalAlpha = win.alpha * 0.85;
    const pillW = Math.round(218 * s);
    const pillH = Math.round(44 * s);
    const px = w - padX - pillW;
    roundRectPath(ctx, px, padY, pillW, pillH, 999);
    ctx.fillStyle = "rgba(12,12,16,0.62)";
    ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,0.16)";
    ctx.lineWidth = Math.max(1, 1.5 * s);
    ctx.stroke();

    // Live rose pulse dot
    ctx.beginPath();
    ctx.arc(px + 22 * s, padY + pillH / 2, 5 * s, 0, Math.PI * 2);
    ctx.fillStyle = "#f43f5e";
    ctx.fill();

    ctx.fillStyle = "#fafafa";
    ctx.font = `700 ${Math.round(17 * s)}px Inter, Segoe UI, sans-serif`;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText("ZENTIRA TEAM", px + 38 * s, padY + pillH / 2 + 1);
    ctx.restore();
  }

  _drawScene1Intro(ctx, t, w, h, s, barMax) {
    const win = animWindow(t, 0.55, 5.75, 0.78, 0.4);
    if (!win.active) return;

    const padX = Math.round((this.isVert ? 64 : 88) * s);
    const baseY = this.isVert ? h * 0.78 : h - barMax - Math.round(92 * s);

    // Animated champagne-gold eyebrow rule + label
    const ruleW = Math.round(52 * s * win.enter);
    ctx.save();
    ctx.globalAlpha = win.alpha;
    ctx.fillStyle = "#e6c767";
    ctx.fillRect(padX, baseY - Math.round(172 * s), ruleW, Math.max(2, Math.round(3 * s)));
    ctx.font = `700 ${Math.round(20 * s)}px Inter, Segoe UI, sans-serif`;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(
      "ZENTIRA VIRTUAL STUDIO",
      padX + ruleW + Math.round(14 * s),
      baseY - Math.round(170 * s)
    );
    ctx.restore();

    // Two-line Masked Kinetic Headline (staggered 120ms)
    const w1 = animWindow(t, 0.65, 5.75, 0.72, 0.36);
    const w2 = animWindow(t, 0.78, 5.75, 0.72, 0.36);
    const headSize = Math.round((this.isVert ? 74 : 82) * s);
    const headFont = `800 ${headSize}px Inter, Segoe UI, sans-serif`;
    drawMaskedLine(ctx, "MEET YOUR", padX, baseY - Math.round(78 * s), headFont, "#ffffff", w1.enter, w1.exit, "left", headSize * 1.15);
    drawMaskedLine(ctx, "AI WORKFORCE.", padX, baseY, headFont, "#f8fafc", w2.enter, w2.exit, "left", headSize * 1.15);

    // Subtitle reveal
    const w3 = animWindow(t, 0.96, 5.65, 0.65, 0.34);
    const subSize = Math.round((this.isVert ? 24 : 25) * s);
    drawMaskedLine(
      ctx,
      "6 Karyawan AI Otonom dalam Satu Kantor Virtual 3D",
      padX,
      baseY + Math.round(44 * s),
      `500 ${subSize}px Inter, Segoe UI, sans-serif`,
      "rgba(244,244,245,0.88)",
      w3.enter,
      w3.exit,
      "left",
      subSize * 1.4
    );
  }

  _drawScene2CounterCard(ctx, t, w, h, s, barMax) {
    const win = animWindow(t, 6.75, 12.45, 0.68, 0.36);
    if (!win.active) return;

    const cardW = Math.round((this.isVert ? w - 120 * s : 560 * s));
    const cardH = Math.round(148 * s);
    const x = Math.round((this.isVert ? 60 * s : 84 * s));
    const slideY = (1 - win.enter) * 34 * s + win.exit * 28 * s;
    const y = Math.round((this.isVert ? h * 0.79 : h - barMax - cardH - 58 * s) + slideY);

    ctx.save();
    ctx.globalAlpha = win.alpha;

    // Frosted obsidian Apple Keynote glass card
    roundRectPath(ctx, x, y, cardW, cardH, Math.round(22 * s));
    ctx.fillStyle = "rgba(12, 12, 16, 0.78)";
    ctx.fill();
    ctx.strokeStyle = "rgba(255, 255, 255, 0.16)";
    ctx.lineWidth = Math.max(1, 1.5 * s);
    ctx.stroke();

    // Animated top champagne-rose gradient accent bar
    const barProgress = easeOutExpo((t - 6.85) / 1.1);
    const barGrad = ctx.createLinearGradient(x, y, x + cardW, y);
    barGrad.addColorStop(0, "#ec4899");
    barGrad.addColorStop(0.55, "#e6c767");
    barGrad.addColorStop(1, "#38bdf8");
    ctx.fillStyle = barGrad;
    roundRectPath(ctx, x + 22 * s, y + 14 * s, (cardW - 44 * s) * barProgress, Math.max(3, 4 * s), 99);
    ctx.fill();

    // Animated kinetic counter 01 -> 06
    const countVal = Math.max(1, Math.min(6, Math.round(1 + 5 * easeOutQuint((t - 6.9) / 1.4))));
    const numStr = `0${countVal}`;
    ctx.fillStyle = "#ffffff";
    ctx.font = `800 ${Math.round(68 * s)}px Inter, Segoe UI, sans-serif`;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(numStr, x + 26 * s, y + cardH * 0.58);

    // Right copy
    const tx = x + Math.round(138 * s);
    ctx.fillStyle = "#e6c767";
    ctx.font = `700 ${Math.round(17 * s)}px Inter, Segoe UI, sans-serif`;
    ctx.fillText("AUTONOMOUS AI AGENTS", tx, y + cardH * 0.44);

    ctx.fillStyle = "rgba(244, 244, 245, 0.86)";
    ctx.font = `500 ${Math.round(21 * s)}px Inter, Segoe UI, sans-serif`;
    ctx.fillText("Hadir otomatis • Siap eksekusi 24/7", tx, y + cardH * 0.71);
    ctx.restore();
  }

  _drawScene3HudCallout(ctx, t, w, h, s, barMax) {
    const win = animWindow(t, 13.5, 18.0, 0.65, 0.34);
    if (!win.active) return;

    const x = Math.round((this.isVert ? 60 * s : 84 * s));
    const y = Math.round((this.isVert ? h * 0.80 : h - barMax - 122 * s));
    const lineLen = Math.round((this.isVert ? w - 160 * s : 480 * s) * win.enter);

    ctx.save();
    ctx.globalAlpha = win.alpha;

    // Pulsing crimson accent node + expanding Swiss hairline
    const pulse = 1 + Math.sin(t * 7) * 0.2;
    ctx.beginPath();
    ctx.arc(x + 8 * s, y, 12 * s * pulse, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(244, 63, 94, 0.28)";
    ctx.fill();
    ctx.beginPath();
    ctx.arc(x + 8 * s, y, 5.5 * s, 0, Math.PI * 2);
    ctx.fillStyle = "#f43f5e";
    ctx.fill();

    ctx.fillStyle = "rgba(255,255,255,0.75)";
    ctx.fillRect(x + 24 * s, y - 1 * s, lineLen, Math.max(1.5, 2 * s));
    ctx.restore();

    drawMaskedLine(
      ctx,
      "SINGLE-DOOR AI ORCHESTRATOR",
      x + 24 * s,
      y - 16 * s,
      `700 ${Math.round(20 * s)}px Inter, Segoe UI, sans-serif`,
      "#f43f5e",
      win.enter,
      win.exit,
      "left",
      32 * s
    );
    drawMaskedLine(
      ctx,
      "1 Perintah Bos → Delegasi Otomatis ke Tim",
      x + 24 * s,
      y + 40 * s,
      `700 ${Math.round((this.isVert ? 30 : 36) * s)}px Inter, Segoe UI, sans-serif`,
      "#ffffff",
      win.enter,
      win.exit,
      "left",
      46 * s
    );
  }

  _drawScene4FounderStrip(ctx, t, w, h, s, barMax) {
    const win = animWindow(t, 19.1, 23.45, 0.72, 0.35);
    if (!win.active) return;

    const cx = w / 2;
    const baseY = Math.round((this.isVert ? h * 0.82 : h - barMax - 82 * s));
    const ruleW = Math.round((this.isVert ? 360 : 520) * s * win.enter);

    ctx.save();
    ctx.globalAlpha = win.alpha;
    const grad = ctx.createLinearGradient(cx - ruleW / 2, baseY, cx + ruleW / 2, baseY);
    grad.addColorStop(0, "rgba(212,175,55,0)");
    grad.addColorStop(0.5, "#e6c767");
    grad.addColorStop(1, "rgba(212,175,55,0)");
    ctx.fillStyle = grad;
    ctx.fillRect(cx - ruleW / 2, baseY - 22 * s, ruleW, Math.max(2, 2.5 * s));
    ctx.restore();

    drawMaskedLine(
      ctx,
      "ARCHITECTED BY RADEN SATRIA JAYA WINATA",
      cx,
      baseY - 36 * s,
      `700 ${Math.round((this.isVert ? 22 : 24) * s)}px Inter, Segoe UI, sans-serif`,
      "#e6c767",
      win.enter,
      win.exit,
      "center",
      34 * s
    );
    drawMaskedLine(
      ctx,
      "Custom Multi-Agent AI System  •  Realtime 3D Control",
      cx,
      baseY + 24 * s,
      `600 ${Math.round((this.isVert ? 24 : 28) * s)}px Inter, Segoe UI, sans-serif`,
      "#ffffff",
      win.enter,
      win.exit,
      "center",
      38 * s
    );
  }

  _drawScene5CapabilityStagger(ctx, t, w, h, s, barMax) {
    const win = animWindow(t, 24.5, 29.7, 0.65, 0.36);
    if (!win.active) return;

    const cx = w / 2;
    const headY = Math.round((this.isVert ? h * 0.72 : h - barMax - 148 * s));
    drawMaskedLine(
      ctx,
      "ALL-IN-ONE AUTONOMOUS DIVISION",
      cx,
      headY,
      `800 ${Math.round((this.isVert ? 30 : 34) * s)}px Inter, Segoe UI, sans-serif`,
      "#ffffff",
      win.enter,
      win.exit,
      "center",
      44 * s
    );

    const badges = [
      { label: "Riset Tren", color: "#38bdf8" },
      { label: "Repurposer 3 Platform", color: "#f472b6" },
      { label: "Lead Hunter UMKM", color: "#34d399" },
      { label: "Admin Keuangan", color: "#fbbf24" },
      { label: "CS & QC Brief", color: "#a78bfa" },
    ];

    const fontPx = Math.round((this.isVert ? 21 : 20) * s);
    ctx.font = `600 ${fontPx}px Inter, Segoe UI, sans-serif`;
    const padX = Math.round(22 * s);
    const pillH = Math.round(46 * s);
    const gap = Math.round(12 * s);

    // Measure pills & lay out into 1 row on 16:9 or 2 crisp centered rows on 9:16
    const measured = badges.map((b) => ({
      ...b,
      pw: Math.round(ctx.measureText(b.label).width + padX * 2 + 18 * s),
    }));
    const rows = this.isVert
      ? [measured.slice(0, 2), measured.slice(2, 4), measured.slice(4)]
      : [measured];

    let globalIdx = 0;
    rows.forEach((row, rowIdx) => {
      const totalRowW = row.reduce((acc, b) => acc + b.pw, 0) + gap * (row.length - 1);
      let cursorX = cx - totalRowW / 2;
      const rowY = headY + Math.round((26 + rowIdx * 58) * s);

      for (const item of row) {
        const delay = globalIdx * 0.11;
        globalIdx += 1;
        const pEnter = easeOutBack((t - (24.7 + delay)) / 0.45);
        const pExit = win.exit;
        const pAlpha = clamp01((t - (24.7 + delay)) / 0.25) * (1 - pExit);
        if (pAlpha > 0.01) {
          const offsetY = (1 - pEnter) * 20 * s + pExit * 18 * s;
          ctx.save();
          ctx.globalAlpha = pAlpha;
          roundRectPath(ctx, cursorX, rowY + offsetY, item.pw, pillH, 999);
          ctx.fillStyle = "rgba(12, 12, 16, 0.78)";
          ctx.fill();
          ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
          ctx.lineWidth = Math.max(1, 1.5 * s);
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(cursorX + 19 * s, rowY + offsetY + pillH / 2, 5.5 * s, 0, Math.PI * 2);
          ctx.fillStyle = item.color;
          ctx.fill();

          ctx.fillStyle = "#fafafa";
          ctx.font = `600 ${fontPx}px Inter, Segoe UI, sans-serif`;
          ctx.textAlign = "left";
          ctx.textBaseline = "middle";
          ctx.fillText(item.label, cursorX + 34 * s, rowY + offsetY + pillH / 2 + 1);
          ctx.restore();
        }
        cursorX += item.pw + gap;
      }
    });
  }

  _drawScene6OutroEndCard(ctx, t, w, h, s, barMax) {
    if (t < 31.3) return;
    const veilAlpha = easeOutExpo((t - 31.3) / 1.2) * 0.64;
    ctx.save();
    ctx.fillStyle = `rgba(9, 9, 13, ${veilAlpha.toFixed(3)})`;
    ctx.fillRect(0, 0, w, h);
    ctx.restore();

    const win = animWindow(t, 31.65, CINEMA_DURATION + 1, 0.85, 0.01);
    if (!win.active) return;

    const cx = w / 2;
    const cy = h * 0.48;

    // 1. Split-Z Logo Scale-In with Soft Subtle Glow
    const logoSize = Math.round((this.isVert ? 136 : 124) * s);
    const logoScale = 0.82 + 0.18 * win.enter;
    ctx.save();
    ctx.globalAlpha = win.alpha;
    ctx.translate(cx, cy - Math.round(115 * s));
    ctx.scale(logoScale, logoScale);
    if (this.logoImg) {
      ctx.globalCompositeOperation = "lighten";
      ctx.drawImage(this.logoImg, -logoSize / 2, -logoSize / 2, logoSize, logoSize);
    }
    ctx.restore();

    // 2. Masked Hero Wordmark: ZENTIRA TEAM
    const wTitle = animWindow(t, 31.85, CINEMA_DURATION + 1, 0.72, 0.01);
    const titleSize = Math.round((this.isVert ? 74 : 84) * s);
    drawMaskedLine(
      ctx,
      "ZENTIRA TEAM",
      cx,
      cy + Math.round(28 * s),
      `800 ${titleSize}px Inter, Segoe UI, sans-serif`,
      "#ffffff",
      wTitle.enter,
      0,
      "center",
      titleSize * 1.18
    );

    // 3. Expanding Champagne-Gold Center Divider
    const divEnter = easeOutExpo((t - 32.15) / 0.7);
    const divW = Math.round((this.isVert ? 340 : 440) * s * divEnter);
    ctx.save();
    ctx.globalAlpha = win.alpha;
    const grad = ctx.createLinearGradient(cx - divW / 2, cy, cx + divW / 2, cy);
    grad.addColorStop(0, "rgba(230,199,103,0)");
    grad.addColorStop(0.5, "#e6c767");
    grad.addColorStop(1, "rgba(230,199,103,0)");
    ctx.fillStyle = grad;
    ctx.fillRect(cx - divW / 2, cy + Math.round(56 * s), divW, Math.max(2, 3 * s));
    ctx.restore();

    // 4. Client Pitch Tagline
    const wSub = animWindow(t, 32.25, CINEMA_DURATION + 1, 0.68, 0.01);
    const subSize = Math.round((this.isVert ? 27 : 28) * s);
    drawMaskedLine(
      ctx,
      "Custom Multi-Agent AI untuk Bisnis & Konten Anda",
      cx,
      cy + Math.round(106 * s),
      `500 ${subSize}px Inter, Segoe UI, sans-serif`,
      "rgba(244,244,245,0.9)",
      wSub.enter,
      0,
      "center",
      subSize * 1.4
    );

    // 5. Sleek @quietdenn Instagram Badge Pill
    const wIg = animWindow(t, 32.55, CINEMA_DURATION + 1, 0.65, 0.01);
    if (wIg.active) {
      const pillW = Math.round(256 * s);
      const pillH = Math.round(56 * s);
      const px = cx - pillW / 2;
      const py = cy + Math.round(142 * s) + (1 - wIg.enter) * 18 * s;

      ctx.save();
      ctx.globalAlpha = wIg.alpha;
      roundRectPath(ctx, px, py, pillW, pillH, 999);
      ctx.fillStyle = "rgba(255, 255, 255, 0.12)";
      ctx.fill();
      ctx.strokeStyle = "rgba(255, 255, 255, 0.24)";
      ctx.lineWidth = Math.max(1, 1.5 * s);
      ctx.stroke();

      const ico = Math.round(32 * s);
      const ix = px + Math.round(16 * s);
      const iy = py + Math.round((pillH - ico) / 2);
      if (this.igImg) {
        ctx.save();
        roundRectPath(ctx, ix, iy, ico, ico, Math.round(9 * s));
        ctx.clip();
        ctx.drawImage(this.igImg, ix, iy, ico, ico);
        ctx.restore();
      }
      ctx.fillStyle = "#ffffff";
      ctx.font = `700 ${Math.round(24 * s)}px Inter, Segoe UI, sans-serif`;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText("@quietdenn", ix + ico + Math.round(14 * s), py + pillH / 2 + 1);
      ctx.restore();
    }
  }

  _drawTransitions(ctx, t, w, h, scenes) {
    let darkAlpha = 0;

    // Opening fade-in (0.0s -> 0.75s)
    if (t < 0.75) {
      darkAlpha = Math.max(darkAlpha, 1 - easeOutQuint(t / 0.75));
    }

    // Silk obsidian cinema cross-dip across scene cuts
    for (let i = 1; i < scenes.length; i++) {
      const cut = scenes[i].start;
      const dist = Math.abs(t - cut);
      if (dist < 0.24) {
        const dip = Math.cos((dist / 0.24) * (Math.PI / 2));
        darkAlpha = Math.max(darkAlpha, dip * 0.88);
      }
    }

    // Closing cinema fade to obsidian (last 0.55s)
    if (t > CINEMA_DURATION - 0.55) {
      darkAlpha = Math.max(darkAlpha, easeInQuint((t - (CINEMA_DURATION - 0.55)) / 0.55));
    }

    if (darkAlpha > 0.005) {
      ctx.save();
      ctx.fillStyle = `rgba(8, 8, 12, ${clamp01(darkAlpha).toFixed(3)})`;
      ctx.fillRect(0, 0, w, h);
      ctx.restore();
    }
  }
}

// =====================================================
// ZENTIRA CINEMA DIRECTOR & DETERMINISTIC MP4 RENDERER
// =====================================================
export class ZentiraCinemaEngine {
  constructor(office3d, cinemaCanvas) {
    this.office3d = office3d;
    this.cinemaCanvas = cinemaCanvas;
    this.active = false;
    this.cancelled = false;
    this.rafId = null;
    this.savedState = null;
    this._onFinish = null;
    this.scenes = buildCinemaScenes();
  }

  _resolveResolution(aspect) {
    const isVert = aspect === "9:16";
    const isMobile = this.office3d.isMobile;
    return {
      width: isVert ? (isMobile ? 720 : 1080) : (isMobile ? 1280 : 1920),
      height: isVert ? (isMobile ? 1280 : 1920) : (isMobile ? 720 : 1080),
      baseFov: isVert ? 48 : 37,
    };
  }

  _applyCameraAt(t, baseFov, stateRef) {
    let idx = this.scenes.findIndex((s) => t >= s.start && t < s.end);
    if (idx === -1) idx = this.scenes.length - 1;
    const sc = this.scenes[idx];
    const localT = clamp01((t - sc.start) / Math.max(0.01, sc.end - sc.start));
    const u = cinemaTravel(localT);

    if (idx !== stateRef.lastSceneIdx) {
      stateRef.lastSceneIdx = idx;
      if (sc.theme && sc.theme !== this.office3d.currentTheme) {
        this.office3d.setTheme(sc.theme);
      }
      if (sc.roof) {
        this.office3d.setRoofMode(sc.roof);
      }
    }

    // Trigger Zentira Shuttle Van arrival cleanly at t = 2.8s so it parks right at Scene 2 start!
    if (!stateRef.shuttleTriggered && t >= 2.8) {
      stateRef.shuttleTriggered = true;
      this.office3d.triggerCinemaShuttleArrival();
    }

    const pos = sc.posCurve.getPoint(u);
    const target = sc.targetCurve.getPoint(u);

    // Subtle stabilized gimbal vertical float for organic cinema feel
    const breathY = Math.sin(t * 1.15) * 0.065;
    this.office3d.camera.position.set(pos.x, pos.y + breathY, pos.z);
    this.office3d.controls.target.copy(target);
    this.office3d.camera.lookAt(target);

    const fovDelta = THREE.MathUtils.lerp(sc.fovShift[0], sc.fovShift[1], u);
    const nextFov = baseFov + fovDelta;
    if (Math.abs(this.office3d.camera.fov - nextFov) > 0.01) {
      this.office3d.camera.fov = nextFov;
      this.office3d.camera.updateProjectionMatrix();
    }

    return sc;
  }

  async startPreview({ aspect = "16:9", onProgress = null, onFinish = null } = {}) {
    if (this.active) this.stop();
    this.active = true;
    this.cancelled = false;
    this._onFinish = onFinish;

    const { width, height, baseFov } = this._resolveResolution(aspect);
    const comp = new CinemaCompositor(this.cinemaCanvas, width, height, aspect);
    await comp.loadAssets();
    if (this.cancelled) {
      this._finish(true);
      return;
    }

    this.savedState = this.office3d.enterCinemaMode({ width, height, fov: baseFov });
    const runRef = { lastSceneIdx: -1, shuttleTriggered: false };
    let elapsed = 0;
    let lastTs = performance.now();

    const loop = (now) => {
      if (!this.active || this.cancelled) return;
      const dt = Math.min((now - lastTs) / 1000, 0.05);
      lastTs = now;
      elapsed += dt;

      if (elapsed >= CINEMA_DURATION) {
        this._finish(false);
        return;
      }

      const sc = this._applyCameraAt(elapsed, baseFov, runRef);
      this.office3d.stepSimulation(dt);
      this.office3d.renderFrame();
      comp.drawFrame(this.office3d.canvas, elapsed, this.scenes);

      if (onProgress) {
        onProgress({
          mode: "preview",
          elapsed,
          total: CINEMA_DURATION,
          percent: Math.round((elapsed / CINEMA_DURATION) * 100),
          label: sc.label,
        });
      }
      this.rafId = requestAnimationFrame(loop);
    };

    this.rafId = requestAnimationFrame(loop);
  }

  async _probeH264Config(width, height, fps) {
    if (typeof window.VideoEncoder === "undefined") return null;
    const codecs = [
      "avc1.640032", // High L5.0 (1080p60)
      "avc1.4d0032", // Main L5.0
      "avc1.420032", // Baseline L5.0
      "avc1.64002a", // High L4.2 (1080p60)
      "avc1.4d002a", // Main L4.2
      "avc1.640028", // High L4.0
    ];
    for (const hw of ["prefer-hardware", "no-preference"]) {
      for (const codec of codecs) {
        const cfg = {
          codec,
          width,
          height,
          bitrate: width >= 1920 || height >= 1920 ? 12_000_000 : 7_500_000,
          framerate: fps,
          hardwareAcceleration: hw,
          avc: { format: "avc" },
        };
        try {
          const res = await VideoEncoder.isConfigSupported(cfg);
          if (res && res.supported) return cfg;
        } catch {
          /* try next codec */
        }
      }
    }
    return null;
  }

  async startOfflineMP4Render({ aspect = "16:9", onProgress = null, onFinish = null } = {}) {
    if (this.active) this.stop();
    this.active = true;
    this.cancelled = false;
    this._onFinish = onFinish;

    const { width, height, baseFov } = this._resolveResolution(aspect);
    const comp = new CinemaCompositor(this.cinemaCanvas, width, height, aspect);
    await comp.loadAssets();
    if (this.cancelled) {
      this._finish(true);
      return;
    }

    const fps = EXPORT_FPS;
    const encoderCfg = await this._probeH264Config(width, height, fps);

    // Fallback to live MediaRecorder on compositor canvas if WebCodecs H.264 is unavailable
    if (!encoderCfg) {
      return this._runMediaRecorderFallback({ aspect, width, height, baseFov, comp, onProgress });
    }

    let MuxerCls = null;
    let TargetCls = null;
    try {
      const mod = await import(MP4_MUXER_URL);
      MuxerCls = mod.Muxer;
      TargetCls = mod.ArrayBufferTarget;
    } catch {
      return this._runMediaRecorderFallback({ aspect, width, height, baseFov, comp, onProgress });
    }

    if (this.cancelled) {
      this._finish(true);
      return;
    }

    this.savedState = this.office3d.enterCinemaMode({ width, height, fov: baseFov });
    const runRef = { lastSceneIdx: -1, shuttleTriggered: false };

    const target = new TargetCls();
    const muxer = new MuxerCls({
      target,
      video: { codec: "avc", width, height },
      fastStart: "in-memory",
      firstTimestampBehavior: "offset",
    });

    let encodeErr = null;
    const encoder = new VideoEncoder({
      output: (chunk, meta) => muxer.addVideoChunk(chunk, meta),
      error: (err) => {
        encodeErr = err;
      },
    });
    encoder.configure(encoderCfg);

    const totalFrames = Math.round(CINEMA_DURATION * fps);
    const dt = 1 / fps;
    const frameDurUs = Math.round(1_000_000 / fps);

    try {
      for (let f = 0; f < totalFrames; f++) {
        if (!this.active || this.cancelled || encodeErr) break;

        const t = f * dt;
        const sc = this._applyCameraAt(t, baseFov, runRef);
        this.office3d.stepSimulation(dt);
        this.office3d.renderFrame();
        comp.drawFrame(this.office3d.canvas, t, this.scenes);

        const vf = new VideoFrame(this.cinemaCanvas, {
          timestamp: Math.round(f * frameDurUs),
          duration: frameDurUs,
        });
        encoder.encode(vf, { keyFrame: f % (fps * 2) === 0 });
        vf.close();

        // Respect hardware/software encoder queue backpressure & keep browser responsive
        while (encoder.encodeQueueSize > 8 && !this.cancelled && !encodeErr) {
          await new Promise((r) => setTimeout(r, 4));
        }

        if (f % 3 === 0 || f === totalFrames - 1) {
          if (onProgress) {
            onProgress({
              mode: "render",
              elapsed: t,
              total: CINEMA_DURATION,
              percent: Math.round(((f + 1) / totalFrames) * 100),
              label: sc.label,
            });
          }
          await new Promise((r) => setTimeout(r, 0));
        }
      }

      if (encodeErr) throw encodeErr;

      if (!this.cancelled) {
        if (onProgress) {
          onProgress({
            mode: "render",
            elapsed: CINEMA_DURATION,
            total: CINEMA_DURATION,
            percent: 100,
            label: "Menyusun file MP4 60fps...",
          });
        }
        await encoder.flush();
        encoder.close();
        muxer.finalize();

        const blob = new Blob([target.buffer], { type: "video/mp4" });
        const filename = this._downloadBlob(blob, aspect, "mp4");
        this._finish(false, { filename, format: "MP4 60fps" });
      } else {
        try {
          encoder.close();
        } catch {
          /* ignore */
        }
        this._finish(true);
      }
    } catch (err) {
      try {
        encoder.close();
      } catch {
        /* ignore */
      }
      this._finish(true, { error: err?.message || String(err) });
    }
  }

  async _runMediaRecorderFallback({ aspect, width, height, baseFov, comp, onProgress }) {
    if (typeof this.cinemaCanvas.captureStream !== "function" || typeof window.MediaRecorder === "undefined") {
      this._finish(true, {
        error: "Browser ini tidak mendukung perekaman video langsung.",
      });
      return;
    }

    this.savedState = this.office3d.enterCinemaMode({ width, height, fov: baseFov });
    const runRef = { lastSceneIdx: -1, shuttleTriggered: false };
    const stream = this.cinemaCanvas.captureStream(30);
    const mimes = ["video/mp4", "video/webm;codecs=h264", "video/webm;codecs=vp8", "video/webm"];
    const mimeType = mimes.find((m) => MediaRecorder.isTypeSupported(m)) || "";
    const chunks = [];
    const rec = new MediaRecorder(stream, {
      ...(mimeType ? { mimeType } : {}),
      videoBitsPerSecond: 8_000_000,
    });
    rec.ondataavailable = (ev) => {
      if (ev.data && ev.data.size > 0) chunks.push(ev.data);
    };
    rec.onstop = () => {
      stream.getTracks().forEach((tr) => tr.stop());
      if (!this.cancelled && chunks.length > 0) {
        const ext = mimeType.includes("mp4") ? "mp4" : "webm";
        const filename = this._downloadBlob(new Blob(chunks, { type: mimeType || "video/webm" }), aspect, ext);
        this._finish(false, { filename, format: ext.toUpperCase() });
      } else {
        this._finish(true);
      }
    };
    rec.start(250);

    let elapsed = 0;
    let lastTs = performance.now();
    const loop = (now) => {
      if (!this.active || this.cancelled) {
        if (rec.state !== "inactive") rec.stop();
        return;
      }
      const dt = Math.min((now - lastTs) / 1000, 0.05);
      lastTs = now;
      elapsed += dt;
      if (elapsed >= CINEMA_DURATION) {
        if (rec.state !== "inactive") rec.stop();
        return;
      }
      const sc = this._applyCameraAt(elapsed, baseFov, runRef);
      this.office3d.stepSimulation(dt);
      this.office3d.renderFrame();
      comp.drawFrame(this.office3d.canvas, elapsed, this.scenes);
      if (onProgress) {
        onProgress({
          mode: "render",
          elapsed,
          total: CINEMA_DURATION,
          percent: Math.round((elapsed / CINEMA_DURATION) * 100),
          label: sc.label,
        });
      }
      this.rafId = requestAnimationFrame(loop);
    };
    this.rafId = requestAnimationFrame(loop);
  }

  _downloadBlob(blob, aspect, ext) {
    const url = URL.createObjectURL(blob);
    const stamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 12);
    const ratioTag = aspect === "9:16" ? "9x16" : "16x9";
    const filename = `zentira-hq-showreel-${ratioTag}-${stamp}.${ext}`;
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 6000);
    return filename;
  }

  _finish(cancelled, result = null) {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    const saved = this.savedState;
    const cb = this._onFinish;
    this.savedState = null;
    this._onFinish = null;
    this.active = false;
    if (saved) {
      this.office3d.exitCinemaMode(saved);
    }
    if (cb) cb(cancelled, result);
  }

  stop() {
    if (!this.active) return;
    this.cancelled = true;
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
      this._finish(true);
    }
  }
}
