"""Run real SUMO on a labeled synthetic corridor; never manufacture outcomes."""

import hashlib
import json
import random
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from app.domain.models import Intervention, Scenario


def binary(name: str) -> str:
    import sumo

    return str(Path(sumo.__file__).parent / "bin" / name)


def command(args: list[str], timeout: int = 60):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"SUMO tool failed: {result.stderr[-1500:]}")
    return result


def make_demand(scenario: Scenario, seed: int, factor: float = 1) -> list[dict]:
    rng = random.Random(seed)
    vehicles = []
    routes = [("east", "main"), ("west", "main")]
    routes += [(f"cross{i}{direction}", "cross") for i in range(3) for direction in ("n", "s")]
    for interval in scenario.intervals():
        for route, axis in routes:
            rate = (interval.main_vph if axis == "main" else interval.cross_vph) * factor
            if rate == 0:
                continue
            clock = interval.begin_s + rng.expovariate(rate / 3600)
            while clock < interval.end_s:
                vehicles.append({"route": route, "axis": axis, "depart": round(clock, 3)})
                clock += rng.expovariate(rate / 3600)
    vehicles.sort(key=lambda v: (v["depart"], v["route"]))
    for i, vehicle in enumerate(vehicles):
        vehicle["id"] = f"{vehicle['axis']}_{i}"
    return vehicles


def network(directory: Path, intervention: Intervention) -> Path:
    nodes = ET.Element("nodes")
    for node, x, y, kind in [("W", -400, 0, "priority"), ("E", 1200, 0, "priority")]:
        ET.SubElement(nodes, "node", id=node, x=str(x), y=str(y), type=kind)
    for i in range(3):
        ET.SubElement(nodes, "node", id=f"j{i}", x=str(i * 400), y="0", type="traffic_light")
        for side, y in [("N", 300), ("S", -300)]:
            ET.SubElement(nodes, "node", id=f"{side}{i}", x=str(i * 400), y=str(y), type="priority")
    edges = ET.Element("edges")
    chain = ["W", "j0", "j1", "j2", "E"]
    for i in range(4):
        for direction, origin, dest in [
            ("e", chain[i], chain[i + 1]),
            ("w", chain[i + 1], chain[i]),
        ]:
            ET.SubElement(
                edges,
                "edge",
                id=f"{direction}{i}",
                **{
                    "from": origin,
                    "to": dest,
                    "numLanes": str(intervention.main_lanes),
                    "speed": "13.89",
                    "priority": "3",
                },
            )
    for i in range(3):
        for side in ("N", "S"):
            for direction, origin, dest in [
                ("in", f"{side}{i}", f"j{i}"),
                ("out", f"j{i}", f"{side}{i}"),
            ]:
                ET.SubElement(
                    edges,
                    "edge",
                    id=f"{side}{i}_{direction}",
                    **{
                        "from": origin,
                        "to": dest,
                        "numLanes": "1",
                        "speed": "11.11",
                        "priority": "1",
                    },
                )
    ET.ElementTree(nodes).write(directory / "nodes.xml")
    ET.ElementTree(edges).write(directory / "edges.xml")
    net = directory / "network.net.xml"
    command(
        [
            binary("netconvert"),
            "--node-files",
            str(directory / "nodes.xml"),
            "--edge-files",
            str(directory / "edges.xml"),
            "--output-file",
            str(net),
            "--no-turnarounds",
            "true",
            "--tls.default-type",
            "static",
        ]
    )
    tree = ET.parse(net)
    # Replace all generated phases using connection ownership, not assumed index order.
    for tl in tree.getroot().findall("tlLogic"):
        connections = [
            c for c in tree.getroot().findall("connection") if c.get("tl") == tl.get("id")
        ]
        length = max(int(c.get("linkIndex")) for c in connections) + 1
        main = ["r"] * length
        cross = ["r"] * length
        for c in connections:
            arterial = c.get("from").startswith(("e", "w"))
            # This first model has only straight trips. Turns receive permissive
            # green in their own axis phase; crossing streams never green together.
            state = "G" if c.get("dir") == "s" else "g"
            (main if arterial else cross)[int(c.get("linkIndex"))] = state
        for child in list(tl):
            tl.remove(child)
        share = intervention.main_green_share
        for duration, state in [
            (80 * share, "".join(main)),
            (3, "".join("y" if c in "Gg" else "r" for c in main)),
            (2, "r" * length),
            (80 * (1 - share), "".join(cross)),
            (3, "".join("y" if c in "Gg" else "r" for c in cross)),
            (2, "r" * length),
        ]:
            ET.SubElement(tl, "phase", duration=str(round(duration, 3)), state=state)
    tree.write(net)
    return net


class SumoSimulator:
    def version(self):
        return command([binary("sumo"), "--version"], timeout=20).stdout.splitlines()[0]

    def run(
        self,
        scenario: Scenario,
        intervention: Intervention,
        seed: int,
        factor: float = 1,
        playback: bool = False,
    ) -> dict:
        demand = make_demand(scenario, seed, factor)
        demand_hash = hashlib.sha256(json.dumps(demand, sort_keys=True).encode()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="bottleneck_") as temp:
            directory = Path(temp)
            net = network(directory, intervention)
            network_hash = hashlib.sha256(net.read_bytes()).hexdigest()
            root = ET.Element("routes")
            ET.SubElement(
                root, "vType", id="car", accel="2.6", decel="4.5", sigma="0.5", length="5"
            )
            ET.SubElement(root, "route", id="east", edges="e0 e1 e2 e3")
            ET.SubElement(root, "route", id="west", edges="w3 w2 w1 w0")
            for i in range(3):
                ET.SubElement(root, "route", id=f"cross{i}n", edges=f"S{i}_in N{i}_out")
                ET.SubElement(root, "route", id=f"cross{i}s", edges=f"N{i}_in S{i}_out")
            for v in demand:
                ET.SubElement(
                    root,
                    "vehicle",
                    id=v["id"],
                    route=v["route"],
                    type="car",
                    depart=str(v["depart"]),
                    departLane="best",
                    departSpeed="max",
                )
            ET.ElementTree(root).write(directory / "routes.xml")
            horizon = scenario.duration_s + 2400
            args = [
                binary("sumo"),
                "--net-file",
                str(net),
                "--route-files",
                str(directory / "routes.xml"),
                "--tripinfo-output",
                str(directory / "trips.xml"),
                "--tripinfo-output.write-unfinished",
                "true",
                "--summary-output",
                str(directory / "summary.xml"),
                "--queue-output",
                str(directory / "queue.xml"),
                "--queue-output.period",
                "10",
                "--seed",
                str(seed),
                "--end",
                str(horizon),
                "--time-to-teleport",
                "-1",
                "--no-step-log",
                "true",
                "--duration-log.disable",
                "true",
            ]
            if playback:
                args += ["--fcd-output", str(directory / "fcd.xml"), "--device.fcd.period", "10"]
            command(args)
            trips = ET.parse(directory / "trips.xml").getroot().findall("tripinfo")
            inserted = {t.get("id") for t in trips}
            uninserted = [v for v in demand if v["id"] not in inserted]
            delays = {
                t.get("id"): float(t.get("timeLoss")) + float(t.get("departDelay")) for t in trips
            }
            for v in uninserted:
                delays[v["id"]] = horizon - v["depart"]
            completed = sum(float(t.get("arrival")) >= 0 for t in trips)
            unfinished = len(trips) - completed

            def axis_delay(axis):
                vals = [delays[v["id"]] for v in demand if v["axis"] == axis]
                return sum(vals) / max(1, len(vals))

            total = sum(delays.values())
            # Lane queueing_length is metres; sum per timestamp, then retain maximum.
            queue_frames = []
            for frame in ET.parse(directory / "queue.xml").getroot():
                length = sum(float(l.get("queueing_length", "0")) for l in frame.iter("lane"))
                queue_frames.append(
                    {
                        "time_s": float(frame.get("timestep", frame.get("time", "0"))),
                        "queue_m": round(length, 2),
                    }
                )
            metrics = {
                "planned": len(demand),
                "completed": completed,
                "unfinished": unfinished,
                "uninserted": len(uninserted),
                "unserved": unfinished + len(uninserted),
                "total_delay_s": total,
                "mean_delay_s": total / max(1, len(demand)),
                "main_mean_delay_s": axis_delay("main"),
                "cross_mean_delay_s": axis_delay("cross"),
                "mean_trip_s": sum(float(t.get("duration")) for t in trips) / max(1, len(trips)),
                "departure_delay_s": sum(float(t.get("departDelay")) for t in trips)
                + sum(horizon - v["depart"] for v in uninserted),
                "max_queue": max((f["queue_m"] for f in queue_frames), default=0),
            }
            frames = []
            if playback:
                for f in ET.parse(directory / "fcd.xml").getroot():
                    vehicles = [
                        {
                            "id": v.get("id"),
                            "x": float(v.get("x")),
                            "y": float(v.get("y")),
                            "speed": float(v.get("speed")),
                        }
                        for v in f.findall("vehicle")
                    ]
                    frames.append({"time_s": float(f.get("time")), "vehicles": vehicles[:150]})
            summary = list(ET.parse(directory / "summary.xml").getroot())
            last = summary[-1].attrib if summary else {}
            if int(last.get("teleports", "0")):
                raise RuntimeError("Unexpected SUMO teleport invalidates comparison")
            return {
                "seed": seed,
                "demand_factor": factor,
                "demand_sha256": demand_hash,
                "network_sha256": network_hash,
                "horizon_s": horizon,
                "metrics": metrics,
                "queues": queue_frames,
                "playback": frames,
                "teleports": 0,
            }
