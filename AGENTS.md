# AGENTS.md

## Mission

Build a **local, Python-launched measurement inspection app** that reads measurements through an **eCAL HDF measurement adapter**, derives message-level metrics, computes summaries and event tables, and serves a **local browser UI** for interactive drill-down.

This project is optimized for:
- **one engineer**
- **one measurement at a time**
- **local execution only** (no hosting)
- **Python 3.11+**
- **clean code** and **test-driven development**

---

## Non-negotiable quality bar

Every increment must be **Ready for Review**:

- ✅ All tests pass
- ✅ All linters/formatters pass
- ✅ Output stable and documented
- ✅ ADR updated if any non-trivial decision was made
- ✅ No TODOs for shipped behavior  
  - TODOs allowed only for future work, explicitly labeled and tracked

---

## Product shape

A single command launches local inspection:

```bash
measure-inspect /path/to/measurement