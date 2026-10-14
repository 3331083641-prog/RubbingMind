"""Compatibility entry for the strict final stele browser acceptance suite.

Run backend probes first, then start `npm run dev` in apps/web and run this file.
Every interaction is asserted by state, pixels or actual UI feedback.
"""
from scripts.validate_stele_final import run

if __name__ == '__main__':
    run('http://127.0.0.1:5173/?steleQA=1')
