# Endfield Toon Addon

基于新杨XIYAG大佬的仿终末地渲染节点制作，用于将导入到`Goo Engine`的模型快速替换成《明日方舟：终末地》风格卡渲材质，并自动挂载预设材质、几何节点、描边与部分场景辅助对象。

## 项目状态

- 当前仓库用于 GitHub 源码发布。
- 插件主体位于 `endfield_toon_addon/`。
- 预设库位于 `endfield_toon_addon/presets/Chen.blend`。
- 许可证使用 `GPL-3.0-or-later`
- 原作者许可
- <img width="646" height="198" alt="image" src="https://github.com/user-attachments/assets/6a191974-e57d-4d55-80de-582eaca531a3" />


## 主要功能

- 一键替换模型材质为 终末地 风格材质。
- 支持按贴图命名规则自动补全缺失贴图路径。
- 可自动挂载描边、几何节点、眼部透明、头部辅助对象等结构。
- 可迁移部分场景环境资源，如 `World`、光源和辅助对象。
- 在插件面板内提供常用参数的安全微调入口。

## 仓库结构

```text
.
├─ LICENSE
├─ README.md
└─ endfield_toon_addon/
   ├─ __init__.py
   └─ presets/
      └─ Chen.blend
```

## 环境要求

- 推荐使用 `Goo Engine`，使用原版blender会缺失部分节点
- 需要可用的模型、材质槽和对应贴图资源，如果没有，推荐使用Materialize手动生成。

## 安装方式

### 方式一：从源码目录手动打包

1. 保留整个 `endfield_toon_addon/` 目录。
2. 将 `endfield_toon_addon/` 压缩为 zip。
3. 确认 zip 根目录内直接包含 `endfield_toon_addon/__init__.py`。
4. 在 Blender 中打开 `编辑 > 偏好设置 > 插件 > 安装...`。
5. 选择刚才的 zip，并启用 `Endfield Toon Addon`。


### 方式二：从 GitHub Release 下载

1. 打开仓库的 `Releases` 页面。
2. 下载已经打包好的插件 zip。
3. 在 Blender 中使用同样的 `安装...` 流程导入。


## 使用教程

### 1. 导入模型

1. 在 Blender 中导入你的模型文件。
2. 检查模型的材质槽是否完整。
3. 确认基础贴图文件已经整理到可访问位置。

### 2. 打开插件面板

1. 切换到 `3D 视图`。
2. 按 `N` 打开右侧 Sidebar。
3. 进入 `终末地卡渲` 选项卡。

<img width="334" height="202" alt="屏幕截图 2026-04-03 213632" src="https://github.com/user-attachments/assets/82d6a1d3-0c81-41aa-a403-6937cf662878" />


### 3. 选择着色器类型

根据当前选中的对象，先选择 `着色器类型`：

- `身体`：皮肤材质，色调看起来比服装要暖一些
- `衣服`：服装材质，如果服装是分块的，可以基于当前选中的多个网格创建非破坏性的描边代理
- `面部`：面部材质，有调节sdf贴图位置的选项，便于将终末地的sdf贴图与现模型匹配
- `头发`：头发材质，对于鸣潮模型效果不佳
- `眼部`：睫毛 / 瞳孔 / 眉毛材质，有眼透效果

建议按对象类型分批处理，而不是一次对所有不同用途的材质混合处理。

<img width="220" height="100" alt="屏幕截图 2026-04-03 213740" src="https://github.com/user-attachments/assets/09501ff9-be26-4169-9e3d-48cdb761b6a0" />

### 4. 确认预设库

插件默认会使用内置预设：

- `endfield_toon_addon/presets/Chen.blend`

如果你有自定义预设库，也可以在面板里手动指定 `preset_library_path`。

<img width="303" height="39" alt="image" src="https://github.com/user-attachments/assets/b8ecf286-4969-4d71-83b2-27bb6827f059" />

### 5. 选择贴图

按照当前材质类型填写贴图路径。常见贴图如下，不需要填满，但必须将漫反射贴图填上：

- `_D`：BaseColor / Diffuse
- `_N`：Normal
- `_P` / `_ID` / `_ILM`：LightMap / ILM
- `_M`：Metal / Smooth / ORM
- `_ST`：描边遮罩 / SDF / FlowMap
- `_E`：Emission

基础建议：

- `BODY`、`CLOTH`、`HAIR` 至少准备 `_D`，并尽量补齐 `_N` 和 `_P`
- `FACE` 通常至少需要 `_D`
- `PUPIL`、`BROW` 一般只需要基础贴图

如果贴图命名较规范，可以开启自动补全，让插件推断缺失路径。

<img width="366" height="166" alt="image" src="https://github.com/user-attachments/assets/016efa25-b3a3-440c-ad92-3e4054d0afa5" />

缺失的贴图可以用Materialize生成

### 6. 设置转换参数

常用参数说明：

- `作用于所选网格`：只处理当前选中的网格对象
- `替换范围`：决定替换当前材质槽还是全部材质槽
- `自动补全缺失贴图`：自动推断缺失贴图
- `清理自定义拆边法线`：清理导入模型中的自定义法线
- `迁移场景环境`：迁移预设中的环境资源
- `迁移辅助集合`：创建或迁移辅助进行计算的空物体
- `自动挂载几何节点`：自动挂载几何节点

通常建议首次转换时保持默认设置，只在结果明确异常时再逐项排查。

<img width="305" height="162" alt="image" src="https://github.com/user-attachments/assets/8b896118-c13b-4fef-87e1-65b9f87d4570" />

### 7. 执行一键生成

1. 选中要处理的对象。
2. 确认 `着色器类型` 和贴图路径无误。
3. 点击 `一键生成`。
4. 检查生成后的材质、描边和几何节点结果。

如果是多种材质混合模型，建议分离模型后按 `身体`、`衣服`、`脸`、`头发` 分开执行。

### 8. FACE 模式的额外设置

`FACE` 模式通常还需要额外确认：

- `Head Bone Armature`
- `Head Bone Name`
- 是否启用 `眼部与脸部一体`
- Iris / Brow 材质槽是否指向正确源材质

如果头骨自动识别失败，应手动指定对应骨架与头骨名称。

<img width="300" height="372" alt="image" src="https://github.com/user-attachments/assets/ca128e9f-f9d7-4a0f-93e5-c235a096f6e8" />

### 9. 描边与微调

对于非 `默认` 模式，还可以进一步调整：

- 描边厚度
- 描边材质偏移
- 描边修改器名称

<img width="303" height="98" alt="image" src="https://github.com/user-attachments/assets/a431c8f4-8802-4b13-a19c-f2a5f857d2c7" />

面部材质还可以在面板底部继续做 SDF / 高光 映射微调。

<img width="307" height="221" alt="image" src="https://github.com/user-attachments/assets/e6a86d2d-93eb-4459-aaf8-0a665ff202ea" />

### 10. 生成效果

<img width="1920" height="1920" alt="image" src="https://github.com/user-attachments/assets/cd1613f1-13f4-4ce2-9f36-07ef56f4a5a7" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/411754a1-5fd1-4307-be85-a32e6e1d538a" />

## 常见问题

### 1. 生成后阴影效果不对

优先检查以下内容：

- 是否缺失 `_N` 或 `_P` 贴图
- 导入模型材质是否本身缺少关键图片
- 当前材质是否被错误归类到不匹配的 `着色器类型`

### 2. 找不到预设库

先确认以下路径存在：

- `endfield_toon_addon/presets/Chen.blend`

如果你改动了目录结构，插件就无法再使用内置默认预设。

### 3. FACE 模式无法正常挂载头部辅助

通常是以下原因之一：

- 没有识别到头部骨架
- 头骨名称不符合自动识别规则
- 目标对象并不是预期的面部网格

这类问题应优先改为手动指定骨架和骨骼名称。

### 4. 使用 `Eevee ` 时结果和预期不一致

当前项目更建议：

- 使用 `Goo Engine 中的Goo Engine渲染器`

如果你切换到其他渲染路径，需要自行验证节点和效果兼容性。

### 5. 阴影有明显断边

如果是单一网格内部的可以使用Weld描边或者GN合并描边，优化效果

对于两个网格之间的断边可以使用Outline Proxy基于当前选中网格创建非破坏性代理对象

## 许可证

本项目使用 `GPL-3.0-or-later`。

## 致谢

- 感谢新杨XIYAG大佬制作的仿《明日方舟：终末地》渲染节点
- 感谢茶叶味香皂大佬配布的《明日方舟：终末地》陈千语
- 感谢GPT5.4在代码方面的帮助
