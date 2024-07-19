import { Dispatch, SetStateAction } from "react";

export interface ValueProps<T> {
  value: T;
  setValue: (value: T) => void;
}

export interface Assets {
  assets: Record<
    string,
    {
      assets: string[];
      props: string[][];
    }
  >;
  faces: Record<string, string>;
}

export interface ImagePreview {
  image: string;
  faces?: string[];
}

export type ImagePreviewBuffer = ImagePreview & {
  loading: boolean;
  index: number;
  key: string;
};

export type ImageBuffer = Record<string, ImagePreview & { index: number }>;

export type SetFunction<T> = Dispatch<SetStateAction<T>>;
