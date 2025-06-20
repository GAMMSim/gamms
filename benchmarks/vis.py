import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Re-importing the necessary libraries due to environment reset
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Intel vs M3 benchmark data for 30x30 grid
intel_benchmark_data = [
    {"benchmark": "30x30 grid with 10 agents vs 100 agents without map sensors", "min": 4.646, "max": 4.646, "mean": 4.646, "min_plus": 45.388, "max_plus": 45.388, "mean_plus": 45.388},
    {"benchmark": "30x30 grid with 10 agents vs 100 agents with map sensors", "min": 7.725, "max": 7.725, "mean": 7.725, "min_plus": 76.981, "max_plus": 76.981, "mean_plus": 76.981},
    {"benchmark": "30x30 grid with 20 agents vs 200 agents without map sensors", "min": 9.165, "max": 9.165, "mean": 9.165, "min_plus": 90.795, "max_plus": 90.795, "mean_plus": 90.795},
    {"benchmark": "30x30 grid with 20 agents vs 200 agents with map sensors", "min": 15.280, "max": 15.280, "mean": 15.280, "min_plus": 155.098, "max_plus": 155.098, "mean_plus": 155.098},
    {"benchmark": "30x30 grid with 30 agents vs 300 agents without map sensors", "min": 13.893, "max": 13.893, "mean": 13.893, "min_plus": 142.738, "max_plus": 142.738, "mean_plus": 142.738},
    {"benchmark": "30x30 grid with 30 agents vs 300 agents with map sensors", "min": 23.446, "max": 23.446, "mean": 23.446, "min_plus": 232.568, "max_plus": 232.568, "mean_plus": 232.568},
    {"benchmark": "30x30 grid with 50 agents vs 500 agents without map sensors", "min": 22.926, "max": 22.926, "mean": 22.926, "min_plus": 226.748, "max_plus": 226.748, "mean_plus": 226.748},
    {"benchmark": "30x30 grid with 50 agents vs 500 agents with map sensors", "min": 38.626, "max": 38.626, "mean": 38.626, "min_plus": 384.081, "max_plus": 384.081, "mean_plus": 384.081},
]

# Convert to DataFrame for Intel
df_intel = pd.DataFrame(intel_benchmark_data)

# M3 data as provided in the previous message
m3_benchmark_data = [
    {"benchmark": "30x30 grid with 10 agents vs 100 agents without map sensors", "min": 1.780, "max": 1.780, "mean": 1.780, "min_plus": 17.928, "max_plus": 17.928, "mean_plus": 17.928},
    {"benchmark": "30x30 grid with 10 agents vs 100 agents with map sensors", "min": 3.560, "max": 3.560, "mean": 3.560, "min_plus": 35.044, "max_plus": 35.044, "mean_plus": 35.044},
    {"benchmark": "30x30 grid with 20 agents vs 200 agents without map sensors", "min": 3.546, "max": 3.546, "mean": 3.546, "min_plus": 35.395, "max_plus": 35.395, "mean_plus": 35.395},
    {"benchmark": "30x30 grid with 20 agents vs 200 agents with map sensors", "min": 8.044, "max": 8.044, "mean": 8.044, "min_plus": 70.350, "max_plus": 70.350, "mean_plus": 70.350},
    {"benchmark": "30x30 grid with 30 agents vs 300 agents without map sensors", "min": 5.497, "max": 5.497, "mean": 5.497, "min_plus": 53.133, "max_plus": 53.133, "mean_plus": 53.133},
    {"benchmark": "30x30 grid with 30 agents vs 300 agents with map sensors", "min": 10.399, "max": 10.399, "mean": 10.399, "min_plus": 107.700, "max_plus": 107.700, "mean_plus": 107.700},
    {"benchmark": "30x30 grid with 50 agents vs 500 agents without map sensors", "min": 8.834, "max": 8.834, "mean": 8.834, "min_plus": 88.391, "max_plus": 88.391, "mean_plus": 88.391},
    {"benchmark": "30x30 grid with 50 agents vs 500 agents with map sensors", "min": 17.501, "max": 17.501, "mean": 17.501, "min_plus": 174.566, "max_plus": 174.566, "mean_plus": 174.566},
]

# Convert to DataFrame for M3
df_m3 = pd.DataFrame(m3_benchmark_data)

# Bar graph for Intel vs M3
fig, ax = plt.subplots(figsize=(12, 6))

# Bar width
bar_width = 0.35

# Bar positions for Intel and M3
index = np.arange(len(df_intel))

# Plot Intel data
ax.bar(index, df_intel['mean'], bar_width, label='Intel', color='blue')
ax.bar(index + bar_width, df_m3['mean'], bar_width, label='M3', color='orange')

ax.set_xlabel('Benchmark')
ax.set_ylabel('Steps per Second')
ax.set_title('Intel vs M3: Benchmark Performance (Mean)')
ax.set_xticks(index + bar_width / 2)
ax.set_xticklabels(df_intel['benchmark'], rotation=45)
ax.legend()

plt.tight_layout()
plt.savefig('benchmark_performance30.png', dpi=300)
plt.show()


"""
100x 100
"""

# # Additional benchmark data
# benchmark_data_additional = [
#     {"benchmark": "100x100 grid with 10 agents vs 100 agents without map sensors", "min": 20.179, "max": 20.179, "mean": 20.179, "min_plus": 202.741, "max_plus": 202.741, "mean_plus": 202.741},
#     {"benchmark": "100x100 grid with 10 agents vs 100 agents with map sensors", "min": 40.049, "max": 40.049, "mean": 40.049, "min_plus": 401.329, "max_plus": 401.329, "mean_plus": 401.329},
#     {"benchmark": "100x100 grid with 20 agents vs 200 agents without map sensors", "min": 40.683, "max": 40.683, "mean": 40.683, "min_plus": 407.157, "max_plus": 407.157, "mean_plus": 407.157},
#     {"benchmark": "100x100 grid with 20 agents vs 200 agents with map sensors", "min": 80.102, "max": 80.102, "mean": 80.102, "min_plus": 802.887, "max_plus": 802.887, "mean_plus": 802.887},
#     {"benchmark": "100x100 grid with 30 agents vs 300 agents without map sensors", "min": 60.435, "max": 60.435, "mean": 60.435, "min_plus": 603.162, "max_plus": 603.162, "mean_plus": 603.162},
#     {"benchmark": "100x100 grid with 30 agents vs 300 agents with map sensors", "min": 119.779, "max": 119.779, "mean": 119.779, "min_plus": 1209.115, "max_plus": 1209.115, "mean_plus": 1209.115},
#     {"benchmark": "100x100 grid with 50 agents vs 500 agents without map sensors", "min": 100.163, "max": 100.163, "mean": 100.163, "min_plus": 1019.049, "max_plus": 1019.049, "mean_plus": 1019.049},
#     {"benchmark": "100x100 grid with 50 agents vs 500 agents with map sensors", "min": 200.549, "max": 200.549, "mean": 200.549, "min_plus": 2012.245, "max_plus": 2012.245, "mean_plus": 2012.245}
# ]

# # Convert to DataFrame
# df_additional = pd.DataFrame(benchmark_data_additional)

# # Plot the new data
# fig, ax = plt.subplots(2, 1, figsize=(10, 10))

# # Plot 1: Min, Max, and Mean values for additional benchmarks
# ax[0].plot(df_additional['benchmark'], df_additional['min'], label="Min", marker='o')
# ax[0].plot(df_additional['benchmark'], df_additional['max'], label="Max", marker='o')
# ax[0].plot(df_additional['benchmark'], df_additional['mean'], label="Mean", marker='o')
# ax[0].set_title('Benchmark Performance: Min, Max, and Mean (100x100 Grid)')
# ax[0].set_xlabel('Benchmark')
# ax[0].set_ylabel('Time (seconds)')
# ax[0].legend()
# ax[0].tick_params(axis='x', rotation=45)

# # Plot 2: Min (+) values for additional benchmarks
# ax[1].plot(df_additional['benchmark'], df_additional['min_plus'], label="Min (+)", marker='o')
# ax[1].plot(df_additional['benchmark'], df_additional['max_plus'], label="Max (+)", marker='o')
# ax[1].plot(df_additional['benchmark'], df_additional['mean_plus'], label="Mean (+)", marker='o')
# ax[1].set_title('Benchmark Performance (+): Min, Max, and Mean (100x100 Grid)')
# ax[1].set_xlabel('Benchmark')
# ax[1].set_ylabel('Time (seconds)')
# ax[1].legend()
# ax[1].tick_params(axis='x', rotation=45)

# plt.tight_layout()
# plt.savefig('benchmark_performance100.png', dpi=300)
# plt.show()


