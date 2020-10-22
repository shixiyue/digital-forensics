from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import traceback
import cv2
import uuid
import seaborn as sns
import pandas as pd
from scipy.spatial import distance as ssd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.fftpack import dct
import numpy as np
import matplotlib.cm as mplcm
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from celery import shared_task

from PIL import Image, ImageChops, ImageEnhance
import sys
import os
import threading
import argparse

import matplotlib

matplotlib.use("agg")


def flatten_rgba(im):
    """
    for removing alpha channel (to allow saving in JPEG for ELA)
    from https://stackoverflow.com/questions/9166400/convert-rgba-png-to-rgb-with-pil
    """
    im.load()  # required for png.split()

    background = Image.new("RGB", im.size, (255, 255, 255))
    background.paste(im, mask=im.split()[3])  # 3 is the alpha channel

    return background


def ela(org_fname, dirname, quality=35):
    """
    Generates an ELA image on save_dir.
    Params:
        fname:      filename w/out path
        orig_dir:   origin path
        save_dir:   save path

    Adapted from:
    https://gist.github.com/cirocosta/33c758ad77e6e6531392
    """
    tmp_fname = os.path.join(dirname, "tmp_ela.jpg")
    ela_fname = os.path.join(dirname, "0-ela.png")

    im = Image.open(org_fname)
    if im.mode == "RGBA":
        im = flatten_rgba(im)
    im.save(tmp_fname, "JPEG", quality=quality)

    tmp_fname_im = Image.open(tmp_fname)
    ela_im = ImageChops.difference(im, tmp_fname_im)

    extrema = ela_im.getextrema()
    if isinstance(extrema[0], int):
        max_diff = max(extrema)
    else:
        max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / max_diff
    ela_im = ImageEnhance.Brightness(ela_im).enhance(scale)

    ela_im.save(ela_fname)
    os.remove(tmp_fname)


def apply_cmap(img, cmap=mplcm.autumn):
    lut = np.array([cmap(i)[:3] for i in np.arange(0, 256, 1)])
    lut = (lut * 255).astype(np.uint8)
    channels = [cv2.LUT(img, lut[:, i]) for i in range(3)]
    img_color = np.dstack(channels)
    return img_color


def get_base_images(target_fn):
    # create base images
    target_original = cv2.imread(target_fn)
    target_overlay = cv2.imread(target_fn)

    # check if color image
    im = Image.open(target_fn)
    print("MODE = ", im.mode)
    if im.mode in ["RGB", "RGBA", "CMYK", "YCbCr", "LAB", "HSV"]:
        # create grey image
        target_grey = cv2.cvtColor(target_original, code=cv2.COLOR_BGR2GRAY)
    else:
        target_grey = target_original  # need to make a copy

    return target_original, target_overlay, target_grey


def get_binary(target_grey, thresh=200, maxval=255):
    blur_target = cv2.GaussianBlur(src=target_grey, ksize=(5, 5), sigmaX=0.0,)
    (_, target_binary) = cv2.threshold(
        src=blur_target, thresh=thresh, maxval=maxval, type=cv2.THRESH_BINARY
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


def collect_contours(contours, hierarchy, minarea=100, maxarea=1000, skip_first=True):
    "collect all contours that are children of the image contour (the bounding box of the image)"
    print("Parameters:", minarea, maxarea)
    band_cts = []
    for idx, cnt in enumerate(hierarchy[0]):
        if keep_contour(contours[idx], minarea, maxarea, cnt[3], skip_first):
            band_cts.append(contours[idx])
    return band_cts


def draw_contours(target_overlay, contours, dirname, color=(255, 0, 0)):
    # draw the countours
    target_contours = cv2.drawContours(
        image=target_overlay, contours=contours, contourIdx=-1, color=color, thickness=1
    )
    fig = plt.figure(figsize=(10, 10))
    plt.imshow(target_contours)
    for idx, cnt in enumerate(contours):
        (x, y), _ = cv2.minEnclosingCircle(cnt)
        plt.annotate(f"{idx}", (x, y), color="cyan")
    plt.savefig("{}/2-band_detection.png".format(dirname), bbox_inches="tight")


def get_most_similar(df_matchDist, threshold=0.1):
    """
    from the distance matrix, identify all contour pairs who differ less than the threshold. 
    """
    df_filtered = df_matchDist[df_matchDist < threshold]
    df_reduced = df_filtered.dropna(how="all")

    close_contour_sets = {
        a: list(set(df_reduced.iloc[a, :].dropna().index.values) - set([a]))
        for a in df_reduced.index
    }
    return close_contour_sets


def get_similar_bands(
    contours, dirname, target_original, target_grey, skip_first=True, colored=False
):
    # create array of contour shapes
    df_matchDist = pd.DataFrame(
        [[cv2.matchShapes(c1, c2, 1, 0.0) for c1 in contours] for c2 in contours]
    )

    # plot clustermap of distances between contours
    g = sns.clustermap(data=df_matchDist, annot=True)
    plt.savefig("{}/4-band_clusters.png".format(dirname), bbox_inches="tight")

    # filter for contours that are most similar
    close_contour_sets = get_most_similar(df_matchDist, 0.1)

    # calculate dendrogram and distances using scipy
    Z = linkage(ssd.squareform(df_matchDist.values), method="average")

    # create bounding boxes for all bands
    # create all-black mask image
    target_mask = np.zeros(shape=target_original.shape, dtype="uint8")

    # "cut out" shapes for all bands:
    band_images = {}
    for idx, c in enumerate(contours[skip_first:]):
        # add one if we skipped the first contour (which can be the contour of the entire image)
        idx += skip_first
        (x, y, w, h) = cv2.boundingRect(c)

        # draw rectangle in mask (currently unnecessary for workflow)
        cv2.rectangle(
            img=target_mask,
            pt1=(x, y),
            pt2=(x + w, y + h),
            color=(255, 255, 255),
            thickness=-1,
        )

        # crop to bounding box of band:
        if y - 5 < 0:
            stretched_y = 0
        else:
            stretched_y = y - 5
        if colored:
            band_images[idx] = target_original[
                stretched_y : y + h + 5, x : x + w, :
            ]  # for colored images
        else:
            band_images[idx] = target_grey[
                stretched_y : y + h + 5, x : x + w
            ]  # add 5px to y axis each way
    return band_images, close_contour_sets


def plot_colored_bands(sorted_idx, band_images, dirname):
    """
    plot ordered set of band images

    sorted_idx:     list of images to draw
    band_images:    dict. where each value is an image array
    dirname: directory to save figure. Set to None if you don't
                    want to save image.
    """
    # filter list to keep only indicies present in band_images:
    idx_filtered = [i for i in sorted_idx if i in band_images]

    # plot figure
    fig = plt.figure(figsize=(25, 5))
    for idx, bid in enumerate(idx_filtered):
        a = fig.add_subplot(1, 5, idx + 1)
        a.set_title(f"band #{bid}")
        try:
            plt.imshow(apply_cmap(band_images[bid], cmap=mplcm.gist_rainbow))
        except TypeError:
            print("########### PROBLEM!:", bid, band_images[bid])

    if dirname:
        plt.savefig(
            "{}/3-band_lineup{}.png".format(
                dirname, "-".join(str(idx) for idx in idx_filtered)
            ),
            bbox_inches="tight",
        )


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
    ab = AnnotationBbox(
        im,
        xy=(5 + (coord * 10), stagger),
        frameon=False,
        annotation_clip=False,
        xycoords="data",
        pad=0,
    )

    ax.add_artist(ab)


def analyse_image(
    target_fn,
    dirname,
    binmin=100,
    binmax=255,
    contour_color=(255, 0, 0),
    skip_first=True,
    color_original=False,
    dendro_cutoff=0.8,
    minarea=1000,
    maxarea=50000,
    ksize=(3, 13),
    min_edge_threshold=15,
    max_edge_threshold=100,
    min_length=30,
):
    # set up baseline images
    target_original, target_overlay, target_grey = get_base_images(target_fn)
    target_binary = get_binary(target_grey, binmin, binmax)

    # highlight background discontinuities
    find_discontinuities(
        target_grey,
        ksize=(3, 13),
        min_edge_threshold=15,
        max_edge_threshold=100,
        min_length=30,
        dirname=dirname,
    )

    # calculate contours of images
    (contours, hierarchy) = cv2.findContours(
        target_binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )[-2:]
    print(f"{len(contours)} contours found")

    # annotate contours
    band_cts = collect_contours(
        contours, hierarchy, minarea=minarea, maxarea=maxarea, skip_first=skip_first
    )
    draw_contours(target_overlay, band_cts, dirname, color=contour_color)

    # find similar bands
    band_images, close_contour_sets = get_similar_bands(
        band_cts,
        dirname,
        target_original,
        target_grey,
        skip_first=skip_first,
        colored=color_original,
    )

    # plot similar bands
    for source, targets in close_contour_sets.items():
        if len(targets) > 0:
            src = [source]
            bands = src + targets
            plot_colored_bands(bands, band_images, dirname)


def find_discontinuities(
    target_grey,
    ksize=(3, 13),
    min_edge_threshold=15,
    max_edge_threshold=100,
    min_length=30,
    dirname="",
):
    # blur image
    target_blurred = cv2.GaussianBlur(src=target_grey, ksize=ksize, sigmaX=0.0)
    # find edges
    edges = cv2.Canny(target_blurred, min_edge_threshold, max_edge_threshold)

    # predict lines
    maxLineGap = 20
    threshold = 50
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold, min_length, maxLineGap)

    # plot edges as overlay on original image
    fig = plt.figure(figsize=(21, 12))

    plt.subplot(121), plt.imshow(target_grey, cmap="gray")
    plt.imshow(edges, cmap="viridis", alpha=0.5)
    plt.title("Edge Image")

    plt.subplot(122)
    plt.imshow(target_grey, cmap="gray")
    for l in lines:
        (x1, y1, x2, y2) = l[0]
        plt.plot([x1, x2], [y1, y2], color="red")

    plt.xlim([0, target_grey.shape[1]])
    plt.ylim([0, target_grey.shape[0]])

    plt.gca().invert_yaxis()

    # save image
    plt.savefig("{}/1-discontinuity_detection.png".format(dirname), bbox_inches="tight")


@shared_task
def check_image(org_fname):
    dirname = os.path.dirname(org_fname)
    ela(org_fname, dirname, quality=35)
    try:
        analyse_image(org_fname, dirname)
    except Exception:
        traceback.print_exc()
        
