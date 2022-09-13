from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.io import curdoc
from bokeh.themes import built_in_themes, Theme
from bokeh.models import ColumnDataSource, Grid, LinearAxis, Plot, Text, Span
from datetime import datetime
import os
from flask import current_app


def make_chart(dates_list, temp_data_list, sleep_data_list):
    # Temperature circles
    fig1=figure(toolbar_location=None,tools='xwheel_zoom,xpan',active_scroll='xwheel_zoom',
            x_range=(dates_list[-7],dates_list[-1]),
            y_range=(-10,110),sizing_mode='stretch_width', height=400)

    fig1.circle(dates_list,temp_data_list, 
        legend_label="Temperature (F)", 
        fill_color='#c77711', 
        line_color=None,
        size=20)

    source1 = ColumnDataSource(dict(x=dates_list, y=temp_data_list, text=temp_data_list)) # data
    glyph1 = Text(text="text",text_font_size={'value': '10px'},x_offset=-10, y_offset=5) # Image
    fig1.add_glyph(source1, glyph1)

#sleep rectangle label
    fig1.square(dates_list, sleep_data_list, legend_label = 'Oura Sleep Score', size=20, color="olive", alpha=0.5)
    
    source4 = ColumnDataSource(dict(x=dates_list, y=sleep_data_list,
        text=sleep_data_list))
    glyph4 = Text(text="text",text_font_size={'value': '10px'},x_offset=-5, y_offset=5)
    fig1.add_glyph(source4, glyph4)

    fig1.ygrid.grid_line_color = None
    fig1.yaxis.major_label_text_color = None
    fig1.yaxis.major_tick_line_color = None
    fig1.yaxis.minor_tick_line_color = None

    fig1.legend.background_fill_color = "#578582"
    fig1.legend.background_fill_alpha = 0.2
    fig1.legend.border_line_color = None
    theme_1=curdoc().theme = Theme(filename=os.path.join(current_app.static_folder, 'chart_theme_2.yml'))

    script1, div1 = components(fig1, theme=theme_1)

    cdn_js=CDN.js_files

    return script1, div1, cdn_js