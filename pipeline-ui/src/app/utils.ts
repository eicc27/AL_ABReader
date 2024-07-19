import axios from "axios";

/**
 * Given a base64 encoded picture, decode it and convert it into an object url.
 * @param b64
 * @param type
 * @returns
 */
export const decodeBase64URL = (b64: string, type = "image/png") => {
  const binaryString = atob(b64);
  const length = binaryString.length;
  const arrayBuffer = new Uint8Array(new ArrayBuffer(length));
  for (let i = 0; i < length; i++) {
    arrayBuffer[i] = binaryString.charCodeAt(i);
  }
  const blob = new Blob([arrayBuffer], { type });
  const imageUrl = URL.createObjectURL(blob);
  return imageUrl;
};

/**
 * Fetches a same-source picture url and convert it into a base64 encoded string.
 * @param url
 * @returns
 */
export const encodeBase64URL = async (url: string) => {
  const resp = await axios.get(url, { responseType: "arraybuffer" });
  const buf = Buffer.from(resp.data, "binary");
  return buf.toString("base64");
};

export function copy<T>(o: T): T {
  return JSON.parse(JSON.stringify(o));
}

export const debug = (...params: any[]) => {
  for (const param of params) console.log(param);
};
