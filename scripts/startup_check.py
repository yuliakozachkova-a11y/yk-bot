"""
Called once at bot startup on cloud.
1. Ensure data/preview_visuals/ exists with all AI infographics
   (regenerates if missing — bot.py imports this on startup)
2. Ensure DB schema exists
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot import db, drive

ROOT = Path(__file__).resolve().parent.parent
VISUALS = ROOT / "data" / "preview_visuals"
VISUALS.mkdir(parents=True, exist_ok=True)

# DB init
db.init_db()
drive.ensure_table()
print("✓ DB schema ready")

# Generate visuals if missing
required = [
    "checklist_value.png",
    "mind_map_depression.png",
    "tpl3_spotlight_book.png",
    "tpl4_stat_hero.png",
    "tpl5_diptych_poll.png",
    "tpl6_world_not_indebted.png",
    "tpl7_convenient_vs_valuable.png",
    "tpl8_saturday_choice.png",
    "tpl9_hero_journey.png",
    "tpl10_quiz_card.png",
    "test_welcome_19_25.png",
]
missing = [v for v in required if not (VISUALS / v).exists()]
if not missing:
    print(f"✓ All {len(required)} visuals exist")
else:
    print(f"⚙️  Generating {len(missing)} missing visuals...")
    try:
        # Import & run all generator scripts
        import subprocess
        for script in ["generate_preview_visuals.py", "generate_preview_visuals_v2.py",
                       "generate_more_visuals.py", "generate_hero_journey_visuals.py",
                       "gen_welcome_visual.py"]:
            script_path = ROOT / "scripts" / script
            if script_path.exists():
                subprocess.run(["python3", str(script_path)], check=False, cwd=str(ROOT))
        print("✓ Visuals regenerated")
    except Exception as e:
        print(f"⚠️  Generation error (non-fatal): {e}")

print("✓ Startup check complete")
