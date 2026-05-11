from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from segym.env import SettlementEthicsEnv
from segym.agents.factory import build_agent
from segym.logging import write_episode_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--agent", default="scripted_honest")
    parser.add_argument("--opponent", default="hybrid_threshold")
    parser.add_argument("--max-rounds", type=int, default=6)
    parser.add_argument("--out", default="runs/debug_episode")
    args = parser.parse_args()
    del args.opponent

    agent = build_agent(args.agent)
    env = SettlementEthicsEnv.from_path(
        args.scenario,
        config={"max_rounds": args.max_rounds, "model_id": agent.model_id, "condition": args.agent},
    )
    obs = env.reset(seed=0)
    done = False
    while not done:
        obs, _reward, done, _info = env.step(agent.act(obs))
    result = write_episode_result(args.out, env.scenario, env.result())
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
