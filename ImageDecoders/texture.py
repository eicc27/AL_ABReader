from time import sleep
from PIL import Image
import numpy as np
import torch
import matplotlib.pyplot as plt

from tqdm import tqdm

V = tuple[int, int]


def show_image(image: np.ndarray):
    image = image.astype(np.uint8)
    image = Image.fromarray(image)
    image.show()


class MeshTexture2D:
    """
    Attention: this class assumes all meshes have the same correponding indexes with textures.
    The transformations defined in the faces are not changing the texture shapes.
    e.g. f 1/1/1 2/2/2 3/3/3
    """

    def __init__(
        self,
        texture_file: str = None,
        mesh_file: str = None,
        texture: Image.Image = None,
        mesh: list[str] = None,
        face_idx_bias=1,
    ) -> None:
        self.texture_file = texture_file
        if texture_file and not mesh_file:
            self.mesh_file = self.texture_file.split(".")[0] + "-mesh.obj"
        else:
            self.mesh_file = mesh_file
        self.picture = self._read_picture(texture)
        print(f"Texture shape: {self.picture.shape}")
        self.mesh = self._read_mesh(mesh, face_idx_bias)
        m = self.mesh["mesh"]
        dims = np.max(m, axis=0)
        self.output = np.zeros((dims[1] + 1, dims[0] + 1, self.picture.shape[-1]))
        print(f"Output shape: {self.output.shape}")

    def _read_mesh(self, mesh: list[str], face_idx_bias=1):
        if mesh:
            lines = mesh
        else:
            with open(self.mesh_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            lines = [line.strip() for line in lines]
        groups = {"mesh": [], "texture": [], "face": []}
        for line in lines:
            args = line.split()
            type = args[0]
            match type:
                case "g":
                    pass
                case "v":
                    groups["mesh"].append(
                        [int(x) for x in args[1:-1]]
                    )  # ignore 3d(z value)
                case "vt":
                    groups["texture"].append([float(x) for x in args[1:]])
                case "f":
                    groups["face"].append(
                        [int(x.split("/")[0]) - face_idx_bias for x in args[1:]]
                    )
        # normalize mesh coordinates to [0, ]
        mesh = groups["mesh"]
        for i in range(len(mesh[0])):
            min_val = min([v[i] for v in mesh])
            for j in range(len(mesh)):
                mesh[j][i] -= min_val
        # transpose
        mesh = [v[::-1] for v in mesh]
        # convert texture coordinates to pixel coords
        texture = groups["texture"]
        for i in range(len(texture)):
            texture[i] = [
                round(texture[i][0] * self.picture.shape[1]),
                round(texture[i][1] * self.picture.shape[0]),
            ]
        # assemble faces into rectrangles
        faces = []
        for i in list(range(len(groups["face"])))[::2]:
            a, b = groups["face"][i], groups["face"][i + 1]
            points = list(set(a + b))
            mesh_points = [mesh[p] for p in points]
            texture_points = [texture[p] for p in points]
            faces.append(
                {
                    "p": (a, b),
                    "m": (
                        min([p[0] for p in mesh_points]),
                        max([p[0] for p in mesh_points]),
                        min([p[1] for p in mesh_points]),
                        max([p[1] for p in mesh_points]),
                    ),
                    "t": (
                        min([p[0] for p in texture_points]),
                        max([p[0] for p in texture_points]),
                        min([p[1] for p in texture_points]),
                        max([p[1] for p in texture_points]),
                    ),
                }
            )
        groups["face"] = faces
        return groups

    def _read_picture(self, texture: Image):
        picture = texture if texture else Image.open(self.texture_file)
        return np.flip(np.array(picture), axis=0)

    def render(self, processes: int = 1):
        faces = self.mesh["face"]
        if processes > 1:
            from concurrent.futures import ThreadPoolExecutor as TPE

            pool = TPE(processes)
        self.pbar = tqdm(total=len(faces))
        for face in faces:
            if processes > 1:
                pool.submit(self._render_face, face)
            else:
                self._render_face(face)
        if processes > 1:
            pool.shutdown(wait=True)
        self.pbar.close()
        self.output = np.flip(self.output, axis=1)
        return self.output

    def _render_face(self, face):
        X, Y, _ = self.output.shape
        X, Y = X - 1, Y - 1
        # print(face)
        m_xmin, m_xmax, m_ymin, m_ymax = face["m"]
        t_xmin, t_xmax, t_ymin, t_ymax = face["t"]
        subtexture = self.picture[t_ymin : t_ymax + 1, t_xmin : t_xmax + 1]
        # subtexture = np.flip(subtexture, axis=1)
        # print(
        #     f"Subtexture shape: {subtexture.shape}, Mesh shape: {m_xmax - m_xmin + 1, m_ymax - m_ymin + 1}"
        # )
        # fill the mesh
        xm = X - m_xmax - 1
        ym = Y - m_ymax - 1
        self.output[
            X - m_xmin : xm if xm >= 0 else None : -1,
            Y - m_ymin : ym if ym >= 0 else None : -1,
            :,
        ] = subtexture[: m_xmax - m_xmin + 1, : m_ymax - m_ymin + 1]
        self.pbar.update(1)


def visualize_v(ax, img: np.ndarray, vertices: list[V], first=None):
    ax.imshow(img)
    for idx, (x, y) in enumerate(vertices[:first] if first else vertices):
        ax.plot(x, y, "o", color="red", markersize=5)
        ax.text(x + 5, y + 5, str(idx), fontsize=8, color="blue")


if __name__ == "__main__":
    texture = MeshTexture2D(
        # "output.png",
        "../adiliao_2_n_rw_tex/0.png",
        "../adiliao_2_n_rw_tex/mesh.obj",
        face_idx_bias=0,
    )
    fig, ax = plt.subplots()
    visualize_v(ax, texture.picture, texture.mesh["texture"])
    plt.show()
    # output = texture.render(processes=1)
    # Image.fromarray(output.astype(np.uint8)).save("output.png")
