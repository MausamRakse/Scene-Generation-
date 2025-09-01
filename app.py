import io
import math
import base64
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

import streamlit as st
from PIL import Image, ImageOps

# -----------------------------
# Utilities
# -----------------------------
POSITION_KEYWORDS = [
    "top-left", "top-right", "bottom-left", "bottom-right",
    "left", "right", "top", "bottom", "center", "middle"
]

ACTION_KEYWORDS = [
    "walking", "running", "sitting", "standing", "waving", "talking",
    "reading", "pointing", "dancing", "jumping", "holding", "looking",
]

def bytes_to_image(file_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(file_bytes)).convert("RGBA")

def image_to_bytes(img: Image.Image, fmt="PNG") -> bytes:
    buff = io.BytesIO()
    img.save(buff, format=fmt)
    return buff.getvalue()

def infer_position_from_prompt(prompt: str, W: int, H: int, index: int, total: int) -> Tuple[int, int]:
    """
    Maps natural language to coordinates. If no keyword found,
    space characters along the bottom.
    """
    p = (prompt or "").lower()
    pad = 40
    spots = {
        "top-left": (pad, pad),
        "top-right": (W - pad, pad),
        "bottom-left": (pad, H - pad),
        "bottom-right": (W - pad, H - pad),
        "left": (pad, H // 2),
        "right": (W - pad, H // 2),
        "top": (W // 2, pad),
        "bottom": (W // 2, H - pad),
        "center": (W // 2, H // 2),
        "middle": (W // 2, H // 2),
    }
    for key in POSITION_KEYWORDS:
        if key in p:
            return spots[key]

    # Fallback: evenly spaced along the bottom
    x = pad + (index + 1) * (W - 2 * pad) // (total + 1)
    y = H - pad
    return (x, y)

def extract_actions(prompt: str) -> List[str]:
    p = (prompt or "").lower()
    return [v for v in ACTION_KEYWORDS if v in p]

def scale_image(img: Image.Image, scale: float) -> Image.Image:
    w, h = img.size
    w2 = max(1, int(w * scale))
    h2 = max(1, int(h * scale))
    return img.resize((w2, h2), Image.LANCZOS)

def paste_rgba(base: Image.Image, overlay: Image.Image, x_center: int, y_bottom: int):
    """
    Pastes overlay so that its bottom center is at (x_center, y_bottom).
    """
    ow, oh = overlay.size
    x = int(x_center - ow / 2)
    y = int(y_bottom - oh)
    base.alpha_composite(overlay, (x, y))

def ensure_rgba(img: Image.Image) -> Image.Image:
    return img.convert("RGBA") if img.mode != "RGBA" else img

def flip_h_if_needed(img: Image.Image, flip_h: bool) -> Image.Image:
    return ImageOps.mirror(img) if flip_h else img

# -----------------------------
# Data Models
# -----------------------------
@dataclass
class Character:
    name: str
    raw_bytes: bytes
    x: int
    y: int
    scale: float = 0.50
    flip_h: bool = False
    actions: List[str] = field(default_factory=list)
    z: int = 0  # z-order, larger = on top

    def as_image(self) -> Image.Image:
        img = bytes_to_image(self.raw_bytes)
        img = flip_h_if_needed(img, self.flip_h)
        img = scale_image(img, self.scale)
        return ensure_rgba(img)

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(
    page_title="Phase 2 — Scene Generator (Streamlit)",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 Advanced Scene Generator and Documentation")
st.caption("Select a background, add multiple characters, and compose a scene from a natural-language prompt.")

# Sidebar — Prompt & Canvas Settings
with st.sidebar:
    st.header("📝 Scene Description (Prompt)")
    prompt = st.text_area(
        "Describe placements & actions",
        value="Two characters sitting at a table on the right; one is waving, the other is reading.",
        height=120,
        help="Use words like left/right/top/bottom/center and actions like waving, sitting, reading, etc."
    )

    st.header("🖼️ Background")
    bg_file = st.file_uploader(
        "Upload a background image",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=False
    )

    colW, colH = st.columns(2)
    with colW:
        canvas_w = st.number_input("Canvas width",  min_value=480, max_value=4096, value=1280, step=16)
    with colH:
        canvas_h = st.number_input("Canvas height", min_value=270,  max_value=4096, value=720,  step=16)

    st.markdown("---")
    st.subheader("⚙️ Placement")
    auto_place_clicked = st.button("🔁 Auto-place from prompt", use_container_width=True)

# Load background or blank
if bg_file is not None:
    bg_img = ensure_rgba(bytes_to_image(bg_file.read()).resize((canvas_w, canvas_h), Image.LANCZOS))
else:
    # blank dark background
    bg_img = Image.new("RGBA", (canvas_w, canvas_h), (10, 10, 10, 255))

# Session state for characters
if "characters" not in st.session_state:
    st.session_state.characters: List[Character] = []

# Right rail: Add/Manage Characters
st.subheader("👥 Characters")
c1, c2 = st.columns([2, 1])

with c1:
    char_files = st.file_uploader(
        "Upload character images (PNG with transparency recommended). You can upload multiple.",
        type=["png", "webp"],
        accept_multiple_files=True,
    )
    add_btn = st.button("➕ Add Uploaded Characters", type="primary")

    if add_btn and char_files:
        total_after = len(st.session_state.characters) + len(char_files)
        actions_from_prompt = extract_actions(prompt)
        for i, f in enumerate(char_files):
            bts = f.read()
            idx = len(st.session_state.characters) + i
            x, y = infer_position_from_prompt(prompt, canvas_w, canvas_h, idx, total_after)
            st.session_state.characters.append(
                Character(
                    name=f"Char {idx+1}",
                    raw_bytes=bts,
                    x=x,
                    y=y,
                    scale=0.50,
                    actions=actions_from_prompt,
                    z=idx
                )
            )
        st.success(f"Added {len(char_files)} character(s).")

with c2:
    st.markdown("**Tips**")
    st.write("- Use **left/right/top/bottom/center** words in the prompt.")
    st.write("- Use **waving, sitting, reading** etc. for actions.")
    st.write("- Fine-tune positions and scale below per character.")
    st.write("- Export the final composition as a PNG (bottom).")

# Auto-place if clicked
if auto_place_clicked and st.session_state.characters:
    actions_from_prompt = extract_actions(prompt)
    n = len(st.session_state.characters)
    for i, ch in enumerate(st.session_state.characters):
        x, y = infer_position_from_prompt(prompt, canvas_w, canvas_h, i, n)
        ch.x, ch.y = x, y
        ch.actions = actions_from_prompt
    st.toast("Re-positioned characters from prompt ✅", icon="✅")

# Per-character controls
st.markdown("---")
if not st.session_state.characters:
    st.info("No characters yet. Upload PNG characters in the section above.")
else:
    # Show controls in a grid
    cols = st.columns(2)
    for idx, ch in enumerate(sorted(st.session_state.characters, key=lambda c: c.z)):
        col = cols[idx % 2]
        with col:
            with st.expander(f"🎭 {ch.name} — controls", expanded=False):
                c1, c2 = st.columns([1, 1])
                with c1:
                    new_name = st.text_input("Name", value=ch.name, key=f"name_{idx}")
                    new_scale = st.slider("Scale (%)", min_value=20, max_value=200, value=int(ch.scale * 100), step=5, key=f"s_{idx}")
                    flip_h = st.checkbox("Flip horizontally", value=ch.flip_h, key=f"flip_{idx}")
                    z_up = st.button("Bring Forward ⬆️", key=f"zu_{idx}")
                with c2:
                    new_x = st.slider("X (center)", 0, canvas_w, value=int(ch.x), step=2, key=f"x_{idx}")
                    new_y = st.slider("Y (bottom)",  0, canvas_h, value=int(ch.y), step=2, key=f"y_{idx}")
                    z_down = st.button("Send Backward ⬇️", key=f"zd_{idx}")
                    remove = st.button("🗑️ Remove", key=f"rm_{idx}")

                # Apply edits
                ch.name = new_name
                ch.scale = new_scale / 100.0
                ch.flip_h = flip_h
                ch.x, ch.y = int(new_x), int(new_y)

                if z_up:
                    ch.z += 1
                if z_down:
                    ch.z -= 1
                if remove:
                    st.session_state.characters.remove(ch)
                    st.experimental_rerun()

                st.caption(f"Actions from prompt: {', '.join(ch.actions) if ch.actions else '—'}")

# Compose preview
st.markdown("---")
st.subheader("🧩 Scene Preview")

# Compose on a fresh canvas
composite = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
composite.alpha_composite(bg_img)

# Draw characters in z-order
for ch in sorted(st.session_state.characters, key=lambda c: c.z):
    sprite = ch.as_image()
    paste_rgba(composite, sprite, ch.x, ch.y)

st.image(composite, caption="Composed scene", use_container_width=True)

# Export buttons
colA, colB, colC = st.columns([1,1,1])

with colA:
    png_bytes = image_to_bytes(composite, "PNG")
    st.download_button(
        "⬇️ Download PNG",
        data=png_bytes,
        file_name="scene.png",
        mime="image/png",
        use_container_width=True
    )

with colB:
    # Export simple JSON (scene data)
    import json
    scene_dict = {
        "prompt": prompt,
        "canvas": {"width": canvas_w, "height": canvas_h},
        "characters": [
            {
                "name": ch.name,
                "x": ch.x,
                "y": ch.y,
                "scale": ch.scale,
                "flip_h": ch.flip_h,
                "z": ch.z,
                "actions": ch.actions
            } for ch in st.session_state.characters
        ]
    }
    st.download_button(
        "⬇️ Download Scene JSON",
        data=json.dumps(scene_dict, indent=2),
        file_name="scene.json",
        mime="application/json",
        use_container_width=True
    )

with colC:
    # Build a quick PDF documentation
    def build_pdf_doc() -> Optional[bytes]:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.utils import ImageReader
            from reportlab.pdfgen import canvas as pdfcanvas
            from reportlab.lib.units import cm

            buff = io.BytesIO()
            c = pdfcanvas.Canvas(buff, pagesize=A4)
            W, H = A4

            # Cover
            c.setFont("Helvetica-Bold", 18)
            c.drawString(2*cm, H-3*cm, "Phase 2 — Advanced Scene Generation")
            c.setFont("Helvetica", 11)
            c.drawString(2*cm, H-4*cm, "Author: YOUR NAME")
            c.drawString(2*cm, H-4.7*cm, "Contact: email@example.com")
            c.drawString(2*cm, H-5.4*cm, "Date: (auto)")
            c.showPage()

            # Prompt + composite
            c.setFont("Helvetica-Bold", 14)
            c.drawString(2*cm, H-2.5*cm, "Scene Prompt")
            c.setFont("Helvetica", 11)
            text_obj = c.beginText(2*cm, H-3.2*cm)
            for line in (prompt or "").splitlines() or ["(no prompt)"]:
                text_obj.textLine(line)
            c.drawText(text_obj)

            # Insert composite image
            comp_reader = ImageReader(io.BytesIO(image_to_bytes(composite, "PNG")))
            max_w = W - 4*cm
            max_h = H/2
            img_w, img_h = composite.size
            ratio = min(max_w / img_w, max_h / img_h)
            draw_w, draw_h = img_w * ratio, img_h * ratio
            c.drawImage(comp_reader, 2*cm, H-3.5*cm - draw_h - 1*cm, width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')
            c.showPage()

            # Character thumbnails + metadata
            c.setFont("Helvetica-Bold", 14)
            c.drawString(2*cm, H-2.5*cm, "Characters & Placement")
            y = H-3.2*cm
            for i, ch in enumerate(st.session_state.characters, 1):
                c.setFont("Helvetica-Bold", 12)
                c.drawString(2*cm, y, f"{i}. {ch.name}")
                y -= 0.6*cm
                meta = f"Pos: ({ch.x},{ch.y}), Scale: {int(ch.scale*100)}%, FlipH: {ch.flip_h}, Z: {ch.z}, Actions: {', '.join(ch.actions) if ch.actions else '—'}"
                c.setFont("Helvetica", 11)
                c.drawString(2*cm, y, meta)
                y -= 0.8*cm

                # add small thumbnail
                try:
                    thumb = ch.as_image().copy()
                    thumb.thumbnail((220, 220))
                    thumb_reader = ImageReader(io.BytesIO(image_to_bytes(thumb, "PNG")))
                    c.drawImage(thumb_reader, 2*cm, y-3*cm, width=5*cm, height=5*cm, mask='auto')
                except Exception:
                    pass

                y -= 3.6*cm
                if y < 4*cm:
                    c.showPage()
                    c.setFont("Helvetica-Bold", 14)
                    c.drawString(2*cm, H-2.5*cm, "Characters & Placement (cont.)")
                    y = H-3.2*cm

            # Reflections stub
            c.showPage()
            c.setFont("Helvetica-Bold", 14)
            c.drawString(2*cm, H-2.5*cm, "Reflections & Notes")
            c.setFont("Helvetica", 11)
            t = c.beginText(2*cm, H-3.2*cm)
            t.textLines([
                "What worked well:",
                "- Prompt-driven auto-placement gives a fast starting layout.",
                "- Manual sliders provide precise control for alignment.",
                "",
                "What could be improved:",
                "- Add drag-and-drop placement via a custom Streamlit component.",
                "- Integrate pose control (OpenPose/ControlNet) for action consistency.",
                "",
                "Future directions:",
                "- Timeline-based multi-scene storytelling.",
                "- Animation export (GIF/WebM)."
            ])
            c.drawText(t)

            c.save()
            return buff.getvalue()
        except Exception as e:
            st.error(f"PDF generation failed: {e}")
            return None

    pdf_bytes = build_pdf_doc()
    st.download_button(
        "⬇️ Download Documentation PDF",
        data=pdf_bytes if pdf_bytes else b"",
        file_name="documentation.pdf",
        mime="application/pdf",
        disabled=(pdf_bytes is None),
        use_container_width=True
    )

# Footnotes
with st.expander("ℹ️ How placement works"):
    st.write("""
- The app scans your prompt for **position keywords** (left/right/top/bottom/center, plus corners).
- If it finds one, all characters anchor to that area.
- If not, characters are evenly spaced along the bottom.
- The **bottom-center** of each character sprite is treated as the 'feet' contact point.
- Actions (like *waving*, *sitting*, *reading*) are detected and stored as tags (useful for docs).
""")

with st.expander("🧪 Ideas to score 'Ideal Submission' points"):
    st.write("""
- Add **drag-and-drop** via a Streamlit custom component (e.g., a lightweight Konva/Canvas bridge).
- Integrate **pose control** (OpenPose + ControlNet) to reflect actions visually in the sprite.
- Build a **timeline** to chain multiple scenes and export a storyboard.
- Add per-character **shadow** and **light direction** controls for realism.
""")
