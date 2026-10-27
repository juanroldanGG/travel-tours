# Makes one mp3 per stop from a tour file, using Microsoft's free neural voices (edge-tts).
# Usage: python make_audio.py tours/porto.es.json
# ponytail: free voice for testing; swap for ElevenLabs once the concept is proven.
import asyncio, json, pathlib, sys
import edge_tts

here = pathlib.Path(__file__).parent
tour = json.loads((here / sys.argv[1]).read_text(encoding="utf-8"))
out = here / tour["audio"]
out.mkdir(parents=True, exist_ok=True)

async def main():
    texts = [tour["intro"]] + [s["text"] for s in tour["stops"]]
    for i, text in enumerate(texts):
        f = out / f"{i}.mp3"
        if f.exists() and "--redo" not in sys.argv:
            continue  # already made; pass --redo after changing the text
        for attempt in range(5):  # the free voice service drops requests when busy
            try:
                await edge_tts.Communicate(text, tour["voice"]).save(str(f))
                break
            except Exception:
                if attempt == 4:
                    raise
                await asyncio.sleep(3 * (attempt + 1))
        print("made", i)

asyncio.run(main())
