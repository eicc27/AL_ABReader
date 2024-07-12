"use client";
import { Cog6ToothIcon, EyeSlashIcon, HandRaisedIcon, MoonIcon, PhotoIcon, SparklesIcon, UserCircleIcon } from "@heroicons/react/24/outline";
import { Autocomplete, AutocompleteItem, Button, Image, Listbox, ListboxItem, ListboxSection, Tooltip } from "@nextui-org/react";
import axios from "axios";
import { useEffect, useState } from "react";

export default function Home() {
  const [charName, setCharName] = useState("");
  const [exportAssets, setExportAssets] = useState([] as string[]);
  const [assets, setAssets] = useState<any>({});
  const searchCharAssets = async (v: string) => {
    console.log(v);
    const resp = await axios.post("http://127.0.0.1:5500/getChars", {
      base_dir: "",
      keyword: v
    });
    setAssets(resp.data);
  }
  return (
    <main className="fixed top-16 flex flex-col items-start justify-center" style={{ width: "80vw", left: "10vw" }}>
      <div className="char-import flex flex-row items-center justify-center mb-10">
        <CharImport value={charName} setValue={setCharName}></CharImport>
        <Button type="button" color="primary" className=" ml-10" onClick={() => charName && searchCharAssets(charName)}>Get Assets</Button>
      </div>
      {(charName && Boolean(Object.keys(assets).length)) &&
        <CharInfo assets={assets} setExportAssets={setExportAssets}></CharInfo>}
    </main>
  );
}

interface ValueProps<T> {
  value: T;
  setValue: (value: T) => void;
}

const CharImport: React.FC<ValueProps<string>> = ({ value, setValue }) => {
  const [searchResults, setSearchResults] = useState([] as string[]);
  const [inputValue, setInputValue] = useState("")
  const searchCharName = async () => {
    const resp = await axios.post("http://127.0.0.1:5500/getMatches", {
      base_dir: "",
      keyword: inputValue
    });
    setSearchResults(resp.data.result);
  }
  return <Autocomplete
    label="Character Name"
    inputValue={inputValue}
    placeholder="use pinyin: longwu=龙武"
    className="w-max"
    onInputChange={(v) => { setInputValue(v); searchCharName(); }}
    onSelectionChange={(v) => { v && setValue(v.toString()); }}
  >
    {searchResults.map(r => <AutocompleteItem key={r}>{r}</AutocompleteItem>)}
  </Autocomplete>
}

const LabelIcons: React.FC<{
  label: string
}> = ({ label }) => {
  switch (label) {
    case "no global background":
      return <Tooltip content={label}><EyeSlashIcon className="w-8 h-8 px-1" ></EyeSlashIcon></Tooltip>
    case "censored":
      return <Tooltip content={label}><HandRaisedIcon className="w-8 h-8 px-1" ></HandRaisedIcon></Tooltip>
    case "character":
      return <Tooltip content={label}><UserCircleIcon className="w-8 h-8 px-1" ></UserCircleIcon></Tooltip>
    case "background layer":
      return <Tooltip content={label}><PhotoIcon className="w-8 h-8 px-1" ></PhotoIcon></Tooltip>
    case "ship gears":
      return <Tooltip content={label}><Cog6ToothIcon className="w-8 h-8 px-1" ></Cog6ToothIcon></Tooltip>
    case "special effect":
      return <Tooltip content={label}><SparklesIcon className="w-8 h-8 px-1" ></SparklesIcon></Tooltip>
    case "shadow":
      return <Tooltip content={label}><MoonIcon className="w-8 h-8 px-1" ></MoonIcon></Tooltip>
    default:
      return null;
  }
}

const CharInfo: React.FC<{
  assets: any,
  setExportAssets: (value: string[]) => void;
}> = ({ assets, setExportAssets }) => {
  const [imgCache, setImgCache] = useState<Record<string, string | null | undefined>>({});
  const [selectedAsset, setSelectedAsset] = useState("");
  const [url, setSrc] = useState("");
  const [imgLoading, setImageLoading] = useState(false);
  const [imgPreview, setImagePreview] = useState(true);
  useEffect(() => { setSrc(imgCache[selectedAsset]!); }, [imgCache, selectedAsset]);
  useEffect(() => { setSrc(""); setImgCache({}); }, [assets]);
  const loadAsset = async (v: string) => {
    if (!imgPreview)
      return;
    if (imgCache[v] !== undefined) // loading protection
      return;
    setImageLoading(true);
    imgCache[v] = null;
    const resp = await axios.post("http://127.0.0.1:5500/loadAsset", {
      "asset": v
    }, {
      responseType: "blob"
    })
    const imgUrl = URL.createObjectURL(resp.data);
    imgCache[v] = imgUrl;
    setImgCache(imgCache);
    setSrc(imgCache[selectedAsset]!);
    setImageLoading(false);
  }
  return <div className="flex flex-row items-start justify-center">
    <div className="flex flex-col items-start justify-center">
      <Listbox className="mr-10"
        style={{ width: "40vw" }}
        topContent={<h3>Select Exportable Assets</h3>}
        selectionMode="multiple"
        disallowEmptySelection={false}>
        {Object.keys(assets).map(k => <ListboxSection title={k}>
          {assets[k]["assets"].map((v: any, i: number) =>
            <ListboxItem
              key={v}
              aria-label={v}
              endContent={assets[k]["props"][i].map((p: string) =>
                <LabelIcons label={p}></LabelIcons>
              )}
              onPress={async () => {
                await ((!imgCache[v]) && loadAsset(v));
                setSelectedAsset(v);
              }}>
              {v}
            </ListboxItem>)}
        </ListboxSection>)}
      </Listbox>
      <div className="flex flex-row content-around justify-center">
        {imgPreview ?
          <Button type="button" color="warning" onPress={() => { setImagePreview(false); }}>Disable image preview</Button> :
          <Button type="button" color="primary" onPress={() => { setImagePreview(true); }}>Enable image preview</Button>}
      </div>
    </div>
    {imgPreview && <Image
      alt="image preview"
      style={{ width: "40vw", height: "40vw", objectFit: "contain" }}
      src={url}
      isLoading={imgLoading}
    >
    </Image>}
  </div>
}