r"""Prepare the controlled 4-segment H3 chain trial with ONE workflow file.

Segment 1 is T2V. Segments 2-4 reuse the same art/comfy/chain4/h3-chain4.json:
before each queue the operator sets node 2 inputs.continue_from to the previous
clip copied into ComfyUI/output/chain4/seg<N-1>.mp4. first_frame_reference=true
stays on to reduce drift. No frame is edited or quantized by hand.

    python art/tests/chain4_prepare.py
    powershell -NoProfile -ExecutionPolicy Bypass -File \
      .opencode\skills\comfyui-runner\scripts\queue_prompt.ps1 \
      -Workflow art\comfy\chain4\h3-chain4.json \
      -PromptFile art\comfy\prompts\chain4\seg1.txt \
      -OutDir out\chain4\seg1 -TimeoutSec 5400
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "art" / "tests"))
from h3_prompt_rules import validate_prompt, video_style_contract  # noqa: E402

PROMPTS = ROOT / "art" / "comfy" / "prompts" / "chain4"
WF_DIR = ROOT / "art" / "comfy" / "chain4"
WORKFLOW = WF_DIR / "h3-chain4.json"
SOUND = ("overall_soundscape: A low aircraft engine hum and soft ventilation continue "
         "underneath, with a faint seat creak when the man shifts.\n\n"
         "non_diegetic_music: N/A")

BODIES = [
    # Segment 1: T2V. Establish one figure and the exact cabin contract.
    ("[Shot 1] Medium-wide eye-level shot of one continuous narrow-body passenger cabin "
     "aisle, two rows of 1+1 navy seats with slate headrests and armrests, exactly four "
     "oval windows on both walls, closed overhead bins, one small bone-white ceiling "
     "fixture visibly lit near the camera, and one thin muted-teal floor runner resting "
     "on the cabin floor. Exactly one relaxed adult man is seated in the near left "
     "window seat; he wears a near-black navy long-sleeve shirt and charcoal trousers, "
     "one solid black silhouette of short messy hair, two dot eyes and one short mouth "
     "line. Camera holds one framing with a very slow 1 percent push-in and a tiny "
     "handheld sway; the seat count, axis and viewpoint never change. "
     "At 00:00.000 he sits slumped, both hands resting on his knees with four gently "
     "curved fingers and one separated thumb. "
     "At 00:02.300 he slowly lifts his head and looks toward the far tail door, "
     "shoulders still, feet on the floor. "
     "At 00:04.600 he settles into one neutral upright pose, eyes open, hands still on "
     "his knees; the last second holds this pose with no motion blur or strong movement. "
     "Low-key night-horror light from the near ceiling fixture, cool slate walls clearly "
     "lighter than the navy seats, hard-edged flat shadow shapes and a heavy four-corner "
     "vignette. One continuous take, no cuts."),
    # Segment 2: first native continuation.
    ("[Shot 1] This segment continues directly from the end of the previous video with no "
     "cut. Medium-wide eye-level shot of the same continuous narrow-body passenger cabin "
     "aisle, two rows of 1+1 navy seats with slate headrests and armrests, exactly four "
     "oval windows on both walls, closed overhead bins, the same near bone-white ceiling "
     "fixture and the same thin muted-teal floor runner. The same single adult man stays "
     "seated in the near left window seat with the same face, same solid black messy-hair "
     "silhouette, same near-black navy long-sleeve shirt and charcoal trousers. Camera "
     "keeps the same scale and one-point perspective with a very slow 1 percent push-in "
     "and a barely visible handheld sway. "
     "At 00:00.000 he holds the seated pose at the seam, hands on his knees. "
     "At 00:02.300 he turns his head a few degrees toward the nearest oval window while "
     "his shoulders stay still. "
     "At 00:04.600 he faces forward again and becomes still, eyes open, both hands "
     "resting on his knees; the last second holds this pose with no motion blur or "
     "strong movement. Low-key night-horror light from the same near ceiling fixture, "
     "cool slate walls clearly lighter than the navy seats, hard-edged flat shadow "
     "shapes and the same heavy four-corner vignette. One continuous take, no cuts."),
    # Segment 3: second native continuation, small supported hand movement.
    ("[Shot 1] This segment continues directly from the end of the previous video with no "
     "cut. Medium-wide eye-level shot of the same narrow-body cabin, two rows of 1+1 navy "
     "seats with slate headrests and armrests, exactly four oval windows on both walls, "
     "closed overhead bins, the same near bone-white ceiling fixture and the same thin "
     "muted-teal floor runner. The same single adult man remains seated in the near left "
     "window seat, same face, same solid black messy-hair silhouette, same near-black "
     "navy long-sleeve shirt and charcoal trousers. Camera keeps the same framing and "
     "one-point perspective with a very slow 1 percent push-in and a tiny handheld sway. "
     "At 00:00.000 he holds the seated pose at the seam. "
     "At 00:02.300 his right hand lifts a few centimetres from his knee and settles on "
     "the slate armrest that supports it, fingers gently curved and thumb separated; "
     "his head stays level. "
     "At 00:04.600 both hands are still, one on the armrest and one on the knee, eyes "
     "open; the last second holds this pose with no motion blur or strong movement. "
     "Low-key night-horror light from the same near ceiling fixture, cool slate walls "
     "clearly lighter than the navy seats, hard-edged flat shadow shapes and the same "
     "heavy four-corner vignette. One continuous take, no cuts."),
    # Segment 4: third continuation, return to a stable neutral pose for comparison.
    ("[Shot 1] This segment continues directly from the end of the previous video with no "
     "cut. Medium-wide eye-level shot of the same narrow-body cabin, two rows of 1+1 navy "
     "seats with slate headrests and armrests, exactly four oval windows on both walls, "
     "closed overhead bins, the same near bone-white ceiling fixture and the same thin "
     "muted-teal floor runner. The same single adult man remains seated in the near left "
     "window seat, same face, same solid black messy-hair silhouette, same near-black "
     "navy long-sleeve shirt and charcoal trousers. Camera keeps the same scale, axis "
     "and one-point perspective with a very slow 1 percent push-in and a tiny handheld "
     "sway. "
     "At 00:00.000 he holds the seated pose at the seam. "
     "At 00:02.300 his right hand returns from the armrest to rest on his knee and his "
     "head inclines forward a few degrees, shoulders still. "
     "At 00:04.600 he returns to the same neutral upright pose as the opening segment, "
     "eyes open, both hands on his knees; the last second holds this pose with no motion "
     "blur or strong movement. Low-key night-horror light from the same near ceiling "
     "fixture, cool slate walls clearly lighter than the navy seats, hard-edged flat "
     "shadow shapes and the same heavy four-corner vignette. One continuous take, no "
     "cuts."),
]


def workflow() -> dict:
    """One API-format graph. continue_from is filled by the operator between runs."""
    return {
        "1": {
            "class_type": "FreeVideoMedia",
            "inputs": {
                "assets": "[]",
                "audio_use": "reference",
            },
        },
        "2": {
            "class_type": "FreeVideoGenerate",
            "inputs": {
                "text": "{{PROMPT}}",
                "width": 704,
                "height": 1280,
                "seconds": 5.0,
                "seed": 20262211,
                "two_pass": True,
                "base_steps": 8,
                "refine_steps": 3,
                "force_regenerate": True,
                "preview": False,
                "refine_from": "",
                "continue_from": "",
                "frames": 0,
                "first_frame_reference": True,
                "voice_reference": False,
                "hide_tail": False,
                "step_cache": "none",
                "upscale_factor": "2",
                "allow_empty_prompt": False,
                "upscale_from": "",
                "upscale_to": "",
                "media": ["1", 0],
            },
        },
    }


def main() -> None:
    PROMPTS.mkdir(parents=True, exist_ok=True)
    WF_DIR.mkdir(parents=True, exist_ok=True)
    contract = video_style_contract().strip()
    for index, body in enumerate(BODIES, 1):
        text = (f"integrated_multimodal_description: {contract} {body}\n\n{SOUND}\n")
        hard, warn = validate_prompt(text, out=str(PROMPTS / f"seg{index}.txt"))
        if hard or warn:
            raise SystemExit(f"seg{index} validation failed: hard={hard} warn={warn}")
        (PROMPTS / f"seg{index}.txt").write_text(text, encoding="utf-8")
        print(f"seg{index}: prompt={len(text)} chars")
    WORKFLOW.write_text(json.dumps(workflow(), ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"workflow -> {WORKFLOW.relative_to(ROOT)} (one file, continue_from edited per run)")


if __name__ == "__main__":
    main()
