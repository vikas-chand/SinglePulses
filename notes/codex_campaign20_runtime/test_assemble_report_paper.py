#!/usr/bin/env python3
"""Tests use completed GRB 081222 and temporary P2 fixtures only."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "campaign_report_assembler", HERE / "assemble_report_paper.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

PRODUCTS_SPEC = importlib.util.spec_from_file_location(
    "campaign_products_authority", HERE / "campaign_products.py")
PRODUCTS = importlib.util.module_from_spec(PRODUCTS_SPEC)
assert PRODUCTS_SPEC.loader is not None
sys.modules[PRODUCTS_SPEC.name] = PRODUCTS
PRODUCTS_SPEC.loader.exec_module(PRODUCTS)


class AssemblerTests(unittest.TestCase):
    @staticmethod
    def write_p2(path: Path) -> None:
        value = {
            "trigger": "bn081222204", "complete": True,
            "provisional": True, "figure_gate_status": MODULE.GATE,
            "t90": {
                "estimator_label": "windowed T90", "t90_s": 11.33,
                "t90_err_s": 0.32, "t90_err_lo_s": 0.21,
                "t90_err_hi_s": 0.43, "lower_limit": False,
                "approved_src_window_s": [-1.16, 16.48],
            },
            "mvt": {
                "canonical_bala": {
                    "mvt_s": 0.0304, "mvt_err_s": 0.0021,
                    "delta_s": 0.016, "status": "detection",
                    "interval_s": [-0.5, 4.5], "seed": 20260718},
                "noncanonical_cwt": {
                    "mvt_s": 0.215, "mvt_err_s": 0.017},
                "noncanonical_haar": {
                    "mvt_s": 1.02, "upper_limit": True},
            },
            "lag": {
                "tau_s": 0.474, "sigma_l_s": 0.269,
                "sigma_r_s": 0.171, "window_systematic_s": 0.377,
            },
            "pulse": {
                "best_pulse_model": "Kocevski",
                "gowri": {
                    "quote_phi": True, "reported_phi": 0.263,
                    "phi_err_raw": 0.029},
            },
            "artifacts": [],
        }
        path.write_text(json.dumps(value))

    def test_trigger_and_escape(self) -> None:
        self.assertEqual(MODULE.CANONICAL_PREFIXES, PRODUCTS.HIGHE_PREFIXES)
        self.assertEqual(
            MODULE.grb_for_trigger("bn081224887"), "GRB 081224")
        self.assertEqual(
            MODULE.grb_for_trigger("bn081222204"), "GRB 081222")
        self.assertEqual(MODULE.tex_escape("a_b&c"), r"a\_b\&c")
        self.assertEqual(
            MODULE.tex_escape(">=9.2; <1.02; >100 MeV"),
            r"\textgreater{}=9.2; \textless{}1.02; \textgreater{}100 MeV")

    def test_asymmetric_t90_precedes_symmetric_error_and_limit_reason(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            p2 = Path(raw) / "p2.json"
            self.write_p2(p2)
            value = json.loads(p2.read_text())
            value["t90"].update({
                "t90_s": 10.0, "t90_err_s": 9.0,
                "t90_err_lo_s": 1.0, "t90_err_hi_s": 2.0,
                "lower_limit": True,
                "lower_limit_reason": "t5/t95 reached the approved source-window edge",
                "t90_window_truncated": True,
            })
            p2.write_text(json.dumps(value))
            ctx = MODULE.load_context(
                "bn081222204", MODULE.FIT_ROOT, MODULE.SWEEP_ROOT, p2)
            statements = MODULE.temporal_statements(ctx)
            self.assertIn("(+2/-1)", statements[0])
            self.assertNotIn("± 9", statements[0])
            self.assertTrue(any(
                "limits spectroscopic coverage" in item and
                "t5/t95 reached" in item for item in statements))

    def test_tex_comparison_symbols_survive_pdf_text_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            escaped = MODULE.tex_escape(">=9.2; <1.02 s; >100 MeV")
            (root / "main.tex").write_text(
                r"\documentclass{aastex631}" + "\n" +
                r"\begin{document}" + "\n" + escaped + "\n" +
                r"\end{document}" + "\n")
            compile_result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                cwd=root, capture_output=True, text=True, check=False)
            self.assertEqual(
                compile_result.returncode, 0,
                compile_result.stdout + compile_result.stderr)
            extracted = subprocess.run(
                ["pdftotext", "main.pdf", "-"], cwd=root,
                capture_output=True, text=True, check=False)
            self.assertEqual(extracted.returncode, 0, extracted.stderr)
            self.assertIn(">=9.2", extracted.stdout)
            self.assertIn("<1.02 s", extracted.stdout)
            self.assertIn(">100 MeV", extracted.stdout)

    def test_completed_fixture_renders_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temporary = Path(raw)
            p2 = temporary / "p2.json"
            self.write_p2(p2)
            ctx = MODULE.load_context(
                "bn081222204", MODULE.FIT_ROOT, MODULE.SWEEP_ROOT, p2)
            self.assertEqual(len(set(ctx.prefixes)), 24)
            self.assertEqual(len(ctx.winners), 7)
            self.assertTrue(ctx.p2_complete)
            figures = MODULE.FigureRegistry(ctx, temporary / "paper")
            legacy = {
                "returncode": 0, "log": "/tmp/fixture.log",
                "used_as_scientific_authority": False,
            }
            report = MODULE.render_report(
                ctx, figures, temporary / "REPORT.md", legacy)
            tex = MODULE.render_tex(ctx, figures, legacy)
            self.assertIn("Every quantitative value is PROVISIONAL", report)
            self.assertIn("UNGATED", report)
            self.assertIn("ΔAIC<2 tie set", report)
            self.assertLess(
                report.index("Step 7 - temporal analysis"),
                report.index("Step 6 - time-resolved spectroscopy"))
            self.assertIn(r"\title{\grb}", tex)
            self.assertIn(
                "Agentic AI Report by Vikas Chand, Khushboo Sharma, and Jagdish C. Joshi",
                tex)
            self.assertIn(r"\noaffiliation", tex)
            self.assertLess(
                tex.index("Step 7: Timing Analysis"),
                tex.index("Step 6: Time-resolved Spectroscopy"))
            self.assertNotIn(r"\includegraphics", tex)
            self.assertNotIn("_VALUE", tex)
            self.assertNotRegex(report + tex, r"[\u2010-\u2015]")
            self.assertIn(r"\begin{longtable}", tex)
            self.assertNotIn(r"\rotate", MODULE.tex_winner_table(ctx))
            self.assertFalse(any(
                item.startswith("P0 block indices incomplete")
                for item in ctx.anomalies))

    def test_missing_products_stay_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            ctx = MODULE.load_context(
                "bn081222204", root / "fits", root / "sweep")
            figures = MODULE.FigureRegistry(ctx, root / "paper")
            legacy = {"returncode": 0, "log": "/tmp/fixture.log"}
            report = MODULE.render_report(
                ctx, figures, root / "REPORT.md", legacy)
            tex = MODULE.render_tex(ctx, figures, legacy)
            self.assertIn("P1 fit missing", " | ".join(ctx.anomalies))
            self.assertIn(
                "no temporal value is substituted", report)
            self.assertNotIn(r"\includegraphics", tex)

    def test_blocked_p2_can_quote_validated_temporal_subset(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temporary = Path(raw)
            p2 = temporary / "p2.json"
            self.write_p2(p2)
            value = json.loads(p2.read_text())
            value["complete"] = False
            value["temporal_values_complete"] = True
            value["validation_errors"] = [
                "step/QC product unavailable after response block"]
            p2.write_text(json.dumps(value))
            ctx = MODULE.load_context(
                "bn081222204", MODULE.FIT_ROOT, MODULE.SWEEP_ROOT, p2)
            self.assertFalse(ctx.p2_complete)
            self.assertTrue(ctx.temporal_values_available)
            statements = MODULE.temporal_statements(ctx)
            self.assertIn("11.3", statements[0])
            status, reason = MODULE.recommend_status(ctx, None)
            self.assertEqual(status, "PARTIAL")
            self.assertIn("P2 temporal summary incomplete", reason)

    def test_temporal_limit_and_haar_detection_uncertainty(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            p2 = Path(raw) / "p2.json"
            self.write_p2(p2)
            value = json.loads(p2.read_text())
            value["mvt"]["canonical_bala"].update({
                "status": "limit", "limit_relation": ">",
                "mvt_err_s": None,
            })
            value["mvt"]["noncanonical_haar"] = {
                "mvt_s": 0.128, "mvt_err_s": 0.016,
                "upper_limit": False,
            }
            p2.write_text(json.dumps(value))
            ctx = MODULE.load_context(
                "bn081222204", MODULE.FIT_ROOT, MODULE.SWEEP_ROOT, p2)
            statement = MODULE.temporal_statements(ctx)[1]
            self.assertIn("status=limit) > 0.0304 s", statement)
            self.assertIn("delta_s=0.016 s", statement)
            self.assertIn("window length 5 s", statement)
            self.assertIn("Haar in-chain = 0.128 ± 0.016 s", statement)

    def test_figure_stage_atomically_replaces_stale_destination(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "source" / "panel.png"
            source.parent.mkdir()
            source.write_bytes(b"fresh-png-fixture")
            ctx = MODULE.load_context(
                "bn081222204", root / "fits", root / "sweep")
            registry = MODULE.FigureRegistry(ctx, root / "paper")
            stale = registry.figure_dir / source.name
            stale.parent.mkdir(parents=True)
            stale.write_bytes(b"stale")
            destination = registry.stage(source, "fixture")
            self.assertEqual(destination, stale)
            self.assertEqual(MODULE.sha256(destination), MODULE.sha256(source))

    def test_campaign_build_options_fail_closed(self) -> None:
        args = SimpleNamespace(
            trig="bn081224887", fit_root=MODULE.FIT_ROOT,
            sweep_root=MODULE.SWEEP_ROOT, p2_summary=None,
            report_path=None, paper_dir=None, no_compile=True,
            allow_fixture=False,
        )
        report = MODULE.SWEEP_ROOT / args.trig / ("REPORT_" + args.trig + ".md")
        paper = MODULE.PAPER_ROOT / MODULE.paper_slug(MODULE.grb_for_trigger(args.trig))
        with self.assertRaises(SystemExit):
            MODULE.enforce_build_paths(
                args, MODULE.FIT_ROOT.resolve(), MODULE.SWEEP_ROOT.resolve(),
                report, paper)

    def test_campaign_spectroscopy_rejects_alternate_model_order(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            p2 = Path(raw) / "p2.json"
            self.write_p2(p2)
            ctx = MODULE.load_context(
                "bn081222204", MODULE.FIT_ROOT, MODULE.SWEEP_ROOT, p2)
            self.assertNotEqual(tuple(ctx.prefixes), MODULE.CANONICAL_PREFIXES)
            ctx.number = 3
            ctx.promotion_receipt = {"input_fingerprint": "fixture"}
            ctx.stage_manifest = {"input_fingerprint": "fixture"}
            ctx.anomalies = []
            self.assertFalse(ctx.spectroscopy_available)

    def test_long_winner_table_is_multipage_capable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            p2 = Path(raw) / "p2.json"
            self.write_p2(p2)
            ctx = MODULE.load_context(
                "bn081222204", MODULE.FIT_ROOT, MODULE.SWEEP_ROOT, p2)
            ctx.winners = (ctx.winners * 5)[:35]
            rendered = MODULE.tex_winner_table(ctx)
            self.assertIn(r"\begin{longtable}", rendered)
            self.assertNotIn(r"\rotate", rendered)
            self.assertGreaterEqual(rendered.count(r" \\"), 35)
            tex = (
                r"\documentclass[twocolumn]{aastex631}" + "\n" +
                r"\begin{document}" + "\n" + rendered + "\n" +
                r"\end{document}" + "\n")
            (Path(raw) / "main.tex").write_text(tex)
            result = subprocess.run(
                ["pdflatex", "-draftmode", "-interaction=nonstopmode",
                 "-halt-on-error", "main.tex"],
                cwd=raw, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((Path(raw) / "main.pdf").exists())

    def test_failed_four_pass_compile_removes_early_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "main.tex").write_text(
                r"\documentclass{aastex631}" + "\n" +
                r"\begin{document}fixture\end{document}" + "\n")
            result = MODULE.compile_paper(root)
            self.assertEqual(len(result["results"]), 4)
            self.assertFalse(result["success"])
            self.assertFalse((root / "main.pdf").exists())
            self.assertFalse((root / root.name).with_suffix(".pdf").exists())

    def test_missing_tex_figure_is_explicit_without_broken_include(self) -> None:
        rendered = MODULE.tex_figure(
            None, "Current-fit Step 9 QC.", "fig:missing")
        self.assertIn("Figure missing", rendered)
        self.assertNotIn(r"\includegraphics", rendered)

    def test_manifest_parser_and_queue_guard(self) -> None:
        text = (
            "| 3 | " + chr(96) + "bn081224887" + chr(96) +
            " | GRB 081224 | DONE | x | y |\n" +
            "| 4 | " + chr(96) + "bn090530760" + chr(96) +
            " | GRB 090530 | IN PROGRESS | x | y |\n")
        self.assertEqual(
            MODULE.parse_manifest(text)["bn081224887"], "DONE")
        MODULE.queue_guard(text, "bn090530760")

    def test_brief_exact_script48_is_captured_not_used(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = MODULE.invoke_script48_exact(
                "bn081222204", Path(raw))
            self.assertEqual(
                result["command"],
                ["python", "scripts/48_burst_report.py",
                 "--trig", "bn081222204"])
            self.assertEqual(result["returncode"], 0)
            self.assertIn("NoneType", result["stdout"])
            self.assertFalse(result["used_as_scientific_authority"])
            self.assertTrue(Path(result["log"]).is_file())


if __name__ == "__main__":
    unittest.main()
