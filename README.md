🎬 Advanced Scene Generator

An interactive Streamlit app that lets you build visual scenes by combining a background image with multiple character sprites.
The app supports prompt-driven auto-placement, per-character controls, and exports to PNG, JSON, and PDF documentation.

🚀 Features

Natural Language Placement

Detects keywords like left, right, top, bottom, center from your prompt.

Auto-places characters accordingly.

Action Extraction

Tags actions such as waving, sitting, reading, running, etc. from the prompt.

Stored as metadata in scene JSON and PDF.

Character Management

Upload multiple characters (transparent PNG/webp recommended).

Adjust position, scale, flip horizontally, z-order, and rename.

Background Support

Upload any background image or use a blank canvas.

Adjustable canvas size (default: 1280×720).

Exports

PNG (composed scene)

JSON (scene data structure)

PDF (documentation with scene preview, character details, reflections/notes)

📦 Installation

Clone this repository and install dependencies:

git clone https://github.com/your-username/scene-generator.git
cd scene-generator
pip install -r requirements.txt


Requirements (requirements.txt):

streamlit
pillow
reportlab

▶️ Usage

Run the Streamlit app:

streamlit run app.py


Then open the local URL shown in your terminal (default: http://localhost:8501).

🖼️ How It Works

Enter a scene prompt in the sidebar.

Example:
“Two characters sitting at a table on the right; one is waving, the other is reading.”

Upload a background image (optional).

Upload character images (transparent PNG recommended).

Click “Auto-place from prompt” or adjust positions manually with sliders.

Preview the scene in real-time.

Export to PNG, JSON, or PDF.

📂 Output Formats

PNG – Final rendered scene

JSON – Scene metadata, including character positions, scale, z-order, and actions

PDF – Documentation with:

Cover page

Scene prompt and preview

Character details & thumbnails

Reflections & notes section

🧩 Example Prompt
Three characters on the bottom:
- Left one is waving
- Middle one is reading
- Right one is sitting

🧪 Ideas for Extensions

Drag-and-drop character placement with a custom Streamlit component.

Pose control integration (OpenPose + ControlNet).

Timeline-based multi-scene storytelling.

Animation exports (GIF/WebM).

👨‍💻 Author

Your Name

Contact: mosuamrakse@gmail.com
