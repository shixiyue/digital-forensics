from PIL import Image, ImageChops, ImageEnhance
import sys, os
import threading
import argparse

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage,AnnotationBbox
import matplotlib.cm as mplcm

import numpy as np
from scipy.fftpack import dct
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial import distance as ssd

import pandas as pd
import seaborn as sns

import uuid

import cv2

def get_names(fname, orig_dir, save_dir):
    TMP_EXT = ".tmp_ela.jpg"
    ELA_EXT = ".ela.png"
    
    basename, ext = os.path.splitext(fname)

    org_fname = os.path.join(orig_dir, fname)
    tmp_fname = os.path.join(save_dir, basename + TMP_EXT)
    ela_fname = os.path.join(save_dir, basename + ELA_EXT)

    return org_fname, tmp_fname, ela_fname

def flatten_rgba(im):
    """
    for removing alpha channel (to allow saving in JPEG for ELA)
    from https://stackoverflow.com/questions/9166400/convert-rgba-png-to-rgb-with-pil
    """
    im.load() # required for png.split()

    background = Image.new("RGB", im.size, (255, 255, 255))
    background.paste(im, mask=im.split()[3]) # 3 is the alpha channel

    return background

def ela(fname, orig_dir, save_dir, quality=35):
    """
    Generates an ELA image on save_dir.
    Params:
        fname:      filename w/out path
        orig_dir:   origin path
        save_dir:   save path
    
    Adapted from:
    https://gist.github.com/cirocosta/33c758ad77e6e6531392
    """
    org_fname, tmp_fname, ela_fname = get_names(fname, orig_dir, save_dir)

    im = Image.open(org_fname)
    if im.mode == "RGBA":
        im = flatten_rgba(im)
    im.save(tmp_fname, 'JPEG', quality=quality)

    tmp_fname_im = Image.open(tmp_fname)
    ela_im = ImageChops.difference(im, tmp_fname_im)

    extrema = ela_im.getextrema()
    if isinstance(extrema[0], int):
        max_diff = max(extrema)
    else:
        max_diff = max([ex[1] for ex in extrema])
    scale = 255.0/max_diff
    ela_im = ImageEnhance.Brightness(ela_im).enhance(scale)

    ela_im.save(ela_fname)
    os.remove(tmp_fname)
    
def img_to_jpg(fname, orig_dir): 
    fpath = os.path.join(orig_dir, fname)
    jpg_name = "{}.jpg".format(os.path.splitext(fname)[0])
    jpg_path = os.path.join(orig_dir, jpg_name)
    
    img = Image.open(fpath)
    rgb_img =img.convert('RGB')
    rgb_img.save(jpg_path)
    return jpg_name 

def run_ela(DIRECTORY, SAVE_REL_DIR='ela_results', QUALITY=35):
    threads = []

    ela_dirc = os.path.join(DIRECTORY, SAVE_REL_DIR)
    print("results file:", ela_dirc)
    if not os.path.exists(ela_dirc):
        os.makedirs(ela_dirc)

    filelist = []
    for d in os.listdir(DIRECTORY):
        if d.endswith(".jpg") or d.endswith(".jpeg") or d.endswith(".tif") or d.endswith(".tiff"):
            filelist.append(d)
            thread = threading.Thread(target=ela, args=[d, DIRECTORY, ela_dirc, QUALITY])
            threads.append(thread)
            thread.start()
        elif d.endswith(".png"):
            d = img_to_jpg(d, DIRECTORY)
            filelist.append(d)
            thread = threading.Thread(target=ela, args=[d, DIRECTORY, ela_dirc, QUALITY])
            threads.append(thread)
            thread.start()
    for t in threads:
        t.join()

    return filelist, ela_dirc

def apply_cmap(img, cmap=mplcm.autumn):
    lut = np.array([cmap(i)[:3] for i in np.arange(0,256,1)])
    lut = (lut*255).astype(np.uint8)
    channels = [cv2.LUT(img, lut[:, i]) for i in range(3)]
    img_color = np.dstack(channels)
    return img_color

def show_ela(filelist, DIRECTORY, ela_dirc):
    if len(filelist) == 0:
        print(DIRECTORY, "has no images!")
        im_original = None
    for f in filelist:
        fp_original, tmp_fname, fp_ela = get_names(f, DIRECTORY, ela_dirc)

        im_original = mpimg.imread(fp_original)
        im_ela = mpimg.imread(fp_ela)
        try:
            im_gray = cv2.cvtColor(im_original, cv2.COLOR_BGR2GRAY)
        except:
            im_gray = im_original
            
        fig = plt.figure(figsize=(60,80))
        a = fig.add_subplot(4, 3, 1)
        a.set_title(f"ORIGINAL: {DIRECTORY}{f}")
        #imgplot.set_clim(0.0, 0.7)
        #plt.imshow(im_original)
        a = fig.add_subplot(4, 3, 2)
        #imgplot.set_clim(0.0, 0.7)
        #plt.imshow(im_ela)
        a.set_title("Error Level Analysis")
        colormaps = [mplcm.jet, mplcm.inferno, mplcm.hsv, mplcm.nipy_spectral, mplcm.gist_ncar, 
                     mplcm.gist_stern, mplcm.RdYlGn, mplcm.Spectral, mplcm.coolwarm, mplcm.gist_rainbow,
                    ]
        for idx,cm in enumerate(colormaps):
            im_color = apply_cmap(im_gray, cm)

            a = fig.add_subplot(4, 3, idx+3)
            #plt.imshow(im_color)
            a.set_title(f"False Color: {cm.name}")
            
        plt.tight_layout()
        plt.savefig(os.path.join(ela_dirc, f"{f}_summary.png"))
        plt.close()
    return im_original 

def get_savedir(target_fn):
    target_split = os.path.split(target_fn)
    target_parent = "{}/contour_analysis".format(target_split[0])
    target_savedir = "{}/contour_analysis/{}".format(target_split[0], os.path.splitext(target_split[1])[0])

    # create directory to save analysis files
    if os.path.exists(target_savedir):
        print("Target directory exists! Results will be overwritten")
    elif os.path.exists(target_parent):
        os.mkdir(target_savedir)
    else:
        os.mkdir(target_parent)
        os.mkdir(target_savedir)
    return target_savedir

def get_base_images(target_fn, crop=None):
    # create base images
    target_original = cv2.imread(target_fn)
    target_overlay = cv2.imread(target_fn)
    
    plt.imshow(target_original)
    # crop to specified region:
    if crop:
        target_original = target_original[crop[0]:crop[1], crop[2]:crop[3]]
        target_overlay =   target_overlay[crop[0]:crop[1], crop[2]:crop[3]]
    
    # check if color image
    im = Image.open(target_fn)
    print("MODE = ", im.mode)
    if im.mode  in ["RGB", "RGBA", "CMYK", "YCbCr", "LAB", "HSV"] :
        # create grey image
        target_grey = cv2.cvtColor(target_original, code = cv2.COLOR_BGR2GRAY)
    else:
        target_grey = target_original  # need to make a copy
        
    return target_original, target_overlay, target_grey

def get_binary(target_grey, thresh=200, maxval=255):
    blur_target = cv2.GaussianBlur(src = target_grey, 
                                    ksize = (5, 5), 
                                    sigmaX = 0.0,
                                  )
    (t, target_binary) = cv2.threshold(src = blur_target,
                                thresh = thresh,
                                maxval = maxval,
                                type = cv2.THRESH_BINARY
                               )
    return target_binary

def keep_contour(cnt, minarea=10, maxarea=1000, parent=0, skip_first=True):
    area = cv2.contourArea(cnt)
    if skip_first and parent != 0:
        return False
    else:
        if area < minarea or area > maxarea:
            return False
        else:
            return True

def contour_summary(contours, limit=400000):
    areas = []
    for c in contours:
        area = cv2.contourArea(c)
        areas.append(area)
    df_cnt = pd.DataFrame({"Area":areas})
    fig, ax = plt.subplots(figsize=(12,5))
    
    # remove exceptional outliers (eg, the image boundaries):
    if len(df_cnt[df_cnt.Area > df_cnt.Area.mean()]) ==1:
        print(f"Removing one exceptional outlier: {df_cnt.Area.max()}")
        df_sample = df_cnt[(df_cnt.Area < df_cnt.Area.mean()) &
                           (df_cnt.Area < limit)
                          ]
    else:
        df_sample = df_cnt[df_cnt.Area < limit]
    
    sns.swarmplot(data=df_sample, y="Area")
    plt.show()

def collect_contours(contours, hierarchy, minarea=100, maxarea=1000, skip_first=True):
    "collect all contours that are children of the image contour (the bounding box of the image)"
    print("Parameters:", minarea, maxarea)
    band_ids = []
    band_cts = []
    for idx,cnt in enumerate(hierarchy[0]):
        if keep_contour(contours[idx], minarea, maxarea, cnt[3], skip_first):
            band_ids.append(idx)
            band_cts.append(contours[idx])
    return band_ids, band_cts

def draw_contours(target_overlay, contours, target_savedir, color=(255, 0, 0)):
    # draw the countours
    target_contours = cv2.drawContours(image = target_overlay, 
                                        contours = contours, 
                                        contourIdx = -1, 
                                        color = color, 
                                        thickness = 1)
    fig = plt.figure(figsize=(10,15))
    plt.imshow(target_contours)
    for idx,cnt in enumerate(contours):
        (x,y),radius = cv2.minEnclosingCircle(cnt)
        plt.annotate(f"{idx}", (x,y), c='cyan')
    plt.savefig("{}/band_detection.png".format(target_savedir))
    return target_contours

def get_most_similar(df_matchDist, threshold=0.1):
    """
    from the distance matrix, identify all contour pairs who differ less than the threshold. 
    """
    df_filtered = df_matchDist[df_matchDist < threshold]
    df_reduced = df_filtered.dropna(how='all')
    
    close_contour_sets = {a:list(set(df_reduced.iloc[a,:].dropna().index.values)-set([a]))  for a in df_reduced.index }
    return close_contour_sets

def get_similar_bands(contours, target_savedir, target_original, target_grey, skip_first=True, colored=False):
    # create array of contour shapes
    df_matchDist = pd.DataFrame([ [cv2.matchShapes(c1,c2,1,0.0) for c1 in contours] for c2 in contours ])
    
    # plot clustermap of distances between contours
    g = sns.clustermap(data=df_matchDist, annot=True)
    plt.savefig("{}/band_clusters.png".format(target_savedir))
    plt.show()
    
    # filter for contours that are most similar
    close_contour_sets = get_most_similar(df_matchDist,  0.1)
    
    # get the re-ordered index:
    sorted_idx = g.dendrogram_row.reordered_ind

    # calculate dendrogram and distances using scipy
    Z = linkage(ssd.squareform(df_matchDist.values), method="average")

    # create bounding boxes for all bands
    # create all-black mask image
    target_mask = np.zeros(shape = target_original.shape, dtype = "uint8")

    # "cut out" shapes for all bands:
    band_images = {}
    for idx,c in enumerate(contours[skip_first:]):
        idx += skip_first # add one if we skipped the first contour (which can be the contour of the entire image)
        (x, y, w, h) = cv2.boundingRect(c)

        # draw rectangle in mask (currently unnecessary for workflow)
        cv2.rectangle(img = target_mask, 
                    pt1 = (x, y), 
                    pt2 = (x + w, y + h), 
                    color = (255, 255, 255), 
                    thickness = -1
                     )

        # crop to bounding box of band: 
        if y - 5 < 0:
            stretched_y = 0
        else:
            stretched_y = y - 5 
        if colored:
            band_images[idx] = target_original[stretched_y : y + h + 5, x : x + w, :] # for colored images
        else:
            band_images[idx] = target_grey[stretched_y : y + h + 5, x : x + w] # add 5px to y axis each way
    return df_matchDist, Z, band_images, sorted_idx, close_contour_sets

def plot_colored_bands(sorted_idx, band_images, target_savedir):
    """
    plot ordered set of band images
    
    sorted_idx:     list of images to draw
    band_images:    dict. where each value is an image array
    target_savedir: directory to save figure. Set to None if you don't
                    want to save image.
    """
    # filter list to keep only indicies present in band_images:
    idx_filtered = [ i for i in sorted_idx if i in band_images ]
    
    # plot figure
    fig = plt.figure(figsize=(30,120))
    for idx,bid in enumerate(idx_filtered):
        a = fig.add_subplot(30, 10, idx+1)
        a.set_title(f"band #{bid}")
        try:
            plt.imshow(apply_cmap(band_images[bid], cmap=mplcm.gist_rainbow))
        except TypeError:
            print("########### PROBLEM!:",bid, band_images[bid])
    
    if target_savedir:
        plt.savefig("{}/band_lineup.png".format(target_savedir))
    
    return idx_filtered

def offset_image(coord, band_images, bid, ax, leaves): 
    img = apply_cmap(band_images[bid], cmap=mplcm.gist_rainbow) 
    im = OffsetImage(img, zoom=0.72)
    im.image.axes = ax
    
    coord = leaves.index(bid)
    
    # set a stagger variable to reduce image overlap:
    if (coord % 2) == 0:
        stagger = -0.25
    else:
        stagger = -0.75
    ab = AnnotationBbox(im, 
                        xy=(5+(coord*10), stagger),  
                        frameon=False,
                        annotation_clip=False,
                        xycoords='data',  
                        pad=0)

    ax.add_artist(ab)

def plot_dendrogram(Z, idx_filtered, target_savedir, band_images, cutoff=0.8):
    # calculate full dendrogram
    fig, ax = plt.subplots(figsize=(50, 12))

    plt.title('Hierarchical Clustering Dendrogram')
    plt.xlabel('band ID')
    plt.ylabel('distance')

    dgram = dendrogram(
                        Z,
                        leaf_rotation=0,  # rotates the x axis labels
                        leaf_font_size=8.,  # font size for the x axis labels
                        color_threshold=cutoff,
                        ax=ax,
                       )

    ax.tick_params(axis='x', which='major', pad=100)

    for idx,bid in enumerate(idx_filtered):
        offset_image(bid, band_images, bid, ax, dgram['leaves'])

    plt.savefig("{}/band_dendrogram.png".format(target_savedir))
    plt.show()
    return dgram

def crop_convert(crop, shape, ):
    if crop:
        y1, y2, x1, x2 = crop
        if y1 < 0:
            y1 = shape[0] + y1
        if y1 > shape[0]:
            y1 = shape[0]
        
        if y2 < 0:
            y2 = shape[0] + y2
        if y2 > shape[0]:
            y2 = shape[0]
            
        if x1 < 0:
            x1 = shape[1] + x1
        if x1 > shape[1]:
            x1 = shape[1]
        if x2 < 0:
            x2 = shape[1] + x2
        if x2 > shape[1]:
            x2 = shape[1]

        return y1,y2,x1,x2
    else:
        return crop

def analyse_image(target_fn, binmin=200, binmax=255, contour_color=(255, 0, 0), skip_first=True, 
                  color_original=False, dendro_cutoff=0.8, minarea=100, maxarea=1000,
                  ksize=(3,13), min_edge_threshold=15, max_edge_threshold=100, min_length=30,
                  target_savedir="..", crop=None,
                 ):
    # show the original image
    orig = cv2.imread(target_fn)    
    
    # convert crop from relative to absolute coords
    if crop:
        print("Original image size:", orig.shape)
        print("Crop coords:", crop)
        y1,y2,x1,x2 = crop_convert(crop, orig.shape)
        image_area = (y2-y1) * (x2-x1)
        print(f"Cropping to: ({x1},{y1}), ({x2},{y2}) (area = {image_area})")
        print("Crop coords:", crop)
    else:
        y1,y2,x1,x2 = (0,orig.shape[0],0,orig.shape[1])
        image_area = y2*x2
        print(f"Image area = {image_area}")    
    crop = (y1,y2,x1,x2)
    
    # set up directories and baseline images
    target_savedir = get_savedir(target_fn)
    target_original, target_overlay, target_grey = get_base_images(target_fn, crop)
    


    orig = cv2.rectangle(orig, (x1,y1),(x2,y2), (255, 0, 0), 2)
    plt.imshow(orig)
    plt.show()
    
    # convert to binary image
    target_binary = get_binary(target_grey, binmin, binmax)
    plt.imshow(target_binary)
    
    # highlight background discontinuities
    edges, lines = find_discontinuities(target_grey, 
                                        ksize=(3,13), 
                                        min_edge_threshold=15, 
                                        max_edge_threshold=100, 
                                        min_length=30, 
                                        target_savedir=target_savedir
                                       )

    # calculate contours of images
    (contours,hierarchy) = cv2.findContours(target_binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    print(f"{len(contours)} contours found")
    contour_summary(contours, image_area)
    
    # annotate contours
    band_ids, band_cts = collect_contours(contours, 
                                          hierarchy, 
                                          minarea=minarea, 
                                          maxarea=maxarea, 
                                          skip_first=skip_first
                                         )
    print(f"{len(band_cts)} contours kept")
    target_contours = draw_contours(target_overlay, 
                                    band_cts, 
                                    target_savedir, 
                                    color=contour_color
                                   )
    
    # find similar bands
    df_matchDist, Z, band_images, sorted_idx, close_contour_sets = get_similar_bands(band_cts, 
                                                                                     target_savedir, 
                                                                                     target_original, 
                                                                                     target_grey,
                                                                                     skip_first=skip_first, 
                                                                                     colored=color_original
                                                                                    )
    
    # plot similar bands
    for source,targets in close_contour_sets.items():
        if len(targets) > 0:
            src = [source]
            bands = src + targets
            idx_similar = plot_colored_bands(bands, band_images, None)
    
    # plot all bands
    idx_filtered = plot_colored_bands(sorted_idx, band_images, target_savedir)
    
    # plot similar bands on dendrogram
    dgram = plot_dendrogram(Z, idx_filtered, target_savedir, band_images, cutoff=dendro_cutoff)
    
    # return key variables for drilldown analysis
    return contours, band_cts, df_matchDist, Z, idx_filtered, dgram

def find_discontinuities(target_grey, ksize=(3,13), min_edge_threshold=15, max_edge_threshold=100, min_length=30, target_savedir="../"):
    # blur image
    target_blurred = cv2.GaussianBlur(src = target_grey, 
                                        ksize = ksize, 
                                        sigmaX = 0.0,
                                      )
    # find edges
    edges = cv2.Canny(target_blurred,min_edge_threshold,max_edge_threshold)

    # predict lines
    maxLineGap = 20
    threshold = 50
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold, min_length, maxLineGap)

    # plot edges as overlay on original image
    fig = plt.figure(figsize=(21,12))

    plt.subplot(121),plt.imshow(target_grey,cmap = 'gray')
    plt.title('Original Image')
    plt.imshow(edges,cmap = 'viridis', alpha=0.5)
    plt.title('Edge Image')

    plt.subplot(122)
    plt.imshow(target_grey,cmap = 'gray')
    for l in lines:
        (x1,y1,x2,y2) = l[0]
        plt.plot([x1,x2], [y1,y2], color='red')

    plt.xlim([0,target_grey.shape[1]])
    plt.ylim([0,target_grey.shape[0]])

    plt.gca().invert_yaxis()

    # save image
    plt.savefig("{}/discontinuity_detection.png".format(target_savedir))
    plt.show()
    return edges, lines

def check_images(image_dir):
    filelist, ela_dirc = run_ela(image_dir, SAVE_REL_DIR='ela_results', QUALITY=35)
    show_ela(filelist, image_dir, ela_dirc)

