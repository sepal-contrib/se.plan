"""Non-invasive memory diagnostics for the se.plan Solara process.

Purpose
-------
The ``solara`` process was OOM-killed twice on a 4 GiB box after its
anonymous heap reached ~2.5 GB (see ``journal-crash.txt.gz``). This module
adds lightweight, behaviour-preserving instrumentation to confirm *which*
mechanism drives the climb:

* a periodic one-line sample of resident memory and live-object counts
  (Solara kernels, pysepal sessions, ipywidgets), so the growth can be
  correlated with user actions;
* ``tracemalloc`` peak tracking so transient spikes that are freed between
  samples are still caught;
* an automatic detailed top-N allocation dump whenever RSS jumps sharply or
  crosses a danger threshold — this captures the smoking gun (e.g. a dense
  AOI import materialising full geometry client-side) without anyone having
  to be watching;
* an on-demand dump via ``SIGUSR1`` (``kill -USR1 <pid>`` inside the
  container).

Everything is guarded so a failure in a probe can never crash the app.

**Disabled by default**: the whole thing (including ``probe()``) is a no-op
unless ``SEPLAN_MEM_DIAG=1`` is set in the environment (e.g. via ``.env``).

Configuration (environment variables)
-------------------------------------
====================================  =========  ======================================
Variable                              Default    Meaning
====================================  =========  ======================================
``SEPLAN_MEM_DIAG``                   ``0``      master switch — set ``1`` to enable
``SEPLAN_MEM_INTERVAL``               ``30``     seconds between periodic samples
``SEPLAN_TRACEMALLOC``                ``1``      enable ``tracemalloc`` (small overhead)
``SEPLAN_TRACEMALLOC_FRAMES``         ``10``     stack depth kept per allocation
``SEPLAN_MEM_JUMP_MB``                ``150``    RSS jump (MB) that triggers a dump
``SEPLAN_MEM_DANGER_MB``              ``1500``   RSS (MB) above which we WARN + dump
``SEPLAN_MEM_TOP``                    ``30``     allocations listed in a detailed dump
``SEPLAN_MEM_LOG``                    *(auto)*   log file path override
====================================  =========  ======================================

Output goes to ``~/module_results/se.plan/mem_diagnostics.log`` (rotating)
*and* to the ``SEPLAN`` logger (stdout / journald), prefixed ``MEMDIAG`` for
easy grepping.
"""

from __future__ import annotations

import logging
import os
import threading
import tracemalloc
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

logger = logging.getLogger("SEPLAN")

# ---------------------------------------------------------------------------
# module-global state (one diagnostics thread per process)
# ---------------------------------------------------------------------------
_started = False
_enabled = False  # set True only when SEPLAN_MEM_DIAG=1 (opt-in); gates probe()
_lock = threading.Lock()
_wake = threading.Event()
_dump_requested = False
_diag_logger: Optional[logging.Logger] = None
_proc = None  # cached psutil.Process if available

# Registry references resolved ONCE in the main thread at start-up. The hot
# loop must not import solara/pysepal/ipywidgets itself: cold-importing them
# from the daemon thread while tracemalloc is active is pathologically slow
# (every allocation during import gets traced), which would stall sampling.
_solara_contexts = None  # solara.server.kernel_context.contexts (dict)
_pysepal_sm = None  # the SessionManager class (live dict is on its singleton)
_ipw_instances = None  # ipywidgets.widgets.widget._instances (dict)


def _env_flag(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() not in ("0", "false", "no", "")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _log_path() -> Path:
    """Resolve the diagnostics log file path, falling back gracefully."""
    override = os.environ.get("SEPLAN_MEM_LOG")
    if override:
        return Path(override).expanduser()
    try:
        from component.parameter.directory import result_dir

        return Path(result_dir) / "mem_diagnostics.log"
    except Exception:
        return Path(
            "~", "module_results", "se.plan", "mem_diagnostics.log"
        ).expanduser()


def _build_diag_logger() -> logging.Logger:
    """Dedicated rotating-file logger so the samples survive a restart."""
    diag = logging.getLogger("SEPLAN.memdiag")
    diag.setLevel(logging.INFO)
    diag.propagate = False  # don't double-print through the root SEPLAN logger
    if not diag.handlers:
        try:
            path = _log_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
            )
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            )
            diag.addHandler(handler)
            logger.info("MEMDIAG writing to %s", path)
        except Exception as e:  # pragma: no cover - filesystem dependent
            logger.warning("MEMDIAG could not open log file: %s", e)
    return diag


def _emit(msg: str, level: int = logging.INFO) -> None:
    """Send a line to both the dedicated file and stdout/journald."""
    if _diag_logger is not None:
        _diag_logger.log(level, msg)
    logger.log(level, "MEMDIAG %s", msg)


# ---------------------------------------------------------------------------
# metric collectors (each fully guarded; -1 means "could not read")
# ---------------------------------------------------------------------------
def _rss_mb() -> float:
    """Resident set size in MB via psutil, /proc, then getrusage."""
    global _proc
    try:
        import psutil

        if _proc is None:
            _proc = psutil.Process()
        return _proc.memory_info().rss / 1024 / 1024
    except Exception:
        pass
    try:
        for line in open("/proc/self/status"):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024  # value is in kB
    except Exception:
        pass
    try:
        import resource

        # ru_maxrss is kB on Linux (high-water mark, not current)
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return -1.0


def _vms_mb() -> float:
    try:
        import psutil

        global _proc
        if _proc is None:
            _proc = psutil.Process()
        return _proc.memory_info().vms / 1024 / 1024
    except Exception:
        return -1.0


def _resolve_registries() -> None:
    """Resolve live-object registries once, in the main thread, at start-up.

    By the time this runs (from ``solara_app.py`` after ``setup_solara_server``)
    solara, pysepal and ipywidgets are already imported, so this is cheap; it
    just caches the dict/class objects the hot loop counts.
    """
    global _solara_contexts, _pysepal_sm, _ipw_instances
    try:
        from solara.server import kernel_context

        _solara_contexts = kernel_context.contexts
    except Exception as e:
        logger.warning("MEMDIAG could not resolve solara contexts: %s", e)
    try:
        from pysepal.solara.session_manager import SessionManager

        _pysepal_sm = SessionManager
    except Exception as e:
        logger.warning("MEMDIAG could not resolve SessionManager: %s", e)
    try:
        from ipywidgets.widgets import widget as _w

        # module-level backing dict (the non-deprecated registry in ipywidgets 8.1)
        _ipw_instances = _w._instances
    except Exception as e:
        logger.warning("MEMDIAG could not resolve ipywidgets registry: %s", e)


def _count_solara_kernels() -> int:
    return len(_solara_contexts) if _solara_contexts is not None else -1


def _count_pysepal_sessions() -> int:
    # The live dict is the instance attr on the singleton (set in __init__);
    # the class attr is a stale empty {} once initialised. Read the instance,
    # falling back to the class attr before the singleton exists.
    sm = _pysepal_sm
    if sm is None:
        return -1
    try:
        inst = getattr(sm, "_instance", None)
        sessions = getattr(inst, "_sessions", None) if inst is not None else None
        if sessions is None:
            sessions = getattr(sm, "_sessions", None)
        return len(sessions) if sessions is not None else -1
    except Exception:
        return -1


def _count_ipywidgets() -> int:
    return len(_ipw_instances) if _ipw_instances is not None else -1


# ---------------------------------------------------------------------------
# detailed tracemalloc dump
# ---------------------------------------------------------------------------
def _dump_top(reason: str, rss: float) -> None:
    """Write the top allocators (by line, plus the single biggest traceback)."""
    if not tracemalloc.is_tracing():
        _emit(f"SNAPSHOT skipped (tracemalloc off) reason={reason} rss={rss:.0f}MB")
        return
    top = _env_int("SEPLAN_MEM_TOP", 30)
    try:
        snapshot = tracemalloc.take_snapshot()
    except Exception as e:
        _emit(f"SNAPSHOT failed: {e}", logging.WARNING)
        return

    lines = [f"==== SNAPSHOT reason={reason} rss={rss:.0f}MB top={top} ===="]
    for i, stat in enumerate(snapshot.statistics("lineno")[:top], 1):
        frame = stat.traceback[0]
        lines.append(
            f"#{i:>2} {stat.size / 1024 / 1024:8.2f} MB  "
            f"{stat.count:>7} blocks  {frame.filename}:{frame.lineno}"
        )

    # full call chain of the single biggest allocation site — this is what
    # reveals e.g. import_aoi_dialog -> get_ipygeojson -> .gdf -> _load_gdf
    big = snapshot.statistics("traceback")
    if big:
        lines.append("---- biggest allocation traceback ----")
        lines.append(f"  ({big[0].size / 1024 / 1024:.2f} MB, {big[0].count} blocks)")
        lines.extend("  " + ln for ln in big[0].traceback.format())
    _emit("\n".join(lines))


# ---------------------------------------------------------------------------
# the sampling loop
# ---------------------------------------------------------------------------
def _loop(interval: int, jump_mb: int, danger_mb: int) -> None:
    global _dump_requested
    last_rss = _rss_mb()
    # high-water band so the long climb to the OOM also gets snapshots
    next_band = ((int(last_rss) // 500) + 1) * 500

    _emit(f"started interval={interval}s rss={last_rss:.0f}MB")

    while True:
        # wakes early on SIGUSR1 (handler sets the event), else ticks on timeout
        _wake.wait(timeout=interval)
        _wake.clear()

        rss = _rss_mb()
        tm_cur = tm_peak = -1.0
        if tracemalloc.is_tracing():
            try:
                cur, peak = tracemalloc.get_traced_memory()
                tm_cur, tm_peak = cur / 1024 / 1024, peak / 1024 / 1024
                tracemalloc.reset_peak()  # so peak is per-interval, catches spikes
            except Exception:
                pass

        delta = rss - last_rss if (rss >= 0 and last_rss >= 0) else 0.0
        level = logging.WARNING if (danger_mb and rss >= danger_mb) else logging.INFO
        _emit(
            f"rss={rss:.0f}MB d={delta:+.0f}MB vms={_vms_mb():.0f}MB "
            f"tm_cur={tm_cur:.0f}MB tm_peak={tm_peak:.0f}MB "
            f"kernels={_count_solara_kernels()} "
            f"sessions={_count_pysepal_sessions()} widgets={_count_ipywidgets()}",
            level,
        )

        # automatic detailed dumps -------------------------------------------------
        if _dump_requested:
            _dump_requested = False
            _dump_top("SIGUSR1", rss)
        if jump_mb and delta >= jump_mb:
            _dump_top(f"RSS_JUMP {delta:+.0f}MB", rss)
        if danger_mb and rss >= danger_mb:
            _dump_top("DANGER", rss)
        elif rss >= next_band:
            _dump_top(f"BAND_{next_band}MB", rss)
            next_band += 500

        if rss >= 0:
            last_rss = rss


def _handle_sigusr1(signum, frame) -> None:  # pragma: no cover - signal path
    global _dump_requested
    _dump_requested = True
    _wake.set()


# ---------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------
def start_memory_diagnostics() -> None:
    """Start the background memory-diagnostics thread (idempotent, safe).

    Call once at process start (from ``solara_app.py``). Honours the
    ``SEPLAN_MEM_*`` environment variables documented in the module docstring.
    **Disabled by default** — a no-op unless ``SEPLAN_MEM_DIAG=1`` is set (or if
    already started).
    """
    global _started, _enabled, _diag_logger
    with _lock:
        if _started:
            return
        if not _env_flag("SEPLAN_MEM_DIAG", "0"):
            return
        _started = True
        _enabled = True

    _diag_logger = _build_diag_logger()

    # Resolve registries in the main thread BEFORE tracemalloc starts.
    _resolve_registries()

    if _env_flag("SEPLAN_TRACEMALLOC"):
        try:
            if not tracemalloc.is_tracing():
                tracemalloc.start(_env_int("SEPLAN_TRACEMALLOC_FRAMES", 10))
            logger.info(
                "MEMDIAG tracemalloc on (frames=%s)",
                _env_int("SEPLAN_TRACEMALLOC_FRAMES", 10),
            )
        except Exception as e:
            logger.warning("MEMDIAG tracemalloc failed to start: %s", e)

    # SIGUSR1 -> on-demand dump (must register on the main thread)
    try:
        import signal

        signal.signal(signal.SIGUSR1, _handle_sigusr1)
        logger.info("MEMDIAG SIGUSR1 dump handler installed (kill -USR1 <pid>)")
    except Exception as e:  # not the main thread / unsupported platform
        logger.warning("MEMDIAG could not install SIGUSR1 handler: %s", e)

    interval = _env_int("SEPLAN_MEM_INTERVAL", 30)
    jump_mb = _env_int("SEPLAN_MEM_JUMP_MB", 150)
    danger_mb = _env_int("SEPLAN_MEM_DANGER_MB", 1500)

    thread = threading.Thread(
        target=_loop,
        args=(interval, jump_mb, danger_mb),
        name="seplan-memdiag",
        daemon=True,
    )
    thread.start()
    logger.info("MEMDIAG sampler thread started (interval=%ss)", interval)


# ---------------------------------------------------------------------------
# targeted probe — wrap a suspect block to log RSS / peak before & after
# ---------------------------------------------------------------------------
class probe:
    """Context manager logging RSS and tracemalloc peak around a block.

    Use it to get an unambiguous per-operation delta on a suspect path, e.g.::

        with probe("aoi-import-extract-geometry"):
            feature_collection = self.model.gdf.__geo_interface__

    Cheap and exception-safe; logs even if the block raises.
    """

    def __init__(self, label: str):
        self.label = label
        self._rss0 = -1.0

    def __enter__(self) -> "probe":
        """Record RSS and reset the tracemalloc peak before the block runs."""
        if not _enabled:  # diagnostics off -> no-op
            return self
        self._rss0 = _rss_mb()
        if tracemalloc.is_tracing():
            try:
                tracemalloc.reset_peak()
            except Exception:
                pass
        _emit(f"PROBE start [{self.label}] rss={self._rss0:.0f}MB")
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        """Log the RSS delta and tracemalloc peak; never swallow exceptions."""
        if not _enabled:  # diagnostics off -> no-op
            return False
        rss1 = _rss_mb()
        peak = -1.0
        if tracemalloc.is_tracing():
            try:
                _, peak_b = tracemalloc.get_traced_memory()
                peak = peak_b / 1024 / 1024
            except Exception:
                pass
        status = "raised " + exc_type.__name__ if exc_type else "ok"
        _emit(
            f"PROBE end   [{self.label}] rss={rss1:.0f}MB "
            f"d={rss1 - self._rss0:+.0f}MB tm_peak={peak:.0f}MB ({status})"
        )
        return False  # never swallow exceptions
