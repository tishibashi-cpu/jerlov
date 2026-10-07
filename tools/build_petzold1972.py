# -*- coding: utf-8 -*-
"""Transcribe the volume scattering functions of Petzold (1972).

T. J. Petzold, 'Volume scattering functions for selected ocean waters',
SIO Ref. 72-78, Scripps Institution of Oceanography, Visibility Laboratory
(October 1972); DTIC AD0753474. Approved for public release; distribution
unlimited.

The report prints, for each of eight ocean stations, the volume scattering
function sigma(theta) at 55 angles (0.1 to 10 degrees in steps of 0.1 in
log theta, then 5-degree steps to 180), with its running integral
2 pi int sigma sin(theta) dtheta and that integral divided by the total s
(Figs. 23, 25, ..., 37). The summary pages before them (Figs. 22, 24, ...,
36) give c, s and a at 530 nm, B/S, the slope used below 0.1 degree, the
median angle and sigma/s at 20, 40, 45 and 90 degrees.

All three columns of all eight tables were read from the page images and
compared with the report's own OCR text; every value the OCR rendered
legibly agreed. The checks below then tie the columns to one another and to
the summary pages, so that a misread digit cannot pass silently. No input
file is needed: the numbers are literals, as for Austin & Petzold (1986).
"""

import sys, pathlib, math, csv
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import DATA_DIR, report

import numpy as np

ANGLES = [round(10 ** (-1 + 0.1 * k), 4) for k in range(21)] + \
         [10.0 + 5 * k for k in range(1, 35)]

# station: (locale, date, figure of the table, c, s, a, B/S, slope,
#           median angle in degrees, sigma/s at 20, 40, 45, 90 degrees)
SUMMARY = {
    "AUTEC 7":  ("Tongue of the Ocean, Bahamas", "1971-07-09", 23, 0.199, 0.117, 0.082, 0.025, -1.599, 2.815, (2.2398e-01, 3.9911e-02, 2.7767e-02, 4.5819e-03)),
    "AUTEC 8":  ("Tongue of the Ocean, Bahamas", "1971-07-13", 25, 0.151, 0.037, 0.114, 0.044, -1.191, 6.252, (2.9474e-01, 5.0931e-02, 3.6785e-02, 6.5953e-03)),
    "AUTEC 9":  ("Tongue of the Ocean, Bahamas", "1971-07-14", 27, 0.165, 0.043, 0.122, 0.038, -1.248, 5.203, (2.8149e-01, 4.6939e-02, 3.3705e-02, 5.7745e-03)),
    "HAOCE 5":  ("Avalon Cove, Catalina Island", "1971-07-31", 29, 0.470, 0.275, 0.195, 0.014, -1.546, 2.152, (1.9702e-01, 2.6258e-02, 1.8893e-02, 2.6144e-03)),
    "HAOCE 11": ("Catalina Channel, offshore southern California", "1971-08-05", 31, 0.398, 0.219, 0.179, 0.013, -1.545, 2.534, (2.0184e-01, 2.7421e-02, 1.8892e-02, 2.3897e-03)),
    "NUC 2200": ("San Diego Harbor", "1971-10-04", 33, 1.920, 1.583, 0.337, 0.019, -1.249, 4.497, (2.4888e-01, 4.3390e-02, 3.1484e-02, 4.5753e-03)),
    "NUC 2040": ("San Diego Harbor", "1971-10-05", 35, 2.190, 1.824, 0.366, 0.020, -1.346, 4.680, (2.4405e-01, 4.3377e-02, 3.2108e-02, 4.6105e-03)),
    "NUC 2240": ("San Diego Harbor", "1971-10-05", 37, 1.330, 1.205, 0.125, 0.018, -1.442, 4.682, (2.4427e-01, 4.0555e-02, 2.9265e-02, 4.0360e-03)),
}

# The smallest angle measured at each station ("DATA READ IN" on the summary
# pages). The low-angle meter's 0.0859-degree point was too weak to use in
# the clearer waters (section 5.1), so there sigma below 0.169 degree is the
# report's own log-log extension with the printed slope.
FIRST_MEASURED = {"AUTEC 7": 0.169, "AUTEC 8": 0.169, "AUTEC 9": 0.169,
                  "HAOCE 5": 0.169, "HAOCE 11": 0.169, "NUC 2200": 0.0859,
                  "NUC 2040": 0.0859, "NUC 2240": 0.0859}

# sigma (1/(m sr)), integral (1/m), normalised integral, at ANGLES.
TABLES = {
    "AUTEC 7": """
    3.5578E02  1.6989E-02  1.4509E-01
    2.4618E02  1.8632E-02  1.5912E-01
    1.7035E02  2.0433E-02  1.7450E-01
    1.1899E02  2.2416E-02  1.9144E-01
    8.2607E01  2.4609E-02  2.1017E-01
    5.6694E01  2.7008E-02  2.3065E-01
    3.8278E01  2.9597E-02  2.5276E-01
    2.5691E01  3.2355E-02  2.7632E-01
    1.7245E01  3.5287E-02  3.0136E-01
    1.1566E01  3.8408E-02  3.2801E-01
    7.7116E00  4.1716E-02  3.5626E-01
    5.1122E00  4.5202E-02  3.8603E-01
    3.3694E00  4.8853E-02  4.1721E-01
    2.2007E00  5.2651E-02  4.4965E-01
    1.4291E00  5.6569E-02  4.8310E-01
    9.2474E-01  6.0593E-02  5.1747E-01
    5.9622E-01  6.4711E-02  5.5264E-01
    3.8303E-01  6.8910E-02  5.8850E-01
    2.4316E-01  7.3167E-02  6.2485E-01
    1.5421E-01  7.7427E-02  6.6124E-01
    9.9396E-02  8.1738E-02  6.9805E-01
    4.7716E-02  8.9779E-02  7.6672E-01
    2.6227E-02  9.5577E-02  8.1624E-01
    1.5466E-02  9.9785E-02  8.5217E-01
    9.7519E-03  1.0288E-01  8.7860E-01
    6.6915E-03  1.0526E-01  8.9892E-01
    4.6734E-03  1.0713E-01  9.1486E-01
    3.2513E-03  1.0857E-01  9.2716E-01
    2.3972E-03  1.0969E-01  9.3677E-01
    1.8570E-03  1.1061E-01  9.4460E-01
    1.4785E-03  1.1137E-01  9.5113E-01
    1.2073E-03  1.1202E-01  9.5668E-01
    9.9904E-04  1.1258E-01  9.6143E-01
    8.3229E-04  1.1305E-01  9.6550E-01
    7.0735E-04  1.1346E-01  9.6900E-01
    6.0370E-04  1.1382E-01  9.7203E-01
    5.3652E-04  1.1413E-01  9.7468E-01
    4.9430E-04  1.1441E-01  9.7708E-01
    4.6757E-04  1.1467E-01  9.7931E-01
    4.5696E-04  1.1492E-01  9.8142E-01
    4.4657E-04  1.1516E-01  9.8344E-01
    4.3223E-04  1.1538E-01  9.8534E-01
    4.2656E-04  1.1559E-01  9.8711E-01
    4.3290E-04  1.1579E-01  9.8882E-01
    4.3649E-04  1.1597E-01  9.9043E-01
    4.2956E-04  1.1615E-01  9.9192E-01
    4.3638E-04  1.1631E-01  9.9328E-01
    4.5911E-04  1.1646E-01  9.9456E-01
    4.8909E-04  1.1660E-01  9.9575E-01
    5.2124E-04  1.1672E-01  9.9684E-01
    5.7340E-04  1.1684E-01  9.9781E-01
    6.4918E-04  1.1694E-01  9.9867E-01
    7.5441E-04  1.1702E-01  9.9937E-01
    7.8458E-04  1.1708E-01  9.9984E-01
    8.1475E-04  1.1709E-01  1.0000E00
""",
    "AUTEC 8": """
    5.3182E01  1.2585E-03  3.3751E-02
    4.0424E01  1.5161E-03  4.0660E-02
    3.0727E01  1.8265E-03  4.8983E-02
    2.3735E01  2.2029E-03  5.9077E-02
    1.8141E01  2.6627E-03  7.1407E-02
    1.3598E01  3.2140E-03  8.6194E-02
    9.9536E00  3.8614E-03  1.0355E-01
    7.1793E00  4.6060E-03  1.2352E-01
    5.1100E00  5.4518E-03  1.4621E-01
    3.5911E00  6.3992E-03  1.7161E-01
    2.4976E00  7.4489E-03  1.9976E-01
    1.7191E00  8.5998E-03  2.3063E-01
    1.1710E00  9.8486E-03  2.6412E-01
    7.7576E-01  1.1182E-02  2.9987E-01
    5.0866E-01  1.2569E-02  3.3707E-01
    3.3399E-01  1.4011E-02  3.7574E-01
    2.1960E-01  1.5512E-02  4.1601E-01
    1.4459E-01  1.7078E-02  4.5798E-01
    9.5219E-02  1.8711E-02  5.0178E-01
    6.2816E-02  2.0414E-02  5.4746E-01
    4.1620E-02  2.2196E-02  5.9525E-01
    2.0375E-02  2.5612E-02  6.8686E-01
    1.0990E-02  2.8075E-02  7.5292E-01
    6.1656E-03  2.9789E-02  7.9888E-01
    3.8877E-03  3.1021E-02  8.3190E-01
    2.6802E-03  3.1972E-02  8.5741E-01
    1.8991E-03  3.2723E-02  8.7756E-01
    1.3717E-03  3.3321E-02  8.9360E-01
    1.0196E-03  3.3798E-02  9.0638E-01
    7.6833E-04  3.4183E-02  9.1672E-01
    6.0280E-04  3.4496E-02  9.2511E-01
    4.8832E-04  3.4761E-02  9.3220E-01
    4.0688E-04  3.4985E-02  9.3822E-01
    3.4571E-04  3.5182E-02  9.4350E-01
    3.0191E-04  3.5353E-02  9.4809E-01
    2.6810E-04  3.5509E-02  9.5226E-01
    2.4593E-04  3.5648E-02  9.5599E-01
    2.3152E-04  3.5779E-02  9.5952E-01
    2.2394E-04  3.5902E-02  9.6280E-01
    2.2254E-04  3.6022E-02  9.6603E-01
    2.2393E-04  3.6137E-02  9.6913E-01
    2.2651E-04  3.6253E-02  9.7221E-01
    2.3392E-04  3.6363E-02  9.7518E-01
    2.5050E-04  3.6476E-02  9.7822E-01
    2.6290E-04  3.6587E-02  9.8118E-01
    2.6615E-04  3.6695E-02  9.8407E-01
    2.7488E-04  3.6794E-02  9.8672E-01
    2.8957E-04  3.6889E-02  9.8928E-01
    3.0882E-04  3.6975E-02  9.9160E-01
    3.3044E-04  3.7057E-02  9.9380E-01
    3.6268E-04  3.7128E-02  9.9570E-01
    4.0732E-04  3.7193E-02  9.9743E-01
    4.6710E-04  3.7243E-02  9.9877E-01
    4.8450E-04  3.7278E-02  9.9972E-01
    5.0190E-04  3.7289E-02  1.0000E00
""",
    "AUTEC 9": """
    7.5181E01  1.9133E-03  4.4926E-02
    5.6404E01  2.2750E-03  5.3420E-02
    4.2318E01  2.7051E-03  6.3520E-02
    3.2379E01  3.2208E-03  7.5629E-02
    2.4458E01  3.8444E-03  9.0272E-02
    1.8039E01  4.5819E-03  1.0759E-01
    1.2885E01  5.4306E-03  1.2752E-01
    9.0697E00  6.3824E-03  1.4987E-01
    6.3271E00  7.4393E-03  1.7468E-01
    4.3741E00  8.6025E-03  2.0200E-01
    2.9964E00  9.8711E-03  2.3179E-01
    2.0339E00  1.1242E-02  2.6398E-01
    1.3679E00  1.2710E-02  2.9845E-01
    9.0011E-01  1.4261E-02  3.3486E-01
    5.8691E-01  1.5866E-02  3.7255E-01
    3.8249E-01  1.7524E-02  4.1148E-01
    2.4913E-01  1.9235E-02  4.5167E-01
    1.6219E-01  2.1001E-02  4.9314E-01
    1.0552E-01  2.2822E-02  5.3588E-01
    6.8616E-02  2.4696E-02  5.7990E-01
    4.4602E-02  2.6625E-02  6.2519E-01
    2.0871E-02  3.0157E-02  7.0812E-01
    1.1988E-02  3.2759E-02  7.6922E-01
    7.0743E-03  3.4693E-02  8.1464E-01
    4.2671E-03  3.6075E-02  8.4709E-01
    2.8615E-03  3.7103E-02  8.7123E-01
    1.9990E-03  3.7900E-02  8.8993E-01
    1.4354E-03  3.8527E-02  9.0466E-01
    1.0695E-03  3.9026E-02  9.1639E-01
    8.1689E-04  3.9433E-02  9.2593E-01
    6.4576E-04  3.9767E-02  9.3379E-01
    5.2780E-04  4.0052E-02  9.4047E-01
    4.3685E-04  4.0294E-02  9.4616E-01
    3.6098E-04  4.0502E-02  9.5104E-01
    3.0890E-04  4.0680E-02  9.5521E-01
    2.7117E-04  4.0837E-02  9.5891E-01
    2.4592E-04  4.0978E-02  9.6221E-01
    2.2817E-04  4.1108E-02  9.6527E-01
    2.1893E-04  4.1228E-02  9.6809E-01
    2.1753E-04  4.1346E-02  9.7085E-01
    2.1892E-04  4.1459E-02  9.7351E-01
    2.2163E-04  4.1571E-02  9.7614E-01
    2.2891E-04  4.1680E-02  9.7869E-01
    2.4411E-04  4.1790E-02  9.8128E-01
    2.5689E-04  4.1898E-02  9.8382E-01
    2.6476E-04  4.2004E-02  9.8631E-01
    2.7486E-04  4.2103E-02  9.8864E-01
    2.8622E-04  4.2197E-02  9.9085E-01
    3.0180E-04  4.2283E-02  9.9286E-01
    3.1644E-04  4.2362E-02  9.9470E-01
    3.4665E-04  4.2430E-02  9.9631E-01
    3.9514E-04  4.2491E-02  9.9775E-01
    4.6697E-04  4.2541E-02  9.9892E-01
    4.8702E-04  4.2576E-02  9.9974E-01
    5.0708E-04  4.2587E-02  1.0000E00
""",
    "HAOCE 5": """
    8.7125E02  3.6769E-02  1.3380E-01
    6.1023E02  4.0817E-02  1.4852E-01
    4.2741E02  4.5309E-02  1.6487E-01
    2.9993E02  5.0301E-02  1.8304E-01
    2.1021E02  5.5850E-02  2.0323E-01
    1.4699E02  6.2008E-02  2.2564E-01
    1.0321E02  6.8842E-02  2.5050E-01
    7.1786E01  7.6422E-02  2.7809E-01
    4.9083E01  8.4714E-02  3.0826E-01
    3.3035E01  9.3617E-02  3.4066E-01
    2.2014E01  1.0307E-01  3.7504E-01
    1.4525E01  1.1299E-01  4.1117E-01
    9.4888E00  1.2333E-01  4.4876E-01
    6.0470E00  1.3391E-01  4.8729E-01
    3.8159E00  1.4452E-01  5.2589E-01
    2.4083E00  1.5513E-01  5.6449E-01
    1.5201E00  1.6574E-01  6.0309E-01
    9.5955E-01  1.7635E-01  6.4169E-01
    6.0612E-01  1.8695E-01  6.8030E-01
    3.8285E-01  1.9757E-01  7.1892E-01
    2.4154E-01  2.0817E-01  7.5750E-01
    1.0703E-01  2.2701E-01  8.2605E-01
    5.4145E-02  2.3947E-01  8.7139E-01
    3.0441E-02  2.4803E-01  9.0252E-01
    1.7026E-02  2.5377E-01  9.2341E-01
    1.0696E-02  2.5772E-01  9.3780E-01
    7.2160E-03  2.6065E-01  9.4847E-01
    5.1921E-03  2.6291E-01  9.5669E-01
    3.8094E-03  2.6472E-01  9.6326E-01
    2.8128E-03  2.6613E-01  9.6840E-01
    2.1547E-03  2.6728E-01  9.7257E-01
    1.7077E-03  2.6820E-01  9.7593E-01
    1.3769E-03  2.6898E-01  9.7879E-01
    1.1132E-03  2.6962E-01  9.8111E-01
    9.3400E-04  2.7018E-01  9.8312E-01
    8.1444E-04  2.7064E-01  9.8481E-01
    7.1848E-04  2.7107E-01  9.8637E-01
    6.3331E-04  2.7143E-01  9.8768E-01
    5.7577E-04  2.7176E-01  9.8890E-01
    5.3823E-04  2.7205E-01  9.8995E-01
    5.1384E-04  2.7234E-01  9.9098E-01
    4.9853E-04  2.7258E-01  9.9188E-01
    4.9379E-04  2.7283E-01  9.9279E-01
    4.9637E-04  2.7305E-01  9.9359E-01
    5.1058E-04  2.7328E-01  9.9442E-01
    5.3875E-04  2.7348E-01  9.9515E-01
    5.7309E-04  2.7370E-01  9.9593E-01
    6.1210E-04  2.7388E-01  9.9662E-01
    6.6212E-04  2.7408E-01  9.9733E-01
    6.9954E-04  2.7424E-01  9.9792E-01
    8.0075E-04  2.7441E-01  9.9852E-01
    9.8574E-04  2.7454E-01  9.9902E-01
    1.2964E-03  2.7468E-01  9.9953E-01
    1.3790E-03  2.7477E-01  9.9985E-01
    1.4616E-03  2.7481E-01  1.0000E00
""",
    "HAOCE 11": """
    6.5329E02  2.7506E-02  1.2541E-01
    4.5768E02  3.0541E-02  1.3925E-01
    3.2064E02  3.3911E-02  1.5461E-01
    2.2517E02  3.7657E-02  1.7169E-01
    1.5788E02  4.1824E-02  1.9069E-01
    1.1038E02  4.6449E-02  2.1178E-01
    7.7309E01  5.1575E-02  2.3515E-01
    5.3705E01  5.7248E-02  2.6102E-01
    3.6749E01  6.3454E-02  2.8931E-01
    2.4805E01  7.0127E-02  3.1974E-01
    1.6623E01  7.7241E-02  3.5217E-01
    1.1060E01  8.4769E-02  3.8650E-01
    7.3058E00  9.2677E-02  4.2256E-01
    4.7505E00  1.0090E-01  4.6006E-01
    3.0669E00  1.0933E-01  4.9849E-01
    1.9772E00  1.1795E-01  5.3778E-01
    1.2728E00  1.2675E-01  5.7789E-01
    8.1825E-01  1.3571E-01  6.1877E-01
    5.2847E-01  1.4485E-01  6.6042E-01
    3.4020E-01  1.5420E-01  7.0307E-01
    2.1554E-01  1.6365E-01  7.4617E-01
    9.2828E-02  1.8032E-01  8.2214E-01
    4.4268E-02  1.9081E-01  8.7000E-01
    2.3900E-02  1.9759E-01  9.0089E-01
    1.4450E-02  2.0229E-01  9.2233E-01
    9.0629E-03  2.0565E-01  9.3767E-01
    6.0140E-03  2.0812E-01  9.4889E-01
    4.1435E-03  2.0996E-01  9.5730E-01
    2.9934E-03  2.1138E-01  9.6379E-01
    2.2525E-03  2.1251E-01  9.6893E-01
    1.7366E-03  2.1343E-01  9.7310E-01
    1.3689E-03  2.1418E-01  9.7652E-01
    1.0940E-03  2.1480E-01  9.7934E-01
    8.7821E-04  2.1531E-01  9.8168E-01
    7.2376E-04  2.1573E-01  9.8362E-01
    6.0355E-04  2.1609E-01  9.8526E-01
    5.2412E-04  2.1640E-01  9.8666E-01
    4.7034E-04  2.1667E-01  9.8789E-01
    4.3626E-04  2.1692E-01  9.8901E-01
    4.1890E-04  2.1714E-01  9.9006E-01
    4.0727E-04  2.1736E-01  9.9104E-01
    3.9941E-04  2.1756E-01  9.9197E-01
    3.9723E-04  2.1776E-01  9.9285E-01
    3.9841E-04  2.1794E-01  9.9369E-01
    4.0710E-04  2.1812E-01  9.9449E-01
    4.2193E-04  2.1828E-01  9.9525E-01
    4.4582E-04  2.1844E-01  9.9598E-01
    4.7749E-04  2.1860E-01  9.9668E-01
    5.2319E-04  2.1874E-01  9.9735E-01
    5.8236E-04  2.1888E-01  9.9798E-01
    6.6651E-04  2.1901E-01  9.9858E-01
    7.8226E-04  2.1913E-01  9.9912E-01
    9.3927E-04  2.1923E-01  9.9958E-01
    9.8473E-04  2.1930E-01  9.9989E-01
    1.0302E-03  2.1933E-01  1.0000E00
""",
    "NUC 2200": """
    2.6897E03  6.8519E-02  4.3293E-02
    2.0184E03  8.1463E-02  5.1471E-02
    1.5137E03  9.6853E-02  6.1195E-02
    1.1434E03  1.1520E-01  7.2787E-02
    8.5880E02  1.3713E-01  8.6645E-02
    6.3858E02  1.6311E-01  1.0306E-01
    4.7132E02  1.9359E-01  1.2232E-01
    3.4338E02  2.2904E-01  1.4472E-01
    2.4613E02  2.6965E-01  1.7038E-01
    1.7368E02  3.1539E-01  1.9928E-01
    1.2098E02  3.6621E-01  2.3138E-01
    8.3195E01  4.2194E-01  2.6660E-01
    5.6477E01  4.8229E-01  3.0473E-01
    3.7376E01  5.4651E-01  3.4531E-01
    2.4419E01  6.1325E-01  3.8747E-01
    1.5884E01  6.8220E-01  4.3104E-01
    1.0287E01  7.5310E-01  4.7584E-01
    6.6334E00  8.2569E-01  5.2170E-01
    4.2564E00  8.9966E-01  5.6844E-01
    2.7197E00  9.7464E-01  6.1581E-01
    1.7321E00  1.0503E00  6.6364E-01
    7.7653E-01  1.1863E00  7.4956E-01
    3.9389E-01  1.2757E00  8.0605E-01
    2.4745E-01  1.3421E00  8.4797E-01
    1.3752E-01  1.3884E00  8.7725E-01
    9.6166E-02  1.4220E00  8.9848E-01
    6.8674E-02  1.4494E00  9.1577E-01
    4.9829E-02  1.4708E00  9.2929E-01
    3.7004E-02  1.4884E00  9.4042E-01
    2.7820E-02  1.5021E00  9.4906E-01
    2.1594E-02  1.5136E00  9.5637E-01
    1.7224E-02  1.5228E00  9.6213E-01
    1.4017E-02  1.5309E00  9.6726E-01
    1.1579E-02  1.5373E00  9.7131E-01
    9.7490E-03  1.5432E00  9.7506E-01
    8.3435E-03  1.5479E00  9.7800E-01
    7.2413E-03  1.5524E00  9.8084E-01
    6.3288E-03  1.5558E00  9.8303E-01
    5.6499E-03  1.5593E00  9.8524E-01
    5.1132E-03  1.5619E00  9.8689E-01
    4.7480E-03  1.5648E00  9.8867E-01
    4.5331E-03  1.5669E00  9.9000E-01
    4.3681E-03  1.5693E00  9.9152E-01
    4.2661E-03  1.5710E00  9.9263E-01
    4.1531E-03  1.5731E00  9.9394E-01
    3.9648E-03  1.5745E00  9.9482E-01
    3.9046E-03  1.5762E00  9.9590E-01
    3.9665E-03  1.5772E00  9.9656E-01
    4.1061E-03  1.5787E00  9.9747E-01
    4.2909E-03  1.5795E00  9.9798E-01
    4.6227E-03  1.5807E00  9.9873E-01
    5.1195E-03  1.5812E00  9.9908E-01
    5.8137E-03  1.5821E00  9.9964E-01
    6.0122E-03  1.5823E00  9.9975E-01
    6.2107E-03  1.5827E00  1.0000E00
""",
    "NUC 2040": """
    3.2620E03  9.5452E-02  5.2322E-02
    2.3974E03  1.1099E-01  6.0837E-02
    1.7566E03  1.2905E-01  7.0740E-02
    1.2745E03  1.4994E-01  8.2190E-02
    9.2603E02  1.7395E-01  9.5349E-02
    6.7637E02  2.0166E-01  1.1054E-01
    5.0267E02  2.3400E-01  1.2827E-01
    3.7048E02  2.7204E-01  1.4912E-01
    2.6762E02  3.1606E-01  1.7325E-01
    1.8974E02  3.6591E-01  2.0057E-01
    1.3288E02  4.2157E-01  2.3109E-01
    9.1912E01  4.8297E-01  2.6474E-01
    6.2795E01  5.4985E-01  3.0140E-01
    4.1708E01  6.2142E-01  3.4063E-01
    2.7365E01  6.9604E-01  3.8153E-01
    1.7926E01  7.7356E-01  4.2402E-01
    1.1723E01  8.5395E-01  4.6809E-01
    7.6549E00  9.3718E-01  5.1371E-01
    5.0388E00  1.0234E00  5.6096E-01
    3.3017E00  1.1134E00  6.1032E-01
    2.1107E00  1.2057E00  6.6088E-01
    9.0405E-01  1.3676E00  7.4963E-01
    4.4523E-01  1.4702E00  8.0587E-01
    2.7335E-01  1.5437E00  8.4617E-01
    1.6128E-01  1.5966E00  8.7515E-01
    1.1087E-01  1.6356E00  8.9658E-01
    7.9133E-02  1.6671E00  9.1381E-01
    5.8575E-02  1.6921E00  9.2752E-01
    4.3884E-02  1.7128E00  9.3887E-01
    3.2882E-02  1.7291E00  9.4780E-01
    2.5483E-02  1.7427E00  9.5524E-01
    2.0408E-02  1.7535E00  9.6120E-01
    1.6550E-02  1.7631E00  9.6642E-01
    1.3446E-02  1.7706E00  9.7058E-01
    1.1239E-02  1.7774E00  9.7430E-01
    9.6372E-03  1.7829E00  9.7728E-01
    8.4110E-03  1.7880E00  9.8009E-01
    7.3961E-03  1.7921E00  9.8234E-01
    6.6940E-03  1.7961E00  9.8455E-01
    6.2195E-03  1.7994E00  9.8632E-01
    5.8912E-03  1.8027E00  9.8817E-01
    5.7291E-03  1.8055E00  9.8967E-01
    5.5491E-03  1.8084E00  9.9129E-01
    5.3427E-03  1.8107E00  9.9255E-01
    5.1541E-03  1.8132E00  9.9392E-01
    4.9670E-03  1.8151E00  9.9492E-01
    4.8223E-03  1.8171E00  9.9603E-01
    4.6347E-03  1.8184E00  9.9678E-01
    4.6344E-03  1.8200E00  9.9764E-01
    4.8998E-03  1.8210E00  9.9819E-01
    5.1417E-03  1.8223E00  9.9888E-01
    5.3587E-03  1.8229E00  9.9924E-01
    5.5497E-03  1.8238E00  9.9971E-01
    5.6177E-03  1.8240E00  9.9981E-01
    5.6857E-03  1.8243E00  1.0000E00
""",
    "NUC 2240": """
    2.2153E03  7.5934E-02  6.2999E-02
    1.5855E03  8.6335E-02  7.1629E-02
    1.1393E03  9.8157E-02  8.1437E-02
    8.2732E02  1.1169E-01  9.2661E-02
    6.0058E02  1.2727E-01  1.0559E-01
    4.3425E02  1.4517E-01  1.2044E-01
    3.1314E02  1.6565E-01  1.3743E-01
    2.2458E02  1.8899E-01  1.5680E-01
    1.6037E02  2.1546E-01  1.7876E-01
    1.1393E02  2.4535E-01  2.0356E-01
    8.0269E01  2.7887E-01  2.3137E-01
    5.6082E01  3.1613E-01  2.6228E-01
    3.8858E01  3.5722E-01  2.9637E-01
    2.6852E01  4.0224E-01  3.3372E-01
    1.8401E01  4.5138E-01  3.7449E-01
    1.2457E01  5.0443E-01  4.1850E-01
    8.3305E00  5.6097E-01  4.6541E-01
    5.5035E00  6.2052E-01  5.1482E-01
    3.6296E00  6.8259E-01  5.6632E-01
    2.3572E00  7.4723E-01  6.1995E-01
    1.4749E00  8.1244E-01  6.7405E-01
    5.9012E-01  9.2093E-01  7.6405E-01
    2.9443E-01  9.8904E-01  8.2056E-01
    1.6615E-01  1.0352E00  8.5887E-01
    1.0204E-01  1.0680E00  8.8606E-01
    6.9550E-02  1.0928E00  9.0661E-01
    4.8882E-02  1.1122E00  9.2275E-01
    3.5274E-02  1.1276E00  9.3550E-01
    2.5982E-02  1.1398E00  9.4566E-01
    1.9268E-02  1.1495E00  9.5372E-01
    1.4840E-02  1.1573E00  9.6020E-01
    1.1801E-02  1.1638E00  9.6553E-01
    9.6046E-03  1.1692E00  9.7001E-01
    8.0020E-03  1.1737E00  9.7380E-01
    6.7265E-03  1.1777E00  9.7707E-01
    5.6162E-03  1.1810E00  9.7983E-01
    4.8646E-03  1.1839E00  9.8220E-01
    4.3754E-03  1.1864E00  9.8429E-01
    3.9923E-03  1.1887E00  9.8618E-01
    3.6746E-03  1.1907E00  9.8787E-01
    3.4458E-03  1.1926E00  9.8942E-01
    3.3149E-03  1.1943E00  9.9084E-01
    3.1757E-03  1.1959E00  9.9215E-01
    2.9975E-03  1.1973E00  9.9333E-01
    2.8847E-03  1.1986E00  9.9439E-01
    2.8162E-03  1.1997E00  9.9534E-01
    2.8087E-03  1.2007E00  9.9621E-01
    2.8509E-03  1.2017E00  9.9699E-01
    2.9532E-03  1.2025E00  9.9770E-01
    3.1716E-03  1.2033E00  9.9834E-01
    3.3427E-03  1.2040E00  9.9891E-01
    3.4632E-03  1.2046E00  9.9937E-01
    3.5323E-03  1.2050E00  9.9972E-01
    3.5640E-03  1.2052E00  9.9992E-01
    3.5956E-03  1.2053E00  1.0000E00
""",
}

# The same sigma as printed a second time, under "ITERATED DATA" on the
# summary pages (Figs. 22, 24, ..., 36), at the angles where the report has
# a measurement and that the 55-angle table shares: 0.1, 10, 15, 20, 25,
# then every 10 degrees from 30 to 180.
ITERATED_ANGLES = [0.1, 10.0, 15.0, 20.0, 25.0] + [30.0 + 10 * k for k in range(16)]
ITERATED = {
    "AUTEC 7":  "3.5578E02 9.9395E-02 4.7716E-02 2.6227E-02 1.5466E-02 9.7519E-03 4.6734E-03 2.3972E-03 1.4785E-03 9.9904E-04 7.0735E-04 5.3652E-04 4.6757E-04 4.4657E-04 4.2656E-04 4.3649E-04 4.3638E-04 4.8909E-04 5.7340E-04 7.5441E-04 8.1475E-04",
    "AUTEC 8":  "5.3182E01 4.1620E-02 2.0375E-02 1.0990E-02 6.1656E-03 3.8877E-03 1.8991E-03 1.0196E-03 6.0280E-04 4.0688E-04 3.0191E-04 2.4593E-04 2.2394E-04 2.2393E-04 2.3392E-04 2.6290E-04 2.7488E-04 3.0882E-04 3.6268E-04 4.6710E-04 5.0190E-04",
    "AUTEC 9":  "7.5181E01 4.4602E-02 2.0871E-02 1.1988E-02 7.0743E-03 4.2671E-03 1.9990E-03 1.0695E-03 6.4576E-04 4.3685E-04 3.0890E-04 2.4592E-04 2.1893E-04 2.1892E-04 2.2891E-04 2.5689E-04 2.7486E-04 3.0180E-04 3.4665E-04 4.6697E-04 5.0708E-04",
    "HAOCE 5":  "8.7125E02 2.4154E-01 1.0703E-01 5.4145E-02 3.0441E-02 1.7026E-02 7.2160E-03 3.8094E-03 2.1547E-03 1.3769E-03 9.3400E-04 7.1848E-04 5.7577E-04 5.1384E-04 4.9379E-04 5.1058E-04 5.7309E-04 6.6212E-04 8.0075E-04 1.2964E-03 1.4616E-03",
    "HAOCE 11": "6.5329E02 2.1554E-01 9.2828E-02 4.4268E-02 2.3900E-02 1.4450E-02 6.0140E-03 2.9934E-03 1.7366E-03 1.0940E-03 7.2376E-04 5.2412E-04 4.3626E-04 4.0727E-04 3.9723E-04 4.0710E-04 4.4582E-04 5.2319E-04 6.6651E-04 9.3927E-04 1.0302E-03",
    "NUC 2200": "2.6897E03 1.7321E00 7.7653E-01 3.9389E-01 2.4745E-01 1.3752E-01 6.8674E-02 3.7004E-02 2.1594E-02 1.4017E-02 9.7490E-03 7.2413E-03 5.6499E-03 4.7480E-03 4.3681E-03 4.1531E-03 3.9046E-03 4.1061E-03 4.6227E-03 5.8137E-03 6.2107E-03",
    "NUC 2040": "3.2620E03 2.1107E00 9.0405E-01 4.4523E-01 2.7335E-01 1.6128E-01 7.9133E-02 4.3884E-02 2.5483E-02 1.6550E-02 1.1239E-02 8.4110E-03 6.6940E-03 5.8912E-03 5.5491E-03 5.1541E-03 4.8223E-03 4.6344E-03 5.1417E-03 5.5497E-03 5.6857E-03",
    "NUC 2240": "2.2153E03 1.4749E00 5.9012E-01 2.9443E-01 1.6615E-01 1.0204E-01 4.8882E-02 2.5982E-02 1.4840E-02 9.6046E-03 6.7265E-03 4.8646E-03 3.9923E-03 3.4458E-03 3.1757E-03 2.8847E-03 2.8087E-03 2.9532E-03 3.3427E-03 3.5323E-03 3.5956E-03",
}


def ulp(x):
    """Half a unit in the fifth significant figure, the printed precision."""
    return 0.5e-4 * 10 ** math.floor(math.log10(abs(x)))


def parse(text):
    rows = [[float(v) for v in line.split()] for line in text.strip().splitlines()]
    if len(rows) != len(ANGLES) or any(len(r) != 3 for r in rows):
        raise SystemExit("a table does not have 55 rows of three numbers")
    return [np.array(c) for c in zip(*rows)]


th = np.radians(ANGLES)
failed = []
for station, text in TABLES.items():
    sigma, integral, norm = parse(text)
    _, _, _, c, s, a, bs, slope, median, ratios = SUMMARY[station]
    total = integral[-1]
    print(f"\n{station}: s = {total:g} 1/m")

    # Check 0: the two printings of sigma agree, to one unit in the fifth
    # figure. (AUTEC 7 at 10 degrees reads 9.9396E-02 in one and 9.9395E-02
    # in the other.)
    second = [float(v) for v in ITERATED[station].split()]
    off = [a for a, v in zip(ITERATED_ANGLES, second)
           if abs(sigma[ANGLES.index(a)] - v) > 2.01 * ulp(v)]
    print(f"  check 0, sigma against its second printing: {len(off)} differ")
    if off: failed.append((station, "second printing", off))

    # Check 1: the normalised column is the integral over s.
    bad = [ANGLES[k] for k in range(55)
           if abs(integral[k] / total - norm[k])
           > 2 * (ulp(integral[k]) / total + ulp(total) * integral[k] / total ** 2
                  + ulp(norm[k]))]
    print(f"  check 1, integral / s = normalised integral: {len(bad)} misses")
    if bad: failed.append((station, "normalised", bad))

    # Check 2: each step of the integral is 2 pi int sigma sin, with sigma
    # taken as a power law between the printed angles. Where the report's own
    # integral alternates about the true one (NUC 2200 and NUC 2040, beyond
    # 90 degrees; see DATA.md section 21), two steps together must agree.
    inc = [0.0]
    for k in range(1, 55):
        m = math.log(sigma[k] / sigma[k - 1]) / math.log(th[k] / th[k - 1])
        x = np.linspace(th[k - 1], th[k], 400)
        y = 2 * math.pi * sigma[k - 1] * (x / th[k - 1]) ** m * np.sin(x)
        inc.append(float(np.sum((y[1:] + y[:-1]) / 2 * np.diff(x))))
    def agrees(i, j):
        # Below 10 degrees the steps are large and the power law fits to
        # 0.4 percent; beyond, the steps are small against the rounding of
        # a running total printed to five figures.
        d, e = integral[j] - integral[i - 1], sum(inc[i:j + 1])
        return abs(e - d) <= (0.01 if j <= 20 else 0.03) * d + 4 * ulp(integral[j])
    single = [k for k in range(1, 55) if not agrees(k, k)]
    unpaired = [k for k in single
                if not (agrees(k - 1, k) if k > 1 else False)
                and not (agrees(k, k + 1) if k < 54 else False)]
    print(f"  check 2, steps of the integral from sigma: {len(single)} single "
          f"steps miss, {len(unpaired)} not recovered over two")
    if unpaired: failed.append((station, "integral", [ANGLES[k] for k in unpaired]))

    # Check 3: sigma/s at 20, 40, 45 and 90 degrees, from the summary page.
    for angle, printed in zip((20.0, 40.0, 45.0, 90.0), ratios):
        mine = sigma[ANGLES.index(angle)] / total
        if abs(mine - printed) > 2 * (ulp(printed) + mine * ulp(total) / total):
            failed.append((station, f"sigma/s at {angle:g}", mine, printed))
    print("  check 3, sigma/s at 20, 40, 45, 90 degrees: done")

    # Check 4: s, a = c - s, and B/S agree with the summary page, which
    # prints them to three decimals.
    back = (total - integral[ANGLES.index(90.0)]) / total
    for name, mine, printed in (("s", total, s), ("c - s", c - s, a),
                                ("B/S", back, bs)):
        if abs(mine - printed) > 0.0015:
            failed.append((station, name, mine, printed))
    print(f"  check 4, s, a and B/S: B/S from the table {back:.4f}, printed {bs}")

    # Check 5: the median angle, where the normalised integral is one half.
    k = int(np.searchsorted(norm, 0.5))
    f = (0.5 - norm[k - 1]) / (norm[k] - norm[k - 1])
    mine = 10 ** (math.log10(ANGLES[k - 1])
                  + f * (math.log10(ANGLES[k]) - math.log10(ANGLES[k - 1])))
    print(f"  check 5, median angle: {mine:.3f} from the table, {median} printed")
    if abs(mine - median) > 0.02 * median:
        failed.append((station, "median", mine, median))

    # Check 7: below 10 degrees sigma is smooth in log-log; each value lies
    # within 1.5 percent of the cubic through its four nearest neighbours
    # (the quadratic through three, next to 0.1 degree)
    # (0.85 percent at worst as printed).
    la, ls = np.log(ANGLES), np.log(sigma)
    rough = []
    for k in range(1, 20):
        near = [j for j in range(k - 2, k + 3) if 0 <= j <= 20 and j != k]
        x = la[near] - la[k]
        fit = np.polyval(np.polyfit(x, ls[near], min(3, len(near) - 1)), 0.0)
        if abs(math.expm1(ls[k] - fit)) > 0.015:
            rough.append(ANGLES[k])
    # Check 8: from 35 to 175 degrees, the angles between two printed twice
    # lie between -5 and +2 percent of their neighbours' geometric mean
    # (-3.9 and +1.0 as printed).
    for angle in [35.0 + 10 * j for j in range(15)]:
        k = ANGLES.index(angle)
        r = sigma[k] / math.sqrt(sigma[k - 1] * sigma[k + 1]) - 1
        if not -0.05 <= r <= 0.02:
            rough.append(angle)
    print(f"  checks 7 and 8, smoothness: {len(rough)} outliers")
    if rough: failed.append((station, "smoothness", rough))

    # Check 6: where there is no measurement below 0.169 degree, the values
    # there follow the printed slope exactly, which is what marks them as
    # the report's extension rather than data.
    if FIRST_MEASURED[station] > 0.1585:
        m = math.log(sigma[2] / sigma[0]) / math.log(ANGLES[2] / ANGLES[0])
        print(f"  check 6, slope from 0.1 to 0.1585 degree: {m:.3f}, printed {slope}")
        if abs(m - slope) > 0.005:
            failed.append((station, "slope", m, slope))

if failed:
    raise SystemExit(f"the transcription fails its checks: {failed}")

with open(DATA_DIR / "petzold1972_vsf.csv", "w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f)
    wr.writerow(["station", "angle_deg", "vsf_per_m_sr", "integral_per_m",
                 "normalized_integral", "status", "note"])
    n = 0
    for station, text in TABLES.items():
        for angle, row in zip(ANGLES, zip(*parse(text))):
            if angle < FIRST_MEASURED[station]:
                status, note = "extrapolated", (
                    "below the first measured angle, 0.169 deg; the report "
                    "extends sigma there with its log-log slope")
            else:
                status, note = "ok", ""
            wr.writerow([station, f"{angle:g}"] + [f"{v:.4E}" for v in row]
                        + [status, note])
            n += 1
report("petzold1972_vsf.csv", n)

with open(DATA_DIR / "petzold1972_stations.csv", "w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f)
    wr.writerow(["station", "locale", "date", "wavelength_nm", "c_per_m",
                 "b_per_m", "a_per_m", "bb_over_b", "slope_below_0.1deg",
                 "median_angle_deg", "report_figure"])
    for station, (locale, date, fig, c, s, a, bs, slope, median, _) in SUMMARY.items():
        wr.writerow([station, locale, date, 530, f"{c:.3f}", f"{s:.3f}",
                     f"{a:.3f}", f"{bs:.3f}", f"{slope:.3f}", f"{median:.3f}",
                     fig])
report("petzold1972_stations.csv", len(SUMMARY))
