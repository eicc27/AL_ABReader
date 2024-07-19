"use client";
import {
  Cog6ToothIcon,
  EyeSlashIcon,
  FaceSmileIcon,
  HandRaisedIcon,
  MoonIcon,
  PhotoIcon,
  SparklesIcon,
  UserCircleIcon,
} from "@heroicons/react/24/outline";
import {
  Autocomplete,
  AutocompleteItem,
  Avatar,
  Button,
  Image,
  Listbox,
  ListboxItem,
  ListboxSection,
  Skeleton,
  Tooltip,
} from "@nextui-org/react";
import axios from "axios";
import { Fragment, useEffect, useState } from "react";
import {
  ImagePreview,
  Assets,
  SetFunction,
  ImageBuffer,
  ImagePreviewBuffer,
} from "./types";
import { debug, decodeBase64URL, encodeBase64URL } from "./utils";

export default function Home() {
  const [charName, setCharName] = useState("");
  const [assets, setAssets] = useState<Assets>();
  const [selectedAssets, setSelectedAssets] = useState(new Set([] as string[]));
  const [imageBuffer, setImageBuffer] = useState({} as ImageBuffer);
  const [preview, setPreview] = useState({
    loading: false,
    index: 0,
    image: "",
    faces: [],
    key: "",
  } as ImagePreviewBuffer);
  useEffect(() => debug(imageBuffer, preview), [imageBuffer, preview]);
  // when assets is redefined, clear the imageBuffer and revoke all urls for GC
  useEffect(() => {
    console.log(imageBuffer);
    const keys = Object.keys(imageBuffer);
    for (const k in keys) {
      const buffer = imageBuffer[k];
      if (!buffer) continue;
      buffer.image && buffer.image.length && URL.revokeObjectURL(buffer.image);
      buffer.faces?.map((f) => URL.revokeObjectURL(f));
    }
    setImageBuffer({});
    setPreview({
      loading: false,
      image: "",
      index: 0,
      key: "",
    });
  }, [assets]);
  const searchCharAssets = async (v: string) => {
    console.log(v);
    const resp = await axios.post("http://127.0.0.1:5500/getChars", {
      base_dir: "",
      keyword: v,
    });
    setAssets(resp.data);
  };
  return (
    <main
      className="absolute top-16 flex flex-col items-start justify-start"
      style={{ width: "80vw", left: "10vw", paddingBottom: "10vh" }}
    >
      <div className="char-import flex flex-row items-center justify-center mb-10">
        <CharImport setCharName={setCharName}></CharImport>
        <Button
          type="button"
          color="primary"
          isDisabled={!charName}
          className=" ml-10"
          onClick={() => charName && searchCharAssets(charName)}
        >
          Get Assets
        </Button>
      </div>
      <div className="chars flex flex-row items-start justify-center">
        <AssetList
          assets={assets}
          setSelectedAssets={setSelectedAssets}
          preview={preview}
          setPreview={setPreview}
          imageBuffer={imageBuffer}
          setImageBuffer={setImageBuffer}
        ></AssetList>
        <Images
          preview={preview}
          setPreview={setPreview}
          imageBuffer={imageBuffer}
          setImageBuffer={setImageBuffer}
        ></Images>
      </div>
    </main>
  );
}

const CharImport: React.FC<{
  setCharName: SetFunction<string>;
}> = ({ setCharName: setValue }) => {
  const [searchResults, setSearchResults] = useState([] as string[]);
  const [inputValue, setInputValue] = useState("");
  const searchCharName = async () => {
    const resp = await axios.post("http://127.0.0.1:5500/getMatches", {
      base_dir: "",
      keyword: inputValue,
    });
    setSearchResults(resp.data.result);
  };
  return (
    <Autocomplete
      label="Character Name"
      inputValue={inputValue}
      placeholder="use pinyin: longwu=龙武"
      className="w-max text-lg"
      onInputChange={(v) => {
        setInputValue(v);
        searchCharName();
      }}
      onSelectionChange={(v) => {
        v && setValue(v.toString());
      }}
    >
      {searchResults.map((r) => (
        <AutocompleteItem key={r}>{r}</AutocompleteItem>
      ))}
    </Autocomplete>
  );
};

const LabelIcons: React.FC<{
  label: string;
}> = ({ label }) => {
  switch (label) {
    case "no global background":
      return (
        <Tooltip key={crypto.randomUUID()} content={label}>
          <EyeSlashIcon
            key={crypto.randomUUID()}
            className="w-8 h-8 px-1 stroke-slate-500"
          ></EyeSlashIcon>
        </Tooltip>
      );
    case "censored":
      return (
        <Tooltip key={crypto.randomUUID()} content={label}>
          <HandRaisedIcon
            key={crypto.randomUUID()}
            className="w-8 h-8 px-1 stroke-slate-500"
          ></HandRaisedIcon>
        </Tooltip>
      );
    case "character":
      return (
        <Tooltip key={crypto.randomUUID()} content={label}>
          <UserCircleIcon
            key={crypto.randomUUID()}
            className="w-8 h-8 px-1 stroke-slate-500"
          ></UserCircleIcon>
        </Tooltip>
      );
    case "background layer":
      return (
        <Tooltip key={crypto.randomUUID()} content={label}>
          <PhotoIcon
            key={crypto.randomUUID()}
            className="w-8 h-8 px-1 stroke-slate-500"
          ></PhotoIcon>
        </Tooltip>
      );
    case "ship gears":
      return (
        <Tooltip key={crypto.randomUUID()} content={label}>
          <Cog6ToothIcon
            key={crypto.randomUUID()}
            className="w-8 h-8 px-1 stroke-slate-500"
          ></Cog6ToothIcon>
        </Tooltip>
      );
    case "special effect":
      return (
        <Tooltip key={crypto.randomUUID()} content={label}>
          <SparklesIcon
            key={crypto.randomUUID()}
            className="w-8 h-8 px-1 stroke-slate-500"
          ></SparklesIcon>
        </Tooltip>
      );
    case "shadow":
      return (
        <Tooltip key={crypto.randomUUID()} content={label}>
          <MoonIcon
            key={crypto.randomUUID()}
            className="w-8 h-8 px-1 stroke-slate-500"
          ></MoonIcon>
        </Tooltip>
      );
    case "face":
      return (
        <Tooltip key={crypto.randomUUID()} content={label}>
          <FaceSmileIcon
            key={crypto.randomUUID()}
            className="w-8 h-8 px-1 stroke-slate-500"
          ></FaceSmileIcon>
        </Tooltip>
      );
    default:
      return null;
  }
};

const AssetList: React.FC<{
  assets: Assets | undefined; // in
  preview: ImagePreviewBuffer;
  imageBuffer: ImageBuffer;
  setSelectedAssets: SetFunction<Set<string>>; // out
  setPreview: SetFunction<ImagePreviewBuffer>;
  setImageBuffer: SetFunction<ImageBuffer>;
}> = ({
  assets,
  preview,
  imageBuffer,
  setSelectedAssets,
  setPreview,
  setImageBuffer,
}) => {
  const loadAsset = async (assetName: string) => {
    setPreview({ ...preview, loading: true });
    // if assetName is already in buffer, directly set imagePreview to the asset
    if (imageBuffer[assetName]) {
      setPreview({
        ...imageBuffer[assetName],
        loading: false,
        key: assetName,
      });
      return;
    }
    // else update the buffer and set imagePreview
    const resp = await axios.post(
      "http://127.0.0.1:5500/loadAsset",
      {
        asset: assetName,
      },
      { responseType: "blob" }
    );
    const data = resp.data as Blob;
    const assetUrl = URL.createObjectURL(data);
    setImageBuffer({
      ...imageBuffer,
      [assetName]: {
        image: assetUrl,
        index: 0,
      },
    });
    setPreview({ image: assetUrl, loading: false, index: 0, key: assetName });
  };
  const applyFace = async (assetName: string, faceName: string) => {
    setPreview({ ...preview, loading: true });
    let req: any;
    if (imageBuffer[assetName]) {
      // if image and faces are all in the buffer
      if (imageBuffer[assetName].faces) {
        setPreview({
          ...imageBuffer[assetName],
          loading: false,
          key: assetName,
        });
        return;
      }
      // if image is in the buffer but faces are not
      else
        req = {
          img: await encodeBase64URL(imageBuffer[assetName].image),
          face: faceName,
        };
    }
    // if both image and faces are not in the buffer
    req = {
      char: assetName,
      face: faceName,
    };
    const resp = await axios.post("http://127.0.0.1:5500/applyFace", req);
    const data = resp.data as ImagePreview;
    data.image = decodeBase64URL(data.image);
    if (data.faces) {
      data.faces = data.faces?.map((f) => decodeBase64URL(f));
      // a first time applying faces
      setImageBuffer({ ...imageBuffer, [assetName]: { ...data, index: 0 } });
      setPreview({ ...data, loading: false, index: 0, key: assetName });
    }
    // only apply the main image on the preview
    else {
      setImageBuffer({
        ...imageBuffer,
        [assetName]: { ...imageBuffer[assetName], image: data.image },
      });
      setPreview({
        ...preview,
        image: data.image,
        loading: false,
        key: assetName,
      });
    }
  };
  if (!assets) return;
  return (
    <Listbox
      className="w-[35vw]"
      selectionMode="multiple"
      topContent={<h3>Assets</h3>}
      disallowEmptySelection={false}
      onSelectionChange={(keys) => {
        setSelectedAssets(keys as Set<string>);
      }}
      // onAction={async (key) => {
      //   console.log(key);
      //   await loadAsset(key.toString());
      // }}
    >
      {Object.keys(assets.assets).flatMap((k) => (
        <ListboxSection key={k} title={k}>
          {assets.assets[k].assets
            .map((assetName, i) => (
              <ListboxItem
                key={assetName}
                className="text-lg my-2"
                onPress={async () => {
                  await loadAsset(assetName);
                }}
                onDrop={async (e) => {
                  e.preventDefault();
                  const faceName = e.dataTransfer.getData("text");
                  await applyFace(assetName, faceName);
                }}
                onDragOver={(e) => {
                  e.preventDefault(); // this allows to drop
                }}
                endContent={assets.assets[k].props[i].map((prop) => (
                  <LabelIcons key={crypto.randomUUID()} label={prop} />
                ))}
              >
                {assetName}
              </ListboxItem>
            ))
            .concat(
              assets.faces[k] ? (
                <ListboxItem
                  key={assets.faces[k]}
                  className="bg-slate-300"
                  isReadOnly={true}
                  draggable={true}
                  onDragStart={(e) => {
                    e.currentTarget.classList.add("dragging");
                    e.dataTransfer.setData("text/plain", assets.faces[k]);
                  }}
                  onDragEnd={(e) => {
                    e.currentTarget.classList.remove("dragging");
                  }}
                  style={{ pointerEvents: "auto" }}
                  endContent={<LabelIcons label="face" />}
                >
                  {assets.faces[k]}
                </ListboxItem>
              ) : (
                <ListboxItem
                  key={crypto.randomUUID()}
                  style={{ display: "none" }}
                ></ListboxItem>
              )
            )}
        </ListboxSection>
      ))}
    </Listbox>
  );
};

const Images: React.FC<{
  preview: ImagePreviewBuffer;
  imageBuffer: ImageBuffer;
  setPreview: SetFunction<ImagePreviewBuffer>;
  setImageBuffer: SetFunction<ImageBuffer>;
}> = ({ preview, imageBuffer, setPreview, setImageBuffer }) => {
  const applyFace = async (
    index: number,
    faceUrl: string,
    assetUrl: string
  ) => {
    setPreview({ ...preview, loading: true });
    const resp = await axios.post("http://127.0.0.1:5500/applyFace", {
      img: await encodeBase64URL(assetUrl),
      face: await encodeBase64URL(faceUrl),
    });
    const data = resp.data as ImagePreview;
    // subsitute current image with 'headed' image
    const image = decodeBase64URL(data.image);
    setPreview((p) => {
      URL.revokeObjectURL(p.image);
      return { ...p, loading: false, image: image, index };
    });
    // update image and selected index in the imageBuffer
    setImageBuffer({
      ...imageBuffer,
      [preview.key]: { ...imageBuffer[preview.key], image, index },
    });
  };
  if (!preview.image || !preview.image.length) return;
  return (
    <div className="flex flex-col align-center justify-start w-[40vw]">
      <Image
        src={preview.image}
        className="w-[35vw] h-[35vw] object-contain"
        isLoading={preview.loading}
      ></Image>
      {preview.faces && (
        <div className="flex flex-row overflow-x-scroll w-[40vw] h-max">
          {preview.faces?.map((f, i) => (
            <img
              src={f}
              onClick={async () => {
                await applyFace(i, f, preview.image);
              }}
              className={
                "w-32 h-32 rounded-full border-blue-300 border-4 p-0.5 m-2 border-solid object-cover transition-all duration-100" +
                "hover:border-blue-500 hover:border-[6px] hover:cursor-pointer hover:scale-90" +
                (i === preview.index ? "border-blue-500 border-[6px]" : "")
              }
            ></img>
          ))}
        </div>
      )}
    </div>
  );
};
