# Makes one mp3 per stop from tour.json, using Microsoft's free neural voices (edge-tts).
# ponytail: free voice for testing; swap for ElevenLabs once the concept is proven.
import asyncio, json, pathlib
import edge_tts

here = pathlib.Path(__file__).parent
tour = json.loads((here / "tour.json").read_text(encoding="utf-8"))
out = here / "audio"
out.mkdir(exist_ok=True)

async def main():
    texts = [tour["intro"]] + [s["text"] for s in tour["stops"]]
    for i, text in enumerate(texts):
        await edge_tts.Communicate(text, tour["voice"]).save(str(out / f"{i}.mp3"))
        print("made", i)

asyncio.run(main())
