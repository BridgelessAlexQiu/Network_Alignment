import matplotlib.pyplot as plt

x = [0, 0.01, 0.03, 0.05, 0.07, 0.09, 0.11, 0.13, 0.15, 0.17, 0.19, 0.21, 0.23, 0.25]

# [, , , , , , , , , , , , , ]

y_mine_naive = [1, 1, 0.999865, 0.999731, 0.992596, 0.997442, 0.995019, 0.990711, 0.975363, 0.984518, 0.977518, 0.981826, 0.971055, 0.967286]

y_mine_advanced = [1, 1, 0.999865, 0.999731, 0.995288, 0.997442, 0.997981, 0.992192, 0.991653, 0.988018, 0.982229, 0.989768, 0.983845, 0.980749]

y_netal = [1, 0.999865, 0.987345, 0.981287, 0.91559, 0.844238, 0.72846, 0.787157, 0.715401, 0.718363, 0.717017, 0.617528, 0.621702, 0.60447]

y_hubalign = [1, 0.789311, 0.757135, 0.66559, 0.646742, 0.578756, 0.589391, 0.549677, 0.571217, 0.572025, 0.56489, 0.555331, 0.531099, 0.539984]

y_iso = [1, 0.39283, 0.1249058, 0.12498327, 0.1129283, 0.1128934, 0.0982734, 0.102829374, 0.1192038, 0.119029, 0.0582823, 0.0529283, 0.058292, 0.0426729]

plt.xlabel("Noise level")
plt.ylabel("EC")
plt.ylim((0, 1.1))

plt.title("Erdos network")

plt.plot(x, y_mine_naive, 'o--', label='Naive_alignment')
plt.plot(x, y_mine_advanced, 'o--', label='Seed_alignment')
plt.plot(x, y_netal, 'o--', label='NETAL')
plt.plot(x, y_hubalign, 'o--', label='HubAlign')
plt.plot(x, y_iso, 'o--', label='IsoRank')
plt.legend()

plt.show()