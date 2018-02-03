import math
import random
import re
from PIL import Image
import requests
import urllib.request as request
from io import BytesIO

topics = ['biochemistry','stoichiometry','lewis structures','VSEPR',\
'bohr','NMR spectroscopy','ionization','oxidation','alkali metals',\
'dimagnetic','dipole','valence','black body radiation','Bohr','wave function','Carbon'\
,'Gerard Parkin','atom', 'orbitals', 'robert millikan', 'John Dalton']

max_per_topic = 20
search_engines = {'google' : ['https://www.google.com/search?tbm=isch&q=','&sout=1&start=','','src="(.*?gstatic.*?)"',[':','.jpg']],
            'bing': ['https://www.bing.com/images/async?q=', '&async=content&first=','&adlt=off&qft=+filterui:color2-FGcls_','imgurl:&quot;(.*?)&quot;',['/','']]}
def get_image_dict (search_term, engine = 'google', verbose = True):#grab urls with corresponding rgb averages
    col_dict = {(0,0,0) : {},(255,0,0): {}, (0,255,0):{}, (0,0,255) : {}}#faster building of images by presorting euclidian into major axes
    user_agent_header = {'User-Agent' : 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0'}
    e_syntax = search_engines[engine]
    for i,topic in enumerate(topics):
        page_num = 1
        if verbose: print("downloading " + str(i+1) + " of " + str(len(topics)) + " topics")
        request_url = e_syntax[0] + topic + '+' + search_term + e_syntax[1] + str(page_num)\
        + e_syntax[2] + (topic if engine == 'bing' else '')
        response = requests.get(request_url, headers=user_agent_header)
        if response.status_code != 200:
            print(response.text, response.status)
            break
        links = re.findall(e_syntax[3], response.text)
        if (len(links)>max_per_topic): links = links[:max_per_topic]
        for link in links:
            try:
                avg_color_key = get_region_color(Image.open(BytesIO(request.urlopen(link).read())))
                if (avg_color_key != None):
                    temp = col_dict[nearest_color(avg_color_key, col_dict.keys())]
                    if avg_color_key in temp: temp[avg_color_key].append(link)
                    else: temp[avg_color_key] = [link]
            except:
                continue
    return col_dict

def get_region_color(region):
    #split into RGB channels and return average color
    hist = region.histogram()
    if len(hist) == 256: return None
    return tuple([0 if j==0 else int(sum(map(lambda x: x[0]*x[1], zip(i,range(256))))/j)\
            for i,j in map(lambda x: [x,sum(x)],\
            [hist[256*k:256*(k+1)] for k in range(3)])])

def nearest_color(color1, colors):
    # euclidean distance between the available colors
    min_dist = float("inf")
    for c in colors:
        euc_dist = math.sqrt(sum(map(lambda x: (x[0]-x[1])**2, zip(color1,c))))
        if euc_dist < min_dist: nearest_col, min_dist = c, euc_dist#min_dist = euc_dist
    return nearest_col

def get_color_order(image, region_size):
    grid_width = image.size[0]//region_size
    grid_height = image.size[1]//region_size
    color_order = []
    new_image = Image.new('RGB', image.size, (0, 255, 0))
    for ih in range(grid_height):
        for iw in range(grid_width):
            region = image.crop((iw*region_size, ih*region_size, iw*region_size+region_size, ih*region_size+region_size))
            color = get_region_color(region)
            patch = Image.new('RGB', (region_size, region_size), color)
            new_image.paste(patch, box=(iw*region_size, ih*region_size))
            color_order.append(color)
    return color_order

def build_image(search_term, block_size, base_image_filename, output_filename):

    img = Image.open(base_image_filename)
    img = img.resize(((img.size[0]//block_size)*block_size,(img.size[1]//block_size)*block_size), Image.ANTIALIAS)
    new_image = Image.new('RGB', img.size, (0, 255, 0))
    img_dict = get_image_dict(search_term)
    col_keys = img_dict.keys()
    for i, color in enumerate(get_color_order(img, block_size)):
        temp = img_dict[nearest_color(color, col_keys)]
        nearest = nearest_color(color, temp.keys())
        patch = Image.open(BytesIO(request.urlopen(temp[nearest][random.randint(0, len(temp[nearest])-1)]).read())).resize((block_size, block_size))
        bbox = ((i*block_size)%img.size[0], (i // (img.size[0]//block_size))*block_size)
        new_image.paste(patch, box=bbox)
        patch.close()
    new_image.save(output_filename)

def main(search_term, block_size, base_image_filename, output_filename):
    build_image(search_term, block_size, base_image_filename, output_filename)

if __name__ == '__main__':
    main('chemistry', 60,'chemistry.jpg','bnh2128mosaic.jpg')
