#!/usr/bin/env python3
"""
build_pptx.py — Build Airlines Process Wiki PPTX from local BPMN PNGs.
One slide per subprocess: title slide + one BPMN diagram slide each.

Usage:
    pip3 install python-pptx --break-system-packages
    python3 scripts/build_pptx.py

Output: data/Airlines_Process_Diagrams.pptx
"""
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

SCRIPT_DIR = Path(__file__).parent
REPO_DIR   = SCRIPT_DIR.parent
PROCESSES  = REPO_DIR / "data" / "processes.json"
IMG_DIR    = REPO_DIR / "assets" / "img"
OUT_FILE   = REPO_DIR / "data" / "Airlines_Process_Diagrams.pptx"

# ── Palette ────────────────────────────────────────────────────────
NAVY   = RGBColor(0x00, 0x33, 0x66)
ORANGE = RGBColor(0xFF, 0x66, 0x00)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
GREY   = RGBColor(0x64, 0x74, 0x8B)
LIGHT  = RGBColor(0xF0, 0xF7, 0xFF)

# Slide dimensions — widescreen 16:9
SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H

blank_layout = prs.slide_layouts[6]  # blank

# ── Load process data ──────────────────────────────────────────────
with open(PROCESSES) as f:
    procs = json.load(f)["processes"]

complete = [p for p in procs if p["status"] == "Complete"]
print(f"Building PPTX: {len(complete)} completed subprocesses")

def add_rect(slide, l, t, w, h, fill_color=None, line_color=None):
    shape = slide.shapes.add_shape(1, l, t, w, h)  # MSO_SHAPE_TYPE.RECTANGLE
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape

def add_text(slide, text, l, t, w, h, size=12, bold=False,
             color=None, align=PP_ALIGN.LEFT, wrap=True):
    txb = slide.shapes.add_textbox(l, t, w, h)
    tf  = txb.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color or WHITE
    return txb

# ══════════════════════════════════════════════════════════════════
#  TITLE SLIDE
# ══════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(blank_layout)

# Background
add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill_color=NAVY)

# Orange accent bar
add_rect(slide, 0, Inches(3.2), SLIDE_W, Inches(0.06), fill_color=ORANGE)

# Title
add_text(slide, "Airlines Process Wiki",
         Inches(1), Inches(1.8), Inches(11.33), Inches(1.2),
         size=48, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Subtitle
add_text(slide, "L1 → L2 → L3 → L4 Business Process Diagrams",
         Inches(1), Inches(3.1), Inches(11.33), Inches(0.6),
         size=20, bold=False, color=RGBColor(0xAD, 0xD8, 0xE6),
         align=PP_ALIGN.CENTER)

# Stats
stats = f"{len(complete)} subprocesses  ·  {len(set(p['l1_domain'] for p in complete))} L1 domains  ·  BPMN process flows"
add_text(slide, stats,
         Inches(1), Inches(3.8), Inches(11.33), Inches(0.5),
         size=14, color=RGBColor(0x90, 0xA4, 0xAE),
         align=PP_ALIGN.CENTER)

# Footer
add_text(slide, "SAP Consulting · Airlines Vertical",
         Inches(1), Inches(6.8), Inches(11.33), Inches(0.4),
         size=11, color=RGBColor(0x78, 0x90, 0x9C),
         align=PP_ALIGN.CENTER)

print("  ✅ Title slide")

# ══════════════════════════════════════════════════════════════════
#  SECTION DIVIDER per L1 domain
# ══════════════════════════════════════════════════════════════════
current_l1 = None

for proc in complete:
    pid  = proc["id"]
    l1   = proc["l1_domain"]
    l2   = proc["l2_process"]
    l3   = proc["l3_name"]
    img  = IMG_DIR / f"{pid.lower()}.png"

    # L1 section divider slide
    if l1 != current_l1:
        current_l1 = l1
        slide = prs.slides.add_slide(blank_layout)

        # Dark background
        add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill_color=RGBColor(0x01, 0x1F, 0x3F))

        # Orange side bar
        add_rect(slide, 0, 0, Inches(0.12), SLIDE_H, fill_color=ORANGE)

        # L1 label
        add_text(slide, "L1 DOMAIN",
                 Inches(0.4), Inches(2.6), Inches(12), Inches(0.4),
                 size=13, bold=True,
                 color=ORANGE, align=PP_ALIGN.LEFT)

        # L1 name
        add_text(slide, l1,
                 Inches(0.4), Inches(3.0), Inches(12), Inches(1.2),
                 size=40, bold=True, color=WHITE, align=PP_ALIGN.LEFT)

        # Count
        domain_procs = [p for p in complete if p["l1_domain"] == l1]
        add_text(slide, f"{len(domain_procs)} subprocesses",
                 Inches(0.4), Inches(4.1), Inches(6), Inches(0.4),
                 size=14, color=RGBColor(0xAD, 0xD8, 0xE6), align=PP_ALIGN.LEFT)

        print(f"  ✅ Section: {l1}")

    # ── Process diagram slide ──────────────────────────────────────
    slide = prs.slides.add_slide(blank_layout)

    # White background
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill_color=WHITE)

    # Navy header bar
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.72), fill_color=NAVY)

    # Orange left accent
    add_rect(slide, 0, 0, Inches(0.06), Inches(0.72), fill_color=ORANGE)

    # PID badge
    add_rect(slide, Inches(0.15), Inches(0.12), Inches(0.85), Inches(0.46),
             fill_color=ORANGE)
    add_text(slide, pid,
             Inches(0.15), Inches(0.12), Inches(0.85), Inches(0.46),
             size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    # L3 name in header
    add_text(slide, l3,
             Inches(1.1), Inches(0.08), Inches(9.5), Inches(0.56),
             size=16, bold=True, color=WHITE, align=PP_ALIGN.LEFT)

    # L1 › L2 breadcrumb
    add_text(slide, f"{l1}  ›  {l2}",
             Inches(1.1), Inches(0.42), Inches(9.5), Inches(0.3),
             size=9, color=RGBColor(0xAD, 0xD8, 0xE6), align=PP_ALIGN.LEFT)

    # BPMN image or placeholder
    if img.exists():
        # Fill remaining slide area with the PNG
        slide.shapes.add_picture(
            str(img),
            Inches(0.1), Inches(0.78),
            width=Inches(13.13), height=Inches(6.62)
        )
    else:
        # Placeholder box
        add_rect(slide, Inches(0.1), Inches(0.78),
                 Inches(13.13), Inches(6.62),
                 fill_color=LIGHT, line_color=RGBColor(0xCC, 0xCC, 0xCC))
        add_text(slide, f"BPMN diagram not yet generated\n{pid.lower()}.png",
                 Inches(4), Inches(3.5), Inches(5), Inches(1),
                 size=12, color=GREY, align=PP_ALIGN.CENTER)

    print(f"  ✅ {pid}: {l3[:50]}")

# ── Save ───────────────────────────────────────────────────────────
prs.save(OUT_FILE)
print(f"\n✅ Saved: {OUT_FILE}")
print(f"   Slides: {len(prs.slides)}  ({len(complete)} diagrams + {len(set(p['l1_domain'] for p in complete))} section dividers + 1 title)")
