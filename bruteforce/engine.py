import asyncio, json

class Engine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.rules = {}
        if getattr(cfg, "rules", ""):
            with open(cfg.rules) as f:
                self.rules = json.load(f)
        self.proxies = [p.strip() for p in cfg.proxies.split(",") if p.strip()] if cfg.proxies else []

    def candidates(self):
        """Yield password candidates from a wordlist and/or a mask."""
        if self.cfg.wordlist:
            with open(self.cfg.wordlist, buffering=1024 * 1024) as f:
                for line in f:
                    yield line.rstrip("\n")
        if self.cfg.mask:
            from .perm import expand
            yield from expand(self.cfg.mask)

    async def handler(self, candidate, state):
        from .protocol import HTTPProtocol
        proto = HTTPProtocol(self.cfg.target, self.proxies, self.rules)
        ok, info = await proto.try_password(self.cfg.username, candidate)
        state["completed"] = state.get("completed", 0) + 1
        if ok:
            print("HIT:", candidate)
            with open(self.cfg.output, "a") as f:
                f.write(candidate + "\n")

    async def run_async(self):
        from .worker import WorkerPool
        from .state import load, save
        st = load(self.cfg.state)
        cands = list(self.candidates())
        start = st.get("completed", 0)
        cands = cands[start:]
        pool = WorkerPool(self.cfg.threads, lambda c: self.handler(c, st), self.cfg.rps)
        await pool.run(cands)
        save(self.cfg.state, {"target": self.cfg.target, "completed": st.get("completed",0), "total": len(cands)+start})
        print("done; checkpoint saved")

    def run(self):
        asyncio.run(self.run_async())
