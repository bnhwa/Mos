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
def get_image_dict (search_term, col_dict, region_size, engine = 'google', verbose = True):#grab urls with corresponding rgb averages
    user_agent_header = {'User-Agent' : 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0'}
    e_syntax = search_engines[engine]
    print(region_size)
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
                img = Image.open(BytesIO(request.urlopen(link).read())).resize((region_size,region_size), Image.ANTIALIAS)
                avg_color_key = get_avg_color(img)
                if (avg_color_key != None):
                    col_dict[nearest_color(avg_color_key,col_dict.keys())].append(img)
            except:
                continue
    return {k: v for k, v in col_dict.items() if v}#deal with empty keys

def get_avg_color(region):
    #split into RGB channels and return average color
    hist = region.histogram()
    if len(hist) == 256: return None
    return tuple([0 if j==0 else int(sum(map(lambda x: x[0]*x[1], zip(i,range(256))))/j)\
            for i,j in map(lambda x: [x,sum(x)],\
            [hist[256*k:256*(k+1)] for k in range(3)])])
    
def nearest_color(color, colors, thresh=0):
    # find color with nearest euclidean distance among array
    min_dist = float("inf")
    for c in colors:
        euc_dist = math.sqrt(sum(map(lambda x: (x[0]-x[1])**2, zip(color,c))))#euclidean_dist(color, c)
        if euc_dist < min_dist: nearest_col, min_dist = c, euc_dist
    if thresh!=0 and min_dist > thresh:
        colors.append(color)
        return color
    return nearest_col

def get_image_cols(search_term, image, region_size, thresh=0):
    #assuming its already resized, return color array of img and dict of thresholded colors
    common_cols = []
    grid_width = image.size[0]//region_size
    grid_height = image.size[1]//region_size
    return [nearest_color(get_avg_color(image.crop((\
    rw*region_size, rh*region_size, rw*region_size+region_size,\
    rh*region_size+region_size))),common_cols, thresh=thresh)\
    for rh in range(grid_height) for rw in range(grid_width)],\
    get_image_dict(search_term,{i:[] for i in common_cols},region_size)

def build_image(search_term, block_size, base_image_filename, output_filename, thresh = 0):

    img = Image.open(base_image_filename)
    img = img.resize(((img.size[0]//block_size)*block_size,(img.size[1]//block_size)*block_size), Image.ANTIALIAS)
    new_image = Image.new('RGB', img.size, (0, 255, 0))
    img_arr, col_dict = get_image_cols(search_term, img, block_size,thresh = thresh)
    print("Done fetching subimage urls, assembling image")
    for i, color in enumerate(img_arr):
        nearest = nearest_color(color, col_dict.keys())
        patch = col_dict[nearest][random.randint(0, len(col_dict[nearest])-1)].copy()
        new_image.paste(patch, box=((i*block_size)%img.size[0], (i // (img.size[0]//block_size))*block_size))
        patch.close()
    new_image.save(output_filename)

def main(search_term, block_size, base_image_filename, output_filename):
    build_image(search_term, block_size, base_image_filename, output_filename, thresh = 10)

if __name__ == '__main__':
    main('chemistry', 30,'chemistry.jpg','bnh2128mosaic.jpg')
