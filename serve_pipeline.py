import io
from flask import Flask, request, send_file
from flask_cors import CORS
import re
import os
import base64

import numpy as np
from ABReader.ab_input import ABInput
from ABReader.ab_exporter import ABExporter
from ImageDecoders.texture import MeshTexture2D
from ImageDecoders.head import Heading
from PIL import Image

app = Flask(__name__)
CORS(app)

ASSET_PROPS = {
    "n": "no global background",
    "hx": "censored",
    "rw": "character",
    "bj": "background layer",
    "jz": "ship gears",
    "tx": "special effect",
    "shadow": "shadow",
}

SKIN_TYPES = {
    "g": "Remodeled",
    "alter": "META",
    "idol": "Idol",
    "younv": "Small ship",
    "h": "Married skin",
    "": "Original",
}


def get_props(props: list[str]):
    ret = []
    # deal with special case
    for prop in props:
        found = False
        for k in ASSET_PROPS.keys():
            if re.search(rf"^{k}\d*", prop):
                ret.append(ASSET_PROPS[k])
                found = True
        if not found:
            ret.append(prop)
    return ret


def find_matching_rw(props: list[list[str]]):
    results = []
    for i, prop in enumerate(props):
        rw_idx = -1
        for p in prop:
            if "rw" in p:
                rw_idx = prop.index(p)
        if rw_idx >= 0:
            popped = prop.copy()
            popped.pop(rw_idx)
            for j, prop_n in enumerate(props):
                if popped == prop_n:
                    results.append((i, j))
    return results


def get_faces(asset_name: str):
    asset_dir = os.path.join("AssetBundles", "paintingface")
    results = []
    for pf in os.listdir(asset_dir):
        if pf.split("_")[0] == asset_name:
            results.append(pf)
    print(results)
    ret = {}
    for r in results:
        segs = r.split("_")
        if len(segs) < 2:  # original
            ret["Original"] = r
        else:
            prop = segs[1]
            if prop in SKIN_TYPES.keys():
                ret[SKIN_TYPES[prop]] = r
            else:
                ret[prop] = r
    return ret


@app.route("/getMatches", methods=["POST"])
def get_matches():
    base_dir = request.json["base_dir"]
    base_dir = "./AssetBundles" if not base_dir else base_dir
    search_name = request.json["keyword"]
    paintings_dir = os.path.join(base_dir, "painting")
    paintings = os.listdir(paintings_dir)
    kwd = re.compile(rf"^[{search_name}.*]")
    # here we only search for character names, the skins and postfixes are don't-cares
    result = set()
    for painting in paintings:
        if kwd.search(painting):
            result.add(painting.split("_")[0])
    return {"result": list(result)}


@app.route("/getChars", methods=["POST"])
def get_char_layers():
    base_dir = request.json["base_dir"]
    base_dir = "./AssetBundles" if not base_dir else base_dir
    search_name = request.json["keyword"]
    # print(search_name)
    paintings_dir = os.path.join(base_dir, "painting")
    # first filter
    paintings = [
        p
        for p in os.listdir(paintings_dir)
        if p.startswith(search_name + "_") and p.endswith("_tex")
    ]
    result = {}
    # second filter
    for painting in paintings:
        segs = painting[len(search_name) + 1 : -4].split("_")
        # default skin
        if not segs or not segs[0].isnumeric():
            if segs:
                if segs[0] in SKIN_TYPES.keys():
                    key = SKIN_TYPES[segs[0]]
                elif any([re.search(rf"^{k}\d*", segs[0]) for k in ASSET_PROPS.keys()]):
                    key = "Original"
                else:
                    key = segs[0]
                result.setdefault(key, [])
                segs = segs[1:] if key != "Original" else segs
                segs = list(filter(lambda x: x, segs))
                result[key].append((painting, segs))
                continue
        else:
            skin = int(segs[0])
            segs = segs[1:]
            result.setdefault(skin, [])
            result[skin].append((painting, segs))
    ret = {"assets": {}, "faces": get_faces(search_name)}
    # generate tags for each asset
    for skin, assets in result.items():
        asset_names, asset_props = [a[0] for a in assets], [a[1] for a in assets]
        # print(skin, assets)
        for rw_idx, bg_idx in find_matching_rw(asset_props):
            # print(rw_idx, bg_idx)
            asset_props[bg_idx].append("bj")
        props = [get_props(p) for p in asset_props]
        k = str(skin)
        ret["assets"][k] = {
            "assets": asset_names,
            "props": [
                (
                    list(set(p))
                    if p and (k.isnumeric() or k in SKIN_TYPES.values())
                    else ["character"]
                )
                for p in props
            ],
        }
    print(ret)
    return ret


def load_asset_from_raw(asset_dir: str):
    # load asset
    ab_input = ABInput(asset_dir)
    ab_input.read_assets()
    exporter = ABExporter(ab_input)
    results = exporter.export(processes=2)
    img: Image.Image = None
    lines: list[str] = None
    # print(results)
    for result in results:
        # print(type(result))
        if type(result) is Image.Image:
            img = result
        else:
            lines = result
    # decode texture
    if lines:
        mt2d = MeshTexture2D(texture=img, mesh=lines, face_idx_bias=0)
        output = Image.fromarray(mt2d.render(4).astype(np.uint8))
    else:
        output = img
    return output


@app.route("/loadAsset", methods=["POST"])
def load_asset():
    asset_name = request.json["asset"]
    base_dir = "AssetBundles"
    asset_dir = os.path.join(base_dir, "painting", asset_name)
    output = load_asset_from_raw(asset_dir)
    buf = io.BytesIO()
    output.save(buf, format="PNG")
    buf.seek(0)
    return send_file(
        buf, mimetype="image/png", as_attachment=True, download_name=f"{asset_name}.png"
    )


def image_to_b64(image: Image.Image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@app.route("/applyFace", methods=["POST"])
def apply_face():
    char = request.json["char"] if "char" in request.json else None
    face = request.json["face"]
    img = request.json["img"] if "img" in request.json else None
    if img:
        img = base64.b64decode(img)
        img = io.BytesIO(img)
        img = Image.open(img)
    else:
        # img is not read into buffer, read from raw file
        img = load_asset_from_raw(os.path.join("AssetBundles", "painting", char))
    export_faces = True
    try:
        # decode face files first
        face_dir = os.path.join("AssetBundles", "paintingface", face)
        ab_input = ABInput(face_dir)
        ab_input.read_assets()
        ab_exporter = ABExporter(ab_input)
        faces: list[Image.Image] = ab_exporter.export(processes=4)
    except:
        # face is b64encoded string
        face = base64.b64decode(face)
        face = io.BytesIO(face)
        face = Image.open(face)
        faces = [face]
        export_faces = False
    heading = Heading(src=img, heads=[faces[0]])
    result = heading.replace_head(0)
    result = image_to_b64(result)
    ret = {
        "image": result,
        "faces": [image_to_b64(f) for f in faces] if export_faces else None,
    }
    return ret


if __name__ == "__main__":
    app.run(port=5500)
