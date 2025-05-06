import pandas as pd
import numpy as np
import altair as alt
import io
import os
import IPython.display as disp
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

def get_svg(graph):
	# Export svg data
	svg = io.StringIO()
	graph.save(svg, format = "svg")

	# Append our patterns
	svgdata = svg.getvalue()
	svgdata = svgdata.replace('</svg>', pattern_svg + '</svg>')

	# Render for preview
	disp.display(disp.SVG(svgdata))

	return svgdata

# IPC_STATS_FOLDER = './ipc_stats'
INST_STATS_FOLDER = './VM-Bench/inst_stats'
OUTPUT_FOLDER = './output'
THP = 'never'

parser = argparse.ArgumentParser()
parser.add_argument('--input')
parser.add_argument('--output')
parser.add_argument('--thp')
args = parser.parse_args()

fontSize = 20

if args.input:
    INST_STATS_FOLDER = args.input
if args.output:
    OUTPUT_FOLDER = args.output
if args.thp:
    THP = args.thp

if THP != 'never' and THP != 'always':
    raise ValueError("THP must be 'never' or 'always'")

if THP == 'never':
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    df = pd.read_csv(f"{INST_STATS_FOLDER}/kern_inst_{THP}_unified.csv")
    df["workload"] = df["workload"].str.replace("Sysbench", "Sysbench")

    # Pattern Description
    # Must be in a seperate cell
    # Must run each generation

    pattern_svg = '''
    <defs>

        <!-- Just play with it to get more -->

        <pattern id="diagonal_up_left" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(-45)">
            <line x1="0" y="0" x2="0" y2="5" stroke="#000000" stroke-width="1" />
        </pattern>

        <pattern id="diagonal_up_right" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(45)">
            <line x1="0" y="0" x2="0" y2="5" stroke="#000000" stroke-width="1" />
        </pattern>

        <pattern id="cross_hatch" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(45)">
            <line x1="0" y="0" x2="5" y2="0" stroke="#000000" stroke-width="1" />
            <line x1="0" y="0" x2="0" y2="5" stroke="#000000" stroke-width="1" />
        </pattern>

    </defs>
    '''

    function_sort_list = ["Page Faults", "khugepaged (THP)", "System Calls", "Timers", "Others"]
    orderExpr = '{"Page Faults": 0, "khugepaged (THP)": 1, "System Calls": 2, "Timers": 3, "Others": 4}[datum.function]'

    colors = ['#96ceb4', '#ffcc5c','#ff6f69', '#1D3557', '#808080']
    function_sort = ["BFS", "DFS", "DC", "SSSP", "GUPS", "Redis"]

    pic_width = 460
    pic_height = 280

    # This is the same as writing "labelAngle = 0, grid = False, ..."
    # Here we just use the **axisConf dict expansion to save some copy-n-paste
    fontsize = 24
    XaxisConf = {
        "labelAngle": 320, 
        "labelAlign": "right",
        "grid": False, 
        "titleFontWeight": 400, 
        "domainColor": "black", 
        "tickColor": "black",
        "labelFontSize": fontSize,
        "titleFontSize": fontSize,
        "labelLimit": 300,
    }

    axisConf = {
        # "labelAngle": 320, 
        # "labelAlign": "right",
        "grid": False, 
        "titleFontWeight": 400, 
        "domainColor": "black", 
        "tickColor": "black",
        "labelFontSize": fontSize,
        "titleFontSize": fontSize,
        "tickCount": 5
    }

    # Create the underlying layer with only color bars
    colorlayer = alt.Chart(df).transform_calculate(
        order=orderExpr
    ).mark_bar(
        stroke='black',       # Sets the color of the outline
        strokeWidth=1
    ).encode(
        xOffset = alt.XOffset("system:N", sort=["x86", "ECPT"], title=None), # offset by system

        # x = alt.X("workload:N").title(None) # each group plots systems
        # 	.axis(alt.Axis(title = None, **axisConf)),
        x = alt.X("workload:N", title=None, sort=function_sort) # each group plots systems
            .axis(alt.Axis(title = None, **XaxisConf)),

        y = alt
            .Y("instruction:Q").aggregate("sum") # Y is the sum of insn counts
            .axis(alt.Axis(title = "Norm. # instructions", **axisConf)), # give a name

        color = alt
            .Color("function:N", sort=function_sort_list) # select color by function name
            .scale(alt.Scale(range=colors)) # color scheme
            .legend(None),

        order=alt.Order("order:O", sort="descending"),
    ).properties(
        width=pic_width,
        height=pic_height
    )


    # Create the pattern layer with only shades
    patternlayer = colorlayer.mark_bar().encode(
        fill = alt
            .Fill("system:N", sort=["x86", "ECPT"], title=None) # select pattern by system name
            .scale(alt.Scale(range=['', 'url(#diagonal_up_left)'])) # pattern scheme
            .legend(None)
            # .legend(orient = "top", title = None),
    )

    # Merge the two layers and set the font and image border
    final = (colorlayer + patternlayer).configure(
        font = "Times New Roman"
    ).configure_view(
        stroke = "black",
        strokeWidth = 1
    ).configure_axis(
        labelFontSize=fontsize,
        titleFontSize=fontsize
    ).configure_legend(
        titleFontSize=fontsize - 2,
        labelFontSize=fontsize - 2
    ) 

    # Preview and save
    svg = get_svg(final)
    with open(f"{OUTPUT_FOLDER}/kern_inst_unified_{THP}.svg", "w") as f:
        f.write(svg)

    svg2pdf(f"{OUTPUT_FOLDER}/kern_inst_unified_{THP}.svg")
else:
    thp = 'always'
    # tag = '_harsh_iterator'
    # tag = ''
    # df_always = pd.read_csv(f"kern_inst_{thp}.csv")
    # df_always = pd.read_csv(f"kern_inst_{thp}_with_khugepaged.csv")
    df_always = pd.read_csv(f"{INST_STATS_FOLDER}/kern_inst_{thp}_unified.csv")
    df_always['workload'] = df_always['workload'].str.replace('Sysbench', 'Sysbench')
    
    # Pattern Description
    # Must be in a seperate cell
    # Must run each generation

    pattern_svg = '''
    <defs>

        <!-- Just play with it to get more -->

        <pattern id="solid_fill" patternUnits="userSpaceOnUse" width="10" height="10">
            <rect x="0" y="0" width="4" height="4" fill="#FF5733" />
        </pattern>

        <pattern id="diagonal_up_left" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(-45)">
            <line x1="0" y="0" x2="0" y2="5" stroke="#000000" stroke-width="1" />
        </pattern>

        <pattern id="diagonal_up_right" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(45)">
            <line x1="0" y="0" x2="0" y2="5" stroke="#000000" stroke-width="1" />
        </pattern>

        <pattern id="cross_hatch" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(45)">
            <line x1="0" y="0" x2="5" y2="0" stroke="#000000" stroke-width="1" />
            <line x1="0" y="0" x2="0" y2="5" stroke="#000000" stroke-width="1" />
        </pattern>

    </defs>
    '''
    function_sort_list = ["Page Faults", "khugepaged (THP)", "System Calls", "Timers", "Others"]
    orderExpr = '{"Page Faults": 0, "khugepaged (THP)": 1, "System Calls": 2, "Timers": 3, "Others": 4}[datum.function]'

    colors = ['#96ceb4', '#ffcc5c','#ff6f69', '#1D3557', '#808080']
    function_sort = ["BFS", "DFS", "DC", "SSSP", "GUPS", "Redis"]

    pic_width = 460
    pic_height = 280

    legendRect = "M -1 -0.4 L -1 0.4 L 1 0.4 L 1 -0.4 L -1 -0.4"

    # This is the same as writing "labelAngle = 0, grid = False, ..."
    # Here we just use the **axisConf dict expansion to save some copy-n-paste
    fontsize = 24
    XaxisConf = {
        "labelAngle": 320, 
        "labelAlign": "right",
        "grid": False, 
        "titleFontWeight": 400, 
        "domainColor": "black", 
        "tickColor": "black",
        "labelFontSize": fontSize,
        "titleFontSize": fontSize,
    }

    axisConf = {
        # "labelAngle": 320, 
        # "labelAlign": "right",
        "grid": False, 
        "titleFontWeight": 400, 
        "domainColor": "black", 
        "tickColor": "black",
        "labelFontSize": fontSize,
        "titleFontSize": fontSize,
    }


    # Create the underlying layer with only color bars
    colorlayer = alt.Chart(df_always).transform_calculate(
        order=orderExpr
    ).mark_bar(
        stroke='black',       # Sets the color of the outline
        strokeWidth=1
    ).encode(
        xOffset = alt.XOffset("system:N", sort=["x86", "ECPT"], title=None), # offset by system

        # x = alt.X("workload:N").title(None) # each group plots systems
        # 	.axis(alt.Axis(title = None, **axisConf)),
        x = alt.X("workload:N", title=None, sort=function_sort) # each group plots systems
            .axis(alt.Axis(title = None, **XaxisConf)),

        y = alt
            .Y("instruction:Q").aggregate("sum") # Y is the sum of insn counts
            .axis(alt.Axis(title = "Norm. # instructions", **axisConf)), # give a name

        color = alt
            .Color("function:N", sort=function_sort_list) # select color by function name
            .scale(alt.Scale(range=colors)) # color scheme
            .legend(None),

        order=alt.Order("order:O", sort="descending"),
    ).properties(
        width=pic_width,
        height=pic_height
    )


    # Create the pattern layer with only shades
    patternlayer = colorlayer.mark_bar().encode(
        fill = alt
            .Fill("system:N", sort=["x86", "ECPT"], title=None) # select pattern by system name
            .scale(alt.Scale(range=['', 'url(#diagonal_up_left)'])) # pattern scheme
            .legend(None)
            # .legend(orient = "top", title = None),
    )

    # Merge the two layers and set the font and image border
    final = (colorlayer + patternlayer).configure(
        font = "serif"
    ).configure_view(
        stroke = "black",
        strokeWidth = 1
    ).configure_axis(
        labelFontSize=fontsize,
        titleFontSize=fontsize
    ).configure_legend(
        titleFontSize=fontsize - 2,
        labelFontSize=fontsize - 2
    ) 

    # Preview and save
    svg = get_svg(final)
    with open(f"{OUTPUT_FOLDER}/kern_inst_unified_{thp}.svg", "w") as f:
        print(f"{OUTPUT_FOLDER}/kern_inst_unified_{thp}.svg")
        f.write(svg)

    svg2pdf(f"{OUTPUT_FOLDER}/kern_inst_unified_{thp}.svg")

