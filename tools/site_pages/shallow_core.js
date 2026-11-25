// The model of docs/pages/shallow.html (DECISIONS.md section 121): Lee et al.'s (1999) shallow-water
// reflectance, straight down, as jerlov.lee1999_shallow_rrs evaluates it. The constants and the
// water's a and bb come from jerlov, embedded by tools/site_pages.py; this only evaluates the
// equations. tests/test_site_pages.py runs it with node, where node is present.
const Shallow = (() => {
  function make(D) {
    const M = D.model;
    // bb as Water.bb gives it with particle_backscatter_ratio = ratio, one of the page's choices.
    const bb = (type, ratio) => D.bb[type][String(ratio)];
    // rrs below the surface and its parts, and Rrs above it, at every wavelength of D.wl.
    function rrs(type, sun, ratio, depth, albedo) {
      const sinW = Math.sin((sun * Math.PI) / 180) / M.n;
      const down = 1 / Math.sqrt(1 - sinW * sinW);
      const b = bb(type, ratio);
      const out = { rrs: [], column: [], bottom: [], deep: [], above: [], aboveDeep: [], u: [] };
      D.a[type].forEach((a, i) => {
        // A gap in the source (null) stays a gap: NaN, drawn as nothing.
        const ai = a === null ? NaN : a, bi = b[i] === null ? NaN : b[i];
        const kappa = ai + bi, u = bi / kappa;
        const deep = (M.g[0] + M.g[1] * u) * u;
        const column = deep * (1 - Math.exp(-(down + M.dc[0] * Math.sqrt(1 + M.dc[1] * u)) * kappa * depth));
        const bottom = (albedo / Math.PI) * Math.exp(-(down + M.db[0] * Math.sqrt(1 + M.db[1] * u)) * kappa * depth);
        const r = column + bottom;
        out.rrs.push(r); out.column.push(column); out.bottom.push(bottom); out.deep.push(deep); out.u.push(u);
        out.above.push((M.zeta * r) / (1 - M.gamma * r));
        out.aboveDeep.push((M.zeta * deep) / (1 - M.gamma * deep));
      });
      return out;
    }
    return { rrs, bb };
  }
  return { make };
})();
if (typeof module !== "undefined") module.exports = Shallow;
