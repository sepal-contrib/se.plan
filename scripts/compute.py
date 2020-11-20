import ipyvuetify as v
from traitlets import Unicode


def add_area(feature):
    return feature.set({'rp_area': feature.geometry().area()})

def sum_up(aoi_io, layer_io, output):
    
    # compute the surface
    ee_fc = aoi_io.get_aoi_ee()
    ee_fc_area = ee_fc.map(add_area)
    
    area = ee_fc_area.first().getInfo()['properties']['rp_area']/10**6
    
    # only display the layers that have a weight > 0 
    li_str = ''
    
    for item in layer_io.layer_list:
        if item['weight'] != 0:
            li = f"<li>{item['name']} using <b>{item['layer']}</b> with a weight of <b>{item['weight']}</b></li>"
        else:
            li = ''
        
        li_str += li
    
    txt = f"""
        <div>
            <p>
                You're about to launch a computation on a AOI that represents <b>{area:.2f}</b> km\u00B2. You will use the following layers : 
            <p>
            <ul>
                {li_str}
            </ul>
            
            <p>
                If you agree with these input you can start the downloading, if not please change the inputs in the previous tiles
            </p>
        </div>
    """
    
    #create a Html widget
    class MyHTML(v.VuetifyTemplate):
        template = Unicode(txt).tag(sync=True)
    
    
    output.add_msg(MyHTML(), 'warning')
    
    return
    