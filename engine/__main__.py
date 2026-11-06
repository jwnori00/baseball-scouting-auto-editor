import argparse
import json
from .video import clip, probe

parser = argparse.ArgumentParser(description="Baseball scouting video engine")
sub = parser.add_subparsers(dest="command", required=True)
p = sub.add_parser("probe")
p.add_argument("input")
p = sub.add_parser("clip")
p.add_argument("input")
p.add_argument("output")
p.add_argument("--start", type=float, required=True)
p.add_argument("--duration", type=float, required=True)
args = parser.parse_args()
if args.command == "probe":
    print(json.dumps(probe(args.input), indent=2))
else:
    clip(args.input, args.output, args.start, args.duration)
