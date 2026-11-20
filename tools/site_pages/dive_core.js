// The arithmetic of docs/pages/dive.html (DECISIONS.md section 109). Its inputs come from jerlov,
// embedded by tools/site_pages.py; this only multiplies and integrates, by the trapezoid rule.
// tests/test_site_pages.py runs it with node, where node is present.
const Core = (() => {
  function trap(y, x, lo = -Infinity, hi = Infinity) {
    let s = 0;
    for (let i = 1; i < x.length; i++) {
      if (x[i - 1] < lo || x[i] > hi) continue;
      s += 0.5 * (y[i] + y[i - 1]) * (x[i] - x[i - 1]);
    }
    return s;
  }
  function make(D) {
    const wl = D.wl, n = wl.length, M = D.xyz_to_srgb, W = D.srgb_white;
    const xyz = (s) => [0, 1, 2].map((k) => trap(s.map((v, i) => v * D.cmf[k][i]), wl));
    const whiteXYZ = xyz(D.es);
    const edAt = (type, z) => D.es.map((e, i) => e * Math.exp(-D.kd[type][i] * z));
    // Linear sRGB of a spectrum, with the surface sunlight as white (as jerlov.spectrum_to_srgb, before clipping).
    function linear(s) {
      const q = xyz(s).map((v, k) => (v / whiteXYZ[k]) * W[k]);
      return M.map((r) => r[0] * q[0] + r[1] * q[1] + r[2] * q[2]);
    }
    const gamma = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(Math.max(c, 0), 1 / 2.4) - 0.055);
    const encode = (lin) => lin.map((c) => gamma(Math.min(1, Math.max(0, c))));
    const Y = (s) => xyz(s)[1] / whiteXYZ[1];
    const photons = D.es.map((e, i) => e * wl[i]);
    const par0 = trap(photons, wl, 400, 700);
    const parFraction = (type, z) =>
      trap(photons.map((p, i) => p * Math.exp(-D.kd[type][i] * z)), wl, 400, 700) / par0;
    function depthOfParFraction(type, f) {
      let lo = 0, hi = 1;
      while (parFraction(type, hi) > f) { lo = hi; hi *= 2; if (hi > 4096) return NaN; }
      for (let k = 0; k < 60; k++) { const m = 0.5 * (lo + hi); (parFraction(type, m) > f ? (lo = m) : (hi = m)); }
      return 0.5 * (lo + hi);
    }
    // The colour of the light itself: hue at full brightness (largest channel = 1, negatives cut).
    function hue(lin) {
      const c = lin.map((v) => Math.max(0, v));
      const m = Math.max(...c);
      return m > 0 ? c.map((v) => v / m) : [0, 0, 0];
    }
    // An object lit from above at depth z, seen from close by; exposure set so the white PVC keeps its surface brightness.
    function objectLinear(material, type, z) {
      const ed = edAt(type, z);
      const exposure = Y(D.refl.white_pvc) / Y(D.refl.white_pvc.map((r, i) => r * ed[i]));
      return linear(D.refl[material].map((r, i) => r * ed[i])).map((c) => c * exposure);
    }
    return { wl, edAt, linear, encode, gamma, Y, parFraction, depthOfParFraction, hue, objectLinear };
  }
  return { make, trap };
})();
if (typeof module !== "undefined") module.exports = Core;
