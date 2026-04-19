ADDON_AUTHOR = "kkskaguya"
DEFAULT_FACE_IRIS_SLOT_COUNT = 1
DEFAULT_FACE_BROW_SLOT_COUNT = 1
ACKNOWLEDGEMENT_LINES = (
    "感谢新杨XIYAG大佬制作的仿《明日方舟：终末地》渲染节点",
    "感谢茶叶味香皂大佬配布的《明日方舟：终末地》陈千语",
)

bl_info = {
    "name": "Endfield Toon Addon",
    "author": "kkskaguya",
    "version": (4, 5, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Endfield Toon",
    "description": "One-click convert imported materials to Arknights: Endfield toon shading.",
    "category": "Material",
}

import json
import os
import re
from dataclasses import dataclass

import bpy
import gpu
from bpy.app.handlers import persistent
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_texture_2d
from mathutils import Matrix, Vector
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup


BUNDLED_PRESET_NAME = "Chen.blend"


SHADER_TYPE_ITEMS = [
    ("BODY", "身体", ""),
    ("CLOTH", "衣服", ""),
    ("FACE", "脸部", ""),
    ("HAIR", "头发", ""),
    ("PUPIL", "眼部", ""),
]

SHADER_GROUP_KEYWORDS = {
    "BODY": ("Arknights: Endfield_PBRToonBase", "Arknights: Endfield_PBRToonBase2.0"),
    "CLOTH": ("Arknights: Endfield_PBRToonBase", "Arknights: Endfield_PBRToonBase2.0"),
    "FACE": (
        "Arknights: Endfield_PBRToonFaceBase",
        "Arknights: Endfield_PBRToonFaceBase2.0",
        "Arknights: Endfield_PBRToonBaseFace",
        "Arknights: Endfield_PBRToonBaseFace2.0",
    ),
    "HAIR": ("Arknights: Endfield_PBRToonBaseHair",),
    "PUPIL": ("Arknights: Endfield_PBRToon_irisBase", "Arknights: Endfield_PBRToon_irisBase2.0"),
    "BROW": ("Arknights: Endfield_PBRToonBaseBrow",),
}

TEMPLATE_MATERIAL_PREFS = {
    "BODY": [
        "M_actor_chen_body_01.001",
        "M_actor_chen_body_01.002",
        "M_actor_endminf_body_01",
        "M_actor_endminf_body_02",
    ],
    "CLOTH": [
        "M_actor_chen_cloth_01",
        "M_actor_chen_cloth_01.001",
        "M_actor_endminf_cloth_03",
        "M_actor_endminf_cloth_01",
        "M_actor_endminf_cloth_02",
        "M_actor_endminf_cloth_04",
    ],
    "FACE": [
        "M_actor_endminf_face_01",
        "M_actor_chen_face_01.002",
        "M_actor_chen_face_01.001",
    ],
    "HAIR": [
        "M_actor_endminf_hair_01",
        "M_actor_chen_hair_01.001",
    ],
    "PUPIL": [
        "M_actor_endminf_iris_01",
        "M_actor_chen_iris_01.002",
    ],
    "BROW": [
        "M_actor_endminf_brow_01",
        "M_actor_chen_brow_01.002",
    ],
}

ALPHA_TEMPLATE_PREFS = {
    "IRIS": [
        "M_actor_chen_iris_01.001Alpha.001",
        "M_actor_chen_iris_01.001Alpha",
    ],
    "BROW": [
        "M_actor_chen_brow_01.001Alpha.001",
        "M_actor_chen_brow_01.001Alpha",
    ],
}

OUTLINE_MATERIAL_PREFS = {
    "BODY": [
        "Chen_Cmmom_outline",
        "Endmin Cloth Outline",
        "FemEndmin outline",
        "Chen_Face_outline",
    ],
    "CLOTH": [
        "Chen_cloth_outline",
        "Endmin Cloth Outline",
        "FemEndmin outline",
        "Chen_Cmmom_outline",
        "Chen_Face_outline",
    ],
    "FACE": [
        "Chen_Face_outline",
        "FemEndmin outline",
        "Endmin Cloth Outline",
    ],
    "HAIR": [
        "PLK_hair_outline",
        "FemEndmin outline",
        "Chen_Face_outline",
    ],
    "PUPIL": [
        "Chen_Face_outline",
        "FemEndmin outline",
    ],
}

SPECIAL_MATERIAL_PREFS = {
    "SHADOW_PROXY": ["Only Shadow Proxy"],
}

GEOMETRY_NODE_PREFS = {
    "SUN_VEC": ["日光方向传递", "FemEndmin SunVec"],
    "SMOOTH_OUTLINE": ["平滑描边"],
    "FACE_VECTOR": ["脸方向向量"],
    "FACE_RAYCAST": ["光线投射"],
    "EYE_TRANSPARENCY": ["眼透位移"],
    "TIME_SETUP": ["鏃堕棿璁剧疆"],
    "SHADOW_PROXY": ["Shadow Proxy"],
}

SOURCE_MASTER_COLLECTION_NAME = "CHEN_MASTER"
SOURCE_RIG_COLLECTION_NAME = "CHEN_RIG"
SOURCE_MESH_COLLECTION_NAME = "CHEN MESH"
SOURCE_MESH_HIGH_COLLECTION_NAME = "CHEN_MESH HIGH POLY"
SOURCE_MESH_LOW_COLLECTION_NAME = "CHEN_MESH LOW POLY"
MASTER_COLLECTION_NAME = "FEMEND_MASTER"
RIG_COLLECTION_NAME = "FEMEND_RIG"
MESH_COLLECTION_NAME = "FEMEND_MESH"
MESH_HIGH_COLLECTION_NAME = "FEMEND_MESH HIGH POLY"
MESH_LOW_COLLECTION_NAME = "FEMEND_MESH LOW POLY"
HELPER_COLLECTION_NAME = "Do not touch"
SOURCE_UTILITY_COLLECTION_NAME = "CHEN_UTILITY"
SOURCE_WIDGETS_COLLECTION_NAME = "CHEN_Widgets"
SOURCE_META_COLLECTION_NAME = "CHEN_Meta"
UTILITY_COLLECTION_NAME = "UTILITY"
WIDGETS_COLLECTION_NAME = "Widgets"
META_COLLECTION_NAME = "Meta"
SOURCE_WORLD_NAME = "World"
TARGET_WORLD_NAME = "zmd world"
SOURCE_CAMERA_NAME = "摄像机"
SOURCE_SUN_LIGHT_NAME = "Chen Light"
SUN_LIGHT_NAME = "FEMEND Sun"
SUN_HELPER_LC_NAME = "LC"
SUN_HELPER_LF_NAME = "LF"
SOURCE_HEAD_HELPER_NAME = "Chen_HC"
SOURCE_HEAD_FORWARD_NAME = "Chen_HF"
SOURCE_HEAD_RIGHT_NAME = "Chen_HR"
HEAD_HELPER_NAME = "HC"
HEAD_FORWARD_NAME = "HF"
HEAD_RIGHT_NAME = "HR"
SUN_LIGHT_LOCATION = Vector((0.042163014, -0.305859387, 1.494289517))
SUN_LIGHT_ROTATION = Vector((-0.426414639, 1.021072388, -7.807478905))
SUN_LC_DISTANCE = 0.587259948
SUN_LF_DISTANCE = 1.329999924
HEAD_FORWARD_OFFSET = Vector((0.0, -0.27221608, 0.0))
HEAD_RIGHT_OFFSET = Vector((-0.27067417, 0.0, 0.0))
HEAD_HELPER_SCALE = (0.28153285, 0.28153285, 0.28153285)
HEAD_DIRECTION_SCALE = (0.19306129, 0.19306129, 0.19306129)
PRESET_RENDER_ENGINE = "BLENDER_EEVEE"
PRESET_RENDER_DEFAULTS = {
    "filter_size": 1.5,
    "film_transparent": False,
    "use_simplify": False,
}
PRESET_VIEW_DEFAULTS = {
    "view_transform": "AgX",
    "look": "AgX - Medium High Contrast",
    "exposure": 0.0,
    "gamma": 1.0,
}
PRESET_EEVEE_DEFAULTS = {
    "use_shadows": True,
    "shadow_cube_size": "4096",
    "shadow_cascade_size": "4096",
    "shadow_step_count": 6,
    "use_raytracing": True,
    "light_threshold": 0.01,
    "gi_cubemap_resolution": "512",
    "taa_render_samples": 128,
    "taa_samples": 64,
}
TEST_WELD_MODIFIER_NAME = "Endfield_TestWeld"
BODY_WELD_MODIFIER_NAME = "鐒婃帴"
BODY_WELD_DISTANCE = 0.0001
TEST_GN_MERGE_MODIFIER_NAME = "Endfield_TestGNMerge"
TEST_GN_MERGE_GROUP_NAME = "Endfield_TestMergeByDistance"
TEST_PROXY_SUFFIX = "_OutlineProxy"
TEST_PROXY_MATERIAL_NAME = "ENDFIELD_ProxyOutline"
EEVEE_SHADER_INFO_COMPAT_GROUP_NAME = "ENDFIELD_EEVEE5_ShaderInfoCompat"
EEVEE_SHADER_INFO_COMPAT_GROUP_VERSION = 2
EEVEE_SHADER_INFO_LIT_COMPAT_GROUP_NAME = "ENDFIELD_EEVEE5_ShaderInfoLitCompat"
EEVEE_SHADER_INFO_LIT_COMPAT_GROUP_VERSION = 1
EEVEE_SCREENSPACE_INFO_COMPAT_GROUP_NAME = "ENDFIELD_EEVEE5_ScreenspaceInfoCompat"
EEVEE_SCREENSPACE_INFO_COMPAT_GROUP_VERSION = 1
FACE_TEX_CONTROL_COLLECTION_NAME = "ENDFIELD_TEX_CONTROLS"
FACE_TEX_CONTROL_ROOT_KEY = "_endfield_face_tex_ctrl_root"
FACE_TEX_CONTROL_SDF_KEY = "_endfield_face_tex_ctrl_sdf"
FACE_TEX_CONTROL_CM_KEY = "_endfield_face_tex_ctrl_cm"
FACE_UV_CALIBRATION_STATE = {
    "running": False,
    "material_name": "",
    "object_name": "",
    "base_image_name": "",
    "sdf_image_name": "",
    "cm_image_name": "",
    "sdf_preview_image_name": "",
    "cm_preview_image_name": "",
    "draw_handle": None,
    "dragging": False,
    "drag_target": "",
    "drag_mode": "",
    "drag_start_uv": (0.0, 0.0),
    "drag_rect": (0.0, 0.0, 1.0, 1.0),
    "editor_images": [],
}
FACE_UV_SHADER = None
FACE_UV_TEXTURE_CACHE = {}


def _requires_eevee_compat() -> bool:
    return tuple(getattr(bpy.app, "version", (0, 0, 0))) >= (5, 0, 0)


TEXTURE_STATE_STORAGE_PROPS = {
    "BODY": "texture_state_body",
    "CLOTH": "texture_state_cloth",
    "FACE": "texture_state_face",
    "HAIR": "texture_state_hair",
    "PUPIL": "texture_state_pupil",
    "BROW": "texture_state_brow",
}

TEXTURE_STATE_ALL_PROP_IDS = (
    "tex_d",
    "tex_n",
    "tex_p",
    "tex_m",
    "tex_st",
    "tex_e",
    "face_sdf_tex",
    "face_cm_tex",
)

HEAD_BONE_KEYWORDS = ("head", "头", "首")


HEAD_BONE_EXACT_NAMES = (
    "head",
    "Head",
    "HEAD",
    "Head.x",
    "head.x",
    "Bip001 Head",
    "bip001 head",
    "mixamorig:Head",
    "ValveBiped.Bip01_Head1",
    "J_Head",
    "j_head",
    "C_Head",
    "c_head",
    "Bone_Head",
    "bone_head",
)
HEAD_BONE_KEYWORDS = ("head", "face")
HEAD_BONE_EXCLUDE_KEYWORDS = ("twist", "end", "nub", "top", "look", "track", "aim", "ik", "socket")
LATTICE_BONE_PREFIXES = ("DEF-", "DEF_", "def-", "def_")
LATTICE_OBJECT_BASENAME = "Lattice"
LATTICE_FIT_MARGIN = Vector((1.15, 1.15, 1.15))

LEGACY_COLLECTION_NAME_PAIRS = (
    (SOURCE_MASTER_COLLECTION_NAME, MASTER_COLLECTION_NAME),
    (SOURCE_RIG_COLLECTION_NAME, RIG_COLLECTION_NAME),
    (SOURCE_MESH_COLLECTION_NAME, MESH_COLLECTION_NAME),
    (SOURCE_MESH_HIGH_COLLECTION_NAME, MESH_HIGH_COLLECTION_NAME),
    (SOURCE_MESH_LOW_COLLECTION_NAME, MESH_LOW_COLLECTION_NAME),
    (SOURCE_UTILITY_COLLECTION_NAME, UTILITY_COLLECTION_NAME),
    (SOURCE_WIDGETS_COLLECTION_NAME, WIDGETS_COLLECTION_NAME),
    (SOURCE_META_COLLECTION_NAME, META_COLLECTION_NAME),
)

LEGACY_OBJECT_NAME_PAIRS = (
    (SOURCE_SUN_LIGHT_NAME, SUN_LIGHT_NAME),
    (SOURCE_HEAD_HELPER_NAME, HEAD_HELPER_NAME),
    (SOURCE_HEAD_FORWARD_NAME, HEAD_FORWARD_NAME),
    (SOURCE_HEAD_RIGHT_NAME, HEAD_RIGHT_NAME),
)

@dataclass(frozen=True)
class TextureSlotDef:
    prop_id: str
    label: str
    colorspace: str = "sRGB"


TEXTURE_SLOT_LAYOUT = {
    "BODY": [
        TextureSlotDef("tex_d", "_D.png (BaseColor)", "sRGB"),
        TextureSlotDef("tex_n", "_N.png (Normal)", "Non-Color"),
        TextureSlotDef("tex_p", "_P.png / _ID.png (ILM)", "Non-Color"),
        TextureSlotDef("tex_m", "_M.png (Metal/Smooth)", "Non-Color"),
        TextureSlotDef("tex_st", "_ST.png (Outline Mask, Optional)", "Non-Color"),
        TextureSlotDef("tex_e", "_E.png (Emission, Optional)", "Non-Color"),
    ],
    "CLOTH": [
        TextureSlotDef("tex_d", "_D.png (BaseColor)", "sRGB"),
        TextureSlotDef("tex_n", "_N.png (Normal)", "Non-Color"),
        TextureSlotDef("tex_p", "_P.png / _ID.png (ILM)", "Non-Color"),
        TextureSlotDef("tex_m", "_M.png (Metal/Smooth)", "Non-Color"),
        TextureSlotDef("tex_st", "_ST.png (Outline Mask, Optional)", "Non-Color"),
        TextureSlotDef("tex_e", "_E.png (Emission, Optional)", "Non-Color"),
    ],
    "FACE": [
        TextureSlotDef("tex_d", "_D.png (Face Base)", "sRGB"),
        TextureSlotDef("tex_st", "_ST.png (Face SDF/Outline Mask, Optional)", "Non-Color"),
    ],
    "HAIR": [
        TextureSlotDef("tex_d", "_D.png (BaseColor)", "sRGB"),
        TextureSlotDef("tex_n", "_N.png / _HN.png (Hair Normal)", "Non-Color"),
        TextureSlotDef("tex_p", "_P.png / _ID.png (ILM)", "Non-Color"),
        TextureSlotDef("tex_st", "_ST.png (Hair Outline Mask, Optional)", "Non-Color"),
    ],
    "PUPIL": [
        TextureSlotDef("tex_d", "_D.png (Iris Base)", "sRGB"),
    ],
    "BROW": [
        TextureSlotDef("tex_d", "_D.png (Brow/Lash Base)", "sRGB"),
    ],
}

ROLE_SUFFIX_CANDIDATES = {
    "tex_n": ["_N", "_HN"],
    "tex_p": ["_P", "_ID", "_ILM", "_LightMap"],
    "tex_m": ["_M", "_ORM", "_RMA"],
    "tex_st": ["_ST"],
    "tex_e": ["_E", "_EM"],
}

ROLE_SEARCH_TAGS = {
    "tex_d": ["mmd_base_tex", "_d", "base color", "basecolor", "albedo", "d_rgb"],
    "tex_n": ["_n", "_hn", "normal", "娉曠嚎"],
    "tex_p": ["_p", "_id", "_ilm", "lightmap", "lm", "spec"],
    "tex_m": ["_m", "metal", "rough", "smooth", "orm", "rma"],
    "tex_st": ["_st", "stock", "outline", "mask", "sdf"],
    "tex_e": ["_e", "emi", "emission"],
}

GENERIC_TEXTURE_SCAN_RULES = {
    "tex_n": {
        "must_any": ("_n", "_hn", "normal"),
        "prefer": ("_n", "_hn"),
        "avoid": ("_d", "_p", "_st", "_e", "cm_m", "hl_m", "eyeshadow", "hairshadow", "lut"),
    },
    "tex_p": {
        "must_any": ("_p", "_id", "_ilm", "lightmap"),
        "prefer": ("_p", "_id", "_ilm", "lightmap"),
        "avoid": ("_d", "_n", "_hn", "_st", "_e", "hl_m", "eyeshadow", "hairshadow", "lut"),
    },
    "tex_st": {
        "must_any": ("_st", "outline", "mask"),
        "prefer": ("_st", "outline", "mask"),
        "avoid": ("_d", "_n", "_hn", "_p", "_e", "hl_m", "cm_m", "eyeshadow", "hairshadow"),
    },
    "face_sdf_tex": {
        "must_any": ("sdf",),
        "prefer": ("female_face", "face", "common"),
        "avoid": ("_st", "_d", "hl_m", "cm_m", "eyeshadow", "hairshadow", "lut"),
    },
    "face_cm_tex": {
        "must_any": ("cm_m",),
        "prefer": ("female_face", "face", "common"),
        "avoid": ("hl_m", "eyeshadow", "hairshadow", "lut", "_st"),
    },
}

ROLE_COLORSPACE_DEFAULTS = {
    "tex_d": "sRGB",
    "tex_n": "Non-Color",
    "tex_p": "Non-Color",
    "tex_m": "Non-Color",
    "tex_st": "Non-Color",
    "tex_e": "Non-Color",
}

ROLE_SOCKET_KEYWORDS = {
    "tex_d_color": ["_d(srgb)r.g.b"],
    "tex_d_alpha": ["_d(srgb).a"],
    "tex_n_color": ["_n(non_color)", "_n(非色彩", "_hn(non_color)r.g.b", "_hn(非色彩", "_hn"],
    "tex_n_alpha": ["_hn(non_color)a", "_hn(非色彩", "_hn.a"],
    "tex_p_color": ["_p(non_color)r.g.b", "_p(非色彩", "_p"],
    "tex_p_alpha": ["_p(non_color)a", "_p(非色彩", "_p.a"],
    "tex_m_color": ["_m", "_m（非色彩", "_m(非色彩", "metal", "smooth", "rough"],
    "tex_e_color": ["_e", "_e（非色彩", "_e(非色彩", "emission", "emi"],
}

EYE_TRANSPARENCY_MODIFIER_PREFIX = "Eye Transparency"

SAFE_TWEAKS = {
    "BODY": [
        ("明暗分界", "CastShadow_center"),
        ("阴影锐度", "CastShadow_sharp"),
        ("边缘光宽度 X", "Rim_width_X"),
        ("边缘光宽度 Y", "Rim_width_Y"),
        ("边缘光强度", "Rim_ColorStrength"),
        ("全局阴影亮度", "GlobalShadowBrightnessAdjustment"),
    ],
    "CLOTH": [
        ("明暗分界", "CastShadow_center"),
        ("阴影锐度", "CastShadow_sharp"),
        ("边缘光宽度 X", "Rim_width_X"),
        ("边缘光宽度 Y", "Rim_width_Y"),
        ("边缘光强度", "Rim_ColorStrength"),
        ("全局阴影亮度", "GlobalShadowBrightnessAdjustment"),
    ],
    "FACE": [
        ("脸部SDF中心", "SDF_RemaphalfLambert_center"),
        ("脸部SDF锐度", "SDF_RemaphalfLambert_sharp"),
        ("正面高光强度", "Front R Pow"),
        ("正面高光平滑", "Front R Smo"),
        ("脸部整体亮度", "Face Final brightness"),
        ("全局阴影亮度", "GlobalShadowBrightnessAdjustment"),
    ],
    "HAIR": [
        ("头发明暗分界", "CastShadow_center"),
        ("头发阴影锐度", "CastShadow_sharp"),
        ("边缘光宽度", "Rim_width_X"),
        ("边缘光强度", "Rim_ColorStrength"),
        ("高光位置", "FHighLightPos"),
        ("最终亮度", "Final brightness"),
    ],
    "PUPIL": [
        ("瞳孔亮度", "Eyes brightness"),
        ("瞳孔高光亮度", "Eyes HightLight brightness"),
    ],
}


def _ensure_face_eye_material_slot_count(
    settings,
    iris_min: int = DEFAULT_FACE_IRIS_SLOT_COUNT,
    brow_min: int = DEFAULT_FACE_BROW_SLOT_COUNT,
):
    while len(settings.face_iris_materials) < iris_min:
        settings.face_iris_materials.add()
    while len(settings.face_brow_materials) < brow_min:
        settings.face_brow_materials.add()


def _on_face_integrated_eye_update(self, context):
    if self.face_integrated_eye_transparency:
        _ensure_face_eye_material_slot_count(
            self,
            DEFAULT_FACE_IRIS_SLOT_COUNT,
            DEFAULT_FACE_BROW_SLOT_COUNT,
        )


def _poll_armature_object(self, obj):
    return bool(obj and obj.type == "ARMATURE")


def _tag_all_areas_for_redraw(area_type: str = ""):
    window_manager = getattr(bpy.context, "window_manager", None)
    if window_manager is None:
        return
    for window in window_manager.windows:
        screen = window.screen
        if screen is None:
            continue
        for area in screen.areas:
            if area_type and area.type != area_type:
                continue
            area.tag_redraw()


def _on_face_uv_overlay_update(self, context):
    _tag_all_areas_for_redraw()


def _texture_state_prop_id(shader_type: str) -> str:
    return TEXTURE_STATE_STORAGE_PROPS.get(shader_type, "")


def _texture_state_field_ids(shader_type: str):
    field_ids = [slot.prop_id for slot in TEXTURE_SLOT_LAYOUT.get(shader_type, ())]
    if shader_type == "FACE":
        field_ids.extend(("face_sdf_tex", "face_cm_tex"))
    return tuple(dict.fromkeys(field_ids))


def _decode_texture_state(raw_state: str):
    if not raw_state:
        return {}
    try:
        data = json.loads(raw_state)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}

    decoded = {}
    for prop_id in TEXTURE_STATE_ALL_PROP_IDS:
        value = data.get(prop_id, "")
        if isinstance(value, str):
            decoded[prop_id] = value
    return decoded


def _texture_state_is_loading(settings) -> bool:
    return bool(getattr(settings, "texture_state_loading", False))


def _capture_texture_state(settings, shader_type: str = ""):
    shader_type = shader_type or getattr(settings, "shader_type", "BODY") or "BODY"
    return {prop_id: getattr(settings, prop_id, "") or "" for prop_id in _texture_state_field_ids(shader_type)}


def _save_texture_state(settings, shader_type: str = ""):
    if settings is None or _texture_state_is_loading(settings):
        return
    shader_type = shader_type or getattr(settings, "shader_type", "BODY") or "BODY"
    prop_id = _texture_state_prop_id(shader_type)
    if not prop_id:
        return
    setattr(settings, prop_id, json.dumps(_capture_texture_state(settings, shader_type), ensure_ascii=False))


def _apply_texture_state(settings, shader_type: str, state: dict):
    if settings is None:
        return
    settings.texture_state_loading = True
    try:
        for prop_id in TEXTURE_STATE_ALL_PROP_IDS:
            setattr(settings, prop_id, "")
        for prop_id in _texture_state_field_ids(shader_type):
            setattr(settings, prop_id, state.get(prop_id, "") or "")
    finally:
        settings.texture_state_loading = False
    _tag_all_areas_for_redraw()


def _restore_texture_state(settings, shader_type: str):
    if settings is None:
        return
    prop_id = _texture_state_prop_id(shader_type)
    state = _decode_texture_state(getattr(settings, prop_id, ""))
    _apply_texture_state(settings, shader_type, state)


def _bootstrap_texture_state(settings):
    if settings is None or getattr(settings, "texture_state_ready", False):
        return
    current_shader = getattr(settings, "shader_type", "BODY") or "BODY"
    prop_id = _texture_state_prop_id(current_shader)
    existing_state = _decode_texture_state(getattr(settings, prop_id, ""))
    if existing_state:
        _apply_texture_state(settings, current_shader, existing_state)
    else:
        _save_texture_state(settings, current_shader)
    settings.last_shader_type = current_shader
    settings.texture_state_ready = True


def _bootstrap_texture_states():
    for scene in bpy.data.scenes:
        settings = getattr(scene, "endfield_toon_settings", None)
        if settings is not None:
            _bootstrap_texture_state(settings)


def _on_texture_path_update(self, context):
    if _texture_state_is_loading(self):
        return
    if not getattr(self, "texture_state_ready", False):
        if context is None:
            return
        _bootstrap_texture_state(self)
    _save_texture_state(self)
    _tag_all_areas_for_redraw()


def _on_shader_type_update(self, context):
    if _texture_state_is_loading(self):
        return
    new_shader = getattr(self, "shader_type", "BODY") or "BODY"
    if not getattr(self, "texture_state_ready", False):
        if context is None:
            self.last_shader_type = new_shader
            return
        _bootstrap_texture_state(self)

    previous_shader = getattr(self, "last_shader_type", "") or new_shader
    if previous_shader != new_shader:
        _save_texture_state(self, previous_shader)
        _restore_texture_state(self, new_shader)
        self.last_shader_type = new_shader
    else:
        _save_texture_state(self, new_shader)


class ENDFIELD_PG_FaceEyeMaterialSlot(PropertyGroup):
    source_material: PointerProperty(name="原材质", type=bpy.types.Material)


class ENDFIELD_PG_Settings(PropertyGroup):
    preset_library_path: StringProperty(
        name="预设库(.blend)",
        subtype="FILE_PATH",
        description="留空时默认使用插件内置的 Chen.blend",
    )
    shader_type: EnumProperty(name="着色器类型选择", items=SHADER_TYPE_ITEMS, default="BODY", update=_on_shader_type_update)
    apply_mode: EnumProperty(
        name="替换范围",
        items=[
            ("ACTIVE_SLOT", "当前材质槽", ""),
            ("ALL_SLOTS", "全部材质槽", ""),
        ],
        default="ACTIVE_SLOT",
    )
    apply_selected_objects: BoolProperty(name="作用于所选网格", default=True)
    auto_fill_missing_maps: BoolProperty(name="一键生成时自动补全缺失贴图", default=True)
    clear_custom_normals: BoolProperty(name="清理自定义分裂法线", default=False)
    force_slot2_outline: BoolProperty(name="保留/创建第2材质槽描边", default=True)
    create_helper_rig: BoolProperty(name="迁移辅助集合/空物体/光源", default=True)
    auto_geometry_nodes: BoolProperty(name="自动挂载几何节点", default=True)
    migrate_source_environment: BoolProperty(name="迁移World/场景环境", default=True)
    outline_modifier_name: StringProperty(name="描边修改器名", default="Endfield_Outline")
    outline_thickness: FloatProperty(name="描边厚度", default=0.001, min=0.0, precision=6, soft_max=0.02)
    outline_material_offset: IntProperty(name="描边材质偏移", default=31, min=0, max=1000)
    test_weld_distance: FloatProperty(name="Weld距离", default=0.0005, min=0.0, precision=6, soft_max=0.01)
    test_gn_merge_distance: FloatProperty(name="GN合并距离", default=0.0005, min=0.0, precision=6, soft_max=0.01)
    head_bone_armature: PointerProperty(
        name="头部骨架",
        type=bpy.types.Object,
        poll=_poll_armature_object,
        description="可手动指定用于头部辅助空物体与 Lattice 的骨架",
    )
    head_bone_name: StringProperty(
        name="头部骨骼",
        description="可手动指定头部骨骼；留空时自动识别常见 Head 骨骼",
        default="",
    )
    eye_target_object: PointerProperty(
        name="眼透位移目标",
        type=bpy.types.Object,
        description="手动指定挂载眼透位移几何节点的网格对象；留空则自动识别",
    )
    eye_target_name: StringProperty(
        name="眼透位移目标搜索",
        description="手动指定挂载眼透位移几何节点的网格对象名称；留空则自动识别",
        default="",
    )
    face_integrated_eye_transparency: BoolProperty(
        name="眼部与脸部一体",
        description="在脸部模式下，对同一对象中指定材质追加眼透位移；材质结构仍来自预设库",
        default=False,
        update=_on_face_integrated_eye_update,
    )
    face_iris_materials: CollectionProperty(type=ENDFIELD_PG_FaceEyeMaterialSlot)
    face_brow_materials: CollectionProperty(type=ENDFIELD_PG_FaceEyeMaterialSlot)

    last_shader_type: StringProperty(default="BODY", options={"HIDDEN"})
    texture_state_ready: BoolProperty(default=False, options={"HIDDEN"})
    texture_state_loading: BoolProperty(default=False, options={"HIDDEN"})
    texture_state_body: StringProperty(default="", options={"HIDDEN"})
    texture_state_cloth: StringProperty(default="", options={"HIDDEN"})
    texture_state_face: StringProperty(default="", options={"HIDDEN"})
    texture_state_hair: StringProperty(default="", options={"HIDDEN"})
    texture_state_pupil: StringProperty(default="", options={"HIDDEN"})
    texture_state_brow: StringProperty(default="", options={"HIDDEN"})

    tex_d: StringProperty(name="_D", subtype="FILE_PATH", update=_on_texture_path_update)
    tex_n: StringProperty(name="_N", subtype="FILE_PATH", update=_on_texture_path_update)
    tex_p: StringProperty(name="_P", subtype="FILE_PATH", update=_on_texture_path_update)
    tex_m: StringProperty(name="_M", subtype="FILE_PATH", update=_on_texture_path_update)
    tex_st: StringProperty(name="_ST", subtype="FILE_PATH", update=_on_texture_path_update)
    tex_e: StringProperty(name="_E", subtype="FILE_PATH", update=_on_texture_path_update)
    face_sdf_tex: StringProperty(name="Face SDF", subtype="FILE_PATH", update=_on_texture_path_update)
    face_cm_tex: StringProperty(name="Face M", subtype="FILE_PATH", update=_on_texture_path_update)
    face_uv_show_sdf: BoolProperty(name="显示 SDF", default=True, update=_on_face_uv_overlay_update)
    face_uv_show_cm: BoolProperty(name="显示 M", default=True, update=_on_face_uv_overlay_update)
    face_uv_active_target: EnumProperty(
        name="当前调整目标",
        items=[
            ("SDF", "SDF", ""),
            ("CM", "M/亮斑", ""),
        ],
        default="SDF",
        update=_on_face_uv_overlay_update,
    )


def _safe_abs_path(path_value: str) -> str:
    if not path_value:
        return ""
    return bpy.path.abspath(path_value)


def _same_file_path(path_a: str, path_b: str) -> bool:
    abs_a = _safe_abs_path(path_a)
    abs_b = _safe_abs_path(path_b)
    if not abs_a or not abs_b:
        return False
    try:
        return os.path.normcase(os.path.normpath(abs_a)) == os.path.normcase(os.path.normpath(abs_b))
    except Exception:
        return abs_a == abs_b


def _addon_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _bundled_library_path() -> str:
    candidate = os.path.join(_addon_dir(), "presets", BUNDLED_PRESET_NAME)
    return candidate if os.path.exists(candidate) else ""

def _effective_library_path(settings: ENDFIELD_PG_Settings) -> str:
    user_path = _safe_abs_path(getattr(settings, "preset_library_path", ""))
    if user_path and os.path.exists(user_path):
        return user_path
    return _bundled_library_path()


def _copy_rna_properties(src, dst, exclude_ids=None):
    exclude = set(exclude_ids or ())
    for prop in src.bl_rna.properties:
        prop_id = prop.identifier
        if prop_id == "rna_type" or prop_id in exclude:
            continue
        if getattr(prop, "is_readonly", False):
            continue
        try:
            setattr(dst, prop_id, getattr(src, prop_id))
        except Exception:
            continue


SOURCE_LIBRARY_STAMP_KEY = "_endfield_source_library_stamp"


def _library_stamp(library_path: str) -> str:
    if not library_path or not os.path.exists(library_path):
        return ""
    try:
        mtime = os.path.getmtime(library_path)
    except OSError:
        mtime = 0.0
    return f"{os.path.abspath(library_path)}|{mtime}"


def _name_matches_datablock(base_name: str, candidate_name: str) -> bool:
    return candidate_name == base_name or candidate_name.startswith(f"{base_name}.")


def _make_backup_name(data_collection, base_name: str, suffix: str) -> str:
    candidate = f"{base_name}{suffix}"
    existing_names = {item.name for item in data_collection}
    index = 1
    while candidate in existing_names:
        candidate = f"{base_name}{suffix}.{index:03d}"
        index += 1
    return candidate


def _backup_matching_datablocks(data_collection, base_names, predicate=None) -> int:
    renamed = 0
    base_names = tuple(dict.fromkeys(name for name in base_names if name))
    if not base_names:
        return 0
    for datablock in list(data_collection):
        datablock_name = getattr(datablock, "name", "")
        if not any(_name_matches_datablock(base_name, datablock_name) for base_name in base_names):
            continue
        if predicate is not None and not predicate(datablock):
            continue
        try:
            datablock.name = _make_backup_name(data_collection, datablock_name, "__OLD")
        except Exception:
            continue
        renamed += 1
    return renamed


def _collect_node_group_names(node_tree, names=None, visited=None):
    if node_tree is None:
        return set() if names is None else names
    names = set() if names is None else names
    visited = set() if visited is None else visited
    tree_key = node_tree.as_pointer()
    if tree_key in visited:
        return names
    visited.add(tree_key)
    names.add(node_tree.name)
    for node in node_tree.nodes:
        child_tree = getattr(node, "node_tree", None)
        if child_tree is None:
            continue
        _collect_node_group_names(child_tree, names, visited)
    return names


def _collect_material_node_group_names(material) -> set:
    if material is None or not material.use_nodes or material.node_tree is None:
        return set()
    return _collect_node_group_names(material.node_tree)


def _append_datablock_from_library(library_path: str, collection_name: str, datablock_name: str):
    if not library_path or not os.path.exists(library_path):
        return None
    data_collection = getattr(bpy.data, collection_name)
    before_names = {item.name for item in data_collection}
    try:
        with bpy.data.libraries.load(library_path, link=False) as (data_from, data_to):
            available = getattr(data_from, collection_name)
            if datablock_name not in available:
                return None
            setattr(data_to, collection_name, [datablock_name])
        appended = None
        for item in data_collection:
            if not _name_matches_datablock(datablock_name, item.name):
                continue
            if item.name not in before_names:
                appended = item
                break
        if appended is not None:
            stamp = _library_stamp(library_path)
            if stamp:
                appended[SOURCE_LIBRARY_STAMP_KEY] = stamp
        return appended
    except Exception:
        return None


def _find_stamped_material(material_name: str, library_path: str):
    stamp = _library_stamp(library_path)
    if not stamp:
        return bpy.data.materials.get(material_name)
    for material in bpy.data.materials:
        if _name_matches_datablock(material_name, material.name) and material.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
            return material
    return None


def _stash_outdated_material(material_name: str, library_path: str):
    material = bpy.data.materials.get(material_name)
    stamp = _library_stamp(library_path)
    if material is None or not stamp:
        return
    if material.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
        return
    material.name = _make_backup_name(bpy.data.materials, material_name, "__OLD")


def _find_stamped_object(object_name: str, library_path: str):
    stamp = _library_stamp(library_path)
    if not stamp:
        return bpy.data.objects.get(object_name)
    for obj in bpy.data.objects:
        if _name_matches_datablock(object_name, obj.name) and obj.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
            return obj
    return None


def _stash_outdated_object(object_name: str, library_path: str):
    obj = bpy.data.objects.get(object_name)
    stamp = _library_stamp(library_path)
    if obj is None or not stamp:
        return
    if obj.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
        return
    obj.name = _make_backup_name(bpy.data.objects, object_name, "__OLD")


def _find_matching_object(object_name: str):
    obj = bpy.data.objects.get(object_name)
    if obj is not None:
        return obj
    for candidate in bpy.data.objects:
        if _name_matches_datablock(object_name, candidate.name):
            return candidate
    return None


def _find_matching_collection(collection_name: str):
    collection = bpy.data.collections.get(collection_name)
    if collection is not None:
        return collection
    for candidate in bpy.data.collections:
        if _name_matches_datablock(collection_name, candidate.name):
            return candidate
    return None


def _rename_datablock(datablocks, datablock, target_name: str):
    if datablock is None or not target_name or datablock.name == target_name:
        return datablock
    existing = datablocks.get(target_name)
    if existing is not None and existing != datablock:
        return existing
    datablock.name = target_name
    return datablock


def _ensure_object_alias(target_name: str, *aliases: str):
    obj = _find_matching_object(target_name)
    if obj is not None:
        return _rename_datablock(bpy.data.objects, obj, target_name)
    for alias in aliases:
        if not alias:
            continue
        obj = _find_matching_object(alias)
        if obj is not None:
            return _rename_datablock(bpy.data.objects, obj, target_name)
    return None


def _ensure_collection_alias(target_name: str, *aliases: str):
    collection = _find_matching_collection(target_name)
    if collection is not None:
        return _rename_datablock(bpy.data.collections, collection, target_name)
    for alias in aliases:
        if not alias:
            continue
        collection = _find_matching_collection(alias)
        if collection is not None:
            return _rename_datablock(bpy.data.collections, collection, target_name)
    return None


def _strip_scene_prefix(name: str):
    for prefix in ("CHEN_", "CHEN ", "Chen_", "Chen "):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def _normalize_helper_collection_tree(helper_collection):
    if helper_collection is None:
        return
    stack = list(helper_collection.children)
    while stack:
        collection = stack.pop()
        stack.extend(list(collection.children))
        stripped_name = _strip_scene_prefix(collection.name)
        if stripped_name != collection.name:
            _rename_datablock(bpy.data.collections, collection, stripped_name)


def _normalize_legacy_scene_names():
    for source_name, target_name in LEGACY_COLLECTION_NAME_PAIRS:
        _ensure_collection_alias(target_name, source_name)
    for source_name, target_name in LEGACY_OBJECT_NAME_PAIRS:
        _ensure_object_alias(target_name, source_name)
    helper_collection = bpy.data.collections.get(HELPER_COLLECTION_NAME)
    if helper_collection is not None:
        _normalize_helper_collection_tree(helper_collection)


def _find_stamped_node_group(group_name: str, library_path: str, tree_type: str = None):
    stamp = _library_stamp(library_path)
    if not stamp:
        group = bpy.data.node_groups.get(group_name)
        if group and (tree_type is None or group.bl_idname == tree_type):
            return group
        return None
    for group in bpy.data.node_groups:
        if not _name_matches_datablock(group_name, group.name):
            continue
        if tree_type is not None and group.bl_idname != tree_type:
            continue
        if group.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
            return group
    return None


def _stash_outdated_node_group(group_name: str, library_path: str, tree_type: str = None):
    stamp = _library_stamp(library_path)
    if not stamp:
        return
    group = bpy.data.node_groups.get(group_name)
    if group is None:
        return
    if tree_type is not None and group.bl_idname != tree_type:
        return
    if group.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
        return
    group.name = _make_backup_name(bpy.data.node_groups, group_name, "__OLD")


def _find_or_append_node_group_by_name(library_path: str, group_name: str, tree_type: str = None):
    group = _find_stamped_node_group(group_name, library_path, tree_type=tree_type)
    if group:
        _patch_node_tree_for_eevee_compat(group)
        return group
    _stash_outdated_node_group(group_name, library_path, tree_type=tree_type)
    group = _append_datablock_from_library(library_path, "node_groups", group_name)
    if group and (tree_type is None or group.bl_idname == tree_type):
        _patch_node_tree_for_eevee_compat(group)
        return group
    group = bpy.data.node_groups.get(group_name)
    if group and (tree_type is None or group.bl_idname == tree_type):
        _patch_node_tree_for_eevee_compat(group)
        return group
    return None


def _ensure_node_tree_uses_library_groups(node_tree, library_path: str, visited=None):
    if not node_tree or not library_path:
        return node_tree
    if node_tree.get("_endfield_face_group_local"):
        return node_tree

    visited = visited or set()
    tree_key = node_tree.as_pointer()
    if tree_key in visited:
        return node_tree
    visited.add(tree_key)

    for node in node_tree.nodes:
        if node.type != "GROUP" or not node.node_tree:
            continue
        target_group = node.node_tree
        if not target_group.get("_endfield_face_group_local"):
            rebound_group = _find_or_append_node_group_by_name(
                library_path,
                target_group.name,
                tree_type=target_group.bl_idname,
            )
            if rebound_group is not None:
                target_group = rebound_group
                if node.node_tree != rebound_group:
                    node.node_tree = rebound_group
        _ensure_node_tree_uses_library_groups(target_group, library_path, visited)

    return node_tree


def _ensure_material_uses_library_node_groups(material, library_path: str):
    if not material or not material.use_nodes or not material.node_tree:
        return material
    _ensure_node_tree_uses_library_groups(material.node_tree, library_path)
    _patch_material_for_eevee_compat(material)
    return material


def _find_or_append_material_by_name(library_path: str, material_name: str):
    material = _find_stamped_material(material_name, library_path)
    if material:
        return _ensure_material_uses_library_node_groups(material, library_path)
    _stash_outdated_material(material_name, library_path)
    material = _append_datablock_from_library(library_path, "materials", material_name)
    if material:
        return _ensure_material_uses_library_node_groups(material, library_path)
    material = bpy.data.materials.get(material_name)
    if material:
        return _ensure_material_uses_library_node_groups(material, library_path)
    return None


def _find_stamped_world(world_name: str, library_path: str):
    stamp = _library_stamp(library_path)
    if not stamp:
        return bpy.data.worlds.get(world_name)
    for world in bpy.data.worlds:
        if _name_matches_datablock(world_name, world.name) and world.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
            return world
    return None


def _stash_outdated_world(world_name: str, library_path: str):
    world = bpy.data.worlds.get(world_name)
    stamp = _library_stamp(library_path)
    if world is None or not stamp:
        return
    if world.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
        return
    world.name = _make_backup_name(bpy.data.worlds, world_name, "__OLD")


def _find_or_append_first_material(library_path: str, candidates):
    for name in candidates:
        material = _find_or_append_material_by_name(library_path, name)
        if material:
            return material
    return None


def _clear_node_group_interface(node_group):
    interface = getattr(node_group, "interface", None)
    items_tree = getattr(interface, "items_tree", None)
    if interface is None or items_tree is None:
        return
    for item in list(items_tree):
        try:
            interface.remove(item)
        except Exception:
            pass


def _ensure_eevee_shader_info_compat_group():
    group = bpy.data.node_groups.get(EEVEE_SHADER_INFO_COMPAT_GROUP_NAME)
    if group is not None and group.bl_idname != "ShaderNodeTree":
        group.name = _make_backup_name(bpy.data.node_groups, EEVEE_SHADER_INFO_COMPAT_GROUP_NAME, "__OLD")
        group = None
    if group is None:
        group = bpy.data.node_groups.new(EEVEE_SHADER_INFO_COMPAT_GROUP_NAME, "ShaderNodeTree")

    if group.get("_endfield_eevee_shader_info_compat_version") == EEVEE_SHADER_INFO_COMPAT_GROUP_VERSION:
        return group

    nodes = group.nodes
    links = group.links
    nodes.clear()
    _clear_node_group_interface(group)

    interface = group.interface
    interface.new_socket(name="WorldPosition", in_out="INPUT", socket_type="NodeSocketVector")
    interface.new_socket(name="Normal", in_out="INPUT", socket_type="NodeSocketVector")
    interface.new_socket(name="Diffuse Shading", in_out="OUTPUT", socket_type="NodeSocketFloat")
    interface.new_socket(name="Cast Shadows", in_out="OUTPUT", socket_type="NodeSocketFloat")
    interface.new_socket(name="Self Shadows", in_out="OUTPUT", socket_type="NodeSocketFloat")
    interface.new_socket(name="Ambient Lighting", in_out="OUTPUT", socket_type="NodeSocketColor")
    interface.new_socket(name="Half-lambert factor", in_out="OUTPUT", socket_type="NodeSocketFloat")

    group_input = nodes.new("NodeGroupInput")
    group_input.location = (-420.0, 0.0)

    one_value = nodes.new("ShaderNodeValue")
    one_value.location = (-180.0, 80.0)
    one_value.outputs["Value"].default_value = 1.0

    ambient_rgb = nodes.new("ShaderNodeRGB")
    ambient_rgb.location = (-180.0, -80.0)
    ambient_rgb.outputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)

    group_output = nodes.new("NodeGroupOutput")
    group_output.location = (120.0, 20.0)

    links.new(one_value.outputs["Value"], group_output.inputs["Diffuse Shading"])
    links.new(one_value.outputs["Value"], group_output.inputs["Cast Shadows"])
    links.new(one_value.outputs["Value"], group_output.inputs["Self Shadows"])
    links.new(ambient_rgb.outputs["Color"], group_output.inputs["Ambient Lighting"])
    links.new(one_value.outputs["Value"], group_output.inputs["Half-lambert factor"])

    group["_endfield_eevee_shader_info_compat_version"] = EEVEE_SHADER_INFO_COMPAT_GROUP_VERSION
    return group


def _ensure_eevee_shader_info_lit_compat_group():
    group = bpy.data.node_groups.get(EEVEE_SHADER_INFO_LIT_COMPAT_GROUP_NAME)
    if group is not None and group.bl_idname != "ShaderNodeTree":
        group.name = _make_backup_name(bpy.data.node_groups, EEVEE_SHADER_INFO_LIT_COMPAT_GROUP_NAME, "__OLD")
        group = None
    if group is None:
        group = bpy.data.node_groups.new(EEVEE_SHADER_INFO_LIT_COMPAT_GROUP_NAME, "ShaderNodeTree")

    if group.get("_endfield_eevee_shader_info_lit_compat_version") == EEVEE_SHADER_INFO_LIT_COMPAT_GROUP_VERSION:
        return group

    nodes = group.nodes
    links = group.links
    nodes.clear()
    _clear_node_group_interface(group)

    interface = group.interface
    interface.new_socket(name="WorldPosition", in_out="INPUT", socket_type="NodeSocketVector")
    interface.new_socket(name="Normal", in_out="INPUT", socket_type="NodeSocketVector")
    interface.new_socket(name="Diffuse Shading", in_out="OUTPUT", socket_type="NodeSocketFloat")
    interface.new_socket(name="Cast Shadows", in_out="OUTPUT", socket_type="NodeSocketFloat")
    interface.new_socket(name="Self Shadows", in_out="OUTPUT", socket_type="NodeSocketFloat")
    interface.new_socket(name="Ambient Lighting", in_out="OUTPUT", socket_type="NodeSocketColor")
    interface.new_socket(name="Half-lambert factor", in_out="OUTPUT", socket_type="NodeSocketFloat")

    group_input = nodes.new("NodeGroupInput")
    group_input.location = (-860.0, 0.0)

    normalize = nodes.new("ShaderNodeVectorMath")
    normalize.operation = "NORMALIZE"
    normalize.location = (-620.0, 40.0)

    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.location = (-380.0, 40.0)
    diffuse.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)

    shader_to_rgb = nodes.new("ShaderNodeShaderToRGB")
    shader_to_rgb.location = (-120.0, 40.0)

    rgb_to_bw = nodes.new("ShaderNodeRGBToBW")
    rgb_to_bw.location = (120.0, 40.0)

    half_lambert = nodes.new("ShaderNodeMath")
    half_lambert.operation = "MULTIPLY_ADD"
    half_lambert.use_clamp = True
    half_lambert.inputs[1].default_value = 0.5
    half_lambert.inputs[2].default_value = 0.5
    half_lambert.location = (360.0, -120.0)

    group_output = nodes.new("NodeGroupOutput")
    group_output.location = (640.0, 20.0)

    links.new(group_input.outputs["Normal"], normalize.inputs[0])
    links.new(normalize.outputs["Vector"], diffuse.inputs["Normal"])
    links.new(diffuse.outputs["BSDF"], shader_to_rgb.inputs["Shader"])
    links.new(shader_to_rgb.outputs["Color"], rgb_to_bw.inputs["Color"])
    links.new(shader_to_rgb.outputs["Color"], group_output.inputs["Ambient Lighting"])
    links.new(rgb_to_bw.outputs["Val"], group_output.inputs["Diffuse Shading"])
    links.new(rgb_to_bw.outputs["Val"], group_output.inputs["Cast Shadows"])
    links.new(rgb_to_bw.outputs["Val"], group_output.inputs["Self Shadows"])
    links.new(rgb_to_bw.outputs["Val"], half_lambert.inputs[0])
    links.new(half_lambert.outputs["Value"], group_output.inputs["Half-lambert factor"])

    group["_endfield_eevee_shader_info_lit_compat_version"] = EEVEE_SHADER_INFO_LIT_COMPAT_GROUP_VERSION
    return group


def _ensure_eevee_screenspace_info_compat_group():
    group = bpy.data.node_groups.get(EEVEE_SCREENSPACE_INFO_COMPAT_GROUP_NAME)
    if group is not None and group.bl_idname != "ShaderNodeTree":
        group.name = _make_backup_name(bpy.data.node_groups, EEVEE_SCREENSPACE_INFO_COMPAT_GROUP_NAME, "__OLD")
        group = None
    if group is None:
        group = bpy.data.node_groups.new(EEVEE_SCREENSPACE_INFO_COMPAT_GROUP_NAME, "ShaderNodeTree")

    if group.get("_endfield_eevee_screenspace_info_compat_version") == EEVEE_SCREENSPACE_INFO_COMPAT_GROUP_VERSION:
        return group

    nodes = group.nodes
    links = group.links
    nodes.clear()
    _clear_node_group_interface(group)

    interface = group.interface
    interface.new_socket(name="View Position", in_out="INPUT", socket_type="NodeSocketVector")
    interface.new_socket(name="Scene Color", in_out="OUTPUT", socket_type="NodeSocketColor")
    interface.new_socket(name="Scene Depth", in_out="OUTPUT", socket_type="NodeSocketFloat")

    group_input = nodes.new("NodeGroupInput")
    group_input.location = (-520.0, 0.0)

    separate_xyz = nodes.new("ShaderNodeSeparateXYZ")
    separate_xyz.location = (-280.0, -80.0)

    abs_depth = nodes.new("ShaderNodeMath")
    abs_depth.operation = "ABSOLUTE"
    abs_depth.location = (-40.0, -80.0)

    scene_color = nodes.new("ShaderNodeRGB")
    scene_color.location = (-40.0, 80.0)
    scene_color.outputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)

    group_output = nodes.new("NodeGroupOutput")
    group_output.location = (200.0, 0.0)

    links.new(group_input.outputs["View Position"], separate_xyz.inputs["Vector"])
    links.new(separate_xyz.outputs["Z"], abs_depth.inputs[0])
    links.new(scene_color.outputs["Color"], group_output.inputs["Scene Color"])
    links.new(abs_depth.outputs["Value"], group_output.inputs["Scene Depth"])

    group["_endfield_eevee_screenspace_info_compat_version"] = EEVEE_SCREENSPACE_INFO_COMPAT_GROUP_VERSION
    return group


def _is_shader_info_placeholder_node(node) -> bool:
    if node is None or getattr(node, "bl_idname", "") != "NodeUndefined":
        return False
    if node.get("_endfield_eevee_compat_disabled"):
        return False
    label = f"{getattr(node, 'name', '')} {getattr(node, 'label', '')}".lower()
    return "shader info" in label or "shaderinfo" in label


def _is_screenspace_info_placeholder_node(node) -> bool:
    if node is None or getattr(node, "bl_idname", "") != "NodeUndefined":
        return False
    if node.get("_endfield_eevee_compat_disabled"):
        return False
    label = f"{getattr(node, 'name', '')} {getattr(node, 'label', '')}".lower()
    return "screenspace info" in label or "screen space info" in label


def _node_tree_uses_face_shader_compat(node_tree) -> bool:
    if node_tree is None:
        return False
    name = getattr(node_tree, "name", "")
    return "FaceBase" in name or "BaseFace" in name

def _copy_socket_default_value(source_socket, target_socket):
    if not hasattr(source_socket, "default_value") or not hasattr(target_socket, "default_value"):
        return
    try:
        value = source_socket.default_value
        if hasattr(value, "copy"):
            value = value.copy()
        elif isinstance(value, (list, tuple)):
            value = tuple(value)
        target_socket.default_value = value
    except Exception:
        pass


def _find_socket_by_name(sockets, socket_name: str):
    if not socket_name:
        return None
    socket = sockets.get(socket_name)
    if socket is not None:
        return socket
    for item in sockets:
        if item.name == socket_name:
            return item
    return None


def _replace_undefined_placeholder(node_tree, node, compat_group, compat_label: str) -> int:
    input_links = {}
    input_defaults = {}
    output_links = []
    for socket in node.inputs:
        if socket.is_linked and socket.links:
            from_socket = socket.links[0].from_socket
            input_links[socket.name] = (from_socket.node, from_socket.name)
        else:
            input_defaults[socket.name] = socket
    for socket in node.outputs:
        for link in socket.links:
            to_socket = link.to_socket
            output_links.append((socket.name, to_socket.node, to_socket.name))

    old_state = {
        "name": node.name,
        "label": node.label,
        "location": tuple(node.location),
        "parent": node.parent,
        "width": getattr(node, "width", 140.0),
        "hide": getattr(node, "hide", False),
        "mute": getattr(node, "mute", False),
        "use_custom_color": getattr(node, "use_custom_color", False),
        "color": tuple(getattr(node, "color", (0.608, 0.608, 0.608))),
    }

    new_node = node_tree.nodes.new("ShaderNodeGroup")
    new_node.node_tree = compat_group
    new_node.name = f"{old_state['name']}_Compat"
    new_node.label = old_state["label"] or f"{compat_label} (Compat)"
    new_node.location = old_state["location"]
    new_node.parent = old_state["parent"]
    new_node.width = old_state["width"]
    new_node.hide = old_state["hide"]
    new_node.mute = old_state["mute"]
    new_node.use_custom_color = old_state["use_custom_color"]
    if old_state["use_custom_color"]:
        new_node.color = old_state["color"]

    for socket in node.inputs:
        for link in list(socket.links):
            node_tree.links.remove(link)
    for socket in node.outputs:
        for link in list(socket.links):
            node_tree.links.remove(link)

    for socket_name, (from_node, from_socket_name) in input_links.items():
        target_socket = _find_socket_by_name(new_node.inputs, socket_name)
        from_socket = _find_socket_by_name(from_node.outputs, from_socket_name) if from_node is not None else None
        if target_socket is not None and from_socket is not None:
            node_tree.links.new(from_socket, target_socket)
    for socket_name, source_socket in input_defaults.items():
        target_socket = _find_socket_by_name(new_node.inputs, socket_name)
        if target_socket is not None:
            _copy_socket_default_value(source_socket, target_socket)
    for socket_name, to_node, to_socket_name in output_links:
        from_socket = _find_socket_by_name(new_node.outputs, socket_name)
        to_socket = _find_socket_by_name(to_node.inputs, to_socket_name) if to_node is not None else None
        if from_socket is not None and to_socket is not None:
            node_tree.links.new(from_socket, to_socket)

    node["_endfield_eevee_compat_disabled"] = True
    node.label = f"{compat_label} (Legacy Disabled)"
    node.hide = True
    node.location = (old_state["location"][0], old_state["location"][1] - 180.0)
    return 1


def _replace_shader_info_placeholder(node_tree, node, compat_group) -> int:
    return _replace_undefined_placeholder(node_tree, node, compat_group, "Shader Info")


def _replace_screenspace_info_placeholder(node_tree, node, compat_group) -> int:
    return _replace_undefined_placeholder(node_tree, node, compat_group, "Screenspace Info")


def _patch_node_tree_for_eevee_compat(node_tree, visited=None) -> int:
    if not _requires_eevee_compat():
        return 0
    if not node_tree:
        return 0

    visited = visited or set()
    tree_key = node_tree.as_pointer()
    if tree_key in visited:
        return 0
    visited.add(tree_key)

    patched = 0
    for node in list(node_tree.nodes):
        if node.type == "GROUP" and node.node_tree:
            patched += _patch_node_tree_for_eevee_compat(node.node_tree, visited)

    shader_compat_group = None
    shader_lit_compat_group = None
    screenspace_compat_group = None
    for node in list(node_tree.nodes):
        if _is_shader_info_placeholder_node(node):
            if _node_tree_uses_face_shader_compat(node_tree):
                if shader_compat_group is None:
                    shader_compat_group = _ensure_eevee_shader_info_compat_group()
                patched += _replace_shader_info_placeholder(node_tree, node, shader_compat_group)
            else:
                if shader_lit_compat_group is None:
                    shader_lit_compat_group = _ensure_eevee_shader_info_lit_compat_group()
                patched += _replace_shader_info_placeholder(node_tree, node, shader_lit_compat_group)
            continue
        if _is_screenspace_info_placeholder_node(node):
            if screenspace_compat_group is None:
                screenspace_compat_group = _ensure_eevee_screenspace_info_compat_group()
            patched += _replace_screenspace_info_placeholder(node_tree, node, screenspace_compat_group)
    return patched


def _looks_like_endfield_node_tree(node_tree) -> bool:
    if not node_tree:
        return False
    if node_tree.get("_endfield_face_group_local"):
        return True
    name = node_tree.name.lower()
    if "endfield" in name:
        return True
    for keywords in SHADER_GROUP_KEYWORDS.values():
        for keyword in keywords:
            if keyword.lower() in name:
                return True
    return False


def _patch_material_for_eevee_compat(material, visited=None) -> int:
    if not _requires_eevee_compat():
        return 0
    if not material or not material.use_nodes or not material.node_tree:
        return 0
    return _patch_node_tree_for_eevee_compat(material.node_tree, visited=visited)


def _patch_all_endfield_materials_for_eevee_compat() -> int:
    if not _requires_eevee_compat():
        return 0
    visited = set()
    patched = 0
    for material in bpy.data.materials:
        if _find_main_shader_node(material) is None:
            continue
        patched += _patch_material_for_eevee_compat(material, visited=visited)
    for node_tree in bpy.data.node_groups:
        if getattr(node_tree, "bl_idname", "") != "ShaderNodeTree":
            continue
        if not _looks_like_endfield_node_tree(node_tree):
            continue
        patched += _patch_node_tree_for_eevee_compat(node_tree, visited=visited)
    return patched


def _prime_preset_resources(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    if not library:
        return False

    material_names = []
    seen = set()
    for candidate_group in (
        TEMPLATE_MATERIAL_PREFS.values(),
        ALPHA_TEMPLATE_PREFS.values(),
        OUTLINE_MATERIAL_PREFS.values(),
        SPECIAL_MATERIAL_PREFS.values(),
    ):
        for names in candidate_group:
            for name in names:
                if name in seen:
                    continue
                seen.add(name)
                material_names.append(name)

    for material_name in material_names:
        _find_or_append_material_by_name(library, material_name)

    for group_names in GEOMETRY_NODE_PREFS.values():
        _find_or_append_node_group(library, group_names)

    if settings.migrate_source_environment:
        _ensure_target_world(settings)
    if settings.shader_type == "FACE" and (settings.create_helper_rig or settings.auto_geometry_nodes):
        _ensure_sun_rig(settings)
    return True


def _find_or_append_node_group(library_path: str, candidates):
    for group_name in candidates:
        group = _find_or_append_node_group_by_name(library_path, group_name, tree_type="GeometryNodeTree")
        if group:
            return group
    return None


def _find_or_append_collection(library_path: str, collection_name: str):
    collection = bpy.data.collections.get(collection_name)
    if collection:
        return collection
    if _append_datablock_from_library(library_path, "collections", collection_name):
        return bpy.data.collections.get(collection_name)
    return None


def _find_or_append_object(library_path: str, object_name: str):
    obj = _find_stamped_object(object_name, library_path)
    if obj:
        return obj
    _stash_outdated_object(object_name, library_path)
    obj = _append_datablock_from_library(library_path, "objects", object_name)
    if obj:
        return obj
    return _find_matching_object(object_name)


def _find_or_append_world(library_path: str, world_name: str = SOURCE_WORLD_NAME):
    world = _find_stamped_world(world_name, library_path)
    if world:
        return world
    _stash_outdated_world(world_name, library_path)
    world = _append_datablock_from_library(library_path, "worlds", world_name)
    if world:
        return world
    world = bpy.data.worlds.get(world_name)
    if world:
        return world
    return bpy.data.worlds[0] if bpy.data.worlds else None


def _ensure_target_world(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    if not library:
        return None

    expected_stamp = _library_stamp(library)
    existing = bpy.data.worlds.get(TARGET_WORLD_NAME)
    if existing is not None:
        if not expected_stamp or existing.get(SOURCE_LIBRARY_STAMP_KEY) == expected_stamp:
            return existing
        existing.name = _make_backup_name(bpy.data.worlds, TARGET_WORLD_NAME, "__OLD")

    source_world = _find_or_append_world(library)
    if source_world is None:
        return None

    if source_world.name != TARGET_WORLD_NAME:
        source_world.name = TARGET_WORLD_NAME
    if expected_stamp:
        source_world[SOURCE_LIBRARY_STAMP_KEY] = expected_stamp
    return source_world


def _cleanup_unused_world_backups():
    for world in list(bpy.data.worlds):
        if world.name.startswith(f"{SOURCE_WORLD_NAME}__OLD") and world.users == 0:
            bpy.data.worlds.remove(world)


def _create_fallback_material(name: str):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "mmd_base_tex"
    tex.label = "Mmd Base Tex"
    tex.location = (-520.0, 120.0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (-170.0, 120.0)
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (120.0, 120.0)

    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return material


def _create_fallback_alpha_material(name: str):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "mmd_base_tex"
    tex.location = (-420.0, 120.0)
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent.location = (-160.0, 20.0)
    mix = nodes.new("ShaderNodeMixShader")
    mix.location = (80.0, 100.0)
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (300.0, 100.0)

    links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(transparent.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    _set_alpha_blend_mode(material)
    return material


def _create_shadow_proxy_material():
    material = bpy.data.materials.new("Only Shadow Proxy")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    holdout = nodes.new("ShaderNodeHoldout")
    holdout.location = (-80.0, 60.0)
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (120.0, 60.0)
    links.new(holdout.outputs["Holdout"], out.inputs["Surface"])
    return material


def _create_fallback_outline_material(name: str):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "mmd_base_tex"
    tex.label = "Outline Base"
    tex.location = (-860.0, 180.0)

    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.location = (-620.0, -60.0)

    shader_to_rgb = nodes.new("ShaderNodeShaderToRGB")
    shader_to_rgb.location = (-380.0, -60.0)

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-140.0, -60.0)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.7

    rgb_to_bw = nodes.new("ShaderNodeRGBToBW")
    rgb_to_bw.location = (20.0, -60.0)

    mix_rgb = nodes.new("ShaderNodeMixRGB")
    mix_rgb.location = (220.0, 140.0)
    mix_rgb.blend_type = "MIX"
    mix_rgb.inputs["Color2"].default_value = (0.02, 0.02, 0.02, 1.0)

    emission = nodes.new("ShaderNodeEmission")
    emission.location = (460.0, 140.0)

    transparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent.location = (460.0, -60.0)

    mix_shader = nodes.new("ShaderNodeMixShader")
    mix_shader.location = (720.0, 100.0)

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (960.0, 100.0)

    links.new(tex.outputs["Color"], diffuse.inputs["Color"])
    links.new(diffuse.outputs["BSDF"], shader_to_rgb.inputs["Shader"])
    links.new(shader_to_rgb.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], rgb_to_bw.inputs["Color"])
    links.new(rgb_to_bw.outputs["Val"], mix_rgb.inputs["Fac"])
    links.new(tex.outputs["Color"], mix_rgb.inputs["Color1"])
    links.new(mix_rgb.outputs["Color"], emission.inputs["Color"])
    links.new(tex.outputs["Alpha"], mix_shader.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix_shader.inputs[1])
    links.new(emission.outputs["Emission"], mix_shader.inputs[2])
    links.new(mix_shader.outputs["Shader"], out.inputs["Surface"])

    _set_alpha_blend_mode(material)
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = True
    return material


def _outline_material_candidates(settings: ENDFIELD_PG_Settings, obj=None, base_material=None):
    if settings.shader_type == "BODY":
        return ["Chen_Cmmom_outline", "Endmin Cloth Outline", "FemEndmin outline", "Chen_Face_outline"]
    if settings.shader_type == "CLOTH":
        return ["Chen_cloth_outline", "Endmin Cloth Outline", "FemEndmin outline", "Chen_Cmmom_outline", "Chen_Face_outline"]
    return list(OUTLINE_MATERIAL_PREFS[settings.shader_type])


def _is_lash_or_brow_target(obj=None, source_material=None) -> bool:
    keywords = ("brow", "lash", "eyelash", "眉", "睫")
    names = []
    if obj is not None:
        names.append(obj.name.lower())
    if source_material is not None:
        names.append(source_material.name.lower())
        shader_type = _detect_shader_type_from_material(source_material)
        if shader_type == "BROW":
            return True
    return any(any(keyword in name for keyword in keywords) for name in names)


def _template_material_candidates(shader_type: str, obj=None, source_material=None):
    if shader_type == "PUPIL" and _is_lash_or_brow_target(obj, source_material):
        return list(TEMPLATE_MATERIAL_PREFS["BROW"])
    return list(TEMPLATE_MATERIAL_PREFS[shader_type])


def _ensure_template_material(settings: ENDFIELD_PG_Settings, shader_type: str = None, obj=None, source_material=None):
    shader_type = shader_type or settings.shader_type
    resolved_shader_type = "BROW" if shader_type == "PUPIL" and _is_lash_or_brow_target(obj, source_material) else shader_type
    library = _effective_library_path(settings)
    material = _find_or_append_first_material(library, _template_material_candidates(resolved_shader_type, obj, source_material))
    if material:
        return material
    fallback_name = f"ENDFIELD_{resolved_shader_type}_Fallback"
    existing = bpy.data.materials.get(fallback_name)
    return existing or _create_fallback_material(fallback_name)


def _ensure_outline_material(settings: ENDFIELD_PG_Settings, obj=None, base_material=None):
    library = _effective_library_path(settings)
    material = _find_or_append_first_material(library, _outline_material_candidates(settings, obj, base_material))
    if material:
        if hasattr(material, "use_backface_culling"):
            material.use_backface_culling = True
        return material

    material = bpy.data.materials.get("ENDFIELD_Outline")
    if material:
        return material

    return _create_fallback_outline_material("ENDFIELD_Outline")


def _ensure_shadow_proxy_material(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    material = _find_or_append_first_material(library, SPECIAL_MATERIAL_PREFS["SHADOW_PROXY"])
    if material:
        return material
    existing = bpy.data.materials.get("Only Shadow Proxy")
    return existing or _create_shadow_proxy_material()


def _set_alpha_blend_mode(material):
    try:
        material.blend_method = "HASHED"
    except Exception:
        pass
    if hasattr(material, "surface_render_method"):
        for mode in ("DITHERED", "BLENDED"):
            try:
                material.surface_render_method = mode
                break
            except Exception:
                continue
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = True


def _load_image(path_value: str, colorspace: str):
    abs_path = _safe_abs_path(path_value)
    if not abs_path or not os.path.exists(abs_path):
        return None
    try:
        image = bpy.data.images.load(abs_path, check_existing=True)
    except RuntimeError:
        return None
    try:
        image.colorspace_settings.name = colorspace
    except Exception:
        pass
    return image


def _role_path_looks_suspicious(path_value: str, role_id: str, base_path: str = "") -> bool:
    if not path_value or role_id == "tex_d":
        return False

    abs_path = _safe_abs_path(path_value)
    if not abs_path or not os.path.exists(abs_path):
        return False

    if base_path and _same_file_path(path_value, base_path):
        score = _texture_filename_match_score(os.path.basename(abs_path), role_id)
        return score <= 0

    return False


def _load_role_image(path_value: str, colorspace: str, role_id: str = "", base_path: str = ""):
    if role_id and _role_path_looks_suspicious(path_value, role_id, base_path):
        return None
    return _load_image(path_value, colorspace)


def _placeholder_rgba_for_role(role_id: str):
    if role_id == "tex_n":
        return (0.5, 0.5, 1.0, 1.0)
    if role_id == "tex_d":
        return (0.8, 0.8, 0.8, 1.0)
    return (0.0, 0.0, 0.0, 1.0)


def _ensure_placeholder_image(role_id: str, colorspace: str = None):
    colorspace = colorspace or ROLE_COLORSPACE_DEFAULTS.get(role_id, "Non-Color")
    safe_colorspace = re.sub(r"[^0-9A-Za-z]+", "_", colorspace).strip("_") or "Default"
    image_name = f"ENDFIELD_EMPTY_{role_id.upper()}_{safe_colorspace}"
    image = bpy.data.images.get(image_name)
    if image is None:
        image = bpy.data.images.new(image_name, width=1, height=1, alpha=True)
    try:
        image.generated_color = _placeholder_rgba_for_role(role_id)
    except Exception:
        pass
    try:
        image.colorspace_settings.name = colorspace
    except Exception:
        pass
    image["endfield_placeholder"] = True
    image["endfield_role_id"] = role_id
    return image


def _iter_tex_image_nodes(material):
    if not material or not material.use_nodes or not material.node_tree:
        return []
    return [node for node in material.node_tree.nodes if node.type == "TEX_IMAGE"]


def _normalize_socket_name(socket_name: str) -> str:
    value = (socket_name or "").strip().casefold()
    replacements = {
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
        "。": ".",
        "，": ",",
        "：": ":",
        "；": ";",
        "－": "-",
        "　": "",
        " ": "",
        "non-color": "non_color",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return value


def _classify_texture_input_socket(socket_name: str) -> str:
    normalized = _normalize_socket_name(socket_name)

    if normalized in {"_d(srgb)r.g.b", "_d(srgb)rgb", "_d(srgb)color"}:
        return "tex_d_color"
    if normalized in {"_d(srgb).a", "_d(srgb)a", "d_alpha"}:
        return "tex_d_alpha"

    if normalized.startswith("_n(") or normalized == "_n":
        if normalized.endswith(".a") or normalized.endswith(")a"):
            return "tex_n_alpha"
        return "tex_n_color"
    if normalized.startswith("_hn(") or normalized == "_hn":
        if normalized.endswith(".a") or normalized.endswith(")a"):
            return "tex_n_alpha"
        return "tex_n_color"

    if normalized.startswith("_p(") or normalized == "_p":
        if normalized.endswith(".a") or normalized.endswith(")a"):
            return "tex_p_alpha"
        return "tex_p_color"

    if normalized in {
        "_m",
        "_m(non_color)",
        "_m(non_color)r.g.b",
        "_m(非色彩)",
        "_m(非色彩)r.g.b",
        "_m(非色彩non_color)",
        "_m(非色彩non_color)r.g.b",
    }:
        return "tex_m_color"

    if normalized in {
        "_e",
        "_e(non_color)",
        "_e(non_color)r.g.b",
        "_e(非色彩)",
        "_e(非色彩)r.g.b",
        "_e(非色彩non_color)",
        "_e(非色彩non_color)r.g.b",
    }:
        return "tex_e_color"

    return ""


def _node_signature(node) -> str:
    parts = [node.name.lower(), node.label.lower()]
    image = getattr(node, "image", None)
    if image and not image.get("endfield_placeholder"):
        parts.append(image.name.lower())
        if image.filepath:
            parts.append(image.filepath.lower())
    return " ".join(parts)


def _collect_upstream_tex_image_nodes(socket, add_node, visited):
    if socket is None:
        return
    node = getattr(socket, "node", None)
    if node is None:
        return

    key = (node.as_pointer(), getattr(socket, "identifier", socket.name))
    if key in visited:
        return
    visited.add(key)

    if node.type == "TEX_IMAGE":
        add_node(node)
        return

    for input_socket in getattr(node, "inputs", ()):
        if not input_socket.is_linked:
            continue
        for link in input_socket.links:
            _collect_upstream_tex_image_nodes(link.from_socket, add_node, visited)


def _find_nodes_for_role(material, role_id: str):
    if not material or not material.use_nodes or not material.node_tree:
        return []

    found = []
    seen = set()

    def add_node(node):
        if not node or node.type != "TEX_IMAGE":
            return
        key = getattr(node, "name_full", node.name)
        if key in seen:
            return
        seen.add(key)
        found.append(node)

    sockets = _shader_input_sockets_for_role(material, role_id)
    if sockets:
        visited = set()
        for socket in sockets.values():
            if not socket or not socket.is_linked:
                continue
            for link in socket.links:
                _collect_upstream_tex_image_nodes(link.from_socket, add_node, visited)
        return found

    tags = ROLE_SEARCH_TAGS.get(role_id, [])
    for node in _iter_tex_image_nodes(material):
        text = _node_signature(node)
        if any(tag in text for tag in tags):
            add_node(node)
    return found


def _main_shader_group_node(material):
    try:
        return _find_main_shader_node(material)
    except Exception:
        return None


def _shader_input_sockets_for_role(material, role_id: str):
    group_node = _main_shader_group_node(material)
    if group_node is None:
        return {}

    inputs = {}
    for socket in group_node.inputs:
        tag = _classify_texture_input_socket(socket.name)
        if role_id == "tex_d":
            if tag == "tex_d_color":
                inputs["color"] = socket
            elif tag == "tex_d_alpha":
                inputs["alpha"] = socket
        elif role_id == "tex_n":
            if tag == "tex_n_color":
                inputs["color"] = socket
            elif tag == "tex_n_alpha":
                inputs["alpha"] = socket
        elif role_id == "tex_p":
            if tag == "tex_p_color":
                inputs["color"] = socket
            elif tag == "tex_p_alpha":
                inputs["alpha"] = socket
        elif role_id == "tex_m":
            if tag == "tex_m_color":
                inputs["color"] = socket
        elif role_id == "tex_e":
            if tag == "tex_e_color":
                inputs["color"] = socket
    return inputs


def _create_linked_role_node(material, role_id: str):
    if not material.use_nodes or not material.node_tree:
        return None
    sockets = _shader_input_sockets_for_role(material, role_id)
    if not sockets:
        return None

    node = material.node_tree.nodes.new("ShaderNodeTexImage")
    node.name = role_id
    node.label = role_id
    node.location = (-980.0, -220.0 - 120.0 * len(_iter_tex_image_nodes(material)))
    links = material.node_tree.links
    if "color" in sockets:
        links.new(node.outputs["Color"], sockets["color"])
    if "alpha" in sockets:
        links.new(node.outputs["Alpha"], sockets["alpha"])
    return node


def _find_or_create_nodes_for_role(material, role_id: str):
    found = _find_nodes_for_role(material, role_id)
    if found:
        return found
    created = _create_linked_role_node(material, role_id)
    if created is not None:
        return [created]
    return []


def _node_matches_role(node, role_id: str) -> bool:
    return any(tag in _node_signature(node) for tag in ROLE_SEARCH_TAGS.get(role_id, []))


def _assign_image_to_role_nodes(material, role_id: str, image, assigned_names, fallback_position: str = ""):
    nodes = [node for node in _find_nodes_for_role(material, role_id) if node.name not in assigned_names]
    if not nodes:
        free_nodes = [node for node in _iter_tex_image_nodes(material) if node.name not in assigned_names]
        if free_nodes:
            if fallback_position == "last":
                nodes = [free_nodes[-1]]
            elif fallback_position == "first":
                nodes = [free_nodes[0]]
    for node in nodes:
        node.image = image
        assigned_names.add(node.name)


def _rebind_outline_material_textures(material, loaded_images):
    if not material or not material.use_nodes or not material.node_tree:
        return

    assigned_names = set()
    tex_d_image = loaded_images.get("tex_d") or _ensure_placeholder_image("tex_d", ROLE_COLORSPACE_DEFAULTS["tex_d"])
    tex_st_image = loaded_images.get("tex_st") or _ensure_placeholder_image("tex_st", ROLE_COLORSPACE_DEFAULTS["tex_st"])
    _assign_image_to_role_nodes(material, "tex_d", tex_d_image, assigned_names, fallback_position="first")
    _assign_image_to_role_nodes(material, "tex_st", tex_st_image, assigned_names, fallback_position="last")

    if tex_d_image and not assigned_names:
        tex_nodes = _iter_tex_image_nodes(material)
        if tex_nodes:
            tex_nodes[0].image = tex_d_image
            assigned_names.add(tex_nodes[0].name)

    for node in _iter_tex_image_nodes(material):
        if node.name in assigned_names:
            continue
        if _node_matches_role(node, "tex_st"):
            node.image = tex_st_image
            assigned_names.add(node.name)
            continue
        if _node_matches_role(node, "tex_d"):
            node.image = tex_d_image
            assigned_names.add(node.name)

    _ensure_alpha_links(material)
    if _has_alpha(loaded_images.get("tex_d"), material.name):
        _set_alpha_blend_mode(material)


def _load_images_from_settings(settings: ENDFIELD_PG_Settings):
    loaded = {}
    base_path = getattr(settings, "tex_d", "")
    for slot in TEXTURE_SLOT_LAYOUT[settings.shader_type]:
        image = _load_role_image(getattr(settings, slot.prop_id), slot.colorspace, slot.prop_id, base_path=base_path)
        if image:
            loaded[slot.prop_id] = image
    return loaded


def _apply_face_special_images(material, settings: ENDFIELD_PG_Settings):
    if material is None or _detect_shader_type_from_material(material) != "FACE":
        return {}

    node_tree = _ensure_local_face_shader_group(material)
    if node_tree is None:
        return {}

    loaded = {}
    sdf_image = _load_role_image(getattr(settings, "face_sdf_tex", ""), "Non-Color", "face_sdf_tex", base_path=getattr(settings, "tex_d", ""))
    if sdf_image is not None:
        for node in _find_face_sdf_image_nodes(node_tree):
            node.image = sdf_image
        loaded["face_sdf_tex"] = sdf_image

    cm_image = _load_role_image(getattr(settings, "face_cm_tex", ""), "Non-Color", "face_cm_tex", base_path=getattr(settings, "tex_d", ""))
    if cm_image is not None:
        for node in _find_face_cm_image_nodes(node_tree):
            node.image = cm_image
        loaded["face_cm_tex"] = cm_image

    return loaded


def _eye_object_prefers_brow_material(obj, source_material=None) -> bool:
    keywords = ("brow", "lash", "eyelash", "眉", "睫")

    def has_keywords(text: str) -> bool:
        text = (text or "").lower()
        return any(keyword in text for keyword in keywords)

    if obj and has_keywords(obj.name):
        return True

    if source_material and has_keywords(source_material.name):
        return True

    if obj:
        for slot in obj.material_slots:
            material = slot.material
            if material and has_keywords(material.name):
                return True

    return False


def _shader_type_for_object(settings: ENDFIELD_PG_Settings, obj, source_material=None) -> str:
    shader_type = settings.shader_type
    if shader_type == "FACE" and settings.face_integrated_eye_transparency and source_material is not None:
        for item in settings.face_iris_materials:
            if item.source_material == source_material:
                return "PUPIL"
        for item in settings.face_brow_materials:
            if item.source_material == source_material:
                return "BROW"
    if shader_type == "PUPIL" and _eye_object_prefers_brow_material(obj, source_material):
        return "BROW"
    return shader_type


def _extract_loaded_images_from_material(material, shader_type: str):
    loaded = {}
    if not material:
        return loaded

    for slot in TEXTURE_SLOT_LAYOUT.get(shader_type, []):
        for node in _find_nodes_for_role(material, slot.prop_id):
            image = getattr(node, "image", None)
            if _image_is_usable(image):
                loaded[slot.prop_id] = image
                break

    if "tex_d" not in loaded:
        for node in _iter_tex_image_nodes(material):
            image = getattr(node, "image", None)
            if _image_is_usable(image):
                loaded["tex_d"] = image
                break

    return loaded


def _apply_source_material_images(target_material, source_material, shader_type: str):
    loaded = _extract_loaded_images_from_material(source_material, shader_type)
    image = loaded.get("tex_d")
    if image is None:
        for node in _iter_tex_image_nodes(source_material):
            candidate = getattr(node, "image", None)
            if _image_is_usable(candidate):
                image = candidate
                break

    role_presence = {}
    if image is not None:
        loaded["tex_d"] = image
        role_presence["tex_d"] = True
    else:
        image = _ensure_placeholder_image("tex_d", "sRGB")
        role_presence["tex_d"] = False

    for node in _find_or_create_nodes_for_role(target_material, "tex_d"):
        node.image = image

    _ensure_alpha_links(target_material)
    return loaded, role_presence


def _ensure_outline_material_instance(
    settings: ENDFIELD_PG_Settings,
    obj,
    base_material,
    loaded_images,
    name_override: str = "",
):
    template = _ensure_outline_material(settings, obj, base_material)
    material_name = name_override or f"{template.name}_{obj.name}_Outline"
    material = bpy.data.materials.get(material_name)
    if material is None:
        material = template.copy()
        material.name = material_name

    _patch_material_for_eevee_compat(material)
    _rebind_outline_material_textures(material, loaded_images)
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = True
    return material


def _ensure_alpha_links(material):
    if not material.use_nodes or not material.node_tree:
        return
    base_nodes = _find_nodes_for_role(material, "tex_d")
    if not base_nodes:
        return
    alpha_output = base_nodes[0].outputs.get("Alpha")
    if not alpha_output:
        return

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    for node in nodes:
        if node.type == "GROUP":
            for socket_name in ("透明度", "Alpha", "D_Alpha", "_D(sRGB).A"):
                socket = node.inputs.get(socket_name)
                if socket and not socket.is_linked:
                    links.new(alpha_output, socket)
        if node.type == "BSDF_PRINCIPLED" and not node.inputs["Alpha"].is_linked:
            links.new(alpha_output, node.inputs["Alpha"])


def _has_alpha(image, material_name: str) -> bool:
    if "alpha" in material_name.lower():
        return True
    if not image:
        return False
    if "alpha" in image.name.lower():
        return True
    try:
        return image.channels >= 4
    except Exception:
        return False


def _image_is_usable(image) -> bool:
    if image is None:
        return False
    try:
        if image.get("endfield_placeholder"):
            return False
    except Exception:
        pass
    if getattr(image, "packed_file", None) is not None:
        return True
    filepath = bpy.path.abspath(image.filepath) if image.filepath else ""
    return bool(filepath and os.path.exists(filepath))


def _role_has_usable_image(material, role_id: str) -> bool:
    for node in _find_nodes_for_role(material, role_id):
        if _image_is_usable(getattr(node, "image", None)):
            return True
    return False


def _apply_textures(material, settings: ENDFIELD_PG_Settings, shader_type: str = None):
    shader_type = shader_type or settings.shader_type
    loaded = {}
    role_presence = {}
    base_path = getattr(settings, "tex_d", "")

    for slot in TEXTURE_SLOT_LAYOUT[shader_type]:
        image = _load_role_image(getattr(settings, slot.prop_id), slot.colorspace, slot.prop_id, base_path=base_path)
        if image:
            loaded[slot.prop_id] = image
        else:
            image = _ensure_placeholder_image(slot.prop_id, slot.colorspace)
        for node in _find_or_create_nodes_for_role(material, slot.prop_id):
            node.image = image

    _ensure_alpha_links(material)
    if shader_type == "FACE":
        loaded.update(_apply_face_special_images(material, settings))
    if _has_alpha(loaded.get("tex_d"), material.name):
        shader_type = _detect_shader_type_from_material(material) or settings.shader_type
        if shader_type not in {"PUPIL", "BROW"}:
            _set_alpha_blend_mode(material)

    for slot in TEXTURE_SLOT_LAYOUT[shader_type]:
        role_presence[slot.prop_id] = _role_has_usable_image(material, slot.prop_id)

    _apply_material_quality_correction(material, shader_type, role_presence)
    return loaded, role_presence


def _ensure_second_outline_slot(obj, outline_material, force_assign: bool):
    for index, slot in enumerate(obj.material_slots):
        if _is_outline_like(slot.material):
            obj.material_slots[index].material = outline_material
            return index

    if force_assign and len(obj.material_slots) < 2:
        while len(obj.material_slots) < 2:
            obj.data.materials.append(None)
        obj.material_slots[1].material = outline_material
        return 1

    obj.data.materials.append(outline_material)
    return len(obj.material_slots) - 1


def _ensure_hair_auxiliary_slots(obj, settings: ENDFIELD_PG_Settings, outline_material):
    shadow_proxy = _ensure_shadow_proxy_material(settings)

    shadow_index = None
    outline_index = None
    for index, slot in enumerate(obj.material_slots):
        material = slot.material
        if material == shadow_proxy or (material and material.name.lower() == shadow_proxy.name.lower()):
            shadow_index = index
        elif material and _is_outline_like(material):
            outline_index = index

    if shadow_index is None:
        obj.data.materials.append(shadow_proxy)
        shadow_index = len(obj.material_slots) - 1
    else:
        obj.material_slots[shadow_index].material = shadow_proxy

    if outline_index is None:
        obj.data.materials.append(outline_material)
        outline_index = len(obj.material_slots) - 1
    else:
        obj.material_slots[outline_index].material = outline_material

    return shadow_index, outline_index


def _ensure_outline_modifier(obj, settings: ENDFIELD_PG_Settings):
    modifier = None
    for item in obj.modifiers:
        if item.type == "SOLIDIFY" or "outline" in item.name.lower():
            modifier = item
            break
    if modifier is None:
        modifier = obj.modifiers.new(settings.outline_modifier_name, "SOLIDIFY")
    modifier.name = settings.outline_modifier_name
    modifier.thickness = settings.outline_thickness
    if hasattr(modifier, "offset"):
        modifier.offset = 1.0
    modifier.material_offset = settings.outline_material_offset
    if hasattr(modifier, "use_flip_normals"):
        modifier.use_flip_normals = True
    if hasattr(modifier, "use_rim_only"):
        modifier.use_rim_only = False
    if hasattr(modifier, "use_rim"):
        modifier.use_rim = False
    return modifier


def _attach_geo_modifier(obj, node_group, name: str):
    modifier = None
    for item in obj.modifiers:
        if item.type == "NODES" and (item.name == name or item.node_group == node_group):
            modifier = item
            break
    if modifier is None:
        modifier = obj.modifiers.new(name, "NODES")
    modifier.name = name
    modifier.node_group = node_group
    return modifier


def _resolve_modifier_input_identifier(modifier, query: str):
    if not modifier or not modifier.node_group:
        return None
    if query in modifier.keys():
        return query
    for item in modifier.node_group.interface.items_tree:
        if item.item_type != "SOCKET" or item.in_out != "INPUT":
            continue
        if item.identifier == query or item.name == query:
            return item.identifier
    return None


def _set_modifier_input(modifier, query: str, value):
    identifier = _resolve_modifier_input_identifier(modifier, query)
    if not identifier:
        return False
    try:
        modifier[identifier] = value
        return True
    except Exception:
        return False


def _clear_custom_split_normals(context, obj):
    mesh = obj.data
    if not getattr(mesh, "has_custom_normals", False):
        return
    view_layer = context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = [item for item in context.selected_objects]
    try:
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        view_layer.objects.active = obj
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="EDIT")
        if bpy.ops.mesh.select_all.poll():
            bpy.ops.mesh.select_all(action="SELECT")
        if bpy.ops.mesh.customdata_custom_splitnormals_clear.poll():
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")
    finally:
        bpy.ops.object.select_all(action="DESELECT")
        for selected in prev_selected:
            if selected and selected.name in bpy.data.objects:
                selected.select_set(True)
        if prev_active and prev_active.name in bpy.data.objects:
            view_layer.objects.active = prev_active


def _set_shade_smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def _ensure_uv0_attribute(obj):
    mesh = obj.data
    uv_layers = getattr(mesh, "uv_layers", None)
    source_layer = None
    if uv_layers:
        source_layer = uv_layers.get("UV0") or getattr(uv_layers, "active", None) or (uv_layers[0] if len(uv_layers) else None)

    attr = mesh.attributes.get("UV0")
    if attr is None:
        attr = mesh.attributes.new("UV0", "FLOAT2", "CORNER")
    if source_layer is None:
        for item in attr.data:
            item.vector = (0.0, 0.0)
        return
    for item, uv in zip(attr.data, source_layer.data):
        item.vector = tuple(uv.uv)


def _ensure_white_color_attribute(obj, domain: str):
    mesh = obj.data
    attr = mesh.attributes.get("Color")
    if attr is None or attr.domain != domain or attr.data_type != "BYTE_COLOR":
        if attr is not None:
            try:
                mesh.attributes.remove(attr)
            except Exception:
                pass
        attr = mesh.color_attributes.new("Color", "BYTE_COLOR", domain)
    for item in attr.data:
        item.color = (1.0, 1.0, 1.0, 1.0)


def _ensure_smoothnormal_attribute(obj):
    mesh = obj.data
    attr = mesh.attributes.get("smoothnormalWS")
    if attr is None:
        attr = mesh.attributes.new("smoothnormalWS", "FLOAT_VECTOR", "CORNER")
    try:
        mesh.calc_normals_split()
    except Exception:
        pass
    corner_normals = getattr(mesh, "corner_normals", None)
    if corner_normals and len(corner_normals) == len(attr.data):
        for item, normal in zip(attr.data, corner_normals):
            vector = getattr(normal, "vector", normal)
            item.vector = tuple(vector)
        return
    for loop, item in zip(mesh.loops, attr.data):
        item.vector = tuple(loop.normal)


def _ensure_required_geometry_attributes(obj, shader_type: str):
    if obj is None or obj.type != "MESH":
        return
    _ensure_uv0_attribute(obj)
    _ensure_smoothnormal_attribute(obj)
    if shader_type == "HAIR":
        _ensure_white_color_attribute(obj, "CORNER")
    elif shader_type == "FACE":
        _ensure_white_color_attribute(obj, "POINT")


def _derive_texture_path(base_path: str, suffix: str) -> str:
    abs_path = _safe_abs_path(base_path)
    if not abs_path:
        return ""
    folder, filename = os.path.split(abs_path)
    stem, ext = os.path.splitext(filename)
    replaced = re.sub(r"(_[Dd])$", suffix, stem)
    if replaced == stem:
        replaced = stem + suffix
    candidate = os.path.join(folder, replaced + ext)
    return candidate if os.path.exists(candidate) else ""


def _guess_texture_by_scan(base_path: str, role_id: str) -> str:
    abs_path = _safe_abs_path(base_path)
    if not abs_path:
        return ""
    folder, filename = os.path.split(abs_path)
    stem, ext = os.path.splitext(filename)
    prefix = stem.rsplit("_", 1)[0] if "_" in stem else stem
    if not os.path.isdir(folder):
        return ""

    valid_ext = {".png", ".tga", ".jpg", ".jpeg", ".bmp", ".webp", ".dds", ext.lower()}
    best_path = ""
    best_score = 0
    for entry in os.listdir(folder):
        entry_lower = entry.lower()
        full = os.path.join(folder, entry)
        if not os.path.isfile(full):
            continue
        if os.path.splitext(entry)[1].lower() not in valid_ext:
            continue
        if prefix.lower() not in entry_lower:
            continue
        score = _texture_filename_match_score(entry, role_id)
        if score > best_score:
            best_score = score
            best_path = full

    if best_path:
        return best_path

    fallback = _guess_texture_by_generic_scan(folder, prefix.lower(), stem.lower(), valid_ext, role_id)
    if fallback:
        return fallback
    return ""


def _texture_category_tokens(stem_lower: str):
    tokens = []
    for token in ("body", "cloth", "face", "hair", "eye", "iris", "brow", "lash"):
        if token in stem_lower:
            tokens.append(token)
    return tuple(dict.fromkeys(tokens))


def _texture_filename_match_score(entry_name: str, role_id: str) -> int:
    stem_lower = os.path.splitext(entry_name)[0].lower()

    if role_id == "tex_n":
        if stem_lower.endswith("_hn"):
            return 140
        if stem_lower.endswith("_n"):
            return 130
        if re.search(r"(?:^|_)normal(?:$|_)", stem_lower):
            return 110
        return 0

    if role_id == "tex_p":
        if stem_lower.endswith("_lightmap"):
            return 140
        if stem_lower.endswith("_ilm"):
            return 135
        if stem_lower.endswith("_id"):
            return 130
        if stem_lower.endswith("_p"):
            return 125
        return 0

    if role_id == "tex_m":
        if any(token in stem_lower for token in ("cm_m", "hl_m", "eyeshadow", "hairshadow", "_lut_")):
            return 0
        if stem_lower.endswith("_orm") or stem_lower.endswith("_rma"):
            return 145
        if stem_lower.endswith("_m"):
            score = 120
            if "_sw_m" in stem_lower:
                score += 8
            return score
        return 0

    if role_id == "tex_st":
        if stem_lower.endswith("_st"):
            return 130
        if stem_lower.endswith("_mask"):
            return 120
        if "outline" in stem_lower:
            return 110
        return 0

    if role_id == "tex_e":
        if stem_lower.endswith("_em"):
            return 135
        if stem_lower.endswith("_e"):
            return 130
        if stem_lower.endswith("_emission"):
            return 125
        return 0

    if role_id == "face_sdf_tex":
        if "sdf" in stem_lower:
            return 150
        return 0

    if role_id == "face_cm_tex":
        if "cm_m" in stem_lower:
            return 150
        return 0

    return 0


def _guess_texture_by_generic_scan(folder: str, prefix_lower: str, stem_lower: str, valid_ext, role_id: str) -> str:
    rules = GENERIC_TEXTURE_SCAN_RULES.get(role_id)
    if not rules:
        return ""

    category_tokens = _texture_category_tokens(stem_lower)
    best_path = ""
    best_score = 0

    for entry in os.listdir(folder):
        entry_lower = entry.lower()
        full = os.path.join(folder, entry)
        if not os.path.isfile(full):
            continue
        if os.path.splitext(entry)[1].lower() not in valid_ext:
            continue

        match_score = _texture_filename_match_score(entry, role_id)
        if match_score <= 0:
            continue

        score = match_score
        if prefix_lower and prefix_lower in entry_lower:
            score += 40
        if category_tokens:
            if any(token in entry_lower for token in category_tokens):
                score += 35
            else:
                score -= 25

        for token in rules["prefer"]:
            if token in entry_lower:
                score += 12
        for token in rules["avoid"]:
            if token in entry_lower:
                score -= 25

        if role_id == "face_cm_tex" and "body" in entry_lower:
            score -= 40
        if role_id == "face_sdf_tex" and "female_face" in entry_lower:
            score += 25
        if role_id == "tex_n" and "body" in category_tokens and "common" in entry_lower:
            score += 10
        if role_id == "tex_m" and "body" in entry_lower:
            score += 8
        if role_id == "tex_m" and "cloth" in entry_lower:
            score += 8

        if score > best_score:
            best_score = score
            best_path = full

    return best_path if best_score > 0 else ""


def _autofill_missing_texture_paths(settings: ENDFIELD_PG_Settings) -> int:
    if not settings.tex_d:
        return 0

    filled = 0
    required_roles = {slot.prop_id for slot in TEXTURE_SLOT_LAYOUT[settings.shader_type]}
    for role_id, suffixes in ROLE_SUFFIX_CANDIDATES.items():
        if role_id not in required_roles:
            continue
        current_value = getattr(settings, role_id)
        if current_value and not _role_path_looks_suspicious(current_value, role_id, settings.tex_d):
            continue
        if current_value and _role_path_looks_suspicious(current_value, role_id, settings.tex_d):
            setattr(settings, role_id, "")

        guessed = ""
        for suffix in suffixes:
            guessed = _derive_texture_path(settings.tex_d, suffix)
            if guessed:
                break
        if not guessed:
            guessed = _guess_texture_by_scan(settings.tex_d, role_id)
        if guessed:
            setattr(settings, role_id, guessed)
            filled += 1

    if settings.shader_type == "FACE":
        for role_id in ("face_sdf_tex", "face_cm_tex"):
            current_value = getattr(settings, role_id)
            if current_value and not _role_path_looks_suspicious(current_value, role_id, settings.tex_d):
                continue
            if current_value and _role_path_looks_suspicious(current_value, role_id, settings.tex_d):
                setattr(settings, role_id, "")
            guessed = _guess_texture_by_scan(settings.tex_d, role_id)
            if guessed:
                setattr(settings, role_id, guessed)
                filled += 1
    return filled


def _sanitize_name(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z_\u4e00-\u9fff]+", "_", value).strip("_")
    return value or "Target"


def _find_armature(obj):
    armature = obj.find_armature()
    if armature:
        return armature
    for modifier in obj.modifiers:
        if modifier.type == "ARMATURE" and modifier.object:
            return modifier.object
    return None


def _find_bone_case_insensitive(armature_obj, bone_name: str):
    if not armature_obj or armature_obj.type != "ARMATURE" or not bone_name:
        return None
    bone = armature_obj.data.bones.get(bone_name)
    if bone is not None:
        return bone
    lowered = bone_name.casefold()
    for candidate in armature_obj.data.bones:
        if candidate.name.casefold() == lowered:
            return candidate
    return None


def _find_head_bone(armature_obj, preferred_name: str = ""):
    if not armature_obj or armature_obj.type != "ARMATURE":
        return None

    preferred = _find_bone_case_insensitive(armature_obj, preferred_name)
    if preferred is not None:
        return preferred

    bones = list(armature_obj.data.bones)
    if not bones:
        return None

    exact_lookup = {name.casefold() for name in HEAD_BONE_EXACT_NAMES}
    for bone in bones:
        if bone.name.casefold() in exact_lookup:
            return bone

    def score_bone_name(name: str) -> int:
        lowered = name.casefold()
        if any(excluded in lowered for excluded in HEAD_BONE_EXCLUDE_KEYWORDS):
            return -1
        score = 0
        for keyword in HEAD_BONE_KEYWORDS:
            keyword_lower = keyword.casefold()
            if lowered == keyword_lower:
                score = max(score, 200)
            elif lowered.endswith(keyword_lower):
                score = max(score, 120)
            elif keyword_lower in lowered:
                score = max(score, 80)
        if lowered.startswith("def-") or lowered.startswith("def_"):
            score -= 10
        return score

    ranked = sorted(
        ((score_bone_name(bone.name), bone.name.casefold(), bone) for bone in bones),
        key=lambda item: (-item[0], item[1]),
    )
    return ranked[0][2] if ranked and ranked[0][0] > 0 else None


def _resolve_helper_armature(settings: ENDFIELD_PG_Settings, obj):
    if getattr(settings, "head_bone_armature", None) and settings.head_bone_armature.type == "ARMATURE":
        return settings.head_bone_armature
    return _find_armature(obj)


def _resolve_head_bone(settings: ENDFIELD_PG_Settings, obj):
    armature = _resolve_helper_armature(settings, obj)
    if armature is None:
        return None, None
    bone = _find_head_bone(armature, getattr(settings, "head_bone_name", ""))
    return armature, bone


def _resolve_lattice_bone(armature_obj, head_bone):
    if armature_obj is None or head_bone is None:
        return None
    preferred_names = []
    if head_bone.name:
        if head_bone.name.startswith(LATTICE_BONE_PREFIXES):
            preferred_names.append(head_bone.name)
        else:
            preferred_names.extend(f"{prefix}{head_bone.name}" for prefix in LATTICE_BONE_PREFIXES)
    preferred_names.extend(["DEF-Head", "DEF_head", "def-head", "def_head"])
    for name in preferred_names:
        bone = _find_bone_case_insensitive(armature_obj, name)
        if bone is not None:
            return bone
    return head_bone


def _estimate_anchor_from_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    center = sum(points, Vector()) / len(points)
    max_z = max(point.z for point in points)
    return Vector((center.x, center.y, max_z - max(obj.dimensions) * 0.15))


def _bounds_world_min_max(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_corner = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    max_corner = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return min_corner, max_corner


def _fit_lattice_to_object(lattice_obj, obj):
    if lattice_obj is None or obj is None:
        return
    if lattice_obj.type == "LATTICE":
        data = lattice_obj.data
        if data is not None:
            for attr_name in ("interpolation_type_u", "interpolation_type_v", "interpolation_type_w"):
                if hasattr(data, attr_name):
                    setattr(data, attr_name, "KEY_BSPLINE")
            if hasattr(data, "use_outside"):
                data.use_outside = False
    lattice_obj.delta_location = (0.0, 0.0, 0.0)
    lattice_obj.delta_rotation_euler = (0.0, 0.0, 0.0)
    lattice_obj.delta_scale = (1.0, 1.0, 1.0)
    min_corner, max_corner = _bounds_world_min_max(obj)
    center = (min_corner + max_corner) * 0.5
    size = (max_corner - min_corner)
    lattice_obj.rotation_euler = (0.0, 0.0, 0.0)
    lattice_obj.location = center
    lattice_obj.scale = (
        max(size.x * 0.5 * LATTICE_FIT_MARGIN.x, 0.001),
        max(size.y * 0.5 * LATTICE_FIT_MARGIN.y, 0.001),
        max(size.z * 0.5 * LATTICE_FIT_MARGIN.z, 0.001),
    )


def _validate_face_helper_targets(settings: ENDFIELD_PG_Settings, objects):
    if settings.shader_type != "FACE":
        return ""
    for obj in objects:
        armature, head_bone = _resolve_head_bone(settings, obj)
        if armature is None:
            return f"对象 {obj.name} 未找到骨架，请先指定头部骨骼用的骨架"
        if head_bone is None:
            return f"对象 {obj.name} 未找到头部骨骼，请在脸部栏指定头部骨骼"
    return ""


def _find_collection_child(parent, name: str):
    for child in parent.children:
        if child.name == name:
            return child
    return None


def _unlink_collection_from_parents(collection, keep_parent=None):
    if collection is None:
        return
    all_parents = [bpy.context.scene.collection, *bpy.data.collections]
    for parent in all_parents:
        if parent == keep_parent:
            continue
        child = _find_collection_child(parent, collection.name)
        if child == collection:
            try:
                parent.children.unlink(collection)
            except RuntimeError:
                pass


def _ensure_collection_child(parent, name: str):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    _unlink_collection_from_parents(collection, keep_parent=parent)
    if _find_collection_child(parent, name) is None:
        parent.children.link(collection)
    return collection


def _find_layer_collection(layer_collection, collection_name: str):
    if layer_collection is None:
        return None
    if layer_collection.collection and layer_collection.collection.name == collection_name:
        return layer_collection
    for child in layer_collection.children:
        found = _find_layer_collection(child, collection_name)
        if found is not None:
            return found
    return None


def _set_collection_excluded(scene, collection_name: str, excluded=True):
    if scene is None or not collection_name:
        return
    for view_layer in scene.view_layers:
        layer_collection = _find_layer_collection(view_layer.layer_collection, collection_name)
        if layer_collection is not None:
            layer_collection.exclude = excluded


def _remove_collection_if_empty(name: str):
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    if collection.objects or collection.children:
        return
    _unlink_collection_from_parents(collection)
    try:
        bpy.data.collections.remove(collection)
    except RuntimeError:
        pass


def _ensure_master_structure():
    _normalize_legacy_scene_names()
    scene = bpy.context.scene
    scene_root = scene.collection
    master = _ensure_collection_child(scene_root, MASTER_COLLECTION_NAME)
    helper = bpy.data.collections.get(HELPER_COLLECTION_NAME)
    if helper is None:
        helper = bpy.data.collections.new(HELPER_COLLECTION_NAME)
    _unlink_collection_from_parents(helper, keep_parent=master)
    if _find_collection_child(master, helper.name) is None:
        master.children.link(helper)
    _ensure_collection_child(helper, UTILITY_COLLECTION_NAME)
    _ensure_collection_child(helper, WIDGETS_COLLECTION_NAME)
    _ensure_collection_child(helper, META_COLLECTION_NAME)
    _remove_collection_if_empty(MESH_HIGH_COLLECTION_NAME)
    _remove_collection_if_empty(MESH_LOW_COLLECTION_NAME)
    _remove_collection_if_empty(MESH_COLLECTION_NAME)
    _remove_collection_if_empty(RIG_COLLECTION_NAME)
    _set_collection_excluded(scene, MASTER_COLLECTION_NAME, True)
    return {
        "master": master,
        "helper": helper,
    }


def _link_object_to_collection(obj, collection):
    if collection and obj is not None:
        names = {item.name for item in collection.objects}
        if obj.name not in names:
            try:
                collection.objects.link(obj)
            except RuntimeError:
                pass


def _move_object_to_collection(obj, target_collection, exclusive=False):
    if obj is None or target_collection is None:
        return
    if exclusive:
        for collection in list(obj.users_collection):
            if collection != target_collection:
                try:
                    collection.objects.unlink(obj)
                except RuntimeError:
                    pass
    _link_object_to_collection(obj, target_collection)


def _get_or_create_empty(name: str, collection):
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type = "PLAIN_AXES"
        obj.empty_display_size = 1.0
    _link_object_to_collection(obj, collection)
    return obj


def _ensure_scene_camera(settings: ENDFIELD_PG_Settings, target_collection=None):
    scene = bpy.context.scene
    scene_root = scene.collection
    library = _effective_library_path(settings)
    camera_obj = _find_or_append_object(library, SOURCE_CAMERA_NAME) if library else bpy.data.objects.get(SOURCE_CAMERA_NAME)
    if camera_obj is None or camera_obj.type != "CAMERA":
        camera_obj = scene.camera if scene.camera and scene.camera.type == "CAMERA" else None
    if camera_obj is None:
        return None
    target_collection = target_collection or scene_root
    is_source_camera = _name_matches_datablock(SOURCE_CAMERA_NAME, camera_obj.name)
    _move_object_to_collection(camera_obj, target_collection, exclusive=is_source_camera)
    scene.camera = camera_obj
    return camera_obj


def _clear_parent_keep_transform(obj):
    matrix_world = obj.matrix_world.copy()
    obj.parent = None
    obj.parent_type = "OBJECT"
    obj.parent_bone = ""
    obj.matrix_world = matrix_world


def _target_matrix(target, subtarget=""):
    if target is None:
        return Matrix.Identity(4)
    if subtarget and target.type == "ARMATURE" and target.pose and target.pose.bones.get(subtarget):
        return target.matrix_world @ target.pose.bones[subtarget].matrix
    return target.matrix_world.copy()


def _ensure_child_of_constraint(obj, name: str, target=None, subtarget: str = "", inverse_matrix=None):
    constraint = None
    for item in obj.constraints:
        if item.type == "CHILD_OF" and item.name == name:
            constraint = item
            break
    if constraint is None:
        constraint = obj.constraints.new("CHILD_OF")
        constraint.name = name
    _clear_parent_keep_transform(obj)
    constraint.target = target
    constraint.subtarget = subtarget
    bpy.context.view_layer.update()
    if inverse_matrix is not None:
        try:
            constraint.inverse_matrix = inverse_matrix.copy()
        except Exception:
            constraint.inverse_matrix = inverse_matrix
    elif hasattr(constraint, "set_inverse_pending"):
        constraint.set_inverse_pending = True
    bpy.context.view_layer.update()
    return constraint


def _ensure_track_to_constraint(obj, name: str, target=None):
    if obj is None:
        return None
    constraint = None
    for item in obj.constraints:
        if item.type == "TRACK_TO" and item.name == name:
            constraint = item
            break
    if constraint is None:
        constraint = obj.constraints.new("TRACK_TO")
        constraint.name = name
    constraint.target = target
    constraint.track_axis = "TRACK_Y"
    constraint.up_axis = "UP_X"
    constraint.target_space = "WORLD"
    constraint.owner_space = "WORLD"
    if hasattr(constraint, "use_target_z"):
        constraint.use_target_z = False
    return constraint


def _remove_child_of_constraints(obj):
    if obj is None:
        return
    for item in list(obj.constraints):
        if item.type == "CHILD_OF":
            obj.constraints.remove(item)


def _remove_track_to_constraints(obj):
    if obj is None:
        return
    for item in list(obj.constraints):
        if item.type == "TRACK_TO":
            obj.constraints.remove(item)


def _replace_child_of_constraint(obj, name: str, target=None, subtarget: str = "", desired_world=None):
    if obj is None:
        return None
    desired_world = desired_world.copy() if desired_world is not None else obj.matrix_world.copy()
    _remove_child_of_constraints(obj)
    bpy.context.view_layer.update()
    target_matrix = _target_matrix(target, subtarget) if target is not None else Matrix.Identity(4)
    local_matrix = target_matrix.inverted_safe() @ desired_world if target is not None else desired_world
    obj.matrix_world = local_matrix
    return _ensure_child_of_constraint(obj, name, target, subtarget, inverse_matrix=Matrix.Identity(4))


def _set_object_info_target(node, target_obj) -> bool:
    if node is None or target_obj is None:
        return False
    socket = node.inputs.get("Object") if hasattr(node, "inputs") else None
    if socket is None:
        return False
    try:
        socket.default_value = target_obj
        return True
    except Exception:
        return False


def _rebind_sun_vec_targets(node_group, lf, lc):
    if node_group is None:
        return False

    object_nodes = [
        node for node in node_group.nodes
        if getattr(node, "type", "") == "OBJECT_INFO" or getattr(node, "bl_idname", "") == "GeometryNodeObjectInfo"
    ]
    if not object_nodes:
        return False

    rebound = False
    unresolved = []
    for node in object_nodes:
        socket = node.inputs.get("Object") if hasattr(node, "inputs") else None
        current_obj = getattr(socket, "default_value", None) if socket else None
        node_hint = f"{node.name} {node.label}".lower()
        current_name = current_obj.name.lower() if current_obj else ""

        if "lf" in node_hint or current_name == SUN_HELPER_LF_NAME.lower():
            rebound = _set_object_info_target(node, lf) or rebound
            continue
        if "lc" in node_hint or current_name == SUN_HELPER_LC_NAME.lower():
            rebound = _set_object_info_target(node, lc) or rebound
            continue

        unresolved.append(node)

    fallback_targets = [lf, lc]
    for node, target in zip(unresolved, fallback_targets):
        rebound = _set_object_info_target(node, target) or rebound

    return rebound


def _sync_material_alpha_settings(material, template):
    if material is None or template is None:
        return

    for attr_name in ("shadow_method", "use_backface_culling"):
        if hasattr(material, attr_name) and hasattr(template, attr_name):
            try:
                setattr(material, attr_name, getattr(template, attr_name))
            except Exception:
                pass

    if hasattr(material, "surface_render_method") and hasattr(template, "surface_render_method"):
        try:
            material.surface_render_method = template.surface_render_method
        except Exception:
            pass

    if hasattr(material, "blend_method") and hasattr(template, "blend_method"):
        try:
            material.blend_method = template.blend_method
        except Exception:
            pass


def _apply_named_settings(target, values):
    if target is None:
        return
    for attr_name, value in values.items():
        if not hasattr(target, attr_name):
            continue
        try:
            setattr(target, attr_name, value)
        except Exception:
            pass


def _apply_preset_scene_settings(scene):
    if scene is None:
        return
    if hasattr(scene, "render") and hasattr(scene.render, "engine"):
        try:
            scene.render.engine = PRESET_RENDER_ENGINE
        except Exception:
            pass
    if hasattr(scene, "render"):
        _apply_named_settings(scene.render, PRESET_RENDER_DEFAULTS)
    if hasattr(scene, "view_settings"):
        _apply_named_settings(scene.view_settings, PRESET_VIEW_DEFAULTS)
    if hasattr(scene, "eevee"):
        _apply_named_settings(scene.eevee, PRESET_EEVEE_DEFAULTS)


def _apply_preset_sun_settings(light_obj):
    if light_obj is None or light_obj.type != "LIGHT" or light_obj.data is None:
        return
    light_obj.data.type = "SUN"
    light_obj.data.energy = 1.0
    if hasattr(light_obj.data, "angle"):
        light_obj.data.angle = 0.009180432185530663
    if hasattr(light_obj.data, "use_shadow"):
        light_obj.data.use_shadow = True
    if hasattr(light_obj.data, "use_contact_shadow"):
        light_obj.data.use_contact_shadow = False


def _strip_old_markers(name: str) -> str:
    if not name:
        return ""
    cleaned = name
    while "__OLD" in cleaned:
        cleaned = cleaned.replace("__OLD", "")
    cleaned = re.sub(r"\.{2,}", ".", cleaned).strip(".")
    return cleaned


def _legacy_name_candidates(name: str):
    raw = name or ""
    stripped = _strip_old_markers(raw)
    candidates = []
    for candidate in (
        raw,
        stripped,
        re.sub(r"(?:\.\d{3})+$", "", stripped),
        re.sub(r"\.\d{3}", "", stripped),
    ):
        candidate = (candidate or "").strip(".")
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _node_group_replacement_score(source_name: str, candidate_name: str) -> int:
    score = -1
    for base_name in _legacy_name_candidates(source_name):
        if candidate_name == base_name:
            score = max(score, 120)
        if _name_matches_datablock(base_name, candidate_name) or _name_matches_datablock(candidate_name, base_name):
            score = max(score, 100)
        if re.sub(r"\.\d{3}", "", candidate_name) == re.sub(r"\.\d{3}", "", base_name):
            score = max(score, 80)
    return score


def _node_group_needs_repair(source_group, current_stamp: str = "") -> bool:
    if source_group is None:
        return False
    if "__OLD" in source_group.name:
        return True
    group_stamp = source_group.get(SOURCE_LIBRARY_STAMP_KEY)
    if current_stamp and group_stamp and group_stamp != current_stamp:
        return True
    return False


def _find_best_library_node_group_name(source_name: str, library_path: str, current_stamp: str = ""):
    if not library_path or not os.path.exists(library_path):
        return ""
    try:
        with bpy.data.libraries.load(library_path, link=False) as (data_from, _data_to):
            available_names = list(data_from.node_groups)
    except Exception:
        return ""

    best_name = ""
    best_score = -1
    for candidate_name in available_names:
        if "__OLD" in candidate_name:
            continue
        score = _node_group_replacement_score(source_name, candidate_name)
        if score < 0:
            continue
        loaded_candidate = bpy.data.node_groups.get(candidate_name)
        if current_stamp and loaded_candidate is not None and loaded_candidate.get(SOURCE_LIBRARY_STAMP_KEY) == current_stamp:
            score += 10
        if score > best_score:
            best_name = candidate_name
            best_score = score
    return best_name


def _find_replacement_node_group(source_group, library_path: str = ""):
    if source_group is None:
        return None
    current_stamp = _library_stamp(library_path)
    if not _node_group_needs_repair(source_group, current_stamp):
        return None
    best_group = None
    best_score = -1
    for candidate in bpy.data.node_groups:
        if candidate == source_group:
            continue
        if candidate.bl_idname != source_group.bl_idname:
            continue
        if "__OLD" in candidate.name:
            continue
        score = _node_group_replacement_score(source_group.name, candidate.name)
        if score < 0:
            continue
        if current_stamp and candidate.get(SOURCE_LIBRARY_STAMP_KEY) == current_stamp:
            score += 10
        if score > best_score:
            best_group = candidate
            best_score = score
    if best_group is None and library_path:
        library_group_name = _find_best_library_node_group_name(source_group.name, library_path, current_stamp=current_stamp)
        if library_group_name:
            candidate = _find_or_append_node_group_by_name(library_path, library_group_name, tree_type=source_group.bl_idname)
            if candidate is not None and candidate != source_group and "__OLD" not in candidate.name:
                best_group = candidate
    return best_group


def _repair_node_tree_group_links(node_tree, library_path: str = "", visited=None):
    if node_tree is None:
        return 0
    visited = visited or set()
    tree_key = node_tree.as_pointer()
    if tree_key in visited:
        return 0
    visited.add(tree_key)

    repaired = 0
    for node in node_tree.nodes:
        if node.type != "GROUP" or not node.node_tree:
            continue
        replacement = _find_replacement_node_group(node.node_tree, library_path)
        if replacement is not None and replacement != node.node_tree:
            node.node_tree = replacement
            repaired += 1
        repaired += _repair_node_tree_group_links(node.node_tree, library_path, visited)
    return repaired


def _repair_legacy_material_node_groups(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    if _requires_eevee_compat():
        _ensure_eevee_shader_info_compat_group()
    repaired = 0
    visited = set()
    for material in bpy.data.materials:
        if not material or not material.use_nodes or not material.node_tree:
            continue
        repaired += _repair_node_tree_group_links(material.node_tree, library, visited)
        _patch_material_for_eevee_compat(material)
    return repaired


def _repair_legacy_modifier_node_groups(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    repaired = 0
    for obj in bpy.data.objects:
        for modifier in obj.modifiers:
            if modifier.type != "NODES" or modifier.node_group is None:
                continue
            replacement = _find_replacement_node_group(modifier.node_group, library)
            if replacement is not None and replacement != modifier.node_group:
                modifier.node_group = replacement
                repaired += 1
    return repaired


def _repair_legacy_scene_bindings(settings: ENDFIELD_PG_Settings):
    repaired = 0
    repaired += _repair_legacy_modifier_node_groups(settings)
    repaired += _repair_legacy_material_node_groups(settings)
    return repaired


def _scene_has_endfield_materials() -> bool:
    for material in bpy.data.materials:
        if _find_main_shader_node(material) is not None:
            return True
    return False


def _scene_has_generated_endfield_scene() -> bool:
    scene = bpy.context.scene
    if scene is not None and getattr(scene, "world", None) is not None:
        if scene.world.name == TARGET_WORLD_NAME:
            return True
    if bpy.data.collections.get(MASTER_COLLECTION_NAME) is not None:
        return True
    for name in (SUN_LIGHT_NAME, SUN_HELPER_LC_NAME, SUN_HELPER_LF_NAME, HEAD_HELPER_NAME, HEAD_FORWARD_NAME, HEAD_RIGHT_NAME):
        if bpy.data.objects.get(name) is not None:
            return True
    for material in bpy.data.materials:
        if not material or not material.use_nodes or not material.node_tree:
            continue
        for node in material.node_tree.nodes:
            node_tree = getattr(node, "node_tree", None)
            if node_tree is None:
                continue
            if "__OLD" in node_tree.name and (
                "Arknights: Endfield" in node_tree.name or "DepthRim" in node_tree.name or "Rain" in node_tree.name
            ):
                return True
    return False


def _remove_default_endfield_scene_lights():
    removed = []
    if bpy.data.objects.get(SUN_LIGHT_NAME) is None and bpy.data.objects.get(SOURCE_SUN_LIGHT_NAME) is None:
        return removed
    target_sun = bpy.data.objects.get(SUN_LIGHT_NAME)
    for obj in list(bpy.data.objects):
        if obj.type != "LIGHT":
            continue
        should_remove = obj.name == "Light"
        if target_sun is not None and obj != target_sun and _name_matches_datablock(SOURCE_SUN_LIGHT_NAME, obj.name):
            should_remove = True
        if not should_remove:
            continue
        removed.append(obj.name)
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except Exception:
            pass
    return removed


def _repair_current_endfield_scene(settings: ENDFIELD_PG_Settings, ensure_environment: bool = False):
    repaired = 0
    removed_lights = []
    if ensure_environment:
        _migrate_scene_environment(settings, bpy.context.scene)
        _ensure_sun_rig(settings)
        removed_lights = _remove_default_endfield_scene_lights()
    repaired += _repair_legacy_scene_bindings(settings)
    return repaired, removed_lights


def _migrate_scene_environment(settings: ENDFIELD_PG_Settings, target_scene):
    if not settings.migrate_source_environment:
        return
    world = _ensure_target_world(settings)
    if world is not None:
        target_scene.world = world
        _cleanup_unused_world_backups()
    _apply_preset_scene_settings(target_scene)


def _ensure_sun_rig(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    structure = _ensure_master_structure()
    helper_collection = _find_or_append_collection(library, HELPER_COLLECTION_NAME) if library else None
    if helper_collection is not None:
        _unlink_collection_from_parents(helper_collection, keep_parent=structure["master"])
        if _find_collection_child(structure["master"], helper_collection.name) is None:
            structure["master"].children.link(helper_collection)
        structure["helper"] = helper_collection
        _ensure_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
        _ensure_collection_child(helper_collection, WIDGETS_COLLECTION_NAME)
        _ensure_collection_child(helper_collection, META_COLLECTION_NAME)
    elif library:
        for child_name in (UTILITY_COLLECTION_NAME, WIDGETS_COLLECTION_NAME, META_COLLECTION_NAME):
            child_collection = _find_or_append_collection(library, child_name)
            if child_collection is not None:
                _unlink_collection_from_parents(child_collection, keep_parent=structure["helper"])
                if _find_collection_child(structure["helper"], child_collection.name) is None:
                    structure["helper"].children.link(child_collection)

    helper_collection = structure["helper"]
    utility_collection = _find_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
    if library and utility_collection is not None:
        for object_name in ("Active Camera Tracker", "Lattice", "Pencil+ 4 Line Merge Helper"):
            utility_obj = _find_or_append_object(library, object_name)
            if utility_obj is not None:
                _move_object_to_collection(utility_obj, utility_collection)

    light_obj = _ensure_object_alias(SUN_LIGHT_NAME, SOURCE_SUN_LIGHT_NAME)
    if light_obj is None and library:
        light_obj = _find_or_append_object(library, SUN_LIGHT_NAME)
    if light_obj is None or light_obj.type != "LIGHT":
        light_data = bpy.data.lights.get(SUN_LIGHT_NAME)
        if light_data is None:
            light_data = bpy.data.lights.new(SUN_LIGHT_NAME, "SUN")
        else:
            light_data.type = "SUN"
        light_obj = bpy.data.objects.get(SUN_LIGHT_NAME) or bpy.data.objects.new(SUN_LIGHT_NAME, light_data)
    alias_light = bpy.data.objects.get(SOURCE_SUN_LIGHT_NAME)
    if alias_light is not None and alias_light != light_obj and alias_light.type == "LIGHT":
        try:
            bpy.data.objects.remove(alias_light, do_unlink=True)
        except Exception:
            pass
    _move_object_to_collection(light_obj, bpy.context.scene.collection, exclusive=True)
    light_obj.location = SUN_LIGHT_LOCATION
    light_obj.rotation_euler = SUN_LIGHT_ROTATION
    _apply_preset_sun_settings(light_obj)
    camera_obj = _ensure_scene_camera(settings, bpy.context.scene.collection)

    lc = _find_or_append_object(library, SUN_HELPER_LC_NAME) if library else bpy.data.objects.get(SUN_HELPER_LC_NAME)
    lf = _find_or_append_object(library, SUN_HELPER_LF_NAME) if library else bpy.data.objects.get(SUN_HELPER_LF_NAME)
    lc = lc or _get_or_create_empty(SUN_HELPER_LC_NAME, helper_collection)
    lf = lf or _get_or_create_empty(SUN_HELPER_LF_NAME, helper_collection)
    _move_object_to_collection(lc, helper_collection)
    _move_object_to_collection(lf, helper_collection)
    _remove_child_of_constraints(lc)
    _remove_child_of_constraints(lf)
    bpy.context.view_layer.update()
    lc.location = light_obj.matrix_world @ Vector((0.0, 0.0, -SUN_LC_DISTANCE))
    lf.location = light_obj.matrix_world @ Vector((0.0, 0.0, -SUN_LF_DISTANCE))
    lc.rotation_euler = (0.0, 0.0, 0.0)
    lf.rotation_euler = (0.0, 0.0, 0.0)
    lc.scale = (0.240563393, 0.240563393, 0.240563393)
    lf.scale = (0.240563393, 0.240563393, 0.240563393)
    bpy.context.view_layer.update()
    lc_world = lc.matrix_world.copy()
    lf_world = lf.matrix_world.copy()
    _ensure_child_of_constraint(lc, "瀛愮骇", light_obj)
    _ensure_child_of_constraint(lf, "瀛愮骇", light_obj)

    _replace_child_of_constraint(lc, "子级", light_obj)
    _replace_child_of_constraint(lf, "子级", light_obj)

    _replace_child_of_constraint(lc, "Child Of", light_obj, desired_world=lc_world)
    _replace_child_of_constraint(lf, "Child Of", light_obj, desired_world=lf_world)

    sun_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SUN_VEC"])
    _rebind_sun_vec_targets(sun_group, lf, lc)
    return {"sun": light_obj, "camera": camera_obj, "helper_collection": helper_collection, "lc": lc, "lf": lf}


def _ensure_head_helper_rig(settings: ENDFIELD_PG_Settings, obj):
    sun_rig = _ensure_sun_rig(settings)
    helper_collection = sun_rig["helper_collection"]
    armature, head_bone = _resolve_head_bone(settings, obj)
    if armature is None or head_bone is None:
        return None
    lattice_bone = _resolve_lattice_bone(armature, head_bone)
    anchor = armature.matrix_world @ head_bone.head_local

    library = _effective_library_path(settings)
    hc = _find_or_append_object(library, HEAD_HELPER_NAME) if library else bpy.data.objects.get(HEAD_HELPER_NAME)
    hf = _find_or_append_object(library, HEAD_FORWARD_NAME) if library else bpy.data.objects.get(HEAD_FORWARD_NAME)
    hr = _find_or_append_object(library, HEAD_RIGHT_NAME) if library else bpy.data.objects.get(HEAD_RIGHT_NAME)
    hc = hc or _get_or_create_empty(HEAD_HELPER_NAME, helper_collection)
    hf = hf or _get_or_create_empty(HEAD_FORWARD_NAME, helper_collection)
    hr = hr or _get_or_create_empty(HEAD_RIGHT_NAME, helper_collection)
    _move_object_to_collection(hc, helper_collection)
    _move_object_to_collection(hf, helper_collection)
    _move_object_to_collection(hr, helper_collection)
    _remove_child_of_constraints(hc)
    bpy.context.view_layer.update()

    hc.scale = HEAD_HELPER_SCALE
    hf.scale = HEAD_DIRECTION_SCALE
    hr.scale = HEAD_DIRECTION_SCALE
    hc.location = anchor
    bpy.context.view_layer.update()
    hc_world = hc.matrix_world.copy()
    _replace_child_of_constraint(hc, "Child Of", armature, head_bone.name, desired_world=hc_world)

    _clear_parent_keep_transform(hf)
    _clear_parent_keep_transform(hr)
    hf.parent = hc
    hr.parent = hc
    hf.matrix_parent_inverse = hc.matrix_world.inverted_safe()
    hr.matrix_parent_inverse = hc.matrix_world.inverted_safe()
    hf.location = anchor + HEAD_FORWARD_OFFSET
    hr.location = anchor + HEAD_RIGHT_OFFSET
    hf.rotation_euler = (0.0, 0.0, 0.0)
    hr.rotation_euler = (0.0, 0.0, 0.0)

    lattice = _find_matching_object(LATTICE_OBJECT_BASENAME)
    if lattice is None and library:
        lattice = _find_or_append_object(library, LATTICE_OBJECT_BASENAME)
    utility_collection = _find_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
    if lattice is not None and utility_collection is not None:
        _move_object_to_collection(lattice, utility_collection)
        _remove_child_of_constraints(lattice)
        bpy.context.view_layer.update()
        _fit_lattice_to_object(lattice, obj)
        bpy.context.view_layer.update()
        lattice_world = lattice.matrix_world.copy()
        _replace_child_of_constraint(
            lattice,
            "Child Of",
            armature,
            lattice_bone.name if lattice_bone else head_bone.name,
            desired_world=lattice_world,
        )
        tracker = _find_matching_object("Active Camera Tracker")
        if tracker is not None:
            _ensure_track_to_constraint(lattice, "Track To", tracker)

    return {"HC": hc, "HF": hf, "HR": hr, "SUN": sun_rig["sun"]}


def _ensure_sun_rig(settings: ENDFIELD_PG_Settings):
    library = _effective_library_path(settings)
    structure = _ensure_master_structure()
    helper_collection = _find_or_append_collection(library, HELPER_COLLECTION_NAME) if library else None
    if helper_collection is not None:
        _normalize_helper_collection_tree(helper_collection)
        _unlink_collection_from_parents(helper_collection, keep_parent=structure["master"])
        if _find_collection_child(structure["master"], helper_collection.name) is None:
            structure["master"].children.link(helper_collection)
        structure["helper"] = helper_collection
        _ensure_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
        _ensure_collection_child(helper_collection, WIDGETS_COLLECTION_NAME)
        _ensure_collection_child(helper_collection, META_COLLECTION_NAME)
    elif library:
        for source_name, child_name in (
            (SOURCE_UTILITY_COLLECTION_NAME, UTILITY_COLLECTION_NAME),
            (SOURCE_WIDGETS_COLLECTION_NAME, WIDGETS_COLLECTION_NAME),
            (SOURCE_META_COLLECTION_NAME, META_COLLECTION_NAME),
        ):
            child_collection = _find_or_append_collection(library, source_name)
            if child_collection is not None:
                child_collection = _rename_datablock(bpy.data.collections, child_collection, child_name)
                _unlink_collection_from_parents(child_collection, keep_parent=structure["helper"])
                if _find_collection_child(structure["helper"], child_collection.name) is None:
                    structure["helper"].children.link(child_collection)

    helper_collection = structure["helper"]
    utility_collection = _find_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
    if library and utility_collection is not None:
        for object_name in ("Active Camera Tracker", "Lattice", "Pencil+ 4 Line Merge Helper"):
            utility_obj = _find_or_append_object(library, object_name)
            if utility_obj is not None:
                _move_object_to_collection(utility_obj, utility_collection)

    light_obj = _ensure_object_alias(SUN_LIGHT_NAME, SOURCE_SUN_LIGHT_NAME)
    if light_obj is None and library:
        light_obj = _find_or_append_object(library, SOURCE_SUN_LIGHT_NAME)
    if light_obj is None or light_obj.type != "LIGHT":
        light_data = bpy.data.lights.get(SUN_LIGHT_NAME)
        if light_data is None:
            light_data = bpy.data.lights.new(SUN_LIGHT_NAME, "SUN")
        else:
            light_data.type = "SUN"
        light_obj = bpy.data.objects.get(SUN_LIGHT_NAME) or bpy.data.objects.new(SUN_LIGHT_NAME, light_data)
    light_obj = _rename_datablock(bpy.data.objects, light_obj, SUN_LIGHT_NAME)
    alias_light = bpy.data.objects.get(SOURCE_SUN_LIGHT_NAME)
    if alias_light is not None and alias_light != light_obj and alias_light.type == "LIGHT":
        try:
            bpy.data.objects.remove(alias_light, do_unlink=True)
        except Exception:
            pass
    _move_object_to_collection(light_obj, bpy.context.scene.collection, exclusive=True)
    light_obj.location = SUN_LIGHT_LOCATION
    light_obj.rotation_euler = SUN_LIGHT_ROTATION
    _apply_preset_sun_settings(light_obj)
    camera_obj = _ensure_scene_camera(settings, bpy.context.scene.collection)

    lc = _find_or_append_object(library, SUN_HELPER_LC_NAME) if library else _find_matching_object(SUN_HELPER_LC_NAME)
    lf = _find_or_append_object(library, SUN_HELPER_LF_NAME) if library else _find_matching_object(SUN_HELPER_LF_NAME)
    lc = lc or _get_or_create_empty(SUN_HELPER_LC_NAME, helper_collection)
    lf = lf or _get_or_create_empty(SUN_HELPER_LF_NAME, helper_collection)
    _move_object_to_collection(lc, helper_collection)
    _move_object_to_collection(lf, helper_collection)
    _remove_child_of_constraints(lc)
    _remove_child_of_constraints(lf)
    bpy.context.view_layer.update()

    lc.location = light_obj.matrix_world @ Vector((0.0, 0.0, -SUN_LC_DISTANCE))
    lf.location = light_obj.matrix_world @ Vector((0.0, 0.0, -SUN_LF_DISTANCE))
    lc.rotation_euler = (0.0, 0.0, 0.0)
    lf.rotation_euler = (0.0, 0.0, 0.0)
    lc.scale = (0.240563393, 0.240563393, 0.240563393)
    lf.scale = (0.240563393, 0.240563393, 0.240563393)
    bpy.context.view_layer.update()
    lc_world = lc.matrix_world.copy()
    lf_world = lf.matrix_world.copy()
    _replace_child_of_constraint(lc, "Child Of", light_obj, desired_world=lc_world)
    _replace_child_of_constraint(lf, "Child Of", light_obj, desired_world=lf_world)

    sun_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SUN_VEC"])
    _rebind_sun_vec_targets(sun_group, lf, lc)
    return {"sun": light_obj, "camera": camera_obj, "helper_collection": helper_collection, "lc": lc, "lf": lf}


def _ensure_head_helper_rig(settings: ENDFIELD_PG_Settings, obj):
    sun_rig = _ensure_sun_rig(settings)
    helper_collection = sun_rig["helper_collection"]
    armature, head_bone = _resolve_head_bone(settings, obj)
    if armature is None or head_bone is None:
        return None
    lattice_bone = _resolve_lattice_bone(armature, head_bone)
    anchor = armature.matrix_world @ head_bone.head_local

    library = _effective_library_path(settings)
    hc = _find_or_append_object(library, SOURCE_HEAD_HELPER_NAME) if library else _ensure_object_alias(HEAD_HELPER_NAME, SOURCE_HEAD_HELPER_NAME)
    hf = _find_or_append_object(library, SOURCE_HEAD_FORWARD_NAME) if library else _ensure_object_alias(HEAD_FORWARD_NAME, SOURCE_HEAD_FORWARD_NAME)
    hr = _find_or_append_object(library, SOURCE_HEAD_RIGHT_NAME) if library else _ensure_object_alias(HEAD_RIGHT_NAME, SOURCE_HEAD_RIGHT_NAME)
    hc = _rename_datablock(bpy.data.objects, hc, HEAD_HELPER_NAME) if hc is not None else None
    hf = _rename_datablock(bpy.data.objects, hf, HEAD_FORWARD_NAME) if hf is not None else None
    hr = _rename_datablock(bpy.data.objects, hr, HEAD_RIGHT_NAME) if hr is not None else None
    hc = hc or _get_or_create_empty(HEAD_HELPER_NAME, helper_collection)
    hf = hf or _get_or_create_empty(HEAD_FORWARD_NAME, helper_collection)
    hr = hr or _get_or_create_empty(HEAD_RIGHT_NAME, helper_collection)
    _move_object_to_collection(hc, helper_collection)
    _move_object_to_collection(hf, helper_collection)
    _move_object_to_collection(hr, helper_collection)

    _remove_child_of_constraints(hc)
    bpy.context.view_layer.update()
    hc.scale = HEAD_HELPER_SCALE
    hc.location = anchor
    hc.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    hc_world = hc.matrix_world.copy()
    _replace_child_of_constraint(hc, "Child Of", armature, head_bone.name, desired_world=hc_world)

    _clear_parent_keep_transform(hf)
    _clear_parent_keep_transform(hr)
    hf.parent = hc
    hr.parent = hc
    hf.matrix_parent_inverse = hc.matrix_world.inverted_safe()
    hr.matrix_parent_inverse = hc.matrix_world.inverted_safe()
    hf.scale = HEAD_DIRECTION_SCALE
    hr.scale = HEAD_DIRECTION_SCALE
    hf.location = anchor + HEAD_FORWARD_OFFSET
    hr.location = anchor + HEAD_RIGHT_OFFSET
    hf.rotation_euler = (0.0, 0.0, 0.0)
    hr.rotation_euler = (0.0, 0.0, 0.0)

    lattice = _find_or_append_object(library, LATTICE_OBJECT_BASENAME) if library else _find_matching_object(LATTICE_OBJECT_BASENAME)
    utility_collection = _find_collection_child(helper_collection, UTILITY_COLLECTION_NAME)
    if lattice is not None and utility_collection is not None:
        _move_object_to_collection(lattice, utility_collection)
        _remove_child_of_constraints(lattice)
        _remove_track_to_constraints(lattice)
        bpy.context.view_layer.update()
        _fit_lattice_to_object(lattice, obj)
        bpy.context.view_layer.update()
        lattice_world = lattice.matrix_world.copy()
        _replace_child_of_constraint(
            lattice,
            "Child Of",
            armature,
            lattice_bone.name if lattice_bone else head_bone.name,
            desired_world=lattice_world,
        )
        tracker = _find_or_append_object(library, "Active Camera Tracker") if library else _find_matching_object("Active Camera Tracker")
        if tracker is not None:
            _ensure_track_to_constraint(lattice, "Track To", tracker)

    return {"HC": hc, "HF": hf, "HR": hr, "SUN": sun_rig["sun"]}


def _current_head_helper_rig():
    hc = _ensure_object_alias(HEAD_HELPER_NAME, SOURCE_HEAD_HELPER_NAME)
    hf = _ensure_object_alias(HEAD_FORWARD_NAME, SOURCE_HEAD_FORWARD_NAME)
    hr = _ensure_object_alias(HEAD_RIGHT_NAME, SOURCE_HEAD_RIGHT_NAME)
    sun = _ensure_object_alias(SUN_LIGHT_NAME, SOURCE_SUN_LIGHT_NAME)
    if hc is None or hf is None or hr is None or sun is None:
        return None
    return {"HC": hc, "HF": hf, "HR": hr, "SUN": sun}


def _find_material_slot(obj, keywords):
    for slot in obj.material_slots:
        material = slot.material
        if not material:
            continue
        name = material.name.lower()
        if any(keyword in name for keyword in keywords):
            return material
    return None


def _ensure_eye_support_materials(settings: ENDFIELD_PG_Settings, obj):
    library = _effective_library_path(settings)
    support = {
        "iris": _find_or_append_first_material(library, TEMPLATE_MATERIAL_PREFS["PUPIL"]),
        "brow": _find_or_append_first_material(library, TEMPLATE_MATERIAL_PREFS["BROW"]),
        "iris_alpha": _find_or_append_first_material(library, ALPHA_TEMPLATE_PREFS["IRIS"]),
        "brow_alpha": _find_or_append_first_material(library, ALPHA_TEMPLATE_PREFS["BROW"]),
    }

    brow_keywords = ("brow", "lash", "eyelash")
    for slot in obj.material_slots:
        material = slot.material
        if not material:
            continue
        name = material.name.lower()
        if support["brow"] and any(keyword in name for keyword in brow_keywords):
            slot.material = support["brow"]

    return support


def _iter_related_mesh_objects(obj):
    armature = _find_armature(obj)
    parent = obj.parent
    collections = set(obj.users_collection)
    related = []
    for candidate in bpy.data.objects:
        if candidate == obj or candidate.type != "MESH":
            continue
        if armature and _find_armature(candidate) == armature:
            related.append(candidate)
            continue
        if parent and candidate.parent == parent:
            related.append(candidate)
            continue
        if collections.intersection(candidate.users_collection):
            related.append(candidate)
    return related


def _remove_modifier_by_name(obj, modifier_name: str):
    modifier = obj.modifiers.get(modifier_name)
    if modifier is not None:
        obj.modifiers.remove(modifier)


def _remove_eye_transparency_modifiers(obj):
    for modifier in list(obj.modifiers):
        if modifier.type != "NODES":
            continue
        node_group_name = modifier.node_group.name if modifier.node_group else ""
        if modifier.name.startswith(EYE_TRANSPARENCY_MODIFIER_PREFIX) or node_group_name in GEOMETRY_NODE_PREFS["EYE_TRANSPARENCY"]:
            obj.modifiers.remove(modifier)


def _attach_named_geo_modifier(obj, node_group, name: str):
    modifier = obj.modifiers.get(name)
    if modifier is None or modifier.type != "NODES":
        modifier = obj.modifiers.new(name, "NODES")
    modifier.name = name
    modifier.node_group = node_group
    return modifier


def _remove_face_outline_modifiers(obj):
    for modifier in list(obj.modifiers):
        if modifier.type == "SOLIDIFY":
            obj.modifiers.remove(modifier)


def _remove_solidify_outline_modifiers(obj):
    for modifier in list(obj.modifiers):
        if modifier.type == "SOLIDIFY":
            obj.modifiers.remove(modifier)


def _ensure_modifier_sequence(obj, modifiers, after_types=("ARMATURE",)):
    target_index = 0
    for index, modifier in enumerate(obj.modifiers):
        if modifier.type in after_types:
            target_index = index + 1
    for modifier in modifiers:
        if modifier is None:
            continue
        current_index = obj.modifiers.find(modifier.name)
        if current_index < 0:
            continue
        if current_index != target_index:
            obj.modifiers.move(current_index, target_index)
        target_index += 1


def _copy_alpha_template(settings: ENDFIELD_PG_Settings, role: str, base_material, target_name: str):
    library = _effective_library_path(settings)
    template = _find_or_append_first_material(library, ALPHA_TEMPLATE_PREFS[role])
    if template is None:
        template = bpy.data.materials.get(target_name)
    if template is None:
        template = _create_fallback_alpha_material(target_name)
        template.name = target_name
        return template

    material = bpy.data.materials.get(target_name)
    if material is None:
        material = template.copy()
        material.name = target_name

    _patch_material_for_eevee_compat(material)
    base_nodes = _find_nodes_for_role(base_material, "tex_d")
    source_image = base_nodes[0].image if base_nodes else None
    if source_image is None:
        for node in _iter_tex_image_nodes(base_material):
            image = getattr(node, "image", None)
            if _image_is_usable(image):
                source_image = image
                break
    if source_image is not None:
        for node in _iter_tex_image_nodes(material):
            node.image = source_image
    _sync_material_alpha_settings(material, template)
    return material


def _ensure_face_material_bundle(settings: ENDFIELD_PG_Settings, obj, face_material=None, related_objects=None, support_materials=None):
    support_materials = support_materials or {}
    iris_material = _find_material_slot(obj, ("iris", "eye", "pupil"))
    brow_material = _find_material_slot(obj, ("brow", "lash", "eyelash"))
    if iris_material is None:
        iris_material = _find_material_slot(obj, ("iris", "eye", "pupil"))
    if brow_material is None:
        brow_material = _find_material_slot(obj, ("brow", "lash", "eyelash"))
    for related in related_objects or ():
        if iris_material is None:
            iris_material = _find_material_slot(related, ("iris", "eye", "eyel", "pupil"))
        if brow_material is None:
            brow_material = _find_material_slot(related, ("brow", "lash", "eyelash"))
        if iris_material is not None and brow_material is not None:
            break
    iris_material = iris_material or support_materials.get("iris")
    brow_material = brow_material or support_materials.get("brow")
    iris_alpha = _copy_alpha_template(settings, "IRIS", iris_material, f"{iris_material.name}_AlphaProxy") if iris_material else support_materials.get("iris_alpha")
    brow_alpha = _copy_alpha_template(settings, "BROW", brow_material, f"{brow_material.name}_AlphaProxy") if brow_material else support_materials.get("brow_alpha")
    return {
        "face": face_material,
        "iris": iris_material,
        "brow": brow_material,
        "iris_alpha": iris_alpha,
        "brow_alpha": brow_alpha,
    }


def _find_material_by_shader_type(obj, shader_type: str):
    if obj is None:
        return None
    for slot in obj.material_slots:
        material = slot.material
        if material is None:
            continue
        if _detect_shader_type_from_material(material) == shader_type:
            return material
    return None


def _ensure_eye_support_materials(settings: ENDFIELD_PG_Settings, obj):
    library = _effective_library_path(settings)
    return {
        "iris": _find_or_append_first_material(library, TEMPLATE_MATERIAL_PREFS["PUPIL"]),
        "brow": _find_or_append_first_material(library, TEMPLATE_MATERIAL_PREFS["BROW"]),
        "iris_alpha": _find_or_append_first_material(library, ALPHA_TEMPLATE_PREFS["IRIS"]),
        "brow_alpha": _find_or_append_first_material(library, ALPHA_TEMPLATE_PREFS["BROW"]),
    }


def _ensure_face_material_bundle(settings: ENDFIELD_PG_Settings, obj, face_material=None, related_objects=None, support_materials=None):
    support_materials = support_materials or {}
    related_objects = list(related_objects or ())

    iris_material = face_material if _detect_shader_type_from_material(face_material) == "PUPIL" else None
    brow_material = face_material if _detect_shader_type_from_material(face_material) == "BROW" else None

    for candidate_obj in (obj, *related_objects):
        if iris_material is None:
            iris_material = _find_material_by_shader_type(candidate_obj, "PUPIL")
        if brow_material is None:
            brow_material = _find_material_by_shader_type(candidate_obj, "BROW")
        if iris_material is not None and brow_material is not None:
            break

    if iris_material is None:
        iris_material = _find_material_slot(obj, ("iris", "eye", "pupil", "eyel"))
    if brow_material is None:
        brow_material = _find_material_slot(obj, ("brow", "lash", "eyelash", "眉", "睫"))
        if brow_material is not None and _detect_shader_type_from_material(brow_material) == "PUPIL":
            brow_material = None

    for related in related_objects:
        if iris_material is None:
            iris_material = _find_material_slot(related, ("iris", "eye", "eyel", "pupil"))
        if brow_material is None:
            brow_material = _find_material_slot(related, ("brow", "lash", "eyelash", "眉", "睫"))
            if brow_material is not None and _detect_shader_type_from_material(brow_material) == "PUPIL":
                brow_material = None
        if iris_material is not None and brow_material is not None:
            break

    iris_material = iris_material or support_materials.get("iris")

    source_brow_material = support_materials.get("brow")
    if source_brow_material is not None:
        if brow_material is None:
            brow_material = source_brow_material
        elif brow_material == iris_material:
            brow_material = source_brow_material
        elif _detect_shader_type_from_material(brow_material) != "BROW":
            brow_material = source_brow_material
        elif "__OLD" in brow_material.name:
            brow_material = source_brow_material
    else:
        brow_material = brow_material or source_brow_material

    iris_alpha = _copy_alpha_template(settings, "IRIS", iris_material, f"{iris_material.name}_AlphaProxy") if iris_material else support_materials.get("iris_alpha")
    brow_alpha = _copy_alpha_template(settings, "BROW", brow_material, f"{brow_material.name}_AlphaProxy") if brow_material else support_materials.get("brow_alpha")
    return {
        "face": face_material,
        "iris": iris_material,
        "brow": brow_material,
        "iris_alpha": iris_alpha,
        "brow_alpha": brow_alpha,
    }


def _configure_eye_transparency_modifier(target_obj, eye_group, bundle, modifier_name=None):
    if target_obj is None or eye_group is None:
        return None
    modifier_name = modifier_name or EYE_TRANSPARENCY_MODIFIER_PREFIX
    if bundle.get("iris") is None and bundle.get("brow") is None:
        _remove_modifier_by_name(target_obj, modifier_name)
        return None

    eye_mod = _attach_named_geo_modifier(target_obj, eye_group, modifier_name)
    _move_modifier_before_outline(target_obj, eye_mod)
    _set_modifier_input(eye_mod, "irisMat", bundle.get("iris"))
    _set_modifier_input(eye_mod, "browMat", bundle.get("brow"))
    _set_modifier_input(eye_mod, "irisAlphaMat", bundle.get("iris_alpha"))
    _set_modifier_input(eye_mod, "browAlphaMat", bundle.get("brow_alpha"))
    return eye_mod


def _configure_smooth_outline_modifier(modifier, outline_material, base_material, st_image, width):
    _set_modifier_input(modifier, "描边宽度", width)
    _set_modifier_input(modifier, "描边材质", outline_material)
    _set_modifier_input(modifier, "使用顶点色控制", False)
    _set_modifier_input(modifier, "_ST", st_image)
    _set_modifier_input(modifier, "使用ST", bool(st_image))
    _set_modifier_input(modifier, "Use material filtering", False)
    _set_modifier_input(modifier, "The material of the object using outline", base_material)


def _remove_face_subdivision_modifier(obj):
    modifier = obj.modifiers.get("Subdivision")
    if modifier is not None and modifier.type == "SUBSURF":
        obj.modifiers.remove(modifier)


def _remove_face_generated_modifiers(obj):
    if obj is None:
        return
    target_group_names = set()
    for key in ("SUN_VEC", "FACE_VECTOR", "SMOOTH_OUTLINE", "FACE_RAYCAST", "EYE_TRANSPARENCY"):
        target_group_names.update(GEOMETRY_NODE_PREFS.get(key, ()))
    for modifier in list(obj.modifiers):
        if modifier.type != "NODES":
            continue
        node_group_name = modifier.node_group.name if modifier.node_group else ""
        if (
            modifier.name in target_group_names
            or node_group_name in target_group_names
            or modifier.name == "Endfield Eye Attribute Patch"
            or modifier.name.startswith(EYE_TRANSPARENCY_MODIFIER_PREFIX)
        ):
            obj.modifiers.remove(modifier)
    _remove_face_subdivision_modifier(obj)


def _is_face_helper_object(obj) -> bool:
    if obj is None:
        return False
    source_names = (SOURCE_HEAD_HELPER_NAME, SOURCE_HEAD_FORWARD_NAME, SOURCE_HEAD_RIGHT_NAME)
    if any(_name_matches_datablock(name, obj.name) for name in source_names):
        return True
    if obj.type != "EMPTY":
        return False
    helper_names = (HEAD_HELPER_NAME, HEAD_FORWARD_NAME, HEAD_RIGHT_NAME)
    if not any(_name_matches_datablock(name, obj.name) for name in helper_names):
        return False
    if obj.parent is not None and _name_matches_datablock(HEAD_HELPER_NAME, obj.parent.name):
        return True
    if any(constraint.type == "CHILD_OF" for constraint in obj.constraints):
        return True
    if obj.get(SOURCE_LIBRARY_STAMP_KEY):
        return True
    for collection in getattr(obj, "users_collection", ()):
        if collection.name in {HELPER_COLLECTION_NAME, UTILITY_COLLECTION_NAME, WIDGETS_COLLECTION_NAME, META_COLLECTION_NAME}:
            return True
    return False


def _face_refresh_material_names(settings: ENDFIELD_PG_Settings):
    names = list(TEMPLATE_MATERIAL_PREFS["FACE"])
    names.extend(OUTLINE_MATERIAL_PREFS["FACE"])
    if settings.face_integrated_eye_transparency:
        names.extend(TEMPLATE_MATERIAL_PREFS["PUPIL"])
        names.extend(TEMPLATE_MATERIAL_PREFS["BROW"])
        names.extend(ALPHA_TEMPLATE_PREFS["IRIS"])
        names.extend(ALPHA_TEMPLATE_PREFS["BROW"])
    return tuple(dict.fromkeys(names))


def _face_refresh_node_group_names(settings: ENDFIELD_PG_Settings):
    names = set(SHADER_GROUP_KEYWORDS["FACE"])
    names.add("Rain")
    for material_name in _face_refresh_material_names(settings):
        for material in bpy.data.materials:
            if _name_matches_datablock(material_name, material.name):
                names.update(_collect_material_node_group_names(material))
    for key in ("SUN_VEC", "FACE_VECTOR", "SMOOTH_OUTLINE", "FACE_RAYCAST"):
        names.update(GEOMETRY_NODE_PREFS.get(key, ()))
    return tuple(sorted(names))


def _force_clean_face_generation(settings: ENDFIELD_PG_Settings, objects):
    if settings.shader_type != "FACE":
        return 0

    _stop_face_uv_calibration_session()

    refreshed = 0
    refreshed += _backup_matching_datablocks(
        bpy.data.objects,
        (
            HEAD_HELPER_NAME,
            HEAD_FORWARD_NAME,
            HEAD_RIGHT_NAME,
            SOURCE_HEAD_HELPER_NAME,
            SOURCE_HEAD_FORWARD_NAME,
            SOURCE_HEAD_RIGHT_NAME,
        ),
        predicate=_is_face_helper_object,
    )
    refreshed += _backup_matching_datablocks(
        bpy.data.materials,
        _face_refresh_material_names(settings),
    )
    refreshed += _backup_matching_datablocks(
        bpy.data.node_groups,
        _face_refresh_node_group_names(settings),
    )

    for obj in objects:
        _remove_face_generated_modifiers(obj)
        _remove_face_outline_modifiers(obj)
        _remove_solidify_outline_modifiers(obj)

    return refreshed


def _iter_face_integrated_eye_entries(settings, source_material_map):
    for item in settings.face_iris_materials:
        source_material = item.source_material
        if source_material is None:
            continue
        source_key = source_material.as_pointer()
        for target_material in source_material_map.get(source_key, []):
            yield "IRIS", target_material
    for item in settings.face_brow_materials:
        source_material = item.source_material
        if source_material is None:
            continue
        source_key = source_material.as_pointer()
        for target_material in source_material_map.get(source_key, []):
            yield "BROW", target_material


def _ensure_face_integrated_eye_node_group(obj, iris_pairs, brow_pairs):
    group_name = f"Endfield Face Eye Transparency {obj.name}"
    group = bpy.data.node_groups.get(group_name)
    if not (group and group.bl_idname == "GeometryNodeTree"):
        group = bpy.data.node_groups.new(group_name, "GeometryNodeTree")

    interface = group.interface
    while interface.items_tree:
        interface.remove(interface.items_tree[0])
    interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = group.nodes
    links = group.links
    nodes.clear()

    group_input = nodes.new("NodeGroupInput")
    group_output = nodes.new("NodeGroupOutput")
    active_camera = nodes.new("GeometryNodeInputActiveCamera")
    object_info = nodes.new("GeometryNodeObjectInfo")
    position = nodes.new("GeometryNodeInputPosition")
    vec_sub = nodes.new("ShaderNodeVectorMath")
    vec_norm = nodes.new("ShaderNodeVectorMath")
    vec_scale = nodes.new("ShaderNodeVectorMath")
    geo_to_instances = nodes.new("GeometryNodeGeometryToInstance")
    join_geometry = nodes.new("GeometryNodeJoinGeometry")

    vec_sub.operation = "SUBTRACT"
    vec_norm.operation = "NORMALIZE"
    vec_scale.operation = "SCALE"
    if "Scale" in vec_scale.inputs:
        vec_scale.inputs["Scale"].default_value = 0.1

    group_input.location = (-1200.0, 0.0)
    active_camera.location = (-1200.0, -260.0)
    object_info.location = (-980.0, -260.0)
    position.location = (-980.0, -40.0)
    vec_sub.location = (-760.0, -140.0)
    vec_norm.location = (-540.0, -140.0)
    vec_scale.location = (-320.0, -140.0)
    geo_to_instances.location = (360.0, -120.0)
    join_geometry.location = (620.0, 0.0)
    group_output.location = (860.0, 0.0)

    links.new(active_camera.outputs["Active Camera"], object_info.inputs["Object"])
    links.new(object_info.outputs["Location"], vec_sub.inputs[0])
    links.new(position.outputs["Position"], vec_sub.inputs[1])
    links.new(vec_sub.outputs["Vector"], vec_norm.inputs[0])
    links.new(vec_norm.outputs["Vector"], vec_scale.inputs[0])
    links.new(group_input.outputs["Geometry"], join_geometry.inputs["Geometry"])
    links.new(geo_to_instances.outputs["Instances"], join_geometry.inputs["Geometry"])
    links.new(join_geometry.outputs["Geometry"], group_output.inputs["Geometry"])

    y = 120.0
    step = -260.0

    def add_branch(base_material, alpha_material, label):
        nonlocal y
        selection = nodes.new("GeometryNodeMaterialSelection")
        set_position = nodes.new("GeometryNodeSetPosition")
        replace_material = nodes.new("GeometryNodeReplaceMaterial")

        selection.location = (-320.0, y)
        set_position.location = (-80.0, y)
        replace_material.location = (160.0, y)
        selection.label = label

        try:
            selection.inputs["Material"].default_value = base_material
        except Exception:
            pass
        try:
            replace_material.inputs["Old"].default_value = base_material
        except Exception:
            pass
        try:
            replace_material.inputs["New"].default_value = alpha_material
        except Exception:
            pass

        links.new(group_input.outputs["Geometry"], set_position.inputs["Geometry"])
        links.new(selection.outputs["Selection"], set_position.inputs["Selection"])
        links.new(vec_scale.outputs["Vector"], set_position.inputs["Offset"])
        links.new(set_position.outputs["Geometry"], replace_material.inputs["Geometry"])
        links.new(replace_material.outputs["Geometry"], geo_to_instances.inputs["Geometry"])
        y += step

    for index, (base_material, alpha_material) in enumerate(iris_pairs, start=1):
        add_branch(base_material, alpha_material, f"Iris {index}")
    for index, (base_material, alpha_material) in enumerate(brow_pairs, start=1):
        add_branch(base_material, alpha_material, f"Brow {index}")

    return group


def _configure_face_integrated_eye_modifiers(settings, obj, library, source_material_map):
    warning = False
    attr_mod = None
    eye_modifiers = []

    if not settings.face_integrated_eye_transparency:
        _remove_modifier_by_name(obj, "Endfield Eye Attribute Patch")
        return warning, attr_mod, eye_modifiers

    attr_group = _ensure_eye_attribute_patch_node_group()
    if attr_group:
        attr_mod = _attach_geo_modifier(obj, attr_group, attr_group.name)
    else:
        warning = True

    _remove_eye_transparency_modifiers(obj)

    configured_entries = list(_iter_face_integrated_eye_entries(settings, source_material_map))
    if not configured_entries:
        return warning, attr_mod, eye_modifiers

    iris_pairs = []
    brow_pairs = []
    for role, target_material in configured_entries:
        if role == "BROW":
            alpha_material = _copy_alpha_template(settings, "BROW", target_material, f"{target_material.name}_AlphaProxy")
            brow_pairs.append((target_material, alpha_material))
        else:
            alpha_material = _copy_alpha_template(settings, "IRIS", target_material, f"{target_material.name}_AlphaProxy")
            iris_pairs.append((target_material, alpha_material))

    if not iris_pairs and not brow_pairs:
        return warning, attr_mod, eye_modifiers

    eye_group = _ensure_face_integrated_eye_node_group(obj, iris_pairs, brow_pairs)
    eye_mod = _attach_named_geo_modifier(obj, eye_group, EYE_TRANSPARENCY_MODIFIER_PREFIX)
    _move_modifier_before_outline(obj, eye_mod)
    eye_modifiers.append(eye_mod)

    return warning, attr_mod, eye_modifiers


def _configure_face_modifiers(settings, obj, face_material, outline_material, helper_rig, library, loaded_images, source_material_map=None):
    warning = False
    sun_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SUN_VEC"])
    sun_mod = obj.modifiers.get(sun_group.name) if sun_group else None
    vector_mod = None
    smooth_mod = None
    raycast_mod = None

    vector_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["FACE_VECTOR"])
    if vector_group:
        vector_mod = _attach_geo_modifier(obj, vector_group, vector_group.name)
        _set_modifier_input(vector_mod, "HC", helper_rig["HC"])
        _set_modifier_input(vector_mod, "HF", helper_rig["HF"])
        _set_modifier_input(vector_mod, "HR", helper_rig["HR"])
        _set_modifier_input(vector_mod, "only need HeadForward", False)
    else:
        warning = True

    smooth_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SMOOTH_OUTLINE"])
    if smooth_group:
        smooth_mod = _attach_geo_modifier(obj, smooth_group, smooth_group.name)
        _configure_smooth_outline_modifier(
            smooth_mod,
            outline_material,
            None,
            loaded_images.get("tex_st"),
            settings.outline_thickness,
        )
    else:
        warning = True

    raycast_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["FACE_RAYCAST"])
    if raycast_group:
        raycast_mod = _attach_geo_modifier(obj, raycast_group, raycast_group.name)
        _set_modifier_input(raycast_mod, "FaceMat", face_material)
    else:
        warning = True

    attr_mod = None
    eye_modifiers = []
    if settings.face_integrated_eye_transparency:
        face_eye_warning, attr_mod, eye_modifiers = _configure_face_integrated_eye_modifiers(
            settings,
            obj,
            library,
            source_material_map or {},
        )
        warning = warning or face_eye_warning
    else:
        _remove_modifier_by_name(obj, "Endfield Eye Attribute Patch")
        _remove_eye_transparency_modifiers(obj)

    _remove_face_subdivision_modifier(obj)
    _ensure_modifier_sequence(obj, [sun_mod, vector_mod, smooth_mod, raycast_mod, attr_mod, *eye_modifiers])
    return warning


def _configure_eye_object_modifiers(settings, obj, eye_material, library):
    warning = False
    support_materials = _ensure_eye_support_materials(settings, obj)
    sun_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SUN_VEC"])
    sun_mod = obj.modifiers.get(sun_group.name) if sun_group else None
    helper_rig = _current_head_helper_rig()
    vector_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["FACE_VECTOR"])
    vector_mod = None
    attr_mod = None
    if vector_group and helper_rig is not None:
        vector_mod = _attach_geo_modifier(obj, vector_group, vector_group.name)
        _set_modifier_input(vector_mod, "HC", helper_rig["HC"])
        _set_modifier_input(vector_mod, "HF", helper_rig["HF"])
        _set_modifier_input(vector_mod, "HR", helper_rig["HR"])
        _set_modifier_input(vector_mod, "only need HeadForward", True)
    else:
        warning = True

    attr_group = _ensure_eye_attribute_patch_node_group()
    if attr_group:
        attr_mod = _attach_geo_modifier(obj, attr_group, attr_group.name)
    else:
        warning = True

    eye_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["EYE_TRANSPARENCY"])
    eye_mod = None
    if eye_group:
        eye_mod = _configure_eye_transparency_modifier(
            obj,
            eye_group,
            _ensure_face_material_bundle(settings, obj, eye_material, support_materials=support_materials),
        )
        if eye_mod is None:
            warning = True
    else:
        warning = True
    _ensure_modifier_sequence(obj, [sun_mod, vector_mod, attr_mod, eye_mod])
    return warning


def _configure_hair_modifiers(settings, obj, library):
    warning = False
    smooth_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SMOOTH_OUTLINE"])
    if smooth_group:
        smooth_mod = _attach_geo_modifier(obj, smooth_group, smooth_group.name)
        _configure_smooth_outline_modifier(
            smooth_mod,
            obj.material_slots[1].material if len(obj.material_slots) > 1 else None,
            obj.material_slots[0].material if len(obj.material_slots) > 0 else None,
            None,
            settings.outline_thickness,
        )
        _move_modifier_before_outline(obj, smooth_mod)
    else:
        warning = True

    shadow_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SHADOW_PROXY"])
    if shadow_group:
        shadow_mod = _attach_geo_modifier(obj, shadow_group, shadow_group.name)
        _move_modifier_after_outline(obj, shadow_mod)
        _set_modifier_input(shadow_mod, "Shadow Proxy", _ensure_shadow_proxy_material(settings))
        _set_modifier_input(shadow_mod, "Pos Offset", -0.38)
        _set_modifier_input(shadow_mod, "Pos Debug", False)
    else:
        warning = True
    return warning


def _configure_surface_outline_modifiers(settings, obj, primary_material, outline_material, library, loaded_images, include_time=False):
    warning = False
    weld_mod = None
    if getattr(settings, "shader_type", "") == "BODY":
        weld_mod = _ensure_body_weld_modifier(obj)

    smooth_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SMOOTH_OUTLINE"])
    smooth_mod = None
    time_mod = None
    if smooth_group:
        smooth_mod = _attach_geo_modifier(obj, smooth_group, smooth_group.name)
        _configure_smooth_outline_modifier(
            smooth_mod,
            outline_material,
            primary_material,
            loaded_images.get("tex_st"),
            settings.outline_thickness,
        )
    else:
        warning = True

    if include_time:
        time_group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["TIME_SETUP"])
        if time_group:
            time_mod = _attach_geo_modifier(obj, time_group, time_group.name)
        else:
            warning = True

    _ensure_modifier_sequence(obj, [weld_mod, obj.modifiers.get(GEOMETRY_NODE_PREFS["SUN_VEC"][0]), smooth_mod, time_mod])
    return warning


def _configure_common_geo_modifier(obj, library):
    group = _find_or_append_node_group(library, GEOMETRY_NODE_PREFS["SUN_VEC"])
    if not group:
        return True
    lf = _find_matching_object(SUN_HELPER_LF_NAME)
    lc = _find_matching_object(SUN_HELPER_LC_NAME)
    if lf is None or lc is None:
        return True
    _rebind_sun_vec_targets(group, lf, lc)
    modifier = _attach_geo_modifier(obj, group, group.name)
    _move_modifier_before_outline(obj, modifier)
    return False


def _is_outline_like(material) -> bool:
    if not material:
        return False
    name = material.name.lower()
    return "outline" in name or "shadow proxy" in name or name.startswith("mmd_edge.")


def _slot_indices_for_object(obj, settings: ENDFIELD_PG_Settings):
    if len(obj.material_slots) == 0:
        obj.data.materials.append(None)

    selected_eye_materials = {
        item.source_material
        for item in [*getattr(settings, "face_iris_materials", []), *getattr(settings, "face_brow_materials", [])]
        if item.source_material is not None
    }
    extra_indices = set()
    if settings.shader_type == "FACE" and settings.face_integrated_eye_transparency and selected_eye_materials:
        for index, slot in enumerate(obj.material_slots):
            if slot.material in selected_eye_materials:
                extra_indices.add(index)

    if settings.apply_mode == "ALL_SLOTS":
        indices = []
        for index, slot in enumerate(obj.material_slots):
            if _is_outline_like(slot.material):
                continue
            indices.append(index)
        indices.extend(sorted(extra_indices))
        return sorted(set(indices)) or [0]
    indices = {max(0, obj.active_material_index), *extra_indices}
    return sorted(indices)


def _detect_shader_type_from_material(material):
    node = _find_main_shader_node(material)
    if node is None or not node.node_tree:
        return None
    name = node.node_tree.name
    if "BaseHair" in name:
        return "HAIR"
    if "FaceBase" in name or "BaseFace" in name:
        return "FACE"
    if "irisBase" in name:
        return "PUPIL"
    if "BaseBrow" in name:
        return "BROW"
    if "PBRToonBase" in name:
        return "BODY" if "body" in material.name.lower() else "CLOTH" if "cloth" in material.name.lower() else "BODY"
    return None


def _find_main_shader_node(material):
    if not material or not material.use_nodes or not material.node_tree:
        return None
    groups = [node for node in material.node_tree.nodes if node.type == "GROUP" and node.node_tree]
    for shader_type in ("FACE", "HAIR", "PUPIL", "BROW", "BODY", "CLOTH"):
        for node in groups:
            if any(keyword in node.node_tree.name for keyword in SHADER_GROUP_KEYWORDS[shader_type]):
                return node
    return None


def _set_main_shader_input_default(material, socket_name: str, value):
    shader_node = _find_main_shader_node(material)
    if shader_node is None:
        return False
    socket = shader_node.inputs.get(socket_name)
    if socket is None or not hasattr(socket, "default_value"):
        return False
    try:
        socket.default_value = value
        return True
    except Exception:
        return False


def _apply_material_quality_correction(material, shader_type: str, role_presence: dict):
    if material is None or shader_type != "CLOTH":
        return

    shader_node = _find_main_shader_node(material)
    if shader_node is None:
        return

    if role_presence.get("tex_n"):
        socket = shader_node.inputs.get("NormalStrength")
        if socket is not None and hasattr(socket, "default_value"):
            try:
                socket.default_value = max(float(socket.default_value), 1.35)
            except Exception:
                pass

    if role_presence.get("tex_p"):
        socket = shader_node.inputs.get("CastShadow_sharp")
        if socket is not None and hasattr(socket, "default_value"):
            try:
                socket.default_value = max(float(socket.default_value), 0.22)
            except Exception:
                pass

def _find_face_sdf_image_nodes(node_tree):
    if not node_tree:
        return []
    results = []
    for node in node_tree.nodes:
        if node.type != "TEX_IMAGE":
            continue
        image = getattr(node, "image", None)
        image_name = image.name.lower() if image else ""
        node_name = f"{node.name} {node.label}".lower()
        output_names = " ".join(getattr(link.to_node, "name", "").lower() for output in node.outputs for link in output.links)
        input_names = " ".join(getattr(link.from_node, "name", "").lower() for socket in node.inputs for link in socket.links)
        if (
            "common_female_face_01_sdf" in image_name
            or "common_female_face_02_sdf" in image_name
            or "face_01_sdf" in image_name
            or "face_02_sdf" in image_name
            or "sdf" in node_name
            or "分离 xyz.001" in output_names
            or "separate xyz.001" in output_names
            or "endfield_face_sdf_mapping" in input_names
        ):
            results.append(node)
    return results


def _find_face_cm_image_nodes(node_tree):
    if not node_tree:
        return []
    results = []
    for node in node_tree.nodes:
        if node.type != "TEX_IMAGE":
            continue
        image = getattr(node, "image", None)
        image_name = image.name.lower() if image else ""
        node_name = f"{node.name} {node.label}".lower()
        output_names = " ".join(getattr(link.to_node, "name", "").lower() for output in node.outputs for link in output.links)
        input_names = " ".join(getattr(link.from_node, "name", "").lower() for socket in node.inputs for link in socket.links)
        if (
            "common_female_face_01_cm_m" in image_name
            or "cm_m" in node_name
            or "转接点.111" in output_names
            or "转接点.112" in output_names
            or "endfield_face_cm_mapping" in input_names
        ):
            results.append(node)
    return results


def _restore_face_template_images(target_tree, source_tree):
    if target_tree is None or source_tree is None:
        return

    source_nodes = {
        node.name: node
        for node in source_tree.nodes
        if getattr(node, "type", "") == "TEX_IMAGE" and getattr(node, "image", None) is not None
    }
    if not source_nodes:
        return

    for target_node in target_tree.nodes:
        if getattr(target_node, "type", "") != "TEX_IMAGE":
            continue
        source_node = source_nodes.get(target_node.name)
        if source_node is None:
            continue
        source_image = getattr(source_node, "image", None)
        if source_image is None:
            continue
        target_image = getattr(target_node, "image", None)
        if target_image is None or not _image_is_usable(target_image):
            target_node.image = source_image


def _ensure_local_face_shader_group(material):
    shader_node = _find_main_shader_node(material)
    if shader_node is None or not shader_node.node_tree:
        return None
    if _detect_shader_type_from_material(material) != "FACE":
        _patch_node_tree_for_eevee_compat(shader_node.node_tree)
        return shader_node.node_tree
    node_tree = shader_node.node_tree
    if node_tree.get("_endfield_face_group_local"):
        _patch_node_tree_for_eevee_compat(node_tree)
        return node_tree
    localized = node_tree.copy()
    localized["_endfield_face_group_local"] = True
    localized["_endfield_face_group_source"] = node_tree.name
    _restore_face_template_images(localized, node_tree)
    _patch_node_tree_for_eevee_compat(localized)
    shader_node.node_tree = localized
    return localized


def _ensure_face_sdf_mapping_controls(material):
    node_tree = _ensure_local_face_shader_group(material)
    if not node_tree:
        return None

    sdf_nodes = _find_face_sdf_image_nodes(node_tree)
    if not sdf_nodes:
        return None

    mapping_name = "ENDFIELD_FACE_SDF_MAPPING"
    mapping_node = node_tree.nodes.get(mapping_name)
    if mapping_node and mapping_node.bl_idname != "ShaderNodeMapping":
        node_tree.nodes.remove(mapping_node)
        mapping_node = None

    for tex_node in sdf_nodes:
        vector_input = tex_node.inputs.get("Vector")
        if vector_input is None:
            continue
        source_socket = None
        if vector_input.is_linked:
            link = vector_input.links[0]
            if link.from_node == mapping_node:
                continue
            source_socket = link.from_socket
            node_tree.links.remove(link)
        if mapping_node is None:
            mapping_node = node_tree.nodes.new("ShaderNodeMapping")
            mapping_node.name = mapping_name
            mapping_node.label = "Face SDF Mapping"
            mapping_node.location = (tex_node.location.x - 220.0, tex_node.location.y)
            if hasattr(mapping_node, "vector_type"):
                mapping_node.vector_type = "POINT"
        if source_socket is not None and not mapping_node.inputs["Vector"].is_linked:
            node_tree.links.new(source_socket, mapping_node.inputs["Vector"])
        if not vector_input.is_linked:
            node_tree.links.new(mapping_node.outputs["Vector"], vector_input)

    return mapping_node


def _ensure_face_cm_mapping_controls(material):
    node_tree = _ensure_local_face_shader_group(material)
    if not node_tree:
        return None

    cm_nodes = _find_face_cm_image_nodes(node_tree)
    if not cm_nodes:
        return None

    mapping_name = "ENDFIELD_FACE_CM_MAPPING"
    uv_name = "ENDFIELD_FACE_CM_UV"
    mapping_node = node_tree.nodes.get(mapping_name)
    if mapping_node and mapping_node.bl_idname != "ShaderNodeMapping":
        node_tree.nodes.remove(mapping_node)
        mapping_node = None

    uv_node = node_tree.nodes.get(uv_name)
    if uv_node and uv_node.bl_idname != "ShaderNodeUVMap":
        node_tree.nodes.remove(uv_node)
        uv_node = None

    for tex_node in cm_nodes:
        vector_input = tex_node.inputs.get("Vector")
        if vector_input is None:
            continue
        source_socket = None
        if vector_input.is_linked:
            link = vector_input.links[0]
            if link.from_node == mapping_node:
                continue
            source_socket = link.from_socket
            node_tree.links.remove(link)
        if uv_node is None:
            uv_node = node_tree.nodes.new("ShaderNodeUVMap")
            uv_node.name = uv_name
            uv_node.label = "Face CM UV"
            uv_node.location = (tex_node.location.x - 440.0, tex_node.location.y)
        if mapping_node is None:
            mapping_node = node_tree.nodes.new("ShaderNodeMapping")
            mapping_node.name = mapping_name
            mapping_node.label = "Face CM Mapping"
            mapping_node.location = (tex_node.location.x - 220.0, tex_node.location.y)
            if hasattr(mapping_node, "vector_type"):
                mapping_node.vector_type = "POINT"
        if source_socket is None:
            source_socket = uv_node.outputs.get("UV")
        if source_socket is not None and not mapping_node.inputs["Vector"].is_linked:
            node_tree.links.new(source_socket, mapping_node.inputs["Vector"])
        if not vector_input.is_linked:
            node_tree.links.new(mapping_node.outputs["Vector"], vector_input)

    return mapping_node


def _face_sdf_mapping_node(material):
    shader_node = _find_main_shader_node(material)
    if shader_node is None or not shader_node.node_tree:
        return None
    node_tree = shader_node.node_tree
    mapping = node_tree.nodes.get("ENDFIELD_FACE_SDF_MAPPING")
    if mapping and mapping.bl_idname == "ShaderNodeMapping":
        return mapping
    return None


def _face_cm_mapping_node(material):
    shader_node = _find_main_shader_node(material)
    if shader_node is None or not shader_node.node_tree:
        return None
    node_tree = shader_node.node_tree
    mapping = node_tree.nodes.get("ENDFIELD_FACE_CM_MAPPING")
    if mapping and mapping.bl_idname == "ShaderNodeMapping":
        return mapping
    return None


def _ensure_face_mapping_node(material, target: str):
    if target == "SDF":
        return _ensure_face_sdf_mapping_controls(material)
    if target == "CM":
        return _ensure_face_cm_mapping_controls(material)
    return None


def _adjust_face_mapping(material, target: str, socket_name: str, index: int, delta: float):
    mapping_node = _ensure_face_mapping_node(material, target)
    if mapping_node is None:
        return None
    socket = mapping_node.inputs.get(socket_name)
    if socket is None or not hasattr(socket, "default_value"):
        return None
    values = list(socket.default_value)
    if index >= len(values):
        return None
    values[index] += delta
    socket.default_value = values
    return mapping_node


def _first_usable_image(nodes):
    for node in nodes:
        image = getattr(node, "image", None)
        if image is not None:
            return image
    return None


def _face_base_image(material):
    image = _first_usable_image(_find_nodes_for_role(material, "tex_d"))
    if image is not None:
        return image
    shader_node = _find_main_shader_node(material)
    if shader_node is None or not shader_node.node_tree:
        return None
    return _first_usable_image(_iter_tex_image_nodes(material))


def _face_uv_overlay_images(material):
    shader_node = _find_main_shader_node(material)
    if shader_node is None or not shader_node.node_tree:
        return (None, None, None)
    node_tree = shader_node.node_tree
    return (
        _face_base_image(material),
        _first_usable_image(_find_face_sdf_image_nodes(node_tree)),
        _first_usable_image(_find_face_cm_image_nodes(node_tree)),
    )


def _ensure_face_uv_preview_image(source_image, preview_name: str, tint, alpha: float):
    if source_image is None:
        return None
    width = max(int(source_image.size[0]), 1)
    height = max(int(source_image.size[1]), 1)
    preview = bpy.data.images.get(preview_name)
    if preview is None or tuple(preview.size[:]) != (width, height):
        if preview is not None:
            try:
                bpy.data.images.remove(preview)
            except Exception:
                pass
        preview = bpy.data.images.new(preview_name, width, height, alpha=True)
        preview.alpha_mode = "STRAIGHT"
    try:
        pixels = list(source_image.pixels[:])
    except Exception:
        return preview
    result = [0.0] * len(pixels)
    for index in range(0, len(pixels), 4):
        strength = max(pixels[index], pixels[index + 1], pixels[index + 2])
        strength = max(strength, 0.12)
        result[index] = tint[0] * strength
        result[index + 1] = tint[1] * strength
        result[index + 2] = tint[2] * strength
        result[index + 3] = alpha * max(0.25, strength)
    preview.pixels.foreach_set(result)
    preview.update()
    return preview


def _safe_mapping_scale(value: float) -> float:
    value = float(value)
    if abs(value) < 1.0e-6:
        return 1.0e-6 if value >= 0.0 else -1.0e-6
    return value


def _face_uv_rect_from_mapping(mapping_node):
    if mapping_node is None:
        return None
    location = mapping_node.inputs["Location"].default_value
    scale = mapping_node.inputs["Scale"].default_value
    scale_x = _safe_mapping_scale(scale[0])
    scale_y = _safe_mapping_scale(scale[1])
    u0 = -float(location[0]) / scale_x
    u1 = (1.0 - float(location[0])) / scale_x
    v0 = -float(location[1]) / scale_y
    v1 = (1.0 - float(location[1])) / scale_y
    return (u0, v0, u1, v1)


def _set_face_uv_mapping_from_rect(mapping_node, rect):
    if mapping_node is None or rect is None:
        return
    u0, v0, u1, v1 = rect
    width = u1 - u0
    height = v1 - v0
    if abs(width) < 1.0e-6 or abs(height) < 1.0e-6:
        return
    scale_x = 1.0 / width
    scale_y = 1.0 / height
    location = list(mapping_node.inputs["Location"].default_value)
    scale = list(mapping_node.inputs["Scale"].default_value)
    scale[0] = scale_x
    scale[1] = scale_y
    location[0] = -u0 * scale_x
    location[1] = -v0 * scale_y
    mapping_node.inputs["Scale"].default_value = scale
    mapping_node.inputs["Location"].default_value = location


def _ensure_face_uv_shader():
    global FACE_UV_SHADER
    if FACE_UV_SHADER is not None:
        return FACE_UV_SHADER
    vertex_source = """
uniform mat4 ModelViewProjectionMatrix;
in vec2 pos;
in vec2 texCoord;
out vec2 uvInterp;
void main()
{
    uvInterp = texCoord;
    gl_Position = ModelViewProjectionMatrix * vec4(pos.xy, 0.0, 1.0);
}
"""
    fragment_source = """
uniform sampler2D image;
uniform float alpha;
uniform vec3 tint;
in vec2 uvInterp;
out vec4 fragColor;
void main()
{
    vec4 color = texture(image, uvInterp);
    float strength = max(max(color.r, color.g), color.b);
    strength = max(strength, 0.18);
    fragColor = vec4(tint.rgb * strength, alpha);
}
"""
    FACE_UV_SHADER = gpu.types.GPUShader(vertex_source, fragment_source)
    return FACE_UV_SHADER


def _face_uv_texture(image):
    if image is None:
        return None
    key = image.name_full
    cached = FACE_UV_TEXTURE_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        texture = gpu.texture.from_image(image)
    except Exception:
        return None
    FACE_UV_TEXTURE_CACHE[key] = texture
    return texture


def _clear_face_uv_texture_cache():
    FACE_UV_TEXTURE_CACHE.clear()


def _face_uv_state_material():
    name = FACE_UV_CALIBRATION_STATE.get("material_name", "")
    return bpy.data.materials.get(name) if name else None


def _face_uv_state_object():
    name = FACE_UV_CALIBRATION_STATE.get("object_name", "")
    return bpy.data.objects.get(name) if name else None


def _face_uv_state_image(key: str):
    name = FACE_UV_CALIBRATION_STATE.get(key, "")
    return bpy.data.images.get(name) if name else None


def _iter_image_editor_areas():
    window_manager = getattr(bpy.context, "window_manager", None)
    if window_manager is None:
        return
    for window in window_manager.windows:
        screen = window.screen
        if screen is None:
            continue
        for area in screen.areas:
            if area.type == "IMAGE_EDITOR":
                yield window, area


def _assign_image_to_image_editors(image):
    if image is None:
        return
    for _window, area in _iter_image_editor_areas():
        for space in area.spaces:
            if space.type == "IMAGE_EDITOR":
                space.image = image


def _snapshot_image_editor_images():
    snapshots = []
    for window, area in _iter_image_editor_areas():
        for space in area.spaces:
            if space.type != "IMAGE_EDITOR":
                continue
            image = getattr(space, "image", None)
            snapshots.append(
                {
                    "window_ptr": window.as_pointer(),
                    "area_ptr": area.as_pointer(),
                    "image_name": image.name if image is not None else "",
                }
            )
            break
    return snapshots


def _restore_image_editor_images(snapshots):
    if not snapshots:
        return
    snapshot_map = {
        (item.get("window_ptr"), item.get("area_ptr")): item.get("image_name", "")
        for item in snapshots
    }
    for window, area in _iter_image_editor_areas():
        image_name = snapshot_map.get((window.as_pointer(), area.as_pointer()))
        if image_name is None:
            continue
        image = bpy.data.images.get(image_name) if image_name else None
        for space in area.spaces:
            if space.type == "IMAGE_EDITOR":
                space.image = image
                break


def _fit_image_editors_view():
    for window, area in _iter_image_editor_areas():
        region = next((region for region in area.regions if region.type == "WINDOW"), None)
        space = next((space for space in area.spaces if space.type == "IMAGE_EDITOR"), None)
        if region is None or space is None:
            continue
        override = {
            "window": window,
            "screen": window.screen,
            "area": area,
            "region": region,
            "space_data": space,
        }
        try:
            with bpy.context.temp_override(**override):
                bpy.ops.image.view_all(fit_view=True)
        except Exception:
            continue


def _face_uv_session_from_context(context):
    obj = context.object
    material = obj.active_material if obj else None
    if obj is None or material is None or _detect_shader_type_from_material(material) != "FACE":
        return None
    _ensure_face_sdf_mapping_controls(material)
    _ensure_face_cm_mapping_controls(material)
    base_image, sdf_image, cm_image = _face_uv_overlay_images(material)
    if base_image is None:
        return None
    return {
        "object": obj,
        "material": material,
        "base_image": base_image,
        "sdf_image": sdf_image,
        "cm_image": cm_image,
    }


def _start_face_uv_calibration_session(context):
    session = _face_uv_session_from_context(context)
    if session is None:
        return None

    if FACE_UV_CALIBRATION_STATE.get("running"):
        _stop_face_uv_calibration_session()

    _clear_face_uv_texture_cache()
    FACE_UV_CALIBRATION_STATE["editor_images"] = _snapshot_image_editor_images()
    sdf_preview = _ensure_face_uv_preview_image(session["sdf_image"], "ENDFIELD_FACE_SDF_PREVIEW", (0.18, 0.85, 1.0), 0.38) if session["sdf_image"] is not None else None
    cm_preview = _ensure_face_uv_preview_image(session["cm_image"], "ENDFIELD_FACE_CM_PREVIEW", (1.0, 0.72, 0.18), 0.32) if session["cm_image"] is not None else None
    FACE_UV_CALIBRATION_STATE["running"] = True
    FACE_UV_CALIBRATION_STATE["material_name"] = session["material"].name
    FACE_UV_CALIBRATION_STATE["object_name"] = session["object"].name
    FACE_UV_CALIBRATION_STATE["base_image_name"] = session["base_image"].name
    FACE_UV_CALIBRATION_STATE["sdf_image_name"] = session["sdf_image"].name if session["sdf_image"] is not None else ""
    FACE_UV_CALIBRATION_STATE["cm_image_name"] = session["cm_image"].name if session["cm_image"] is not None else ""
    FACE_UV_CALIBRATION_STATE["sdf_preview_image_name"] = sdf_preview.name if sdf_preview is not None else ""
    FACE_UV_CALIBRATION_STATE["cm_preview_image_name"] = cm_preview.name if cm_preview is not None else ""
    FACE_UV_CALIBRATION_STATE["dragging"] = False
    FACE_UV_CALIBRATION_STATE["drag_target"] = ""
    FACE_UV_CALIBRATION_STATE["drag_mode"] = ""
    _assign_image_to_image_editors(session["base_image"])
    _fit_image_editors_view()

    if FACE_UV_CALIBRATION_STATE.get("draw_handle") is None:
        FACE_UV_CALIBRATION_STATE["draw_handle"] = bpy.types.SpaceImageEditor.draw_handler_add(
            _draw_face_uv_calibration_overlay,
            (),
            "WINDOW",
            "POST_PIXEL",
        )
    _tag_all_areas_for_redraw()
    return session


def _stop_face_uv_calibration_session():
    _restore_image_editor_images(FACE_UV_CALIBRATION_STATE.get("editor_images") or [])
    handle = FACE_UV_CALIBRATION_STATE.get("draw_handle")
    if handle is not None:
        try:
            bpy.types.SpaceImageEditor.draw_handler_remove(handle, "WINDOW")
        except Exception:
            pass
    FACE_UV_CALIBRATION_STATE["draw_handle"] = None
    FACE_UV_CALIBRATION_STATE["running"] = False
    FACE_UV_CALIBRATION_STATE["dragging"] = False
    FACE_UV_CALIBRATION_STATE["drag_target"] = ""
    FACE_UV_CALIBRATION_STATE["drag_mode"] = ""
    FACE_UV_CALIBRATION_STATE["drag_start_uv"] = (0.0, 0.0)
    FACE_UV_CALIBRATION_STATE["drag_rect"] = (0.0, 0.0, 1.0, 1.0)
    FACE_UV_CALIBRATION_STATE["editor_images"] = []
    _clear_face_uv_texture_cache()
    for key in ("sdf_preview_image_name", "cm_preview_image_name"):
        preview = _face_uv_state_image(key)
        if preview is not None:
            try:
                bpy.data.images.remove(preview)
            except Exception:
                pass
        FACE_UV_CALIBRATION_STATE[key] = ""
    for key in ("material_name", "object_name", "base_image_name", "sdf_image_name", "cm_image_name"):
        FACE_UV_CALIBRATION_STATE[key] = ""
    _tag_all_areas_for_redraw()


def _face_uv_region_from_context(context):
    if context.region and context.region.type == "WINDOW":
        return context.region
    if context.area is None:
        return None
    for region in context.area.regions:
        if region.type == "WINDOW":
            return region
    return None


def _face_uv_event_to_uv(context, event, base_image):
    region = _face_uv_region_from_context(context)
    if region is None or base_image is None:
        return None
    view_x, view_y = region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
    return (view_x, view_y)


def _face_uv_rect_contains(rect, uv):
    if rect is None or uv is None:
        return False
    u0, v0, u1, v1 = rect
    u_min, u_max = sorted((u0, u1))
    v_min, v_max = sorted((v0, v1))
    return u_min <= uv[0] <= u_max and v_min <= uv[1] <= v_max


def _face_uv_current_rects(material):
    return {
        "SDF": _face_uv_rect_from_mapping(_face_sdf_mapping_node(material)),
        "CM": _face_uv_rect_from_mapping(_face_cm_mapping_node(material)),
    }


def _pick_face_uv_target(settings, material, uv):
    rects = _face_uv_current_rects(material)
    visible = []
    if settings.face_uv_show_sdf and rects["SDF"] is not None:
        visible.append("SDF")
    if settings.face_uv_show_cm and rects["CM"] is not None:
        visible.append("CM")
    if not visible:
        return None
    preferred = settings.face_uv_active_target
    order = [preferred] + [item for item in visible if item != preferred]
    for target in order:
        rect = rects.get(target)
        if _face_uv_rect_contains(rect, uv):
            return target
    return preferred if preferred in visible else visible[0]


def _apply_face_uv_drag(material, target: str, mode: str, start_rect, start_uv, current_uv):
    mapping_node = _ensure_face_mapping_node(material, target)
    if mapping_node is None:
        return
    if start_rect is None or start_uv is None or current_uv is None:
        return

    u0, v0, u1, v1 = start_rect
    du = current_uv[0] - start_uv[0]
    dv = current_uv[1] - start_uv[1]

    if mode == "SCALE":
        center_u = (u0 + u1) * 0.5
        center_v = (v0 + v1) * 0.5
        half_w = max(abs(u1 - u0) * 0.5 + du, 1.0e-4)
        half_h = max(abs(v1 - v0) * 0.5 + dv, 1.0e-4)
        rect = (center_u - half_w, center_v - half_h, center_u + half_w, center_v + half_h)
    else:
        rect = (u0 + du, v0 + dv, u1 + du, v1 + dv)

    _set_face_uv_mapping_from_rect(mapping_node, rect)
    _tag_all_areas_for_redraw()


def _draw_face_uv_textured_rect(region, base_image, overlay_image, rect):
    if region is None or base_image is None or overlay_image is None or rect is None:
        return
    u0, v0, u1, v1 = rect
    texture = _face_uv_texture(overlay_image)
    if texture is None:
        return
    lower_left = region.view2d.view_to_region(u0, v0, clip=False)
    upper_right = region.view2d.view_to_region(u1, v1, clip=False)
    draw_width = upper_right[0] - lower_left[0]
    draw_height = upper_right[1] - lower_left[1]
    if abs(draw_width) < 1.0 or abs(draw_height) < 1.0:
        return
    gpu.state.blend_set("ALPHA")
    draw_texture_2d(texture, lower_left, draw_width, draw_height)


def _draw_face_uv_outline(region, base_image, rect, color):
    if region is None or base_image is None or rect is None:
        return
    u0, v0, u1, v1 = rect
    points = [
        region.view2d.view_to_region(u0, v0, clip=False),
        region.view2d.view_to_region(u1, v0, clip=False),
        region.view2d.view_to_region(u1, v1, clip=False),
        region.view2d.view_to_region(u0, v1, clip=False),
    ]
    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    batch = batch_for_shader(shader, "LINE_LOOP", {"pos": points})
    gpu.state.blend_set("ALPHA")
    gpu.state.line_width_set(2.0)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.line_width_set(1.0)


def _draw_face_uv_calibration_overlay():
    if not FACE_UV_CALIBRATION_STATE.get("running"):
        return
    context = bpy.context
    region = context.region
    if region is None or region.type != "WINDOW":
        return

    material = _face_uv_state_material()
    base_image = _face_uv_state_image("base_image_name")
    if material is None or base_image is None:
        return

    settings = context.scene.endfield_toon_settings
    rects = _face_uv_current_rects(material)
    if settings.face_uv_show_sdf:
        _draw_face_uv_textured_rect(region, base_image, _face_uv_state_image("sdf_preview_image_name"), rects["SDF"])
        _draw_face_uv_outline(region, base_image, rects["SDF"], (0.5, 0.9, 1.0, 0.95) if settings.face_uv_active_target == "SDF" else (0.5, 0.9, 1.0, 0.55))
    if settings.face_uv_show_cm:
        _draw_face_uv_textured_rect(region, base_image, _face_uv_state_image("cm_preview_image_name"), rects["CM"])
        _draw_face_uv_outline(region, base_image, rects["CM"], (1.0, 0.8, 0.35, 0.95) if settings.face_uv_active_target == "CM" else (1.0, 0.8, 0.35, 0.55))

def _sanitize_name_fragment(text: str, max_len: int = 36) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_]+", "_", text or "")
    cleaned = cleaned.strip("_")
    if not cleaned:
        cleaned = "Item"
    return cleaned[:max_len]


def _ensure_face_tex_control_collection():
    scene_root = bpy.context.scene.collection
    collection = bpy.data.collections.get(FACE_TEX_CONTROL_COLLECTION_NAME)
    if collection is None:
        collection = bpy.data.collections.new(FACE_TEX_CONTROL_COLLECTION_NAME)
    if collection.name not in {child.name for child in scene_root.children}:
        scene_root.children.link(collection)
    return collection


def _material_face_tex_control_name(material, suffix: str) -> str:
    fragment = _sanitize_name_fragment(material.name, max_len=28)
    return f"ENDFIELD_{fragment}_{suffix}"


def _material_face_tex_control_object(material, prop_key: str, fallback_suffix: str = ""):
    if material is None:
        return None
    name = material.get(prop_key, "")
    obj = bpy.data.objects.get(name) if name else None
    if obj is not None:
        return obj
    if fallback_suffix:
        return bpy.data.objects.get(_material_face_tex_control_name(material, fallback_suffix))
    return None


def _world_bbox_points(obj):
    if obj is None or getattr(obj, "type", "") != "MESH":
        location = obj.matrix_world.translation.copy() if obj is not None else Vector((0.0, 0.0, 0.0))
        return [location]
    return [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]


def _projected_span(points, center: Vector, axis: Vector) -> float:
    if not points:
        return 0.0
    values = [(point - center).dot(axis) for point in points]
    return max(values) - min(values)


def _safe_normalized(vector: Vector, fallback: Vector) -> Vector:
    if vector.length <= 1.0e-8:
        return fallback.normalized()
    return vector.normalized()


def _face_control_basis(obj):
    points = _world_bbox_points(obj)
    center = sum(points, Vector((0.0, 0.0, 0.0))) / max(len(points), 1)

    helper_rig = _current_head_helper_rig()
    if helper_rig is not None:
        hc = helper_rig["HC"].matrix_world.translation
        hf = helper_rig["HF"].matrix_world.translation
        hr = helper_rig["HR"].matrix_world.translation
        x_axis = _safe_normalized(hr - hc, Vector((1.0, 0.0, 0.0)))
        forward = _safe_normalized(hf - hc, Vector((0.0, -1.0, 0.0)))
        z_axis = _safe_normalized(x_axis.cross(forward), Vector((0.0, 0.0, 1.0)))
        forward = _safe_normalized(z_axis.cross(x_axis), forward)
    else:
        basis = obj.matrix_world.to_3x3()
        x_axis = _safe_normalized(basis @ Vector((1.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0)))
        z_axis = _safe_normalized(basis @ Vector((0.0, 0.0, 1.0)), Vector((0.0, 0.0, 1.0)))
        forward = _safe_normalized(-(basis @ Vector((0.0, 1.0, 0.0))), Vector((0.0, -1.0, 0.0)))

    depth_span = max(_projected_span(points, center, forward), 0.02)
    origin = center + forward * max(depth_span * 0.6, 0.02)
    span_x = max(_projected_span(points, center, x_axis), 0.02)
    span_z = max(_projected_span(points, center, z_axis), 0.02)
    basis_matrix = Matrix((x_axis, forward, z_axis)).transposed().to_4x4()
    return origin, basis_matrix, span_x, span_z


def _configure_face_tex_control_object(obj, display_size: float):
    if obj is None:
        return
    if obj.type == "EMPTY":
        obj.empty_display_type = "CUBE"
        obj.empty_display_size = display_size
    elif obj.type == "MESH":
        if hasattr(obj, "display_type"):
            obj.display_type = "TEXTURED"
    obj.hide_viewport = False
    obj.show_name = True
    if hasattr(obj, "show_in_front"):
        obj.show_in_front = True
    obj.hide_render = True
    obj.lock_location[1] = True
    obj.lock_rotation[0] = True
    obj.lock_rotation[1] = True
    obj.lock_rotation[2] = True
    obj.lock_scale[1] = True


def _ensure_face_preview_material(name: str, image, tint=(1.0, 1.0, 1.0, 1.0), alpha_factor: float = 0.55):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    tex.location = (-720.0, 120.0)
    tex.image = image

    tint_node = nodes.new("ShaderNodeMixRGB")
    tint_node.location = (-480.0, 120.0)
    tint_node.blend_type = "MULTIPLY"
    tint_node.inputs["Fac"].default_value = 1.0
    tint_node.inputs["Color2"].default_value = tint

    emission = nodes.new("ShaderNodeEmission")
    emission.location = (-200.0, 120.0)
    emission.inputs["Strength"].default_value = 1.0

    transparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent.location = (-200.0, -80.0)

    alpha_math = nodes.new("ShaderNodeMath")
    alpha_math.location = (-480.0, -80.0)
    alpha_math.operation = "MULTIPLY"
    alpha_math.inputs[1].default_value = alpha_factor

    mix_shader = nodes.new("ShaderNodeMixShader")
    mix_shader.location = (40.0, 60.0)

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (260.0, 60.0)

    links.new(tex.outputs["Color"], tint_node.inputs["Color1"])
    links.new(tint_node.outputs["Color"], emission.inputs["Color"])
    links.new(tex.outputs["Alpha"], alpha_math.inputs[0])
    links.new(alpha_math.outputs["Value"], mix_shader.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix_shader.inputs[1])
    links.new(emission.outputs["Emission"], mix_shader.inputs[2])
    links.new(mix_shader.outputs["Shader"], out.inputs["Surface"])

    _set_alpha_blend_mode(material)
    if hasattr(material, "shadow_method"):
        try:
            material.shadow_method = "NONE"
        except Exception:
            pass
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = False
    return material


def _create_face_preview_plane_mesh(mesh_name: str):
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(
        [
            (-0.5, 0.0, -0.5),
            (0.5, 0.0, -0.5),
            (0.5, 0.0, 0.5),
            (-0.5, 0.0, 0.5),
        ],
        [],
        [(0, 1, 2, 3)],
    )
    mesh.update()
    return mesh


def _ensure_face_preview_plane_object(name: str, collection, image, label: str, tint=(1.0, 1.0, 1.0, 1.0)):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        if obj is not None:
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception:
                pass
        mesh = _create_face_preview_plane_mesh(f"{name}_Mesh")
        obj = bpy.data.objects.new(name, mesh)
    elif obj.data is None:
        obj.data = _create_face_preview_plane_mesh(f"{name}_Mesh")

    _link_object_to_collection(obj, collection)
    obj.name = name
    obj.hide_render = True
    obj.show_name = True
    obj.name = name

    material_name = f"{name}_PreviewMat"
    material = _ensure_face_preview_material(material_name, image, tint=tint)
    if len(obj.data.materials) == 0:
        obj.data.materials.append(material)
    else:
        obj.data.materials[0] = material
    for index in range(len(obj.data.materials) - 1, 0, -1):
        obj.data.materials.pop(index=index)
    obj["preview_label"] = label
    return obj


def _remove_control_object_with_data(obj):
    if obj is None:
        return
    data = getattr(obj, "data", None)
    materials = list(getattr(data, "materials", [])) if data is not None and hasattr(data, "materials") else []
    bpy.data.objects.remove(obj, do_unlink=True)
    if data is not None and getattr(data, "users", 0) == 0:
        try:
            bpy.data.meshes.remove(data)
        except Exception:
            pass
    for material in materials:
        if material is not None and material.users == 0:
            try:
                bpy.data.materials.remove(material)
            except Exception:
                pass


def _clear_driver_variables(driver):
    while driver.variables:
        driver.variables.remove(driver.variables[0])


def _add_transform_driver_var(driver, name: str, target_obj, transform_type: str):
    variable = driver.variables.new()
    variable.name = name
    variable.type = "TRANSFORMS"
    target = variable.targets[0]
    target.id = target_obj
    target.transform_type = transform_type
    target.transform_space = "LOCAL_SPACE"
    return variable


def _add_single_prop_driver_var(driver, name: str, target_id, data_path: str):
    variable = driver.variables.new()
    variable.name = name
    variable.type = "SINGLE_PROP"
    target = variable.targets[0]
    target.id = target_id
    target.data_path = data_path
    return variable


def _configure_face_mapping_drivers(mapping_node, controller, span_x: float, span_z: float):
    if mapping_node is None or controller is None:
        return

    location_socket = mapping_node.inputs.get("Location")
    scale_socket = mapping_node.inputs.get("Scale")
    if location_socket is None or scale_socket is None:
        return

    base_location = list(location_socket.default_value)
    base_scale = list(scale_socket.default_value)
    rest_location = controller.location.copy()
    rest_scale = controller.scale.copy()

    controller["base_loc_x"] = float(base_location[0])
    controller["base_loc_y"] = float(base_location[1])
    controller["base_scale_x"] = float(base_scale[0])
    controller["base_scale_y"] = float(base_scale[1])
    controller["rest_loc_x"] = float(rest_location.x)
    controller["rest_loc_z"] = float(rest_location.z)
    controller["rest_scale_x"] = float(rest_scale.x)
    controller["rest_scale_z"] = float(rest_scale.z)
    controller["span_x"] = float(max(span_x, 1.0e-6))
    controller["span_z"] = float(max(span_z, 1.0e-6))

    for socket, index, expression in (
        (location_socket, 0, "base_loc_x - ((loc_x - rest_loc_x) / span_x)"),
        (location_socket, 1, "base_loc_y - ((loc_z - rest_loc_z) / span_z)"),
        (scale_socket, 0, "base_scale_x * rest_scale_x / scale_x"),
        (scale_socket, 1, "base_scale_y * rest_scale_z / scale_z"),
    ):
        try:
            fcurve = socket.driver_add("default_value", index)
        except TypeError:
            continue
        driver = fcurve.driver
        driver.type = "SCRIPTED"
        _clear_driver_variables(driver)
        _add_transform_driver_var(driver, "loc_x", controller, "LOC_X")
        _add_transform_driver_var(driver, "loc_z", controller, "LOC_Z")
        _add_transform_driver_var(driver, "scale_x", controller, "SCALE_X")
        _add_transform_driver_var(driver, "scale_z", controller, "SCALE_Z")
        _add_single_prop_driver_var(driver, "base_loc_x", controller, '["base_loc_x"]')
        _add_single_prop_driver_var(driver, "base_loc_y", controller, '["base_loc_y"]')
        _add_single_prop_driver_var(driver, "base_scale_x", controller, '["base_scale_x"]')
        _add_single_prop_driver_var(driver, "base_scale_y", controller, '["base_scale_y"]')
        _add_single_prop_driver_var(driver, "rest_loc_x", controller, '["rest_loc_x"]')
        _add_single_prop_driver_var(driver, "rest_loc_z", controller, '["rest_loc_z"]')
        _add_single_prop_driver_var(driver, "rest_scale_x", controller, '["rest_scale_x"]')
        _add_single_prop_driver_var(driver, "rest_scale_z", controller, '["rest_scale_z"]')
        _add_single_prop_driver_var(driver, "span_x", controller, '["span_x"]')
        _add_single_prop_driver_var(driver, "span_z", controller, '["span_z"]')
        driver.expression = expression


def _remove_mapping_socket_drivers(socket):
    if socket is None or not hasattr(socket, "default_value"):
        return
    value = list(socket.default_value)
    for index in range(len(value)):
        try:
            socket.driver_remove("default_value", index)
        except TypeError:
            continue
    socket.default_value = value


def _apply_face_drag_mapping(material, remove_controls: bool = True):
    if material is None:
        return 0

    baked = 0
    for mapping_node in (_face_sdf_mapping_node(material), _face_cm_mapping_node(material)):
        if mapping_node is None:
            continue
        location_socket = mapping_node.inputs.get("Location")
        scale_socket = mapping_node.inputs.get("Scale")
        if location_socket is not None:
            _remove_mapping_socket_drivers(location_socket)
            baked += 1
        if scale_socket is not None:
            _remove_mapping_socket_drivers(scale_socket)

    if not remove_controls:
        return baked

    for key, fallback in (
        (FACE_TEX_CONTROL_SDF_KEY, "SDF_CTRL"),
        (FACE_TEX_CONTROL_CM_KEY, "CM_CTRL"),
        (FACE_TEX_CONTROL_ROOT_KEY, "CTRL_ROOT"),
    ):
        obj = _material_face_tex_control_object(material, key, fallback_suffix=fallback)
        if obj is not None:
            _remove_control_object_with_data(obj)
        if key in material:
            del material[key]
    return baked


def _ensure_face_drag_controls(settings: ENDFIELD_PG_Settings, obj, material):
    if obj is None or material is None:
        return None

    sdf_mapping = _ensure_face_sdf_mapping_controls(material)
    cm_mapping = _ensure_face_cm_mapping_controls(material)
    if sdf_mapping is None and cm_mapping is None:
        return None

    _apply_face_drag_mapping(material, remove_controls=True)

    collection = _ensure_face_tex_control_collection()
    root_name = _material_face_tex_control_name(material, "CTRL_ROOT")
    sdf_name = _material_face_tex_control_name(material, "SDF_CTRL")
    cm_name = _material_face_tex_control_name(material, "CM_CTRL")

    root = _get_or_create_empty(root_name, collection)
    sdf_image = next((getattr(node, "image", None) for node in _find_face_sdf_image_nodes(sdf_mapping.id_data) if getattr(node, "image", None) is not None), None) if sdf_mapping is not None else None
    cm_image = next((getattr(node, "image", None) for node in _find_face_cm_image_nodes(cm_mapping.id_data) if getattr(node, "image", None) is not None), None) if cm_mapping is not None else None
    sdf_ctrl = _ensure_face_preview_plane_object(sdf_name, collection, sdf_image, "SDF", tint=(0.82, 0.95, 1.0, 1.0)) if sdf_mapping is not None else _get_or_create_empty(sdf_name, collection)
    cm_ctrl = _ensure_face_preview_plane_object(cm_name, collection, cm_image, "CM", tint=(1.0, 0.88, 0.72, 1.0)) if cm_mapping is not None else _get_or_create_empty(cm_name, collection)
    _move_object_to_collection(root, collection, exclusive=True)
    _move_object_to_collection(sdf_ctrl, collection, exclusive=True)
    _move_object_to_collection(cm_ctrl, collection, exclusive=True)

    origin, basis_matrix, span_x, span_z = _face_control_basis(obj)
    display_size = max(span_x, span_z) * 0.25

    _clear_parent_keep_transform(root)
    _remove_child_of_constraints(root)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = max(display_size * 0.25, 0.01)
    root.show_name = False
    root.hide_render = True
    root.hide_viewport = False
    root.matrix_world = Matrix.Translation(origin) @ basis_matrix

    armature, head_bone = _resolve_head_bone(settings, obj)
    if armature is not None and head_bone is not None:
        root_world = root.matrix_world.copy()
        _replace_child_of_constraint(root, "Child Of", armature, head_bone.name, desired_world=root_world)

    _clear_parent_keep_transform(sdf_ctrl)
    _clear_parent_keep_transform(cm_ctrl)
    sdf_ctrl.parent = root
    cm_ctrl.parent = root
    sdf_ctrl.matrix_parent_inverse = root.matrix_world.inverted_safe()
    cm_ctrl.matrix_parent_inverse = root.matrix_world.inverted_safe()

    sdf_ctrl.location = Vector((-span_x * 0.35, 0.0, 0.0))
    cm_ctrl.location = Vector((span_x * 0.35, 0.0, 0.0))
    sdf_ctrl.rotation_euler = (0.0, 0.0, 0.0)
    cm_ctrl.rotation_euler = (0.0, 0.0, 0.0)

    if sdf_mapping is not None:
        sdf_scale = sdf_mapping.inputs["Scale"].default_value
        sdf_ctrl.scale = (
            max(1.0 / max(abs(float(sdf_scale[0])), 1.0e-4), 0.1),
            0.02,
            max(1.0 / max(abs(float(sdf_scale[1])), 1.0e-4), 0.1),
        )
        _configure_face_tex_control_object(sdf_ctrl, display_size)
        _configure_face_mapping_drivers(sdf_mapping, sdf_ctrl, span_x, span_z)
    else:
        sdf_ctrl.hide_viewport = True

    if cm_mapping is not None:
        cm_scale = cm_mapping.inputs["Scale"].default_value
        cm_ctrl.scale = (
            max(1.0 / max(abs(float(cm_scale[0])), 1.0e-4), 0.1),
            0.02,
            max(1.0 / max(abs(float(cm_scale[1])), 1.0e-4), 0.1),
        )
        _configure_face_tex_control_object(cm_ctrl, display_size)
        _configure_face_mapping_drivers(cm_mapping, cm_ctrl, span_x, span_z)
    else:
        cm_ctrl.hide_viewport = True

    material[FACE_TEX_CONTROL_ROOT_KEY] = root.name
    material[FACE_TEX_CONTROL_SDF_KEY] = sdf_ctrl.name
    material[FACE_TEX_CONTROL_CM_KEY] = cm_ctrl.name
    return {"root": root, "sdf": sdf_ctrl if sdf_mapping is not None else None, "cm": cm_ctrl if cm_mapping is not None else None}


def _selected_test_meshes(context):
    meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
    if meshes:
        return meshes
    if context.active_object and context.active_object.type == "MESH":
        return [context.active_object]
    return []


def _outline_anchor_index(obj):
    smooth_outline_names = set(GEOMETRY_NODE_PREFS["SMOOTH_OUTLINE"])
    for index, modifier in enumerate(obj.modifiers):
        if modifier.type == "SOLIDIFY":
            return index
        if modifier.type == "NODES" and modifier.node_group and modifier.node_group.name in smooth_outline_names:
            return index
    return None


def _move_modifier_before_outline(obj, modifier):
    if modifier is None:
        return
    current_index = obj.modifiers.find(modifier.name)
    if current_index < 0:
        return
    anchor_index = _outline_anchor_index(obj)
    if anchor_index is None:
        return
    if current_index > anchor_index:
        obj.modifiers.move(current_index, anchor_index)


def _move_modifier_after_outline(obj, modifier):
    if modifier is None:
        return
    current_index = obj.modifiers.find(modifier.name)
    if current_index < 0:
        return
    anchor_index = _outline_anchor_index(obj)
    if anchor_index is None:
        return
    target_index = min(anchor_index + 1, len(obj.modifiers) - 1)
    if current_index != target_index:
        obj.modifiers.move(current_index, target_index)


def _ensure_test_weld_modifier(obj, distance: float):
    modifier = obj.modifiers.get(TEST_WELD_MODIFIER_NAME)
    if modifier is None or modifier.type != "WELD":
        modifier = obj.modifiers.new(TEST_WELD_MODIFIER_NAME, "WELD")
    if hasattr(modifier, "merge_threshold"):
        modifier.merge_threshold = distance
    if hasattr(modifier, "mode"):
        try:
            modifier.mode = "ALL"
        except Exception:
            pass
    _move_modifier_before_outline(obj, modifier)
    return modifier


def _ensure_body_weld_modifier(obj):
    modifier = obj.modifiers.get(BODY_WELD_MODIFIER_NAME)
    if modifier is None or modifier.type != "WELD":
        modifier = obj.modifiers.new(BODY_WELD_MODIFIER_NAME, "WELD")
    modifier.name = BODY_WELD_MODIFIER_NAME
    if hasattr(modifier, "merge_threshold"):
        modifier.merge_threshold = BODY_WELD_DISTANCE
    if hasattr(modifier, "mode"):
        try:
            modifier.mode = "ALL"
        except Exception:
            pass
    if hasattr(modifier, "loose_edges"):
        modifier.loose_edges = False
    return modifier


def _ensure_test_merge_node_group():
    group = bpy.data.node_groups.get(TEST_GN_MERGE_GROUP_NAME)
    if group and group.bl_idname == "GeometryNodeTree":
        return group

    group = bpy.data.node_groups.new(TEST_GN_MERGE_GROUP_NAME, "GeometryNodeTree")
    interface = group.interface
    interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    interface.new_socket(name="Distance", in_out="INPUT", socket_type="NodeSocketFloat")
    interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = group.nodes
    links = group.links
    nodes.clear()

    group_input = nodes.new("NodeGroupInput")
    merge = nodes.new("GeometryNodeMergeByDistance")
    group_output = nodes.new("NodeGroupOutput")

    group_input.location = (-260.0, 0.0)
    merge.location = (0.0, 0.0)
    group_output.location = (240.0, 0.0)

    links.new(group_input.outputs["Geometry"], merge.inputs["Geometry"])
    if "Distance" in group_input.outputs and "Distance" in merge.inputs:
        links.new(group_input.outputs["Distance"], merge.inputs["Distance"])
    links.new(merge.outputs["Geometry"], group_output.inputs["Geometry"])
    return group


def _ensure_test_gn_merge_modifier(obj, distance: float):
    node_group = _ensure_test_merge_node_group()
    modifier = obj.modifiers.get(TEST_GN_MERGE_MODIFIER_NAME)
    if modifier is None or modifier.type != "NODES":
        modifier = obj.modifiers.new(TEST_GN_MERGE_MODIFIER_NAME, "NODES")
    modifier.node_group = node_group
    _set_modifier_input(modifier, "Distance", distance)
    _move_modifier_before_outline(obj, modifier)
    return modifier


def _ensure_eye_attribute_patch_node_group():
    group_name = "Endfield Eye Attribute Patch"
    group = bpy.data.node_groups.get(group_name)
    if not (group and group.bl_idname == "GeometryNodeTree"):
        group = bpy.data.node_groups.new(group_name, "GeometryNodeTree")
        interface = group.interface
        interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        nodes = group.nodes
        links = group.links
        nodes.clear()

        group_input = nodes.new("NodeGroupInput")
        store_eyes = nodes.new("GeometryNodeStoreNamedAttribute")
        group_output = nodes.new("NodeGroupOutput")

        group_input.location = (-260.0, 0.0)
        store_eyes.location = (0.0, 0.0)
        group_output.location = (240.0, 0.0)

        links.new(group_input.outputs["Geometry"], store_eyes.inputs["Geometry"])
        links.new(store_eyes.outputs["Geometry"], group_output.inputs["Geometry"])

    store_eyes = next((node for node in group.nodes if node.bl_idname == "GeometryNodeStoreNamedAttribute"), None)
    if store_eyes is None:
        return group

    store_eyes.data_type = "FLOAT"
    store_eyes.domain = "POINT"
    if "Name" in store_eyes.inputs:
        store_eyes.inputs["Name"].default_value = "Eyes"
    if "Selection" in store_eyes.inputs:
        store_eyes.inputs["Selection"].default_value = True
    if "Value" in store_eyes.inputs:
        store_eyes.inputs["Value"].default_value = 0.0

    return group


def _is_chen_source_image(image) -> bool:
    if image is None:
        return False
    name = image.name.lower()
    filepath = bpy.path.abspath(image.filepath).lower() if image.filepath else ""
    chen_markers = ("t_actor_chen", "m_actor_chen", "chen_")
    return any(marker in name or marker in filepath for marker in chen_markers)


def _cleanup_unused_source_assets(library_path: str):
    stamp = _library_stamp(library_path)

    for material in list(bpy.data.materials):
        if material.users != 0:
            continue
        if stamp and material.get(SOURCE_LIBRARY_STAMP_KEY) == stamp:
            bpy.data.materials.remove(material)

    for image in list(bpy.data.images):
        if image.users != 0:
            continue
        if _is_chen_source_image(image):
            bpy.data.images.remove(image)


@persistent
def _endfield_load_post(_dummy=None):
    compat_required = _requires_eevee_compat()
    try:
        _ensure_eye_attribute_patch_node_group()
        if compat_required:
            _ensure_eevee_shader_info_compat_group()
            _ensure_eevee_shader_info_lit_compat_group()
            _ensure_eevee_screenspace_info_compat_group()
    except Exception:
        pass
    try:
        _bootstrap_texture_states()
    except Exception:
        pass
    try:
        generated_scene = _scene_has_generated_endfield_scene()
        if compat_required and generated_scene and _scene_has_endfield_materials():
            _patch_all_endfield_materials_for_eevee_compat()
        settings = getattr(bpy.context.scene, "endfield_toon_settings", None)
        if settings is not None and generated_scene:
            _repair_current_endfield_scene(settings, ensure_environment=True)
    except Exception:
        pass


def _ensure_proxy_outline_material(settings: ENDFIELD_PG_Settings, source_obj, base_material=None, loaded_images=None, name_override: str = ""):
    loaded_images = dict(loaded_images or _load_images_from_settings(settings))
    material = _ensure_outline_material_instance(
        settings,
        source_obj,
        base_material,
        loaded_images,
        name_override=name_override or TEST_PROXY_MATERIAL_NAME,
    )
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = False
    if hasattr(material, "shadow_method"):
        try:
            material.shadow_method = "NONE"
        except Exception:
            pass
    return material


def _remove_object_and_data(obj):
    if obj is None:
        return
    mesh_data = obj.data if obj.type == "MESH" else None
    bpy.data.objects.remove(obj, do_unlink=True)
    if mesh_data and mesh_data.users == 0:
        bpy.data.meshes.remove(mesh_data)


def _prepare_proxy_modifiers(proxy_obj):
    keep_types = {"ARMATURE", "MIRROR", "LATTICE", "SUBSURF", "MESH_DEFORM", "SURFACE_DEFORM", "CORRECTIVE_SMOOTH"}
    for modifier in list(proxy_obj.modifiers):
        if modifier.type not in keep_types:
            proxy_obj.modifiers.remove(modifier)


def _ensure_proxy_material_slots(proxy_obj, settings: ENDFIELD_PG_Settings, source_obj):
    original_materials = [slot.material for slot in proxy_obj.material_slots]
    fallback_base = None
    if source_obj is not None and source_obj.active_material and not _is_outline_like(source_obj.active_material):
        fallback_base = source_obj.active_material
    if fallback_base is None:
        fallback_base = next((material for material in original_materials if material and not _is_outline_like(material)), None)
    if fallback_base is None:
        fallback_base = _ensure_template_material(settings)

    base_materials = []
    old_to_new = {}
    for index, material in enumerate(original_materials):
        if material is None:
            material = fallback_base
        if _is_outline_like(material):
            continue
        old_to_new[index] = len(base_materials)
        base_materials.append(material)

    if not base_materials:
        base_materials = [fallback_base]

    remapped_indices = []
    if hasattr(proxy_obj.data, "polygons"):
        remapped_indices = [old_to_new.get(polygon.material_index, 0) for polygon in proxy_obj.data.polygons]

    proxy_obj.data.materials.clear()
    outline_materials = []
    default_images = _load_images_from_settings(settings)

    for index, base_material in enumerate(base_materials):
        proxy_obj.data.materials.append(base_material)
        slot_images = dict(default_images)
        slot_images.update(_extract_loaded_images_from_material(base_material, settings.shader_type))
        outline_material = _ensure_proxy_outline_material(
            settings,
            proxy_obj,
            base_material,
            loaded_images=slot_images,
            name_override=f"{TEST_PROXY_MATERIAL_NAME}_{index:02d}_{base_material.name}",
        )
        outline_materials.append(outline_material)

    for outline_material in outline_materials:
        proxy_obj.data.materials.append(outline_material)

    if remapped_indices:
        for polygon, material_index in zip(proxy_obj.data.polygons, remapped_indices):
            polygon.material_index = material_index

    return len(base_materials)


def _ensure_proxy_solidify(proxy_obj, settings: ENDFIELD_PG_Settings, material_offset: int):
    modifier = proxy_obj.modifiers.get(settings.outline_modifier_name)
    if modifier is None or modifier.type != "SOLIDIFY":
        modifier = proxy_obj.modifiers.new(settings.outline_modifier_name, "SOLIDIFY")
    modifier.thickness = settings.outline_thickness
    if hasattr(modifier, "offset"):
        modifier.offset = 1.0
    if hasattr(modifier, "use_flip_normals"):
        modifier.use_flip_normals = True
    if hasattr(modifier, "use_rim_only"):
        modifier.use_rim_only = True
    if hasattr(modifier, "use_rim"):
        modifier.use_rim = True
    if hasattr(modifier, "material_offset"):
        modifier.material_offset = material_offset
    return modifier


def _create_or_update_outline_proxy(context, settings: ENDFIELD_PG_Settings, objects):
    if not objects:
        return None

    active_source = context.view_layer.objects.active if context.view_layer.objects.active in objects else objects[0]
    proxy_name = f"{active_source.name}{TEST_PROXY_SUFFIX}"
    existing_proxy = bpy.data.objects.get(proxy_name)
    if existing_proxy is not None:
        _remove_object_and_data(existing_proxy)

    view_layer = context.view_layer
    previous_active = view_layer.objects.active
    previous_selected = [obj for obj in context.selected_objects]

    try:
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

        duplicates = []
        active_duplicate = None
        for source in objects:
            duplicate = source.copy()
            duplicate.data = source.data.copy()
            duplicate.animation_data_clear()
            for collection in source.users_collection:
                _link_object_to_collection(duplicate, collection)
            duplicate.select_set(True)
            duplicates.append(duplicate)
            if source == active_source:
                active_duplicate = duplicate

        view_layer.objects.active = active_duplicate
        if len(duplicates) > 1 and bpy.ops.object.join.poll():
            bpy.ops.object.join()
            proxy_obj = view_layer.objects.active
        else:
            proxy_obj = active_duplicate

        proxy_obj.name = proxy_name
        proxy_obj.data.name = f"{proxy_name}_Mesh"
        _prepare_proxy_modifiers(proxy_obj)
        material_offset = _ensure_proxy_material_slots(proxy_obj, settings, active_source)
        _ensure_test_weld_modifier(proxy_obj, settings.test_weld_distance)
        _ensure_test_gn_merge_modifier(proxy_obj, settings.test_gn_merge_distance)
        _ensure_proxy_solidify(proxy_obj, settings, material_offset)
        return proxy_obj
    finally:
        bpy.ops.object.select_all(action="DESELECT")
        for selected in previous_selected:
            if selected.name in bpy.data.objects:
                bpy.data.objects[selected.name].select_set(True)
        if previous_active and previous_active.name in bpy.data.objects:
            view_layer.objects.active = bpy.data.objects[previous_active.name]


class ENDFIELD_OT_TestOutlineWeld(Operator):
    bl_idname = "endfield_toon.test_outline_weld"
    bl_label = "A：Weld描边"
    bl_description = "给选中网格添加非破坏性 Weld 修改器，用于描边缝隙修复"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(_selected_test_meshes(context))

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        objects = _selected_test_meshes(context)
        for obj in objects:
            _ensure_test_weld_modifier(obj, settings.test_weld_distance)
        self.report({"INFO"}, f"已为 {len(objects)} 个网格添加焊接修改器 ")
        return {"FINISHED"}


class ENDFIELD_OT_TestOutlineProxy(Operator):
    bl_idname = "endfield_toon.test_outline_proxy"
    bl_label = "B：Outline Proxy"
    bl_description = "基于当前选中网格创建非破坏性描边代理对象"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(_selected_test_meshes(context))

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        objects = _selected_test_meshes(context)
        proxy_obj = _create_or_update_outline_proxy(context, settings, objects)
        if proxy_obj is None:
            self.report({"WARNING"}, "未能创建描边代理")
            return {"CANCELLED"}
        self.report({"INFO"}, f"已创建描边代理：{proxy_obj.name}")
        return {"FINISHED"}


class ENDFIELD_OT_TestOutlineGNMerge(Operator):
    bl_idname = "endfield_toon.test_outline_gn_merge"
    bl_label = "C：GN合并描边"
    bl_description = "给选中网格添加 Geometry Nodes Merge by Distance 修改器"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(_selected_test_meshes(context))

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        objects = _selected_test_meshes(context)
        for obj in objects:
            _ensure_test_gn_merge_modifier(obj, settings.test_gn_merge_distance)
        self.report({"INFO"}, f"已为 {len(objects)} 个网格添加 GN 合并")
        return {"FINISHED"}


class ENDFIELD_OT_AutoFillTextures(Operator):
    bl_idname = "endfield_toon.autofill_textures"
    bl_label = "按_D自动补全贴图"
    bl_description = "根据_D贴图自动推断其它贴图"

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        if not settings.tex_d:
            self.report({"WARNING"}, "请先选择 _D.png")
            return {"CANCELLED"}

        filled = _autofill_missing_texture_paths(settings)
        self.report({"INFO"}, f"已自动补全 {filled} 个贴图槽")
        return {"FINISHED"}


class ENDFIELD_OT_AddFaceEyeMaterialSlot(Operator):
    bl_idname = "endfield_toon.add_face_eye_material_slot"
    bl_label = "添加眼透材质"
    bl_description = "为脸眼一体模式添加一个需要眼透的材质槽"
    bl_options = {"REGISTER", "UNDO"}

    target_group: EnumProperty(
        name="Target Group",
        items=[
            ("IRIS", "Iris", ""),
            ("BROW", "Brow", ""),
        ],
        default="IRIS",
    )

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        if self.target_group == "BROW":
            settings.face_brow_materials.add()
            self.report({"INFO"}, "已添加眉睫材质槽")
        else:
            settings.face_iris_materials.add()
            self.report({"INFO"}, "已添加瞳孔材质槽")
        return {"FINISHED"}


class ENDFIELD_OT_RemoveFaceEyeMaterialSlot(Operator):
    bl_idname = "endfield_toon.remove_face_eye_material_slot"
    bl_label = "移除眼透材质"
    bl_description = "移除一个脸眼一体模式的眼透材质槽"
    bl_options = {"REGISTER", "UNDO"}

    index: IntProperty(name="Index", default=-1, min=-1)
    target_group: EnumProperty(
        name="Target Group",
        items=[
            ("IRIS", "Iris", ""),
            ("BROW", "Brow", ""),
        ],
        default="IRIS",
    )

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        collection = settings.face_brow_materials if self.target_group == "BROW" else settings.face_iris_materials
        if 0 <= self.index < len(collection):
            collection.remove(self.index)
            self.report({"INFO"}, "已移除眼透材质槽")
            return {"FINISHED"}
        self.report({"WARNING"}, "没有可移除的眼透材质槽")
        return {"CANCELLED"}


class ENDFIELD_OT_AdjustFaceMapping(Operator):
    bl_idname = "endfield_toon.adjust_face_mapping"
    bl_label = "微调脸部贴图映射"
    bl_description = "按固定步长微调脸部 SDF/亮斑贴图的映射"
    bl_options = {"REGISTER", "UNDO"}

    target: EnumProperty(
        name="Target",
        items=[
            ("SDF", "SDF", ""),
            ("CM", "CM", ""),
        ],
    )
    socket_name: EnumProperty(
        name="Socket",
        items=[
            ("Location", "Location", ""),
            ("Scale", "Scale", ""),
        ],
    )
    axis: IntProperty(name="Axis", default=0, min=0, max=2)
    delta: FloatProperty(name="Delta", default=0.0)

    @classmethod
    def poll(cls, context):
        obj = context.object
        return bool(obj and obj.active_material)

    def execute(self, context):
        material = context.object.active_material if context.object else None
        mapping_node = _adjust_face_mapping(material, self.target, self.socket_name, self.axis, self.delta)
        if mapping_node is None:
            self.report({"WARNING"}, "当前材质没有可调的脸部贴图映射")
            return {"CANCELLED"}
        return {"FINISHED"}


class ENDFIELD_OT_EnableFaceDragControls(Operator):
    bl_idname = "endfield_toon.enable_face_drag_controls"
    bl_label = "启用拖拽校准"
    bl_description = "Create viewport drag controls for the face SDF and highlight textures"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        material = obj.active_material if obj else None
        return bool(obj and obj.type == "MESH" and _detect_shader_type_from_material(material) == "FACE")

    def execute(self, context):
        obj = context.object
        material = obj.active_material if obj else None
        controls = _ensure_face_drag_controls(context.scene.endfield_toon_settings, obj, material)
        if controls is None:
            self.report({"WARNING"}, "当前脸部材质没有可拖拽的 SDF / 亮斑贴图映射节点")
            return {"CANCELLED"}
        self.report({"INFO"}, "已创建拖拽校准控制器：在正视图中移动/缩放控制器即可直观调整")
        return {"FINISHED"}


class ENDFIELD_OT_ApplyFaceDragControls(Operator):
    bl_idname = "endfield_toon.apply_face_drag_controls"
    bl_label = "应用并移除拖拽校准"
    bl_description = "Bake the current drag result back into Mapping values and remove the temporary controls"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        material = obj.active_material if obj else None
        return bool(obj and obj.type == "MESH" and _detect_shader_type_from_material(material) == "FACE")

    def execute(self, context):
        material = context.object.active_material if context.object else None
        baked = _apply_face_drag_mapping(material, remove_controls=True)
        if not baked:
            self.report({"WARNING"}, "当前脸部材质没有正在使用的拖拽校准")
            return {"CANCELLED"}
        self.report({"INFO"}, "已将拖拽结果写回贴图映射，并移除控制器")
        return {"FINISHED"}


class ENDFIELD_OT_StartFaceUVCalibration(Operator):
    bl_idname = "endfield_toon.start_face_uv_calibration"
    bl_label = "开始 UV 校准"
    bl_description = "Show the face _D + SDF + M overlay calibration tool in the Image Editor"

    @classmethod
    def poll(cls, context):
        return bool(context.area and context.area.type == "IMAGE_EDITOR" and context.object and context.object.active_material and _detect_shader_type_from_material(context.object.active_material) == "FACE")

    def invoke(self, context, event):
        session = _start_face_uv_calibration_session(context)
        if session is None:
            self.report({"WARNING"}, "当前脸部材质缺少可用于 UV 校准的 _D 贴图或 Mapping 节点")
            return {"CANCELLED"}
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if not FACE_UV_CALIBRATION_STATE.get("running"):
            return {"FINISHED"}
        if context.area is None or context.area.type != "IMAGE_EDITOR":
            return {"PASS_THROUGH"}

        material = _face_uv_state_material()
        base_image = _face_uv_state_image("base_image_name")
        if material is None or base_image is None:
            _stop_face_uv_calibration_session()
            return {"CANCELLED"}

        settings = context.scene.endfield_toon_settings

        if event.value == "PRESS" and event.type in {"RET", "NUMPAD_ENTER", "SPACE"}:
            FACE_UV_CALIBRATION_STATE["dragging"] = False
            FACE_UV_CALIBRATION_STATE["drag_target"] = ""
            FACE_UV_CALIBRATION_STATE["drag_mode"] = ""
            _stop_face_uv_calibration_session()
            self.report({"INFO"}, "UV 校准已应用并退出")
            return {"FINISHED"}

        if event.type == "ESC" and event.value == "PRESS":
            if FACE_UV_CALIBRATION_STATE.get("dragging"):
                FACE_UV_CALIBRATION_STATE["dragging"] = False
                FACE_UV_CALIBRATION_STATE["drag_target"] = ""
                FACE_UV_CALIBRATION_STATE["drag_mode"] = ""
                return {"RUNNING_MODAL"}
            _stop_face_uv_calibration_session()
            return {"FINISHED"}

        if event.type == "RIGHTMOUSE" and event.value == "PRESS":
            if FACE_UV_CALIBRATION_STATE.get("dragging"):
                FACE_UV_CALIBRATION_STATE["dragging"] = False
                FACE_UV_CALIBRATION_STATE["drag_target"] = ""
                FACE_UV_CALIBRATION_STATE["drag_mode"] = ""
                return {"RUNNING_MODAL"}
            _stop_face_uv_calibration_session()
            return {"FINISHED"}

        if event.type == "LEFTMOUSE":
            if event.value == "PRESS":
                uv = _face_uv_event_to_uv(context, event, base_image)
                target = _pick_face_uv_target(settings, material, uv)
                if target is None:
                    return {"PASS_THROUGH"}
                FACE_UV_CALIBRATION_STATE["dragging"] = True
                FACE_UV_CALIBRATION_STATE["drag_target"] = target
                FACE_UV_CALIBRATION_STATE["drag_mode"] = "SCALE" if event.ctrl else "MOVE"
                FACE_UV_CALIBRATION_STATE["drag_start_uv"] = uv
                FACE_UV_CALIBRATION_STATE["drag_rect"] = _face_uv_current_rects(material).get(target) or (0.0, 0.0, 1.0, 1.0)
                settings.face_uv_active_target = target
                return {"RUNNING_MODAL"}
            if event.value == "RELEASE" and FACE_UV_CALIBRATION_STATE.get("dragging"):
                FACE_UV_CALIBRATION_STATE["dragging"] = False
                FACE_UV_CALIBRATION_STATE["drag_target"] = ""
                FACE_UV_CALIBRATION_STATE["drag_mode"] = ""
                return {"RUNNING_MODAL"}

        if event.type == "MOUSEMOVE" and FACE_UV_CALIBRATION_STATE.get("dragging"):
            uv = _face_uv_event_to_uv(context, event, base_image)
            _apply_face_uv_drag(
                material,
                FACE_UV_CALIBRATION_STATE.get("drag_target", settings.face_uv_active_target),
                FACE_UV_CALIBRATION_STATE.get("drag_mode", "MOVE"),
                FACE_UV_CALIBRATION_STATE.get("drag_rect"),
                FACE_UV_CALIBRATION_STATE.get("drag_start_uv"),
                uv,
            )
            return {"RUNNING_MODAL"}

        return {"PASS_THROUGH"}


class ENDFIELD_OT_StopFaceUVCalibration(Operator):
    bl_idname = "endfield_toon.stop_face_uv_calibration"
    bl_label = "停止 UV 校准"
    bl_description = "Hide the UV/Image Editor overlay calibration tool"

    def execute(self, context):
        if not FACE_UV_CALIBRATION_STATE.get("running"):
            self.report({"INFO"}, "当前没有正在运行的 UV 校准器")
            return {"CANCELLED"}
        _stop_face_uv_calibration_session()
        self.report({"INFO"}, "已关闭 UV/Image Editor 贴图校准器")
        return {"FINISHED"}


class ENDFIELD_OT_FixEeveeCompat(Operator):
    bl_idname = "endfield_toon.fix_eevee_compat"
    bl_label = "Fix Eevee 5.x"
    bl_description = "Replace broken Goo-only Shader Info placeholders with an Eevee-safe compatibility group"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        patched = _patch_all_endfield_materials_for_eevee_compat()
        if patched:
            self.report({"INFO"}, f"Patched {patched} Shader Info node(s) for Eevee 5.x compatibility.")
        else:
            self.report({"INFO"}, "No broken Shader Info placeholder nodes were found.")
        return {"FINISHED"}


class ENDFIELD_OT_SyncSceneEnvironment(Operator):
    bl_idname = "endfield_toon.sync_scene_environment"
    bl_label = "Sync Scene Settings"
    bl_description = "Sync World, Goo/Eevee render settings, and the Endfield sun rig from the preset"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        library = _effective_library_path(settings)
        if not library:
            self.report({"WARNING"}, "No preset library found.")
            return {"CANCELLED"}
        repaired, removed_lights = _repair_current_endfield_scene(settings, ensure_environment=True)
        extra_lights = [
            obj.name for obj in bpy.data.objects
            if obj.type == "LIGHT" and obj.name not in {SUN_LIGHT_NAME, SOURCE_SUN_LIGHT_NAME}
        ]
        message = "Scene environment and Goo/Eevee settings synced."
        if repaired:
            message += f" Repaired {repaired} legacy node-group links."
        if removed_lights:
            message += f" Removed default scene lights: {', '.join(removed_lights)}."
        if extra_lights:
            message += f" Extra scene lights detected: {', '.join(extra_lights[:3])}"
        self.report({"INFO"}, message)
        return {"FINISHED"}


class ENDFIELD_OT_OneClickGenerate(Operator):
    bl_idname = "endfield_toon.one_click_generate"
    bl_label = "一键生成"
    bl_description = "替换材质、Alpha、描边与终末地几何节点"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context):
        settings = context.scene.endfield_toon_settings
        if settings.apply_selected_objects:
            objects = [obj for obj in context.selected_objects if obj.type == "MESH"]
        else:
            objects = [context.active_object] if context.active_object and context.active_object.type == "MESH" else []

        if not objects:
            self.report({"WARNING"}, "没有可用网格对象")
            return {"CANCELLED"}

        autofilled = 0
        if settings.auto_fill_missing_maps and settings.tex_d:
            autofilled = _autofill_missing_texture_paths(settings)

        library = _effective_library_path(settings)
        if not library:
            self.report({"WARNING"}, "未找到终末地预设库，请先指定 .blend 预设")
            return {"CANCELLED"}

        face_validation_error = _validate_face_helper_targets(settings, objects)
        if face_validation_error:
            self.report({"WARNING"}, face_validation_error)
            return {"CANCELLED"}

        _force_clean_face_generation(settings, objects)
        _prime_preset_resources(settings)

        processed = 0
        replaced = 0
        geo_warning = False
        fallback_warning = False
        missing_shadow_maps = False

        if settings.migrate_source_environment:
            _migrate_scene_environment(settings, context.scene)
        if settings.auto_geometry_nodes and settings.shader_type in {"FACE", "BODY", "CLOTH", "HAIR", "PUPIL"}:
            _ensure_sun_rig(settings)
        _repair_legacy_scene_bindings(settings)
        _remove_default_endfield_scene_lights()

        for obj in objects:
            if settings.clear_custom_normals:
                _clear_custom_split_normals(context, obj)
            _set_shade_smooth(obj)
            _ensure_required_geometry_attributes(obj, settings.shader_type)

            slot_indices = _slot_indices_for_object(obj, settings)
            primary_material = None
            latest_loaded_images = {}
            source_material_map = {}

            for slot_index in slot_indices:
                while slot_index >= len(obj.material_slots):
                    obj.data.materials.append(None)

                source_material = obj.material_slots[slot_index].material
                source_material_key = source_material.as_pointer() if source_material is not None else None
                material_shader_type = _shader_type_for_object(settings, obj, source_material)
                template_material = _ensure_template_material(
                    settings,
                    shader_type=material_shader_type,
                    obj=obj,
                    source_material=source_material,
                )
                fallback_warning = fallback_warning or template_material.name.startswith("ENDFIELD_")
                new_material = template_material.copy()
                new_material.name = f"{template_material.name}_{obj.name}_{slot_index}"
                _patch_material_for_eevee_compat(new_material)
                if settings.shader_type == "FACE" and settings.face_integrated_eye_transparency and material_shader_type in {"PUPIL", "BROW"}:
                    loaded_images, role_presence = _apply_source_material_images(new_material, source_material, material_shader_type)
                else:
                    loaded_images, role_presence = _apply_textures(new_material, settings, shader_type=material_shader_type)
                if template_material.get(SOURCE_LIBRARY_STAMP_KEY):
                    new_material[SOURCE_LIBRARY_STAMP_KEY] = template_material.get(SOURCE_LIBRARY_STAMP_KEY)
                _sync_material_alpha_settings(new_material, template_material)
                if material_shader_type == "FACE":
                    _ensure_face_sdf_mapping_controls(new_material)
                    _ensure_face_cm_mapping_controls(new_material)
                obj.material_slots[slot_index].material = new_material
                if source_material_key is not None:
                    source_material_map.setdefault(source_material_key, []).append(new_material)

                if settings.shader_type == "FACE":
                    if material_shader_type == "FACE" or primary_material is None:
                        primary_material = new_material
                        latest_loaded_images = loaded_images
                else:
                    latest_loaded_images = loaded_images
                    primary_material = primary_material or new_material
                replaced += 1

                if material_shader_type in {"BODY", "CLOTH", "HAIR"}:
                    if (not role_presence.get("tex_n", False)) and (not role_presence.get("tex_p", False)):
                        missing_shadow_maps = True

            outline_material = None
            if settings.shader_type != "PUPIL":
                outline_material = _ensure_outline_material_instance(settings, obj, primary_material, latest_loaded_images)
                if settings.shader_type == "HAIR":
                    _ensure_hair_auxiliary_slots(obj, settings, outline_material)
                else:
                    _ensure_second_outline_slot(obj, outline_material, settings.force_slot2_outline)
            if settings.auto_geometry_nodes and settings.shader_type in {"FACE", "BODY", "CLOTH", "HAIR", "PUPIL"}:
                _remove_solidify_outline_modifiers(obj)
            elif settings.shader_type != "PUPIL":
                _ensure_outline_modifier(obj, settings)

            if settings.auto_geometry_nodes and primary_material is not None:
                geo_warning = _configure_common_geo_modifier(obj, library) or geo_warning

                if settings.shader_type == "FACE":
                    helper_rig = _ensure_head_helper_rig(settings, obj)
                    geo_warning = (
                        _configure_face_modifiers(
                            settings,
                            obj,
                            primary_material,
                            outline_material,
                            helper_rig,
                            library,
                            latest_loaded_images,
                            source_material_map,
                        )
                        or geo_warning
                    )
                elif settings.shader_type == "PUPIL":
                    geo_warning = _configure_eye_object_modifiers(
                        settings,
                        obj,
                        primary_material,
                        library,
                    ) or geo_warning
                elif settings.shader_type == "HAIR":
                    geo_warning = _configure_hair_modifiers(settings, obj, library) or geo_warning
                elif settings.shader_type == "BODY":
                    geo_warning = _configure_surface_outline_modifiers(
                        settings,
                        obj,
                        primary_material,
                        outline_material,
                        library,
                        latest_loaded_images,
                        include_time=True,
                    ) or geo_warning
                elif settings.shader_type == "CLOTH":
                    geo_warning = _configure_surface_outline_modifiers(
                        settings,
                        obj,
                        primary_material,
                        outline_material,
                        library,
                        latest_loaded_images,
                        include_time=True,
                    ) or geo_warning

            processed += 1

        if geo_warning:
            self.report({"WARNING"}, "部分几何节点组未找到，已跳过对应挂载")
        if fallback_warning:
            self.report({"WARNING"}, "部分预设材质未找到，已改用简化备用材质")
        if missing_shadow_maps:
            self.report({"WARNING"}, "缺少 _N/_P 贴图，阴影层次可能不足")

        _cleanup_unused_source_assets(library)
        self.report({"INFO"}, f"完成：{processed} 个网格，替换 {replaced} 个材质槽，自动补图 {autofilled} 个")
        return {"FINISHED"}


def _draw_face_mapping_row(layout, target: str, mapping_node, socket_name: str, index: int, label: str, delta: float):
    if mapping_node is None:
        return
    row = layout.row(align=True)
    minus = row.operator("endfield_toon.adjust_face_mapping", text="-")
    minus.target = target
    minus.socket_name = socket_name
    minus.axis = index
    minus.delta = -delta
    row.prop(mapping_node.inputs[socket_name], "default_value", index=index, text=label)
    plus = row.operator("endfield_toon.adjust_face_mapping", text="+")
    plus.target = target
    plus.socket_name = socket_name
    plus.axis = index
    plus.delta = delta


class ENDFIELD_PT_MainPanel(Panel):
    bl_label = "终末地卡渲材质转换"
    bl_idname = "ENDFIELD_PT_MAIN_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "终末地卡渲"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.endfield_toon_settings

        header = layout.box()
        header.label(text=f"插件版本: {'.'.join(str(v) for v in bl_info['version'])}", icon="INFO")
        header.prop(settings, "preset_library_path")
        library = _effective_library_path(settings)
        if library:
            header.label(text=f"当前预设: {os.path.basename(library)}", icon="CHECKMARK")
        else:
            header.label(text="未检测到终末地预设库", icon="ERROR")
        header.prop(settings, "shader_type")

        tex = layout.box()
        tex.label(text="贴图选择框（动态）")
        for slot in TEXTURE_SLOT_LAYOUT[settings.shader_type]:
            tex.prop(settings, slot.prop_id, text=slot.label)
        if settings.shader_type == "FACE":
            face_tex_box = tex.box()
            face_tex_box.label(text="面部专用贴图")
            face_tex_box.prop(settings, "face_sdf_tex", text="SDF 贴图")
            face_tex_box.prop(settings, "face_cm_tex", text="M 亮斑贴图")
            face_tex_box.label(text="留空时沿用预设中的默认 SDF / M", icon="INFO")
        tex.operator("endfield_toon.autofill_textures", icon="FILE_REFRESH")

        convert = layout.box()
        convert.label(text="一键生成")
        convert.prop(settings, "apply_selected_objects")
        convert.prop(settings, "apply_mode")
        convert.prop(settings, "auto_fill_missing_maps")
        convert.prop(settings, "clear_custom_normals")
        convert.prop(settings, "migrate_source_environment")
        convert.prop(settings, "auto_geometry_nodes")
        convert.operator("endfield_toon.fix_eevee_compat", icon="SHADING_RENDERED", text="Fix Eevee 5.x")
        convert.operator("endfield_toon.sync_scene_environment", icon="WORLD", text="Sync Scene Settings")
        if settings.shader_type == "FACE":
            convert.prop(settings, "create_helper_rig")
            head_box = convert.box()
            head_box.label(text="头部骨骼")
            head_box.prop(settings, "head_bone_armature", text="骨架")
            if settings.head_bone_armature and settings.head_bone_armature.type == "ARMATURE":
                head_box.prop_search(settings, "head_bone_name", settings.head_bone_armature.data, "bones", text="头部骨骼")
            else:
                head_box.prop(settings, "head_bone_name", text="头部骨骼")
                head_box.label(text="留空时自动识别常见 Head 骨骼", icon="INFO")
                head_box.label(text="自动识别失败将中止生成", icon="ERROR")
            convert.prop(settings, "face_integrated_eye_transparency")
            if settings.face_integrated_eye_transparency:
                face_eye_box = layout.box()
                face_eye_box.label(text="脸眼一体眼透材质")
                face_eye_box.label(text="这里只用于指定要处理的材质，并提取原始贴图", icon="INFO")
                face_eye_box.label(text="具体节点结构仍使用当前预设库中的瞳孔/眉睫材质", icon="INFO")
                face_eye_box.label(text="启用后会默认准备 2 个瞳孔槽 + 1 个眉睫槽", icon="INFO")

                iris_box = face_eye_box.box()
                iris_box.label(text="瞳孔栏")
                for index, item in enumerate(settings.face_iris_materials):
                    row = iris_box.row(align=True)
                    row.prop(item, "source_material", text=f"瞳孔材质 {index + 1}")
                    remove_op = row.operator("endfield_toon.remove_face_eye_material_slot", text="", icon="X")
                    remove_op.index = index
                    remove_op.target_group = "IRIS"
                add_iris = iris_box.operator("endfield_toon.add_face_eye_material_slot", icon="ADD")
                add_iris.target_group = "IRIS"

                brow_box = face_eye_box.box()
                brow_box.label(text="眉睫栏")
                for index, item in enumerate(settings.face_brow_materials):
                    row = brow_box.row(align=True)
                    row.prop(item, "source_material", text=f"眉睫材质 {index + 1}")
                    remove_op = row.operator("endfield_toon.remove_face_eye_material_slot", text="", icon="X")
                    remove_op.index = index
                    remove_op.target_group = "BROW"
                add_brow = brow_box.operator("endfield_toon.add_face_eye_material_slot", icon="ADD")
                add_brow.target_group = "BROW"
            else:
                convert.label(text="脸部模式默认不挂载眼透位移", icon="INFO")
        elif settings.shader_type == "PUPIL":
            convert.label(text="眼部模式会将眼透位移挂到当前对象", icon="INFO")
        convert.label(text="建议至少提供 _D + _N/_P 以获得稳定阴影", icon="INFO")

        if settings.shader_type != "PUPIL":
            outline = layout.box()
            outline.label(text="描边系统")
            outline.prop(settings, "force_slot2_outline")
            outline.prop(settings, "outline_thickness")
            outline.prop(settings, "outline_material_offset")
            outline.prop(settings, "outline_modifier_name")

            test_box = layout.box()
            test_box.label(text="优化断边（对当前选中网格）")
            test_box.prop(settings, "test_weld_distance")
            test_box.operator("endfield_toon.test_outline_weld", icon="AUTOMERGE_OFF")
            test_box.separator()
            test_box.operator("endfield_toon.test_outline_proxy", icon="DUPLICATE")
            test_box.separator()
            test_box.prop(settings, "test_gn_merge_distance")
            test_box.operator("endfield_toon.test_outline_gn_merge", icon="GEOMETRY_NODES")
        else:
            eye_box = layout.box()
            eye_box.label(text="眼部模式")
            eye_box.label(text="仅挂载眼透位移，不创建描边", icon="INFO")

        tweak = layout.box()
        tweak.label(text="精细调节（主要参数已隐藏）")
        active_material = context.object.active_material if context.object else None
        shader_node = _find_main_shader_node(active_material)
        shader_type = _detect_shader_type_from_material(active_material)

        if shader_node and shader_type in SAFE_TWEAKS:
            for label, socket_name in SAFE_TWEAKS[shader_type]:
                socket = shader_node.inputs.get(socket_name)
                if socket and hasattr(socket, "default_value"):
                    tweak.prop(socket, "default_value", text=label)
            if shader_type == "FACE":
                mapping_node = _ensure_face_sdf_mapping_controls(active_material)
                if mapping_node:
                    tweak.separator()
                    tweak.label(text="SDF贴图校准")
                    tweak.prop(mapping_node.inputs["Location"], "default_value", index=0, text="SDF位置 X")
                    tweak.prop(mapping_node.inputs["Location"], "default_value", index=1, text="SDF位置 Y")
                    tweak.prop(mapping_node.inputs["Scale"], "default_value", index=0, text="SDF尺寸 X")
                    tweak.prop(mapping_node.inputs["Scale"], "default_value", index=1, text="SDF尺寸 Y")
            if shader_type == "FACE":
                mapping_node = _ensure_face_sdf_mapping_controls(active_material)
                cm_mapping_node = _ensure_face_cm_mapping_controls(active_material)
                if mapping_node:
                    tweak.separator()
                    tweak.label(text="SDF微调按钮")
                    _draw_face_mapping_row(tweak, "SDF", mapping_node, "Location", 0, "SDF X (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "SDF", mapping_node, "Location", 1, "SDF Y (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "SDF", mapping_node, "Scale", 0, "SDF Scale X (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "SDF", mapping_node, "Scale", 1, "SDF Scale Y (±0.02)", 0.02)
                if cm_mapping_node:
                    tweak.separator()
                    tweak.label(text="亮斑贴图微调")
                    _draw_face_mapping_row(tweak, "CM", cm_mapping_node, "Location", 0, "亮斑 X (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "CM", cm_mapping_node, "Location", 1, "亮斑 Y (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "CM", cm_mapping_node, "Scale", 0, "亮斑 Scale X (±0.02)", 0.02)
                    _draw_face_mapping_row(tweak, "CM", cm_mapping_node, "Scale", 1, "亮斑 Scale Y (±0.02)", 0.02)
                drag_box = tweak.box()
                drag_box.label(text="拖拽式贴图校准")
                drag_box.label(text="启用后会在脸前创建 SDF / 亮斑 控制器", icon="INFO")
                drag_box.label(text="正视图中 G 移动 X/Z，S 缩放 X/Z 即可直观匹配", icon="INFO")
                drag_box.operator("endfield_toon.enable_face_drag_controls", icon="EMPTY_AXIS")
                drag_box.operator("endfield_toon.apply_face_drag_controls", icon="CHECKMARK")
                uv_box = tweak.box()
                uv_box.label(text="UV/Image Editor 叠层校准")
                uv_box.label(text="请在 UV/Image Editor 中打开“脸部贴图校准”面板", icon="INFO")
                uv_box.label(text="可单独开关 SDF / M，并直接在 _D 底图上拖动", icon="INFO")
        elif shader_type == "BROW":
            tweak.label(text="当前眉毛材质无需额外暴露调节项", icon="INFO")
        else:
            tweak.label(text="先套用终末地材质后，这里会显示安全调节项", icon="INFO")

        credits = layout.box()
        credits.label(text="致谢", icon="HEART")
        for line in ACKNOWLEDGEMENT_LINES:
            credits.label(text=line)

        layout.operator("endfield_toon.one_click_generate", icon="MATERIAL")


class ENDFIELD_PT_ImageCalibrationPanel(Panel):
    bl_label = "脸部贴图校准"
    bl_idname = "ENDFIELD_PT_IMAGE_CALIBRATION_PANEL"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "终末地卡渲"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.endfield_toon_settings
        obj = context.object
        material = obj.active_material if obj else None
        shader_type = _detect_shader_type_from_material(material)

        if shader_type != "FACE":
            layout.label(text="请先在 3D 视图中选中脸部材质", icon="INFO")
            return

        box = layout.box()
        box.label(text="UV/Image Editor 叠层校准")
        box.label(text="背景会显示 _D，叠加显示 SDF / M", icon="IMAGE_DATA")
        box.label(text="左键拖动: 平移  Ctrl+左键拖动: 缩放", icon="MOUSE_LMB")
        box.prop(settings, "face_uv_show_sdf")
        box.prop(settings, "face_uv_show_cm")
        box.prop(settings, "face_uv_active_target")
        row = box.row(align=True)
        row.operator("endfield_toon.start_face_uv_calibration", icon="UV")
        row.operator("endfield_toon.stop_face_uv_calibration", icon="PANEL_CLOSE")


classes = (
    ENDFIELD_PG_FaceEyeMaterialSlot,
    ENDFIELD_PG_Settings,
    ENDFIELD_OT_AutoFillTextures,
    ENDFIELD_OT_TestOutlineWeld,
    ENDFIELD_OT_TestOutlineProxy,
    ENDFIELD_OT_TestOutlineGNMerge,
    ENDFIELD_OT_AddFaceEyeMaterialSlot,
    ENDFIELD_OT_RemoveFaceEyeMaterialSlot,
    ENDFIELD_OT_AdjustFaceMapping,
    ENDFIELD_OT_EnableFaceDragControls,
    ENDFIELD_OT_ApplyFaceDragControls,
    ENDFIELD_OT_StartFaceUVCalibration,
    ENDFIELD_OT_StopFaceUVCalibration,
    ENDFIELD_OT_FixEeveeCompat,
    ENDFIELD_OT_SyncSceneEnvironment,
    ENDFIELD_OT_OneClickGenerate,
    ENDFIELD_PT_MainPanel,
    ENDFIELD_PT_ImageCalibrationPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.endfield_toon_settings = PointerProperty(type=ENDFIELD_PG_Settings)
    _endfield_load_post()
    if _endfield_load_post not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_endfield_load_post)


def unregister():
    _stop_face_uv_calibration_session()
    if _endfield_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_endfield_load_post)
    if hasattr(bpy.types.Scene, "endfield_toon_settings"):
        del bpy.types.Scene.endfield_toon_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

