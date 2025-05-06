import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import math
import shutil
import os
import argparse
from subprocess import Popen

def svg2pdf(src):
    dst = src.replace('.svg', '.pdf')
    print('Rendering: ', src, ' -> ', dst)
    x = Popen(['inkscape', src, \
        '--export-filename=%s' % dst])
    try:
        waitForResponse(x)
    except:
        return False

def waitForResponse(x): 
    out, err = x.communicate() 
    if x.returncode < 0: 
        r = "Popen returncode: " + str(x.returncode) 
        raise OSError(r)
    
def post_process(ax, ylabel, sheetX, sheetY, datasheet, datadiv, transpose, name, yformat, ylabel_offset=0.22):
	_datasheet = datasheet.copy()
	_sheetY = sheetY.copy()
	# shape = datasheet.shape
	# datasheet = datasheet / datadiv[:,None]
	# datasheet = datasheet.reshape(shape)
	print(_datasheet)
	radix_speedup = _datasheet[:, 0] / _datasheet[:, 0]
	ecpt_speedup = _datasheet[:, 0] / _datasheet[:, 1]
	print(max(ecpt_speedup))
	print(min(ecpt_speedup))
 
	geo_mean = math.exp(np.mean(np.log(ecpt_speedup)))
	# print(geo_mean)
	# _datasheet[:, 0] = radix_speedup
	# _datasheet[:, 1] = ecpt_speedup
	# print(_datasheet)
	# _datasheet = np.vstack((_datasheet, np.array([[np.mean(radix_speedup), np.mean(ecpt_speedup)]])))
	_datasheet = np.vstack((np.column_stack((radix_speedup, ecpt_speedup)), np.array([[np.mean(radix_speedup), np.mean(ecpt_speedup)]])))
	_sheetY.append("Mean")

	print(_datasheet)
	maxY = np.amax(_datasheet) * heightMargin

	if transpose:
		_datasheet = _datasheet.T
		(_sheetY, sheetX) = (sheetX, _sheetY)

	df = pd.DataFrame(_datasheet, columns = sheetX, index = _sheetY)
	df.plot(ax = ax, kind = 'bar', legend = False, width = barWidth)

	colors = color[0 : len(sheetX)]

	bars = ax.patches
	colors = [item for item in colors for i in range(len(df))]

	for bar, clr in zip(bars, colors): # set bar style
		bar.set_facecolor(clr[0])
		bar.set_edgecolor(clr[1])
		bar.set_hatch(clr[2])

	# ax.set_xlabel(name) # clear x label
	ax.set_ylabel(ylabel, fontsize = fontSize - 2)
	
	ax.set_ylim([0, maxY])
	ax.yaxis.set_label_coords(-0.11, ylabel_offset)
	#ax.grid(axis = 'y', linestyle = 'dotted') # add horizental grid lines
	ax.locator_params(nbins=8, axis='y') # plot more y ticks
	ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter(yformat))

	ax.tick_params(axis="x", labelsize=fontSize - 6) # prevent x labels from displayed vertically
	plt.setp(ax.xaxis.get_majorticklabels(), rotation=40, ha="right", rotation_mode="anchor") 
      
IPC_STATS_FOLDER = './ipc_stats'
# INST_STATS_FOLDER = './VM-bench/inst_stats'
OUTPUT_FOLDER = './output'
THP = 'never'

archs = ['RADIX', 'ECPT']

parser = argparse.ArgumentParser()
parser.add_argument('--input', default='./ipc_stats')
# parser.add_argument('--inst_stats', default='./VM-bench/inst_stats')
parser.add_argument('--output', default='./output')
parser.add_argument('--thp', default='never')
args = parser.parse_args()

if args.input:
    IPC_STATS_FOLDER = args.input
if args.output:
    OUTPUT_FOLDER = args.output
if args.thp:
	THP = args.thp
if THP != 'never' and THP != 'always':
	raise ValueError("THP must be 'never' or 'always'")

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ylabel2 = "Page Walk speedup"
sheetX2 = archs
sheetY2 = ["BFS", "DFS", "DC", "SSSP", "GUPS", "Redis"]
df_unified_radix_result = pd.read_csv(os.path.join(IPC_STATS_FOLDER, f'ipc_unified_{THP}_radix_result.csv'))
df_unified_ecpt_result = pd.read_csv(os.path.join(IPC_STATS_FOLDER, f'ipc_unified_{THP}_ecpt_result.csv'))
radix_page_walk_latency_4KB = df_unified_radix_result['page_walk_latency'].values
radix_ipc_4KB = df_unified_radix_result['ipc'].values
radix_E2E_4KB = df_unified_radix_result['total_cycles'].values
ecpt_page_walk_latency_4KB = df_unified_ecpt_result['page_walk_latency'].values
ecpt_ipc_4KB = df_unified_ecpt_result['ipc'].values
ecpt_E2E_4KB = df_unified_ecpt_result['total_cycles'].values
datasheet2 = np.column_stack((np.array(radix_page_walk_latency_4KB), np.array(ecpt_page_walk_latency_4KB)))
print(datasheet2)
datadiv2 = np.ones_like(len(sheetY2))
transpose2 = False
name2 = 'Page walk speedup'
yformat2 = '%.1f'

# ========== THP page walk speedup ========== #
ylabel1 = "IPC speedup"
sheetX1 = [
    'EMT-Radix', 
    'EMT-ECPT', 
]
sheetY1 = sheetY2.copy()
datasheet1 = np.column_stack((1/np.array(radix_ipc_4KB), 1/np.array(ecpt_ipc_4KB)))
datadiv1 = np.array(np.ones_like(len(sheetY1)))
transpose1 = False
name1 = 'THP page walk speedup'
yformat1 = '%.1f'

ylabel3 = "Total Cycles Reduction"
sheetX3 = [
    'EMT-Radix', 
    'EMT-ECPT', 
]
sheetY3 = sheetY2.copy()
datasheet3 = np.column_stack((1 / np.array(radix_E2E_4KB), 1 / np.array(ecpt_E2E_4KB)))
datadiv3 = np.array(np.ones_like(len(sheetY3)))
transpose3 = False
name3 = 'THP page walk speedup'
yformat3 = '%.1f'
# print(datasheet3)

filename = os.path.join(OUTPUT_FOLDER, 'ecpt.svg')

# release mode (generate pdf and copy mkplot)
releasePdf = True
releaseSrc = False

# color of each bar (bar clrs, texture clrs, texture)
# count >= len(sheetX), redundant colors will be ignored
# available texture: ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']
color = [
    ['#808080', '#000000', None], # Vanilla
    ['#96ceb4', '#000000', None], # Hyperlane
]

# % width of the bar group
barWidth = 0.8

# folder of the exported file
folder = OUTPUT_FOLDER

# rows of legends
legendRows = 1

# plot size
plotSize = (8, 3.75)

# font size
fontSize = 20
fontName = 'serif'

# pad image height by this value, used to save space for the legend
heightMargin = 1.1

# legend offset, used to adjust legend's place on plot
legendOffset = 0.95

# legend width, relative to figure width
legendWidth = 0.7

legendSpacing = 10

plt.rcParams.update({ 'font.size': fontSize, 'font.family': fontName })

fig, ax = plt.subplots(1, 1, figsize = plotSize)

fig.tight_layout()

# 4KB page walk latency
post_process(ax, ylabel2, sheetX2, sheetY2, datasheet2, datadiv2, transpose2, name2, yformat2)
# fig.savefig(filename, bbox_inches="tight")
# legend and output

handles, labels = ax.get_legend_handles_labels()
colCount = math.ceil(len(sheetX1) / legendRows)

fig.legend(handles, labels, # create legend, use plt.legend to create global legend
		bbox_to_anchor = ((1 - legendWidth) / 2, legendOffset, legendWidth, .102), # (x0, y0, width, height)
		loc = 'lower left',
		ncol = colCount,
		mode = 'expand',
		borderaxespad = 0.,
		frameon = False,
		prop = { 'size': fontSize - 6 },
	)

filename = f"ecpt_pgwalk_THP.svg"
if releasePdf:
	path = folder + '/' + filename
	fig.savefig(path, bbox_inches="tight")
	svg2pdf(path)


if releaseSrc:
	path = folder + '/' + filename
	raw = path + ".ipynb"
	if os.path.exists(raw):
		os.remove(raw)
	shutil.copyfile("mkplot.ipynb", raw)
      
# image layout

fig2, ax2 = plt.subplots(1, 1, figsize = plotSize)

fig2.tight_layout()

# 4KB page walk latency
post_process(ax2, ylabel1, sheetX1, sheetY1, datasheet1, datadiv1, transpose1, name1, yformat1)

# post_process(ax[1], ylabel1, sheetX1, sheetY1, datasheet1, datadiv1, transpose1, name1, yformat1)

# fig.text(0.215, -0.13, "(a) 4KB", fontsize=fontSize + 2, weight='bold', fontfamily='Times New Roman')
# fig.text(0.700, -0.13, "(b) THP", fontsize=fontSize + 2, weight='bold', fontfamily='Times New Roman')

# legend and output

handles, labels = ax2.get_legend_handles_labels()
colCount = math.ceil(len(sheetX1) / legendRows)

fig2.legend(handles, labels, # create legend, use plt.legend to create global legend
		bbox_to_anchor = ((1 - legendWidth) / 2, legendOffset, legendWidth, .001), # (x0, y0, width, height)
		loc = 'lower left',
		ncol = colCount,
		mode = 'expand',
		borderaxespad = 0.,
		frameon = False,
		prop = { 'size': fontSize - 6 },
	)

filename = f"ecpt_ipc_{THP}.svg"
if releasePdf:
	path = folder + '/' + filename
	fig2.savefig(path, bbox_inches="tight")
	svg2pdf(path)


if releaseSrc:
	path = folder + '/' + filename
	raw = path + ".ipynb"
	if os.path.exists(raw):
		os.remove(raw)
	shutil.copyfile("mkplot.ipynb", raw)
      
# image layout

fig3, ax3 = plt.subplots(1, 1, figsize = plotSize)

fig3.tight_layout()

# 4KB page walk latency
post_process(ax3, ylabel3, sheetX3, sheetY3, datasheet3, datadiv3, transpose3, name3, yformat3)

# post_process(ax[1], ylabel1, sheetX1, sheetY1, datasheet1, datadiv1, transpose1, name1, yformat1)

# fig.text(0.215, -0.13, "(a) 4KB", fontsize=fontSize + 2, weight='bold', fontfamily='Times New Roman')
# fig.text(0.700, -0.13, "(b) THP", fontsize=fontSize + 2, weight='bold', fontfamily='Times New Roman')

# legend and output

handles, labels = ax3.get_legend_handles_labels()
colCount = math.ceil(len(sheetX1) / legendRows)

# fig3.legend(handles, labels, # create legend, use plt.legend to create global legend
# 		bbox_to_anchor = ((1 - legendWidth) / 2, legendOffset, legendWidth, .102), # (x0, y0, width, height)
# 		loc = 'lower left',
# 		ncol = colCount,
# 		mode = 'expand',
# 		borderaxespad = 0.,
# 		frameon = False,
# 		prop = { 'size': fontSize - 6 },
# 	)

filename = f"ecpt_e2e_{THP}.svg"
if releasePdf:
	path = folder + '/' + filename
	fig3.savefig(path, bbox_inches="tight")
	svg2pdf(path)


if releaseSrc:
	path = folder + '/' + filename
	raw = path + ".ipynb"
	if os.path.exists(raw):
		os.remove(raw)
	shutil.copyfile("mkplot.ipynb", raw)

