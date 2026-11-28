"""A vector Monte Carlo for a homogeneous Rayleigh layer, against Natraj,
Li and Yung's (2009) tables: DECISIONS.md section 145.

    V. Natraj, K.-F. Li and Y. L. Yung (2009), "Rayleigh scattering in
    planetary atmospheres: corrected tables through accurate computation of
    X and Y functions", Astrophys. J. 691, 1909-1920,
    doi:10.1088/0004-637X/691/2/1909.

Tables 1 to 6 (pp. 1912-1913), I, Q and U of the diffuse light leaving the
top (upwelling) and the bottom (downwelling) of a layer of optical
thickness 0.5 over a black surface, the sun at mu0 = 0.2, are transcribed
below from the text layer of the authors' PDF (born digital), and rows
of each were read against the page image.

Each photon carries a Stokes vector (I, Q, U, V), with Q = I1 - I2 and
U = I(+45) - I(-45) for a reference axis e1 normal to its direction d and
e2 = d x e1. It is scattered by Rayleigh's matrix: the angle drawn from
the phase function for unpolarised light, the scattering plane's normal
uniformly about d, the Stokes vector rotated into the scattering plane
(e1 = n x d, e2 = n) and multiplied by the matrix divided by its (1,1)
element, so that I carries the weight (Tynes et al. 2001, Appl. Opt. 40,
400, section 2). At each scattering the light it would send out of the
layer in every tabulated direction is added (a next-event estimate): the
phase matrix towards that direction, the attenuation to the boundary, over
the direction's cosine, rotated into the direction's meridian plane.

    python tools/polarised_mc.py OUT.csv
    python tools/polarised_mc.py --kokhanovsky OUT.csv

The CSV holds I, Q and U in the tables' conventions (TO_TABLES).

This is a tool for the comparison, not part of the package.
"""

from __future__ import annotations

import csv
import math
import sys

import numpy as np

TAU = 0.5
MU0 = 0.2
MUS = (0.02, 0.06, 0.10, 0.16, 0.20, 0.28, 0.32, 0.40, 0.52, 0.64, 0.72,
       0.84, 0.92, 0.96, 0.98, 1.00)
PHIS = (0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0)
PHOTONS, BATCHES, SEED = 400_000, 10, 2009
_WEIGHT_FLOOR = 1e-4


#: Natraj et al. (2009) Tables 1 to 6, pp. 1912-1913: (level, Stokes
#: parameter) -> rows of mu and the values at PHIS.
TABLES = {
    ('top', 'I'): (  # Table 1
        (0.02, (0.44129802, 0.39444956, 0.30091208, 0.25465866, 0.30253774, 0.39726529, 0.44454934)),
        (0.06, (0.39250948, 0.35223311, 0.27210130, 0.23339588, 0.27639321, 0.35966691, 0.40109329)),
        (0.10, (0.35082997, 0.31575536, 0.24622966, 0.21348201, 0.25258702, 0.32676664, 0.36354469)),
        (0.16, (0.29863696, 0.26973242, 0.21277028, 0.18702656, 0.22140580, 0.28468958, 0.31590800)),
        (0.20, (0.26939388, 0.24383765, 0.19368088, 0.17169133, 0.20342523, 0.26071536, 0.28888259)),
        (0.28, (0.22153000, 0.20137817, 0.16217962, 0.14615212, 0.17344750, 0.22089470, 0.24406575)),
        (0.32, (0.20185562, 0.18392101, 0.14920591, 0.13557847, 0.16097330, 0.20430272, 0.22539038)),
        (0.40, (0.16889020, 0.15469709, 0.12752450, 0.11786073, 0.13989890, 0.17613018, 0.19363900)),
        (0.52, (0.13097041, 0.12117362, 0.10280748, 0.09759154, 0.11532259, 0.14285044, 0.15600064)),
        (0.64, (0.10231626, 0.09595756, 0.08440503, 0.08239375, 0.09628240, 0.11652976, 0.12607100)),
        (0.72, (0.08683737, 0.08239718, 0.07459712, 0.07418876, 0.08561228, 0.10147599, 0.10886768)),
        (0.84, (0.06783499, 0.06583006, 0.06269131, 0.06393739, 0.07157324, 0.08121402, 0.08559886)),
        (0.92, (0.05781217, 0.05713933, 0.05643322, 0.05814731, 0.06295443, 0.06843439, 0.07085458)),
        (0.96, (0.05385796, 0.05372482, 0.05391877, 0.05550325, 0.05861141, 0.06185271, 0.06324324)),
        (0.98, (0.05240320, 0.05247332, 0.05294178, 0.05423678, 0.05628819, 0.05826948, 0.05909602)),
        (1.00, (0.05300496, 0.05300496, 0.05300496, 0.05300496, 0.05300496, 0.05300496, 0.05300496)),
    ),
    ('bottom', 'I'): (  # Table 2
        (0.02, (0.09703171, 0.08901596, 0.07295573, 0.06483276, 0.07266281, 0.08850861, 0.09644588)),
        (0.06, (0.11553675, 0.10592439, 0.08659640, 0.07659862, 0.08554343, 0.10410059, 0.11343081)),
        (0.10, (0.13485741, 0.12338692, 0.10024223, 0.08801144, 0.09816504, 0.11978912, 0.13070302)),
        (0.16, (0.15368433, 0.14027168, 0.11306987, 0.09825212, 0.10923106, 0.13362266, 0.14600671)),
        (0.20, (0.15838610, 0.14444914, 0.11608879, 0.10033646, 0.11112912, 0.13585873, 0.14846675)),
        (0.28, (0.15618358, 0.14242837, 0.11424823, 0.09799362, 0.10741978, 0.13060115, 0.14252669)),
        (0.32, (0.15191358, 0.13860786, 0.11125496, 0.09518205, 0.10369486, 0.12551338, 0.13679338)),
        (0.40, (0.14070011, 0.12863410, 0.10365367, 0.08842135, 0.09500316, 0.11365098, 0.12339910)),
        (0.52, (0.12178394, 0.11192848, 0.09128777, 0.07796226, 0.08180742, 0.09550803, 0.10282324)),
        (0.64, (0.10305234, 0.09550874, 0.07949285, 0.06848327, 0.07002363, 0.07910758, 0.08411390)),
        (0.72, (0.09102071, 0.08502244, 0.07214297, 0.06284951, 0.06314035, 0.06942945, 0.07301547)),
        (0.84, (0.07348081, 0.06981390, 0.06174753, 0.05534670, 0.05427833, 0.05687686, 0.05854240)),
        (0.92, (0.06170619, 0.05964952, 0.05499023, 0.05089607, 0.04942372, 0.05000805, 0.05057318)),
        (0.96, (0.05544795, 0.05425758, 0.05148138, 0.04881521, 0.04744944, 0.04727404, 0.04738406)),
        (0.98, (0.05198745, 0.05127723, 0.04957393, 0.04780805, 0.04668981, 0.04628180, 0.04621923)),
        (1.00, (0.04682203, 0.04682203, 0.04682203, 0.04682203, 0.04682203, 0.04682203, 0.04682203)),
    ),
    ('top', 'Q'): (  # Table 3
        (0.02, (-0.01753141, -0.06485313, -0.15965601, -0.20757277, -0.16128167, -0.06766886, -0.02078273)),
        (0.06, (-0.01772108, -0.05944266, -0.14330674, -0.18659926, -0.14759865, -0.06687645, -0.02630489)),
        (0.10, (-0.01524525, -0.05274909, -0.12838028, -0.16821107, -0.13473764, -0.06376036, -0.02795997)),
        (0.16, (-0.00990697, -0.04270497, -0.10914792, -0.14510675, -0.11778344, -0.05766213, -0.02717801)),
        (0.20, (-0.00608288, -0.03648858, -0.09825566, -0.13222805, -0.10800002, -0.05336629, -0.02557158)),
        (0.28, (0.00131430, -0.02554220, -0.08036031, -0.11134114, -0.09162819, -0.04505874, -0.02122145)),
        (0.32, (0.00477642, -0.02076298, -0.07299588, -0.10284244, -0.08476326, -0.04114469, -0.01875835)),
        (0.40, (0.01119511, -0.01235218, -0.06066038, -0.08873702, -0.07303478, -0.03378526, -0.01355369)),
        (0.52, (0.01968930, -0.00196538, -0.04650218, -0.07273772, -0.05901730, -0.02364220, -0.00534093)),
        (0.64, (0.02701775, 0.00644566, -0.03586341, -0.06078292, -0.04774078, -0.01412655, 0.00326301)),
        (0.72, (0.03129776, 0.01117009, -0.03016559, -0.05432509, -0.04118074, -0.00790872, 0.00926745)),
        (0.84, (0.03668441, 0.01698497, -0.02328501, -0.04623546, -0.03216694, 0.00160101, 0.01892054)),
        (0.92, (0.03923450, 0.01977043, -0.01979730, -0.04164830, -0.02631851, 0.00847536, 0.02619209)),
        (0.96, (0.03983604, 0.02053460, -0.01852852, -0.03954758, -0.02322116, 0.01240671, 0.03045076)),
        (0.98, (0.03969919, 0.02052770, -0.01814346, -0.03853982, -0.02148987, 0.01473155, 0.03300636)),
        (1.00, (0.03755859, 0.01877930, -0.01877930, -0.03755859, -0.01877930, 0.01877930, 0.03755859)),
    ),
    ('bottom', 'Q'): (  # Table 4
        (0.02, (-0.00920833, -0.01715198, -0.03301054, -0.04084698, -0.03271763, -0.01664463, -0.00862250)),
        (0.06, (-0.01266323, -0.02206189, -0.04075593, -0.04976917, -0.03970296, -0.02023809, -0.01055729)),
        (0.10, (-0.01538451, -0.02652451, -0.04860080, -0.05898050, -0.04652360, -0.02292670, -0.01123012)),
        (0.16, (-0.01746551, -0.03052730, -0.05627439, -0.06793108, -0.05243558, -0.02387828, -0.00978788)),
        (0.20, (-0.01767297, -0.03138703, -0.05832873, -0.07022742, -0.05336906, -0.02279663, -0.00775363)),
        (0.28, (-0.01625676, -0.03036695, -0.05791762, -0.06952842, -0.05108917, -0.01853974, -0.00259987)),
        (0.32, (-0.01495157, -0.02903636, -0.05646445, -0.06778205, -0.04890435, -0.01594187, 0.00016863)),
        (0.40, (-0.01160882, -0.02551200, -0.05246997, -0.06320685, -0.04381947, -0.01052889, 0.00569219)),
        (0.52, (-0.00542392, -0.01910281, -0.04553080, -0.05573965, -0.03605045, -0.00268237, 0.01353678)),
        (0.64, (0.00169861, -0.01201444, -0.03851183, -0.04875891, -0.02904261, 0.00438673, 0.02063705)),
        (0.72, (0.00689487, -0.00700779, -0.03393019, -0.04453766, -0.02492757, 0.00858520, 0.02490011)),
        (0.84, (0.01547851, 0.00103248, -0.02712704, -0.03883915, -0.01965783, 0.01396952, 0.03041692)),
        (0.92, (0.02204865, 0.00703628, -0.02244251, -0.03541740, -0.01687601, 0.01667775, 0.03318166)),
        (0.96, (0.02590733, 0.01051101, -0.01988620, -0.03380673, -0.01585426, 0.01749454, 0.03397123)),
        (0.98, (0.02821492, 0.01257041, -0.01843576, -0.03302461, -0.01555164, 0.01756584, 0.03398315)),
        (1.00, (0.03225729, 0.01612864, -0.01612864, -0.03225729, -0.01612864, 0.01612864, 0.03225729)),
    ),
    ('top', 'U'): (  # Table 5
        (0.02, (0, 0.04390364, 0.07365528, 0.08128298, 0.06713098, 0.03737934, 0)),
        (0.06, (0, 0.04428736, 0.07046980, 0.07153176, 0.05342685, 0.02724440, 0)),
        (0.10, (0, 0.04435776, 0.06762732, 0.06357361, 0.04248541, 0.01921585, 0)),
        (0.16, (0, 0.04408551, 0.06384064, 0.05397200, 0.02964161, 0.00988649, 0)),
        (0.20, (0, 0.04374666, 0.06158007, 0.04872177, 0.02280850, 0.00497510, 0)),
        (0.28, (0, 0.04291904, 0.05764878, 0.04024242, 0.01205313, -0.00267662, 0)),
        (0.32, (0, 0.04248227, 0.05594215, 0.03677307, 0.00775068, -0.00570920, 0)),
        (0.40, (0, 0.04161531, 0.05293867, 0.03093600, 0.00064404, -0.01067932, 0)),
        (0.52, (0, 0.04036105, 0.04917038, 0.02406753, -0.00748419, -0.01629352, 0)),
        (0.64, (0, 0.03913232, 0.04592516, 0.01855839, -0.01378109, -0.02057393, 0)),
        (0.72, (0, 0.03828742, 0.04388718, 0.01529883, -0.01738884, -0.02298860, 0)),
        (0.84, (0, 0.03686504, 0.04073530, 0.01057373, -0.02242105, -0.02629131, 0)),
        (0.92, (0, 0.03563204, 0.03822653, 0.00708827, -0.02594929, -0.02854377, 0)),
        (0.96, (0, 0.03475930, 0.03654849, 0.00488817, -0.02808194, -0.02987113, 0)),
        (0.98, (0, 0.03413018, 0.03538005, 0.00341471, -0.02946560, -0.03071547, 0)),
        (1.00, (0, 0.03252669, 0.03252669, 0, -0.03252669, -0.03252669, 0)),
    ),
    ('bottom', 'U'): (  # Table 6
        (0.02, (0, 0.00677002, 0.01213073, 0.01464574, 0.01323643, 0.00787572, 0)),
        (0.06, (0, 0.00679905, 0.01322260, 0.01754947, 0.01717397, 0.01075042, 0)),
        (0.10, (0, 0.00646972, 0.01407278, 0.02077195, 0.02190528, 0.01430222, 0)),
        (0.16, (0, 0.00465948, 0.01344137, 0.02399258, 0.02811500, 0.01933310, 0)),
        (0.20, (0, 0.00282059, 0.01189742, 0.02479837, 0.03105461, 0.02197778, 0)),
        (0.28, (0, -0.00132035, 0.00760602, 0.02438731, 0.03463403, 0.02570766, 0)),
        (0.32, (0, -0.00336870, 0.00527877, 0.02362532, 0.03564148, 0.02699402, 0)),
        (0.40, (0, -0.00717886, 0.00073690, 0.02162626, 0.03672088, 0.02880512, 0)),
        (0.52, (0, -0.01208088, -0.00540771, 0.01823144, 0.03698549, 0.03031232, 0)),
        (0.64, (0, -0.01616543, -0.01074985, 0.01479565, 0.03637667, 0.03096109, 0)),
        (0.72, (0, -0.01856617, -0.01398952, 0.01250364, 0.03564645, 0.03106981, 0)),
        (0.84, (0, -0.02190697, -0.01865230, 0.00889191, 0.03405355, 0.03079888, 0)),
        (0.92, (0, -0.02417402, -0.02195936, 0.00605055, 0.03243922, 0.03022456, 0)),
        (0.96, (0, -0.02547988, -0.02394259, 0.00419995, 0.03121711, 0.02967982, 0)),
        (0.98, (0, -0.02628920, -0.02521200, 0.00294297, 0.03030938, 0.02923217, 0)),
        (1.00, (0, -0.02793563, -0.02793563, 0, 0.02793563, 0.02793563, 0)),
    ),
}


#: Kokhanovsky et al. (2010), J. Quant. Spectrosc. Radiat. Transfer 111,
#: 1931-1946, doi:10.1016/j.jqsrt.2010.03.005: Rayleigh scattering without
#: depolarisation, optical thickness 0.3262, the sun at 60 degrees, a black
#: surface (DECISIONS.md section 146). Transcribed from the page images
#: (the text layer drops the minus signs).
K_TAU = 0.3262
K_MU0 = 0.5
K_VZA = (0.0, 20.0, 40.0, 60.0, 80.0, 89.0)
K_PHIS = (0.0, 90.0, 180.0)
#: Table A1 (p. 1943): VZA -> for phi 0, 90, 180: (IR, QR, IT, QT).
K_TABLE_A1 = {
    0.0: ((0.1433981, 0.07253129, 0.1396923, 0.07040628),
          (0.1433981, -0.07253129, 0.1396923, -0.07040628),
          (0.1433981, 0.07253129, 0.1396923, 0.07040628)),
    20.0: ((0.1281929, 0.09953042, 0.1846301, 0.03655640),
           (0.1501054, -0.07537969, 0.1460187, -0.07306526),
           (0.1899151, 0.03780822, 0.1247472, 0.09643928)),
    40.0: ((0.1560517, 0.1140612, 0.2590920, 0.001549839),
           (0.1746397, -0.08605730, 0.1689676, -0.08295291),
           (0.2682317, 0.001881170, 0.1509949, 0.1096469)),
    60.0: ((0.2641460, 0.1125426, 0.3811575, -0.02444004),
           (0.2379419, -0.1146228, 0.2265788, -0.1086739),
           (0.4017650, -0.02507640, 0.2511095, 0.1056079)),
    80.0: ((0.6078904, 0.08824163, 0.6138623, -0.01452666),
           (0.4301002, -0.2043280, 0.3769405, -0.1773986),
           (0.7084867, -0.01235467, 0.5277571, 0.07157849)),
    89.0: ((0.8581319, 0.06684238, 0.5599639, 0.02324266),
           (0.5458706, -0.2592859, 0.3617355, -0.1666421),
           (0.8718045, 0.05316980, 0.5515021, 0.03170448)),
}
#: Tables A4 and A5 (pp. 1944-1945), Rayleigh: U at phi = 90, VZA ->
#: (UR, UT).
K_TABLE_U90 = {0.0: (0.0, 0.0), 20.0: (0.03284170, 0.03186302),
               40.0: (0.07322031, 0.07055535), 60.0: (0.1376191, 0.1300480),
               80.0: (0.2896555, 0.2479299), 89.0: (0.3917105, 0.2424255)}


def _cross(a, b):
    return np.stack([a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
                     a[0] * b[1] - a[1] * b[0]])


def _unit(v):
    return v / np.linalg.norm(v, axis=0)


def _rotate(S, cos_chi, sin_chi):
    """Stokes vectors (4 x n) referred to axes turned by chi from e1
    towards e2."""
    c2 = cos_chi * cos_chi - sin_chi * sin_chi
    s2 = 2 * sin_chi * cos_chi
    out = S.copy()
    out[1] = S[1] * c2 + S[2] * s2
    out[2] = -S[1] * s2 + S[2] * c2
    return out


def _rayleigh(S, cos_t, per_sr):
    """Rayleigh's matrix (no depolarisation) on Stokes vectors referred to
    the scattering plane. ``per_sr``: the matrix per steradian, its (1,1)
    element the phase function 3 (1 + cos^2) / (16 pi); otherwise the
    matrix divided by its (1,1) element."""
    c2 = cos_t * cos_t
    a = (1 + c2) / 2
    b = (c2 - 1) / 2
    out = np.empty_like(S)
    out[0] = a * S[0] + b * S[1]
    out[1] = b * S[0] + a * S[1]
    out[2] = cos_t * S[2]
    out[3] = cos_t * S[3]
    scale = 3 / (8 * math.pi) if per_sr else 1 / a
    return out * scale


def _draw_rayleigh_cos(rng, n):
    """cos(angle) from 3 (1 + x^2) / 8 on [-1, 1], by its cubic CDF."""
    u = rng.random(n)
    # (x^3 + 3x + 4) / 8 = u: Cardano
    q = 4 - 8 * u
    r = np.sqrt(q * q / 4 + 1)
    return np.cbrt(-q / 2 + r) + np.cbrt(-q / 2 - r)


def detectors(mus=MUS, phis=PHIS):
    """Unit directions (z down) of the tabulated light: upwelling at the
    top, downwelling at the bottom, azimuth phi measured from the sun's
    direction of travel (the sun's beam travels towards +x)."""
    out = []
    for level in ("top", "bottom"):
        for mu in mus:
            for phi in phis:
                s = math.sqrt(max(0.0, 1 - mu * mu))
                p = math.radians(phi)
                z = -mu if level == "top" else mu
                out.append((level, mu, phi, (s * math.cos(p), s * math.sin(p),
                                             z)))
    return out


def _meridian_e1(u, phi_deg=None):
    """The reference axis in the meridian plane of direction u (3 x k):
    normal to u, towards +z (down). Straight up or down the meridian plane
    is the limit along the azimuth ``phi_deg`` (as the tables take it), or
    +x if none is given."""
    z = np.array([0.0, 0.0, 1.0])[:, None]
    e = z - (u[2] * u)
    small = np.linalg.norm(e, axis=0) < 1e-12
    if np.any(small):
        phi = (np.zeros(u.shape[1]) if phi_deg is None
               else np.radians(np.asarray(phi_deg, dtype=float)))
        side = -np.sign(u[2])
        e[:, small] = np.stack([side * np.cos(phi), side * np.sin(phi),
                                np.zeros_like(phi)])[:, small]
    return _unit(e)


def _estimate(pos_z, d, e1, S, U, U_e1, top, tau, polarised):
    """Next-event estimates from photons at depth pos_z with direction d,
    axis e1 and Stokes S (before scattering) into detector directions U
    (3 x k): a (4, k) sum."""
    n, k = d.shape[1], U.shape[1]
    out = np.zeros((4, k))
    for j in range(k):
        u = U[:, j:j + 1]
        cos_t = np.clip(np.sum(d * u, axis=0), -1.0, 1.0)
        nrm = _cross(d, np.repeat(u, n, axis=1))
        size = np.linalg.norm(nrm, axis=0)
        e2 = _cross(d, e1)
        nrm = np.where(size > 1e-12, nrm / np.maximum(size, 1e-300), e2)
        e1_sp = _cross(nrm, d)
        Sj = _rotate(S, np.sum(e1_sp * e1, axis=0), np.sum(e1_sp * e2, axis=0)) \
            if polarised else S
        out_s = _rayleigh(Sj, cos_t, per_sr=True) if polarised else \
            np.vstack([S[0] * 3 * (1 + cos_t ** 2) / (16 * math.pi),
                       np.zeros((3, n))])
        if polarised:
            e1_out = _cross(nrm, np.repeat(u, n, axis=1))
            m = np.repeat(U_e1[:, j:j + 1], n, axis=1)
            out_s = _rotate(out_s, np.sum(m * e1_out, axis=0),
                            np.sum(m * nrm, axis=0))
        mu = abs(float(u[2, 0]))
        path = (pos_z if top[j] else tau - pos_z) / mu
        out[:, j] = np.sum(out_s * np.exp(-path), axis=1) / mu
    return out


def run(seed, photons, tau=TAU, polarised=True, orders=None, mu0=MU0,
        mus=MUS, phis=PHIS):
    """One batch: the (4, k) Stokes parameters of the light leaving in
    every tabulated direction, per unit planar irradiance on the top.
    ``orders``: if given, only light scattered that many times or fewer."""
    rng = np.random.default_rng(seed)
    dets = detectors(mus, phis)
    U = np.array([d[3] for d in dets]).T
    U_e1 = _meridian_e1(U, [d[2] for d in dets])
    top = np.array([d[0] == "top" for d in dets])
    s0 = math.sqrt(1 - mu0 * mu0)
    d = np.tile([[s0], [0.0], [mu0]], photons)
    e1 = _meridian_e1(d)
    S = np.zeros((4, photons))
    S[0] = 1.0
    z = np.zeros(photons)
    total = np.zeros((4, U.shape[1]))
    order = 0
    while d.shape[1]:
        order += 1
        if orders is not None and order > orders:
            break
        step = -np.log(1.0 - rng.random(d.shape[1]))
        z = z + step * d[2]
        inside = (z > 0) & (z < tau)
        d, e1, S, z = d[:, inside], e1[:, inside], S[:, inside], z[inside]
        if not d.shape[1]:
            break
        total += _estimate(z, d, e1, S, U, U_e1, top, tau, polarised)
        # scatter (single scattering albedo 1)
        cos_t = _draw_rayleigh_cos(rng, d.shape[1])
        sin_t = np.sqrt(np.maximum(0.0, 1 - cos_t * cos_t))
        psi = 2 * math.pi * rng.random(d.shape[1])
        e2 = _cross(d, e1)
        nrm = np.cos(psi) * e2 + np.sin(psi) * e1
        e1_sp = _cross(nrm, d)
        if polarised:
            S = _rotate(S, np.sum(e1_sp * e1, axis=0),
                        np.sum(e1_sp * e2, axis=0))
            S = _rayleigh(S, cos_t, per_sr=False)
        d = _unit(cos_t * d + sin_t * e1_sp)
        e1 = _cross(nrm, d)
        weak = S[0] < _WEIGHT_FLOOR
        keep = rng.random(d.shape[1]) < 0.1
        S[:, weak & keep] *= 10.0
        alive = ~weak | keep
        d, e1, S, z = d[:, alive], e1[:, alive], S[:, alive], z[alive]
    return total / photons


def single_scattering(tau, mu0=MU0, mus=MUS, phis=PHIS):
    """The light singly scattered out of a layer of optical thickness tau
    (exactly, not only thin), per unit planar irradiance on the top, in
    this module's convention: (4, k)."""
    dets = detectors(mus, phis)
    U = np.array([d[3] for d in dets]).T
    U_e1 = _meridian_e1(U, [d[2] for d in dets])
    s0 = math.sqrt(1 - mu0 * mu0)
    d = np.array([[s0], [0.0], [mu0]])
    e1 = _meridian_e1(d)
    out = np.zeros((4, U.shape[1]))
    for j, det in enumerate(dets):
        mu = abs(det[3][2])
        if det[0] == "top":        # integral over the depth of the beam
            depth = (1 - math.exp(-tau * (1 / mu0 + 1 / mu))) \
                / (1 / mu0 + 1 / mu)
        elif abs(mu - mu0) < 1e-12:
            depth = tau * math.exp(-tau / mu0)
        else:
            depth = (math.exp(-tau / mu) - math.exp(-tau / mu0)) \
                / (1 / mu0 - 1 / mu)
        S = np.array([[1.0], [0.0], [0.0], [0.0]])
        u = U[:, j:j + 1]
        e2 = _cross(d, e1)
        nrm = _cross(d, u)
        size = float(np.linalg.norm(nrm))
        nrm = nrm / size if size > 1e-12 else e2   # forward: any plane
        e1_sp = _cross(nrm, d)
        S = _rotate(S, np.sum(e1_sp * e1, axis=0), np.sum(e1_sp * e2, axis=0))
        S = _rayleigh(S, np.sum(d * u, axis=0), per_sr=True)
        e1_out = _cross(nrm, u)
        m = U_e1[:, j:j + 1]
        S = _rotate(S, np.sum(m * e1_out, axis=0), np.sum(m * nrm, axis=0))
        # the beam's planar irradiance 1 is 1 / mu0 across the beam
        out[:, j] = S[:, 0] / mu0 * depth / mu
    return out


#: From this module's convention to the tables': I per unit planar
#: irradiance to I for an incident flux pi across the beam (F0 = 1), so
#: times pi mu0; Q = I1 - I2 with e1 in the meridian plane is Il - Ir,
#: and the tables' Q is Ir - Il (Coulson et al. 1960; Natraj et al. 2009,
#: p. 1909); U's sign, which depends on the handedness of the azimuth,
#: is the tables' with the opposite sign (fixed by the tables themselves,
#: DECISIONS.md section 145).
TO_TABLES = (math.pi * MU0, -math.pi * MU0, -math.pi * MU0, math.pi * MU0)


#: To Kokhanovsky et al.'s: Eq. (6), pi S / (mu0 F0), so pi times this
#: module's values per unit planar irradiance. Their tables' Q is I-perp
#: less I-parallel, as Coulson's, the opposite of their Eq. (2) as printed
#: (single scattering decides it: DECISIONS.md section 146), so this
#: module's Q with the opposite sign; U's sign fixed by the tables.
TO_KOKHANOVSKY = (math.pi, -math.pi, -math.pi, math.pi)


def kokhanovsky(path: str) -> None:
    """Section 146's run: Kokhanovsky et al.'s Rayleigh case."""
    mus = tuple(math.cos(math.radians(v)) for v in K_VZA)
    dets = detectors(mus, K_PHIS)
    scale = np.array(TO_KOKHANOVSKY)[:, None]
    geometry = dict(tau=K_TAU, mu0=K_MU0, mus=mus, phis=K_PHIS)
    batches = [run(SEED + k, PHOTONS, **geometry) * scale
               for k in range(BATCHES)]
    scalar = [run(SEED + 100 + k, PHOTONS, polarised=False, **geometry)
              * scale for k in range(BATCHES)]
    _write(path, dets, batches, scalar,
           vza=[K_VZA[mus.index(d[1])] for d in dets])


def _write(path, dets, batches, scalar, vza=None):
    mean = np.mean(batches, axis=0)
    se = np.std(batches, axis=0, ddof=1) / math.sqrt(len(batches))
    smean = np.mean(scalar, axis=0)
    sse = np.std(scalar, axis=0, ddof=1) / math.sqrt(len(scalar))
    rows = []
    for j, (level, mu, phi, _) in enumerate(dets):
        row = dict(level=level, mu=mu, phi=phi)
        if vza is not None:
            row = dict(level=level, vza=vza[j], phi=phi)
        row.update(I=f"{mean[0, j]:.8e}", I_se=f"{se[0, j]:.2e}",
                   Q=f"{mean[1, j]:.8e}", Q_se=f"{se[1, j]:.2e}",
                   U=f"{mean[2, j]:.8e}", U_se=f"{se[2, j]:.2e}",
                   V=f"{mean[3, j]:.8e}", V_se=f"{se[3, j]:.2e}",
                   I_scalar=f"{smean[0, j]:.8e}",
                   I_scalar_se=f"{sse[0, j]:.2e}")
        rows.append(row)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(path: str) -> None:
    dets = detectors()
    scale = np.array(TO_TABLES)[:, None]
    batches = [run(SEED + k, PHOTONS) * scale for k in range(BATCHES)]
    scalar = [run(SEED + 100 + k, PHOTONS, polarised=False) * scale
              for k in range(BATCHES)]
    mean = np.mean(batches, axis=0)
    se = np.std(batches, axis=0, ddof=1) / math.sqrt(BATCHES)
    smean = np.mean(scalar, axis=0)
    sse = np.std(scalar, axis=0, ddof=1) / math.sqrt(BATCHES)
    rows = []
    for j, (level, mu, phi, _) in enumerate(dets):
        rows.append(dict(level=level, mu=mu, phi=phi,
                         I=f"{mean[0, j]:.8e}", I_se=f"{se[0, j]:.2e}",
                         Q=f"{mean[1, j]:.8e}", Q_se=f"{se[1, j]:.2e}",
                         U=f"{mean[2, j]:.8e}", U_se=f"{se[2, j]:.2e}",
                         V=f"{mean[3, j]:.8e}", V_se=f"{se[3, j]:.2e}",
                         I_scalar=f"{smean[0, j]:.8e}",
                         I_scalar_se=f"{sse[0, j]:.2e}"))
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--kokhanovsky":
        kokhanovsky(sys.argv[2])
    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        sys.exit(__doc__)
